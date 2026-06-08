import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _ensure_config(request, tmp_path: Path, monkeypatch):
    """Create a dummy settings file so SetupScreen is not shown during tests.

    Skipped for tests marked with @pytest.mark.skip_config_fixture.
    """
    if request.node.get_closest_marker("skip_config_fixture"):
        yield
        return
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(
        json.dumps({"api_url": "https://api.openai.com/v1", "api_key": "sk-test", "model": "glm-4-flash"}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    yield
