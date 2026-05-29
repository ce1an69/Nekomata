"""Pure CLI mode — interactive or one-liner tarot readings with streaming AI."""

import argparse
import random
import sys
import threading

from rich.console import Console
from rich.table import Table

from nekomata.ai.interpreter import InterpretationError, get_interpreter
from nekomata.card.display import card_keywords, status_label as _status_label
from nekomata.card.deck import Deck
from nekomata.card.types import DrawnCard
from nekomata.i18n import set_lang, ui_strings
from nekomata.spread import SPREAD_REGISTRY, get_spread
from nekomata.storage.config import AppConfig

console = Console()


def _prompt(question: str, default: str = "") -> str:
    """Prompt the user for input, returning the trimmed value."""
    hint = f" [{default}]" if default else ""
    try:
        value = input(f"{question}{hint}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return value or default


def _prompt_int(question: str, default: int = 0) -> int:
    """Prompt for an integer, re-prompting on invalid input."""
    while True:
        raw = _prompt(question, str(default))
        try:
            return int(raw)
        except ValueError:
            print(f"  Please enter a number, got: {raw}")


def _prompt_choice(question: str, options: list[str], default_idx: int = 0) -> str:
    """Prompt the user to choose from a numbered list."""
    print(f"\n{question}")
    for i, opt in enumerate(options):
        marker = ">" if i == default_idx else " "
        print(f"  {marker} {i + 1}. {opt}")
    idx = _prompt("Enter number", str(default_idx + 1))
    try:
        chosen = int(idx) - 1
        if 0 <= chosen < len(options):
            return options[chosen]
    except ValueError:
        pass
    return options[default_idx]


def _draw_cards(
    spread_key: str, seed: int, reversal_prob: float = 0.5
) -> tuple[list[DrawnCard], object]:
    """Shuffle and draw cards for the given spread."""
    random.seed(seed)
    spread = get_spread(spread_key)
    deck = Deck()
    deck.shuffle()
    drawn: list[DrawnCard] = []
    for position in spread.positions:
        card, is_reversed = deck.draw(reversal_prob)
        drawn.append(DrawnCard(card=card, position=position, is_reversed=is_reversed))
    return drawn, spread


def _print_cards(drawn: list[DrawnCard], lang: str) -> None:
    """Display drawn cards in a table."""
    console.print()

    table = Table(show_header=True, border_style="dim")
    table.add_column("Position", style="cyan")
    table.add_column("Card", style="bold")
    table.add_column("Status", style="yellow")
    table.add_column("Keywords", style="dim")

    for dc in drawn:
        table.add_row(
            dc.position.name,
            dc.card.name,
            _status_label(dc.is_reversed, lang),
            ", ".join(card_keywords(dc.card, dc.is_reversed, lang)),
        )
    console.print(table)
    console.print()


def _stream_interpretation(
    config: AppConfig,
    drawn: list[DrawnCard],
    question: str,
    spread_key: str = "",
) -> None:
    """Stream AI interpretation to the console with a loading spinner."""
    try:
        interp = get_interpreter(config)
    except InterpretationError as e:
        console.print(f"[red]Error:[/red] {e}")
        return

    stop_event = threading.Event()
    spinner: threading.Thread | None = None

    def _spin(label: str = "Consulting the cards...") -> None:
        frames = ui_strings()["loading_frames"]
        idx = 0
        while not stop_event.is_set():
            frame = frames[idx % len(frames)]
            sys.stdout.write(f"\r  {frame} {label}")
            sys.stdout.flush()
            idx += 1
            stop_event.wait(0.08)
        sys.stdout.write("\r" + " " * 50 + "\r")
        sys.stdout.flush()

    def _stop_spinner() -> None:
        nonlocal spinner
        if spinner is not None:
            stop_event.set()
            spinner.join()
            spinner = None

    def _start_spinner(label: str = "Consulting the cards...") -> None:
        nonlocal spinner
        _stop_spinner()
        stop_event.clear()
        spinner = threading.Thread(target=_spin, args=(label,), daemon=True)
        spinner.start()

    _start_spinner()
    first_content = True

    try:
        for chunk in interp.interpret_stream(drawn, question, spread_key=spread_key, lang=config.lang):
            if chunk.kind == "content":
                if first_content:
                    _stop_spinner()
                    first_content = False
                console.print(chunk.text, end="", markup=False, highlight=False)
            elif chunk.kind == "thinking" and first_content:
                _start_spinner("Thinking...")
            sys.stdout.flush()
    except InterpretationError as e:
        console.print(f"\n[red]Interpretation error:[/red] {e}")
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
    finally:
        _stop_spinner()

    if not first_content:
        console.print("\n")


def run_cli(args: argparse.Namespace) -> None:
    """Run the CLI reading flow."""
    config = AppConfig.load()
    set_lang(config.lang)

    if not config.api_key or not config.api_url:
        console.print("[red]Error:[/red] API not configured.")
        console.print(
            "[dim]Run the TUI first (just `nekomata`) to set up your API key,"
        )
        console.print("[dim]or edit .neko/settings.json manually.[/dim]")
        return

    spread_keys = [key for key, _ in SPREAD_REGISTRY]
    spread_names = []
    for key in spread_keys:
        try:
            s = get_spread(key)
            spread_names.append(f"{s.name} ({key})")
        except Exception:
            spread_names.append(key)

    question = args.question
    seed = args.seed
    spread_key = args.spread

    if not question:
        question = _prompt("Your question")
        if not question:
            console.print("[dim]No question provided. Exiting.[/dim]")
            return

    if seed is None:
        seed = (
            random.randint(1, 9999)
            if args.yes
            else _prompt_int("Random seed", random.randint(1, 9999))
        )

    if not spread_key:
        if args.yes:
            spread_key = spread_keys[0]
        else:
            chosen = _prompt_choice("Choose a spread:", spread_names, default_idx=0)
            spread_key = spread_keys[spread_names.index(chosen)]
    elif spread_key not in spread_keys:
        console.print(f"[red]Unknown spread:[/red] {spread_key}")
        console.print(f"[dim]Available: {', '.join(spread_keys)}[/dim]")
        return

    drawn, _ = _draw_cards(spread_key, seed)
    _print_cards(drawn, config.lang)

    if args.yes:
        _stream_interpretation(config, drawn, question, spread_key)
        return

    confirm = _prompt("Start AI interpretation? (Y/n)", "y")
    if confirm.lower() in ("y", "yes", ""):
        _stream_interpretation(config, drawn, question, spread_key)
    else:
        console.print("[dim]Skipped interpretation.[/dim]")
