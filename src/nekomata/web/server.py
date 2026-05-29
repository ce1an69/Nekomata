"""FastAPI web server for Nekomata — serves static UI and shared data APIs."""

import asyncio
import json
import logging
import threading
import webbrowser

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from nekomata.ai.interpreter import InterpretationError, build_messages, get_interpreter
from nekomata.ai.prompts import build_followup_prompt
from nekomata.card.data import load_all_cards
from nekomata.card.types import Card, DrawnCard, Position
from nekomata.i18n import SUPPORTED_LANGS, arcana_label, ui_strings
from nekomata.render.styles import (
    C_BASE,
    C_CRUST,
    C_LAVENDER,
    C_MANTLE,
    C_MAUVE,
    C_OVERLAY0,
    C_PINK,
    C_RED,
    C_SUBTEXT0,
    C_SUBTEXT1,
    C_SURFACE0,
    C_SURFACE1,
    C_SURFACE2,
    C_TEXT,
)
from nekomata._paths import assets_dir, static_dir
from nekomata.spread import SPREAD_REGISTRY
from nekomata.storage.config import AppConfig

log = logging.getLogger(__name__)

_STATIC_DIR = static_dir()
_ASSETS_DIR = assets_dir()

# Catppuccin Mocha colors mapped to CSS variable names
_THEME_COLORS = {
    "crust": C_CRUST,
    "mantle": C_MANTLE,
    "base": C_BASE,
    "surface0": C_SURFACE0,
    "surface1": C_SURFACE1,
    "surface2": C_SURFACE2,
    "overlay0": C_OVERLAY0,
    "subtext0": C_SUBTEXT0,
    "subtext1": C_SUBTEXT1,
    "text": C_TEXT,
    "mauve": C_MAUVE,
    "lavender": C_LAVENDER,
    "pink": C_PINK,
    "red": C_RED,
}


async def _sse_error(message: str):
    """Single-shot SSE generator that yields one error then stops."""
    yield f"data: {json.dumps({'error': message})}\n\n"


def _card_to_dict(card: Card, has_origin: bool = False) -> dict:
    return {
        "id": card.id,
        "name": card.name,
        "name_zh": card.name_zh,
        "arcana": card.arcana.value,
        "arcana_zh": arcana_label(card.arcana.value, lang="zh"),
        "number": card.number,
        "element": card.element,
        "astrology": card.astrology,
        "keywords_upright": list(card.keywords_upright),
        "keywords_reversed": list(card.keywords_reversed),
        "meaning_upright": card.meaning_upright,
        "meaning_reversed": card.meaning_reversed,
        "keywords_upright_en": list(card.keywords_upright_en),
        "keywords_reversed_en": list(card.keywords_reversed_en),
        "meaning_upright_en": card.meaning_upright_en,
        "meaning_reversed_en": card.meaning_reversed_en,
        "has_image": has_origin,
    }


def _get_cached_cards(app) -> tuple[list[dict], dict[str, Card]]:
    """Return cached (card_dicts, cards_by_id). Loads once from disk."""
    if not hasattr(app.state, "cards_dict"):
        cards = load_all_cards()
        app.state.cards_by_id = {c.id: c for c in cards}
        app.state.cards_dict = [
            _card_to_dict(
                c,
                has_origin=c.image_path is not None
                and (c.image_path.parent / f"{c.id}_detail.png").exists(),
            )
            for c in cards
        ]
    return app.state.cards_dict, app.state.cards_by_id


def _spreads_to_list(lang: str | None = None) -> list[dict]:
    from nekomata.spread import get_spread as _get_spread

    result = []
    for key, cls in SPREAD_REGISTRY:
        spread = _get_spread(key, lang=lang)
        result.append(
            {
                "key": key,
                "description": spread.description,
                "suitable_for": spread.suitable_for,
                "name": spread.name,
                "positions": [
                    {"name": p.name, "description": p.description}
                    for p in spread.positions
                ],
                "card_count": len(spread.positions),
            }
        )
    return result


