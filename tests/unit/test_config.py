import json
from pathlib import Path

from nekomata.storage.config import AppConfig


def test_default_config():
    config = AppConfig()
    assert config.api_url == ""
    assert config.api_key is None
    assert config.model == ""


def test_load_from_local_file(tmp_path: Path, monkeypatch):
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps({"api_url": "http://localhost:11434/v1", "api_key": "sk-test"}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    config = AppConfig.load()
    assert config.api_url == "http://localhost:11434/v1"
    assert config.api_key == "sk-test"


def test_load_from_user_home(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    settings = home_dir / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps({"api_url": "http://home:11434/v1", "api_key": "sk-home"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: home_dir)
    config = AppConfig.load()
    assert config.api_url == "http://home:11434/v1"
    assert config.api_key == "sk-home"


def test_local_takes_priority_over_home(tmp_path: Path, monkeypatch):
    local_dir = tmp_path / "project"
    local_dir.mkdir()
    local_settings = local_dir / ".neko" / "settings.json"
    local_settings.parent.mkdir(parents=True)
    local_settings.write_text(
        json.dumps({"api_url": "http://local:11434/v1", "api_key": "sk-local"}),
        encoding="utf-8",
    )

    home_dir = tmp_path / "home"
    home_dir.mkdir()
    home_settings = home_dir / ".neko" / "settings.json"
    home_settings.parent.mkdir(parents=True)
    home_settings.write_text(
        json.dumps({"api_url": "http://home:11434/v1", "api_key": "sk-home"}),
        encoding="utf-8",
    )

    monkeypatch.chdir(local_dir)
    monkeypatch.setattr(Path, "home", lambda: home_dir)
    config = AppConfig.load()
    assert config.api_url == "http://local:11434/v1"
    assert config.api_key == "sk-local"


def test_missing_file_uses_defaults(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "nonexistent")
    config = AppConfig.load()
    assert config.api_url == ""
    assert config.api_key is None


def test_partial_config(tmp_path: Path, monkeypatch):
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"api_key": "sk-test"}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    config = AppConfig.load()
    assert config.api_url == ""
    assert config.api_key == "sk-test"


def test_load_ignores_unknown_keys(tmp_path: Path, monkeypatch):
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps({"api_url": "http://test/v1", "unknown": "value"}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    config = AppConfig.load()
    assert config.api_url == "http://test/v1"


def test_malformed_json_uses_defaults(tmp_path: Path, monkeypatch):
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text("{invalid json", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    config = AppConfig.load()
    assert config.api_url == ""


def test_empty_api_key_normalized_to_none(tmp_path: Path, monkeypatch):
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"api_key": ""}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    config = AppConfig.load()
    assert config.api_key is None


def test_whitespace_api_key_normalized_to_none(tmp_path: Path, monkeypatch):
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"api_key": "   "}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    config = AppConfig.load()
    assert config.api_key is None


def test_real_api_key_preserved(tmp_path: Path, monkeypatch):
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"api_key": "sk-test-real"}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    config = AppConfig.load()
    assert config.api_key == "sk-test-real"


def test_non_dict_json_uses_defaults(tmp_path: Path, monkeypatch):
    settings = tmp_path / ".neko" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text('["not", "a", "dict"]', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    config = AppConfig.load()
    assert config.api_url == ""


def test_save_creates_in_home_when_no_local(tmp_path: Path, monkeypatch):
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    config = AppConfig.save("http://test/v1", "sk-new", "model-a")
    assert config.api_url == "http://test/v1"
    assert config.api_key == "sk-new"
    assert config.model == "model-a"

    saved = home_dir / ".neko" / "settings.json"
    assert saved.exists()
    data = json.loads(saved.read_text(encoding="utf-8"))
    assert data["api_url"] == "http://test/v1"


def test_save_writes_to_local_when_exists(tmp_path: Path, monkeypatch):
    local_dir = tmp_path / "project"
    local_dir.mkdir()
    local_settings = local_dir / ".neko" / "settings.json"
    local_settings.parent.mkdir(parents=True)
    local_settings.write_text(json.dumps({"api_url": "http://old/v1"}), encoding="utf-8")

    home_dir = tmp_path / "home"
    home_dir.mkdir()

    monkeypatch.chdir(local_dir)
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    AppConfig.save("http://new/v1", "sk-key", "model-b")

    assert local_settings.exists()
    data = json.loads(local_settings.read_text(encoding="utf-8"))
    assert data["api_url"] == "http://new/v1"

    home_settings = home_dir / ".neko" / "settings.json"
    assert not home_settings.exists()
