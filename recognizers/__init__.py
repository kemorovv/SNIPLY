"""SNIPLY Smart Content Recognizers Package."""

from recognizers.base import BaseRecognizer, RecognitionResult
from recognizers.code import CodeRecognizer
from recognizers.color import ColorRecognizer
from recognizers.email import EmailRecognizer
from recognizers.json_recognizer import JsonRecognizer
from recognizers.text import TextRecognizer
from recognizers.url import UrlRecognizer

__all__ = [
    "BaseRecognizer",
    "RecognitionResult",
    "ColorRecognizer",
    "UrlRecognizer",
    "JsonRecognizer",
    "CodeRecognizer",
    "EmailRecognizer",
    "TextRecognizer",
]
