"""
High-level Persistent Storage Repository for SNIPLY.
Provides CRUD, search, filtering, sorting, tag management, collections, snippets,
settings persistence, statistics aggregation, backup, and JSON export/import.
"""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from app.constants import (
    CONTENT_TYPE_CODE,
    CONTENT_TYPE_COLOR,
    CONTENT_TYPE_IMAGE,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_TEXT,
    CONTENT_TYPE_URL,
)
from app.paths import AppPaths
from core.database import Database
from core.logger import get_logger
from models.clip import Clip
from models.collection import Collection
from models.settings import AppSettings
from models.snippet import Snippet

logger = get_logger("storage")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StorageRepository:
    """Repository encapsulating all SQLite data operations with parameterized queries."""

    def __init__(self, database: Optional[Database] = None) -> None:
        self.db = database or Database()

    # -------------------------------------------------------------------------
    # Clips CRUD & Deduplication Support
    # -------------------------------------------------------------------------

    def add_or_update_clip(
        self,
        clip: Clip,
        deduplicate: bool = True,
    ) -> Tuple[Clip, bool]:
        """
        Insert a new clip or update an existing duplicate clip.
        Returns (saved_clip, is_duplicate).
        Pinned and favorite states are strictly preserved on duplicate updates.
        """
        now_iso = _utc_now_iso()
        with self.db.transaction() as conn:
            if deduplicate and clip.content_hash:
                existing_row = conn.execute(
                    """
                    SELECT c.*, col.name AS collection_name, col.color AS collection_color
                    FROM clips c
                    LEFT JOIN collections col ON c.collection_id = col.id
                    WHERE c.content_hash = ? AND c.content_type = ?
                    ORDER BY c.id DESC LIMIT 1
                    """,
                    (clip.content_hash, clip.content_type),
                ).fetchone()

                if existing_row is not None:
                    existing_id = int(existing_row["id"])
                    new_count = int(existing_row["usage_count"]) + 1
                    conn.execute(
                        """
                        UPDATE clips
                        SET last_copied_at = ?,
                            last_used_at = ?,
                            usage_count = ?,
                            metadata_json = ?
                        WHERE id = ?
                        """,
                        (now_iso, now_iso, new_count, clip.metadata_json, existing_id),
                    )
                    updated = self._get_clip_in_conn(conn, existing_id)
                    if updated is not None:
                        return updated, True

            cursor = conn.execute(
                """
                INSERT INTO clips (
                    content_type, text_content, html_content, content_hash,
                    image_path, thumbnail_path, preview, metadata_json,
                    created_at, last_copied_at, last_used_at, usage_count,
                    is_pinned, is_favorite, collection_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clip.content_type,
                    clip.text_content,
                    clip.html_content,
                    clip.content_hash,
                    clip.image_path,
                    clip.thumbnail_path,
                    clip.preview,
                    clip.metadata_json,
                    clip.created_at or now_iso,
                    clip.last_copied_at or now_iso,
                    clip.last_used_at or now_iso,
                    clip.usage_count,
                    1 if clip.is_pinned else 0,
                    1 if clip.is_favorite else 0,
                    clip.collection_id,
                ),
            )
            clip_id = int(cursor.lastrowid)
            if clip.tags:
                self._set_clip_tags_in_conn(conn, clip_id, clip.tags)
            saved = self._get_clip_in_conn(conn, clip_id)
            assert saved is not None
            return saved, False

    def _get_clip_in_conn(self, conn: sqlite3.Connection, clip_id: int) -> Optional[Clip]:
        row = conn.execute(
            """
            SELECT c.*, col.name AS collection_name, col.color AS collection_color
            FROM clips c
            LEFT JOIN collections col ON c.collection_id = col.id
            WHERE c.id = ?
            """,
            (clip_id,),
        ).fetchone()
        if not row:
            return None
        tags = self._get_clip_tags_in_conn(conn, clip_id)
        return Clip.from_row(row, tags=tags)

    def get_clip(self, clip_id: int) -> Optional[Clip]:
        with self.db.connection() as conn:
            return self._get_clip_in_conn(conn, clip_id)

    def find_by_hash(self, content_hash: str, content_type: Optional[str] = None) -> Optional[Clip]:
        with self.db.connection() as conn:
            if content_type:
                row = conn.execute(
                    """
                    SELECT c.*, col.name AS collection_name, col.color AS collection_color
                    FROM clips c
                    LEFT JOIN collections col ON c.collection_id = col.id
                    WHERE c.content_hash = ? AND c.content_type = ?
                    LIMIT 1
                    """,
                    (content_hash, content_type),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT c.*, col.name AS collection_name, col.color AS collection_color
                    FROM clips c
                    LEFT JOIN collections col ON c.collection_id = col.id
                    WHERE c.content_hash = ?
                    LIMIT 1
                    """,
                    (content_hash,),
                ).fetchone()
            if not row:
                return None
            tags = self._get_clip_tags_in_conn(conn, int(row["id"]))
            return Clip.from_row(row, tags=tags)

    def query_clips(
        self,
        search_query: str = "",
        content_type: Optional[str] = None,
        only_pinned: bool = False,
        only_favorites: bool = False,
        collection_id: Optional[int] = None,
        sort_by: str = "recent_copied",  # recent_copied | recent_used | oldest | most_used
        pinned_first: bool = True,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Clip]:
        """
        Query clips with fast local filtering, Unicode case-insensitive search, and sorting.
        """
        conditions: List[str] = []
        params: List[Any] = []

        if content_type and content_type != "all":
            conditions.append("c.content_type = ?")
            params.append(content_type)

        if only_pinned:
            conditions.append("c.is_pinned = 1")

        if only_favorites:
            conditions.append("c.is_favorite = 1")

        if collection_id is not None:
            conditions.append("c.collection_id = ?")
            params.append(collection_id)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        sort_map = {
            "recent_copied": "c.last_copied_at DESC, c.id DESC",
            "recent_used": "c.last_used_at DESC, c.id DESC",
            "oldest": "c.created_at ASC, c.id ASC",
            "most_used": "c.usage_count DESC, c.last_copied_at DESC",
        }
        order_clause = sort_map.get(sort_by, "c.last_copied_at DESC, c.id DESC")
        if pinned_first and not only_pinned:
            order_clause = f"c.is_pinned DESC, {order_clause}"

        with self.db.connection() as conn:
            # Register Unicode casefold function for full Cyrillic + international search
            conn.create_function(
                "PY_CONTAINS",
                2,
                lambda haystack, needle: (needle in haystack.casefold()) if (haystack and needle) else False,
            )

            if search_query and search_query.strip():
                needle = search_query.strip().casefold()
                search_cond = """(
                    PY_CONTAINS(COALESCE(c.text_content, ''), ?)
                    OR PY_CONTAINS(COALESCE(c.preview, ''), ?)
                    OR PY_CONTAINS(COALESCE(c.content_type, ''), ?)
                    OR PY_CONTAINS(COALESCE(col.name, ''), ?)
                    OR EXISTS (
                        SELECT 1 FROM clip_tags ct
                        JOIN tags t ON ct.tag_id = t.id
                        WHERE ct.clip_id = c.id AND PY_CONTAINS(t.name, ?)
                    )
                )"""
                if where_sql:
                    where_sql = f"{where_sql} AND {search_cond}"
                else:
                    where_sql = f"WHERE {search_cond}"
                params.extend([needle, needle, needle, needle, needle])

            sql = f"""
                SELECT c.*, col.name AS collection_name, col.color AS collection_color
                FROM clips c
                LEFT JOIN collections col ON c.collection_id = col.id
                {where_sql}
                ORDER BY {order_clause}
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            rows = conn.execute(sql, tuple(params)).fetchall()

            if not rows:
                return []

            clip_ids = [int(r["id"]) for r in rows]
            tags_by_clip = self._batch_get_tags_in_conn(conn, clip_ids)
            return [Clip.from_row(r, tags=tags_by_clip.get(int(r["id"]), [])) for r in rows]

    def count_clips(
        self,
        content_type: Optional[str] = None,
        only_pinned: bool = False,
        only_favorites: bool = False,
        collection_id: Optional[int] = None,
    ) -> int:
        conditions: List[str] = []
        params: List[Any] = []
        if content_type and content_type != "all":
            conditions.append("content_type = ?")
            params.append(content_type)
        if only_pinned:
            conditions.append("is_pinned = 1")
        if only_favorites:
            conditions.append("is_favorite = 1")
        if collection_id is not None:
            conditions.append("collection_id = ?")
            params.append(collection_id)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.db.connection() as conn:
            row = conn.execute(f"SELECT COUNT(*) FROM clips {where_sql}", tuple(params)).fetchone()
            return int(row[0]) if row else 0

    def set_pinned(self, clip_id: int, is_pinned: bool) -> Optional[Clip]:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE clips SET is_pinned = ? WHERE id = ?",
                (1 if is_pinned else 0, clip_id),
            )
            return self._get_clip_in_conn(conn, clip_id)

    def set_favorite(self, clip_id: int, is_favorite: bool) -> Optional[Clip]:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE clips SET is_favorite = ? WHERE id = ?",
                (1 if is_favorite else 0, clip_id),
            )
            return self._get_clip_in_conn(conn, clip_id)

    def set_clip_collection(self, clip_id: int, collection_id: Optional[int]) -> Optional[Clip]:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE clips SET collection_id = ? WHERE id = ?",
                (collection_id, clip_id),
            )
            return self._get_clip_in_conn(conn, clip_id)

    def mark_clip_used(self, clip_id: int) -> Optional[Clip]:
        now_iso = _utc_now_iso()
        with self.db.transaction() as conn:
            conn.execute(
                """
                UPDATE clips
                SET last_used_at = ?, usage_count = usage_count + 1
                WHERE id = ?
                """,
                (now_iso, clip_id),
            )
            return self._get_clip_in_conn(conn, clip_id)

    def delete_clip(self, clip_id: int, allow_pinned: bool = False) -> bool:
        """
        Delete a clip by ID. If the clip is pinned and allow_pinned is False,
        refuses deletion to protect pinned items from accidental removal.
        """
        with self.db.transaction() as conn:
            row = conn.execute(
                "SELECT is_pinned, image_path, thumbnail_path FROM clips WHERE id = ?",
                (clip_id,),
            ).fetchone()
            if not row:
                return False
            if bool(row["is_pinned"]) and not allow_pinned:
                return False

            conn.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
            self._cleanup_image_files(row["image_path"], row["thumbnail_path"])
            return True

    def bulk_delete_clips(self, clip_ids: List[int], allow_pinned: bool = False) -> int:
        if not clip_ids:
            return 0
        deleted = 0
        for cid in clip_ids:
            if self.delete_clip(cid, allow_pinned=allow_pinned):
                deleted += 1
        return deleted

    def clear_unprotected_history(self, include_favorites: bool = False) -> int:
        """Delete all unpinned clips (and non-favorite clips unless include_favorites=True)."""
        with self.db.transaction() as conn:
            cond = "is_pinned = 0" if include_favorites else "is_pinned = 0 AND is_favorite = 0"
            rows = conn.execute(
                f"SELECT id, image_path, thumbnail_path FROM clips WHERE {cond}"
            ).fetchall()
            for r in rows:
                self._cleanup_image_files(r["image_path"], r["thumbnail_path"])
            cursor = conn.execute(f"DELETE FROM clips WHERE {cond}")
            return cursor.rowcount

    @staticmethod
    def _cleanup_image_files(image_path: Optional[str], thumbnail_path: Optional[str]) -> None:
        for p_str in (image_path, thumbnail_path):
            if p_str:
                try:
                    p = Path(p_str)
                    if p.exists() and p.is_file():
                        p.unlink()
                except OSError:
                    pass

    # -------------------------------------------------------------------------
    # Tags
    # -------------------------------------------------------------------------

    def _get_clip_tags_in_conn(self, conn: sqlite3.Connection, clip_id: int) -> List[str]:
        rows = conn.execute(
            """
            SELECT t.name FROM tags t
            JOIN clip_tags ct ON ct.tag_id = t.id
            WHERE ct.clip_id = ?
            ORDER BY t.name ASC
            """,
            (clip_id,),
        ).fetchall()
        return [str(r["name"]) for r in rows]

    def _batch_get_tags_in_conn(
        self, conn: sqlite3.Connection, clip_ids: List[int]
    ) -> Dict[int, List[str]]:
        if not clip_ids:
            return {}
        placeholders = ",".join("?" for _ in clip_ids)
        rows = conn.execute(
            f"""
            SELECT ct.clip_id, t.name
            FROM clip_tags ct
            JOIN tags t ON ct.tag_id = t.id
            WHERE ct.clip_id IN ({placeholders})
            ORDER BY t.name ASC
            """,
            tuple(clip_ids),
        ).fetchall()
        result: Dict[int, List[str]] = {}
        for r in rows:
            result.setdefault(int(r["clip_id"]), []).append(str(r["name"]))
        return result

    def _set_clip_tags_in_conn(
        self, conn: sqlite3.Connection, clip_id: int, tags: List[str]
    ) -> None:
        conn.execute("DELETE FROM clip_tags WHERE clip_id = ?", (clip_id,))
        cleaned = sorted({t.strip() for t in tags if t.strip()})
        for tag_name in cleaned:
            conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            tag_row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
            if tag_row:
                conn.execute(
                    "INSERT OR IGNORE INTO clip_tags (clip_id, tag_id) VALUES (?, ?)",
                    (clip_id, int(tag_row["id"])),
                )

    def set_clip_tags(self, clip_id: int, tags: List[str]) -> Optional[Clip]:
        with self.db.transaction() as conn:
            self._set_clip_tags_in_conn(conn, clip_id, tags)
            return self._get_clip_in_conn(conn, clip_id)

    # -------------------------------------------------------------------------
    # Collections
    # -------------------------------------------------------------------------

    def list_collections(self) -> List[Collection]:
        with self.db.connection() as conn:
            rows = conn.execute(
                """
                SELECT col.*, COUNT(c.id) AS clip_count
                FROM collections col
                LEFT JOIN clips c ON c.collection_id = col.id
                GROUP BY col.id
                ORDER BY col.name COLLATE NOCASE ASC
                """
            ).fetchall()
            return [Collection.from_row(r) for r in rows]

    def create_collection(
        self,
        name: str,
        description: str = "",
        color: str = "#A78BFA",
        icon: str = "collections",
    ) -> Collection:
        now_iso = _utc_now_iso()
        with self.db.transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO collections (name, description, color, icon, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name.strip(), description.strip(), color, icon, now_iso),
            )
            col_id = int(cursor.lastrowid)
            row = conn.execute(
                "SELECT *, 0 AS clip_count FROM collections WHERE id = ?", (col_id,)
            ).fetchone()
            return Collection.from_row(row)

    def update_collection(
        self,
        collection_id: int,
        name: str,
        description: str = "",
        color: str = "#A78BFA",
        icon: str = "collections",
    ) -> Optional[Collection]:
        with self.db.transaction() as conn:
            conn.execute(
                """
                UPDATE collections
                SET name = ?, description = ?, color = ?, icon = ?
                WHERE id = ?
                """,
                (name.strip(), description.strip(), color, icon, collection_id),
            )
            row = conn.execute(
                """
                SELECT col.*, COUNT(c.id) AS clip_count
                FROM collections col
                LEFT JOIN clips c ON c.collection_id = col.id
                WHERE col.id = ?
                GROUP BY col.id
                """,
                (collection_id,),
            ).fetchone()
            return Collection.from_row(row) if row else None

    def delete_collection(self, collection_id: int, delete_underlying_clips: bool = False) -> bool:
        """
        Delete a collection.
        By default (`delete_underlying_clips=False`), keeps all entries and unassigns `collection_id`.
        If `delete_underlying_clips=True`, deletes unpinned entries in that collection.
        """
        with self.db.transaction() as conn:
            if delete_underlying_clips:
                rows = conn.execute(
                    """
                    SELECT image_path, thumbnail_path FROM clips
                    WHERE collection_id = ? AND is_pinned = 0
                    """,
                    (collection_id,),
                ).fetchall()
                for r in rows:
                    self._cleanup_image_files(r["image_path"], r["thumbnail_path"])
                conn.execute(
                    "DELETE FROM clips WHERE collection_id = ? AND is_pinned = 0",
                    (collection_id,),
                )
            conn.execute(
                "UPDATE clips SET collection_id = NULL WHERE collection_id = ?",
                (collection_id,),
            )
            cursor = conn.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
            return cursor.rowcount > 0

    # -------------------------------------------------------------------------
    # Snippets Library
    # -------------------------------------------------------------------------

    def list_snippets(self, search_query: str = "", category: Optional[str] = None) -> List[Snippet]:
        with self.db.connection() as conn:
            conn.create_function(
                "PY_CONTAINS",
                2,
                lambda haystack, needle: (needle in haystack.casefold()) if (haystack and needle) else False,
            )
            conditions: List[str] = []
            params: List[Any] = []

            if category and category != "All":
                conditions.append("category = ?")
                params.append(category)

            if search_query and search_query.strip():
                needle = search_query.strip().casefold()
                conditions.append(
                    """(
                        PY_CONTAINS(name, ?)
                        OR PY_CONTAINS(description, ?)
                        OR PY_CONTAINS(content, ?)
                        OR PY_CONTAINS(category, ?)
                        OR PY_CONTAINS(tags, ?)
                    )"""
                )
                params.extend([needle, needle, needle, needle, needle])

            where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            rows = conn.execute(
                f"""
                SELECT * FROM snippets
                {where_sql}
                ORDER BY is_pinned DESC, updated_at DESC
                """,
                tuple(params),
            ).fetchall()
            return [Snippet.from_row(r) for r in rows]

    def create_snippet(self, snippet: Snippet) -> Snippet:
        now_iso = _utc_now_iso()
        with self.db.transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO snippets (
                    name, description, content, category, tags,
                    created_at, updated_at, last_used_at, is_pinned
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snippet.name.strip(),
                    snippet.description.strip(),
                    snippet.content,
                    snippet.category.strip() or "General",
                    snippet.tags_str,
                    now_iso,
                    now_iso,
                    snippet.last_used_at,
                    1 if snippet.is_pinned else 0,
                ),
            )
            row = conn.execute(
                "SELECT * FROM snippets WHERE id = ?", (int(cursor.lastrowid),)
            ).fetchone()
            return Snippet.from_row(row)

    def update_snippet(self, snippet: Snippet) -> Optional[Snippet]:
        if snippet.id is None:
            return None
        now_iso = _utc_now_iso()
        with self.db.transaction() as conn:
            conn.execute(
                """
                UPDATE snippets
                SET name = ?, description = ?, content = ?, category = ?,
                    tags = ?, updated_at = ?, is_pinned = ?
                WHERE id = ?
                """,
                (
                    snippet.name.strip(),
                    snippet.description.strip(),
                    snippet.content,
                    snippet.category.strip() or "General",
                    snippet.tags_str,
                    now_iso,
                    1 if snippet.is_pinned else 0,
                    snippet.id,
                ),
            )
            row = conn.execute("SELECT * FROM snippets WHERE id = ?", (snippet.id,)).fetchone()
            return Snippet.from_row(row) if row else None

    def duplicate_snippet(self, snippet_id: int) -> Optional[Snippet]:
        with self.db.connection() as conn:
            row = conn.execute("SELECT * FROM snippets WHERE id = ?", (snippet_id,)).fetchone()
            if not row:
                return None
            orig = Snippet.from_row(row)
        copy_snip = Snippet(
            name=f"{orig.name} (Copy)",
            description=orig.description,
            content=orig.content,
            category=orig.category,
            tags=list(orig.tags),
            is_pinned=orig.is_pinned,
        )
        return self.create_snippet(copy_snip)

    def mark_snippet_used(self, snippet_id: int) -> None:
        now_iso = _utc_now_iso()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE snippets SET last_used_at = ? WHERE id = ?",
                (now_iso, snippet_id),
            )

    def delete_snippet(self, snippet_id: int) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.execute("DELETE FROM snippets WHERE id = ?", (snippet_id,))
            return cursor.rowcount > 0

    # -------------------------------------------------------------------------
    # Settings & Excluded Applications
    # -------------------------------------------------------------------------

    def load_settings(self) -> AppSettings:
        with self.db.connection() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            raw: Dict[str, Any] = {}
            for r in rows:
                try:
                    raw[str(r["key"])] = json.loads(r["value"])
                except Exception:
                    raw[str(r["key"])] = r["value"]
            return AppSettings.from_dict(raw)

    def save_settings(self, settings: AppSettings) -> None:
        data = settings.to_dict()
        with self.db.transaction() as conn:
            for key, val in data.items():
                conn.execute(
                    """
                    INSERT INTO settings (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, json.dumps(val)),
                )

    def set_setting(self, key: str, value: Any) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, json.dumps(value)),
            )

    def list_excluded_apps(self) -> List[str]:
        with self.db.connection() as conn:
            rows = conn.execute(
                "SELECT executable_name FROM excluded_apps ORDER BY executable_name COLLATE NOCASE ASC"
            ).fetchall()
            return [str(r["executable_name"]) for r in rows]

    def add_excluded_app(self, executable_name: str) -> bool:
        cleaned = executable_name.strip()
        if not cleaned:
            return False
        now_iso = _utc_now_iso()
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO excluded_apps (executable_name, created_at) VALUES (?, ?)",
                (cleaned, now_iso),
            )
            return cursor.rowcount > 0

    def remove_excluded_app(self, executable_name: str) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "DELETE FROM excluded_apps WHERE executable_name = ? COLLATE NOCASE",
                (executable_name.strip(),),
            )
            return cursor.rowcount > 0

    # -------------------------------------------------------------------------
    # Clipboard Insights / Statistics (100% Derived from Actual Database Records)
    # -------------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Compute real statistics from the local database."""
        with self.db.connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
            by_type_rows = conn.execute(
                "SELECT content_type, COUNT(*) AS cnt FROM clips GROUP BY content_type"
            ).fetchall()
            by_type = {str(r["content_type"]): int(r["cnt"]) for r in by_type_rows}

            top_clips_rows = conn.execute(
                """
                SELECT id, preview, content_type, usage_count
                FROM clips
                ORDER BY usage_count DESC, last_used_at DESC
                LIMIT 5
                """
            ).fetchall()
            top_clips = [dict(r) for r in top_clips_rows]

            top_cols_rows = conn.execute(
                """
                SELECT col.name, col.color, COUNT(c.id) AS clip_count
                FROM collections col
                LEFT JOIN clips c ON c.collection_id = col.id
                GROUP BY col.id
                ORDER BY clip_count DESC, col.name ASC
                """
            ).fetchall()
            top_collections = [dict(r) for r in top_cols_rows]

            # Daily activity over the last 7 days
            daily_activity: List[Tuple[str, int]] = []
            now_utc = datetime.now(timezone.utc)
            for days_back in range(6, -1, -1):
                day_dt = now_utc - timedelta(days=days_back)
                day_prefix = day_dt.strftime("%Y-%m-%d")
                cnt_row = conn.execute(
                    "SELECT COUNT(*) FROM clips WHERE created_at LIKE ?",
                    (f"{day_prefix}%",),
                ).fetchone()
                daily_activity.append((day_prefix, int(cnt_row[0]) if cnt_row else 0))

            text_like_count = (
                by_type.get(CONTENT_TYPE_TEXT, 0)
                + by_type.get(CONTENT_TYPE_CODE, 0)
                + by_type.get(CONTENT_TYPE_JSON, 0)
                + by_type.get(CONTENT_TYPE_URL, 0)
                + by_type.get("email", 0)
            )

            return {
                "total_clips": int(total),
                "text_entries": text_like_count,
                "image_entries": by_type.get(CONTENT_TYPE_IMAGE, 0),
                "color_entries": by_type.get(CONTENT_TYPE_COLOR, 0),
                "by_type": by_type,
                "most_frequent_clips": top_clips,
                "collections_breakdown": top_collections,
                "daily_activity": daily_activity,
            }

    # -------------------------------------------------------------------------
    # Storage Size, Backup, Export & Import
    # -------------------------------------------------------------------------

    def get_storage_metrics(self) -> Dict[str, int]:
        db_bytes = self.db.db_path.stat().st_size if self.db.db_path.exists() else 0
        img_bytes = 0
        for folder in (AppPaths.get_images_storage_dir(), AppPaths.get_thumbnails_dir()):
            if folder.exists():
                for f in folder.rglob("*"):
                    if f.is_file():
                        img_bytes += f.stat().st_size
        return {
            "db_bytes": db_bytes,
            "images_bytes": img_bytes,
            "total_bytes": db_bytes + img_bytes,
        }

    def backup_database(self, dest_path: Optional[Path] = None) -> Path:
        if dest_path is None:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            dest_path = AppPaths.get_backups_dir() / f"sniply_backup_{stamp}.db"
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with self.db.connection() as src_conn:
            dst_conn = sqlite3.connect(str(dest_path))
            try:
                src_conn.backup(dst_conn)
            finally:
                dst_conn.close()
        return dest_path

    def export_to_json(self, file_path: Path) -> None:
        clips = self.query_clips(limit=100000)
        collections = self.list_collections()
        snippets = self.list_snippets()
        payload = {
            "app": "SNIPLY",
            "version": "1.0.0",
            "exported_at": _utc_now_iso(),
            "collections": [
                {
                    "name": c.name,
                    "description": c.description,
                    "color": c.color,
                    "icon": c.icon,
                }
                for c in collections
            ],
            "snippets": [
                {
                    "name": s.name,
                    "description": s.description,
                    "content": s.content,
                    "category": s.category,
                    "tags": s.tags,
                    "is_pinned": s.is_pinned,
                }
                for s in snippets
            ],
            "clips": [
                {
                    "content_type": cl.content_type,
                    "text_content": cl.text_content,
                    "html_content": cl.html_content,
                    "content_hash": cl.content_hash,
                    "preview": cl.preview,
                    "metadata": cl.metadata,
                    "created_at": cl.created_at,
                    "usage_count": cl.usage_count,
                    "is_pinned": cl.is_pinned,
                    "is_favorite": cl.is_favorite,
                    "tags": cl.tags,
                }
                for cl in clips
                if cl.content_type != CONTENT_TYPE_IMAGE
            ],
        }
        file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def import_from_json(self, file_path: Path) -> Dict[str, int]:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        imported_clips = 0
        imported_snippets = 0
        for col_data in data.get("collections", []):
            try:
                self.create_collection(
                    name=col_data["name"],
                    description=col_data.get("description", ""),
                    color=col_data.get("color", "#A78BFA"),
                    icon=col_data.get("icon", "collections"),
                )
            except sqlite3.IntegrityError:
                pass

        for snip_data in data.get("snippets", []):
            self.create_snippet(
                Snippet(
                    name=snip_data.get("name", "Imported Snippet"),
                    description=snip_data.get("description", ""),
                    content=snip_data.get("content", ""),
                    category=snip_data.get("category", "General"),
                    tags=snip_data.get("tags", []),
                    is_pinned=bool(snip_data.get("is_pinned", False)),
                )
            )
            imported_snippets += 1

        for clip_data in data.get("clips", []):
            clip = Clip(
                content_type=clip_data.get("content_type", CONTENT_TYPE_TEXT),
                text_content=clip_data.get("text_content"),
                html_content=clip_data.get("html_content"),
                content_hash=clip_data.get("content_hash", ""),
                preview=clip_data.get("preview", ""),
                metadata=clip_data.get("metadata", {}),
                is_pinned=bool(clip_data.get("is_pinned", False)),
                is_favorite=bool(clip_data.get("is_favorite", False)),
                tags=clip_data.get("tags", []),
            )
            self.add_or_update_clip(clip, deduplicate=True)
            imported_clips += 1

        return {"clips": imported_clips, "snippets": imported_snippets}
