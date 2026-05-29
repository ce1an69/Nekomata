import pytest

from nekomata.app import NekomataApp


@pytest.mark.asyncio
async def test_draw_escape_goes_home():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "esc test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        assert isinstance(app.screen, DrawScreen)

        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_draw_screen_has_spread_info():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "spread label test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        assert isinstance(app.screen, DrawScreen)
        title = app.screen.query_one("#draw-title")
        rendered = str(title.render())
        assert "Single Card" in rendered


@pytest.mark.asyncio
async def test_draw_screen_has_deck_cards():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "deck test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen, DeckCard
        assert isinstance(app.screen, DrawScreen)
        deck_cards = list(app.screen.query(DeckCard))
        assert len(deck_cards) > 0


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
        from nekomata.screens.draw import DrawScreen
        assert isinstance(app.screen, DrawScreen)


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
async def test_draw_escape_goes_home_from_multi_spread():
    """Esc from a multi-card spread draw screen returns to home."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "multi esc test"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-past_present_future")
        await pilot.pause()
        from nekomata.screens.draw import DrawScreen
        assert isinstance(app.screen, DrawScreen)

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
async def test_detail_panel_has_content_after_first_flip():
    """After the last flip opens detail, it should be populated immediately."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "detail first open"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.2)

        preview = app.screen.query_one("#card-preview")
        spread_area = app.screen.query_one("#spread-area")
        assert preview.has_class("visible")
        assert preview.region.y + preview.region.height == spread_area.region.y + spread_area.region.height
        assert len(preview.children) > 0


@pytest.mark.asyncio
async def test_detail_card_image_is_centered():
    """The detail panel card image should be horizontally centered."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "detail image centered"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.2)

        preview = app.screen.query_one("#card-preview")
        frame = preview.query_one(".card-origin-frame")
        image = preview.query_one(".card-origin")

        frame_center = frame.region.x + frame.region.width / 2
        image_center = image.region.x + image.region.width / 2
        assert abs(frame_center - image_center) <= 1


@pytest.mark.asyncio
async def test_q_during_interpretation_confirms_then_returns_home():
    """Q during interpretation should confirm before going home."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "confirm exit interpretation"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.0)

        from nekomata.screens.draw import DrawScreen
        from nekomata.screens.draw_widgets import ConfirmExitInterpretation
        from nekomata.screens.home import HomeScreen

        assert isinstance(app.screen, DrawScreen)
        app.screen._dialog.show()
        await pilot.pause(0.2)
        preview = app.screen.query_one("#card-preview")
        dialog = app.screen.query_one("#interp-dialog")
        assert dialog.region.y + dialog.region.height == preview.region.y + preview.region.height

        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmExitInterpretation)

        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_detail_panel_keeps_interpretation_height_after_toggle():
    """Reopening detail during interpretation should keep it aligned with the dialog."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "toggle detail during interpretation"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.0)

        from nekomata.screens.draw import DrawScreen

        assert isinstance(app.screen, DrawScreen)
        app.screen._dialog.show()
        await pilot.pause(0.2)

        await pilot.press("d")
        await pilot.pause(0.2)
        await pilot.press("d")
        await pilot.pause(0.2)

        preview = app.screen.query_one("#card-preview")
        dialog = app.screen.query_one("#interp-dialog")
        preview_bottom = preview.region.y + preview.region.height
        dialog_bottom = dialog.region.y + dialog.region.height
        assert preview.has_class("visible")
        assert dialog_bottom == preview_bottom


@pytest.mark.asyncio
async def test_fullscreen_interpretation_keeps_top_visible():
    """Fullscreen interpretation should not make the whole screen scroll."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test(size=(198, 62)) as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "fullscreen interpretation top visible"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.0)

        from nekomata.screens.draw import DrawScreen

        assert isinstance(app.screen, DrawScreen)
        app.screen._dialog.show(
            sync_layout=app.screen._sync_interp_layout,
            fit_height=lambda: app.screen._dialog.fit_height(
                app.screen._w_main_area,
                app.screen._detail.visible,
            ),
        )
        await pilot.pause(0.2)

        if app.screen._detail.visible:
            await pilot.press("d")
            await pilot.pause(0.2)

        await pilot.press("h")
        await pilot.pause(0.2)

        dialog = app.screen.query_one("#interp-dialog")
        divider = app.screen.query_one("#draw-divider")
        content = app.screen.content_region
        assert app.screen._dialog.fullscreen
        assert dialog.region.y == divider.region.y + divider.region.height
        assert dialog.region.x - content.x == content.right - dialog.region.right
        assert dialog.region.y + dialog.region.height < app.screen.size.height
        assert app.screen.max_scroll_y == 0


