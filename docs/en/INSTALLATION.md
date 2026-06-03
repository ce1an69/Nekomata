# Installation Guide

Install Nekomata via PyPI, or set up from source for development.

**[中文版](../zh/INSTALLATION.md)**

---

## Install from PyPI

The simplest way to get started:

```bash
pip install nekomata-tarot
```

> Requires **Python 3.13+**. If you don't have Python, see [python.org](https://www.python.org/) or use your system package manager.

After installation, launch with:

```bash
nekomata-tarot          # TUI mode (default)
nekomata-tarot -c       # CLI mode
nekomata-tarot --desktop  # Desktop mode (requires extra deps, see below)
```

### Desktop Mode

Desktop mode requires additional dependencies. Install them with:

```bash
pip install "nekomata-tarot[desktop]"
```

---

## Install from Source

For development or if you want the latest unreleased changes.

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** (recommended package manager)

### Steps

```bash
git clone https://github.com/ce1an69/Nekomata.git
cd Nekomata
uv sync
```

For the full development setup (desktop + dev tools):

```bash
uv sync --extra desktop --extra dev
```

### Optional Dependency Groups

| Group | Install Command | Contents |
|-------|----------------|----------|
| `desktop` | `uv sync --extra desktop` | PyWebView, FastAPI, uvicorn, PyInstaller |
| `dev` | `uv sync --extra dev` | pytest, pytest-asyncio, pytest-mock, pyright |

---

## Verify Installation

```bash
nekomata-tarot --help
```

If you see the help output, the installation was successful.

## Troubleshooting

### `command not found: nekomata-tarot`

Make sure your Python `bin/` directory is in your `PATH`. With `uv`, you can also run directly:

```bash
uv run nekomata-tarot
```

### `ImportError: no module named 'textual'`

Reinstall the package:

```bash
pip install --force-reinstall nekomata-tarot
```

### TUI shows text-only cards

Your terminal may not support Kitty Graphics Protocol or Sixel. For the best experience, use **Kitty**, **Ghostty**, or **Contour**. See the [README](../../README.md) for the full compatibility table.
