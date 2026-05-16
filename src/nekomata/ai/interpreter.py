from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import AsyncIterator, Protocol, runtime_checkable

from nekomata.card.types import DrawnCard
from nekomata.ai.prompts import SYSTEM_PROMPT, build_interpretation_prompt

log = logging.getLogger(__name__)


class InterpretationError(Exception):
    """AI interpretation failure."""

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


@runtime_checkable
class AIInterpreter(Protocol):
    def interpret(self, drawn_cards: list[DrawnCard], question: str) -> str: ...


def _cards_info(drawn_cards: list[DrawnCard]) -> str:
    lines = []
    for dc in drawn_cards:
        status = "逆位" if dc.is_reversed else "正位"
        keywords = dc.card.keywords_reversed if dc.is_reversed else dc.card.keywords_upright
        meaning = dc.card.meaning_reversed if dc.is_reversed else dc.card.meaning_upright
        lines.append(
            f"【{dc.position.name_zh}】{dc.card.name_zh}（{status}）"
            f" — 关键词：{', '.join(keywords)}，释义：{meaning}"
        )
    return "\n".join(lines)


def _build_messages(style: str, question: str, drawn_cards: list[DrawnCard]) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT.format(style=style)},
        {"role": "user", "content": build_interpretation_prompt(question, _cards_info(drawn_cards))},
    ]


def template_interpret(drawn_cards: list[DrawnCard], question: str) -> str:
    parts = [f"🔮 问题：{question}\n"]
    for dc in drawn_cards:
        status = "逆位" if dc.is_reversed else "正位"
        keywords = dc.card.keywords_reversed if dc.is_reversed else dc.card.keywords_upright
        meaning = dc.card.meaning_reversed if dc.is_reversed else dc.card.meaning_upright
        parts.append(f"【{dc.position.name_zh}】{dc.card.name_zh}（{status}）")
        parts.append(f"  关键词：{', '.join(keywords)}")
        parts.append(f"  释义：{meaning}")
        parts.append("")
    return "\n".join(parts)


async def template_interpret_stream(drawn_cards: list[DrawnCard], question: str) -> AsyncIterator[str]:
    """Stream template interpretation line by line."""
    text = template_interpret(drawn_cards, question)
    for line in text.split("\n"):
        yield line + "\n"


class OpenAIInterpreter:
    """Interpret via OpenAI-compatible remote API."""

    def __init__(self, model: str, base_url: str = "https://api.openai.com/v1",
                 api_key: str | None = None, timeout: float = 60.0,
                 style: str = "mystical") -> None:
        self._model = model
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._api_key = api_key
        self._timeout = timeout
        self._style = style

    def health_check(self) -> bool:
        try:
            req = urllib.request.Request(
                self._url.rsplit("/", 1)[0] + "/models",
                headers={"Authorization": f"Bearer {self._api_key}"} if self._api_key else {},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def interpret(self, drawn_cards: list[DrawnCard], question: str) -> str:
        payload = json.dumps({
            "model": self._model,
            "messages": _build_messages(self._style, question, drawn_cards),
            "stream": False,
        }).encode()

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        req = urllib.request.Request(self._url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except urllib.error.URLError as e:
            raise InterpretationError(str(e), retryable=True) from e
        except (KeyError, IndexError) as e:
            raise InterpretationError(str(e), retryable=False) from e

    async def interpret_stream(self, drawn_cards: list[DrawnCard], question: str) -> AsyncIterator[str]:
        """Stream interpretation chunks from OpenAI SSE endpoint."""
        payload = json.dumps({
            "model": self._model,
            "messages": _build_messages(self._style, question, drawn_cards),
            "stream": True,
        }).encode()

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        req = urllib.request.Request(self._url, data=payload, headers=headers)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            with await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=self._timeout)) as resp:
                buffer = ""
                while True:
                    chunk = await loop.run_in_executor(None, resp.read, 1024)
                    if not chunk:
                        break
                    buffer += chunk.decode()
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            return
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except urllib.error.URLError as e:
            raise InterpretationError(str(e), retryable=True) from e


def get_interpreter(config) -> AIInterpreter:
    """Factory: return the configured interpreter, with optional template fallback."""
    backend = getattr(config, "ai_backend", "template")
    if backend == "openai_compatible":
        backend = "openai"

    if backend == "openai":
        try:
            return OpenAIInterpreter(
                model=config.ai_model,
                base_url=config.ai_base_url,
                api_key=config.ai_api_key,
                timeout=config.ai_timeout,
                style=config.ai_style,
            )
        except Exception:
            if not getattr(config, "ai_fallback", True):
                raise
            log.warning("Falling back to template interpreter")
            return TemplateFallback()

    return TemplateFallback()


class TemplateFallback:
    """Wraps template_interpret to satisfy AIInterpreter protocol."""
    def interpret(self, drawn_cards: list[DrawnCard], question: str) -> str:
        return template_interpret(drawn_cards, question)
