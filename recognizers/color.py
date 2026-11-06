"""
Smart Color Recognizer for HEX (#RGB, #RGBA, #RRGGBB, #RRGGBBAA) and RGB/RGBA strings.
Computes accurate HEX, RGB, HSL, and Alpha conversions.
"""

import colorsys
import re
from typing import Optional, Tuple

from app.constants import CONTENT_TYPE_COLOR
from recognizers.base import BaseRecognizer, RecognitionResult


class ColorRecognizer(BaseRecognizer):
    """Recognizes standalone HEX and RGB/RGBA color strings."""

    # Strict whole-string matching (allowing leading/trailing whitespace and optional trailing semicolon)
    _HEX_RE = re.compile(r"^\s*#([0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\s*;?\s*$")
    _RGB_RE = re.compile(
        r"^\s*rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(?:\s*,\s*([01](?:\.\d+)?|0?\.\d+|\d{1,3}%))?\s*\)\s*;?\s*$",
        re.IGNORECASE,
    )

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_COLOR

    def recognize(self, content: str) -> Optional[RecognitionResult]:
        if not content or len(content) > 64:
            return None

        hex_match = self._HEX_RE.match(content)
        if hex_match:
            raw_hex = hex_match.group(1)
            r, g, b, alpha = self._parse_hex(raw_hex)
            return self._build_result(r, g, b, alpha, source_format="hex")

        rgb_match = self._RGB_RE.match(content)
        if rgb_match:
            r = int(rgb_match.group(1))
            g = int(rgb_match.group(2))
            b = int(rgb_match.group(3))
            if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                return None

            alpha_str = rgb_match.group(4)
            alpha = 1.0
            if alpha_str is not None:
                if alpha_str.endswith("%"):
                    pct = float(alpha_str[:-1])
                    if not (0.0 <= pct <= 100.0):
                        return None
                    alpha = round(pct / 100.0, 2)
                else:
                    alpha = float(alpha_str)
                    if not (0.0 <= alpha <= 1.0):
                        return None
                    alpha = round(alpha, 2)

            fmt = "rgba" if alpha_str is not None else "rgb"
            return self._build_result(r, g, b, alpha, source_format=fmt)

        return None

    @staticmethod
    def _parse_hex(hex_digits: str) -> Tuple[int, int, int, float]:
        length = len(hex_digits)
        if length == 3:
            r = int(hex_digits[0] * 2, 16)
            g = int(hex_digits[1] * 2, 16)
            b = int(hex_digits[2] * 2, 16)
            return r, g, b, 1.0
        if length == 4:
            r = int(hex_digits[0] * 2, 16)
            g = int(hex_digits[1] * 2, 16)
            b = int(hex_digits[2] * 2, 16)
            a = round(int(hex_digits[3] * 2, 16) / 255.0, 2)
            return r, g, b, a
        if length == 6:
            r = int(hex_digits[0:2], 16)
            g = int(hex_digits[2:4], 16)
            b = int(hex_digits[4:6], 16)
            return r, g, b, 1.0
        # length == 8
        r = int(hex_digits[0:2], 16)
        g = int(hex_digits[2:4], 16)
        b = int(hex_digits[4:6], 16)
        a = round(int(hex_digits[6:8], 16) / 255.0, 2)
        return r, g, b, a

    @staticmethod
    def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[int, int, int]:
        h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        return round(h * 360) % 360, round(s * 100), round(l * 100)

    def _build_result(
        self, r: int, g: int, b: int, alpha: float, source_format: str
    ) -> RecognitionResult:
        hex_code = f"#{r:02X}{g:02X}{b:02X}"
        hex_with_alpha = (
            f"#{r:02X}{g:02X}{b:02X}{round(alpha * 255):02X}" if alpha < 1.0 else hex_code
        )
        h, s, l = self.rgb_to_hsl(r, g, b)

        if alpha < 1.0:
            rgb_str = f"rgba({r}, {g}, {b}, {alpha})"
            hsl_str = f"hsla({h}, {s}%, {l}%, {alpha})"
        else:
            rgb_str = f"rgb({r}, {g}, {b})"
            hsl_str = f"hsl({h}, {s}%, {l}%)"

        return RecognitionResult(
            content_type=CONTENT_TYPE_COLOR,
            confidence=1.0,
            preview=f"{hex_with_alpha}  •  {rgb_str}",
            metadata={
                "format": source_format,
                "hex": hex_code,
                "hex_full": hex_with_alpha,
                "rgb": [r, g, b],
                "rgb_str": rgb_str,
                "hsl": [h, s, l],
                "hsl_str": hsl_str,
                "alpha": alpha,
            },
        )
