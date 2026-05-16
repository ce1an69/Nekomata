from nekomata.render.themes import get_theme, CardTheme, THEMES


def test_default_theme():
    theme = get_theme()
    assert theme.upright_border == "yellow"
    assert theme.reversed_border == "blue"


def test_dark_theme():
    theme = get_theme("dark")
    assert isinstance(theme, CardTheme)


def test_light_theme():
    theme = get_theme("light")
    assert theme.upright_border == "bright_yellow"


def test_cat_theme():
    theme = get_theme("cat")
    assert theme.upright_border == "color(180)"


def test_unknown_theme_fallback():
    theme = get_theme("nonexistent")
    assert theme == THEMES["dark"]


def test_all_themes_have_required_fields():
    for name, theme in THEMES.items():
        assert theme.upright_border
        assert theme.reversed_border
        assert theme.summary_border
