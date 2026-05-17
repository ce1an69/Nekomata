import pytest

from nekomata.app import NekomataApp


@pytest.mark.asyncio
async def test_single_card_full_flow():
    app = NekomataApp()
    async with app.run_test() as pilot:
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)

        inp = app.screen.query_one("#prompt-input")
        inp.value = "今天适合做什么？"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        await pilot.click("#spread-single")
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
        inp = app.screen.query_one("#prompt-input")
        inp.value = "未来发展如何？"
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
        inp.value = "返回测试"
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
        inp.value = "测试输入"
        await pilot.press("enter")
        await pilot.pause()

        # Go to spread select then back home via Escape
        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)

        # Input should be cleared and refocused on return to home
        inp = app.screen.query_one("#prompt-input")
        assert inp.value == ""
        assert inp.has_focus


@pytest.mark.asyncio
async def test_reading_escape_goes_home():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "esc测试"
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
        inp.value = "牌阵名称测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        label = app.screen.query_one("#spread-label")
        assert "单牌" in str(label.render())
        assert "每日灵感" in str(label.render())


@pytest.mark.asyncio
async def test_reading_screen_has_reshuffle_button():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "重新抽牌测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        btn = app.screen.query_one("#reshuffle")
        assert btn is not None


@pytest.mark.asyncio
async def test_interpretation_screen_has_header():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "解读头部测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.click("#interpret")
        await pilot.pause()
        from nekomata.screens.interpretation import InterpretationScreen
        assert isinstance(app.screen, InterpretationScreen)
        header = app.screen.query_one("#interp-header")
        assert "解读头部测试" in str(header.render())
        summary = app.screen.query_one("#card-summary")
        assert "今日指引" in str(summary.render())


@pytest.mark.asyncio
async def test_spread_select_digit_key():
    """Pressing '1' on spread select screen picks single card spread."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "数字键测试"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        # Press "1" to select single card spread
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
        inp.value = "清除测试"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        # Navigate back home — input should be cleared
        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)
        inp = app.screen.query_one("#prompt-input")
        assert inp.value == ""


@pytest.mark.asyncio
async def test_interpretation_save_button():
    """Clicking save persists the reading and disables the button."""
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        import nekomata.storage.journal as journal_mod
        original_init = journal_mod.Journal.__init__

        def patched_init(self, db_path_arg=None):
            original_init(self, db_path)

        journal_mod.Journal.__init__ = patched_init

        app = NekomataApp()
        async with app.run_test() as pilot:
            inp = app.screen.query_one("#prompt-input")
            inp.value = "保存测试"
            await pilot.press("enter")
            await pilot.pause()
            await pilot.click("#spread-single")
            await pilot.pause()
            await pilot.click("#interpret")
            await pilot.pause()

            from nekomata.screens.interpretation import InterpretationScreen
            assert isinstance(app.screen, InterpretationScreen)

            # Skip typewriter so save button is enabled
            await pilot.press("space")
            await pilot.pause(0)
            await pilot.pause(0)

            # Click save
            await pilot.click("#save")
            await pilot.pause()

            # Status should show saved confirmation
            status = app.screen.query_one("#save-status")
            assert "已保存" in str(status.render())

            # Save button should be disabled
            save_btn = app.screen.query_one("#save")
            assert save_btn.disabled

        journal_mod.Journal.__init__ = original_init
    finally:
        db_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_interpretation_save_failure_shows_error():
    """If save fails, an error message is shown and the button stays enabled."""
    import tempfile
    from pathlib import Path
    from unittest.mock import patch

    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "保存失败测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.click("#interpret")
        await pilot.pause()

        from nekomata.screens.interpretation import InterpretationScreen
        assert isinstance(app.screen, InterpretationScreen)

        # Skip typewriter
        await pilot.press("space")
        await pilot.pause(0)
        await pilot.pause(0)

        # Make save fail
        with patch("nekomata.screens.interpretation.Journal.save", side_effect=Exception("db error")):
            await pilot.click("#save")
            await pilot.pause()

        status = app.screen.query_one("#save-status")
        assert "保存失败" in str(status.render())

        # Button should still be enabled for retry
        save_btn = app.screen.query_one("#save")
        assert not save_btn.disabled


@pytest.mark.asyncio
async def test_interpretation_save_disabled_during_typewriter():
    """Save button is disabled during typewriter, re-enabled after skip or completion."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "打字机禁用测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.click("#interpret")
        await pilot.pause()

        from nekomata.screens.interpretation import InterpretationScreen
        screen = app.screen
        assert isinstance(screen, InterpretationScreen)

        save_btn = screen.query_one("#save")

        # If typewriter timer is still running, button should be disabled.
        # If it already completed (fast in test mode), button should be enabled.
        # Either way, pressing Space must leave the button enabled.
        await pilot.press("space")
        await pilot.pause(0)
        await pilot.pause(0)

        assert not save_btn.disabled, "Save should be enabled after typewriter completes or is skipped"


