import json
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def _ensure_config(request, tmp_path: Path, monkeypatch):
    """Create a dummy settings file so SetupScreen is not shown during tests.

    Skipped for test_config.py which manages its own config files.
    """
    if "test_config" in request.node.nodeid or "test_renderer" in request.node.nodeid:
        yield
        return
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps({"api_url": "https://api.openai.com/v1", "api_key": "sk-test", "model": "glm-4-flash"}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    yield
