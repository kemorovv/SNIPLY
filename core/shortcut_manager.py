"""
Global Shortcut Manager for SNIPLY.
Supports native Windows `RegisterHotKey` via Win32 API / Qt native event filter,
shortcut validation, and conflict detection.
"""

import ctypes
import sys
from typing import Callable, Dict, List, Optional, Set, Tuple

from core.logger import get_logger

logger = get_logger("shortcut_manager")

# Win32 Modifier Constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

# Common Virtual-Key codes for Windows RegisterHotKey
VK_MAP: Dict[str, int] = {
    **{chr(c): c for c in range(ord("A"), ord("Z") + 1)},
    **{chr(c): c for c in range(ord("0"), ord("9") + 1)},
    "SPACE": 0x20,
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "TAB": 0x09,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "BACKSPACE": 0x08,
    "DELETE": 0x2E,
    "INSERT": 0x2D,
    "HOME": 0x24,
    "END": 0x23,
    "PGUP": 0x21,
    "PGDN": 0x22,
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
    **{f"F{i}": 0x6F + i for i in range(1, 13)},
}


class ShortcutManager:
    """Validates, detects conflicts, and registers global Windows hotkeys."""

    def __init__(self) -> None:
        self._registered: Dict[str, Tuple[int, str, Callable[[], None]]] = {}
        self._next_id = 1001

    @staticmethod
    def parse_shortcut(shortcut_str: str) -> Optional[Tuple[int, int, str]]:
        """
        Parse a shortcut string like 'Ctrl+Shift+V' into (win32_modifiers, vk_code, normalized_str).
        Returns None if the shortcut string is invalid.
        """
        if not shortcut_str or not shortcut_str.strip():
            return None

        parts = [p.strip() for p in shortcut_str.split("+") if p.strip()]
        if len(parts) < 2:
            return None

        modifiers = 0
        mod_names: List[str] = []
        key_token: Optional[str] = None

        for part in parts:
            upper = part.upper()
            if upper in ("CTRL", "CONTROL"):
                modifiers |= MOD_CONTROL
                if "Ctrl" not in mod_names:
                    mod_names.append("Ctrl")
            elif upper == "SHIFT":
                modifiers |= MOD_SHIFT
                if "Shift" not in mod_names:
                    mod_names.append("Shift")
            elif upper == "ALT":
                modifiers |= MOD_ALT
                if "Alt" not in mod_names:
                    mod_names.append("Alt")
            elif upper in ("WIN", "META", "SUPER"):
                modifiers |= MOD_WIN
                if "Win" not in mod_names:
                    mod_names.append("Win")
            else:
                if key_token is not None:
                    return None  # Multiple non-modifier keys
                if upper not in VK_MAP:
                    return None
                key_token = upper

        if modifiers == 0 or key_token is None:
            return None

        normalized = "+".join(mod_names + [key_token.capitalize() if len(key_token) > 1 else key_token])
        return modifiers | MOD_NOREPEAT, VK_MAP[key_token], normalized

    @classmethod
    def validate_shortcut_set(cls, shortcuts: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        """
        Validate a dictionary of {action_name: shortcut_str} for syntax validity and duplicate conflicts.
        Returns (is_valid, conflicting_or_invalid_shortcut).
        """
        seen: Set[str] = set()
        for _, raw in shortcuts.items():
            parsed = cls.parse_shortcut(raw)
            if parsed is None:
                return False, raw
            norm = parsed[2].upper()
            if norm in seen:
                return False, parsed[2]
            seen.add(norm)
        return True, None

    def register_shortcut(
        self,
        action_name: str,
        shortcut_str: str,
        callback: Callable[[], None],
        hwnd: Optional[int] = None,
    ) -> bool:
        """Register a global shortcut on Windows (with safe fallback on non-Windows platforms)."""
        parsed = self.parse_shortcut(shortcut_str)
        if parsed is None:
            logger.warning(f"Invalid shortcut syntax for {action_name}: {shortcut_str}")
            return False

        mods, vk, normalized = parsed
        self.unregister_shortcut(action_name, hwnd=hwnd)

        hotkey_id = self._next_id
        self._next_id += 1

        if sys.platform == "win32":
            try:
                windll = getattr(ctypes, "windll", None)
                if windll is not None:
                    ok = windll.user32.RegisterHotKey(hwnd or 0, hotkey_id, mods, vk)
                    if not ok:
                        logger.warning(f"Win32 RegisterHotKey failed for {normalized}")
                        return False
            except Exception as exc:
                logger.warning(f"RegisterHotKey exception for {normalized}: {exc}")
                return False

        self._registered[action_name] = (hotkey_id, normalized, callback)
        return True

    def unregister_shortcut(self, action_name: str, hwnd: Optional[int] = None) -> None:
        entry = self._registered.pop(action_name, None)
        if entry is None:
            return
        hotkey_id, _, _ = entry
        if sys.platform == "win32":
            try:
                windll = getattr(ctypes, "windll", None)
                if windll is not None:
                    windll.user32.UnregisterHotKey(hwnd or 0, hotkey_id)
            except Exception:
                pass

    def unregister_all(self, hwnd: Optional[int] = None) -> None:
        for action in list(self._registered.keys()):
            self.unregister_shortcut(action, hwnd=hwnd)

    def handle_hotkey_id(self, hotkey_id: int) -> bool:
        """Trigger the callback matching a received WM_HOTKEY identifier."""
        for _, (reg_id, _, cb) in list(self._registered.items()):
            if reg_id == hotkey_id:
                try:
                    cb()
                except Exception as exc:
                    logger.error(f"Error executing global shortcut callback: {exc}")
                return True
        return False
