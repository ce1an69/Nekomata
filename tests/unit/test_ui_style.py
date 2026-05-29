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
from nekomata.screens.solid_static import SolidStatic
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


def test_solid_static_paints_full_line_with_current_css_style():
    render_source = inspect.getsource(SolidStatic.render)
    pad_source = inspect.getsource(SolidStatic._padded_content)

    assert "self.rich_style" in render_source
    assert "self.content_size.width" in pad_source


def test_setup_and_spread_static_headers_use_solid_static_lines():
    setup_source = inspect.getsource(SetupScreen.compose)
    spread_source = inspect.getsource(SpreadSelectScreen.compose)

    assert "SolidStatic" in setup_source
    assert "id=\"setup-title\"" in setup_source
    assert "SetupButton(_STR[\"save_label\"]" in setup_source
    assert "SolidStatic(question" in spread_source


def test_setup_language_select_has_no_blank_prompt_and_uses_local_style():
    css = SetupScreen.DEFAULT_CSS
    source = inspect.getsource(SetupScreen.compose)

    assert "allow_blank=False" in source
    assert "SetupScreen #lang-select > SelectCurrent" in css
    assert "SetupScreen #lang-select > SelectOverlay" in css
    assert ".option-list--option-highlighted" in css


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
    assert "transition: opacity 280ms" in detail_css
    assert "offset 340ms" in detail_css


def test_draw_interpretation_panel_fills_bottom_flow_space():
    css = DrawScreen.DEFAULT_CSS

    interp_css = css.split("#interp-dialog {")[1].split("}")[0]
    content_css = css.split("#interp-dialog-content {")[1].split("}")[0]
    assert "dock: bottom;" in interp_css
    assert "width: 1fr;" in interp_css
    assert "transition: width 300ms" in interp_css
    assert "transition: opacity" not in interp_css
    assert "offset 340ms" not in interp_css
    assert "width 300ms" in interp_css
    assert "height: 1fr;" not in content_css


def test_draw_interpretation_panel_width_tracks_detail_space():
    from nekomata.screens.draw_dialog import InterpretationDialog
    source = inspect.getsource(InterpretationDialog.sync_layout)

    assert "styles.width = max(" in source
    assert "screen_width" in source
    assert "DETAIL_PANEL_WIDTH" in source
    assert "INTERP_FULL_SIDE_MARGIN * 2" in source
    assert "INTERP_FULL_WIDTH_CORRECTION" in source


def test_draw_interpretation_height_animation_starts_from_cell_height():
    from nekomata.screens.draw_dialog import InterpretationDialog

    class FakeStyles:
        def __init__(self):
            self.height = None
            self.animation = None

        def animate(self, attr, value, duration, easing):
            self.animation = (attr, value, duration, easing)

    class FakeWidget:
        def __init__(self):
            self.styles = FakeStyles()

    class FakeApp:
        animation_enabled = True

    class FakeScreen:
        app = FakeApp()

        def set_timer(self, *_args, **_kwargs):
            return None

    dialog = InterpretationDialog.__new__(InterpretationDialog)
    dialog._height_timers = []
    dialog._screen = FakeScreen()
    dialog._w_interp = FakeWidget()

    dialog._animate_interp_height(28, 14)

    assert dialog._w_interp.styles.height == 28
    assert dialog._w_interp.styles.animation[0:2] == ("height", 14)


def test_draw_fullscreen_height_animation_uses_cell_heights():
    from nekomata.screens.draw_dialog import InterpretationDialog

    source = inspect.getsource(InterpretationDialog.toggle_fullscreen)

    assert "self._panel_height_cells()" in source
    assert 'INTERP_PANEL_HEIGHT,' not in source


def test_draw_hiding_fullscreen_interpretation_restores_layout_after_animation():
    from nekomata.screens.draw_dialog import InterpretationDialog

    source = inspect.getsource(InterpretationDialog.hide)

    assert "was_fullscreen = self._fullscreen" in source
    assert "def _finish_hide()" in source
    assert "if was_fullscreen:" in source
    assert source.index("if was_fullscreen:") > source.index("def _finish_hide()")


def test_draw_hiding_detail_recenters_spread_area():
    from nekomata.screens.draw_detail import DetailPanel
    source = inspect.getsource(DetailPanel.hide)
    finish_source = inspect.getsource(DetailPanel._finish_hide)

    assert "center_spread" in source
    assert "display = False" in finish_source


def test_draw_stream_uses_app_thread_callback():
    from nekomata.screens.stream_handler import StreamHandler
    source = inspect.getsource(StreamHandler._run_stream)

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
    assert "C_TEXT" in source
    assert "self._render_content(parts)" in source


def test_draw_export_image_includes_drawn_cards():
    source = inspect.getsource(DrawScreen._export_image)

    assert "render_interp_image(" in source
    assert "self._initial_interp_content" in source
    assert "self._drawn_cards" in source
    assert "question=self._question" in source


def test_draw_loading_hint_rotates_cat_tarot_messages():
    from nekomata.screens import stream_handler
    from nekomata.i18n import ui_strings

    s = stream_handler._s()
    assert s["loading_message_interval_s"] == 2.0
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
