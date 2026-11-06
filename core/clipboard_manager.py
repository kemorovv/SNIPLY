"""
Central Clipboard Manager for SNIPLY.
Coordinates clipboard monitoring, privacy & exclusion filtering, smart recognition,
image thumbnail processing, deduplication, persistence, and clipboard restoration.
"""

from typing import Callable, List, Optional, Tuple

from app.constants import CONTENT_TYPE_IMAGE, DEMO_ENTRIES
from core.clipboard_adapter import BaseClipboardAdapter, ClipboardPayload
from core.clipboard_monitor import ClipboardMonitor
from core.duplicate_detector import DuplicateDetector
from core.image_manager import ImageManager, ImageTooLargeError
from core.logger import get_logger
from core.privacy import PrivacyGuard
from core.recognition_engine import RecognitionEngine
from core.retention import RetentionManager
from core.storage import StorageRepository
from models.clip import Clip
from models.settings import AppSettings

logger = get_logger("clipboard_manager")


class ClipboardManager:
    """High-level coordinator connecting clipboard events, recognition, privacy, and storage."""

    def __init__(
        self,
        storage: StorageRepository,
        adapter: BaseClipboardAdapter,
        image_manager: Optional[ImageManager] = None,
        recognition_engine: Optional[RecognitionEngine] = None,
    ) -> None:
        self.storage = storage
        self.adapter = adapter
        self.image_manager = image_manager or ImageManager()
        self.recognition_engine = recognition_engine or RecognitionEngine()
        self.retention_manager = RetentionManager(self.storage)
        self.monitor = ClipboardMonitor(self.adapter)
        self.monitor.on_payload(self._handle_incoming_payload)

        self.settings: AppSettings = self.storage.load_settings()
        self.demo_mode: bool = False

        self._clip_captured_listeners: List[Callable[[Clip, bool], None]] = []
        self._notification_listeners: List[Callable[[str, str], None]] = []

    def initialize_monitoring(self) -> None:
        """Start monitoring only if user consent was granted and monitoring is enabled."""
        self.settings = self.storage.load_settings()
        if self.settings.monitoring_consent_given and self.settings.monitoring_enabled:
            self.monitor.start()
        else:
            self.monitor.pause()

    def set_monitoring_enabled(self, enabled: bool) -> None:
        self.settings.monitoring_enabled = enabled
        if enabled:
            self.settings.monitoring_consent_given = True
        self.storage.save_settings(self.settings)
        if enabled:
            self.monitor.start()
        else:
            self.monitor.pause()

    def on_clip_captured(self, callback: Callable[[Clip, bool], None]) -> None:
        if callback not in self._clip_captured_listeners:
            self._clip_captured_listeners.append(callback)

    def on_notification(self, callback: Callable[[str, str], None]) -> None:
        """Subscribe to user-facing notifications: callback(translation_key, detail)."""
        if callback not in self._notification_listeners:
            self._notification_listeners.append(callback)

    def _emit_notification(self, key: str, detail: str = "") -> None:
        for cb in list(self._notification_listeners):
            try:
                cb(key, detail)
            except Exception:
                pass

    def process_payload(
        self,
        payload: ClipboardPayload,
        active_executable: Optional[str] = None,
    ) -> Optional[Tuple[Clip, bool]]:
        """
        Process a clipboard payload through privacy checks, recognition, deduplication, and storage.
        Returns (Clip, is_duplicate) if saved, or None if skipped.
        """
        if payload.is_empty:
            return None

        # 1. Check first-run consent and monitoring state
        if not self.settings.monitoring_consent_given or not self.settings.monitoring_enabled:
            return None

        # 2. Check excluded foreground applications
        excluded_apps = self.storage.list_excluded_apps()
        if PrivacyGuard.is_process_excluded(excluded_apps, active_executable=active_executable):
            logger.info("Skipped clipboard capture from excluded foreground application")
            return None

        # 3. Handle Image Payload
        if payload.image is not None:
            if not self.settings.save_images:
                return None
            try:
                content_hash, img_path, thumb_path, meta = self.image_manager.process_and_save_image(
                    payload.image,
                    max_size_mb=self.settings.max_image_size_mb,
                )
            except ImageTooLargeError as exc:
                self._emit_notification("toast.image_too_large", str(exc.max_mb))
                return None
            except Exception as exc:
                logger.error(f"Failed to decode or store copied image: {exc}")
                return None

            w, h = meta.get("width", 0), meta.get("height", 0)
            fmt = meta.get("format", "PNG")
            clip = Clip(
                content_type=CONTENT_TYPE_IMAGE,
                text_content=None,
                content_hash=content_hash,
                image_path=str(img_path),
                thumbnail_path=str(thumb_path),
                preview=f"{fmt} Image ({w} × {h} px)",
                metadata=meta,
            )
            saved, is_dup = self.storage.add_or_update_clip(
                clip, deduplicate=self.settings.deduplicate_enabled
            )
            self._notify_captured(saved, is_dup)
            return saved, is_dup

        # 4. Handle Text / Rich HTML Payload
        raw_text = payload.text
        if raw_text is None or len(raw_text) == 0 or len(raw_text.strip()) == 0:
            return None

        # 5. Sensitive content filtering
        if self.settings.filter_sensitive_content:
            is_sensitive, _ = PrivacyGuard.inspect_sensitive_text(raw_text)
            if is_sensitive:
                self._emit_notification("toast.sensitive_skipped", "")
                return None

        # 6. Smart content recognition (preserving exact original text)
        recognition = self.recognition_engine.analyze(raw_text)
        content_hash = DuplicateDetector.compute_text_hash(raw_text)

        clip = Clip(
            content_type=recognition.content_type,
            text_content=raw_text,
            html_content=payload.html,
            content_hash=content_hash,
            preview=recognition.preview,
            metadata=recognition.metadata,
        )
        saved, is_dup = self.storage.add_or_update_clip(
            clip, deduplicate=self.settings.deduplicate_enabled
        )
        self._notify_captured(saved, is_dup)
        return saved, is_dup

    def _handle_incoming_payload(self, payload: ClipboardPayload) -> None:
        self.process_payload(payload)

    def _notify_captured(self, clip: Clip, is_dup: bool) -> None:
        # Enforce retention limits asynchronously / lightweight check
        try:
            self.retention_manager.run_cleanup(
                retention_days=self.settings.retention_days,
                max_history_size=self.settings.max_history_size,
            )
        except Exception as exc:
            logger.error(f"Retention check failed: {exc}")

        for cb in list(self._clip_captured_listeners):
            try:
                cb(clip, is_dup)
            except Exception as exc:
                logger.error(f"Listener error on clip captured: {exc}")

    def restore_clip_to_clipboard(self, clip: Clip) -> bool:
        """
        Restore a Clip's original text, HTML, or image to the system clipboard
        and update its last_used_at timestamp.
        """
        self.monitor.suppress_next_event()
        if clip.content_type == CONTENT_TYPE_IMAGE and clip.image_path:
            ok = self.adapter.write_payload(image_path=clip.image_path)
        else:
            ok = self.adapter.write_payload(
                text=clip.text_content or "",
                html=clip.html_content,
            )

        if ok and clip.id is not None and not clip.is_demo:
            self.storage.mark_clip_used(clip.id)
        return ok

    def copy_custom_text(self, text: str) -> bool:
        """Copy a formatted conversion (e.g., RGB, HSL, Pretty JSON, or Snippet) to the clipboard."""
        self.monitor.suppress_next_event()
        return self.adapter.write_payload(text=text)

    @staticmethod
    def get_demo_clips() -> List[Clip]:
        """Return isolated demonstration clips clearly marked with `is_demo=True`."""
        demo_list: List[Clip] = []
        for idx, item in enumerate(DEMO_ENTRIES, start=1):
            demo_list.append(
                Clip(
                    id=-idx,
                    content_type=item["content_type"],
                    text_content=item["text_content"],
                    preview=item["preview"],
                    metadata=dict(item["metadata"]),
                    usage_count=idx * 2,
                    is_pinned=(idx == 1),
                    is_favorite=(idx in (1, 3)),
                    is_demo=True,
                )
            )
        return demo_list
