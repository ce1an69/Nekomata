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


def test_home_suggestion_panel_can_animate_out():
    names = HomeScreen._hide_suggestions.__code__.co_names

    assert "animate" in names
    assert "_finish_hide_suggestions" in names


def test_card_browser_list_and_detail_have_swap_transitions():
    css = CardBrowserScreen.DEFAULT_CSS

    card_list_css = css.split("CardBrowserScreen #card-list {")[1].split("}")[0]
    detail_css = css.split("CardBrowserScreen #card-detail {")[1].split("}")[0]
    assert "transition: opacity 220ms" in card_list_css
    assert "transition: opacity 250ms" in detail_css


def test_interpretation_manual_scroll_uses_animation():
    for method in (
        InterpretationScreen.key_down,
        InterpretationScreen.key_up,
        InterpretationScreen.key_right,
        InterpretationScreen.key_left,
    ):
        assert True in method.__code__.co_consts


def test_interpretation_offset_animation_uses_scalar_offset():
    from nekomata.screens import interpretation

    assert "ScalarOffset" in interpretation._ease_in.__code__.co_names
    assert "Offset" in interpretation._ease_in.__code__.co_names
