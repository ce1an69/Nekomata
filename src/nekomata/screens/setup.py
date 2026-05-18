"""Setup screen — configure API settings on first launch."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.css.scalar import ScalarOffset
from textual.geometry import Offset
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Input, Static

from nekomata.storage.config import AppConfig


class SetupButton(Static):
    """Focusable setup action without Textual Button's inner label fill."""

    can_focus = True

    class Pressed(Message):
        """Posted when the setup action is activated."""

    def on_click(self) -> None:
        self.post_message(self.Pressed())

    def key_enter(self) -> None:
        self.post_message(self.Pressed())


class SetupScreen(Screen):
    """First-launch setup screen for API URL and API Key."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    DEFAULT_CSS = """
    SetupScreen {
        align: center middle;
    }
    SetupScreen #setup-stack {
        width: 60;
        height: auto;
        align: center middle;
        border: round #313244;
        background: #181825;
        padding: 1 2;
    }
    SetupScreen #setup-title {
        margin-bottom: 0;
        width: 100%;
        background: #181825;
        color: #cba6f7;
        text-align: center;
        text-style: bold;
    }
    SetupScreen #setup-subtitle {
        width: 100%;
        height: auto;
        background: #181825;
        color: #a6adc8;
        text-align: center;
        margin-bottom: 1;
    }
    SetupScreen #setup-ornament-top {
        background: #181825;
        color: #45475a;
        text-align: center;
        height: 1;
        margin-bottom: 1;
    }
    SetupScreen #setup-ornament-bottom {
        background: #181825;
        color: #45475a;
        text-align: center;
        height: 1;
        margin-bottom: 1;
    }
    SetupScreen .field-label {
        width: 100%;
        height: auto;
        background: #181825;
        color: #a6adc8;
        margin-bottom: 0;
    }
    SetupScreen #api-url-input {
        width: 100%;
        height: 3;
        margin-bottom: 1;
        border: round #45475a;
        background: #1e1e2e;
        color: #cdd6f4;
        padding: 0 1;
    }
    SetupScreen #api-url-input:focus {
        border: round #cba6f7;
        background: #181825;
    }
    SetupScreen #api-key-input {
        width: 100%;
        height: 3;
        margin-bottom: 1;
        border: round #45475a;
        background: #1e1e2e;
        color: #cdd6f4;
        padding: 0 1;
    }
    SetupScreen #api-key-input:focus {
        border: round #cba6f7;
        background: #181825;
    }
    SetupScreen #model-input {
        width: 100%;
        height: 3;
        margin-bottom: 1;
        border: round #45475a;
        background: #1e1e2e;
        color: #cdd6f4;
        padding: 0 1;
    }
    SetupScreen #model-input:focus {
        border: round #cba6f7;
        background: #181825;
    }
    SetupButton {
        width: 12;
        height: 3;
        margin-top: 1;
        padding: 0 2;
        background: #1e1e2e;
        border: round #cba6f7;
        color: #cba6f7;
        content-align: center middle;
    }
    SetupButton:hover {
        background: #313244;
        color: #cdd6f4;
    }
    SetupButton:focus {
        background: #313244;
        border: round #cba6f7;
        color: #cdd6f4;
        text-style: bold;
    }
    SetupScreen #setup-error {
        background: #181825;
        color: #f38ba8;
        text-align: center;
        height: auto;
        margin-top: 1;
    }
    SetupScreen #setup-hints {
        width: 100%;
        height: auto;
        background: #181825;
        color: #6c7086;
        text-align: center;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="setup-stack"):
            yield Static("Setup", id="setup-title")
            yield Static("Configure your API connection", id="setup-subtitle")
            yield Static("─── ✦ ───", id="setup-ornament-top")
            yield Static("API URL", classes="field-label")
            yield Input(
                value="https://api.openai.com/v1",
                placeholder="https://api.openai.com/v1",
                id="api-url-input",
            )
            yield Static("API Key", classes="field-label")
            yield Input(
                placeholder="sk-...",
                id="api-key-input",
                password=True,
            )
            yield Static("Model", classes="field-label")
            yield Input(
                placeholder="e.g. glm-4-flash",
                id="model-input",
            )
            yield Static("─── ✦ ───", id="setup-ornament-bottom")
            yield SetupButton("Save", id="save-btn")
            yield Static("", id="setup-error")
            yield Static("Enter next / save · Tab switch", id="setup-hints")

    def on_mount(self) -> None:
        self.query_one("#api-url-input", Input).focus()
        if self.app.animation_enabled:
            stack = self.query_one("#setup-stack")
            stack.styles.opacity = 0
            stack.styles.offset = (0, 1)
            stack.styles.animate("opacity", 1.0, duration=0.35, easing="out_cubic")
            stack.styles.animate(
                "offset",
                ScalarOffset.from_offset(Offset(0, 0)),
                duration=0.35,
                easing="out_cubic",
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "api-url-input":
            self.query_one("#api-key-input", Input).focus()
        elif event.input.id == "api-key-input":
            self.query_one("#model-input", Input).focus()
        elif event.input.id == "model-input":
            self._save()

    def on_setup_button_pressed(self, event: SetupButton.Pressed) -> None:
        event.stop()
        self._save()

    def _save(self) -> None:
        url = self.query_one("#api-url-input", Input).value.strip()
        key = self.query_one("#api-key-input", Input).value.strip()
        model = self.query_one("#model-input", Input).value.strip()
        if not url:
            self.query_one("#setup-error", Static).update("API URL is required")
            return
        if not model:
            self.query_one("#setup-error", Static).update("Model is required")
            return
        config = AppConfig.save(url, key, model)
        self.app.config = config  # type: ignore[misc]
        self.dismiss(None)
