"""
Privacy-safe rotating file logger for SNIPLY.
Ensures clipboard contents or sensitive tokens are never written to log files.
"""

import logging
from logging.handlers import RotatingFileHandler
import re
from typing import Optional

from app.paths import AppPaths


class PrivacyLogFilter(logging.Filter):
    """Redacts any accidental long token or bearer/key pattern from log records."""

    _REDACT_PATTERNS = [
        re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
        re.compile(r"(sk-[A-Za-z0-9]{16,})"),
        re.compile(r"(ghp_[A-Za-z0-9]{20,})"),
        re.compile(r"(AIza[0-9A-Za-z\-_]{25,})"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for pattern in self._REDACT_PATTERNS:
            msg = pattern.sub("[REDACTED]", msg)
        record.msg = msg
        record.args = ()
        return True


_logger_initialized = False


def get_logger(name: str = "sniply") -> logging.Logger:
    """Configure and return a rotating, privacy-filtered logger."""
    global _logger_initialized
    root_logger = logging.getLogger("sniply")

    if not _logger_initialized:
        root_logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        privacy_filter = PrivacyLogFilter()

        try:
            log_file = AppPaths.get_logs_dir() / "sniply.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=2 * 1024 * 1024,  # 2 MB per file
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            file_handler.addFilter(privacy_filter)
            root_logger.addHandler(file_handler)
        except OSError:
            pass

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(privacy_filter)
        root_logger.addHandler(stream_handler)

        _logger_initialized = True

    if name == "sniply":
        return root_logger
    return logging.getLogger(f"sniply.{name}")
