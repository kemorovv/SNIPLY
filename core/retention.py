"""
Retention & Automatic History Cleanup Engine for SNIPLY.
Enforces configurable age limits (1, 7, 30, 90 days, or Never) and maximum entry counts
while strictly protecting pinned and favorite entries.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

from core.logger import get_logger
from core.storage import StorageRepository

logger = get_logger("retention")


class RetentionManager:
    """Executes safe retention cleanup without deleting pinned or favorite items."""

    def __init__(self, storage: StorageRepository) -> None:
        self.storage = storage

    def run_cleanup(
        self,
        retention_days: int = 30,
        max_history_size: int = 2500,
        protect_pinned: bool = True,
        protect_favorites: bool = True,
    ) -> Dict[str, int]:
        """
        Remove expired and excess history entries according to retention settings.
        Returns {'expired_deleted': int, 'overflow_deleted': int}.
        """
        expired_deleted = 0
        overflow_deleted = 0

        protection_clauses = []
        if protect_pinned:
            protection_clauses.append("is_pinned = 0")
        if protect_favorites:
            protection_clauses.append("is_favorite = 0")
        protect_sql = " AND ".join(protection_clauses) if protection_clauses else "1=1"

        with self.storage.db.transaction() as conn:
            # 1. Age-based cleanup (if retention_days > 0)
            if retention_days > 0:
                cutoff_dt = datetime.now(timezone.utc) - timedelta(days=retention_days)
                cutoff_iso = cutoff_dt.isoformat()
                old_rows = conn.execute(
                    f"""
                    SELECT id, image_path, thumbnail_path
                    FROM clips
                    WHERE {protect_sql} AND last_copied_at < ?
                    """,
                    (cutoff_iso,),
                ).fetchall()

                if old_rows:
                    for r in old_rows:
                        self._delete_file_quietly(r["image_path"])
                        self._delete_file_quietly(r["thumbnail_path"])
                    ids = [int(r["id"]) for r in old_rows]
                    placeholders = ",".join("?" for _ in ids)
                    cursor = conn.execute(
                        f"DELETE FROM clips WHERE id IN ({placeholders})", tuple(ids)
                    )
                    expired_deleted = cursor.rowcount

            # 2. Maximum history count cleanup
            if max_history_size > 0:
                total_unprotected = conn.execute(
                    f"SELECT COUNT(*) FROM clips WHERE {protect_sql}"
                ).fetchone()[0]

                if total_unprotected > max_history_size:
                    excess_count = int(total_unprotected) - int(max_history_size)
                    excess_rows = conn.execute(
                        f"""
                        SELECT id, image_path, thumbnail_path
                        FROM clips
                        WHERE {protect_sql}
                        ORDER BY last_copied_at ASC, id ASC
                        LIMIT ?
                        """,
                        (excess_count,),
                    ).fetchall()

                    if excess_rows:
                        for r in excess_rows:
                            self._delete_file_quietly(r["image_path"])
                            self._delete_file_quietly(r["thumbnail_path"])
                        ids = [int(r["id"]) for r in excess_rows]
                        placeholders = ",".join("?" for _ in ids)
                        cursor = conn.execute(
                            f"DELETE FROM clips WHERE id IN ({placeholders})", tuple(ids)
                        )
                        overflow_deleted = cursor.rowcount

        if expired_deleted or overflow_deleted:
            logger.info(
                f"Retention cleanup finished: expired={expired_deleted}, overflow={overflow_deleted}"
            )
        return {
            "expired_deleted": expired_deleted,
            "overflow_deleted": overflow_deleted,
        }

    @staticmethod
    def _delete_file_quietly(path_str: str | None) -> None:
        if not path_str:
            return
        try:
            p = Path(path_str)
            if p.exists() and p.is_file():
                p.unlink()
        except OSError:
            pass
