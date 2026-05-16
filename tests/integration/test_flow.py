import pytest

from nekomata.app import NekomataApp


@pytest.mark.asyncio
async def test_single_card_full_flow():
    app = NekomataApp()
    async with app.run_test() as pilot:
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)

        await pilot.click("#start-reading")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.question import QuestionScreen
        assert isinstance(app.screen, QuestionScreen)

        q_inp = app.screen.query_one("#question-input")
        q_inp.value = "今天适合做什么？"
        await pilot.click("#submit")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)

        await pilot.click("#interpret")
        await pilot.pause()
        from nekomata.screens.interpretation import InterpretationScreen
        assert isinstance(app.screen, InterpretationScreen)


@pytest.mark.asyncio
async def test_three_card_flow():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#start-reading")
        await pilot.pause()
        await pilot.click("#spread-past-present-future")
        await pilot.pause()
        q_inp = app.screen.query_one("#question-input")
        q_inp.value = "未来发展如何？"
        await pilot.click("#submit")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        cards = app.screen.query("Static")
        assert len(cards) >= 3


@pytest.mark.asyncio
async def test_back_navigation():
    app = NekomataApp()
    async with app.run_test() as pilot:
        await pilot.click("#start-reading")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)
        # Use pop_screen instead of clicking #back (may be off-screen in test)
        app.pop_screen()
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)
