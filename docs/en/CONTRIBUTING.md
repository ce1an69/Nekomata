# Contributing to Nekomata

[中文](../zh/CONTRIBUTING.md)

Thanks for your interest! Here's how to get started.

## Development Setup

```bash
# Clone and enter the repo
git clone https://github.com/ce1an69/Nekomata.git
cd Nekomata

# Install with dev dependencies (requires uv)
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
```

## Making Changes

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make your changes
3. Run checks:

```bash
uv run pytest                    # tests
uv run ruff check src/ tests/    # lint
uv run ruff format src/ tests/   # format
uv run pyright                   # type check
```

4. Commit with a clear message (conventional commits preferred: `feat:`, `fix:`, `docs:`, etc.)
5. Open a pull request against `main`

## Code Style

- Python 3.13+ with type annotations on all function signatures
- Formatted with **ruff** (replaces black + isort)
- Line length: 120 characters
- Imports sorted with isort (via ruff)

## Adding / Modifying UI Strings

All user-facing strings live in `data/locales/{en,zh}.json` (shared by TUI and Web).
Spread-specific strings are in `data/locales/spreads_{en,zh}.json`.

## Running Tests

```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# With coverage
uv run pytest --cov=nekomata --cov-report=term-missing
```

## Reporting Issues

Please use the [GitHub issue tracker](https://github.com/ce1an69/Nekomata/issues) and include:

- OS, Python version, terminal emulator
- Steps to reproduce
- Expected vs actual behavior
