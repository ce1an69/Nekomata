import pytest

from nekomata.app import NekomataApp
from nekomata.screens.draw import (
    DECK_HIDE_DELAY,
    PICK_COMPLETE_DELAY,
    DeckCard,
    DrawScreen,
    NUM_DECK_CARDS,
    SLOT_FLIP_FADE_IN,
    SLOT_FLIP_FADE_OUT,
    SLOT_FLIP_GLOW_HOLD,
    SLOT_FLIP_SWAP_PAUSE,
    SLOT_PLACE_DURATION,
    SLOT_PLACE_OFFSET,
    SPREAD_RECENTER_DURATION,
    SPREAD_RECENTER_OFFSET,
    SpreadSlot,
)


class DummyStyles:
    opacity = 1
    offset = (0, 0)


class SyncAnimateWidget:
    def __init__(self) -> None:
        self.styles = DummyStyles()
        self.calls = []
        self.styles.animate = self.styles_animate

    def styles_animate(self, attribute, value, duration):
        self.calls.append((attribute, value, duration))
        return None


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
        from nekomata.screens.draw import DrawScreen, DeckCard, SpreadSlot
        assert isinstance(app.screen, DrawScreen)
        deck_rows = app.screen.query(".deck-row-line")
        assert len(deck_rows) == 3
        assert [len(list(row.query(DeckCard))) for row in deck_rows] == [8, 8, 8]
        deck_cards = app.screen.query(DeckCard)
        assert len(deck_cards) > 0
        slots = app.screen.query(SpreadSlot)
        assert len(slots) == 1


def test_animation_functions_exist():
    """Verify animation module exports the reveal function."""
    from nekomata.render.animations import animate_reveal
    assert callable(animate_reveal)


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


def test_spread_slot_matches_deck_card_ratio_and_rounding():
    """Placed cards should keep the same compact shape as selectable cards."""
    deck_css = DeckCard.DEFAULT_CSS
    slot_css = SpreadSlot.DEFAULT_CSS

    deck_width = int(deck_css.split("width: ")[1].split(";")[0])
    deck_height = int(deck_css.split("height: ")[1].split(";")[0])
    slot_width = int(slot_css.split("width: ")[1].split(";")[0])
    slot_height = int(slot_css.split("height: ")[1].split(";")[0])

    assert (slot_width, slot_height) == (deck_width, deck_height)
    assert "border: round" in deck_css
    assert "border: round" in slot_css
    assert "border: dashed" not in slot_css


def test_spread_grid_uses_compact_columns():
    """Spread cards should sit close together instead of stretching across the row."""
    css = DrawScreen.DEFAULT_CSS

    assert "grid-columns: 1fr 1fr 1fr;" not in css
    assert "grid-columns: 12 12 12;" in css
    assert "grid-columns: 12 12 12 12 12;" in css


def test_deck_cards_have_light_spacing():
    """Selectable cards need a little air between them."""
    css = DeckCard.DEFAULT_CSS

    assert "margin: 0 1;" in css
    assert "border: round" in css
    assert "border: dashed" not in css


def test_deck_section_has_room_for_three_rows():
    """The candidate deck area should comfortably fit three rows."""
    css = DrawScreen.DEFAULT_CSS

    min_height = int(css.split("#deck-section {")[1].split("min-height: ")[1].split(";")[0])
    assert min_height >= 30


def test_draw_screen_offers_more_candidate_cards():
    """The selectable row should feel like a fuller deck."""
    assert NUM_DECK_CARDS == 24


def test_pick_complete_transition_is_gentler():
    """Finishing selection should move briskly into the flip phase."""
    css = DrawScreen.DEFAULT_CSS

    assert "transition: opacity 420ms" in css
    assert "offset 420ms" in css
    assert DECK_HIDE_DELAY == pytest.approx(0.42)
    assert PICK_COMPLETE_DELAY == pytest.approx(0.35)


def test_spread_recenters_with_motion_after_deck_exit():
    """When the deck disappears, the spread should glide into its centered layout."""
    css = DrawScreen.DEFAULT_CSS

    main_area_css = css.split("#main-area {")[1].split("}")[0]
    assert "transition: offset 280ms" in main_area_css
    assert SPREAD_RECENTER_OFFSET == 4
    assert SPREAD_RECENTER_DURATION == pytest.approx(0.28)


def test_spread_slot_place_uses_short_slide_in():
    """Placed cards should slide into their slot quickly instead of just fading in."""
    constants = DrawScreen._animate_slot_entrance.__code__.co_names
    reveal_constants = DrawScreen._reveal_slot.__code__.co_names

    assert "SLOT_PLACE_OFFSET" in constants
    assert "SLOT_PLACE_DURATION" in reveal_constants
    assert SLOT_PLACE_OFFSET == 2
    assert SLOT_PLACE_DURATION == pytest.approx(0.22)


def test_spread_slot_flip_uses_smooth_two_phase_motion():
    """Flipping should be compact and animated through the face swap."""
    constants = SpreadSlot.flip.__code__.co_consts
    css = SpreadSlot.DEFAULT_CSS

    assert "offset 220ms" in css
    assert 0.12 in constants
    assert SLOT_FLIP_FADE_OUT == pytest.approx(0.10)
    assert SLOT_FLIP_SWAP_PAUSE == pytest.approx(0.015)
    assert SLOT_FLIP_FADE_IN == pytest.approx(0.18)
    assert SLOT_FLIP_GLOW_HOLD == pytest.approx(0.08)


def test_done_phase_does_not_wait_for_completion_shimmer():
    """The detail panel should appear immediately after the final flip."""
    names = DrawScreen.on_spread_slot_flipped.__code__.co_names

    assert "run_worker" in names
    assert "_completion_shimmer" in names


def test_completion_shimmer_avoids_zero_delay_timer():
    """The first completion pulse should not use Textual's zero-second timer path."""
    constants = DrawScreen._completion_shimmer.__code__.co_consts

    assert 0.01 in constants


@pytest.mark.asyncio
async def test_animate_reveal_allows_sync_textual_animate():
    """Installed Textual may return None from animate()."""
    from nekomata.render.animations import animate_reveal

    widget = SyncAnimateWidget()

    await animate_reveal(widget)

    assert widget.styles.opacity == 0
    assert widget.calls == [("opacity", 1.0, 0.3)]