def _build_theme_css() -> str:
    vars_str = "\n".join(f"  --{k}: {v};" for k, v in _THEME_COLORS.items())
    return f":root {{\n{vars_str}\n}}"


# --- Request models ---


class ConfigPayload(BaseModel):
    api_url: str = ""
    api_key: str = ""
    model: str = ""
    lang: str = "en"

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v: str) -> str:
        if v not in SUPPORTED_LANGS:
            raise ValueError(f"Unsupported language: {v}")
        return v

    @field_validator("api_url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("api_url must start with http:// or https://")
        return v


class DrawnCardPayload(BaseModel):
    card_id: str = Field(min_length=1)
    position_name: str = Field(min_length=1)
    position_name_zh: str = ""
    position_description: str = ""
    is_reversed: bool


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str


class InterpretPayload(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    cards: list[DrawnCardPayload] = Field(min_length=1)
    spread_key: str = ""


class FollowupPayload(BaseModel):
    messages: list[ChatMessage]
    question: str = Field(min_length=1, max_length=2000)


class ExportImagePayload(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    cards: list[DrawnCardPayload] = []
    spread_name: str = ""
    question: str = ""


def _resolve_drawn_cards(
    cards_payload: list[DrawnCardPayload], cards_by_id: dict[str, Card]
) -> list[DrawnCard]:
    """Validate card IDs and build DrawnCard list from a request payload."""
    invalid_ids = [dc.card_id for dc in cards_payload if dc.card_id not in cards_by_id]
    if invalid_ids:
        raise HTTPException(status_code=422, detail=f"Invalid card IDs: {invalid_ids}")
    return [
        DrawnCard(
            card=cards_by_id[dc.card_id],
            position=Position(
                name=dc.position_name,
                name_zh=dc.position_name_zh,
                description=dc.position_description,
            ),
            is_reversed=dc.is_reversed,
        )
        for dc in cards_payload
    ]


# --- App factory ---


def create_app() -> FastAPI:
    app = FastAPI(title="Nekomata Web", docs_url=None, redoc_url=None)

    # Rate limiting (localhost-only for desktop, generous limits for local dev)
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/")
    async def index():
        if not hasattr(app.state, "cached_html"):
            html = (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
            theme_css = _build_theme_css()
            app.state.cached_html = html.replace("/*__THEME_VARS__*/", theme_css)
        return HTMLResponse(app.state.cached_html)

    @app.get("/api/config")
    async def get_config():
        cfg = AppConfig.load()
        return {
            "api_url": cfg.api_url,
            "api_key": "",
            "model": cfg.model,
            "lang": cfg.lang,
            "has_api_key": bool(cfg.api_key),
        }

    @app.post("/api/config")
    async def save_config(payload: ConfigPayload):
        existing = AppConfig.load()
        api_key = payload.api_key or existing.api_key or ""
        cfg = AppConfig.save(
            api_url=payload.api_url,
            api_key=api_key,
            model=payload.model,
            lang=payload.lang,
        )
        return {
            "ok": True,
            "api_url": cfg.api_url,
            "model": cfg.model,
            "lang": cfg.lang,
            "has_api_key": bool(cfg.api_key),
        }

    @app.get("/api/cards")
    async def get_cards():
        card_dicts, _ = _get_cached_cards(app)
        return card_dicts

    @app.get("/api/spreads")
    async def get_spreads():
        cfg = AppConfig.load()
        cache_key = f"spreads_{cfg.lang}"
        if not hasattr(app.state, cache_key):
            setattr(app.state, cache_key, _spreads_to_list(lang=cfg.lang))
        return getattr(app.state, cache_key)

    @app.get("/api/theme")
    async def get_theme():
        return _THEME_COLORS

    @app.get("/api/strings")
    async def get_strings():
        cfg = AppConfig.load()
        return ui_strings(lang=cfg.lang)

    @app.post("/api/interpret")
    # AI endpoints: lower rate limit (expensive upstream calls)
    async def interpret(req: InterpretPayload):
        config = AppConfig.load()
        _, cards_by_id = _get_cached_cards(app)
        drawn = _resolve_drawn_cards(req.cards, cards_by_id)

        if not drawn:
            return StreamingResponse(
                _sse_error("No valid cards provided"), media_type="text/event-stream"
            )

        try:
            interp = get_interpreter(config)
        except InterpretationError as exc:
            return StreamingResponse(
                _sse_error(str(exc)), media_type="text/event-stream"
            )

        async def _stream():
            loop = asyncio.get_running_loop()
            try:
                msgs = build_messages("mystical", req.question, drawn, req.spread_key, lang=config.lang)
                yield f"data: {json.dumps({'messages': msgs})}\n\n"
                gen = interp.interpret_stream(drawn, req.question, req.spread_key, lang=config.lang)
                while True:
                    chunk = await loop.run_in_executor(None, next, gen, None)
                    if chunk is None:
                        break
                    data = json.dumps({"text": chunk.text, "kind": chunk.kind})
                    yield f"data: {data}\n\n"
                yield "data: [DONE]\n\n"
            except InterpretationError as e:
                data = json.dumps({"error": str(e)})
                yield f"data: {data}\n\n"
            except Exception as e:
                log.exception("Unexpected interpretation failure")
                data = json.dumps({"error": f"Interpretation failed: {e}"})
                yield f"data: {data}\n\n"

        return StreamingResponse(_stream(), media_type="text/event-stream")

    @app.post("/api/interpret/followup")
    async def interpret_followup(req: FollowupPayload):
        """Stream a follow-up interpretation using conversation history."""
        config = AppConfig.load()
        try:
            interp = get_interpreter(config)
        except InterpretationError as exc:
            return StreamingResponse(
                _sse_error(str(exc)), media_type="text/event-stream"
            )

        followup_msg = build_followup_prompt(req.question, lang=config.lang)
        messages = [m.model_dump() for m in req.messages] + [{"role": "user", "content": followup_msg}]

        async def _stream():
            loop = asyncio.get_running_loop()
            try:
                gen = interp.stream_raw(messages, thinking=False)
                while True:
                    chunk = await loop.run_in_executor(None, next, gen, None)
                    if chunk is None:
                        break
                    data = json.dumps({"text": chunk.text, "kind": chunk.kind})
                    yield f"data: {data}\n\n"
                yield "data: [DONE]\n\n"
            except InterpretationError as e:
                data = json.dumps({"error": str(e)})
                yield f"data: {data}\n\n"
            except Exception as e:
                log.exception("Unexpected follow-up interpretation failure")
                data = json.dumps({"error": f"Interpretation failed: {e}"})
                yield f"data: {data}\n\n"

        return StreamingResponse(_stream(), media_type="text/event-stream")

    @app.post("/api/export-image")
    async def export_image(req: ExportImagePayload):
        """Render interpretation as a Catppuccin-themed PNG image."""
        from io import BytesIO

        from fastapi.responses import Response
        from nekomata.render.image_export import render_interp_image

        config = AppConfig.load()
        _, cards_by_id = _get_cached_cards(app)
        drawn = _resolve_drawn_cards(req.cards, cards_by_id)

        img = render_interp_image(req.text, drawn or None, lang=config.lang, question=req.question)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return Response(
            content=buf.getvalue(),
            media_type="image/png",
            headers={
                "Content-Disposition": "attachment; filename=nekomata-reading.png"
            },
        )

    # Mount static files last (catch-all)
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
    app.mount("/assets", StaticFiles(directory=str(_ASSETS_DIR)), name="assets")

    return app


def start_web_server(port: int = 8080) -> None:
    import uvicorn

    app = create_app()
    url = f"http://localhost:{port}"
    print(f"\n  Nekomata Web UI: {url}\n")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
