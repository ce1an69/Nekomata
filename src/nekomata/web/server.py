"""FastAPI web server for Nekomata — serves static UI and shared data APIs."""

import asyncio
import json
import logging
import threading
import webbrowser

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from nekomata.ai.interpreter import InterpretationError, get_interpreter
from nekomata.card.data import load_all_cards
from nekomata.card.types import ARCANA_ZH, Card, DrawnCard, Position
from nekomata.i18n import set_lang, ui_strings
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
from nekomata._paths import assets_dir, data_dir, static_dir
from nekomata.spread import SPREAD_REGISTRY
from nekomata.storage.config import AppConfig

log = logging.getLogger(__name__)

_STATIC_DIR = static_dir()
_ASSETS_DIR = assets_dir()

# Cached at module level — read once, not per-request
_CACHED_HTML: str | None = None
_CACHED_SPREADS: list[dict] | None = None
_CACHED_CARDS_DICT: list[dict] | None = None
_CACHED_CARDS_BY_ID: dict[str, Card] | None = None

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
        "arcana_zh": ARCANA_ZH.get(card.arcana, ""),
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


def _get_cached_cards() -> tuple[list[dict], dict[str, Card]]:
    """Return cached (card_dicts, cards_by_id). Loads once from disk."""
    global _CACHED_CARDS_DICT, _CACHED_CARDS_BY_ID
    if _CACHED_CARDS_DICT is None:
        cards = load_all_cards()
        _CACHED_CARDS_BY_ID = {c.id: c for c in cards}
        _CACHED_CARDS_DICT = [
            _card_to_dict(
                c,
                has_origin=c.image_path is not None
                and (c.image_path.parent / f"{c.id}_detail.png").exists(),
            )
            for c in cards
        ]
    return _CACHED_CARDS_DICT, _CACHED_CARDS_BY_ID


def _spreads_to_list() -> list[dict]:
    from nekomata.spread import get_spread as _get_spread
    result = []
    for key, cls in SPREAD_REGISTRY:
        spread = _get_spread(key)
        result.append({
            "key": key,
            "description": spread.description,
            "suitable_for": spread.suitable_for,
            "name": spread.name,
            "positions": [
                {"name": p.name, "description": p.description}
                for p in spread.positions
            ],
            "card_count": len(spread.positions),
        })
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

class DrawnCardPayload(BaseModel):
    card_id: str
    position_name: str
    position_name_zh: str = ""
    position_description: str = ""
    is_reversed: bool

class InterpretPayload(BaseModel):
    question: str
    cards: list[DrawnCardPayload]
    spread_key: str = ""


# --- App factory ---

def create_app() -> FastAPI:
    app = FastAPI(title="Nekomata Web", docs_url=None, redoc_url=None)

    @app.get("/")
    async def index():
        global _CACHED_HTML
        if _CACHED_HTML is None:
            html = (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
            theme_css = _build_theme_css()
            _CACHED_HTML = html.replace("/*__THEME_VARS__*/", theme_css)
        return HTMLResponse(_CACHED_HTML)

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
        return {"ok": True, "api_url": cfg.api_url, "model": cfg.model, "lang": cfg.lang, "has_api_key": bool(cfg.api_key)}

    @app.get("/api/cards")
    async def get_cards():
        card_dicts, _ = _get_cached_cards()
        return card_dicts

    @app.get("/api/spreads")
    async def get_spreads():
        cfg = AppConfig.load()
        set_lang(cfg.lang)
        global _CACHED_SPREADS
        _CACHED_SPREADS = _spreads_to_list()
        return _CACHED_SPREADS

    @app.get("/api/theme")
    async def get_theme():
        return _THEME_COLORS

    @app.get("/api/strings")
    async def get_strings():
        cfg = AppConfig.load()
        set_lang(cfg.lang)
        return ui_strings()

    @app.post("/api/interpret")
    async def interpret(req: InterpretPayload):
        config = AppConfig.load()
        _, cards_by_id = _get_cached_cards()

        drawn: list[DrawnCard] = []
        for dc in req.cards:
            card = cards_by_id.get(dc.card_id)
            if card is None:
                continue
            drawn.append(DrawnCard(
                card=card,
                position=Position(
                    name=dc.position_name,
                    name_zh=dc.position_name_zh,
                    description=dc.position_description,
                ),
                is_reversed=dc.is_reversed,
            ))

        if not drawn:
            return StreamingResponse(_sse_error("No valid cards provided"), media_type="text/event-stream")

        try:
            interp = get_interpreter(config)
        except InterpretationError as exc:
            return StreamingResponse(_sse_error(str(exc)), media_type="text/event-stream")

        async def _stream():
            loop = asyncio.get_running_loop()
            try:
                gen = interp.interpret_stream(drawn, req.question, req.spread_key)
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
