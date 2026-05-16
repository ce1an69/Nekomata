from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Protocol, runtime_checkable

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


class OllamaInterpreter:
    """Interpret via local Ollama API (OpenAI-compatible endpoint)."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434",
                 timeout: float = 120.0, style: str = "mystical") -> None:
        self._model = model
        self._url = f"{base_url.rstrip('/')}/v1/chat/completions"
        self._timeout = timeout
        self._style = style

    def health_check(self) -> bool:
        try:
            req = urllib.request.Request(
                self._url.rsplit("/", 2)[0] + "/api/tags",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def interpret(self, drawn_cards: list[DrawnCard], question: str) -> str:
        payload = json.dumps({
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.format(style=self._style)},
                {"role": "user", "content": build_interpretation_prompt(question, _cards_info(drawn_cards))},
            ],
            "stream": False,
        }).encode()

        req = urllib.request.Request(
            self._url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except urllib.error.URLError as e:
            raise InterpretationError(str(e), retryable=True) from e
        except (KeyError, IndexError) as e:
            raise InterpretationError(str(e), retryable=False) from e


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
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.format(style=self._style)},
                {"role": "user", "content": build_interpretation_prompt(question, _cards_info(drawn_cards))},
            ],
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


def get_interpreter(config) -> AIInterpreter:
    """Factory: return the configured interpreter, with optional template fallback."""
    backend = getattr(config, "ai_backend", "template")

    if backend == "ollama":
        try:
            return OllamaInterpreter(
                model=config.ai_model or "llama3",
                base_url=config.ai_base_url,
                timeout=config.ai_timeout,
                style=config.ai_style,
            )
        except Exception:
            if not getattr(config, "ai_fallback", True):
                raise
            log.warning("Falling back to template interpreter")
            return TemplateFallback()

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
