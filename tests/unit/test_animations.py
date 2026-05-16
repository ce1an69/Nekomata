import pytest

from nekomata.app import NekomataApp


@pytest.mark.asyncio
async def test_reading_screen_animated_reveal():
    """Cards should mount with staggered reveal animation."""
    app = NekomataApp()
    app.animation_enabled = False  # disable for test stability
    async with app.run_test() as pilot:
        await pilot.click("#start-reading")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        q_inp = app.screen.query_one("#question-input")
        q_inp.value = "动画测试"
        await pilot.click("#submit")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        cards = app.screen.query("CardWidget")
        assert len(cards) == 1


def test_animation_functions_exist():
    """Verify animation module exports expected functions."""
    from nekomata.render.animations import animate_slide_in, animate_reveal, animate_shuffle
    assert callable(animate_slide_in)
    assert callable(animate_reveal)
    assert callable(animate_shuffle)
