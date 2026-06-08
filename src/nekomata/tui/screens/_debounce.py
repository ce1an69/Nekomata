"""Lightweight debounce helper for deferring UI renders on rapid input."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from textual.screen import Screen


class DebouncedCall:
    """Debounce a callback: rapid schedule() calls collapse into one delayed invocation.

    Usage::

        debouncer = DebouncedCall(screen, 0.08, my_callback)
        debouncer.schedule(arg1, arg2)   # cancels previous, schedules new
        debouncer.cancel()               # stops pending invocation
    """

    def __init__(self, screen: Screen, delay: float, callback: Callable[..., None]) -> None:
        self._screen = screen
        self._delay = delay
        self._callback = callback
        self._timer = None
        self._pending: tuple[Any, ...] | None = None

    def schedule(self, *args: Any) -> None:
        """Cancel any pending invocation and schedule a new one with the given args."""
        self._pending = args
        if self._timer is not None:
            self._timer.stop()
        self._timer = self._screen.set_timer(self._delay, self._run)

    def cancel(self) -> None:
        """Stop the pending timer and discard stored args."""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._pending = None

    def _run(self) -> None:
        self._timer = None
        pending = self._pending
        self._pending = None
        if pending is not None:
            self._callback(*pending)
