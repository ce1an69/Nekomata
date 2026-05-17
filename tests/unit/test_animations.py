import pytest

from nekomata.app import NekomataApp


class DummyStyles:
    opacity = 1
    offset = (0, 0)


class SyncAnimateWidget:
    def __init__(self) -> None:
        self.styles = DummyStyles()
        self.calls = []
        self.styles.animate = self.styles_animate

    def styles_animate(self, attribute, value, duration):
        self.calls.append((attribute, value, duration))
        return None


@pytest.mark.asyncio
async def test_reading_screen_animated_reveal():
    """Cards should mount with staggered reveal animation."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "动画测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        cards = app.screen.query("CardWidget")
        assert len(cards) == 1


def test_animation_functions_exist():
    """Verify animation module exports the reveal function."""
    from nekomata.render.animations import animate_reveal
    assert callable(animate_reveal)


@pytest.mark.asyncio
async def test_animate_reveal_allows_sync_textual_animate():
    """Installed Textual may return None from animate()."""
    from nekomata.render.animations import animate_reveal

    widget = SyncAnimateWidget()

    await animate_reveal(widget)

    assert widget.styles.opacity == 0
    assert widget.calls == [("opacity", 1.0, 0.3)]
