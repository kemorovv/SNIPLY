"""
Smart URL Recognizer for HTTP and HTTPS links.
Extracts domain, scheme, path, and query parameters completely offline without network requests.
"""

import re
from typing import Optional
from urllib.parse import urlparse

from app.constants import CONTENT_TYPE_URL
from recognizers.base import BaseRecognizer, RecognitionResult


class UrlRecognizer(BaseRecognizer):
    """Recognizes standalone valid HTTP and HTTPS URLs."""

    _URL_RE = re.compile(
        r"^\s*(https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+)\s*$",
        re.IGNORECASE,
    )

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_URL

    def recognize(self, content: str) -> Optional[RecognitionResult]:
        if not content or len(content) > 4096 or "\n" in content.strip():
            return None

        match = self._URL_RE.match(content)
        if not match:
            return None

        clean_url = match.group(1)
        try:
            parsed = urlparse(clean_url)
        except ValueError:
            return None

        if parsed.scheme.lower() not in ("http", "https"):
            return None

        hostname = parsed.hostname or ""
        if not hostname or ("." not in hostname and hostname.lower() != "localhost"):
            return None

        return RecognitionResult(
            content_type=CONTENT_TYPE_URL,
            confidence=1.0,
            preview=clean_url[:140],
            metadata={
                "url": clean_url,
                "domain": hostname,
                "scheme": parsed.scheme.lower(),
                "path": parsed.path or "/",
                "query": parsed.query or "",
            },
        )
