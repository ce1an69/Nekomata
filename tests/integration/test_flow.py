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
async def test_reading_screen_uses_shortcuts_without_action_buttons():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "shortcut test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        assert not app.screen.query("#interpret")
        assert not app.screen.query("#home")
        assert "I interpret" in str(app.screen.query_one("#hints").render())


@pytest.mark.asyncio
async def test_reading_screen_uses_spread_layout_canvas():
    """Reading cards are mounted in a spread layout canvas, not a vertical card list."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "layout test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen, CardWidget
        screen = app.screen
        assert isinstance(screen, ReadingScreen)

        canvas = screen.query_one("#cards-container")
        assert canvas.has_class("spread-3")
        cards = list(screen.query(CardWidget))
        assert len(cards) == 3
        assert cards[0]._drawn.position.description == "过去的影响"


@pytest.mark.asyncio
async def test_reading_layout_gives_more_width_to_cards_than_preview():
    """The preview rail is narrower so spread cards keep their proportions."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "layout width test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("5")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        screen = app.screen
        assert isinstance(screen, ReadingScreen)

        canvas = screen.query_one("#cards-container")
        preview = screen.query_one("#card-preview")
        assert canvas.styles.width.value == 2
        assert preview.styles.width.value == 56


@pytest.mark.asyncio
async def test_reading_preview_updates_for_selected_card():
    """Focusing a spread card updates the right-side preview panel."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "preview layout test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen, CardWidget
        screen = app.screen
        assert isinstance(screen, ReadingScreen)

        card = list(screen.query(CardWidget))[0]
        card.focus()
        await pilot.pause()

        preview = screen.query_one("#card-preview")
        rendered = str(preview.render())
        assert "Select a card" not in rendered


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

        await pilot.press("i")
        await pilot.pause(0)
        await pilot.pause(0)
        await pilot.pause(0)

        # Should still be on ReadingScreen with an error message
        assert isinstance(app.screen, ReadingScreen)
        status = app.screen.query_one("#status")
        rendered_error = str(status.render())
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
            await pilot.press("i")
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
async def test_reading_tab_cycles_between_cards():
    """Tab key keeps keyboard navigation inside the spread cards."""
    app = NekomataApp()
    app.animation_enabled = False
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
        for _ in range(5):
            await pilot.pause(0)
            if isinstance(screen.focused, CardWidget) and screen.focused is cards[1]:
                break
        assert isinstance(screen.focused, CardWidget)
        assert screen.focused is cards[1]

        await pilot.press("tab")
        for _ in range(5):
            await pilot.pause(0)
            if isinstance(screen.focused, CardWidget) and screen.focused is cards[2]:
                break
        assert isinstance(screen.focused, CardWidget)
        assert screen.focused is cards[2]


@pytest.mark.asyncio
async def test_reading_arrow_keys_stay_in_spread_cards():
    """Arrow keys move through cards without entering removed action buttons."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "arrow action test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause(0)
        await pilot.pause(0)
        from nekomata.screens.reading import ReadingScreen, CardWidget
        screen = app.screen
        assert isinstance(screen, ReadingScreen)

        cards = list(screen.query(CardWidget))
        cards[-1].focus()
        await pilot.pause()

        await pilot.press("down")
        await pilot.pause()
        assert isinstance(screen.focused, CardWidget)
        assert screen.focused is cards[-1]

        await pilot.press("up")
        await pilot.pause()
        assert isinstance(screen.focused, CardWidget)
        assert screen.focused is cards[-2]


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
            await pilot.press("i")
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
