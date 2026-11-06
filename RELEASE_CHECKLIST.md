# SNIPLY — Initial GitHub Release Preparation Checklist (v1.0.0)

Use this checklist before tagging and publishing a public release on GitHub.

## 1. Code Quality & Automated Verification
- [x] All 29 automated tests in `tests/` pass (`python -m unittest discover -s tests -v` / `pytest -v`).
- [x] 10,000-entry SQLite pagination benchmark completes in under 250 ms (`test_08_performance_with_10000_entries`).
- [x] English (`resources/translations/en.json`) and Russian (`resources/translations/ru.json`) have 100% key parity (`test_01_translation_files_key_parity_and_completeness`).
- [x] Russian CLDR pluralization (`1 элемент`, `2 элемента`, `5 элементов`, `21 элемент`) is verified (`test_02_live_language_switching_and_russian_pluralization`).
- [x] All Python modules compile cleanly with zero syntax warnings (`test_03_all_python_modules_compile_cleanly`).

## 2. Privacy & Security Audit
- [x] First-launch onboarding requires explicit user consent before clipboard monitoring starts (`test_01_consent_required_before_monitoring`).
- [x] Default password manager exclusions (`1Password.exe`, `KeePassXC.exe`, `Bitwarden.exe`, etc.) are seeded and respected (`test_04_excluded_app_blocks_capture`).
- [x] Conservative sensitive-content filter blocks private keys, OpenAI/GitHub/AWS tokens, JWTs, and password assignments (`test_sensitive_content_filtering`).
- [x] Rotating logger (`core/logger.py`) redacts token patterns and never logs clipboard payloads.
- [x] `.gitignore` blocks `*.db`, `*.log`, user images, and personal settings from ever being committed.

## 3. Windows Packaging & Installer Verification (On Windows 10 / 11 x64 Build Host)
- [ ] Run `python scripts/build_windows.py` on a 64-bit Windows 10/11 build machine with `pip install -r requirements.txt`.
- [ ] Verify `dist/SNIPLY/SNIPLY.exe` launches cleanly on a clean Windows VM without Python installed.
- [ ] Verify global hotkey `Ctrl + Shift + V` summons Quick Paste from external Windows applications (Notepad, VS Code, Chrome).
- [ ] Verify `dist/SNIPLY_v1.0.0_Windows_x64_Portable.zip` and `dist/installer/SNIPLY_Setup_v1.0.0.exe` (via Inno Setup 6) include the multi-size `sniply.ico` icon and preserve user data on uninstall unless confirmed.
