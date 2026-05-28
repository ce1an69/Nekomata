from time import perf_counter

import pytest
from textual.css.query import NoMatches

from nekomata.app import NekomataApp
from nekomata.card.types import Arcana, Card, DrawnCard, Position
from nekomata.screens.draw_widgets import (
    DECK_HIDE_DELAY,
    PICK_COMPLETE_DELAY,
    DeckCard,
    NUM_DECK_CARDS,
    SPREAD_SLOT_HEIGHT,
    SPREAD_SLOT_WIDTH,
    SLOT_FLIP_FADE_IN,
    SLOT_FLIP_FADE_OUT,
    SLOT_FLIP_GLOW_HOLD,
    SLOT_FLIP_SWAP_PAUSE,
    SPREAD_RECENTER_DURATION,
    SPREAD_RECENTER_OFFSET,
    SpreadSlot,
)


def _make_drawn_card() -> DrawnCard:
    card = Card(
        id="test",
        name="Test",
        name_zh="测试",
        arcana=Arcana.MAJOR,
        number=0,
        element="air",
        astrology="Uranus",
        keywords_upright=("a",),
        keywords_reversed=("b",),
        meaning_upright="up",
        meaning_reversed="down",
    )
    return DrawnCard(
        card=card,
        position=Position(name="Present", name_zh="现在", description="当前"),
        is_reversed=False,
    )


