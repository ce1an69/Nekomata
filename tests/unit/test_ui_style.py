"""Style consistency checks for the Textual UI."""

import inspect
import re

from nekomata.app import NekomataApp
from nekomata.render.themes import THEMES
from nekomata.render.styles import (
    C_CRUST,
    C_LAVENDER,
    C_MANTLE,
    C_MAUVE,
    C_OVERLAY0,
    C_PINK,
    C_RED,
    C_SUBTEXT0,
    C_SUBTEXT1,
    C_SURFACE0,
    C_SURFACE1,
    C_SURFACE2,
    C_TEXT,
)
from nekomata.screens.card_browser import CardBrowserScreen, CardListItem
from nekomata.screens.draw import DrawScreen
from nekomata.screens.draw_widgets import (
    ConfirmExitInterpretation,
    DeckCard,
    SpreadSlot,
)
from nekomata.screens.home import HomeScreen
from nekomata.screens.setup import SetupButton, SetupScreen
from nekomata.screens.spread_select import SpreadSelectScreen


CSS_SOURCES = [
    NekomataApp.DEFAULT_CSS,
    HomeScreen.DEFAULT_CSS,
    SpreadSelectScreen.DEFAULT_CSS,
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
    C_CRUST,
    C_MANTLE,
    "#1e1e2e",  # base
    C_SURFACE0,
    C_SURFACE1,
    C_SURFACE2,
    C_OVERLAY0,
    C_SUBTEXT0,
    C_SUBTEXT1,
    C_TEXT,
    C_MAUVE,
    C_LAVENDER,
    C_PINK,
    C_RED,
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

    assert theme.upright_border == C_MAUVE
    assert theme.reversed_border == C_LAVENDER
    assert theme.title_style == f"bold {C_LAVENDER}"
    assert theme.keyword_style == f"bold {C_MAUVE}"


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


def test_draw_detail_panel_docks_to_right_full_height():
    css = DrawScreen.DEFAULT_CSS

    detail_css = css.split("#card-preview {")[1].split("}")[0]
    assert "dock: right;" in detail_css
    assert "height: 1fr;" in detail_css
    assert "transition: opacity 240ms" in detail_css
    assert "offset 320ms" in detail_css


def test_draw_interpretation_panel_fills_bottom_flow_space():
    css = DrawScreen.DEFAULT_CSS

    interp_css = css.split("#interp-dialog {")[1].split("}")[0]
    content_css = css.split("#interp-dialog-content {")[1].split("}")[0]
    assert "dock: bottom;" in interp_css
    assert "width: 1fr;" in interp_css
    assert "transition: opacity 240ms" in interp_css
    assert "width 220ms" in interp_css
    assert "height: 1fr;" not in content_css


def test_draw_interpretation_panel_width_tracks_detail_space():
    from nekomata.screens.draw_dialog import InterpretationDialog
    source = inspect.getsource(InterpretationDialog.sync_layout)

    assert "styles.width = max(" in source
    assert "screen_width" in source
    assert "DETAIL_PANEL_WIDTH" in source
    assert "INTERP_FULL_SIDE_MARGIN * 2" in source
    assert "INTERP_FULL_WIDTH_CORRECTION" in source


def test_draw_hiding_detail_recenters_spread_area():
    from nekomata.screens.draw_detail import DetailPanel
    source = inspect.getsource(DetailPanel.hide)
    finish_source = inspect.getsource(DetailPanel._finish_hide)

    assert "center_spread" in source
    assert "display = False" in finish_source


def test_draw_stream_uses_app_thread_callback():
    from nekomata.screens.stream_handler import StreamHandler
    source = inspect.getsource(StreamHandler.run)

    assert "call_from_thread" in source


def test_draw_interpretation_panel_uses_arrow_scroll():
    up_source = inspect.getsource(DrawScreen.key_up)
    down_source = inspect.getsource(DrawScreen.key_down)

    assert "interp" in up_source
    assert "scroll_up(animate=True)" in up_source
    assert "interp" in down_source
    assert "scroll_down(animate=True)" in down_source


def test_draw_stream_content_renders_markdown():
    from nekomata.screens.stream_handler import StreamHandler
    source = inspect.getsource(StreamHandler._render)

    assert 'Markdown("".join(self._content_chars)' in source
    assert "C_MAUVE" in source
    assert "self._render_content(parts)" in source


def test_draw_loading_hint_rotates_cat_tarot_messages():
    from nekomata.screens import stream_handler
    from nekomata.i18n import ui_strings
    source = inspect.getsource(stream_handler.StreamHandler._tick_loading)

    assert "模型正在解读" not in source
    assert "_LOADING_MESSAGE_INTERVAL" in source
    assert stream_handler._LOADING_MESSAGE_INTERVAL == 2.0
    messages = ui_strings()["loading_messages"]
    assert len(messages) >= 3
    assert any("cat" in message.lower() for message in messages)


def test_interpretation_exit_confirm_uses_catppuccin_modal():
    css = ConfirmExitInterpretation.DEFAULT_CSS
    source = inspect.getsource(DrawScreen.action_handle_back)

    assert "ConfirmExitInterpretation" in source
    assert "callback=on_confirm" in source
    assert f"background: {C_CRUST};" in css
    assert "background: #11111b 70%" not in css
    assert f"border: round {C_MAUVE}" in css
    assert f"background: {C_MANTLE}" in css
    assert "#confirm-content" in css
    assert "transition: opacity 220ms" in css


def test_interpretation_exit_confirm_animates_in():
    source = inspect.getsource(ConfirmExitInterpretation.on_mount)

    assert "animate_entrance" in source


def test_draw_recentering_spread_uses_animation():
    source = inspect.getsource(DrawScreen._center_spread_area)

    assert "styles.animate" in source
    assert "duration=0.22" in source
