"""Shared TUI utilities for Nekomata screens."""

from textual.screen import Screen


def go_home(screen: Screen) -> None:
    """Pop screens until HomeScreen is on top, then reset its input."""
    from nekomata.tui.screens.home import HomeScreen

    while len(screen.app.screen_stack) > 1 and not isinstance(
        screen.app.screen, HomeScreen
    ):
        screen.app.pop_screen()
    home = screen.app.screen
    if isinstance(home, HomeScreen):
        home.resume()
