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
        from nekomata.screens.draw import SpreadSlot
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

        await pilot.press("q")
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
        from nekomata.screens.draw import DeckCard, DrawScreen
        assert isinstance(app.screen, DrawScreen)

        cards = list(app.screen.query(DeckCard))
        assert app.screen.focused is cards[0]

        await pilot.press("right")
        await pilot.pause()
        assert app.screen.focused is cards[1]
        await pilot.press("down")
        await pilot.pause()
        assert app.screen.focused is cards[9]
        await pilot.press("up")
        await pilot.pause()
        assert app.screen.focused is cards[1]
        await pilot.press("left")
        await pilot.pause()
        assert app.screen.focused is cards[0]


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
        for _ in range(3):
            await pilot.press("enter")
            await pilot.pause(0.1)
        await pilot.pause(1.0)

        from nekomata.screens.draw import DrawScreen, SpreadSlot
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
async def test_draw_escape_goes_home():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "esc test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        assert isinstance(app.screen, DrawScreen)

        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_draw_screen_has_spread_info():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "spread label test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        assert isinstance(app.screen, DrawScreen)
        title = app.screen.query_one("#draw-title")
        rendered = str(title.render())
        assert "单牌" in rendered


@pytest.mark.asyncio
async def test_draw_screen_has_deck_cards():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "deck test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen, DeckCard
        assert isinstance(app.screen, DrawScreen)
        deck_cards = list(app.screen.query(DeckCard))
        assert len(deck_cards) > 0


@pytest.mark.asyncio
async def test_spread_select_digit_key():
    """Pressing '1' on spread select screen picks single card spread."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "digit key test"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        await pilot.press("1")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        assert isinstance(app.screen, DrawScreen)


@pytest.mark.asyncio
async def test_input_cleared_after_submit():
    """Input field is cleared after submitting a question."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "clear test"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)
        inp = app.screen.query_one("#prompt-input")
        assert inp.value == ""


@pytest.mark.asyncio
async def test_draw_escape_goes_home_from_multi_spread():
    """Esc from a multi-card spread draw screen returns to home."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "multi esc test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        assert isinstance(app.screen, DrawScreen)

        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_spread_select_shows_position_preview():
    """Spread select screen shows position names in preview area."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "preview test"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        desc = app.screen.query_one("#preview-desc")
        positions = app.screen.query_one("#preview-positions")
        rendered = f"{desc.render()}\n{positions.render()}"
        assert "Daily" in rendered


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


@pytest.mark.asyncio
async def test_detail_panel_has_content_after_first_flip():
    """After the last flip opens detail, it should be populated immediately."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "detail first open"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.2)

        preview = app.screen.query_one("#card-preview")
        content = app.screen.query_one("#preview-content")
        assert preview.has_class("visible")
        assert str(content.render()).strip()
