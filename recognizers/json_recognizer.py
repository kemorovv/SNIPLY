"""
Smart JSON Recognizer.
Detects JSON objects and arrays, validates syntax, provides pretty formatting and minification,
and safely marks malformed JSON-like payloads without crashing.
"""

import json
import re
from typing import Any, Optional

from app.constants import CONTENT_TYPE_JSON
from recognizers.base import BaseRecognizer, RecognitionResult


class JsonRecognizer(BaseRecognizer):
    """Recognizes valid and malformed JSON objects and arrays."""

    _JSON_LIKE_KV_RE = re.compile(r'"[^"\n]{1,64}"\s*:')

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_JSON

    def recognize(self, content: str) -> Optional[RecognitionResult]:
        if not content:
            return None

        stripped = content.strip()
        if len(stripped) < 2:
            return None

        is_object_candidate = stripped.startswith("{") and stripped.endswith("}")
        is_array_candidate = stripped.startswith("[") and stripped.endswith("]")

        if not (is_object_candidate or is_array_candidate):
            return None

        try:
            parsed: Any = json.loads(stripped)
            if not isinstance(parsed, (dict, list)):
                return None

            pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
            minified = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
            root_type = "object" if isinstance(parsed, dict) else "array"
            item_count = len(parsed)

            one_line = " ".join(stripped.split())
            preview = one_line[:140] + ("..." if len(one_line) > 140 else "")

            return RecognitionResult(
                content_type=CONTENT_TYPE_JSON,
                confidence=1.0,
                preview=preview,
                metadata={
                    "valid": True,
                    "root_type": root_type,
                    "item_count": item_count,
                    "pretty": pretty,
                    "minified": minified,
                    "error": None,
                },
            )
        except json.JSONDecodeError as err:
            # Only classify as malformed JSON if it strongly resembles a JSON object/array with quoted keys
            if is_object_candidate and self._JSON_LIKE_KV_RE.search(stripped):
                one_line = " ".join(stripped.split())
                preview = one_line[:140] + ("..." if len(one_line) > 140 else "")
                return RecognitionResult(
                    content_type=CONTENT_TYPE_JSON,
                    confidence=0.75,
                    preview=preview,
                    metadata={
                        "valid": False,
                        "root_type": "object",
                        "item_count": 0,
                        "pretty": content,
                        "minified": content,
                        "error": f"Line {err.lineno}, Col {err.colno}: {err.msg}",
                    },
                )
            return None
