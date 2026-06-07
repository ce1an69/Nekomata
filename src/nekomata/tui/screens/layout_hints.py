"""Responsive layout calculations shared across screens.

Pure computation — no Textual dependencies. Feed terminal dimensions and
render mode, get layout parameters back.
"""

from __future__ import annotations

import math


class LayoutHints:
    """Computed layout parameters based on terminal size and render mode."""

    def __init__(self, width: int, height: int, render_mode: str) -> None:
        self.width = width
        self.height = height
        self.render_mode = render_mode

    # -- Breakpoints --------------------------------------------------------

    @property
    def is_narrow(self) -> bool:
        """True if terminal is too narrow for side-by-side detail panel."""
        return self.width < 120

    @property
    def is_tiny(self) -> bool:
        """True if terminal is too small for normal layout."""
        return self.width < 100 or self.height < 28

    # -- Deck layout --------------------------------------------------------

    @property
    def deck_cards_per_row(self) -> int:
        """Number of deck cards per row that fits the current width."""
        # Each card: width=9 + margin=1+1 = 11 cols
        available = self.width - 4  # 2 padding each side for #deck-section
        return max(4, min(12, available // 11))

    @property
    def deck_row_count(self) -> int:
        """Number of rows needed for the full deck."""
        from nekomata.tui.screens.draw_constants import NUM_DECK_CARDS

        return math.ceil(NUM_DECK_CARDS / self.deck_cards_per_row)

    @property
    def deck_section_min_height(self) -> int:
        """Min height for deck section in current terminal."""
        # Each row: 7 (card height) + 1 (row margin) = 8
        # + 2 for label + 2 for padding
        return self.deck_row_count * 8 + 4

    # -- Spread slot sizes --------------------------------------------------

    @property
    def spread_slot_width(self) -> int:
        """SpreadSlot width for current terminal."""
        if self.render_mode == "text":
            return 12
        if self.is_narrow:
            return 14
        return 16

    @property
    def spread_slot_height(self) -> int:
        """SpreadSlot height for current terminal."""
        if self.render_mode == "text":
            return 8
        if self.height < 30:
            return 10
        return 12

    @property
    def spread_grid_col_width(self) -> int:
        """Grid column width (slot width + 2 margin)."""
        return self.spread_slot_width + 2

    # -- Detail panel -------------------------------------------------------

    @property
    def detail_stacked(self) -> bool:
        """True if detail panel should dock below instead of side-by-side."""
        return self.width < 140

    @property
    def detail_panel_width(self) -> int:
        """Detail panel width for current terminal."""
        if self.detail_stacked:
            return self.width - 4
        return min(66, self.width - self.spread_grid_col_width * 5 - 6)
