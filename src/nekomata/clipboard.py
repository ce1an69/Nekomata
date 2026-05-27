"""Clipboard operations — text copy and image copy using platform tools."""

import logging
import platform
import shutil
import subprocess
import tempfile

log = logging.getLogger(__name__)


def copy_text(text: str) -> bool:
    """Copy text to system clipboard. Returns True on success."""
    system = platform.system()
    try:
        if system == "Darwin":
            proc = subprocess.run(
                ["pbcopy"], input=text.encode("utf-8"), capture_output=True,
            )
            return proc.returncode == 0
        if system == "Linux":
            if shutil.which("xclip"):
                proc = subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode("utf-8"), capture_output=True,
                )
                return proc.returncode == 0
            if shutil.which("xsel"):
                proc = subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=text.encode("utf-8"), capture_output=True,
                )
                return proc.returncode == 0
        if system == "Windows":
            proc = subprocess.run(
                ["clip"], input=text.encode("utf-8"), capture_output=True,
            )
            return proc.returncode == 0
    except Exception:
        log.exception("Text copy failed")
    return False


def copy_image(png_path: str) -> bool:
    """Copy a PNG image file to system clipboard. Returns True on success."""
    system = platform.system()
    try:
        if system == "Darwin":
            return _copy_image_macos(png_path)
        if system == "Linux":
            return _copy_image_linux(png_path)
    except Exception:
        log.exception("Image copy failed")
    return False


def _copy_image_macos(png_path: str) -> bool:
    """Copy image to clipboard on macOS using osascript + AppKit."""
    script = (
        'use framework "AppKit"\n'
        f'set imgPath to "{png_path}"\n'
        "set theImage to current application's NSImage's alloc()'s "
        "initWithContentsOfFile:imgPath\n"
        "set thePasteboard to current application's NSPasteboard's generalPasteboard()\n"
        "thePasteboard's clearContents()\n"
        "thePasteboard's writeObjects:{theImage}\n"
    )
    proc = subprocess.run(
        ["osascript", "-e", script], capture_output=True, timeout=5,
    )
    return proc.returncode == 0


def _copy_image_linux(png_path: str) -> bool:
    """Copy image to clipboard on Linux using xclip."""
    if shutil.which("xclip"):
        proc = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", png_path],
            capture_output=True,
        )
        return proc.returncode == 0
    return False
