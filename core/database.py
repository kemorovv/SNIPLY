"""
SQLite Database Engine & Schema Migration Manager for SNIPLY.
Enforces parameterized queries, foreign keys, WAL mode, indexes, and transactional safety.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import threading
from typing import Any, Callable, Dict, Iterator, List, Optional

from app.constants import DEFAULT_COLLECTIONS, DEFAULT_EXCLUDED_APPS
from app.paths import AppPaths
from core.logger import get_logger

logger = get_logger("database")

CURRENT_SCHEMA_VERSION = 2


class Database:
    """Thread-safe SQLite database connection and schema migration manager."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path: Path = Path(db_path) if db_path else AppPaths.get_database_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_database()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Provide a thread-safe transactional database connection."""
        with self._lock:
            conn = self._connect()
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Provide a read connection."""
        with self._lock:
            conn = self._connect()
            try:
                yield conn
            finally:
                conn.close()

    def get_schema_version(self) -> int:
        with self.connection() as conn:
            row = conn.execute("PRAGMA user_version;").fetchone()
            return int(row[0]) if row else 0

    def _init_database(self) -> None:
        with self.transaction() as conn:
            version = conn.execute("PRAGMA user_version;").fetchone()[0]
            if version < 1:
                self._migrate_v1(conn)
                conn.execute("PRAGMA user_version = 1;")
                version = 1
            if version < 2:
                self._migrate_v2(conn)
                conn.execute("PRAGMA user_version = 2;")
                version = 2

    def _migrate_v1(self, conn: sqlite3.Connection) -> None:
        """Initial schema creation for v1."""
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                color TEXT DEFAULT '#A78BFA',
                icon TEXT DEFAULT 'collections',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT NOT NULL,
                text_content TEXT,
                html_content TEXT,
                content_hash TEXT NOT NULL,
                image_path TEXT,
                thumbnail_path TEXT,
                preview TEXT NOT NULL DEFAULT '',
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                last_copied_at TEXT NOT NULL,
                last_used_at TEXT NOT NULL,
                usage_count INTEGER NOT NULL DEFAULT 1,
                is_pinned INTEGER NOT NULL DEFAULT 0,
                is_favorite INTEGER NOT NULL DEFAULT 0,
                collection_id INTEGER REFERENCES collections(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                content TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                tags TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_used_at TEXT,
                is_pinned INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS excluded_apps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                executable_name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE
            );

            CREATE TABLE IF NOT EXISTS clip_tags (
                clip_id INTEGER NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
                tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (clip_id, tag_id)
            );
            """
        )

        # Seed default collections and excluded password manager applications
        now_iso = datetime.now(timezone.utc).isoformat()
        for col in DEFAULT_COLLECTIONS:
            conn.execute(
                """
                INSERT OR IGNORE INTO collections (name, description, color, icon, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (col["name"], col["description"], col["color"], col["icon"], now_iso),
            )

        for exe in DEFAULT_EXCLUDED_APPS:
            conn.execute(
                """
                INSERT OR IGNORE INTO excluded_apps (executable_name, created_at)
                VALUES (?, ?)
                """,
                (exe, now_iso),
            )

    def _migrate_v2(self, conn: sqlite3.Connection) -> None:
        """Add high-performance indexes for 10,000+ clip queries, sorting, and filtering."""
        conn.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_clips_content_hash ON clips(content_hash);
            CREATE INDEX IF NOT EXISTS idx_clips_content_type ON clips(content_type);
            CREATE INDEX IF NOT EXISTS idx_clips_last_copied ON clips(last_copied_at DESC);
            CREATE INDEX IF NOT EXISTS idx_clips_last_used ON clips(last_used_at DESC);
            CREATE INDEX IF NOT EXISTS idx_clips_usage_count ON clips(usage_count DESC);
            CREATE INDEX IF NOT EXISTS idx_clips_pinned ON clips(is_pinned DESC, last_copied_at DESC);
            CREATE INDEX IF NOT EXISTS idx_clips_favorite ON clips(is_favorite DESC, last_copied_at DESC);
            CREATE INDEX IF NOT EXISTS idx_clips_collection ON clips(collection_id);
            CREATE INDEX IF NOT EXISTS idx_snippets_pinned ON snippets(is_pinned DESC, updated_at DESC);
            """
        )