@pytest.mark.asyncio
async def test_draw_screen_mounts_deck():
    """DrawScreen mounts deck cards and spread slots."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "动画测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        from nekomata.screens.draw_widgets import DeckCard, SpreadSlot
        assert isinstance(app.screen, DrawScreen)
        deck_rows = app.screen.query(".deck-row-line")
        assert len(deck_rows) == 4
        assert [len(list(row.query(DeckCard))) for row in deck_rows] == [12, 12, 12, 12]
        deck_cards = app.screen.query(DeckCard)
        assert len(deck_cards) > 0
        slots = app.screen.query(SpreadSlot)
        assert len(slots) == 1


def test_deck_card_back_uses_card_like_terminal_ratio():
    """Face-down choices should not render as tall vertical bars."""
    css = DeckCard.DEFAULT_CSS

    width = int(css.split("width: ")[1].split(";")[0])
    height = int(css.split("height: ")[1].split(";")[0])

    assert height <= width


def test_deck_card_motion_stays_subtle():
    """Pick/focus movement should feel like a glide, and picked cards stay visible."""
    css = DeckCard.DEFAULT_CSS

    assert "offset 300ms" in css
    assert "DeckCard:focus" in css
    assert "offset: 0 -1;" in css
    assert "DeckCard.picked" in css
    picked_css = css.split("DeckCard.picked {")[1].split("}")[0]
    assert "opacity: 1;" in picked_css
    assert "offset: 0 -1;" in picked_css
    assert "border: round" in picked_css


def test_spread_slot_has_room_for_complete_face_preview():
    """Placed cards should fit the complete rendered face instead of clipping it."""
    deck_css = DeckCard.DEFAULT_CSS
    slot_css = SpreadSlot.DEFAULT_CSS

    deck_width = int(deck_css.split("width: ")[1].split(";")[0])
    deck_height = int(deck_css.split("height: ")[1].split(";")[0])
    slot_width = int(slot_css.split("width: ")[1].split(";")[0])
    slot_height = int(slot_css.split("height: ")[1].split(";")[0])

    assert slot_width > deck_width
    assert slot_height > deck_height
    assert (slot_width, slot_height) == (SPREAD_SLOT_WIDTH, SPREAD_SLOT_HEIGHT)
    assert "border: round" in deck_css
    assert "border: round" in slot_css
    assert "border: dashed" not in slot_css


def test_spread_grid_uses_compact_columns():
    """Spread cards should sit close together instead of stretching across the row."""
    from nekomata.screens.draw import DrawScreen
    css = DrawScreen.DEFAULT_CSS

    assert "grid-columns: 1fr 1fr 1fr;" not in css
    assert "grid-columns: 18 18 18;" in css
    assert "grid-columns: 18 18 18 18 18;" in css


def test_deck_cards_have_light_spacing():
    """Selectable cards need a little air between them."""
    css = DeckCard.DEFAULT_CSS

    assert "margin: 0 1;" in css
    assert "border: round" in css
    assert "border: dashed" not in css


def test_deck_section_has_room_for_three_rows():
    """The candidate deck area should comfortably fit three rows."""
    from nekomata.screens.draw import DrawScreen
    css = DrawScreen.DEFAULT_CSS

    min_height = int(css.split("#deck-section {")[1].split("min-height: ")[1].split(";")[0])
    assert min_height >= 30


def test_draw_screen_offers_more_candidate_cards():
    """The selectable row should feel like a fuller deck."""
    assert NUM_DECK_CARDS == 48


def test_pick_complete_transition_is_gentle():
    """Finishing selection should move briskly into the flip phase."""
    from nekomata.screens.draw import DrawScreen
    css = DrawScreen.DEFAULT_CSS

    assert "transition: opacity 420ms" in css
    assert "offset 420ms" in css
    assert DECK_HIDE_DELAY == pytest.approx(0.42)
    assert PICK_COMPLETE_DELAY == pytest.approx(0.0)


def test_spread_recenters_with_motion_after_deck_exit():
    """When the deck disappears, the spread should glide into its centered layout."""
    from nekomata.screens.draw import DrawScreen
    css = DrawScreen.DEFAULT_CSS

    main_area_css = css.split("#main-area {")[1].split("}")[0]
    assert "transition: offset 280ms" in main_area_css
    assert SPREAD_RECENTER_OFFSET == 4
    assert SPREAD_RECENTER_DURATION == pytest.approx(0.28)


def test_spread_slot_flip_uses_smooth_two_phase_motion():
    """Flipping should be compact and animated through the face swap."""
    constants = SpreadSlot.flip.__code__.co_consts
    css = SpreadSlot.DEFAULT_CSS

    assert "offset 220ms" in css
    assert 0.0 in constants  # fade-out to fully invisible (no flash)
    assert SLOT_FLIP_FADE_OUT == pytest.approx(0.14)
    assert SLOT_FLIP_SWAP_PAUSE == pytest.approx(0.02)
    assert SLOT_FLIP_FADE_IN == pytest.approx(0.28)
    assert SLOT_FLIP_GLOW_HOLD == pytest.approx(0.16)


@pytest.mark.asyncio
async def test_spread_slot_flip_skips_animation_when_disabled():
    """Reduced-animation mode should reveal immediately without sleep delays."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        slot = SpreadSlot(0, "现在")
        await app.screen.mount(slot)
        await pilot.pause()

        slot.place_card(_make_drawn_card())
        start = perf_counter()
        await slot.flip()
        elapsed = perf_counter() - start

        assert slot.is_revealed
        assert slot.has_class("revealed")
        assert not slot.has_class("face-down")
        assert not slot.has_class("glow")
        assert elapsed < SLOT_FLIP_FADE_OUT


def test_spread_slot_reveal_only_ignores_missing_slot_content(monkeypatch):
    """Reveal should not hide unexpected query failures."""
    slot = SpreadSlot(0, "现在")
    slot.drawn_card = _make_drawn_card()

    def raise_no_matches(*_args, **_kwargs):
        raise NoMatches("missing")

    monkeypatch.setattr(slot, "query_one", raise_no_matches)
    slot._render_revealed()
    assert slot.is_revealed is False

    def raise_runtime_error(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(slot, "query_one", raise_runtime_error)
    with pytest.raises(RuntimeError, match="boom"):
        slot._render_revealed()


def test_done_phase_does_not_wait_for_completion_shimmer():
    """The detail panel should appear immediately after the final flip."""
    from nekomata.screens.draw import DrawScreen
    names = DrawScreen.on_spread_slot_flipped.__code__.co_names

    assert "run_worker" in names
    assert "_completion_shimmer" in names


def test_completion_shimmer_avoids_zero_delay_timer():
    """The first completion pulse should not use Textual's zero-second timer path."""
    from nekomata.screens.draw import DrawScreen
    constants = DrawScreen._completion_shimmer.__code__.co_consts

    assert 0.01 in constants
