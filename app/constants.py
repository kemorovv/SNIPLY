"""
Application-wide constants, design tokens, and default configurations for SNIPLY.
"""

from typing import Dict, List

APP_NAME = "SNIPLY"
APP_TAGLINE = "Your clipboard. Reimagined."
APP_VERSION = "1.0.0"
APP_AUTHOR = "SNIPLY Contributors"
APP_LICENSE = "MIT"
APP_GITHUB_URL = "https://github.com/kemorovv/SNIPLY"
SINGLE_INSTANCE_KEY = "SNIPLY_Desktop_Clipboard_Manager_SingleInstance_v1"

# Window Dimensions
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 820
MIN_WINDOW_WIDTH = 950
MIN_WINDOW_HEIGHT = 650

QUICK_PASTE_WIDTH = 600
QUICK_PASTE_HEIGHT = 480

SIDEBAR_EXPANDED_WIDTH = 232
SIDEBAR_COLLAPSED_WIDTH = 68
INSPECTOR_DEFAULT_WIDTH = 340

# Design System Color Palette (Dark Theme Default)
COLORS: Dict[str, str] = {
    "bg_main": "#17181C",
    "bg_secondary": "#1C1D23",
    "bg_card": "#22232A",
    "bg_elevated": "#282932",
    "border_primary": "#30313B",
    "border_subtle": "#292A32",
    "text_primary": "#F4F2FA",
    "text_secondary": "#A3A1AE",
    "text_muted": "#72717E",
    "accent_primary": "#A78BFA",
    "accent_secondary": "#8B5CF6",
    "accent_hover": "#B99AFF",
    "success": "#6DD6A5",
    "warning": "#E9BB70",
    "error": "#F07886",
}

LIGHT_COLORS: Dict[str, str] = {
    "bg_main": "#F7F7FA",
    "bg_secondary": "#EFEFF5",
    "bg_card": "#FFFFFF",
    "bg_elevated": "#E6E6F0",
    "border_primary": "#D4D4E0",
    "border_subtle": "#E2E2EC",
    "text_primary": "#17181C",
    "text_secondary": "#525160",
    "text_muted": "#7D7C8C",
    "accent_primary": "#7C3AED",
    "accent_secondary": "#6D28D9",
    "accent_hover": "#8B5CF6",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
}

# Supported Languages
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "ru": "Русский",
}

# Content Types
CONTENT_TYPE_TEXT = "text"
CONTENT_TYPE_COLOR = "color"
CONTENT_TYPE_URL = "url"
CONTENT_TYPE_JSON = "json"
CONTENT_TYPE_CODE = "code"
CONTENT_TYPE_EMAIL = "email"
CONTENT_TYPE_IMAGE = "image"

ALL_CONTENT_TYPES: List[str] = [
    CONTENT_TYPE_TEXT,
    CONTENT_TYPE_COLOR,
    CONTENT_TYPE_URL,
    CONTENT_TYPE_JSON,
    CONTENT_TYPE_CODE,
    CONTENT_TYPE_EMAIL,
    CONTENT_TYPE_IMAGE,
]

# Default Excluded Password Managers & Sensitive Utilities
DEFAULT_EXCLUDED_APPS: List[str] = [
    "1Password.exe",
    "KeePass.exe",
    "KeePassXC.exe",
    "Bitwarden.exe",
    "Dashlane.exe",
    "NordPass.exe",
    "LastPass.exe",
    "mstsc.exe",
]

# Default Collections
DEFAULT_COLLECTIONS = [
    {"name": "Design", "description": "Colors, UI tokens, and visual references", "color": "#A78BFA", "icon": "colors"},
    {"name": "Development", "description": "Code fragments, JSON payloads, and commands", "color": "#6DD6A5", "icon": "snippets"},
    {"name": "Work", "description": "Important links, emails, and meeting notes", "color": "#E9BB70", "icon": "collections"},
    {"name": "Personal", "description": "Saved everyday notes and personal items", "color": "#F07886", "icon": "favorites"},
    {"name": "Prompts", "description": "AI prompts and reusable instructions", "color": "#8B5CF6", "icon": "zap"},
]

# Demo Mode Showcase Entries (Strictly isolated from user clipboard history)
DEMO_ENTRIES = [
    {
        "content_type": CONTENT_TYPE_COLOR,
        "text_content": "#A78BFA",
        "preview": "#A78BFA — Primary Purple Accent",
        "metadata": {
            "format": "hex",
            "hex": "#A78BFA",
            "rgb": [167, 139, 250],
            "rgb_str": "rgb(167, 139, 250)",
            "hsl": [255, 92, 76],
            "hsl_str": "hsl(255, 92%, 76%)",
            "alpha": 1.0,
        },
    },
    {
        "content_type": CONTENT_TYPE_URL,
        "text_content": "https://github.com/",
        "preview": "https://github.com/",
        "metadata": {
            "domain": "github.com",
            "scheme": "https",
            "path": "/",
            "url": "https://github.com/",
        },
    },
    {
        "content_type": CONTENT_TYPE_JSON,
        "text_content": '{\n  "product": "SNIPLY",\n  "version": "1.0.0",\n  "local_first": true,\n  "languages": ["en", "ru"]\n}',
        "preview": '{ "product": "SNIPLY", "version": "1.0.0", "local_first": true, ... }',
        "metadata": {
            "valid": True,
            "root_type": "object",
            "key_count": 4,
            "minified": '{"product":"SNIPLY","version":"1.0.0","local_first":true,"languages":["en","ru"]}',
        },
    },
    {
        "content_type": CONTENT_TYPE_CODE,
        "text_content": "def recognize_clip(content: str) -> dict:\n    \"\"\"Analyze copied text and return structured metadata.\"\"\"\n    engine = RecognitionEngine()\n    return engine.analyze(content)",
        "preview": "def recognize_clip(content: str) -> dict: ...",
        "metadata": {
            "language": "Python",
            "lexer": "python",
            "line_count": 4,
        },
    },
    {
        "content_type": CONTENT_TYPE_TEXT,
        "text_content": "SNIPLY automatically organizes everything you copy — colors, links, JSON payloads, code snippets, and images — right on your machine with zero cloud uploads.",
        "preview": "SNIPLY automatically organizes everything you copy — colors, links, JSON payloads...",
        "metadata": {
            "char_count": 159,
            "word_count": 23,
            "line_count": 1,
            "reading_time_sec": 7,
        },
    },
]