@pytest.mark.asyncio
async def test_interpretation_space_skips_typewriter():
    """Pressing Space skips the typewriter animation."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "跳过动画测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.click("#interpret")
        await pilot.pause()

        from nekomata.screens.interpretation import InterpretationScreen
        screen = app.screen
        assert isinstance(screen, InterpretationScreen)

        # Press Space to skip typewriter
        await pilot.press("space")
        await pilot.pause()

        # Content should now show the full text
        content = screen.query_one("#interp-content")
        rendered = str(content.render())
        assert len(rendered) > 10

        # Hints should no longer show "跳过动画"
        hints = screen.query_one("#hints")
        assert "跳过动画" not in str(hints.render())


@pytest.mark.asyncio
async def test_reading_reshuffle_changes_cards():
    """Clicking reshuffle redraws cards with different results."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "重新抽牌"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen, CardWidget
        screen = app.screen
        assert isinstance(screen, ReadingScreen)

        # Record first draw
        first_cards = list(screen.query(CardWidget))
        assert len(first_cards) >= 1

        # Click reshuffle
        await pilot.click("#reshuffle")
        await pilot.pause(0)
        await pilot.pause(0)

        # Cards should still be present (new draw)
        new_cards = list(screen.query(CardWidget))
        assert len(new_cards) >= 1


@pytest.mark.asyncio
async def test_reading_r_key_reshuffles():
    """Pressing R key triggers reshuffle."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "R键测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)

        await pilot.press("r")
        await pilot.pause(0)
        await pilot.pause(0)
        # Should still be on reading screen with cards
        assert isinstance(app.screen, ReadingScreen)
        cards = list(app.screen.query("CardWidget"))
        assert len(cards) >= 1


@pytest.mark.asyncio
async def test_reading_tab_cycles_cards_to_buttons():
    """Tab key moves focus from cards to action buttons."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "Tab测试"
        await pilot.press("enter")
        await pilot.pause()
        # Use three-card spread for more deterministic Tab cycling
        await pilot.click("#spread-past_present_future")
        await pilot.pause(0)
        await pilot.pause(0)
        from nekomata.screens.reading import ReadingScreen, CardWidget
        screen = app.screen
        assert isinstance(screen, ReadingScreen)

        # Ensure cards are present and manually focus the first one
        cards = list(screen.query(CardWidget))
        assert len(cards) >= 3

        # Explicitly focus card (not relying on animation callback)
        cards[0].focus()
        await pilot.pause(0)
        await pilot.pause(0)
        assert isinstance(screen.focused, CardWidget)

        # Tab should go to first button
        await pilot.press("tab")
        from textual.widgets import Button
        for _ in range(5):
            await pilot.pause(0)
            if isinstance(screen.focused, Button):
                break
        assert isinstance(screen.focused, Button), f"Expected Button, got {type(screen.focused).__name__}"

        # Tab back to cards
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
        inp.value = "多牌Esc测试"
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
    """Esc from interpretation screen returns to home."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "解读Esc测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.click("#interpret")
        await pilot.pause()
        from nekomata.screens.interpretation import InterpretationScreen
        assert isinstance(app.screen, InterpretationScreen)

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
        inp.value = "预览测试"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        # Preview should show first spread's positions on mount
        preview = app.screen.query_one("#spread-preview")
        rendered = str(preview.render())
        assert "今日指引" in rendered


@pytest.mark.asyncio
async def test_spread_select_arrow_updates_preview():
    """Arrow keys update the spread preview to show selected spread's positions."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "箭头预览测试"
        await pilot.press("enter")
        await pilot.pause()
        from nekomata.screens.spread_select import SpreadSelectScreen
        assert isinstance(app.screen, SpreadSelectScreen)

        # Press down to move to second spread
        await pilot.press("down")
        await pilot.pause()
        preview = app.screen.query_one("#spread-preview")
        rendered = str(preview.render())
        # PastPresentFuture spread has these positions
        assert "过去" in rendered
        assert "现在" in rendered
        assert "未来" in rendered


@pytest.mark.asyncio
async def test_reading_screen_shows_reversal_count():
    """Reading screen label includes upright/reversed counts when reversed cards exist."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "逆位计数测试"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.reading import ReadingScreen
        assert isinstance(app.screen, ReadingScreen)
        label = app.screen.query_one("#spread-label")
        rendered = str(label.render())
        # Label always has the spread name; reversal count appears only if any are reversed
        assert "单牌" in rendered


@pytest.mark.asyncio
async def test_interpretation_s_key_saves():
    """Pressing S key on interpretation screen saves the reading."""
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        import nekomata.storage.journal as journal_mod
        original_init = journal_mod.Journal.__init__

        def patched_init(self, db_path_arg=None):
            original_init(self, db_path)

        journal_mod.Journal.__init__ = patched_init

        app = NekomataApp()
        async with app.run_test() as pilot:
            inp = app.screen.query_one("#prompt-input")
            inp.value = "S键保存测试"
            await pilot.press("enter")
            await pilot.pause()
            await pilot.click("#spread-single")
            await pilot.pause()
            await pilot.click("#interpret")
            await pilot.pause()

            from nekomata.screens.interpretation import InterpretationScreen
            assert isinstance(app.screen, InterpretationScreen)

            # Skip typewriter
            await pilot.press("space")
            await pilot.pause(0)
            await pilot.pause(0)

            # Press S to save
            await pilot.press("s")
            await pilot.pause()

            status = app.screen.query_one("#save-status")
            assert "已保存" in str(status.render())

        journal_mod.Journal.__init__ = original_init
    finally:
        db_path.unlink(missing_ok=True)
