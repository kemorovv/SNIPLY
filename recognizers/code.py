"""
Smart Code Recognizer using deterministic language signatures and Pygments syntax highlighting.
Supports Python, JavaScript, TypeScript, HTML, CSS, SQL, Bash, PowerShell, Java, and C++.
"""

import re
from typing import List, Optional, Tuple

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, TextLexer

from app.constants import CONTENT_TYPE_CODE
from recognizers.base import BaseRecognizer, RecognitionResult


class CodeRecognizer(BaseRecognizer):
    """Detects programming languages and generates Pygments syntax-highlighted HTML previews."""

    # Ordered rules: (Display Name, Pygments Lexer Name, List of regex patterns, min_matches)
    _LANGUAGE_RULES: List[Tuple[str, str, List[re.Pattern], int]] = [
        (
            "HTML",
            "html",
            [
                re.compile(r"<!DOCTYPE\s+html>", re.IGNORECASE),
                re.compile(r"<(html|head|body|div|section|script|style|span|a|p|table|form|input)\b[^>]*>", re.IGNORECASE),
                re.compile(r"</(html|head|body|div|section|script|style|span|a|p|table|form)>", re.IGNORECASE),
            ],
            1,
        ),
        (
            "SQL",
            "sql",
            [
                re.compile(
                    r"^\s*(SELECT\s+.+\s+FROM\s+|INSERT\s+INTO\s+\w+|UPDATE\s+\w+\s+SET\s+|DELETE\s+FROM\s+\w+|CREATE\s+(TABLE|INDEX|VIEW)\s+)",
                    re.IGNORECASE | re.DOTALL,
                ),
            ],
            1,
        ),
        (
            "PowerShell",
            "powershell",
            [
                re.compile(r"\b(Get|Set|New|Remove|Invoke|Write|Start|Stop)-[A-Z][A-Za-z0-9]+\b"),
                re.compile(r"\$PSVersionTable|\$ErrorActionPreference|\bparam\s*\("),
            ],
            1,
        ),
        (
            "Bash",
            "bash",
            [
                re.compile(r"^#!\s*/bin/(ba)?sh", re.MULTILINE),
                re.compile(r"^\s*(sudo\s+|apt-get\s+|systemctl\s+|chmod\s+\+x|export\s+[A-Z0-9_]+=)", re.MULTILINE),
                re.compile(r"\bif\s+\[\s+.+\s+\];\s*then\b"),
            ],
            1,
        ),
        (
            "Python",
            "python",
            [
                re.compile(r"^\s*(def|class)\s+[A-Za-z_][A-Za-z0-9_]*\s*[\(:]", re.MULTILINE),
                re.compile(r"^\s*(from\s+[A-Za-z0-9_.]+\s+import\s+|import\s+[A-Za-z0-9_]+)", re.MULTILINE),
                re.compile(r"if\s+__name__\s*==\s*['\"]__main__['\"]\s*:"),
                re.compile(r"@dataclass|@property|@staticmethod|@classmethod"),
            ],
            1,
        ),
        (
            "TypeScript",
            "typescript",
            [
                re.compile(r"\b(interface|type)\s+[A-Z][A-Za-z0-9_]*\s*[={]"),
                re.compile(r"\b(const|let|function)\s+[A-Za-z_$][A-Za-z0-9_$]*\s*:\s*(string|number|boolean|any|Record|Promise)\b"),
                re.compile(r"\bexport\s+(interface|type|enum)\s+"),
            ],
            1,
        ),
        (
            "JavaScript",
            "javascript",
            [
                re.compile(r"\b(const|let|var)\s+[A-Za-z_$][A-Za-z0-9_$]*\s*=\s*"),
                re.compile(r"\b(function\s+[A-Za-z_$]|console\.log\s*\(|document\.querySelector|window\.addEventListener)"),
                re.compile(r"=>\s*\{|\bexport\s+(default\s+)?(function|class|const)\b"),
            ],
            1,
        ),
        (
            "CSS",
            "css",
            [
                re.compile(r"([.#]?[a-zA-Z0-9_\-]+\s*\{\s*[a-z\-]+\s*:\s*[^;{}]+;\s*\})", re.DOTALL),
                re.compile(r"@media\s*\([^)]+\)\s*\{|:root\s*\{"),
            ],
            1,
        ),
        (
            "C++",
            "cpp",
            [
                re.compile(r"^\s*#include\s*[<\"][A-Za-z0-9_./]+[>\"]", re.MULTILINE),
                re.compile(r"\bstd::(cout|cin|vector|string|map|shared_ptr|unique_ptr)\b"),
                re.compile(r"\bint\s+main\s*\([^)]*\)\s*\{"),
            ],
            1,
        ),
        (
            "Java",
            "java",
            [
                re.compile(r"\b(public|private|protected)\s+(static\s+)?(class|void|int|String)\s+[A-Za-z0-9_]+"),
                re.compile(r"\bSystem\.out\.println\s*\(|\bpublic\s+static\s+void\s+main\s*\(\s*String"),
            ],
            1,
        ),
    ]

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_CODE

    def recognize(self, content: str) -> Optional[RecognitionResult]:
        if not content or len(content.strip()) < 8:
            return None

        detected_lang: Optional[str] = None
        detected_lexer: Optional[str] = None

        for lang_name, lexer_name, patterns, min_matches in self._LANGUAGE_RULES:
            matches = sum(1 for pat in patterns if pat.search(content))
            if matches >= min_matches:
                detected_lang = lang_name
                detected_lexer = lexer_name
                break

        if not detected_lang or not detected_lexer:
            return None

        lines = content.splitlines()
        first_non_empty = next((ln.strip() for ln in lines if ln.strip()), content.strip())
        preview = f"[{detected_lang}] {first_non_empty[:120]}"

        highlighted_html = self.highlight_code(content, detected_lexer)

        return RecognitionResult(
            content_type=CONTENT_TYPE_CODE,
            confidence=0.92,
            preview=preview,
            metadata={
                "language": detected_lang,
                "lexer": detected_lexer,
                "line_count": len(lines),
                "char_count": len(content),
                "highlighted_html": highlighted_html,
            },
        )

    @staticmethod
    def highlight_code(code: str, lexer_name: str) -> str:
        """Render syntax-highlighted inline-styled HTML using Pygments."""
        try:
            lexer = get_lexer_by_name(lexer_name, stripall=False)
        except Exception:
            lexer = TextLexer()

        formatter = HtmlFormatter(
            noclasses=True,
            style="monokai",
            nowrap=False,
            prestyles="margin: 0; padding: 12px; background-color: #17181C; color: #F4F2FA; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 12px; border-radius: 8px; overflow-x: auto;",
        )
        try:
            return highlight(code[:12000], lexer, formatter)
        except Exception:
            return f"<pre>{code[:4000]}</pre>"
