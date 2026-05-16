from pathlib import Path

from nekomata.storage.config import AppConfig


def test_default_config():
    config = AppConfig()
    assert config.ai_backend == "template"
    assert config.display_animation is True
    assert config.reversal_prob == 0.5


def test_load_from_file(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        '[ai]\nbackend = "ollama"\nmodel = "llama3"\n\n'
        '[display]\nanimation = false\n'
        "[reversal]\nprobability = 0.3\n",
        encoding="utf-8",
    )
    config = AppConfig.load(config_file)
    assert config.ai_backend == "ollama"
    assert config.ai_model == "llama3"
    assert config.display_animation is False
    assert config.reversal_prob == 0.3


def test_load_missing_file_uses_defaults(tmp_path: Path):
    config = AppConfig.load(tmp_path / "nonexistent.toml")
    assert config.ai_backend == "template"


def test_load_partial_config(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('[ai]\nbackend = "openai_compatible"\n', encoding="utf-8")
    config = AppConfig.load(config_file)
    assert config.ai_backend == "openai_compatible"
    assert config.display_animation is True
