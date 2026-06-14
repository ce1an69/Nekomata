"""Unit tests for web/server.py — API endpoint tests using httpx AsyncClient."""

import json

import pytest

from nekomata.core.ai.interpreter import InterpretationError, StreamChunk
from nekomata.web.server import create_app

pytestmark = pytest.mark.skip_config_fixture


@pytest.fixture()
def _config(tmp_path, monkeypatch):
    """Create a settings file so AppConfig.load() works."""
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text('{"api_url":"http://localhost:1234","api_key":"sk-test-key","model":"test-model","lang":"en"}')
    monkeypatch.chdir(tmp_path)


@pytest.fixture()
def app(_config):
    return create_app()


@pytest.fixture()
async def client(app):
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _valid_card_payload(client):
    cards = (await client.get("/api/cards")).json()
    return {
        "card_id": cards[0]["id"],
        "position_name": "Present",
        "position_description": "Current situation",
        "is_reversed": False,
    }


def _sse_events(resp):
    events = []
    for block in resp.text.strip().split("\n\n"):
        if block.startswith("data: "):
            data = block[6:]
            events.append(data if data == "[DONE]" else json.loads(data))
    return events


class _FakeInterpreter:
    def __init__(self, chunks=None, *, error=None, raw_chunks=None, raw_error=None):
        self._chunks = chunks or []
        self._error = error
        self._raw_chunks = raw_chunks if raw_chunks is not None else self._chunks
        self._raw_error = raw_error

    def interpret_stream(self, drawn, question, spread_key="", lang="en"):
        yield from self._yield_chunks(self._chunks, self._error)

    def stream_raw(self, messages, *, thinking=True):
        yield from self._yield_chunks(self._raw_chunks, self._raw_error)

    @staticmethod
    def _yield_chunks(chunks, error):
        yield from chunks
        if error is not None:
            raise error


# -- GET endpoints --


@pytest.mark.asyncio
async def test_get_config(client):
    resp = await client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_api_key"] is True
    assert data["model"] == "test-model"


@pytest.mark.asyncio
async def test_index_injects_theme_css_and_uses_cache(client, app, monkeypatch):
    reads = 0

    import nekomata.web.server as server

    class FakeStaticFile:
        def read_text(self, encoding="utf-8"):
            nonlocal reads
            reads += 1
            return "<style>/*__THEME_VARS__*/</style>"

    class FakeStaticDir:
        def __truediv__(self, name):
            assert name == "index.html"
            return FakeStaticFile()

    monkeypatch.setattr(server, "_STATIC_DIR", FakeStaticDir())

    first = await client.get("/")
    second = await client.get("/")

    assert first.status_code == 200
    assert "--crust:" in first.text
    assert "/*__THEME_VARS__*/" not in first.text
    assert second.text == first.text
    assert reads == 1


@pytest.mark.asyncio
async def test_get_cards(client):
    resp = await client.get("/api/cards")
    assert resp.status_code == 200
    cards = resp.json()
    assert isinstance(cards, list)
    assert len(cards) == 78


@pytest.mark.asyncio
async def test_get_spreads(client):
    resp = await client.get("/api/spreads")
    assert resp.status_code == 200
    spreads = resp.json()
    assert isinstance(spreads, list)
    assert len(spreads) >= 3


@pytest.mark.asyncio
async def test_get_theme(client):
    resp = await client.get("/api/theme")
    assert resp.status_code == 200
    theme = resp.json()
    assert "crust" in theme
    assert "text" in theme
    assert len(theme) == 14


@pytest.mark.asyncio
async def test_get_strings(client):
    resp = await client.get("/api/strings")
    assert resp.status_code == 200
    strings = resp.json()
    assert isinstance(strings, dict)
    assert "arcana_labels" in strings


# -- POST endpoints --


