"""
Image Storage, Thumbnail Generation & LRU Cache Manager for SNIPLY.
Handles saving full-resolution images, generating compact thumbnails, enforcing size limits,
and avoiding duplicate image files on disk.
"""

from collections import OrderedDict
from datetime import datetime, timezone
import io
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import uuid
from PIL import Image

from app.paths import AppPaths
from core.duplicate_detector import DuplicateDetector
from core.logger import get_logger

logger = get_logger("image_manager")


class ImageTooLargeError(ValueError):
    """Raised when a copied image exceeds the user's configured maximum size in MB."""

    def __init__(self, actual_mb: float, max_mb: int) -> None:
        super().__init__(f"Image size {actual_mb:.2f} MB exceeds limit of {max_mb} MB")
        self.actual_mb = actual_mb
        self.max_mb = max_mb


class ImageManager:
    """Manages clipboard image persistence, thumbnail generation, and memory-bounded caching."""

    THUMBNAIL_MAX_SIZE = (360, 240)
    CACHE_CAPACITY = 128

    def __init__(self, storage_dir: Optional[Path] = None, thumbnails_dir: Optional[Path] = None) -> None:
        self._storage_dir = storage_dir
        self._thumbnails_dir = thumbnails_dir
        self._thumb_cache: "OrderedDict[str, bytes]" = OrderedDict()

    @property
    def storage_dir(self) -> Path:
        return self._storage_dir or AppPaths.get_images_storage_dir()

    @property
    def thumbnails_dir(self) -> Path:
        return self._thumbnails_dir or AppPaths.get_thumbnails_dir()

    def process_and_save_image(
        self,
        image: Image.Image,
        max_size_mb: int = 15,
        source_format: str = "PNG",
    ) -> Tuple[str, Path, Path, Dict[str, Any]]:
        """
        Validate size limit, compute content hash, save PNG image & thumbnail (or reuse if already stored),
        and return (content_hash, image_path, thumbnail_path, metadata_dict).
        """
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

        # Serialize to PNG buffer to measure exact stored size
        buf = io.BytesIO()
        fmt = (source_format or image.format or "PNG").upper()
        if fmt not in ("PNG", "JPEG", "WEBP", "BMP"):
            fmt = "PNG"
        save_img = image.convert("RGB") if fmt == "JPEG" else image.convert("RGBA")
        save_img.save(buf, format="PNG")
        raw_bytes = buf.getvalue()
        file_size_bytes = len(raw_bytes)
        actual_mb = file_size_bytes / (1024.0 * 1024.0)

        if max_size_mb > 0 and actual_mb > float(max_size_mb):
            raise ImageTooLargeError(actual_mb=actual_mb, max_mb=max_size_mb)

        content_hash = DuplicateDetector.compute_image_hash(image)
        file_stem = f"clip_{content_hash}"
        image_path = self.storage_dir / f"{file_stem}.png"
        thumb_path = self.thumbnails_dir / f"{file_stem}_thumb.png"

        if not image_path.exists():
            image_path.write_bytes(raw_bytes)

        if not thumb_path.exists():
            thumb = save_img.copy()
            thumb.thumbnail(self.THUMBNAIL_MAX_SIZE, Image.Resampling.LANCZOS)
            tbuf = io.BytesIO()
            thumb.save(tbuf, format="PNG", optimize=True)
            thumb_bytes = tbuf.getvalue()
            thumb_path.write_bytes(thumb_bytes)
            self._put_cache(str(thumb_path), thumb_bytes)

        width, height = image.size
        now_iso = datetime.now(timezone.utc).isoformat()
        metadata: Dict[str, Any] = {
            "width": width,
            "height": height,
            "format": fmt,
            "file_size": file_size_bytes,
            "created_at": now_iso,
            "uuid": str(uuid.uuid5(uuid.NAMESPACE_OID, content_hash)),
        }
        return content_hash, image_path, thumb_path, metadata

    def get_thumbnail_bytes(self, thumb_path_str: str) -> Optional[bytes]:
        """Return cached thumbnail bytes without reloading full-resolution images."""
        if not thumb_path_str:
            return None
        if thumb_path_str in self._thumb_cache:
            self._thumb_cache.move_to_end(thumb_path_str)
            return self._thumb_cache[thumb_path_str]

        p = Path(thumb_path_str)
        if not p.exists():
            return None
        try:
            data = p.read_bytes()
            self._put_cache(thumb_path_str, data)
            return data
        except OSError:
            return None

    def _put_cache(self, key: str, data: bytes) -> None:
        self._thumb_cache[key] = data
        self._thumb_cache.move_to_end(key)
        while len(self._thumb_cache) > self.CACHE_CAPACITY:
            self._thumb_cache.popitem(last=False)
