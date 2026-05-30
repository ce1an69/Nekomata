import pytest

from nekomata.app import NekomataApp
from nekomata.screens.card_browser import CardBrowserScreen


@pytest.mark.asyncio
async def test_navigate_to_card_browser():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, CardBrowserScreen)


@pytest.mark.asyncio
async def test_card_browser_has_filter_buttons():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        buttons = app.screen.query("#filter-bar Button")
        ids = [b.id for b in buttons if b.id]
        assert "filter-all" in ids
        assert "filter-major" in ids
        assert "filter-cups" in ids


@pytest.mark.asyncio
async def test_card_browser_shows_cards():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        assert len(items) > 0


@pytest.mark.asyncio
async def test_card_browser_shows_card_count():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        count = app.screen.query_one("#card-count")
        assert "78" in str(count.render())


@pytest.mark.asyncio
async def test_card_browser_filter_by_suit():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#filter-cups")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        assert len(items) == 78  # all items mounted; filtered ones are display:none


@pytest.mark.asyncio
async def test_card_browser_filter_updates_count():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.click("#filter-major")
        await pilot.pause()
        count = app.screen.query_one("#card-count")
        assert "22/78" in str(count.render())


@pytest.mark.asyncio
async def test_card_browser_back():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, CardBrowserScreen)
        await pilot.press("escape")
        await pilot.pause()
        from nekomata.screens.home import HomeScreen
        assert isinstance(app.screen, HomeScreen)


@pytest.mark.asyncio
async def test_card_browser_list_items_have_numbers():
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        first_text = str(items[0].render())
        assert "0" in first_text or "The Fool" in first_text


@pytest.mark.asyncio
async def test_card_browser_detail_updates_on_focus():
    """Focusing a card item updates the detail panel."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        assert len(items) > 0
        items[0].focus()
        await pilot.pause()
        detail = app.screen.query_one("#card-detail")
        # Detail panel should have content (not the placeholder)
        children = list(detail.children)
        assert len(children) > 0


@pytest.mark.asyncio
async def test_card_browser_detail_wraps_card_image_in_frame():
    """Browser detail keeps image layout on a normal Textual container."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        items[0].focus()
        await pilot.pause()

        detail = app.screen.query_one("#card-detail")
        frame = detail.query_one(".card-origin-frame")
        image = frame.query_one(".card-origin")

        assert frame is not None
        assert image is not None


@pytest.mark.asyncio
async def test_card_browser_ignores_duplicate_detail_refresh():
    """Focusing the same card again should not rebuild the detail panel."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        items[0].focus()
        await pilot.pause()

        detail = app.screen.query_one("#card-detail")
        children = tuple(detail.children)
        items[0]._show_detail()
        await pilot.pause()

        assert tuple(detail.children) == children


@pytest.mark.asyncio
async def test_card_browser_reversal_refreshes_detail():
    """Changing orientation should rebuild the current card detail."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        items[0].focus()
        await pilot.pause()

        detail_text = app.screen.query_one("#detail-text-slot")
        before = str(detail_text.render())
        await pilot.press("r")
        await pilot.pause()

        assert str(detail_text.render()) != before


@pytest.mark.asyncio
async def test_card_browser_detail_slots_stay_stable_between_cards():
    """Switching cards updates slot content without moving detail layout."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        items[0].focus()
        await pilot.pause()

        detail = app.screen.query_one("#card-detail")
        image_slot = app.screen.query_one("#detail-image-slot")
        text_slot = app.screen.query_one("#detail-text-slot")
        detail_children = tuple(detail.children)
        image_region = image_slot.region
        text_region = text_slot.region
        first_text = str(text_slot.render())

        items[1].focus()
        await pilot.pause()

        assert tuple(detail.children) == detail_children
        assert image_slot.region == image_region
        assert text_slot.region == text_region
        assert str(text_slot.render()) != first_text


@pytest.mark.asyncio
async def test_card_browser_selected_state():
    """Focusing a card adds the .selected class."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        items[0].focus()
        await pilot.pause()
        assert items[0].has_class("selected")


@pytest.mark.asyncio
async def test_card_browser_card_list_uses_up_down_arrows():
    """Up/down should move through cards when the list is focused."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        items = list(app.screen.query("CardListItem"))
        assert len(items) >= 2

        items[0].focus()
        await pilot.pause()
        await pilot.press("down")
        await pilot.pause()
        assert app.screen.focused is items[1]
        await pilot.press("up")
        await pilot.pause()
        assert app.screen.focused is items[0]


@pytest.mark.asyncio
async def test_card_browser_tab_cycles_all_panels():
    """Tab cycles: card list → filter buttons → card list."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()

        items = app.screen.query("CardListItem")
        assert len(items) > 0
        items[0].focus()
        await pilot.pause()
        assert isinstance(app.screen.focused, type(items[0]))

        # Tab: card → first filter button
        await pilot.press("tab")
        await pilot.pause()
        from textual.widgets import Button
        assert isinstance(app.screen.focused, Button)
        assert app.screen.focused.id == "filter-all"

        # Tab through remaining filter buttons
        filter_buttons = list(app.screen.query("#filter-bar Button"))
        for _ in range(len(filter_buttons) - 1):
            await pilot.press("tab")
            await pilot.pause()

        # Now on last filter, Tab should wrap to first card
        await pilot.press("tab")
        await pilot.pause()
        assert isinstance(app.screen.focused, type(items[0]))


@pytest.mark.asyncio
async def test_card_browser_reversal_toggle():
    """R key toggles reversed preview in the browser."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()
        items = app.screen.query("CardListItem")
        items[0].focus()
        await pilot.pause()

        # Default: not reversed
        assert app.screen._reversed_preview is False

        # Press R to toggle
        await pilot.press("r")
        await pilot.pause()
        assert app.screen._reversed_preview is True

        # Press R again to toggle back
        await pilot.press("r")
        await pilot.pause()
        assert app.screen._reversed_preview is False


@pytest.mark.asyncio
async def test_card_browser_reversal_indicator():
    """Card count shows reversal indicator when R is toggled on."""
    app = NekomataApp()
    async with app.run_test() as pilot:
        inp = app.screen.query_one("#prompt-input")
        inp.value = "/browse"
        await pilot.press("enter")
        await pilot.pause()

        # Initially no reversal indicator
        count = app.screen.query_one("#card-count")
        assert "reversed preview" not in str(count.render())

        # Toggle reversal on
        items = app.screen.query("CardListItem")
        items[0].focus()
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause(0)
        await pilot.pause(0)
        await pilot.pause(0)

        # Verify internal state toggled
        assert app.screen._reversed_preview is True
        count = app.screen.query_one("#card-count")
        assert "reversed preview" in str(count.render())
