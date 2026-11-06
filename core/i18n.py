"""
Centralized Localization & Pluralization Engine for SNIPLY.
Supports English (en) and Russian (ru) with immediate live switching,
Russian CLDR plural rules (one/few/many), locale-aware timestamps, and Windows locale detection.
"""

import ctypes
from datetime import datetime, timezone
import json
import locale
import sys
from typing import Any, Callable, Dict, List, Optional

from app.constants import SUPPORTED_LANGUAGES
from app.paths import AppPaths
from core.logger import get_logger

logger = get_logger("i18n")


class LocalizationManager:
    """Manages translations, pluralization, locale detection, and live UI language switching."""

    _instance: Optional["LocalizationManager"] = None

    def __init__(self, default_lang: str = "en") -> None:
        self._current_lang: str = default_lang if default_lang in SUPPORTED_LANGUAGES else "en"
        self._translations: Dict[str, Dict[str, str]] = {"en": {}, "ru": {}}
        self._listeners: List[Callable[[str], None]] = []
        self._load_translations()

    @classmethod
    def instance(cls) -> "LocalizationManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_translations(self) -> None:
        trans_dir = AppPaths.get_translations_dir()
        for lang in SUPPORTED_LANGUAGES:
            file_path = trans_dir / f"{lang}.json"
            if file_path.exists():
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        self._translations[lang] = data
                except Exception as exc:
                    logger.error(f"Failed to load translation file {file_path}: {exc}")

    @property
    def language(self) -> str:
        return self._current_lang

    def set_language(self, lang: str) -> bool:
        """Switch active language and notify all subscribed UI components immediately."""
        if lang not in SUPPORTED_LANGUAGES:
            return False
        if lang == self._current_lang:
            return True
        self._current_lang = lang
        for callback in list(self._listeners):
            try:
                callback(lang)
            except Exception as exc:
                logger.error(f"Error notifying language listener: {exc}")
        return True

    def subscribe(self, callback: Callable[[str], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[str], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def translate(self, key: str, **kwargs: Any) -> str:
        """Look up translation key in current language with safe fallback to English."""
        lang_dict = self._translations.get(self._current_lang, {})
        text = lang_dict.get(key)
        if text is None:
            text = self._translations.get("en", {}).get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                return text
        return text

    @staticmethod
    def get_russian_plural_form(count: int) -> str:
        """
        Return CLDR plural category ('one', 'few', 'many') for Russian integers.
        Examples:
          1, 21, 31 -> 'one' (1 элемент)
          2, 3, 4, 22 -> 'few' (2 элемента)
          0, 5..20, 25 -> 'many' (5 элементов)
        """
        n = abs(int(count))
        mod10 = n % 10
        mod100 = n % 100
        if mod10 == 1 and mod100 != 11:
            return "one"
        if 2 <= mod10 <= 4 and not (12 <= mod100 <= 14):
            return "few"
        return "many"

    @staticmethod
    def get_english_plural_form(count: int) -> str:
        return "one" if abs(int(count)) == 1 else "many"

    def plural(self, base_key: str, count: int, **kwargs: Any) -> str:
        """Format a pluralized translation string using language-specific plural rules."""
        if self._current_lang == "ru":
            form = self.get_russian_plural_form(count)
        else:
            form = self.get_english_plural_form(count)

        full_key = f"{base_key}.{form}"
        return self.translate(full_key, count=count, **kwargs)

    def format_relative_time(self, timestamp_iso: Optional[str], now: Optional[datetime] = None) -> str:
        """Format an ISO-8601 timestamp into a localized relative string ('Copied 5 minutes ago')."""
        if not timestamp_iso:
            return self.translate("time.just_now")
        try:
            dt = datetime.fromisoformat(timestamp_iso)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            ref = now or datetime.now(timezone.utc)
            if ref.tzinfo is None:
                ref = ref.replace(tzinfo=timezone.utc)
            delta_sec = max(0, int((ref - dt).total_seconds()))
        except Exception:
            return self.translate("time.just_now")

        if delta_sec < 10:
            return self.translate("time.just_now")
        if delta_sec < 60:
            return self.plural("time.seconds_ago", delta_sec)
        minutes = delta_sec // 60
        if minutes < 60:
            return self.plural("time.minutes_ago", minutes)
        hours = minutes // 60
        if hours < 24:
            return self.plural("time.hours_ago", hours)
        days = hours // 24
        return self.plural("time.days_ago", days)

    def format_file_size(self, size_bytes: int) -> str:
        """Format byte size into locale-aware KB / MB / GB."""
        units_en = ["B", "KB", "MB", "GB"]
        units_ru = ["Б", "КБ", "МБ", "ГБ"]
        units = units_ru if self._current_lang == "ru" else units_en

        value = float(max(0, size_bytes))
        idx = 0
        while value >= 1024.0 and idx < len(units) - 1:
            value /= 1024.0
            idx += 1

        if idx == 0:
            formatted = f"{int(value)}"
        else:
            formatted = f"{value:.1f}"
            if self._current_lang == "ru":
                formatted = formatted.replace(".", ",")
        return f"{formatted} {units[idx]}"

    @staticmethod
    def detect_system_language() -> str:
        """
        Detect whether the host Windows/OS environment is configured for Russian.
        Returns 'ru' if Russian is detected, otherwise 'en'.
        """
        if sys.platform == "win32":
            try:
                windll = getattr(ctypes, "windll", None)
                if windll is not None:
                    lang_id = windll.kernel32.GetUserDefaultUILanguage()
                    # Primary language ID 0x19 is Russian (0x0419 = ru-RU)
                    if (lang_id & 0x3FF) == 0x19:
                        return "ru"
            except Exception:
                pass

        try:
            loc = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
            if loc.lower().startswith("ru"):
                return "ru"
        except Exception:
            pass

        return "en"


def tr(key: str, **kwargs: Any) -> str:
    """Global convenience helper for translating a string."""
    return LocalizationManager.instance().translate(key, **kwargs)


def tr_plural(base_key: str, count: int, **kwargs: Any) -> str:
    """Global convenience helper for pluralized translations."""
    return LocalizationManager.instance().plural(base_key, count, **kwargs)
