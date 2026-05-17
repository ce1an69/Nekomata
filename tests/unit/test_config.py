from pathlib import Path

from nekomata.storage.config import AppConfig


def test_default_config():
    config = AppConfig()
    assert config.ai_backend == "template"
    assert config.display_animation is True
    assert config.display_theme == "catppuccin"
    assert config.reversal_prob == 0.5


def test_load_from_file(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        '[ai]\nbackend = "openai_compatible"\nmodel = "gpt-4"\n\n'
        '[display]\nanimation = false\n'
        "[reversal]\nprobability = 0.3\n",
        encoding="utf-8",
    )
    config = AppConfig.load(config_file)
    assert config.ai_backend == "openai_compatible"
    assert config.ai_model == "gpt-4"
    assert config.display_animation is False
    assert config.reversal_prob == 0.3


def test_load_missing_file_uses_defaults(tmp_path: Path):
    config = AppConfig.load(tmp_path / "nonexistent.toml")
    assert config.ai_backend == "template"
    assert config.display_theme == "catppuccin"


def test_load_partial_config(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('[ai]\nbackend = "openai_compatible"\n', encoding="utf-8")
    config = AppConfig.load(config_file)
    assert config.ai_backend == "openai_compatible"
    assert config.display_animation is True
    assert config.display_theme == "catppuccin"


def test_reversal_prob_clamped_high(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("[reversal]\nprobability = 2.0\n", encoding="utf-8")
    config = AppConfig.load(config_file)
    assert config.reversal_prob == 1.0


def test_reversal_prob_clamped_low(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("[reversal]\nprobability = -0.5\n", encoding="utf-8")
    config = AppConfig.load(config_file)
    assert config.reversal_prob == 0.0


def test_load_ignores_unknown_keys(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        '[ai]\nbackend = "template"\nunknown_key = "value"\n',
        encoding="utf-8",
    )
    config = AppConfig.load(config_file)
    assert config.ai_backend == "template"


def test_load_malformed_toml_uses_defaults(tmp_path: Path):
    """Malformed TOML falls back to defaults instead of crashing."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("[ai\nbackend = invalid", encoding="utf-8")
    config = AppConfig.load(config_file)
    assert config.ai_backend == "template"
    assert config.display_animation is True


def test_empty_api_key_normalized_to_none(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('[ai]\napi_key = ""\n', encoding="utf-8")
    config = AppConfig.load(config_file)
    assert config.ai_api_key is None


def test_whitespace_api_key_normalized_to_none(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('[ai]\napi_key = "   "\n', encoding="utf-8")
    config = AppConfig.load(config_file)
    assert config.ai_api_key is None


def test_real_api_key_preserved(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('[ai]\napi_key = "sk-test-real"\n', encoding="utf-8")
    config = AppConfig.load(config_file)
    assert config.ai_api_key == "sk-test-real"
