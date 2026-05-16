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
        assert "NEKOMATA · 猫又塔罗 · 像素风猫咪占卜" not in str(title.render())


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
        assert "/browse" in str(suggestions.render())
        assert "/quit" in str(suggestions.render())


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
async def test_navigate_to_spread_select():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "测试问题"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)


@pytest.mark.asyncio
async def test_spread_select_has_options():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "测试"
        await pilot.press("enter")
        await pilot.pause()
        buttons = app.screen.query("Button")
        ids = [b.id for b in buttons if b.id]
        assert "spread-single" in ids
        assert "spread-past-present-future" in ids


@pytest.mark.asyncio
async def test_reading_screen_shows_cards():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "测试问题"
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
        inp.value = "预览测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        assert app.screen.query_one("#card-preview") is not None


@pytest.mark.asyncio
async def test_full_flow_to_interpretation():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "完整流程测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.click("#interpret")
        await pilot.pause()
        from nekomata.screens.interpretation import InterpretationScreen
        assert isinstance(app.screen, InterpretationScreen)
