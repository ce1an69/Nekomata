from nekomata.render.themes import get_theme, CardTheme, THEMES, set_default_theme


def test_default_theme():
    theme = get_theme()
    assert theme == THEMES["catppuccin"]


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
    assert theme == THEMES["catppuccin"]


def test_all_themes_have_required_fields():
    for name, theme in THEMES.items():
        assert theme.upright_border
        assert theme.reversed_border


def test_set_default_theme():
    set_default_theme("dark")
    assert get_theme() == THEMES["dark"]
    set_default_theme("catppuccin")  # restore


def test_set_default_theme_ignores_unknown():
    set_default_theme("nonexistent")
    assert get_theme() == THEMES["catppuccin"]
