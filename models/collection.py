"""
Collection data model for user-created clipboard collections.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Collection:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    color: str = "#A78BFA"
    icon: str = "collections"
    created_at: str = field(default_factory=_utc_now_iso)
    clip_count: int = 0

    @classmethod
    def from_row(cls, row: Any) -> "Collection":
        data = dict(row)
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            color=data.get("color", "#A78BFA"),
            icon=data.get("icon", "collections"),
            created_at=data.get("created_at") or _utc_now_iso(),
            clip_count=int(data.get("clip_count") or 0),
        )
