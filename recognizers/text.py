"""
Fallback Plain Text Recognizer.
Computes character count, word count, line count, and estimated reading time.
"""

import math
from typing import Optional

from app.constants import CONTENT_TYPE_TEXT
from recognizers.base import BaseRecognizer, RecognitionResult


class TextRecognizer(BaseRecognizer):
    """Analyzes ordinary plain text entries."""

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_TEXT

    def recognize(self, content: str) -> Optional[RecognitionResult]:
        if content is None:
            return None

        char_count = len(content)
        words = content.split()
        word_count = len(words)
        lines = content.splitlines() or [content]
        line_count = len(lines)

        # Average reading speed ~200 words per minute
        reading_time_sec = max(1, math.ceil((word_count / 200.0) * 60)) if word_count > 0 else 1

        one_line = " ".join(content.strip().split())
        preview = one_line[:160] + ("..." if len(one_line) > 160 else "")

        return RecognitionResult(
            content_type=CONTENT_TYPE_TEXT,
            confidence=1.0,
            preview=preview or "(Whitespace)",
            metadata={
                "char_count": char_count,
                "word_count": word_count,
                "line_count": line_count,
                "reading_time_sec": reading_time_sec,
            },
        )
