"""
Automated Tests for Smart Recognition Engine:
- HEX colors (#RGB, #RGBA, #RRGGBB, #RRGGBBAA)
- RGB and RGBA colors and conversions to HEX/HSL
- URLs (HTTP/HTTPS) and rejection of invalid links
- Valid JSON formatting/minification and graceful invalid JSON handling
- Code language recognition and Pygments syntax highlighting
- Email recognition
- Plain text metrics (chars, words, lines, reading time)
"""

import unittest

from app.constants import (
    CONTENT_TYPE_CODE,
    CONTENT_TYPE_COLOR,
    CONTENT_TYPE_EMAIL,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_TEXT,
    CONTENT_TYPE_URL,
)
from core.recognition_engine import RecognitionEngine


class TestRecognitionEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = RecognitionEngine()

    def test_hex_color_recognition(self) -> None:
        for hex_input, expected_hex in (
            ("#A78BFA", "#A78BFA"),
            ("#fff", "#FFFFFF"),
            ("#A78BFA80", "#A78BFA"),
            ("  #8b5cf6; ", "#8B5CF6"),
        ):
            res = self.engine.analyze(hex_input)
            self.assertEqual(res.content_type, CONTENT_TYPE_COLOR)
            self.assertEqual(res.metadata["hex"], expected_hex)
            self.assertIn("rgb_str", res.metadata)
            self.assertIn("hsl_str", res.metadata)

        # Arbitrary text containing a hex-like word must NOT be misclassified as a color
        non_color = self.engine.analyze("Please check ticket #123456 in the tracker")
        self.assertEqual(non_color.content_type, CONTENT_TYPE_TEXT)

    def test_rgb_and_rgba_recognition(self) -> None:
        res_rgb = self.engine.analyze("rgb(167, 139, 250)")
        self.assertEqual(res_rgb.content_type, CONTENT_TYPE_COLOR)
        self.assertEqual(res_rgb.metadata["hex"], "#A78BFA")
        self.assertEqual(res_rgb.metadata["rgb"], [167, 139, 250])

        res_rgba = self.engine.analyze("rgba(167, 139, 250, 0.8)")
        self.assertEqual(res_rgba.content_type, CONTENT_TYPE_COLOR)
        self.assertEqual(res_rgba.metadata["alpha"], 0.8)

        # Out-of-range RGB values must not match color
        invalid_rgb = self.engine.analyze("rgb(999, 0, 0)")
        self.assertNotEqual(invalid_rgb.content_type, CONTENT_TYPE_COLOR)

    def test_url_recognition(self) -> None:
        res = self.engine.analyze("https://github.com/kemorovv/SNIPLY?tab=readme")
        self.assertEqual(res.content_type, CONTENT_TYPE_URL)
        self.assertEqual(res.metadata["domain"], "github.com")
        self.assertEqual(res.metadata["scheme"], "https")

        # Non-HTTP protocol must not be recognized as HTTP/HTTPS URL
        ftp_res = self.engine.analyze("ftp://files.example.com/archive.zip")
        self.assertEqual(ftp_res.content_type, CONTENT_TYPE_TEXT)

    def test_json_recognition_valid_and_invalid(self) -> None:
        valid_json = '{"name": "SNIPLY", "items": [1, 2, 3], "active": true}'
        res = self.engine.analyze(valid_json)
        self.assertEqual(res.content_type, CONTENT_TYPE_JSON)
        self.assertTrue(res.metadata["valid"])
        self.assertIn("\n  \"name\": \"SNIPLY\"", res.metadata["pretty"])
        self.assertEqual(
            res.metadata["minified"], '{"name":"SNIPLY","items":[1,2,3],"active":true}'
        )

        # Malformed JSON object with trailing comma / missing closing quote must be handled gracefully
        malformed_json = '{"name": "SNIPLY", "broken": [1, 2, }'
        bad_res = self.engine.analyze(malformed_json)
        self.assertEqual(bad_res.content_type, CONTENT_TYPE_JSON)
        self.assertFalse(bad_res.metadata["valid"])
        self.assertIsNotNone(bad_res.metadata["error"])

    def test_code_recognition_multiple_languages(self) -> None:
        py_code = "def compute_hash(text: str) -> str:\n    import hashlib\n    return hashlib.sha256(text.encode()).hexdigest()"
        py_res = self.engine.analyze(py_code)
        self.assertEqual(py_res.content_type, CONTENT_TYPE_CODE)
        self.assertEqual(py_res.metadata["language"], "Python")
        self.assertIn("<div", py_res.metadata["highlighted_html"])

        sql_code = "SELECT id, content_type, created_at FROM clips WHERE is_pinned = 1 ORDER BY id DESC;"
        sql_res = self.engine.analyze(sql_code)
        self.assertEqual(sql_res.content_type, CONTENT_TYPE_CODE)
        self.assertEqual(sql_res.metadata["language"], "SQL")

    def test_email_recognition(self) -> None:
        res = self.engine.analyze("developer@sniply.app")
        self.assertEqual(res.content_type, CONTENT_TYPE_EMAIL)
        self.assertEqual(res.metadata["domain"], "sniply.app")

    def test_ordinary_text_recognition(self) -> None:
        paragraph = "Meeting at 14:30 in Room 402. Bring the Q4 roadmap notes!"
        res = self.engine.analyze(paragraph)
        self.assertEqual(res.content_type, CONTENT_TYPE_TEXT)
        self.assertEqual(res.metadata["word_count"], 11)
        self.assertEqual(res.metadata["line_count"], 1)


if __name__ == "__main__":
    unittest.main()
