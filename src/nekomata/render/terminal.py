"""Terminal capability detection for render mode selection."""


import shutil


def get_render_mode() -> str:
    """Detect terminal size and return render mode: full/medium/compact/text."""
    cols, rows = shutil.get_terminal_size()
    if cols >= 160 and rows >= 50:
        return "full"
    if cols >= 120 and rows >= 40:
        return "medium"
    if cols >= 80 and rows >= 24:
        return "compact"
    return "text"
