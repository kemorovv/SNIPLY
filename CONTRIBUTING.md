# Contributing to SNIPLY

Thank you for your interest in contributing to **SNIPLY**! We welcome bug reports, recognizer improvements, localization refinements, and UI enhancements that align with our core principles: **local-first privacy, zero cloud dependencies, high responsiveness, and premium visual quality**.

## Development Setup

1. **Prerequisites**:
   - Windows 10 or Windows 11 (64-bit) for native Win32 hotkey and process integration (or Linux/macOS for core & UI development).
   - Python 3.11 or newer.

2. **Clone and create a virtual environment**:
   ```bash
   git clone https://github.com/kemorovv/SNIPLY.git
   cd sniply
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Generate icon and translation assets**:
   ```bash
   python scripts/generate_assets.py
   python scripts/generate_translations.py
   ```

5. **Run the automated test suite**:
   ```bash
   pytest -v
   # or using standard library unittest:
   python -m unittest discover -s tests -v
   ```

## Architectural Guidelines

- **Strict Layer Separation**: Keep UI views (`ui/`) decoupled from SQLite queries (`core/storage.py`) and content recognizers (`recognizers/`).
- **Adding a New Content Recognizer**:
  - Subclass `BaseRecognizer` in `recognizers/`.
  - Return a `RecognitionResult` with structured `metadata` when matched, or `None` otherwise.
  - Register the recognizer in `core/recognition_engine.py` and add unit tests in `tests/test_recognition.py`.
- **Localization Requirement (English & Russian)**:
  - Never hardcode user-facing strings inside UI widgets.
  - Add every new key to `scripts/generate_translations.py`, regenerate `resources/translations/en.json` and `ru.json`, and run `tests/test_i18n.py` to verify 100% key parity and Russian plural forms.
- **Privacy & Security**:
  - Never introduce network calls, telemetry, or analytics SDKs.
  - Always use parameterized SQL queries (`?` placeholders) in `core/database.py` and `core/storage.py`.
  - Never log clipboard contents.
