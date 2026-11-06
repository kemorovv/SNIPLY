"""
Duplicate Detection Engine for SNIPLY.
Computes stable SHA-256 content hashes for text and perceptual + exact byte verification hashes for images.
"""

import hashlib
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image


class DuplicateDetector:
    """Computes stable hashes and verifies exact equality for text and image clipboard items."""

    @staticmethod
    def compute_text_hash(text: str) -> str:
        """
        Compute a deterministic SHA-256 hash of exact text content (preserving whitespace and Unicode).
        """
        if text is None:
            return ""
        return hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest()

    @staticmethod
    def compute_image_hash(image: Image.Image) -> str:
        """
        Compute a combined perceptual average hash (aHash) + exact pixel SHA-256 digest
        so visually similar but non-identical images are never falsely merged.
        """
        rgba = image.convert("RGBA")
        w, h = rgba.size

        # 8x8 grayscale perceptual average hash prefix
        small = rgba.convert("L").resize((8, 8), Image.Resampling.BILINEAR)
        pixels = np.asarray(small, dtype=np.float32)
        avg = pixels.mean()
        bits = (pixels >= avg).flatten()
        ahash_int = 0
        for bit in bits:
            ahash_int = (ahash_int << 1) | int(bit)
        ahash_hex = f"{ahash_int:016x}"

        # Exact pixel SHA-256 digest for strict equality verification
        pixel_digest = hashlib.sha256(rgba.tobytes()).hexdigest()[:32]
        return f"img_{w}x{h}_{ahash_hex}_{pixel_digest}"

    @staticmethod
    def are_images_identical(img_a: Image.Image, img_b: Image.Image) -> bool:
        """Verify exact pixel-by-pixel equality between two Pillow images."""
        if img_a.size != img_b.size:
            return False
        return img_a.convert("RGBA").tobytes() == img_b.convert("RGBA").tobytes()

    @staticmethod
    def are_image_files_identical(path_a: Optional[Path], path_b: Optional[Path]) -> bool:
        if not path_a or not path_b or not path_a.exists() or not path_b.exists():
            return False
        try:
            with Image.open(path_a) as ia, Image.open(path_b) as ib:
                return DuplicateDetector.are_images_identical(ia, ib)
        except Exception:
            return False