@pytest.mark.asyncio
async def test_fullscreen_can_toggle_detail_panel():
    """Fullscreen mode should still allow the detail panel layout."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test(size=(198, 62)) as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "fullscreen detail toggle"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.0)

        from nekomata.screens.draw import DrawScreen

        assert isinstance(app.screen, DrawScreen)
        app.screen._dialog.show(
            sync_layout=app.screen._sync_interp_layout,
            fit_height=lambda: app.screen._dialog.fit_height(
                app.screen._w_main_area,
                app.screen._detail.visible,
            ),
        )
        await pilot.pause(0.2)

        if app.screen._detail.visible:
            await pilot.press("d")
            await pilot.pause(0.2)

        await pilot.press("h")
        await pilot.pause(0.2)

        dialog = app.screen.query_one("#interp-dialog")
        full_width = dialog.region.width

        await pilot.press("d")
        await pilot.pause(0.2)

        preview = app.screen.query_one("#card-preview")
        assert app.screen._dialog.fullscreen
        assert app.screen._detail.visible
        assert preview.has_class("visible")
        assert dialog.region.width < full_width
        assert preview.region.x >= dialog.region.right
        assert app.screen.max_scroll_y == 0

        await pilot.press("d")
        await pilot.pause(0.2)

        assert not app.screen._detail.visible
        assert dialog.region.width == full_width


@pytest.mark.asyncio
async def test_fullscreen_hint_hidden_before_interpretation_starts():
    """The footer should not advertise fullscreen before the dialog exists."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "fullscreen hint hidden"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.0)

        from nekomata.screens.draw import DrawScreen

        assert isinstance(app.screen, DrawScreen)
        footer = app.screen.query_one("#draw-footer")
        assert "H " not in str(footer.render())


@pytest.mark.asyncio
async def test_footer_hides_interpret_hint_after_interpretation_starts():
    """Once the dialog is open, the footer should not repeat I interpret."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "footer interpret hint"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.0)

        from nekomata.screens.draw import DrawScreen

        assert isinstance(app.screen, DrawScreen)
        app.screen._dialog.show(
            sync_layout=app.screen._sync_interp_layout,
            fit_height=lambda: app.screen._dialog.fit_height(
                app.screen._w_main_area,
                app.screen._detail.visible,
            ),
        )
        app.screen._update_footer_fullscreen()

        footer = str(app.screen.query_one("#draw-footer").render())
        assert "I " not in footer
        assert "Esc " in footer


@pytest.mark.asyncio
async def test_interpretation_hints_do_not_duplicate_shortcut_keys():
    """Hint strings already include their shortcut keys."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "hint duplication"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.0)

        from nekomata.screens.draw import DrawScreen

        assert isinstance(app.screen, DrawScreen)
        app.screen._first_interp_done = True
        app.screen._update_followup_hints()

        hints = str(app.screen.query_one("#interp-dialog-hints").render())
        assert "F F " not in hints
        assert "C C " not in hints
        assert "E E " not in hints


@pytest.mark.asyncio
async def test_fullscreen_toggle_during_stream_does_not_show_action_hints():
    """Toggling fullscreen mid-stream should not show completed interpretation actions."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "streaming fullscreen hints"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.0)

        from nekomata.screens.draw import DrawScreen

        assert isinstance(app.screen, DrawScreen)
        app.screen._dialog.show(
            sync_layout=app.screen._sync_interp_layout,
            fit_height=lambda: app.screen._dialog.fit_height(
                app.screen._w_main_area,
                app.screen._detail.visible,
            ),
        )
        app.screen._first_interp_done = False
        app.screen._w_interp_hints.update("loading")

        await pilot.press("h")
        await pilot.pause()

        hints = str(app.screen.query_one("#interp-dialog-hints").render())
        assert "copy text" not in hints
        assert "export image" not in hints


@pytest.mark.asyncio
async def test_loading_hint_keeps_rotating_between_stream_chunks():
    """Loading hint should keep animating while the model stream is temporarily quiet."""
    app = NekomataApp()
    app.animation_enabled = False
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "loading hint keeps rotating"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#spread-single")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause(1.0)
        await pilot.press("enter")
        await pilot.pause(1.0)

        from nekomata.ai.interpreter import StreamChunk
        from nekomata.screens.draw import DrawScreen

        assert isinstance(app.screen, DrawScreen)
        app.screen._dialog.show()
        app.screen._stream.append_chunk(StreamChunk("猫", "thinking"))
        await pilot.pause(0.3)

        assert app.screen._stream_timer is None
        assert app.screen._loading_timer is not None
        first_hint = str(app.screen.query_one("#interp-dialog-hints").render())

        await pilot.pause(2.1)
        second_hint = str(app.screen.query_one("#interp-dialog-hints").render())
        assert first_hint != second_hint
