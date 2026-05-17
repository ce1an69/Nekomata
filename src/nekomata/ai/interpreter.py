"""AI interpretation via OpenAI-compatible API."""

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
            f"【{dc.position.name}】{desc}{dc.card.name}（{dc.status_label}）"
            f" — keywords: {', '.join(dc.keywords)}, meaning: {dc.meaning}"
        )
    return "\n".join(lines)


def _build_messages(style: str, question: str, drawn_cards: list[DrawnCard]) -> list[dict]:
    """Build the system + user message list for the OpenAI chat API."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT.format(style=style)},
        {"role": "user", "content": build_interpretation_prompt(question, _cards_info(drawn_cards))},
    ]


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
    """Factory: return the configured interpreter.

    Raises InterpretationError if the API is not properly configured.
    """
    backend = config.ai_backend
    if backend == "openai_compatible":
        backend = "openai"

    if backend == "openai":
        if not config.ai_api_key:
            raise InterpretationError(
                "API key not configured. "
                "Set ai.api_key in config.toml to enable interpretation.",
                retryable=False,
            )
        if not config.ai_model:
            raise InterpretationError(
                "AI model not configured. "
                "Set ai.model in config.toml to enable interpretation.",
                retryable=False,
            )
        return OpenAIInterpreter(
            model=config.ai_model,
            base_url=config.ai_base_url,
            api_key=config.ai_api_key,
            timeout=config.ai_timeout,
            style=config.ai_style,
        )

    raise InterpretationError(
        f"Unknown AI backend: {backend}. Set ai.backend to 'openai' in config.toml.",
        retryable=False,
    )
