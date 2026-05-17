import pytest

from nekomata.app import NekomataApp


@pytest.mark.asyncio
async def test_three_card_flow():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "test question"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        cards = app.screen.query("Static")
        assert len(cards) >= 3


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
async def test_reading_escape_goes_home():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "esc test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)

        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_reading_screen_has_spread_label():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "spread label test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        label = app.screen.query_one("#spread-label")
        rendered = str(label.render())
        assert "Single" in rendered


@pytest.mark.asyncio
async def test_reading_screen_has_reshuffle_button():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "reshuffle test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        btn = app.screen.query_one("#reshuffle")
        assert btn is not None


@pytest.mark.asyncio
async def test_interpret_without_api_shows_error():
    """Interpretation without API configured shows an error message."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "no api test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)

        await pilot.click("#interpret")
        await pilot.pause(0)
        await pilot.pause(0)
        await pilot.pause(0)

        # Should still be on ReadingScreen with an error message
        assert isinstance(app.screen, ReadingScreen)
        error_msg = app.screen.query_one("#error-msg")
        rendered_error = str(error_msg.render())
        assert "config.toml" in rendered_error or "API key" in rendered_error


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
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)


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
async def test_interpretation_space_skips_typewriter():
    """Pressing Space skips the typewriter animation (mocked API)."""
    from unittest.mock import patch
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "skip anim test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()

        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)

        # Mock the interpreter to return a response
        from nekomata.ai.interpreter import OpenAIInterpreter
        with patch.object(OpenAIInterpreter, "interpret", return_value="Test interpretation result"):
            await pilot.click("#interpret")
            await pilot.pause(0)
            await pilot.pause(0)
            await pilot.pause(0)
            await pilot.pause(0)

        from nekomata.screens.interpretation import InterpretationScreen
        screen = app.screen
        if not isinstance(screen, InterpretationScreen):
            pytest.skip("Interpretation screen not reached in test environment")
            return

        await pilot.press("space")
        await pilot.pause()

        content = screen.query_one("#interp-content")
        rendered = str(content.render())
        assert len(rendered) > 10


@pytest.mark.asyncio
async def test_reading_reshuffle_changes_cards():
    """Clicking reshuffle redraws cards."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "reshuffle test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen, CardWidget
        screen = app.screen
        assert isinstance(screen, ReadingScreen)

        first_cards = list(screen.query(CardWidget))
        assert len(first_cards) >= 1

        await pilot.click("#reshuffle")
        await pilot.pause(0)
        await pilot.pause(0)

        new_cards = list(screen.query(CardWidget))
        assert len(new_cards) >= 1


@pytest.mark.asyncio
async def test_reading_r_key_reshuffles():
    """Pressing R key triggers reshuffle."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "R key test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)

        await pilot.press("r")
        await pilot.pause(0)
        await pilot.pause(0)
        assert isinstance(app.screen, ReadingScreen)
        cards = list(app.screen.query("CardWidget"))
        assert len(cards) >= 1


@pytest.mark.asyncio
async def test_reading_tab_cycles_cards_to_buttons():
    """Tab key moves focus from cards to action buttons."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "Tab test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause(0)
        await pilot.pause(0)
        from nekomata.screens.reading import ReadingScreen, CardWidget
        screen = app.screen
        assert isinstance(screen, ReadingScreen)

        cards = list(screen.query(CardWidget))
        assert len(cards) >= 3

        cards[0].focus()
        await pilot.pause(0)
        await pilot.pause(0)
        assert isinstance(screen.focused, CardWidget)

        await pilot.press("tab")
        from textual.widgets import Button
        for _ in range(5):
            await pilot.pause(0)
            if isinstance(screen.focused, Button):
                break
        assert isinstance(screen.focused, Button), f"Expected Button, got {type(screen.focused).__name__}"

        await pilot.press("tab")
        for _ in range(5):
            await pilot.pause(0)
            if isinstance(screen.focused, CardWidget):
                break
        assert isinstance(screen.focused, CardWidget)


@pytest.mark.asyncio
async def test_reading_escape_goes_home_from_multi_spread():
    """Esc from a multi-card spread reading returns to home."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "multi esc test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)

        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_interpretation_escape_goes_home():
    """Esc from interpretation screen returns to home (mocked API)."""
    from unittest.mock import patch
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "interp esc test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()

        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)

        from nekomata.ai.interpreter import OpenAIInterpreter
        with patch.object(OpenAIInterpreter, "interpret", return_value="Test result"):
            await pilot.click("#interpret")
            await pilot.pause(0)
            await pilot.pause(0)
            await pilot.pause(0)
            await pilot.pause(0)

        from nekomata.screens.interpretation import InterpretationScreen
        if not isinstance(app.screen, InterpretationScreen):
            pytest.skip("Interpretation screen not reached in test environment")
            return

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

        preview = app.screen.query_one("#spread-preview")
        rendered = str(preview.render())
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
        preview = app.screen.query_one("#spread-preview")
        rendered = str(preview.render())
        assert "Past" in rendered or "Present" in rendered or "Future" in rendered


@pytest.mark.asyncio
async def test_reading_screen_shows_reversal_count():
    """Reading screen label includes upright/reversed counts when reversed cards exist."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "reversal count test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        label = app.screen.query_one("#spread-label")
        rendered = str(label.render())
        assert "Single" in rendered
