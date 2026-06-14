"""Unit tests for cli/run.py — helper functions for the CLI mode."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from nekomata.cli.run import (
    _draw_cards,
    _print_cards,
    _prompt,
    _prompt_choice,
    _prompt_int,
    _stream_interpretation,
    run_cli,
)
from nekomata.core.ai.interpreter import InterpretationError, StreamChunk


class _FakeThread:
    started: list[tuple] = []
    joined = 0

    def __init__(self, target, args=(), daemon=None):
        self.target = target
        self.args = args
        self.daemon = daemon

    def start(self):
        self.started.append(self.args)

    def join(self):
        type(self).joined += 1


class _RunningFakeThread:
    def __init__(self, target, args=(), daemon=None):
        self.target = target
        self.args = args
        self.daemon = daemon

    def start(self):
        self.target(*self.args)

    def join(self):
        pass


class _OneSpinEvent:
    def __init__(self):
        self._stopped = False

    def is_set(self):
        return self._stopped

    def set(self):
        self._stopped = True

    def clear(self):
        self._stopped = False

    def wait(self, timeout):
        self._stopped = True


class _FakeInterpreter:
    def __init__(self, chunks=None, error=None):
        self.chunks = chunks or []
        self.error = error

    def interpret_stream(self, drawn, question, spread_key="", lang="en"):
        yield from self.chunks
        if self.error is not None:
            raise self.error


def test_prompt_int_valid():
    with patch("nekomata.cli.run._prompt", return_value="3"):
        result = _prompt_int("Pick a number", default=0)
    assert result == 3


def test_prompt_int_invalid_then_valid():
    with patch("nekomata.cli.run._prompt", side_effect=["abc", "5"]):
        result = _prompt_int("Pick a number", default=0)
    assert result == 5


def test_prompt_choice_selects_option():
    with patch("nekomata.cli.run._prompt", return_value="1"):
        result = _prompt_choice("Choose", ["alpha", "beta", "gamma"])
    assert result == "alpha"


def test_prompt_choice_out_of_range_defaults():
    with patch("nekomata.cli.run._prompt", return_value="99"):
        result = _prompt_choice("Choose", ["alpha", "beta"], default_idx=1)
    assert result == "beta"


def test_prompt_choice_invalid_input_defaults():
    with patch("nekomata.cli.run._prompt", return_value="not_a_number"):
        result = _prompt_choice("Choose", ["alpha", "beta"], default_idx=0)
    assert result == "alpha"


def test_draw_cards_single():
    drawn, _spread = _draw_cards("single", seed=42)
    assert len(drawn) == 1
    assert drawn[0].card is not None
    assert drawn[0].position is not None


def test_draw_cards_five_card_cross():
    drawn, _spread = _draw_cards("five_card_cross", seed=42)
    assert len(drawn) == 5


def test_draw_cards_past_present_future():
    drawn, _spread = _draw_cards("past_present_future", seed=42)
    assert len(drawn) == 3


def test_draw_cards_deterministic_with_seed():
    drawn1, _ = _draw_cards("single", seed=42)
    drawn2, _ = _draw_cards("single", seed=42)
    assert drawn1[0].card.id == drawn2[0].card.id
    assert drawn1[0].is_reversed == drawn2[0].is_reversed


# --- _prompt tests ---


def test_prompt_returns_trimmed():
    with patch("nekomata.cli.run.input", return_value="  hello  "):
        result = _prompt("Say hi")
    assert result == "hello"


def test_prompt_empty_uses_default():
    with patch("nekomata.cli.run.input", return_value=""):
        result = _prompt("Say hi", default="fallback")
    assert result == "fallback"


def test_prompt_eof_exits():
    with patch("nekomata.cli.run.input", side_effect=EOFError), pytest.raises(SystemExit):
        _prompt("Question")


def test_prompt_keyboard_interrupt_exits():
    with patch("nekomata.cli.run.input", side_effect=KeyboardInterrupt), pytest.raises(SystemExit):
        _prompt("Question")


# --- _print_cards tests ---


def test_print_cards_no_crash():
    drawn, _ = _draw_cards("single", seed=42)
    with patch("nekomata.cli.run.console.print"):
        _print_cards(drawn, "en")  # should not raise


# --- _stream_interpretation tests ---


def test_stream_interpretation_config_error():
    config = MagicMock()
    config.lang = "en"
    with (
        patch(
            "nekomata.cli.run.get_interpreter",
            side_effect=InterpretationError("no api key", config_error=True),
        ),
        patch("nekomata.cli.run.console.print") as mock_print,
    ):
        _stream_interpretation(config, [], "test question")
    calls = [str(c) for c in mock_print.call_args_list]
    assert any("Error" in c for c in calls)


def test_stream_interpretation_prints_content_and_stops_spinner():
    _FakeThread.started = []
    _FakeThread.joined = 0
    config = MagicMock(lang="en")
    interp = _FakeInterpreter([StreamChunk("Answer", "content")])

    with (
        patch("nekomata.cli.run.get_interpreter", return_value=interp),
        patch("nekomata.cli.run.threading.Thread", _FakeThread),
        patch("nekomata.cli.run.console.print") as mock_print,
        patch("nekomata.cli.run.sys.stdout.flush"),
    ):
        _stream_interpretation(config, [], "test question", "single")

    assert _FakeThread.started == [("Consulting the cards...",)]
    assert _FakeThread.joined == 1
    mock_print.assert_any_call("Answer", end="", markup=False, highlight=False)
    mock_print.assert_any_call("\n")


def test_stream_interpretation_restarts_spinner_for_thinking():
    _FakeThread.started = []
    _FakeThread.joined = 0
    config = MagicMock(lang="en")
    interp = _FakeInterpreter([StreamChunk("Thought", "thinking"), StreamChunk("Answer", "content")])

    with (
        patch("nekomata.cli.run.get_interpreter", return_value=interp),
        patch("nekomata.cli.run.threading.Thread", _FakeThread),
        patch("nekomata.cli.run.console.print") as mock_print,
        patch("nekomata.cli.run.sys.stdout.flush"),
    ):
        _stream_interpretation(config, [], "test question")

    assert _FakeThread.started == [("Consulting the cards...",), ("Thinking...",)]
    assert _FakeThread.joined == 2
    mock_print.assert_any_call("Answer", end="", markup=False, highlight=False)


def test_stream_interpretation_prints_stream_error():
    config = MagicMock(lang="en")
    interp = _FakeInterpreter(error=InterpretationError("provider failed"))

    with (
        patch("nekomata.cli.run.get_interpreter", return_value=interp),
        patch("nekomata.cli.run.threading.Thread", _FakeThread),
        patch("nekomata.cli.run.console.print") as mock_print,
        patch("nekomata.cli.run.sys.stdout.flush"),
    ):
        _stream_interpretation(config, [], "test question")

    calls = [str(c) for c in mock_print.call_args_list]
    assert any("Interpretation error" in c and "provider failed" in c for c in calls)


def test_stream_interpretation_handles_keyboard_interrupt():
    config = MagicMock(lang="en")
    interp = _FakeInterpreter(error=KeyboardInterrupt())

    with (
        patch("nekomata.cli.run.get_interpreter", return_value=interp),
        patch("nekomata.cli.run.threading.Thread", _FakeThread),
        patch("nekomata.cli.run.console.print") as mock_print,
        patch("nekomata.cli.run.sys.stdout.flush"),
    ):
        _stream_interpretation(config, [], "test question")

    calls = [str(c) for c in mock_print.call_args_list]
    assert any("Interrupted" in c for c in calls)


def test_stream_interpretation_spinner_writes_and_clears_stdout():
    config = MagicMock(lang="en")
    interp = _FakeInterpreter([StreamChunk("Answer", "content")])

    with (
        patch("nekomata.cli.run.get_interpreter", return_value=interp),
        patch("nekomata.cli.run.threading.Thread", _RunningFakeThread),
        patch("nekomata.cli.run.threading.Event", _OneSpinEvent),
        patch("nekomata.cli.run.console.print"),
        patch("nekomata.cli.run.sys.stdout.write") as write,
        patch("nekomata.cli.run.sys.stdout.flush"),
    ):
        _stream_interpretation(config, [], "test question")

    writes = [call.args[0] for call in write.call_args_list]
    assert any("Consulting the cards" in text for text in writes)
    assert any(text.strip() == "" for text in writes)


# --- run_cli integration tests ---


def _make_args(**overrides):
    defaults = dict(question="", seed=None, spread="", yes=False)
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def test_run_cli_no_api_key():
    config = MagicMock(api_key="", api_url="", lang="en")
    with (
        patch("nekomata.cli.run.AppConfig.load", return_value=config),
        patch("nekomata.cli.run.console.print") as mock_print,
    ):
        run_cli(_make_args(question="test", seed=42, spread="single", yes=True))
    calls = [str(c) for c in mock_print.call_args_list]
    assert any("API not configured" in c for c in calls)


def test_run_cli_unknown_spread():
    config = MagicMock(api_key="k", api_url="http://x", lang="en")
    with (
        patch("nekomata.cli.run.AppConfig.load", return_value=config),
        patch("nekomata.cli.run.console.print") as mock_print,
    ):
        run_cli(_make_args(question="q", seed=42, spread="nonexistent", yes=True))
    calls = [str(c) for c in mock_print.call_args_list]
    assert any("Unknown spread" in c for c in calls)


def test_run_cli_spread_name_falls_back_when_get_spread_fails():
    config = MagicMock(api_key="k", api_url="http://x", lang="en")
    drawn = [MagicMock()]

    with (
        patch("nekomata.cli.run.AppConfig.load", return_value=config),
        patch("nekomata.cli.run.SPREAD_REGISTRY", [("bad", object())]),
        patch("nekomata.cli.run.get_spread", side_effect=RuntimeError("bad spread")),
        patch("nekomata.cli.run._prompt_choice", return_value="bad") as choice,
        patch("nekomata.cli.run._draw_cards", return_value=(drawn, MagicMock())),
        patch("nekomata.cli.run._print_cards"),
        patch("nekomata.cli.run._prompt", return_value="n"),
    ):
        run_cli(_make_args(question="q", seed=1))

    choice.assert_called_once()


def test_run_cli_yes_uses_defaults_and_streams():
    config = MagicMock(api_key="k", api_url="http://x", lang="en")
    drawn = [MagicMock()]

    with (
        patch("nekomata.cli.run.AppConfig.load", return_value=config),
        patch("nekomata.cli.run.random.randint", return_value=123),
        patch("nekomata.cli.run._draw_cards", return_value=(drawn, MagicMock())) as mock_draw,
        patch("nekomata.cli.run._print_cards") as mock_print_cards,
        patch("nekomata.cli.run._stream_interpretation") as mock_stream,
    ):
        run_cli(_make_args(question="q", yes=True))

    mock_draw.assert_called_once_with("single", 123)
    mock_print_cards.assert_called_once_with(drawn, "en")
    mock_stream.assert_called_once_with(config, drawn, "q", "single")


def test_run_cli_prompts_and_confirms_stream():
    config = MagicMock(api_key="k", api_url="http://x", lang="en")
    drawn = [MagicMock()]

    with (
        patch("nekomata.cli.run.AppConfig.load", return_value=config),
        patch("nekomata.cli.run._prompt", side_effect=["Will it rain?", "y"]),
        patch("nekomata.cli.run._prompt_int", return_value=7),
        patch("nekomata.cli.run._prompt_choice", return_value="Single Card (single)"),
        patch("nekomata.cli.run._draw_cards", return_value=(drawn, MagicMock())) as mock_draw,
        patch("nekomata.cli.run._print_cards"),
        patch("nekomata.cli.run._stream_interpretation") as mock_stream,
    ):
        run_cli(_make_args())

    mock_draw.assert_called_once_with("single", 7)
    mock_stream.assert_called_once_with(config, drawn, "Will it rain?", "single")


def test_run_cli_prompt_empty_question_exits():
    config = MagicMock(api_key="k", api_url="http://x", lang="en")

    with (
        patch("nekomata.cli.run.AppConfig.load", return_value=config),
        patch("nekomata.cli.run._prompt", return_value=""),
        patch("nekomata.cli.run.console.print") as mock_print,
    ):
        run_cli(_make_args())

    calls = [str(c) for c in mock_print.call_args_list]
    assert any("No question provided" in c for c in calls)


def test_run_cli_skips_interpretation_when_declined():
    config = MagicMock(api_key="k", api_url="http://x", lang="en")
    drawn = [MagicMock()]

    with (
        patch("nekomata.cli.run.AppConfig.load", return_value=config),
        patch("nekomata.cli.run._draw_cards", return_value=(drawn, MagicMock())),
        patch("nekomata.cli.run._print_cards"),
        patch("nekomata.cli.run._prompt", return_value="n"),
        patch("nekomata.cli.run._stream_interpretation") as mock_stream,
        patch("nekomata.cli.run.console.print") as mock_print,
    ):
        run_cli(_make_args(question="q", seed=1, spread="single"))

    mock_stream.assert_not_called()
    calls = [str(c) for c in mock_print.call_args_list]
    assert any("Skipped interpretation" in c for c in calls)
