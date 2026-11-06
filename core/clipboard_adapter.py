"""
Extensible Clipboard Adapter Architecture for SNIPLY.
Supports Qt QClipboard on Windows 10/11 (capturing & restoring plain text, rich HTML, and images)
as well as an InMemoryClipboardAdapter for deterministic automated testing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import io
from pathlib import Path
from typing import Callable, List, Optional
from PIL import Image

from core.logger import get_logger

logger = get_logger("clipboard_adapter")


@dataclass
class ClipboardPayload:
    """Represents raw content extracted from or written to the system clipboard."""

    text: Optional[str] = None
    html: Optional[str] = None
    image: Optional[Image.Image] = None

    @property
    def is_empty(self) -> bool:
        has_text = self.text is not None and len(self.text) > 0
        has_img = self.image is not None
        return not (has_text or has_img)


class BaseClipboardAdapter(ABC):
    """Abstract adapter for reading, restoring, and subscribing to OS clipboard events."""

    @abstractmethod
    def read_payload(self) -> ClipboardPayload:
        """Read current content from the clipboard."""

    @abstractmethod
    def write_payload(
        self,
        text: Optional[str] = None,
        html: Optional[str] = None,
        image_path: Optional[str] = None,
        image: Optional[Image.Image] = None,
    ) -> bool:
        """Restore content (text, optional HTML, or image) to the clipboard."""

    @abstractmethod
    def connect_change_listener(self, callback: Callable[[], None]) -> None:
        """Register callback invoked when the OS clipboard changes."""

    @abstractmethod
    def disconnect_change_listener(self, callback: Callable[[], None]) -> None:
        """Unregister clipboard change callback."""


class QtClipboardAdapter(BaseClipboardAdapter):
    """Production Windows/Qt clipboard adapter backed by PySide6 QGuiApplication.clipboard()."""

    def __init__(self) -> None:
        from PySide6.QtGui import QGuiApplication

        self._clipboard = QGuiApplication.clipboard()

    def read_payload(self) -> ClipboardPayload:
        from PySide6.QtCore import QBuffer, QIODevice

        try:
            mime = self._clipboard.mimeData()
            if mime is None:
                return ClipboardPayload()

            if mime.hasImage():
                qimage = self._clipboard.image()
                if not qimage.isNull():
                    buffer = QBuffer()
                    buffer.open(QIODevice.OpenModeFlag.ReadWrite)
                    qimage.save(buffer, "PNG")
                    pil_img = Image.open(io.BytesIO(bytes(buffer.data()))).convert("RGBA")
                    buffer.close()
                    return ClipboardPayload(image=pil_img)

            text_val: Optional[str] = None
            html_val: Optional[str] = None

            if mime.hasText():
                raw_text = mime.text()
                if raw_text and len(raw_text) > 0:
                    text_val = raw_text

            if mime.hasHtml():
                raw_html = mime.html()
                if raw_html and len(raw_html.strip()) > 0:
                    html_val = raw_html

            return ClipboardPayload(text=text_val, html=html_val)
        except Exception as exc:
            logger.error(f"Clipboard read failed gracefully: {exc}")
            return ClipboardPayload()

    def write_payload(
        self,
        text: Optional[str] = None,
        html: Optional[str] = None,
        image_path: Optional[str] = None,
        image: Optional[Image.Image] = None,
    ) -> bool:
        from PySide6.QtCore import QMimeData
        from PySide6.QtGui import QImage

        try:
            if image is not None or image_path is not None:
                target_path = Path(image_path) if image_path else None
                if target_path and target_path.exists():
                    qimg = QImage(str(target_path))
                elif image is not None:
                    buf = io.BytesIO()
                    image.convert("RGBA").save(buf, format="PNG")
                    qimg = QImage.fromData(buf.getvalue(), "PNG")
                else:
                    return False

                if not qimg.isNull():
                    self._clipboard.setImage(qimg)
                    return True
                return False

            if text is not None:
                mime = QMimeData()
                mime.setText(text)
                if html:
                    mime.setHtml(html)
                self._clipboard.setMimeData(mime)
                return True
            return False
        except Exception as exc:
            logger.error(f"Clipboard write failed gracefully: {exc}")
            return False

    def connect_change_listener(self, callback: Callable[[], None]) -> None:
        self._clipboard.dataChanged.connect(callback)

    def disconnect_change_listener(self, callback: Callable[[], None]) -> None:
        try:
            self._clipboard.dataChanged.disconnect(callback)
        except Exception:
            pass


class InMemoryClipboardAdapter(BaseClipboardAdapter):
    """Deterministic in-memory clipboard adapter for automated testing and headless verification."""

    def __init__(self) -> None:
        self._current = ClipboardPayload()
        self._listeners: List[Callable[[], None]] = []

    def read_payload(self) -> ClipboardPayload:
        return self._current

    def write_payload(
        self,
        text: Optional[str] = None,
        html: Optional[str] = None,
        image_path: Optional[str] = None,
        image: Optional[Image.Image] = None,
    ) -> bool:
        loaded_img = image
        if loaded_img is None and image_path:
            p = Path(image_path)
            if p.exists():
                loaded_img = Image.open(p).convert("RGBA")
        self._current = ClipboardPayload(text=text, html=html, image=loaded_img)
        for cb in list(self._listeners):
            cb()
        return True

    def simulate_user_copy(
        self,
        text: Optional[str] = None,
        html: Optional[str] = None,
        image: Optional[Image.Image] = None,
    ) -> None:
        self._current = ClipboardPayload(text=text, html=html, image=image)
        for cb in list(self._listeners):
            cb()

    def connect_change_listener(self, callback: Callable[[], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def disconnect_change_listener(self, callback: Callable[[], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)