@pytest.mark.asyncio
async def test_save_config(client):
    resp = await client.post(
        "/api/config",
        json={
            "api_url": "https://api.test.com/v1",
            "api_key": "sk-new",
            "model": "gpt-4",
            "lang": "en",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["model"] == "gpt-4"


@pytest.mark.asyncio
async def test_save_config_invalid_lang(client):
    resp = await client.post(
        "/api/config",
        json={
            "api_url": "https://api.test.com/v1",
            "api_key": "sk-new",
            "model": "gpt-4",
            "lang": "xx",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_save_config_invalid_api_url(client):
    resp = await client.post(
        "/api/config",
        json={
            "api_url": "ftp://api.test.com/v1",
            "api_key": "sk-new",
            "model": "gpt-4",
            "lang": "en",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_interpret_invalid_card_id_returns_422(client):
    resp = await client.post(
        "/api/interpret",
        json={
            "question": "What should I know?",
            "cards": [
                {
                    "card_id": "missing",
                    "position_name": "Present",
                    "is_reversed": False,
                }
            ],
        },
    )
    assert resp.status_code == 422
    assert "Invalid card IDs" in resp.text


@pytest.mark.asyncio
async def test_export_image(client):
    resp = await client.post(
        "/api/export-image",
        json={
            "text": "# Test\nHello world",
            "cards": [],
            "question": "Test question",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_interpret_stream_success(client, monkeypatch):
    monkeypatch.setattr(
        "nekomata.web.server.get_interpreter",
        lambda config: _FakeInterpreter(
            [
                StreamChunk("thinking", "thinking"),
                StreamChunk("answer", "content"),
            ]
        ),
    )
    resp = await client.post(
        "/api/interpret",
        json={
            "question": "What should I know?",
            "spread_key": "single",
            "cards": [await _valid_card_payload(client)],
        },
    )

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    events = _sse_events(resp)
    assert events[0]["messages"][0]["role"] == "system"
    assert {"text": "thinking", "kind": "thinking"} in events
    assert {"text": "answer", "kind": "content"} in events
    assert events[-1] == "[DONE]"


@pytest.mark.asyncio
async def test_interpret_stream_no_valid_cards(client, monkeypatch):
    monkeypatch.setattr("nekomata.web.server._resolve_drawn_cards", lambda cards, cards_by_id: [])

    resp = await client.post(
        "/api/interpret",
        json={
            "question": "What should I know?",
            "cards": [await _valid_card_payload(client)],
        },
    )

    assert _sse_events(resp) == [{"error": "No valid cards provided", "config_error": False}]


@pytest.mark.asyncio
async def test_interpret_stream_config_error(client, monkeypatch):
    monkeypatch.setattr(
        "nekomata.web.server.get_interpreter",
        lambda config: (_ for _ in ()).throw(InterpretationError("missing key", config_error=True)),
    )

    resp = await client.post(
        "/api/interpret",
        json={
            "question": "What should I know?",
            "cards": [await _valid_card_payload(client)],
        },
    )

    assert _sse_events(resp) == [{"error": "missing key", "config_error": True}]


@pytest.mark.asyncio
async def test_interpret_stream_interpretation_error(client, monkeypatch):
    monkeypatch.setattr(
        "nekomata.web.server.get_interpreter",
        lambda config: _FakeInterpreter(error=InterpretationError("provider failed", config_error=False)),
    )

    resp = await client.post(
        "/api/interpret",
        json={
            "question": "What should I know?",
            "cards": [await _valid_card_payload(client)],
        },
    )

    assert _sse_events(resp)[-1] == {"error": "provider failed", "config_error": False}


@pytest.mark.asyncio
async def test_interpret_stream_unexpected_error(client, monkeypatch):
    monkeypatch.setattr(
        "nekomata.web.server.get_interpreter",
        lambda config: _FakeInterpreter(error=RuntimeError("boom")),
    )

    resp = await client.post(
        "/api/interpret",
        json={
            "question": "What should I know?",
            "cards": [await _valid_card_payload(client)],
        },
    )

    assert _sse_events(resp)[-1] == {"error": "Interpretation failed: boom"}


@pytest.mark.asyncio
async def test_followup_stream_success(client, monkeypatch):
    monkeypatch.setattr(
        "nekomata.web.server.get_interpreter",
        lambda config: _FakeInterpreter(raw_chunks=[StreamChunk("follow-up", "content")]),
    )

    resp = await client.post(
        "/api/interpret/followup",
        json={
            "question": "Can you clarify?",
            "messages": [{"role": "assistant", "content": "Initial answer"}],
        },
    )

    assert _sse_events(resp) == [{"text": "follow-up", "kind": "content"}, "[DONE]"]


@pytest.mark.asyncio
async def test_followup_stream_errors(client, monkeypatch):
    monkeypatch.setattr(
        "nekomata.web.server.get_interpreter",
        lambda config: _FakeInterpreter(raw_error=InterpretationError("follow-up failed", config_error=True)),
    )

    resp = await client.post(
        "/api/interpret/followup",
        json={
            "question": "Can you clarify?",
            "messages": [{"role": "assistant", "content": "Initial answer"}],
        },
    )

    assert _sse_events(resp) == [{"error": "follow-up failed", "config_error": True}]


@pytest.mark.asyncio
async def test_followup_stream_config_error(client, monkeypatch):
    monkeypatch.setattr(
        "nekomata.web.server.get_interpreter",
        lambda config: (_ for _ in ()).throw(InterpretationError("missing key", config_error=True)),
    )

    resp = await client.post(
        "/api/interpret/followup",
        json={
            "question": "Can you clarify?",
            "messages": [{"role": "assistant", "content": "Initial answer"}],
        },
    )

    assert _sse_events(resp) == [{"error": "missing key", "config_error": True}]


@pytest.mark.asyncio
async def test_followup_stream_unexpected_error(client, monkeypatch):
    monkeypatch.setattr(
        "nekomata.web.server.get_interpreter",
        lambda config: _FakeInterpreter(raw_error=RuntimeError("boom")),
    )

    resp = await client.post(
        "/api/interpret/followup",
        json={
            "question": "Can you clarify?",
            "messages": [{"role": "assistant", "content": "Initial answer"}],
        },
    )

    assert _sse_events(resp) == [{"error": "Interpretation failed: boom"}]
