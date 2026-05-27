import pytest
from textual.widgets import Input

from nekomata.app import NekomataApp


@pytest.mark.asyncio
async def test_app_starts():
    app = NekomataApp()
    async with app.run_test():
        assert app.screen is not None


@pytest.mark.asyncio
async def test_home_screen_has_title():
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test():
        title = app.screen.query_one("#title")
        rendered = str(title.render())
        assert "Nekomata" in rendered


@pytest.mark.asyncio
async def test_home_screen_has_input():
    app = NekomataApp()
    async with app.run_test():
        assert app.screen.query_one("#prompt-input") is not None


@pytest.mark.asyncio
async def test_home_screen_hides_command_suggestions_by_default():
    app = NekomataApp()
    async with app.run_test():
        suggestions = app.screen.query_one("#command-suggestions")
        assert not suggestions.display


@pytest.mark.asyncio
async def test_home_screen_shows_command_suggestions_while_typing_slash():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/"
        await pilot.pause()
        suggestions = app.screen.query_one("#command-suggestions")
        assert suggestions.display
        rendered = str(suggestions.render())
        assert "/browse" in rendered
        assert "/config" in rendered
        assert "/quit" in rendered


@pytest.mark.asyncio
async def test_home_screen_tab_completes_matching_command():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/br"
        await pilot.press("tab")
        await pilot.pause()
        assert inp.value == "/browse"
        assert not app.screen.query_one("#command-suggestions").display


@pytest.mark.asyncio
async def test_home_screen_hides_suggestions_on_exact_match():
    """Typing a full command name hides the suggestion dropdown."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/browse"
        await pilot.pause()
        suggestions = app.screen.query_one("#command-suggestions")
        assert not suggestions.display


@pytest.mark.asyncio
async def test_home_screen_config_command():
    """The /config command opens the setup screen."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/config"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.setup import SetupScreen
        assert isinstance(app.screen, SetupScreen)


@pytest.mark.asyncio
async def test_home_screen_ctrl_q_exits():
    """Pressing Ctrl+Q exits the app."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+q")
        await pilot.pause()
        assert app._exit


@pytest.mark.asyncio
async def test_navigate_to_spread_select():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "test question"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)


@pytest.mark.asyncio
async def test_spread_select_has_options():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "test"
        await pilot.press("enter")
        await pilot.pause()
        options = app.screen.query("SpreadOption")
        ids = [option.id for option in options if option.id]
        assert "spread-single" in ids
        assert "spread-past_present_future" in ids


@pytest.mark.asyncio
async def test_draw_screen_shows_deck():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "test question"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        from nekomata.screens.draw_widgets import DeckCard, SpreadSlot
        assert isinstance(app.screen, DrawScreen)
        deck_cards = app.screen.query(DeckCard)
        assert len(deck_cards) > 0
        slots = app.screen.query(SpreadSlot)
        assert len(slots) == 1  # single card spread


@pytest.mark.asyncio
async def test_draw_screen_has_spread_slots():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "preview test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        from nekomata.screens.draw_widgets import SpreadSlot
        assert isinstance(app.screen, DrawScreen)
        slots = app.screen.query(SpreadSlot)
        assert len(slots) == 3  # three card spread
