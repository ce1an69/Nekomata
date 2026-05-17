"""AI interpretation backends: OpenAI-compatible API and template fallback."""

import json
import logging
import urllib.request
import urllib.error
from typing import Protocol, runtime_checkable

from nekomata.card.types import DrawnCard
from nekomata.ai.prompts import SYSTEM_PROMPT, build_interpretation_prompt
from nekomata.storage.config import AppConfig

log = logging.getLogger(__name__)


class InterpretationError(Exception):
    """AI interpretation failure."""

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


@runtime_checkable
class AIInterpreter(Protocol):
    """Protocol for AI interpretation backends."""

    def interpret(self, drawn_cards: list[DrawnCard], question: str) -> str:
        """Return a textual interpretation for the given cards and question."""
        ...


def _cards_info(drawn_cards: list[DrawnCard]) -> str:
    """Format drawn cards into a structured string for AI prompt."""
    lines = []
    for dc in drawn_cards:
        desc = f"（{dc.position.description}）" if dc.position.description else ""
        lines.append(
            f"【{dc.position.name_zh}】{desc}{dc.card.name_zh}（{dc.status_label}）"
            f" — 关键词：{', '.join(dc.keywords)}，释义：{dc.meaning}"
        )
    return "\n".join(lines)


def _build_messages(style: str, question: str, drawn_cards: list[DrawnCard]) -> list[dict]:
    """Build the system + user message list for the OpenAI chat API."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT.format(style=style)},
        {"role": "user", "content": build_interpretation_prompt(question, _cards_info(drawn_cards))},
    ]


def template_interpret(drawn_cards: list[DrawnCard], question: str) -> str:
    """Generate a structured Markdown interpretation from card keywords and meanings."""
    parts = [f"**问题：{question}**\n"]
    for dc in drawn_cards:
        parts.append(f"### 【{dc.position.name_zh}】{dc.card.name_zh}（{dc.status_label}）")
        if dc.position.description:
            parts.append(f"*{dc.position.description}*")
        parts.append(f"**关键词：** {', '.join(dc.keywords)}")
        parts.append(f"\n{dc.meaning}\n")

    # Add a brief overall summary
    reversed_cards = [dc for dc in drawn_cards if dc.is_reversed]
    n_reversed = len(reversed_cards)
    if len(drawn_cards) > 1:
        parts.append("---\n")
        parts.append("### 综合概述\n")
        all_keywords = []
        for dc in drawn_cards:
            all_keywords.extend(dc.keywords)
        # Pick up to 6 unique keywords for a thematic summary
        unique_kw = list(dict.fromkeys(all_keywords))[:6]
        parts.append(f"本次占卜的主题关键词：{'、'.join(unique_kw)}。\n")
        if n_reversed == 0:
            parts.append("全部正位，整体能量流畅，各方面发展较为顺利。")
        elif n_reversed == len(drawn_cards):
            parts.append("全部逆位，提示当前可能面临较多挑战，需要内省和调整。")
        else:
            parts.append(f"正位 {len(drawn_cards) - n_reversed} 张、逆位 {n_reversed} 张，"
                         "能量有进有退，提醒你在顺境中保持警觉，在逆境中寻找转机。")

    return "\n".join(parts)


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

    def interpret(self, drawn_cards: list[DrawnCard], question: str) -> str:
        """Send cards and question to the API and return the interpretation."""
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
                content = data["choices"][0]["message"]["content"]
                if not content or not content.strip():
                    raise InterpretationError("Empty response from API", retryable=True)
                return content
        except urllib.error.URLError as e:
            raise InterpretationError(str(e), retryable=True) from e
        except (KeyError, IndexError) as e:
            raise InterpretationError(str(e), retryable=False) from e


def get_interpreter(config: AppConfig) -> AIInterpreter:
    """Factory: return the configured interpreter, with optional template fallback."""
    backend = config.ai_backend
    if backend == "openai_compatible":
        backend = "openai"

    if backend == "openai":
        return OpenAIInterpreter(
            model=config.ai_model,
            base_url=config.ai_base_url,
            api_key=config.ai_api_key,
            timeout=config.ai_timeout,
            style=config.ai_style,
        )

    return TemplateFallback()


class TemplateFallback:
    """Wraps template_interpret to satisfy AIInterpreter protocol."""

    def interpret(self, drawn_cards: list[DrawnCard], question: str) -> str:
        return template_interpret(drawn_cards, question)
