# Building the Desktop App

Build the Nekomata desktop app from source on macOS / Windows.

## Prerequisites

| Dependency | Minimum Version | Notes |
|-----------|----------------|-------|
| Python | 3.13+ | Windows desktop build requires 3.13 for pywebview WinForms / pythonnet compatibility |
| uv | latest | Package manager for installing dependencies |

## macOS

### 1. Install Prerequisites

```bash
# Python (Homebrew)
brew install python@3.14

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install Project Dependencies

```bash
cd Nekomata
uv sync --extra desktop
```

### 3. Build

```bash
python scripts/build_desktop.py
```

Output: `dist/Nekomata.app` + `dist/Nekomata.dmg`

Open the DMG and drag Nekomata.app into the Applications folder.

### 4. Clean Rebuild

```bash
python scripts/build_desktop.py --clean
```

---

## Windows

### 1. Install Prerequisites

```powershell
# Python (3.13 recommended for packaging, for pywebview Windows backend compatibility)
winget install Python.Python.3.13

# uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install Project Dependencies

```powershell
cd Nekomata
$env:UV_PROJECT_ENVIRONMENT = ".venv-win"
uv sync --python 3.13 --extra desktop
```

### 3. Build

```powershell
.\.venv-win\Scripts\python.exe scripts\build_desktop.py
```

Output: `dist/Nekomata.exe`, a single-file executable with no external `_internal` directory needed.

### 4. Clean Rebuild

```powershell
.\.venv-win\Scripts\python.exe scripts\build_desktop.py --clean
```

---

## Notes

- **WebView engine**: pywebview uses WKWebView on macOS (built-in) and WinForms + Edge WebView2 on Windows (built-in on Win10/11; older Windows requires [Evergreen Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)).
- **Windows Python version**: Windows builds use Python 3.13; Python 3.14 is incompatible with pythonnet and causes WinForms backend initialization failure.
- **Artifact size**: ~50-60 MB (card assets take up most of the space; `_origin.png` and `contact_sheet` are excluded). On Windows, it's a single-file exe that PyInstaller unpacks to a temp directory at startup.
- **TUI dependencies** (textual, rich, PIL, etc.) are excluded from the build; the desktop app does not depend on terminal rendering.
- **Spec file**: Build configuration is in `nekomata.spec`. Edit this file to adjust packaging options (icon, hidden imports, etc.).
