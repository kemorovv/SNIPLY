"""
Automated Tests for Retention Cleanup (Age-based & Max-History-Size)
verifying that pinned and favorite entries are strictly protected.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from app.constants import CONTENT_TYPE_TEXT
from app.paths import AppPaths
from core.database import Database
from core.retention import RetentionManager
from core.storage import StorageRepository
from models.clip import Clip


class TestRetentionCleanup(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp_dir.name)
        AppPaths.set_custom_data_dir(self.base_path)
        self.storage = StorageRepository(Database(self.base_path / "retention.db"))
        self.retention = RetentionManager(self.storage)

    def tearDown(self) -> None:
        AppPaths.set_custom_data_dir(None)
        self.tmp_dir.cleanup()

    def test_age_and_count_cleanup_protects_pinned_and_favorites(self) -> None:
        old_iso = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        recent_iso = datetime.now(timezone.utc).isoformat()

        # 1. Old unprotected entry (should be deleted by 30-day rule)
        self.storage.add_or_update_clip(
            Clip(
                content_type=CONTENT_TYPE_TEXT,
                text_content="Old unprotected",
                content_hash="h_old_unprot",
                created_at=old_iso,
                last_copied_at=old_iso,
            ),
            deduplicate=False,
        )

        # 2. Old pinned entry (must survive 30-day rule)
        pinned_old, _ = self.storage.add_or_update_clip(
            Clip(
                content_type=CONTENT_TYPE_TEXT,
                text_content="Old pinned",
                content_hash="h_old_pin",
                created_at=old_iso,
                last_copied_at=old_iso,
                is_pinned=True,
            ),
            deduplicate=False,
        )

        # 3. Old favorite entry (must survive 30-day rule)
        fav_old, _ = self.storage.add_or_update_clip(
            Clip(
                content_type=CONTENT_TYPE_TEXT,
                text_content="Old favorite",
                content_hash="h_old_fav",
                created_at=old_iso,
                last_copied_at=old_iso,
                is_favorite=True,
            ),
            deduplicate=False,
        )

        # 4. Add 5 recent unprotected entries and set max_history_size=3
        for i in range(5):
            self.storage.add_or_update_clip(
                Clip(
                    content_type=CONTENT_TYPE_TEXT,
                    text_content=f"Recent {i}",
                    content_hash=f"h_rec_{i}",
                    created_at=recent_iso,
                    last_copied_at=recent_iso,
                ),
                deduplicate=False,
            )

        result = self.retention.run_cleanup(retention_days=30, max_history_size=3)
        self.assertEqual(result["expired_deleted"], 1)
        self.assertEqual(result["overflow_deleted"], 2)

        # Total remaining should be 2 protected + 3 recent = 5
        self.assertEqual(self.storage.count_clips(), 5)
        self.assertIsNotNone(self.storage.get_clip(pinned_old.id))  # type: ignore[arg-type]
        self.assertIsNotNone(self.storage.get_clip(fav_old.id))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
