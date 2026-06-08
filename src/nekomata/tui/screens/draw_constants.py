"""Shared layout and animation constants for the draw screen and its sub-modules."""

from nekomata.core.i18n import lazy_section

# ── Shared i18n ───────────────────────────────────────────────────────
_STR = lazy_section("draw")

# ── Deck layout ──────────────────────────────────────────────────────
NUM_DECK_CARDS = 48
DECK_ROW_COUNT = 4
DECK_CARD_WIDTH = 9
DECK_CARD_HEIGHT = 7
SPREAD_SLOT_WIDTH = 16
SPREAD_SLOT_HEIGHT = 12

# ── Animation timing ─────────────────────────────────────────────────
PICK_COMPLETE_DELAY = 0.0
SLOT_FLIP_FADE_OUT = 0.14
SLOT_FLIP_SWAP_PAUSE = 0.12
SLOT_FLIP_FADE_IN = 0.28
SLOT_FLIP_GLOW_HOLD = 0.16
DECK_ENTRANCE_STAGGER = 0.025
DECK_EXIT_DURATION = 0.18
DECK_ENTRANCE_FADE = 0.18
SPREAD_SLOT_ENTRANCE_STAGGER = 0.07
SPREAD_SLOT_ENTRANCE_FADE = 0.28

# ── Interpretation dialog layout ─────────────────────────────────────
INTERP_PANEL_HEIGHT = "46%"  # CSS-only; runtime code uses _panel_height_cells()
INTERP_PANEL_HEIGHT_RATIO = 0.46
INTERP_MIN_HEIGHT = 14
INTERP_MAX_HEIGHT = 30
INTERP_SIDE_MARGIN = 1
SCROLL_NEAR_BOTTOM_THRESHOLD = 2
INTERP_DETAIL_GAP = 0
INTERP_FULL_SIDE_MARGIN = 5
INTERP_FULL_WIDTH_CORRECTION = 4
INTERP_FULLSCREEN_VERTICAL_CHROME = 5
INTERP_FULLSCREEN_SIDE_MARGIN = 1
DETAIL_PANEL_WIDTH = 66
FOLLOWUP_BOTTOM_MARGIN = 5

# ── Panel animation timing ───────────────────────────────────────────
PANEL_ENTRANCE_DURATION = 0.28
PANEL_EXIT_DURATION = 0.22
PANEL_FADE_OUT_DURATION = 0.14
PANEL_SWAP_DELAY = 0.16
PANEL_FADE_IN_DURATION = 0.22
FOLLOWUP_ENTRANCE_DURATION = 0.24
FOLLOWUP_EXIT_DURATION = 0.18

# ── Shimmer / completion ─────────────────────────────────────────────
SHIMMER_INITIAL_DELAY = 0.01
SHIMMER_STAGGER = 0.08
SHIMMER_GLOW_HOLD = 0.22

# ── Detail panel ─────────────────────────────────────────────────────
DETAIL_UPDATE_DEBOUNCE = 0.08

# ── Spread entrance ──────────────────────────────────────────────────
SPREAD_ENTRANCE_DELAY = 0.05
SPREAD_CENTER_DURATION = 0.22

# ── Interpretation dialog extras ─────────────────────────────────────
INTERP_ENTRANCE_DURATION = 0.30
TIMER_SLACK = 0.01
DECK_EXIT_SLEEP_SLACK = 0.02
