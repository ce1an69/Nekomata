"""Unit tests for LayoutHints responsive calculations."""

from nekomata.tui.screens.layout_hints import LayoutHints


class TestBreakpoints:
    def test_narrow_below_120(self):
        assert LayoutHints(119, 40, "compact").is_narrow is True
        assert LayoutHints(120, 40, "compact").is_narrow is False

    def test_tiny_below_100_width(self):
        assert LayoutHints(99, 40, "compact").is_tiny is True
        assert LayoutHints(100, 40, "compact").is_tiny is False

    def test_tiny_below_28_height(self):
        assert LayoutHints(120, 27, "compact").is_tiny is True
        assert LayoutHints(120, 28, "compact").is_tiny is False


class TestDeckLayout:
    def test_wide_terminal_fits_12_per_row(self):
        hints = LayoutHints(160, 50, "full")
        assert hints.deck_cards_per_row == 12

    def test_120_col_terminal_fits_10_per_row(self):
        hints = LayoutHints(120, 40, "medium")
        assert hints.deck_cards_per_row == 10

    def test_80_col_terminal_fits_fewer(self):
        hints = LayoutHints(80, 24, "compact")
        # (80 - 4) // 11 = 6
        assert hints.deck_cards_per_row == 6

    def test_minimum_4_per_row(self):
        hints = LayoutHints(40, 24, "text")
        assert hints.deck_cards_per_row == 4

    def test_row_count_for_48_cards(self):
        hints = LayoutHints(160, 50, "full")
        assert hints.deck_row_count == 4  # 48 / 12

        hints = LayoutHints(120, 40, "medium")
        assert hints.deck_row_count == 5  # 48 / 10, ceil

    def test_min_height_scales_with_rows(self):
        wide = LayoutHints(160, 50, "full")
        assert wide.deck_section_min_height == 36  # 4 rows × 8 + 4

        narrow = LayoutHints(80, 24, "compact")
        # 6 cards/row → 8 rows → 8*8+4=68
        assert narrow.deck_section_min_height == 68


class TestSpreadSlotSizes:
    def test_default_size_for_wide(self):
        hints = LayoutHints(160, 50, "full")
        assert hints.spread_slot_width == 16
        assert hints.spread_slot_height == 12

    def test_compact_size_for_narrow(self):
        hints = LayoutHints(100, 40, "compact")
        assert hints.spread_slot_width == 14
        assert hints.spread_slot_height == 12

    def test_text_mode_smallest(self):
        hints = LayoutHints(80, 24, "text")
        assert hints.spread_slot_width == 12
        assert hints.spread_slot_height == 8

    def test_short_terminal_reduces_height(self):
        hints = LayoutHints(140, 26, "compact")
        assert hints.spread_slot_height == 10

    def test_grid_col_width_includes_margin(self):
        hints = LayoutHints(160, 50, "full")
        assert hints.spread_grid_col_width == 18  # 16 + 2


class TestDetailPanel:
    def test_side_by_side_above_140(self):
        hints = LayoutHints(160, 50, "full")
        assert hints.detail_stacked is False

    def test_stacked_below_140(self):
        hints = LayoutHints(130, 40, "compact")
        assert hints.detail_stacked is True

    def test_stacked_width_fills_terminal(self):
        hints = LayoutHints(100, 40, "compact")
        assert hints.detail_panel_width == 96  # 100 - 4

    def test_side_by_side_width_adjusts_to_slot_size(self):
        hints = LayoutHints(160, 50, "full")
        # min(66, 160 - 18*5 - 6) = min(66, 64) = 64
        assert hints.detail_panel_width == 64
