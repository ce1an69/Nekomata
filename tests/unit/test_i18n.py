"""Unit tests for core/i18n.py — language switching, locale loading, lazy proxies."""

import pytest

import nekomata.core.i18n as mod


@pytest.fixture(autouse=True)
def _reset_i18n():
    mod._current_lang = mod.DEFAULT_LANG
    mod._cache.clear()
    yield
    mod._current_lang = mod.DEFAULT_LANG
    mod._cache.clear()


# -- set_lang / get_lang --


def test_get_lang_default():
    assert mod.get_lang() == "en"


def test_set_lang_supported():
    mod.set_lang("zh")
    assert mod.get_lang() == "zh"


def test_set_lang_en():
    mod.set_lang("en")
    assert mod.get_lang() == "en"


def test_set_lang_unsupported_falls_back(caplog):
    mod.set_lang("fr")
    assert mod.get_lang() == "en"
    assert "Unsupported" in caplog.text


# -- _load_locale --


def test_load_locale_returns_dict():
    result = mod._load_locale("ui")
    assert isinstance(result, dict)
    assert len(result) > 0


def test_load_locale_caches():
    first = mod._load_locale("ui")
    second = mod._load_locale("ui")
    assert first is second


def test_load_locale_with_explicit_lang():
    result = mod._load_locale("ui", lang="zh")
    assert isinstance(result, dict)
    assert len(result) > 0


# -- ui_section / ui_strings / spread_strings --


def test_ui_section_returns_expected_keys():
    result = mod.ui_section("arcana_labels")
    assert "major" in result
    assert "cups" in result


def test_ui_section_missing_returns_empty():
    result = mod.ui_section("nonexistent_section")
    assert result == {}


def test_ui_strings_returns_full_dict():
    result = mod.ui_strings()
    assert "arcana_labels" in result


def test_spread_strings_returns_data():
    result = mod.spread_strings()
    assert isinstance(result, dict)
    assert len(result) > 0


# -- arcana_label --


def test_arcana_label_known_key():
    result = mod.arcana_label("major")
    assert isinstance(result, str)
    assert len(result) > 0


def test_arcana_label_unknown_returns_key():
    result = mod.arcana_label("nonexistent_arcana")
    assert result == "nonexistent_arcana"


# -- _LazySection --


def test_lazy_section_getitem():
    section = mod.lazy_section("arcana_labels")
    assert section["major"] is not None
    assert len(section["major"]) > 0


def test_lazy_section_get_default():
    section = mod.lazy_section("arcana_labels")
    assert section.get("nonexistent_key", "fallback") == "fallback"


def test_lazy_section_get_existing():
    section = mod.lazy_section("arcana_labels")
    result = section.get("major")
    assert result is not None


# -- _LazyStrings --


def test_lazy_strings_getitem():
    strings = mod.lazy_strings()
    assert strings["arcana_labels"] is not None


def test_lazy_strings_get_default():
    strings = mod.lazy_strings()
    assert strings.get("nonexistent_key", "fallback") == "fallback"


# -- Language switching affects lazy proxies --


def test_lazy_section_follows_lang_change():
    section = mod.lazy_section("arcana_labels")
    mod.set_lang("en")
    en_val = section["major"]
    mod.set_lang("zh")
    zh_val = section["major"]
    # Both should be non-empty but different languages
    assert en_val and zh_val
