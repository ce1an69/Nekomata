"""Style consistency checks for the Textual UI."""

import inspect
import re

from nekomata.app import NekomataApp
from nekomata.render.themes import THEMES
from nekomata.screens.card_browser import CardBrowserScreen, CardListItem
from nekomata.screens.draw import (
    ConfirmExitInterpretation,
    DETAIL_PANEL_WIDTH,
    INTERP_FULL_SIDE_MARGIN,
    INTERP_FULL_WIDTH_CORRECTION,
    INTERP_MAX_HEIGHT,
    INTERP_MIN_HEIGHT,
    INTERP_PANEL_HEIGHT,
    DeckCard,
    DrawScreen,
    SpreadSlot,
)
from nekomata.screens.home import HomeScreen
from nekomata.screens.interpretation import InterpretationScreen
from nekomata.screens.reading import CardWidget, ReadingScreen
from nekomata.screens.setup import SetupButton, SetupScreen
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
    DeckCard.DEFAULT_CSS,
    SpreadSlot.DEFAULT_CSS,
    DrawScreen.DEFAULT_CSS,
    ConfirmExitInterpretation.DEFAULT_CSS,
    SetupButton.DEFAULT_CSS,
    SetupScreen.DEFAULT_CSS,
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
    "#f5c2e7",  # pink
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


def test_setup_hints_do_not_advertise_q_quit():
    assert "Q quit" not in SetupScreen.compose.__code__.co_consts


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


def test_draw_detail_panel_docks_to_right_full_height():
    css = DrawScreen.DEFAULT_CSS

    detail_css = css.split("#card-preview {")[1].split("}")[0]
    assert "dock: right;" in detail_css
    assert f"width: {DETAIL_PANEL_WIDTH};" in detail_css
    assert f"min-width: {DETAIL_PANEL_WIDTH};" in detail_css
    assert "height: 100%;" in detail_css
    assert "transition: opacity 240ms" in detail_css
    assert "offset 320ms" in detail_css


def test_draw_interpretation_panel_fills_bottom_flow_space():
    css = DrawScreen.DEFAULT_CSS

    interp_css = css.split("#interp-dialog {")[1].split("}")[0]
    content_css = css.split("#interp-dialog-content {")[1].split("}")[0]
    assert "dock: bottom;" in interp_css
    assert "width: 1fr;" in interp_css
    assert f"height: {INTERP_PANEL_HEIGHT};" in interp_css
    assert f"min-height: {INTERP_MIN_HEIGHT};" in interp_css
    assert f"max-height: {INTERP_MAX_HEIGHT};" in interp_css
    assert "transition: opacity 240ms" in interp_css
    assert "width 220ms" in interp_css
    assert "height: 1fr;" not in content_css


def test_draw_interpretation_panel_width_tracks_detail_space():
    source = inspect.getsource(DrawScreen._sync_interp_layout)

    assert "dialog.styles.width = max(" in source
    assert "self.size.width" in source
    assert "DETAIL_PANEL_WIDTH" in source
    assert "INTERP_FULL_SIDE_MARGIN * 2" in source
    assert "INTERP_FULL_WIDTH_CORRECTION" in source


def test_draw_hiding_detail_recenters_spread_area():
    source = inspect.getsource(DrawScreen._hide_detail_panel)
    finish_source = inspect.getsource(DrawScreen._finish_hide_detail_panel)

    assert "_center_spread_area" in source
    assert "preview.display = False" in finish_source
    assert "_center_spread_area" in finish_source
    assert INTERP_FULL_SIDE_MARGIN > 1
    assert INTERP_FULL_WIDTH_CORRECTION >= 4


def test_draw_stream_uses_app_thread_callback():
    source = inspect.getsource(DrawScreen._run_interpretation)

    assert "self.app.call_from_thread" in source


def test_draw_interpretation_panel_uses_arrow_scroll():
    up_source = inspect.getsource(DrawScreen.key_up)
    down_source = inspect.getsource(DrawScreen.key_down)

    assert "interp" in up_source
    assert "scroll_up(animate=True)" in up_source
    assert "interp" in down_source
    assert "scroll_down(animate=True)" in down_source


def test_draw_stream_content_renders_markdown():
    source = inspect.getsource(DrawScreen._render_stream_content)

    assert "Markdown(self._stream_thinking_text" in source
    assert "Markdown(self._stream_content_text" in source
    assert "Group(*parts)" in source


def test_interpretation_exit_confirm_uses_catppuccin_modal():
    css = ConfirmExitInterpretation.DEFAULT_CSS
    source = inspect.getsource(DrawScreen.action_handle_back)

    assert "ConfirmExitInterpretation" in source
    assert "callback=self._on_exit_interpretation_confirmed" in source
    assert "border: round #cba6f7" in css
    assert "background: #181825" in css
    assert "#confirm-hint" in css
    assert "transition: opacity 220ms" in css


def test_interpretation_exit_confirm_animates_in():
    source = inspect.getsource(ConfirmExitInterpretation.on_mount)

    assert "styles.animate" in source
    assert "ScalarOffset.from_offset" in source


def test_draw_recentering_spread_uses_animation():
    source = inspect.getsource(DrawScreen._center_spread_area)

    assert "styles.animate" in source
    assert "duration=0.22" in source
