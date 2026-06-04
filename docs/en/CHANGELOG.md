# Changelog

[中文](../zh/CHANGELOG.md)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Bundle WOFF2 fonts instead of TTF — reduces package size by ~40 MB
- Update author email in package metadata

### Fixed

- Disable Kitty keyboard protocol on macOS to fix CJK IME input
- Fix fullscreen dialog bottom alignment and exit animation ordering
- Add missing `SLOT_FLIP_*` imports in draw widgets
- Prevent `AssertionError` on DrawScreen mouse click

## [0.1.3] - 2026-05-31

### Fixed

- Correct desktop build artifact file paths for release upload

## [0.1.2] - 2026-05-31

### Fixed

- Fix desktop build release workflow

## [0.1.1] - 2026-05-31

### Added

- CLI mode with streaming AI interpretation (`nekomata-tarot --cli`)
- Desktop mode with native window (PyWebView)
- Web UI — FastAPI server + vanilla JS SPA (used by Desktop mode)
- Follow-up question system with thinking mode toggle
- Spread toggle, text copy, and image export for interpretations
- macOS DMG and Windows EXE desktop builds (PyInstaller)
- Full i18n support with lazy locale resolution (English / Chinese)
- Card browser with suit filtering and arrow key navigation
- Setup wizard with arrow key navigation for first-run configuration

### Changed

- Rename PyPI package from `nekomata` to `nekomata-tarot`
- Replace `Q` with `Esc` for all back/close keybindings
- Streamline commands and keybindings across screens

### Fixed

- Resolve freeze after picking all cards in draw screen
- Smooth card browser detail transitions and stabilize preview
- Reload spreads after language change in web config
- Pre-fill existing config when re-entering setup
- Remove duplicate interpretation title from stream content
- Web UI fixes: i18n, port fallback, config redirect on errors
- Desktop build compatibility for Windows (edgechromium backend)

## [0.1.0] - 2026-05-29

### Added

- 78 pixel-art cat tarot cards with upright/reversed meanings
- 5 spread layouts (Single, Past-Present-Future, Body-Mind-Spirit, Five-Card Cross, Situation-Action-Result)
- AI-powered interpretation via OpenAI-compatible API (SSE streaming)
- TUI mode with Catppuccin Mocha theme
- Card browser with suit filtering
- Image export (Catppuccin-themed PNG)
- Cross-platform clipboard support
- Bilingual support (English / Chinese)

[Unreleased]: https://github.com/ce1an69/Nekomata/compare/v0.1.3...HEAD
[0.1.3]: https://github.com/ce1an69/Nekomata/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/ce1an69/Nekomata/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ce1an69/Nekomata/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ce1an69/Nekomata/releases/tag/v0.1.0
