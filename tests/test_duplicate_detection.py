"""
Automated Tests for Duplicate Detection (Text & Images) and Pinned/Favorite Preservation.
"""

from pathlib import Path
import tempfile
import unittest
from PIL import Image, ImageDraw

from app.constants import CONTENT_TYPE_TEXT
from app.paths import AppPaths
from core.database import Database
from core.duplicate_detector import DuplicateDetector
from core.storage import StorageRepository
from models.clip import Clip


class TestDuplicateDetection(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp_dir.name)
        AppPaths.set_custom_data_dir(self.base_path)
        self.storage = StorageRepository(Database(self.base_path / "dup.db"))

    def tearDown(self) -> None:
        AppPaths.set_custom_data_dir(None)
        self.tmp_dir.cleanup()

    def test_text_hash_and_deduplication_preserves_pin_and_favorite(self) -> None:
        text = "Exact text with   whitespace\nand emoji ✨"
        h1 = DuplicateDetector.compute_text_hash(text)
        h2 = DuplicateDetector.compute_text_hash(text)
        self.assertEqual(h1, h2)

        first, is_dup1 = self.storage.add_or_update_clip(
            Clip(
                content_type=CONTENT_TYPE_TEXT,
                text_content=text,
                content_hash=h1,
                preview="Exact text",
                is_pinned=True,
                is_favorite=True,
            ),
            deduplicate=True,
        )
        self.assertFalse(is_dup1)
        self.assertEqual(first.usage_count, 1)

        # Copy same text again -> should update existing record, increment usage_count, and preserve pin/favorite
        second, is_dup2 = self.storage.add_or_update_clip(
            Clip(
                content_type=CONTENT_TYPE_TEXT,
                text_content=text,
                content_hash=h2,
                preview="Exact text",
            ),
            deduplicate=True,
        )
        self.assertTrue(is_dup2)
        self.assertEqual(first.id, second.id)
        self.assertEqual(second.usage_count, 2)
        self.assertTrue(second.is_pinned)
        self.assertTrue(second.is_favorite)
        self.assertEqual(self.storage.count_clips(), 1)

    def test_image_hash_distinguishes_visually_similar_images(self) -> None:
        img1 = Image.new("RGBA", (64, 64), (167, 139, 250, 255))
        img2 = Image.new("RGBA", (64, 64), (167, 139, 250, 255))
        draw = ImageDraw.Draw(img2)
        draw.point((32, 32), fill=(255, 255, 255, 255))

        self.assertEqual(
            DuplicateDetector.compute_image_hash(img1),
            DuplicateDetector.compute_image_hash(img1.copy()),
        )
        self.assertNotEqual(
            DuplicateDetector.compute_image_hash(img1),
            DuplicateDetector.compute_image_hash(img2),
        )
        self.assertFalse(DuplicateDetector.are_images_identical(img1, img2))


if __name__ == "__main__":
    unittest.main()
