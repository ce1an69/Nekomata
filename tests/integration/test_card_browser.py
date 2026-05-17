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
        assert len(items) == 14


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
        await pilot.click("#back")
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
        assert "愚者" in first_text


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
async def test_card_browser_tab_cycles_all_panels():
    """Tab cycles: card list → filter buttons → back button → card list."""
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

        # Tab: last filter → back button (skip through remaining filters)
        filter_buttons = list(app.screen.query("#filter-bar Button"))
        for _ in range(len(filter_buttons) - 1):
            await pilot.press("tab")
            await pilot.pause()

        # Now on last filter, Tab should go to back button
        await pilot.press("tab")
        await pilot.pause()
        assert app.screen.focused.id == "back"

        # Tab: back button → wrap to first card
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
        assert "逆位" not in str(count.render())

        # Toggle reversal on
        items = app.screen.query("CardListItem")
        items[0].focus()
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()

        count = app.screen.query_one("#card-count")
        assert "逆位" in str(count.render())
