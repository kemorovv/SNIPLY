"""
Clip data model representing a single captured clipboard entry.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

from app.constants import CONTENT_TYPE_TEXT


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Clip:
    id: Optional[int] = None
    content_type: str = CONTENT_TYPE_TEXT
    text_content: Optional[str] = None
    html_content: Optional[str] = None
    content_hash: str = ""
    image_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    preview: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now_iso)
    last_copied_at: str = field(default_factory=_utc_now_iso)
    last_used_at: str = field(default_factory=_utc_now_iso)
    usage_count: int = 1
    is_pinned: bool = False
    is_favorite: bool = False
    collection_id: Optional[int] = None
    collection_name: Optional[str] = None
    collection_color: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_demo: bool = False

    @property
    def metadata_json(self) -> str:
        return json.dumps(self.metadata, ensure_ascii=False)

    @classmethod
    def from_row(cls, row: Any, tags: Optional[List[str]] = None) -> "Clip":
        """Construct a Clip instance from a sqlite3.Row or dictionary."""
        data = dict(row)
        raw_meta = data.get("metadata_json") or "{}"
        try:
            parsed_meta = json.loads(raw_meta) if isinstance(raw_meta, str) else dict(raw_meta)
        except Exception:
            parsed_meta = {}

        return cls(
            id=data.get("id"),
            content_type=data.get("content_type", CONTENT_TYPE_TEXT),
            text_content=data.get("text_content"),
            html_content=data.get("html_content"),
            content_hash=data.get("content_hash", ""),
            image_path=data.get("image_path"),
            thumbnail_path=data.get("thumbnail_path"),
            preview=data.get("preview", ""),
            metadata=parsed_meta,
            created_at=data.get("created_at") or _utc_now_iso(),
            last_copied_at=data.get("last_copied_at") or _utc_now_iso(),
            last_used_at=data.get("last_used_at") or _utc_now_iso(),
            usage_count=int(data.get("usage_count") or 1),
            is_pinned=bool(data.get("is_pinned", 0)),
            is_favorite=bool(data.get("is_favorite", 0)),
            collection_id=data.get("collection_id"),
            collection_name=data.get("collection_name"),
            collection_color=data.get("collection_color"),
            tags=tags if tags is not None else [],
        )
