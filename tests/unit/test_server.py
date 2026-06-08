"""Unit tests for web/server.py — API endpoint tests using httpx AsyncClient."""

import pytest

from nekomata.web.server import create_app

pytestmark = pytest.mark.skip_config_fixture


@pytest.fixture()
def _config(tmp_path, monkeypatch):
    """Create a settings file so AppConfig.load() works."""
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(
        '{"api_url":"http://localhost:1234","api_key":"sk-test-key","model":"test-model","lang":"en"}'
    )
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


# -- GET endpoints --


@pytest.mark.asyncio
async def test_get_config(client):
    resp = await client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_api_key"] is True
    assert data["model"] == "test-model"


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
    resp = await client.post("/api/config", json={
        "api_url": "https://api.test.com/v1",
        "api_key": "sk-new",
        "model": "gpt-4",
        "lang": "en",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["model"] == "gpt-4"


@pytest.mark.asyncio
async def test_save_config_invalid_lang(client):
    resp = await client.post("/api/config", json={
        "api_url": "https://api.test.com/v1",
        "api_key": "sk-new",
        "model": "gpt-4",
        "lang": "xx",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_export_image(client):
    resp = await client.post("/api/export-image", json={
        "text": "# Test\nHello world",
        "cards": [],
        "question": "Test question",
    })
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert len(resp.content) > 0
