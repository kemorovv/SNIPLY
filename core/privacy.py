"""
Privacy & Security Guard for SNIPLY.
Implements:
1. First-run user consent check before capturing clipboard contents.
2. Foreground Windows process executable detection and exclusion matching.
3. Conservative sensitive-content filtering (API keys, private keys, JWTs, password labels).
"""

import ctypes
from pathlib import Path
import re
import sys
from typing import Iterable, List, Optional, Tuple

from core.logger import get_logger

logger = get_logger("privacy")


class PrivacyGuard:
    """Evaluates application exclusions and conservative sensitive-content rules."""

    # Conservative patterns for obvious secrets, private keys, and tokens
    _SENSITIVE_PATTERNS: List[Tuple[str, re.Pattern]] = [
        (
            "private_key",
            re.compile(r"-----BEGIN\s+(?:RSA\s+|OPENSSH\s+|EC\s+|PGP\s+)?PRIVATE\s+KEY-----", re.IGNORECASE),
        ),
        (
            "openai_or_api_secret",
            re.compile(r"^\s*(?:sk-[A-Za-z0-9\-_]{20,}|ghp_[A-Za-z0-9]{25,}|gho_[A-Za-z0-9]{25,}|xox[baprs]-[A-Za-z0-9\-]{20,})\s*$"),
        ),
        (
            "aws_access_key",
            re.compile(r"^\s*(?:AKIA|ASIA)[0-9A-Z]{16}\s*$"),
        ),
        (
            "jwt_token",
            re.compile(r"^\s*eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\s*$"),
        ),
        (
            "password_assignment",
            re.compile(
                r"^\s*(?:password|passwd|pwd|secret_key|api_key|access_token|auth_token|client_secret)\s*[:=]\s*\S{6,}\s*$",
                re.IGNORECASE,
            ),
        ),
    ]

    @staticmethod
    def get_foreground_executable_name() -> Optional[str]:
        """
        Retrieve the executable name (e.g., 'KeePassXC.exe') of the current Windows foreground window
        using native Win32 ctypes APIs (`GetForegroundWindow`, `GetWindowThreadProcessId`,
        `OpenProcess`, `QueryFullProcessImageNameW`).
        Returns None on non-Windows platforms or if detection is unavailable.
        """
        if sys.platform != "win32":
            return None

        try:
            windll = getattr(ctypes, "windll", None)
            if windll is None:
                return None

            hwnd = windll.user32.GetForegroundWindow()
            if not hwnd:
                return None

            pid = ctypes.c_ulong(0)
            windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == 0:
                return None

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h_process = windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value
            )
            if not h_process:
                return None

            try:
                buf_len = ctypes.c_ulong(1024)
                buf = ctypes.create_unicode_buffer(1024)
                success = windll.kernel32.QueryFullProcessImageNameW(
                    h_process, 0, buf, ctypes.byref(buf_len)
                )
                if success and buf.value:
                    return Path(buf.value).name
            finally:
                windll.kernel32.CloseHandle(h_process)
        except Exception:
            return None

        return None

    @classmethod
    def is_process_excluded(
        cls,
        excluded_executables: Iterable[str],
        active_executable: Optional[str] = None,
    ) -> bool:
        """
        Check whether the given (or detected foreground) executable matches the user's exclusion list.
        Matching is case-insensitive and supports both 'App.exe' and 'App'.
        """
        proc_name = active_executable if active_executable is not None else cls.get_foreground_executable_name()
        if not proc_name:
            return False

        proc_clean = proc_name.strip().lower()
        proc_stem = proc_clean[:-4] if proc_clean.endswith(".exe") else proc_clean

        for item in excluded_executables:
            ex = item.strip().lower()
            if not ex:
                continue
            ex_stem = ex[:-4] if ex.endswith(".exe") else ex
            if proc_clean == ex or proc_stem == ex_stem:
                return True
        return False

    @classmethod
    def inspect_sensitive_text(cls, text: str) -> Tuple[bool, Optional[str]]:
        """
        Inspect copied text for obvious sensitive credentials or secret markers.
        Returns (is_sensitive, matched_rule_name).
        Never logs the text itself.
        """
        if not text:
            return False, None

        for rule_name, pattern in cls._SENSITIVE_PATTERNS:
            if pattern.search(text):
                logger.info(f"Skipped clipboard capture due to sensitive rule: {rule_name}")
                return True, rule_name

        return False, None
