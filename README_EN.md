# Nekomata

English | **[中文](README.md)**

> "Nekomata" comes from the Japanese mythological two-tailed cat spirit, known for shapeshifting and foresight.

A pixel-art cat tarot divination app in your terminal. All 78 cards feature cat-themed artwork, with AI-powered personalized interpretations.

Supports three modes: **TUI** (terminal), **Web UI** (browser), and **Desktop** (native window).

## Features

### Tarot Card System

- **Full 78-card deck**: 22 Major Arcana + 56 Minor Arcana (Cups, Wands, Swords, Pentacles)
- **Pixel-art cards**: 64x96 pixels, RGBA format, NEAREST interpolation scaling
- **Adaptive rendering**: automatically selects render mode based on terminal size (full / medium / compact / preview / text)
- **Reversed cards**: configurable reversal probability (default 50%)

### Spread System

- **Single Card**: quick reading for daily questions
- **Past-Present-Future**: timeline analysis
- **Situation-Action-Result**: action guidance
- **Body-Mind-Spirit**: inner exploration
- **Five-Card Cross**: multi-dimensional in-depth reading

### AI Interpretation

- **OpenAI-compatible API**: works with any OpenAI-compatible endpoint
- **Streaming output**: real-time interpretation display
- **Follow-up questions**: ask further questions about the reading
- **Structured prompts**: dedicated prompt template per spread type
- **No SDK dependency**: lightweight urllib-based implementation

### Multi-Mode Interface

- **TUI mode**: Textual-based terminal UI with Catppuccin Mocha theme
- **CLI mode**: pure command-line interaction, supports one-liner readings
- **Web UI mode**: FastAPI-based browser interface
- **Desktop mode**: PyWebView native window
- **Internationalization**: supports Chinese / English

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install

```bash
# Clone the repository
git clone https://github.com/ce1an69/Nekomata.git
cd Nekomata

# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### Optional Dependencies

```bash
# Web UI
uv sync --extra web

# Desktop (includes Web UI)
uv sync --extra desktop

# Development (testing, etc.)
uv sync --extra dev

# Everything
uv sync --extra desktop --extra dev
```

## Usage

### TUI Mode (Default)

```bash
nekomata
# or
uv run nekomata
```

### CLI Mode

```bash
# Interactive
nekomata --cli
nekomata -c

# One-liner reading
nekomata -c -q "How's my luck today?" -S past_present_future -y

# With seed (reproducible)
nekomata -c -q "My question" -s 42
```

### Web UI Mode

```bash
nekomata --web              # default port 8080
nekomata --web --port 3000  # custom port
```

### Desktop Mode

```bash
nekomata-desktop            # open native window
nekomata-desktop --debug    # debug mode
```

### Command Line Arguments

| Argument            | Description                                  |
| ------------------- | -------------------------------------------- |
| `--web`             | Launch Web UI mode                           |
| `--port PORT`       | Web server port (default 8080)               |
| `--cli` / `-c`      | Launch CLI mode                              |
| `-q` / `--question` | Question for the reading (CLI mode)          |
| `-s` / `--seed`     | Random seed (reproducible draws)             |
| `-S` / `--spread`   | Spread type key                              |
| `-y` / `--yes`      | Skip confirmation, start reading immediately |

### Keyboard Shortcuts (TUI Mode)

| Key             | Action                         |
| --------------- | ------------------------------ |
| `q` / `Esc`     | Back / Quit                    |
| `↑` `↓` `←` `→` | Navigate                       |
| `Enter`         | Confirm / Select               |
| `Tab`           | Switch focus panel             |
| `1`–`6`         | Quick spread selection         |
| `i`             | AI interpretation              |
| `d`             | Show / hide details            |
| `r`             | Toggle reversed (card browser) |

## Configuration

### First Run

On first launch, a setup wizard guides you through configuring the AI backend:

- API URL (default: `https://api.openai.com/v1`)
- API key
- Model name
- Language (Chinese / English)

