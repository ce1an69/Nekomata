"""AI interpretation via OpenAI-compatible API."""

import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Generator, Protocol, runtime_checkable

from nekomata.card.types import DrawnCard
from nekomata.card.display import card_keywords, card_meaning, card_name, status_label as _status_label
from nekomata.ai.prompts import build_user_prompt, load_spread_prompt, load_system_prompt
from nekomata.storage.config import AppConfig

log = logging.getLogger(__name__)


class InterpretationError(Exception):
    """AI interpretation failure."""

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


@dataclass(frozen=True)
class StreamChunk:
    """A typed streaming fragment from the model."""

    text: str
    kind: str = "content"


@runtime_checkable
class AIInterpreter(Protocol):
    """Protocol for AI interpretation backends."""

    def interpret(self, drawn_cards: list[DrawnCard], question: str, spread_key: str = "", lang: str = "en") -> str: ...

    def interpret_stream(
        self, drawn_cards: list[DrawnCard], question: str, spread_key: str = "", lang: str = "en"
    ) -> Generator[StreamChunk, None, None]: ...

    def stream_raw(
        self, messages: list[dict], *, thinking: bool = True
    ) -> Generator[StreamChunk, None, None]: ...


def _cards_info(drawn_cards: list[DrawnCard], lang: str) -> str:
    """Format drawn cards into a structured string for AI prompt."""
    lines = []
    for dc in drawn_cards:
        desc = f" ({dc.position.description})" if dc.position.description else ""
        name = card_name(dc.card, lang)
        slbl = _status_label(dc.is_reversed, lang)
        kw = ", ".join(card_keywords(dc.card, dc.is_reversed, lang))
        meaning = card_meaning(dc.card, dc.is_reversed, lang)
        if lang == "en":
            lines.append(
                f"[{dc.position.name}]{desc} {name} ({slbl})"
                f" — keywords: {kw}, meaning: {meaning}"
            )
        else:
            lines.append(
                f"【{dc.position.name}】{desc}{name}（{slbl}）"
                f" — keywords: {kw}, meaning: {meaning}"
            )
    return "\n".join(lines)


def build_messages(style: str, question: str, drawn_cards: list[DrawnCard], spread_key: str = "", lang: str = "en") -> list[dict]:
    """Build the system + user message list for the OpenAI chat API."""
    system_content = load_system_prompt().format(style=style)
    spread_prompt = load_spread_prompt(spread_key) if spread_key else ""
    if spread_prompt:
        system_content += "\n\n" + spread_prompt
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": build_user_prompt(question, _cards_info(drawn_cards, lang))},
    ]


_DEFAULT_TIMEOUT = 60.0
_DEFAULT_STYLE = "mystical"


class OpenAIInterpreter:
    """Interpret via OpenAI-compatible remote API."""

    def __init__(self, model: str, base_url: str = "https://api.openai.com/v1",
                 api_key: str | None = None) -> None:
        self._model = model
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._api_key = api_key

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _make_request(self, payload: dict) -> urllib.request.Request:
        return urllib.request.Request(
            self._url,
            data=json.dumps(payload).encode(),
            headers=self._build_headers(),
        )

    def interpret(self, drawn_cards: list[DrawnCard], question: str, spread_key: str = "", lang: str = "en") -> str:
        """Send cards and question to the API and return the interpretation."""
        req = self._make_request({
            "model": self._model,
            "messages": build_messages(_DEFAULT_STYLE, question, drawn_cards, spread_key, lang),
            "stream": False,
        })
        try:
            with urllib.request.urlopen(req, timeout=_DEFAULT_TIMEOUT) as resp:
                data = json.loads(resp.read())
                content = data["choices"][0]["message"]["content"]
                if not content or not content.strip():
                    raise InterpretationError("Empty response from API", retryable=True)
                return content
        except urllib.error.URLError as e:
            raise InterpretationError(str(e), retryable=True) from e
        except (KeyError, IndexError) as e:
            raise InterpretationError(str(e), retryable=False) from e

    def interpret_stream(
        self, drawn_cards: list[DrawnCard], question: str, spread_key: str = "", lang: str = "en"
    ) -> Generator[StreamChunk, None, None]:
        """Yield text chunks from the streaming API (SSE)."""
        messages = build_messages(_DEFAULT_STYLE, question, drawn_cards, spread_key, lang)
        yield from self.stream_raw(messages)

    def stream_raw(
        self, messages: list[dict], *, thinking: bool = True
    ) -> Generator[StreamChunk, None, None]:
        """Yield text chunks from pre-built messages (for follow-up conversations).

        Parses Server-Sent Events line by line. Each event is "data: {json}".
        The delta object may contain reasoning (chain-of-thought) and/or
        content (the actual response). Different providers use different
        field names for reasoning — we check all common variants.

        Set thinking=False to disable reasoning output (faster responses).
        """
        payload: dict = {
            "model": self._model,
            "messages": messages,
            "stream": True,
        }
        if not thinking:
            payload["enable_thinking"] = False
        req = self._make_request(payload)
        try:
            with urllib.request.urlopen(req, timeout=_DEFAULT_TIMEOUT) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    if line == "data: [DONE]":
                        return
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        choices = data.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        if thinking:
                            reasoning = (
                                delta.get("reasoning_content")
                                or delta.get("reasoning")
                                or delta.get("thinking")
                                or delta.get("think")
                                or ""
                            )
                            if reasoning:
                                yield StreamChunk(str(reasoning), "thinking")
                        content = delta.get("content", "")
                        if content:
                            yield StreamChunk(str(content), "content")
        except urllib.error.URLError as e:
            raise InterpretationError(str(e), retryable=True) from e
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise InterpretationError(str(e), retryable=False) from e


def get_interpreter(config: AppConfig) -> AIInterpreter:
    """Factory: return an OpenAI-compatible interpreter.

    Raises InterpretationError if the API key is not configured.
    """
    if not config.api_key:
        raise InterpretationError(
            "API key not configured. "
            "Set api_key in .neko/settings.json to enable interpretation.",
            retryable=False,
        )
    return OpenAIInterpreter(
        model=config.model,
        base_url=config.api_url,
        api_key=config.api_key,
    )
