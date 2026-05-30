# Nekomata

English | **[中文](README.md)**

> "Nekomata" comes from the Japanese mythological two-tailed cat spirit, known for shapeshifting and foresight.

A pixel-art cat tarot divination app in your terminal. All 78 cards feature cat-themed artwork, with AI-powered personalized interpretations.

Supports four modes: **TUI** / **CLI** / **Web UI** / **Desktop**.

## Features

- **Full 78-card deck** — 22 Major + 56 Minor Arcana, pixel-art cards, adaptive rendering
- **5 spreads** — Single / Past-Present-Future / Situation-Action-Result / Body-Mind-Spirit / Five-Card Cross
- **AI interpretation** — OpenAI-compatible API, streaming output, follow-up questions, urllib-based (no SDK)
- **Multi-mode UI** — TUI (Catppuccin Mocha) / CLI / Web UI (FastAPI) / Desktop (PyWebView)
- **i18n** — Chinese / English

## Installation

Python 3.13+, [uv](https://docs.astral.sh/uv/) recommended:

```bash
git clone https://github.com/ce1an69/Nekomata.git
cd Nekomata
uv sync
```

Optional deps: `--extra web` / `--extra desktop` (includes Web) / `--extra dev`.

## Usage

```bash
nekomata                  # TUI mode (default)
nekomata -c               # CLI interactive
nekomata -c -q "How's my luck?" -S past_present_future -y  # one-liner
nekomata --web            # Web UI, default port 8080
nekomata-desktop          # native desktop window
```

### CLI Arguments

| Argument            | Description                  |
| ------------------- | ---------------------------- |
| `--web`             | Launch Web UI                |
| `--port PORT`       | Web port (default 8080)      |
| `--cli` / `-c`      | CLI mode                     |
| `-q` / `--question` | Question for reading         |
| `-s` / `--seed`     | Random seed (reproducible)   |
| `-S` / `--spread`   | Spread key                   |
| `-y` / `--yes`      | Skip confirmation            |

### TUI Terminal Compatibility

TUI mode uses Kitty Graphics Protocol / Sixel for pixel-art card rendering. Experience varies by terminal:

| Experience | Terminals | Notes |
|-----------|-----------|-------|
| ✅ Best | **Kitty** · **Ghostty** · **Contour** | Native TGP support, sharpest card rendering |
| 👍 Good | **WezTerm** · **Konsole** · **foot** | Sixel auto-detected, cards display fine |
| 📝 Text-only | Other terminals (e.g. Alacritty, iTerm2) | Falls back to text/colored-block cards |

> 💡 Terminal window of at least **160×50** recommended for full layout. Below **80×24**, text-only mode kicks in.

### TUI Shortcuts

`q`/`Esc` back · `↑↓←→` navigate · `Enter` confirm · `Tab` switch panel · `1`-`6` select spread · `i` interpret · `d` details · `r` toggle reversed

## Configuration

First launch opens a setup wizard for the AI backend (API URL / key / model / language).

Settings saved in `.neko/settings.json`. Override via env vars: `NEKOMATA_API_URL` / `NEKOMATA_API_KEY` / `NEKOMATA_MODEL`.

## Tech Stack

Python 3.13+ · Textual · textual-image · Pillow · FastAPI + vanilla JS · PyWebView · urllib (AI) · custom i18n

## Project Structure

```
src/nekomata/        Main code (app / cli / desktop / card / spread / render / ai / screens / web)
assets/              Cards (78×3 variants), cat photos, icons, fonts
data/                Card meanings YAML, i18n JSON, prompt templates
tests/               pytest unit + integration tests
scripts/             Build scripts
```

## Development

```bash
uv sync --extra desktop --extra dev
uv run pytest                  # all tests
uv run pytest --cov=nekomata   # coverage
```

## License

- **Code**: [MIT License](LICENSE)
- **Art assets** (`assets/cards/`): [CC BY-NC-SA 4.0](LICENSE-ASSETS.md)

## Acknowledgments

[Textual](https://textual.textualize.io/) · [textual-image](https://github.com/sarusso/textual-image) · [FastAPI](https://fastapi.tiangolo.com/) · [Catppuccin](https://github.com/catppuccin/catppuccin) · [PyWebView](https://pywebview.flowrl.com/)
