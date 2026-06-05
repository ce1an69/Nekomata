"""TCSS stylesheet for the draw screen (extracted for readability)."""

from nekomata.core.render.styles import EASE_OUT
from nekomata.tui.screens.draw_constants import (
    DETAIL_PANEL_WIDTH,
    INTERP_MAX_HEIGHT,
    INTERP_MIN_HEIGHT,
    INTERP_PANEL_HEIGHT,
)

DRAW_SCREEN_CSS = f"""
DrawScreen {{
    align: center top;
}}
#draw-header {{
    text-align: center;
    height: auto;
    margin-bottom: 0;
}}
#draw-divider {{
    color: $surface2;
    text-align: center;
    height: 1;
}}
#draw-title {{
    color: $mauve;
    text-style: bold;
    text-align: center;
}}
#draw-question {{
    color: $subtext0;
    text-align: center;
}}
#deck-section {{
    height: auto;
    min-height: 32;
    padding: 0 1;
    margin: 0 0;
    border: round transparent;
    border-bottom: round $surface0;
    background: $crust;
    transition: opacity 420ms {EASE_OUT}, offset 420ms {EASE_OUT}, border 180ms {EASE_OUT};
}}
#deck-section.box-active {{
    border-bottom: round $mauve;
}}
#deck-label {{
    background: $crust;
    color: $lavender;
    text-style: bold;
    text-align: center;
    margin: 0 0 1 0;
}}
#deck-row {{
    height: auto;
    padding: 0 1;
    align: center middle;
}}
.deck-row-line {{
    height: auto;
    margin: 0 0 1 0;
    align: center middle;
}}
#main-area {{
    height: 1fr;
    margin-top: 0;
    transition: offset 280ms {EASE_OUT};
}}
#reading-area {{
    height: 1fr;
    width: 1fr;
}}
#left-pane {{
    width: 1fr;
    height: 1fr;
}}
#spread-area {{
    width: 1fr;
    height: 1fr;
    padding: 1 0;
    align: center middle;
    border: round transparent;
    transition: border 180ms {EASE_OUT};
}}
#spread-area.box-active {{
    border: round $mauve;
}}
#spread-label {{
    color: $lavender;
    text-style: bold;
    text-align: center;
    margin: 0 0 1 0;
}}
#spread-grid {{
    height: auto;
    align: center middle;
}}
#spread-grid.layout-1 {{
    layout: grid;
    grid-size: 1;
    grid-columns: 18;
}}
#spread-grid.layout-3 {{
    layout: grid;
    grid-size: 3 1;
    grid-columns: 18 18 18;
}}
#spread-grid.layout-5 {{
    layout: grid;
    grid-size: 5 1;
    grid-columns: 18 18 18 18 18;
}}
#spread-grid.layout-10 {{
    layout: grid;
    grid-size: 5 2;
    grid-columns: 18 18 18 18 18;
    grid-rows: auto auto;
}}
#card-preview {{
    width: {DETAIL_PANEL_WIDTH};
    min-width: {DETAIL_PANEL_WIDTH};
    height: 1fr;
    border: round $surface0;
    background: $mantle;
    padding: 1 1;
    align: center top;
    opacity: 0;
    display: none;
    offset: 4 0;
    transition: opacity 280ms {EASE_OUT}, offset 340ms {EASE_OUT}, border 180ms {EASE_OUT};
}}
#card-preview.box-active {{
    border: round $mauve;
}}
#card-preview .card-detail-frame {{
    width: 100%;
    height: auto;
    align: center middle;
    background: $crust;
    border: round $lavender;
    padding: 1 1;
}}
#card-preview .card-detail {{
    width: 50%;
    height: auto;
    background: $crust;
}}
#card-preview Static {{
    background: $mantle;
}}
#card-preview.visible {{
    display: block;
    opacity: 1;
    offset: 0 0;
}}
#draw-footer {{
    dock: bottom;
    height: 1;
    color: $overlay0;
    text-align: center;
    padding: 0 2;
}}
#interp-dialog {{
    width: 1fr;
    height: {INTERP_PANEL_HEIGHT};
    min-height: {INTERP_MIN_HEIGHT};
    max-height: {INTERP_MAX_HEIGHT};
    display: none;
    border: round $surface1;
    background: $mantle;
    padding: 0 1;
    margin: 0 1 0 1;
    opacity: 0;
    offset: 0 2;
    transition: width 300ms {EASE_OUT}, border 180ms {EASE_OUT};
}}
#interp-dialog.box-active {{
    border: round $mauve;
}}
#interp-dialog.visible {{
    display: block;
    opacity: 1;
    offset: 0 0;
}}
#interp-dialog.fullscreen {{
    max-height: 999;
    margin-top: 0;
}}
#interp-dialog-title {{
    color: $mauve;
    text-style: bold;
    height: 1;
    margin: 0;
}}
#interp-dialog-content {{
    color: $text;
    margin: 0;
}}
#interp-dialog-hints {{
    color: $overlay0;
    height: 1;
    margin: 0;
}}
#followup-section {{
    dock: bottom;
    width: 100%;
    height: 3;
    margin: 0 0 1 0;
    padding: 0;
    background: transparent;
    display: none;
    opacity: 0;
    offset: 0 1;
    align: center middle;
    transition: opacity 240ms {EASE_OUT}, offset 300ms {EASE_OUT};
}}
#followup-section.visible {{
    display: block;
    opacity: 1;
    offset: 0 0;
}}
#followup-input {{
    width: 50;
    height: 3;
    padding: 0 1;
    border: round $mauve;
    background: transparent;
    color: $text;
}}
#followup-input:focus {{
    border: round $pink;
    background: transparent;
}}
#status {{
    text-align: center;
    color: $mauve;
    height: auto;
}}
"""
