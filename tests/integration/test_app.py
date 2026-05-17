import pytest

from nekomata.app import NekomataApp


@pytest.mark.asyncio
async def test_app_starts():
    app = NekomataApp()
    async with app.run_test() as pilot:
        assert app.screen is not None


@pytest.mark.asyncio
async def test_home_screen_has_title():
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        title = app.screen.query_one("#title")
        assert "███████" in str(title.render())


@pytest.mark.asyncio
async def test_home_screen_has_input():
    app = NekomataApp()
    async with app.run_test() as pilot:
        assert app.screen.query_one("#prompt-input") is not None


@pytest.mark.asyncio
async def test_home_screen_hides_command_suggestions_by_default():
    app = NekomataApp()
    async with app.run_test() as pilot:
        suggestions = app.screen.query_one("#command-suggestions")
        assert not suggestions.display


@pytest.mark.asyncio
async def test_home_screen_shows_command_suggestions_while_typing_slash():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/"
        await pilot.pause()
        suggestions = app.screen.query_one("#command-suggestions")
        assert suggestions.display
        rendered = str(suggestions.render())
        assert "/browse" in rendered
        assert "/quit" in rendered
        assert "Browse" in rendered or "Exit" in rendered


@pytest.mark.asyncio
async def test_home_screen_tab_completes_matching_command():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
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
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.pause()
        suggestions = app.screen.query_one("#command-suggestions")
        assert not suggestions.display


@pytest.mark.asyncio
async def test_home_screen_help_command():
    """The /help command shows a help panel and clears the input."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        await pilot.press("slash")
        await pilot.press("h")
        await pilot.press("e")
        await pilot.press("l")
        await pilot.press("p")
        await pilot.press("enter")
        await pilot.pause(0)
        await pilot.pause(0)
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)
        assert inp.value == ""


@pytest.mark.asyncio
async def test_home_screen_status_command():
    """The /status command shows current configuration."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/status"
        await pilot.press("enter")
        await pilot.pause(0)
        await pilot.pause(0)
        await pilot.pause(0)
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)
        suggestions = app.screen.query_one("#command-suggestions")
        assert suggestions.display
        rendered = str(suggestions.render())
        assert "Backend" in rendered or "Model" in rendered
        assert inp.value == ""


@pytest.mark.asyncio
async def test_navigate_to_spread_select():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "test question"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)


@pytest.mark.asyncio
async def test_spread_select_has_options():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "test"
        await pilot.press("enter")
        await pilot.pause()
        buttons = app.screen.query("Button")
        ids = [b.id for b in buttons if b.id]
        assert "spread-single" in ids
        assert "spread-past_present_future" in ids


@pytest.mark.asyncio
async def test_reading_screen_shows_cards():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "test question"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)


@pytest.mark.asyncio
async def test_reading_screen_card_preview():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "preview test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        assert app.screen.query_one("#card-preview") is not None
