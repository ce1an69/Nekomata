"""Shared TUI utilities for Nekomata screens."""


from textual.screen import Screen


def focus_sibling(screen: Screen, widget_type: type, delta: int) -> None:
    """Move focus to the next/previous focusable widget of a given type.

    Args:
        screen: The active Textual Screen.
        widget_type: The class of widgets to navigate (e.g. CardWidget).
        delta: +1 for next, -1 for previous.
    """
    items = list(screen.query(widget_type))
    if not items:
        return
    focused = screen.focused
    try:
        idx = items.index(focused)
    except ValueError:
        items[0].focus()
        return
    new_idx = idx + delta
    if 0 <= new_idx < len(items):
        items[new_idx].focus()


def go_home(screen: Screen) -> None:
    """Pop screens until HomeScreen is on top, then reset its input."""
    from nekomata.screens.home import HomeScreen
    while len(screen.app.screen_stack) > 1 and not isinstance(screen.app.screen, HomeScreen):
        screen.app.pop_screen()
    home = screen.app.screen
    if isinstance(home, HomeScreen):
        home.resume()
