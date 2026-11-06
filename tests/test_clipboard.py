"""
Automated Tests for Clipboard Lifecycle, First-Run Consent Enforcement,
Image Capture & Restoration, HTML Preservation, and Shortcut Validation.
"""

from pathlib import Path
import tempfile
import unittest
from PIL import Image

from app.constants import CONTENT_TYPE_COLOR, CONTENT_TYPE_IMAGE, CONTENT_TYPE_TEXT
from app.paths import AppPaths
from core.clipboard_adapter import ClipboardPayload, InMemoryClipboardAdapter
from core.clipboard_manager import ClipboardManager
from core.database import Database
from core.duplicate_detector import DuplicateDetector
from core.shortcut_manager import ShortcutManager
from core.storage import StorageRepository


class TestClipboardLifecycle(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp_dir.name)
        AppPaths.set_custom_data_dir(self.base_path)
        self.storage = StorageRepository(Database(self.base_path / "clip.db"))
        self.adapter = InMemoryClipboardAdapter()
        self.manager = ClipboardManager(storage=self.storage, adapter=self.adapter)

    def tearDown(self) -> None:
        self.manager.monitor.stop()
        AppPaths.set_custom_data_dir(None)
        self.tmp_dir.cleanup()

    def test_01_consent_required_before_monitoring(self) -> None:
        # Before consent is granted, copying must NOT record history
        self.assertFalse(self.manager.settings.monitoring_consent_given)
        self.manager.initialize_monitoring()
        self.adapter.simulate_user_copy(text="Should not be captured before consent")
        self.assertEqual(self.storage.count_clips(), 0)

        # Grant consent and enable monitoring -> copies are now captured
        self.manager.set_monitoring_enabled(True)
        self.adapter.simulate_user_copy(text="#A78BFA")
        self.assertEqual(self.storage.count_clips(), 1)
        captured = self.storage.query_clips()[0]
        self.assertEqual(captured.content_type, CONTENT_TYPE_COLOR)

    def test_02_text_and_html_restoration(self) -> None:
        self.manager.set_monitoring_enabled(True)
        raw_text = "Formatted Heading\n\tIndented body"
        raw_html = "<h1>Formatted Heading</h1><p>Indented body</p>"
        self.adapter.simulate_user_copy(text=raw_text, html=raw_html)

        clips = self.storage.query_clips()
        self.assertEqual(len(clips), 1)
        saved_clip = clips[0]
        self.assertEqual(saved_clip.text_content, raw_text)
        self.assertEqual(saved_clip.html_content, raw_html)

        # Overwrite clipboard with something else, then restore saved_clip
        self.adapter.simulate_user_copy(text="Temporary text")
        self.assertEqual(self.storage.count_clips(), 2)

        ok = self.manager.restore_clip_to_clipboard(saved_clip)
        self.assertTrue(ok)
        current_payload = self.adapter.read_payload()
        self.assertEqual(current_payload.text, raw_text)
        self.assertEqual(current_payload.html, raw_html)

        # Restoring an item must NOT create a new duplicate entry
        self.assertEqual(self.storage.count_clips(), 2)

    def test_03_image_capture_and_restoration(self) -> None:
        self.manager.set_monitoring_enabled(True)
        img = Image.new("RGBA", (320, 200), (139, 92, 246, 255))
        self.adapter.simulate_user_copy(image=img)

        clips = self.storage.query_clips(content_type=CONTENT_TYPE_IMAGE)
        self.assertEqual(len(clips), 1)
        img_clip = clips[0]
        self.assertTrue(Path(img_clip.image_path).exists())  # type: ignore[arg-type]
        self.assertTrue(Path(img_clip.thumbnail_path).exists())  # type: ignore[arg-type]
        self.assertEqual(img_clip.metadata["width"], 320)
        self.assertEqual(img_clip.metadata["height"], 200)

        # Clear clipboard to text, then restore image clip
        self.adapter.simulate_user_copy(text="Some text")
        self.manager.restore_clip_to_clipboard(img_clip)
        restored_payload = self.adapter.read_payload()
        self.assertIsNotNone(restored_payload.image)
        self.assertTrue(
            DuplicateDetector.are_images_identical(img, restored_payload.image)  # type: ignore[arg-type]
        )

    def test_04_excluded_app_blocks_capture(self) -> None:
        self.manager.set_monitoring_enabled(True)
        res = self.manager.process_payload(
            ClipboardPayload(text="KeePass Master Secret"),
            active_executable="KeePassXC.exe",
        )
        self.assertIsNone(res)
        self.assertEqual(self.storage.count_clips(), 0)

    def test_05_shortcut_validation_and_conflict_detection(self) -> None:
        parsed = ShortcutManager.parse_shortcut("Ctrl+Shift+V")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed[2], "Ctrl+Shift+V")  # type: ignore[index]

        valid, conflict = ShortcutManager.validate_shortcut_set(
            {
                "quick_paste": "Ctrl+Shift+V",
                "main_window": "Ctrl+Shift+S",
                "pause": "Ctrl+Shift+P",
            }
        )
        self.assertTrue(valid)
        self.assertIsNone(conflict)

        # Duplicate shortcut must be flagged as conflict
        valid_dup, conflict_dup = ShortcutManager.validate_shortcut_set(
            {
                "quick_paste": "Ctrl+Shift+V",
                "main_window": "ctrl + shift + v",
            }
        )
        self.assertFalse(valid_dup)
        self.assertEqual(conflict_dup, "Ctrl+Shift+V")


if __name__ == "__main__":
    unittest.main()
