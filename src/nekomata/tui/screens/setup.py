"""Setup screen — configure API settings and language on first launch."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Input, Select, Static

from nekomata.i18n import SUPPORTED_LANGS, set_lang
from nekomata.render.animations import animate_entrance
from nekomata.render.styles import (
    C_BASE,
    C_MANTLE,
    C_MAUVE,
    C_OVERLAY0,
    C_RED,
    C_SUBTEXT0,
    C_SURFACE0,
    C_SURFACE1,
    C_TEXT,
)
from nekomata.i18n import lazy_section
from nekomata.i18n import ORNAMENT
from nekomata.screens.solid_static import SolidStatic
from nekomata.storage.config import AppConfig

_STR = lazy_section("setup")

_FOCUS_FIELDS = ("api-url-input", "api-key-input", "model-input", "lang-select", "save-btn")

_LANG_OPTIONS = [("English", "en"), ("中文", "zh")]


class NavSelect(Select, inherit_bindings=False):
    """Select that only opens on Enter/Space, not on up/down arrow keys."""

    BINDINGS = [Binding("enter,space", "show_overlay", "Show menu", show=False)]


if SUPPORTED_LANGS != ("en", "zh"):
    _LANG_OPTIONS = [
        (
            code.upper()
            if code not in ("en", "zh")
            else ("English" if code == "en" else "中文"),
            code,
        )
        for code in SUPPORTED_LANGS
    ]


class SetupButton(SolidStatic):
    """Focusable setup action without Textual Button's inner label fill."""

    can_focus = True

    class Pressed(Message):
        """Posted when the setup action is activated."""

    def on_click(self) -> None:
        self.post_message(self.Pressed())

    def key_enter(self) -> None:
        self.post_message(self.Pressed())


