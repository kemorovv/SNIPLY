# Changelog

All notable changes to **SNIPLY** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-11-07 (First Public Release)

### Added
- **Smart Clipboard Engine**: Event-driven OS clipboard listener (`QClipboard.dataChanged`) with extensible `BaseClipboardAdapter` architecture supporting plain text, rich HTML, and high-resolution images without high-frequency polling.
- **Modular Smart Recognition Engine**:
  - **Color Recognizer**: Detects `#RGB`, `#RGBA`, `#RRGGBB`, `#RRGGBBAA`, `rgb(...)`, and `rgba(...)` strings and computes instant conversions between HEX, RGB, HSL, and Alpha.
  - **JSON Recognizer**: Validates JSON objects and arrays, builds collapsible tree structures, formats pretty/minified payloads, and handles malformed JSON gracefully.
  - **Code Recognizer**: Detects Python, JavaScript, TypeScript, HTML, CSS, SQL, Bash, PowerShell, Java, and C++ with inline Pygments syntax highlighting.
  - **URL & Email Recognizers**: Extracts domain/scheme metadata and provides offline browser launch and quick copy actions without making external network requests.
  - **Plain Text Recognizer**: Calculates character, word, and line counts along with estimated reading times.
- **Quick Paste Floating Launcher (`Ctrl + Shift + V`)**:
  - Compact 600 × 480 floating window centered near the cursor with instant debounced search, keyboard navigation (`Up`/`Down`/`Enter`/`Esc`/`Ctrl+F`), and configurable optional auto-paste into the previously focused Windows application.
- **Complete Multi-Language Localization (English & Russian)**:
  - Centralized `LocalizationManager` (`core/i18n.py`) with 280+ keys across `en.json` and `ru.json`, immediate live UI language switching without restart, Russian CLDR pluralization rules (`1 элемент`, `2 элемента`, `5 элементов`), locale-aware relative timestamps, and automatic Windows Russian language detection on first launch.
- **Collections, Pinned Items, Favorites & Snippets Library**:
  - Custom user collections with color badges, safe collection deletion dialog, pin protection against retention cleanup, and a dedicated reusable Snippets library.
- **Colors Workspace, Image Grid & Clipboard Insights**:
  - Dedicated visual palette workspace with JSON/CSS palette export, cached thumbnail image grid, and real-time local SQLite analytics with a 7-day activity chart.
- **Privacy & Security Controls**:
  - 6-step first-launch onboarding wizard with explicit monitoring consent, foreground Windows executable exclusion (`KeePassXC.exe`, `1Password.exe`, `Bitwarden.exe`, etc.), conservative sensitive-token filtering, and configurable retention cleanup (1, 7, 30, 90 days, or Never).
- **Packaging & Automated Testing**:
  - 29 automated tests covering database migrations, 10,000-clip query performance, deduplication, recognition, privacy, retention, and localization, plus PyInstaller (`installer/sniply.spec`) and Inno Setup (`installer/sniply_setup.iss`) configurations.
