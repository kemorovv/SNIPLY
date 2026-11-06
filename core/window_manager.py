"""
Windows Foreground Window & Startup Registry Manager for SNIPLY.
Handles:
1. Capturing the previously focused window handle before Quick Paste opens.
2. Safely restoring focus and optionally sending Ctrl+V only after verifying the window still exists.
3. Managing the Windows Startup registry entry (`HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`).
"""

import ctypes
import sys
import time
from typing import Optional

from app.constants import APP_NAME
from core.logger import get_logger

logger = get_logger("window_manager")


class WindowManager:
    """Manages Windows foreground window focus restoration and startup registration."""

    def __init__(self) -> None:
        self._last_foreground_hwnd: Optional[int] = None

    def remember_foreground_window(self, own_hwnds: Optional[set[int]] = None) -> Optional[int]:
        """Record the active foreground window before summoning Quick Paste."""
        if sys.platform != "win32":
            return None
        try:
            windll = getattr(ctypes, "windll", None)
            if windll is None:
                return None
            hwnd = int(windll.user32.GetForegroundWindow())
            if hwnd and (not own_hwnds or hwnd not in own_hwnds):
                self._last_foreground_hwnd = hwnd
                return hwnd
        except Exception:
            pass
        return None

    def restore_and_optional_paste(self, auto_paste: bool = False) -> bool:
        """
        Restore focus to the previously active window and optionally send Ctrl+V
        only after verifying that the target window handle is still valid and visible.
        """
        if sys.platform != "win32" or not self._last_foreground_hwnd:
            return False

        hwnd = self._last_foreground_hwnd
        try:
            windll = getattr(ctypes, "windll", None)
            if windll is None:
                return False

            if not windll.user32.IsWindow(hwnd) or not windll.user32.IsWindowVisible(hwnd):
                return False

            windll.user32.SetForegroundWindow(hwnd)
            if not auto_paste:
                return True

            time.sleep(0.06)
            active_now = int(windll.user32.GetForegroundWindow())
            if active_now != hwnd:
                logger.warning("Target foreground window did not regain focus; skipping auto-paste")
                return False

            # Synthesize Ctrl+V keystroke safely via keybd_event
            VK_CONTROL = 0x11
            VK_V = 0x56
            KEYEVENTF_KEYUP = 0x0002
            windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
            windll.user32.keybd_event(VK_V, 0, 0, 0)
            windll.user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            return True
        except Exception as exc:
            logger.error(f"Failed to restore window or auto-paste: {exc}")
            return False

    @staticmethod
    def set_windows_startup(enabled: bool, executable_command: Optional[str] = None) -> bool:
        """Configure or remove SNIPLY in the current user's Windows Startup Run key."""
        if sys.platform != "win32":
            return False

        try:
            import winreg

            run_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            cmd = executable_command
            if not cmd:
                if getattr(sys, "frozen", False):
                    cmd = f'"{sys.executable}" --minimized'
                else:
                    cmd = f'"{sys.executable}" "{sys.argv[0]}" --minimized'

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, run_key_path, 0, winreg.KEY_SET_VALUE
            ) as key:
                if enabled:
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
            return True
        except Exception as exc:
            logger.warning(f"Could not update Windows startup registry: {exc}")
            return False