### Config File

Settings are saved in `.neko/settings.json` (current directory or `~/.neko/`):

```json
{
  "api_url": "https://api.openai.com/v1",
  "api_key": "sk-...",
  "model": "gpt-4",
  "lang": "en"
}
```

### Environment Variables

Override config via environment variables:

- `NEKOMATA_API_URL`: API URL
- `NEKOMATA_API_KEY`: API key
- `NEKOMATA_MODEL`: model name

## Tech Stack

| Component         | Technology           | Description                       |
| ----------------- | -------------------- | --------------------------------- |
| Language          | Python 3.13+         |                                   |
| TUI Framework     | Textual              | Terminal UI framework             |
| Card Rendering    | textual-image        | Terminal image rendering          |
| Image Processing  | Pillow               | PNG processing and export         |
| AI Interpretation | OpenAI-compatible    | Lightweight urllib implementation |
| Web UI            | FastAPI + vanilla JS | Browser interface                 |
| Desktop           | PyWebView            | Native window                     |
| i18n              | Custom i18n          | en/zh support                     |
| Card Data         | YAML                 | 78-card upright/reversed meanings |
| Config            | JSON                 | User settings                     |

## Project Structure

```
Nekomata/
├── src/nekomata/           # Main package
│   ├── app.py              # TUI entry + argparse
│   ├── cli.py              # Pure CLI mode
│   ├── desktop.py          # PyWebView desktop entry
│   ├── _paths.py           # Path resolution
│   ├── i18n.py             # Internationalization
│   ├── clipboard.py        # Clipboard operations
│   ├── card/               # Card logic (types / deck / data)
│   ├── spread/             # Spread system (5 spreads + registry)
│   ├── render/             # Rendering (renderer / export / themes / animations)
│   ├── ai/                 # AI interpretation (interpreter / prompts)
│   ├── screens/            # Textual screens (15 modules)
│   ├── storage/            # Config management
│   └── web/                # Web UI (FastAPI + vanilla JS)
├── assets/
│   ├── cards/              # 78 cards × 3 PNG variants
│   ├── cats/real/          # 6 mystic cat photos
│   └── icon/               # App icons
├── data/
│   ├── card_meanings.yaml  # 78-card meanings
│   ├── locales/            # i18n (en/zh)
│   └── prompts/            # AI prompt templates
├── scripts/                # Build and utility scripts
├── tests/                  # Tests (unit / integration)
├── pyproject.toml          # Project config
└── nekomata.spec           # PyInstaller build
```

## Development

```bash
# Install all dependencies
uv sync --extra desktop --extra dev

# Run tests
uv run pytest

# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# Coverage report
uv run pytest --cov=nekomata
```

## Mystic Cat Diviners

Nekomata's tarot readings are hosted by six mystic cats:

| Name      | Breed                   | Gender | Traits                                |
| --------- | ----------------------- | ------ | ------------------------------------- |
| Gourou    | Siamese                 | Female | Adorably goofy                        |
| Pifatzi   | Cream British Shorthair | Male   | On the chubby side                    |
| Jinlongyu | White longhair          | Male   | Fluffy coat                           |
| Meiqiu    | Dark-face Siamese       | Male   | Much darker face markings than Gourou |
| Huahua    | Calico tabby            | Female | Tri-color pattern                     |
| Wayne     | Tuxedo cat              | Male   | Black and white bicolor               |

## License

- **Code**: [MIT License](LICENSE)
- **Art assets** (all PNGs under `assets/cards/`): [CC BY-NC-SA 4.0](LICENSE-ASSETS.md)

## Acknowledgments

- [Textual](https://textual.textualize.io/) - Terminal UI framework
- [textual-image](https://github.com/sarusso/textual-image) - Terminal image rendering
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Catppuccin](https://github.com/catppuccin/catppuccin) - Color scheme
- [PyWebView](https://pywebview.flowrl.com/) - Native window
