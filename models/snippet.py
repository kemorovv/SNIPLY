"""
Snippet data model for reusable user templates and saved snippets.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Snippet:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    content: str = ""
    category: str = "General"
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utc_now_iso)
    updated_at: str = field(default_factory=_utc_now_iso)
    last_used_at: Optional[str] = None
    is_pinned: bool = False

    @property
    def tags_str(self) -> str:
        return ", ".join(t.strip() for t in self.tags if t.strip())

    @classmethod
    def from_row(cls, row: Any) -> "Snippet":
        data = dict(row)
        raw_tags = data.get("tags") or ""
        tags_list = [t.strip() for t in raw_tags.split(",") if t.strip()] if isinstance(raw_tags, str) else list(raw_tags)
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            content=data.get("content", ""),
            category=data.get("category") or "General",
            tags=tags_list,
            created_at=data.get("created_at") or _utc_now_iso(),
            updated_at=data.get("updated_at") or _utc_now_iso(),
            last_used_at=data.get("last_used_at"),
            is_pinned=bool(data.get("is_pinned", 0)),
        )
