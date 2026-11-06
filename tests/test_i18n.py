"""
Automated Tests for Multi-Language Localization (English & Russian) and Codebase Verification:
- Complete parity between en.json and ru.json keys
- Immediate language switching and listener notifications
- Russian pluralization (1 элемент, 2 элемента, 5 элементов, 21 элемент)
- Relative timestamp formatting in English and Russian
- AST compilation & syntax verification of all Python modules
"""

import ast
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest

from app.paths import AppPaths
from core.i18n import LocalizationManager, tr, tr_plural


class TestLocalizationAndSyntax(unittest.TestCase):
    def test_01_translation_files_key_parity_and_completeness(self) -> None:
        trans_dir = AppPaths.get_translations_dir()
        en_file = trans_dir / "en.json"
        ru_file = trans_dir / "ru.json"
        self.assertTrue(en_file.exists())
        self.assertTrue(ru_file.exists())

        en_data = json.loads(en_file.read_text(encoding="utf-8"))
        ru_data = json.loads(ru_file.read_text(encoding="utf-8"))

        self.assertEqual(set(en_data.keys()), set(ru_data.keys()))
        self.assertGreaterEqual(len(en_data), 150)

        for key, val in ru_data.items():
            self.assertTrue(isinstance(val, str) and len(val.strip()) > 0, f"Empty RU key: {key}")

    def test_02_live_language_switching_and_russian_pluralization(self) -> None:
        mgr = LocalizationManager.instance()
        notified_langs = []
        mgr.subscribe(lambda l: notified_langs.append(l))

        mgr.set_language("en")
        self.assertEqual(tr("navigation.all_clips"), "All Clips")
        self.assertEqual(tr_plural("items.count", 1), "1 item")
        self.assertEqual(tr_plural("items.count", 5), "5 items")

        mgr.set_language("ru")
        self.assertIn("ru", notified_langs)
        self.assertEqual(tr("navigation.all_clips"), "Вся история")
        self.assertEqual(tr("navigation.pinned"), "Закреплённое")
        self.assertEqual(tr("navigation.favorites"), "Избранное")
        self.assertEqual(tr("navigation.collections"), "Коллекции")
        self.assertEqual(tr("navigation.snippets"), "Шаблоны")
        self.assertEqual(tr("quick_paste.title"), "Быстрая вставка")

        # Verify Russian CLDR plural forms
        self.assertEqual(tr_plural("items.count", 1), "1 элемент")
        self.assertEqual(tr_plural("items.count", 2), "2 элемента")
        self.assertEqual(tr_plural("items.count", 4), "4 элемента")
        self.assertEqual(tr_plural("items.count", 5), "5 элементов")
        self.assertEqual(tr_plural("items.count", 11), "11 элементов")
        self.assertEqual(tr_plural("items.count", 21), "21 элемент")
        self.assertEqual(tr_plural("items.count", 22), "22 элемента")
        self.assertEqual(tr_plural("items.count", 25), "25 элементов")

        # Relative timestamps in both languages
        now = datetime.now(timezone.utc)
        five_min_ago = (now - timedelta(minutes=5)).isoformat()
        self.assertEqual(mgr.format_relative_time(five_min_ago, now=now), "Скопировано 5 минут назад")

        mgr.set_language("en")
        self.assertEqual(mgr.format_relative_time(five_min_ago, now=now), "Copied 5 minutes ago")

    def test_03_all_python_modules_compile_cleanly(self) -> None:
        root = AppPaths.get_bundle_root()
        py_files = list(root.rglob("*.py"))
        self.assertGreaterEqual(len(py_files), 28)
        for py_file in py_files:
            source = py_file.read_text(encoding="utf-8")
            try:
                ast.parse(source, filename=str(py_file))
            except SyntaxError as err:
                self.fail(f"SyntaxError in {py_file}: {err}")


if __name__ == "__main__":
    unittest.main()