class SetupScreen(Screen):
    """Setup screen for API URL, API Key, and language. Pre-fills existing config when re-entered via /config."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    def __init__(self, existing_config: AppConfig | None = None) -> None:
        super().__init__()
        self._existing = existing_config

    DEFAULT_CSS = f"""
    SetupScreen {{
        align: center middle;
    }}
    SetupScreen #setup-stack {{
        width: 60;
        height: auto;
        align: center middle;
        border: round {C_SURFACE0};
        background: {C_MANTLE};
        padding: 1 2;
    }}
    SetupScreen #setup-title {{
        margin-bottom: 0;
        width: 100%;
        background: {C_MANTLE};
        color: {C_MAUVE};
        text-align: center;
        text-style: bold;
    }}
    SetupScreen #setup-subtitle {{
        width: 100%;
        height: auto;
        background: {C_MANTLE};
        color: {C_SUBTEXT0};
        text-align: center;
        margin-bottom: 1;
    }}
    SetupScreen #setup-ornament-top {{
        background: {C_MANTLE};
        color: {C_SURFACE1};
        text-align: center;
        height: 1;
        margin-bottom: 1;
    }}
    SetupScreen #setup-ornament-bottom {{
        background: {C_MANTLE};
        color: {C_SURFACE1};
        text-align: center;
        height: 1;
        margin-bottom: 1;
    }}
    SetupScreen .field-label {{
        width: 100%;
        height: auto;
        background: {C_MANTLE};
        color: {C_SUBTEXT0};
        margin-bottom: 0;
    }}
    SetupScreen .setup-input {{
        width: 100%;
        height: 3;
        margin-bottom: 1;
        border: round {C_SURFACE1};
        background: {C_BASE};
        color: {C_TEXT};
        padding: 0 1;
    }}
    SetupScreen .setup-input:focus {{
        border: round {C_MAUVE};
        background: {C_MANTLE};
    }}
    SetupScreen #lang-select {{
        width: 100%;
        height: 3;
        margin-bottom: 1;
        background: {C_BASE};
        color: {C_TEXT};
    }}
    SetupScreen #lang-select > SelectCurrent {{
        height: 3;
        border: round {C_SURFACE1};
        background: {C_BASE};
        color: {C_TEXT};
        padding: 0 1;
    }}
    SetupScreen #lang-select:focus > SelectCurrent {{
        border: round {C_MAUVE};
        background: {C_MANTLE};
    }}
    SetupScreen #lang-select > SelectOverlay {{
        border: round {C_MAUVE};
        background: {C_BASE};
        color: {C_TEXT};
        padding: 0 1;
        max-height: 4;
    }}
    SetupScreen #lang-select > SelectOverlay > .option-list--option {{
        background: {C_BASE};
        color: {C_TEXT};
        padding: 0 1;
    }}
    SetupScreen #lang-select > SelectOverlay > .option-list--option-highlighted {{
        background: {C_MAUVE};
        color: {C_BASE};
        text-style: bold;
    }}
    SetupButton {{
        width: 12;
        height: 3;
        margin-top: 1;
        padding: 0 2;
        background: {C_BASE};
        border: round {C_MAUVE};
        color: {C_MAUVE};
        content-align: center middle;
    }}
    SetupButton:hover {{
        background: {C_SURFACE0};
        color: {C_TEXT};
    }}
    SetupButton:focus {{
        background: {C_SURFACE0};
        border: round {C_MAUVE};
        color: {C_TEXT};
        text-style: bold;
    }}
    SetupScreen #setup-error {{
        display: none;
        background: {C_MANTLE};
        color: {C_RED};
        text-align: center;
        height: auto;
        margin-top: 1;
    }}
    SetupScreen #setup-hints {{
        width: 100%;
        height: auto;
        background: {C_MANTLE};
        color: {C_OVERLAY0};
        text-align: center;
        margin-top: 1;
    }}
    """

    def compose(self) -> ComposeResult:
        cfg = self._existing or AppConfig()
        with Vertical(id="setup-stack"):
            yield SolidStatic(
                _STR["title"],
                align="center",
                id="setup-title",
            )
            yield SolidStatic(_STR["subtitle"], align="center", id="setup-subtitle")
            yield SolidStatic(ORNAMENT, align="center", id="setup-ornament-top")
            yield Static(_STR["field_api_url"], classes="field-label")
            yield Input(
                value=cfg.api_url
                if cfg and cfg.api_url
                else "https://api.openai.com/v1",
                placeholder="https://api.openai.com/v1",
                id="api-url-input",
                classes="setup-input",
            )
            yield Static(_STR["field_api_key"], classes="field-label")
            yield Input(
                value=cfg.api_key or "",
                placeholder="sk-...",
                id="api-key-input",
                classes="setup-input",
            )
            yield Static(_STR["field_model"], classes="field-label")
            yield Input(
                value=cfg.model if cfg and cfg.model else "",
                placeholder="e.g. glm-4-flash",
                id="model-input",
                classes="setup-input",
            )
            yield Static(_STR["field_lang"], classes="field-label")
            yield NavSelect(
                options=_LANG_OPTIONS,
                allow_blank=False,
                value=cfg.lang if cfg else "en",
                id="lang-select",
            )
            yield SolidStatic(ORNAMENT, align="center", id="setup-ornament-bottom")
            yield SetupButton(_STR["save_label"], align="center", id="save-btn")
            yield SolidStatic("", align="center", id="setup-error")
            yield SolidStatic(_STR["hints"], align="center", id="setup-hints")

    def action_go_back(self) -> None:
        self.dismiss(None)

    def on_mount(self) -> None:
        self.query_one("#api-url-input", Input).focus()
        animate_entrance(self.query_one("#setup-stack"), duration=0.35)

    def _navigate_field(self, direction: int) -> None:
        """Move focus to adjacent field. Skips when Select overlay is open."""
        focused = self.app.focused
        if focused is None or focused.id not in _FOCUS_FIELDS:
            return
        idx = _FOCUS_FIELDS.index(focused.id) + direction
        if 0 <= idx < len(_FOCUS_FIELDS):
            self.query_one(f"#{_FOCUS_FIELDS[idx]}").focus()

    def key_down(self) -> None:
        self._navigate_field(1)

    def key_up(self) -> None:
        self._navigate_field(-1)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "api-url-input":
            self.query_one("#api-key-input", Input).focus()
        elif event.input.id == "api-key-input":
            self.query_one("#model-input", Input).focus()
        elif event.input.id == "model-input":
            self.query_one("#lang-select", NavSelect).focus()

    def on_setup_button_pressed(self, event: SetupButton.Pressed) -> None:
        event.stop()
        self._save()

    def _save(self) -> None:
        url = self.query_one("#api-url-input", Input).value.strip()
        key = self.query_one("#api-key-input", Input).value.strip()
        model = self.query_one("#model-input", Input).value.strip()
        lang = self.query_one("#lang-select", NavSelect).value
        if not url:
            self._show_error(_STR["error_url_required"])
            return
        if not model:
            self._show_error(_STR["error_model_required"])
            return
        if lang == Select.BLANK:
            lang = "en"
        config = AppConfig.save(url, key, model, lang=lang)
        self.app.config = config  # type: ignore[misc]
        set_lang(lang)
        self.dismiss(None)

    def _show_error(self, message: str) -> None:
        error = self.query_one("#setup-error", SolidStatic)
        error.display = True
        error.update(message)
