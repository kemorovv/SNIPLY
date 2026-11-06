"""
Event-driven Clipboard Monitor for SNIPLY.
Listens to native OS clipboard notifications without high-frequency polling,
and suppresses self-restored clipboard writes so restoring an item doesn't re-trigger capture loops.
"""

from typing import Callable, List, Optional

from core.clipboard_adapter import BaseClipboardAdapter, ClipboardPayload
from core.logger import get_logger

logger = get_logger("clipboard_monitor")


class ClipboardMonitor:
    """Monitors clipboard changes via OS event notifications and dispatches payloads."""

    def __init__(self, adapter: BaseClipboardAdapter) -> None:
        self.adapter = adapter
        self._running: bool = False
        self._suppress_next_change: bool = False
        self._callbacks: List[Callable[[ClipboardPayload], None]] = []
        self.adapter.connect_change_listener(self._on_clipboard_changed)

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        self._running = True
        logger.info("Clipboard monitoring started")

    def pause(self) -> None:
        self._running = False
        logger.info("Clipboard monitoring paused")

    def stop(self) -> None:
        self._running = False
        self.adapter.disconnect_change_listener(self._on_clipboard_changed)
        logger.info("Clipboard monitoring stopped")

    def suppress_next_event(self) -> None:
        """Mark the next clipboard notification as originating from SNIPLY restoration."""
        self._suppress_next_change = True

    def on_payload(self, callback: Callable[[ClipboardPayload], None]) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def _on_clipboard_changed(self) -> None:
        if not self._running:
            return
        if self._suppress_next_change:
            self._suppress_next_change = False
            return

        payload = self.adapter.read_payload()
        if payload.is_empty:
            return

        for cb in list(self._callbacks):
            try:
                cb(payload)
            except Exception as exc:
                logger.error(f"Error processing clipboard payload: {exc}")
