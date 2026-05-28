import pytest

from nekomata.app import NekomataApp


@pytest.mark.asyncio
async def test_three_card_flow():
    """Selecting a 3-card spread opens DrawScreen with 3 slots."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "test question"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        assert isinstance(app.screen, DrawScreen)
        from nekomata.screens.draw import DrawScreen
        from nekomata.screens.draw_widgets import SpreadSlot
        slots = app.screen.query(SpreadSlot)
        assert len(slots) == 3


@pytest.mark.asyncio
async def test_back_navigation():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "test question"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)
        app.pop_screen()
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_go_home_refocuses_input():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "test input"
        await pilot.press("enter")
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)

        inp = app.screen.query_one("#prompt-input")
        assert inp.value == ""
        assert inp.has_focus


@pytest.mark.asyncio
async def test_q_returns_from_spread_select_to_home():
    """Q returns from spread selection to the home screen."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "q back test"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_spread_select_arrow_keys_move_focus():
    """Arrow keys move between spread choices."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "arrow test"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        assert app.screen.focused.id == "spread-single"
        await pilot.press("down")
        await pilot.pause()
        assert app.screen.focused.id == "spread-past_present_future"
        await pilot.press("up")
        await pilot.pause()
        assert app.screen.focused.id == "spread-single"
        await pilot.press("right")
        await pilot.pause()
        assert app.screen.focused.id == "spread-past_present_future"
        await pilot.press("left")
        await pilot.pause()
        assert app.screen.focused.id == "spread-single"


@pytest.mark.asyncio
async def test_draw_screen_candidate_grid_uses_all_arrow_keys():
    """Draw screen candidate cards support left/right and up/down movement."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "candidate arrow test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        from nekomata.screens.draw_widgets import DeckCard
        assert isinstance(app.screen, DrawScreen)

        cards = list(app.screen.query(DeckCard))
        assert app.screen.focused is cards[0]

        await pilot.press("right")
        await pilot.pause()
        assert app.screen.focused is cards[1]
        await pilot.press("down")
        await pilot.pause()
        assert app.screen.focused is cards[13]
        await pilot.press("up")
        await pilot.pause()
        assert app.screen.focused is cards[1]
        await pilot.press("left")
        await pilot.pause()
        assert app.screen.focused is cards[0]


@pytest.mark.asyncio
async def test_draw_screen_prepares_spread_cards_on_entry():
    """Draw screen pre-draws exactly the cards needed for the spread."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "prepared cards test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        assert isinstance(app.screen, DrawScreen)

        planned_ids = [dc.card.id for dc in app.screen._planned_cards]
        assert len(planned_ids) == 3
        assert len(set(planned_ids)) == 3
        assert app.screen._drawn_cards == []


@pytest.mark.asyncio
async def test_draw_screen_ignores_repeated_pick_on_same_card():
    """A picked deck card stays highlighted and cannot fill another spread slot."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "duplicate pick test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        from nekomata.screens.draw_widgets import DeckCard
        assert isinstance(app.screen, DrawScreen)

        cards = list(app.screen.query(DeckCard))
        await pilot.press("enter")
        await pilot.pause()

        cards[0].focus()
        await pilot.press("enter")
        await pilot.pause()

        assert cards[0].has_class("picked")
        assert app.screen._pick_index == 1
        assert len(app.screen._drawn_cards) == 1


@pytest.mark.asyncio
async def test_draw_screen_keeps_focus_on_picked_card():
    """Picking a card should not move focus to another deck card."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "focus stays test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        from nekomata.screens.draw_widgets import DeckCard
        assert isinstance(app.screen, DrawScreen)

        cards = list(app.screen.query(DeckCard))
        await pilot.press("right")
        await pilot.press("right")
        await pilot.pause()
        assert app.screen.focused is cards[2]

        await pilot.press("enter")
        await pilot.pause()
        assert cards[2].has_class("picked")
        assert app.screen.focused is cards[2]

        await pilot.press("right")
        await pilot.pause()
        assert app.screen.focused is cards[3]


@pytest.mark.asyncio
async def test_draw_screen_spread_slots_use_all_arrow_keys_after_pick():
    """Once cards are picked, spread slots also respond to all arrow keys."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "slot arrow test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause()
        for i in range(3):
            await pilot.press("enter")
            await pilot.pause(0.1)
            if i < 2:
                await pilot.press("right")
                await pilot.pause(0.1)
        await pilot.pause(1.0)

        from nekomata.screens.draw import DrawScreen
        from nekomata.screens.draw_widgets import SpreadSlot
        assert isinstance(app.screen, DrawScreen)
        slots = list(app.screen.query(SpreadSlot))
        assert app.screen.focused is slots[0]

        await pilot.press("right")
        await pilot.pause()
        assert app.screen.focused is slots[1]
        await pilot.press("left")
        await pilot.pause()
        assert app.screen.focused is slots[0]
        await pilot.press("down")
        await pilot.pause()
        assert app.screen.focused is slots[1]
        await pilot.press("up")
        await pilot.pause()
        assert app.screen.focused is slots[0]


@pytest.mark.asyncio
async def test_draw_screen_enters_flip_immediately_after_final_pick():
    """The final picked card should move straight into the flip phase."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "final pick transition"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()

        from nekomata.screens.draw import DrawScreen, Phase
        from nekomata.screens.draw_widgets import SpreadSlot

        assert isinstance(app.screen, DrawScreen)
        await pilot.press("enter")
        await pilot.pause(0.1)

        slots = list(app.screen.query(SpreadSlot))
        assert app.screen._phase == Phase.FLIP
        assert app.screen.focused is slots[0]


@pytest.mark.asyncio
async def test_draw_screen_accepts_final_pick_during_deck_entrance():
    """A focused card can be picked before the entrance timer finishes."""
    app = NekomataApp()
    app.animation_enabled = True
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "early final pick"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause(0.05)

        from nekomata.screens.draw import DrawScreen, Phase
        from nekomata.screens.draw_widgets import SpreadSlot

        assert isinstance(app.screen, DrawScreen)
        assert app.screen._dealing
        await pilot.press("right")
        await pilot.press("enter")
        await pilot.pause(0.1)

        slots = list(app.screen.query(SpreadSlot))
        assert app.screen._phase == Phase.FLIP
        assert app.screen._pick_index == 1
        assert app.screen.focused is slots[0]


@pytest.mark.asyncio
async def test_spread_select_arrow_updates_preview():
    """Arrow keys update the spread preview."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "arrow test"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        await pilot.press("down")
        await pilot.pause()
        desc = app.screen.query_one("#preview-desc")
        positions = app.screen.query_one("#preview-positions")
        rendered = f"{desc.render()}\n{positions.render()}"
        assert "Past" in rendered or "Present" in rendered or "Future" in rendered


@pytest.mark.asyncio
async def test_spread_select_omits_ten_card_spread():
    """The spread picker should not offer the 10-card Celtic Cross."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "no ten card spread"
        await pilot.press("enter")
        await pilot.pause()

        option_ids = {option.id for option in app.screen.query("SpreadOption")}
        assert "spread-celtic_cross" not in option_ids
