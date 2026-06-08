"""Unit tests for cli/run.py — helper functions for the CLI mode."""

from unittest.mock import patch

from nekomata.cli.run import _draw_cards, _prompt_choice, _prompt_int


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
    drawn, spread = _draw_cards("single", seed=42)
    assert len(drawn) == 1
    assert drawn[0].card is not None
    assert drawn[0].position is not None


def test_draw_cards_five_card_cross():
    drawn, spread = _draw_cards("five_card_cross", seed=42)
    assert len(drawn) == 5


def test_draw_cards_past_present_future():
    drawn, spread = _draw_cards("past_present_future", seed=42)
    assert len(drawn) == 3


def test_draw_cards_deterministic_with_seed():
    drawn1, _ = _draw_cards("single", seed=42)
    drawn2, _ = _draw_cards("single", seed=42)
    assert drawn1[0].card.id == drawn2[0].card.id
    assert drawn1[0].is_reversed == drawn2[0].is_reversed
