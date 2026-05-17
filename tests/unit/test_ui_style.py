"""Style consistency checks for the Textual UI."""

import re

from nekomata.app import NekomataApp
from nekomata.render.themes import THEMES
from nekomata.screens.card_browser import CardBrowserScreen, CardListItem
from nekomata.screens.home import HomeScreen
from nekomata.screens.interpretation import InterpretationScreen
from nekomata.screens.reading import CardWidget, ReadingScreen
from nekomata.screens.spread_select import SpreadSelectScreen


CSS_SOURCES = [
    NekomataApp.DEFAULT_CSS,
    HomeScreen.DEFAULT_CSS,
    SpreadSelectScreen.DEFAULT_CSS,
    ReadingScreen.DEFAULT_CSS,
    CardWidget.DEFAULT_CSS,
    InterpretationScreen.DEFAULT_CSS,
    CardBrowserScreen.DEFAULT_CSS,
    CardListItem.DEFAULT_CSS,
]

CATPPUCCIN_MOCHA = {
    "#11111b",  # crust
    "#181825",  # mantle
    "#1e1e2e",  # base
    "#313244",  # surface0
    "#45475a",  # surface1
    "#585b70",  # surface2
    "#6c7086",  # overlay0
    "#a6adc8",  # subtext0
    "#bac2de",  # subtext1
    "#cdd6f4",  # text
    "#cba6f7",  # mauve
    "#b4befe",  # lavender
    "#f38ba8",  # red
}


def test_ui_css_uses_only_catppuccin_mocha_colors():
    colors = {
        color.lower()
        for css in CSS_SOURCES
        for color in re.findall(r"#[0-9a-fA-F]{6}", css)
    }

    assert colors <= CATPPUCCIN_MOCHA


def test_ui_css_uses_soft_round_borders():
    combined = "\n".join(CSS_SOURCES)

    assert "border: tall" not in combined
    assert "border: double" not in combined
    assert "border-left:" not in combined


def test_card_rendering_catppuccin_theme_uses_purple_accents():
    theme = THEMES["catppuccin"]

    assert theme.upright_border == "#cba6f7"
    assert theme.reversed_border == "#b4befe"
    assert theme.title_style == "bold #b4befe"
    assert theme.keyword_style == "bold #cba6f7"
