"""
Smart Email Address Recognizer.
Identifies valid standalone email addresses without network calls.
"""

import re
from typing import Optional

from app.constants import CONTENT_TYPE_EMAIL
from recognizers.base import BaseRecognizer, RecognitionResult


class EmailRecognizer(BaseRecognizer):
    """Recognizes standalone email addresses."""

    _EMAIL_RE = re.compile(
        r"^\s*(?:mailto:)?([A-Za-z0-9._%+\-]+@([A-Za-z0-9.\-]+\.[A-Za-z]{2,24}))\s*$",
        re.IGNORECASE,
    )

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_EMAIL

    def recognize(self, content: str) -> Optional[RecognitionResult]:
        if not content or len(content) > 320 or "\n" in content.strip():
            return None

        match = self._EMAIL_RE.match(content)
        if not match:
            return None

        email_addr = match.group(1)
        domain = match.group(2)
        local_part = email_addr.split("@", 1)[0]

        return RecognitionResult(
            content_type=CONTENT_TYPE_EMAIL,
            confidence=1.0,
            preview=email_addr,
            metadata={
                "email": email_addr,
                "local_part": local_part,
                "domain": domain,
            },
        )
