import pytest
from textual.widgets import Input

from nekomata.tui.app import NekomataApp


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
        from nekomata.tui.screens.setup import SetupScreen

        assert isinstance(app.screen, SetupScreen)


@pytest.mark.asyncio
async def test_home_screen_unknown_slash_command_shows_error():
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/missing"
        await pilot.press("enter")
        await pilot.pause()

        suggestions = app.screen.query_one("#command-suggestions")
        assert suggestions.display
        assert "/missing" in str(suggestions.render())


@pytest.mark.asyncio
async def test_home_screen_arrow_selects_suggestion_and_right_accepts():
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/"
        await pilot.pause()

        await pilot.press("down")
        await pilot.pause()
        assert app.screen._suggestion_idx == 0

        await pilot.press("up")
        await pilot.pause()
        assert app.screen._suggestion_idx == len(app.screen._suggestion_matches) - 1

        expected = app.screen._suggestion_matches[-1]
        await pilot.press("right")
        await pilot.pause()
        assert inp.value == expected


@pytest.mark.asyncio
async def test_home_screen_quit_command_exits():
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/quit"
        await pilot.press("enter")
        await pilot.pause()

        assert app._exit


@pytest.mark.asyncio
async def test_home_screen_ctrl_q_exits():
    """Pressing Ctrl+Q exits the app."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+q")
        await pilot.pause()
        assert app._exit


@pytest.mark.asyncio
async def test_setup_screen_validates_required_fields():
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/config"
        await pilot.press("enter")
        await pilot.pause()

        app.screen.query_one("#api-url-input", Input).value = ""
        app.screen.query_one("#model-input", Input).value = "test-model"
        app.screen._save()
        await pilot.pause()

        error = app.screen.query_one("#setup-error")
        assert error.display
        assert str(error.render())


@pytest.mark.asyncio
async def test_setup_screen_validates_model_required():
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/config"
        await pilot.press("enter")
        await pilot.pause()

        app.screen.query_one("#api-url-input", Input).value = "https://example.test/v1"
        app.screen.query_one("#model-input", Input).value = ""
        app.screen._save()
        await pilot.pause()

        error = app.screen.query_one("#setup-error")
        assert error.display
        assert str(error.render())


@pytest.mark.asyncio
async def test_setup_screen_navigation_moves_between_fields():
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/config"
        await pilot.press("enter")
        await pilot.pause()

        api_url = app.screen.query_one("#api-url-input", Input)
        api_key = app.screen.query_one("#api-key-input", Input)
        model = app.screen.query_one("#model-input", Input)

        assert api_url.has_focus
        app.screen._navigate_field(1)
        await pilot.pause()
        assert api_key.has_focus
        app.screen._navigate_field(1)
        await pilot.pause()
        assert model.has_focus
        app.screen._navigate_field(-1)
        await pilot.pause()
        assert api_key.has_focus


@pytest.mark.asyncio
async def test_setup_screen_escape_returns_home():
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/config"
        await pilot.press("enter")
        await pilot.pause()

        app.screen.action_go_back()
        await pilot.pause()

        from nekomata.tui.screens.home import HomeScreen

        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_setup_screen_saves_config_and_returns_home():
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "/config"
        await pilot.press("enter")
        await pilot.pause()

        app.screen.query_one("#api-url-input", Input).value = "https://example.test/v1"
        app.screen.query_one("#api-key-input", Input).value = "sk-new"
        app.screen.query_one("#model-input", Input).value = "model-new"
        app.screen._save()
        await pilot.pause()

        from nekomata.tui.screens.home import HomeScreen

        assert isinstance(app.screen, HomeScreen)
        assert app.config.api_url == "https://example.test/v1"
        assert app.config.api_key == "sk-new"
        assert app.config.model == "model-new"


@pytest.mark.asyncio
async def test_navigate_to_spread_select():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input", Input)
        inp.value = "test question"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.tui.screens.spread_select import SpreadSelectScreen

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
        from nekomata.tui.screens.draw import DrawScreen
        from nekomata.tui.screens.draw_widgets import DeckCard, SpreadSlot

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
        from nekomata.tui.screens.draw import DrawScreen
        from nekomata.tui.screens.draw_widgets import SpreadSlot

        assert isinstance(app.screen, DrawScreen)
        slots = app.screen.query(SpreadSlot)
        assert len(slots) == 3  # three card spread
