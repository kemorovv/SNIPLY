"""
Base recognizer interface and structured RecognitionResult dataclass.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class RecognitionResult:
    content_type: str
    confidence: float
    preview: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.content_type,
            "confidence": self.confidence,
            "preview": self.preview,
            "metadata": self.metadata,
        }


class BaseRecognizer(ABC):
    """Abstract base class for independent clipboard content recognizers."""

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Identifier for the recognized content type."""

    @abstractmethod
    def recognize(self, content: str) -> Optional[RecognitionResult]:
        """
        Inspect text content and return a RecognitionResult if matched,
        or None if the content does not match this recognizer's rules.
        """
