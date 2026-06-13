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
from nekomata.core.ai.interpreter import InterpretationError


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
