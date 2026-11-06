"""
Extensible Smart Recognition Engine for SNIPLY.
Evaluates copied text through an ordered pipeline of modular recognizers.
"""

from typing import List

from recognizers.base import BaseRecognizer, RecognitionResult
from recognizers.code import CodeRecognizer
from recognizers.color import ColorRecognizer
from recognizers.email import EmailRecognizer
from recognizers.json_recognizer import JsonRecognizer
from recognizers.text import TextRecognizer
from recognizers.url import UrlRecognizer


class RecognitionEngine:
    """Coordinates content recognizers and allows custom recognizers to be registered dynamically."""

    def __init__(self) -> None:
        self._recognizers: List[BaseRecognizer] = [
            ColorRecognizer(),
            UrlRecognizer(),
            EmailRecognizer(),
            JsonRecognizer(),
            CodeRecognizer(),
        ]
        self._fallback_recognizer = TextRecognizer()

    def register_recognizer(self, recognizer: BaseRecognizer, priority_index: int = 0) -> None:
        """Register an additional recognizer without modifying the clipboard engine."""
        self._recognizers.insert(max(0, priority_index), recognizer)

    def analyze(self, text: str) -> RecognitionResult:
        """Run text through registered recognizers and return the highest-confidence match."""
        for recognizer in self._recognizers:
            try:
                result = recognizer.recognize(text)
                if result is not None:
                    return result
            except Exception:
                continue

        fallback = self._fallback_recognizer.recognize(text)
        assert fallback is not None
        return fallback
