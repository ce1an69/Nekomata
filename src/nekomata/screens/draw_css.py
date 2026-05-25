"""TCSS stylesheet for the draw screen (extracted for readability)."""

from nekomata.render.styles import (
    C_CRUST, C_LAVENDER, C_MANTLE, C_MAUVE, C_OVERLAY0,
    C_SUBTEXT0, C_SURFACE0, C_SURFACE1, C_SURFACE2, C_TEXT,
    EASE_OUT, EASE_SPRING,
)
from nekomata.screens.draw_dialog import DETAIL_PANEL_WIDTH, INTERP_PANEL_HEIGHT, INTERP_MIN_HEIGHT, INTERP_MAX_HEIGHT

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
    color: {C_SURFACE2};
    text-align: center;
    height: 1;
}}
#draw-title {{
    color: {C_MAUVE};
    text-style: bold;
    text-align: center;
}}
#draw-question {{
    color: {C_SUBTEXT0};
    text-align: center;
}}
#deck-section {{
    height: auto;
    min-height: 32;
    padding: 0 1;
    margin: 0 0;
    border: round transparent;
    border-bottom: round {C_SURFACE0};
    background: {C_CRUST};
    transition: opacity 420ms {EASE_OUT}, offset 420ms {EASE_OUT}, border 180ms {EASE_OUT};
}}
#deck-section.box-active {{
    border-bottom: round {C_MAUVE};
}}
#deck-label {{
    background: {C_CRUST};
    color: {C_LAVENDER};
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
    transition: offset 280ms {EASE_SPRING};
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
    border: round {C_MAUVE};
}}
#spread-label {{
    color: {C_LAVENDER};
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
    dock: right;
    width: {DETAIL_PANEL_WIDTH};
    min-width: {DETAIL_PANEL_WIDTH};
    height: 1fr;
    border: round {C_SURFACE0};
    background: {C_MANTLE};
    padding: 1 1;
    align: center top;
    opacity: 0;
    display: none;
    offset: 4 0;
    transition: opacity 240ms {EASE_OUT}, offset 320ms {EASE_SPRING}, border 180ms {EASE_OUT};
}}
#card-preview.box-active {{
    border: round {C_MAUVE};
}}
#card-preview .card-origin-frame {{
    width: 100%;
    height: auto;
    align: center middle;
    background: {C_CRUST};
    border: round {C_LAVENDER};
    padding: 1 1;
}}
#card-preview .card-origin {{
    width: 50%;
    height: auto;
    background: {C_CRUST};
}}
#card-preview Static {{
    background: {C_MANTLE};
}}
#card-preview.visible {{
    display: block;
    opacity: 1;
    offset: 0 0;
}}
#draw-footer {{
    dock: bottom;
    height: 1;
    color: {C_OVERLAY0};
    text-align: center;
    padding: 0 2;
}}
#interp-dialog {{
    dock: bottom;
    width: 1fr;
    height: {INTERP_PANEL_HEIGHT};
    min-height: {INTERP_MIN_HEIGHT};
    max-height: {INTERP_MAX_HEIGHT};
    display: none;
    border: round {C_SURFACE1};
    background: {C_MANTLE};
    padding: 0 1;
    margin: 0 1 1 1;
    opacity: 0;
    offset: 0 2;
    transition: opacity 240ms {EASE_OUT}, offset 320ms {EASE_SPRING}, width 220ms {EASE_OUT}, border 180ms {EASE_OUT};
}}
#interp-dialog.box-active {{
    border: round {C_MAUVE};
}}
#interp-dialog.visible {{
    display: block;
    opacity: 1;
    offset: 0 0;
}}
#interp-dialog-title {{
    color: {C_MAUVE};
    text-style: bold;
    height: 1;
    margin: 0;
}}
#interp-dialog-content {{
    color: {C_TEXT};
    margin: 0;
}}
#interp-dialog-hints {{
    color: {C_OVERLAY0};
    height: 1;
    margin: 0;
}}
#status {{
    text-align: center;
    color: {C_MAUVE};
    height: auto;
}}
"""
