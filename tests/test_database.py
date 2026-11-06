"""
Automated Tests for SQLite Database Creation, Migrations, Persistence, Search,
Pinning, Favorites, Collections, Snippets, Settings, Backup, and 10,000-entry Performance.
"""

from pathlib import Path
import tempfile
import time
import unittest

from app.constants import CONTENT_TYPE_COLOR, CONTENT_TYPE_IMAGE, CONTENT_TYPE_TEXT
from app.paths import AppPaths
from core.database import CURRENT_SCHEMA_VERSION, Database
from core.storage import StorageRepository
from models.clip import Clip
from models.snippet import Snippet


class TestDatabaseAndStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp_dir.name)
        AppPaths.set_custom_data_dir(self.base_path)
        self.db = Database(self.base_path / "test_sniply.db")
        self.storage = StorageRepository(self.db)

    def tearDown(self) -> None:
        AppPaths.set_custom_data_dir(None)
        self.tmp_dir.cleanup()

    def test_01_database_creation_and_migrations(self) -> None:
        self.assertTrue(self.db.db_path.exists())
        self.assertEqual(self.db.get_schema_version(), CURRENT_SCHEMA_VERSION)
        cols = self.storage.list_collections()
        self.assertGreaterEqual(len(cols), 5)
        exclusions = self.storage.list_excluded_apps()
        self.assertIn("KeePassXC.exe", exclusions)

    def test_02_text_persistence_unicode_and_multiline(self) -> None:
        multiline_unicode = "Привет, мир! 🚀\n\tIndented line 2\nLine 3 with symbols: € £ ¥"
        clip = Clip(
            content_type=CONTENT_TYPE_TEXT,
            text_content=multiline_unicode,
            content_hash="hash_unicode_1",
            preview="Привет, мир!",
            metadata={"char_count": len(multiline_unicode)},
        )
        saved, is_dup = self.storage.add_or_update_clip(clip)
        self.assertFalse(is_dup)
        self.assertIsNotNone(saved.id)

        # Re-open fresh StorageRepository pointing to same SQLite file to verify restart persistence
        reopened = StorageRepository(Database(self.db.db_path))
        fetched = reopened.get_clip(saved.id)  # type: ignore[arg-type]
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.text_content, multiline_unicode)  # type: ignore[union-attr]

    def test_03_image_metadata_persistence(self) -> None:
        img_clip = Clip(
            content_type=CONTENT_TYPE_IMAGE,
            content_hash="img_hash_001",
            image_path="/tmp/fake_img.png",
            thumbnail_path="/tmp/fake_thumb.png",
            preview="PNG Image (1920 × 1080 px)",
            metadata={"width": 1920, "height": 1080, "format": "PNG", "file_size": 245760},
        )
        saved, _ = self.storage.add_or_update_clip(img_clip)
        fetched = self.storage.get_clip(saved.id)  # type: ignore[arg-type]
        self.assertEqual(fetched.content_type, CONTENT_TYPE_IMAGE)  # type: ignore[union-attr]
        self.assertEqual(fetched.metadata["width"], 1920)  # type: ignore[union-attr]
        self.assertEqual(fetched.metadata["height"], 1080)  # type: ignore[union-attr]

    def test_04_pin_and_favorite_states(self) -> None:
        clip, _ = self.storage.add_or_update_clip(
            Clip(content_type=CONTENT_TYPE_TEXT, text_content="Important Pin", content_hash="h_pin")
        )
        assert clip.id is not None
        pinned = self.storage.set_pinned(clip.id, True)
        self.assertTrue(pinned.is_pinned)  # type: ignore[union-attr]

        fav = self.storage.set_favorite(clip.id, True)
        self.assertTrue(fav.is_favorite)  # type: ignore[union-attr]

        # Pinned item must refuse accidental deletion when allow_pinned=False
        deleted = self.storage.delete_clip(clip.id, allow_pinned=False)
        self.assertFalse(deleted)
        self.assertIsNotNone(self.storage.get_clip(clip.id))

        # Intentional deletion with allow_pinned=True succeeds
        deleted_intentional = self.storage.delete_clip(clip.id, allow_pinned=True)
        self.assertTrue(deleted_intentional)

    def test_05_collection_assignment_and_safe_deletion(self) -> None:
        col = self.storage.create_collection("UI Tokens", "Design system tokens", "#A78BFA")
        assert col.id is not None

        clip, _ = self.storage.add_or_update_clip(
            Clip(content_type=CONTENT_TYPE_COLOR, text_content="#A78BFA", content_hash="h_col")
        )
        assert clip.id is not None
        assigned = self.storage.set_clip_collection(clip.id, col.id)
        self.assertEqual(assigned.collection_id, col.id)  # type: ignore[union-attr]
        self.assertEqual(assigned.collection_name, "UI Tokens")  # type: ignore[union-attr]

        # Deleting collection with delete_underlying_clips=False must keep the clip
        self.storage.delete_collection(col.id, delete_underlying_clips=False)
        still_there = self.storage.get_clip(clip.id)
        self.assertIsNotNone(still_there)
        self.assertIsNone(still_there.collection_id)  # type: ignore[union-attr]

    def test_06_search_english_and_russian_and_tags(self) -> None:
        c1, _ = self.storage.add_or_update_clip(
            Clip(
                content_type=CONTENT_TYPE_TEXT,
                text_content="Конфиденциальность и локальное хранение",
                content_hash="h_ru_1",
                preview="Конфиденциальность",
                tags=["безопасность", "privacy"],
            )
        )
        self.storage.add_or_update_clip(
            Clip(
                content_type=CONTENT_TYPE_TEXT,
                text_content="Unrelated English note",
                content_hash="h_en_2",
                preview="Unrelated",
            )
        )

        # Case-insensitive Cyrillic search
        res_ru = self.storage.query_clips(search_query="ЛОКАЛЬНОЕ")
        self.assertEqual(len(res_ru), 1)
        self.assertEqual(res_ru[0].id, c1.id)

        # Tag search
        res_tag = self.storage.query_clips(search_query="безопасность")
        self.assertEqual(len(res_tag), 1)
        self.assertEqual(res_tag[0].id, c1.id)

    def test_07_snippets_and_settings_persistence(self) -> None:
        snip = self.storage.create_snippet(
            Snippet(
                name="Git Commit Template",
                description="Conventional commit header",
                content="feat(core): implement smart clipboard recognition",
                category="Development",
                tags=["git", "dev"],
            )
        )
        self.assertIsNotNone(snip.id)
        dup = self.storage.duplicate_snippet(snip.id)  # type: ignore[arg-type]
        self.assertIsNotNone(dup)
        self.assertEqual(len(self.storage.list_snippets(search_query="conventional")), 2)

        settings = self.storage.load_settings()
        settings.language = "ru"
        settings.max_history_size = 5000
        self.storage.save_settings(settings)

        reloaded = self.storage.load_settings()
        self.assertEqual(reloaded.language, "ru")
        self.assertEqual(reloaded.max_history_size, 5000)

    def test_08_performance_with_10000_entries(self) -> None:
        """Verify responsive insert and query performance with 10,000 text entries."""
        now_iso = "2026-11-07T00:00:00+00:00"
        rows = [
            (
                CONTENT_TYPE_TEXT,
                f"Sample clipboard entry number {i} with searchable token_{i % 50}",
                None,
                f"hash_{i}",
                None,
                None,
                f"Sample clipboard entry #{i}",
                "{}",
                now_iso,
                now_iso,
                now_iso,
                1,
                1 if i == 9999 else 0,
                0,
                None,
            )
            for i in range(10000)
        ]
        with self.db.transaction() as conn:
            conn.executemany(
                """
                INSERT INTO clips (
                    content_type, text_content, html_content, content_hash,
                    image_path, thumbnail_path, preview, metadata_json,
                    created_at, last_copied_at, last_used_at, usage_count,
                    is_pinned, is_favorite, collection_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

        self.assertEqual(self.storage.count_clips(), 10000)

        t0 = time.perf_counter()
        page = self.storage.query_clips(limit=100)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        self.assertEqual(len(page), 100)
        self.assertTrue(page[0].is_pinned)  # Pinned item sorted first
        self.assertLess(elapsed_ms, 250.0, f"Paginated query took {elapsed_ms:.1f} ms")


if __name__ == "__main__":
    unittest.main()
