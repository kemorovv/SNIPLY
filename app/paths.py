"""
Application path management following Windows %LOCALAPPDATA% conventions
and supporting PyInstaller frozen builds as well as custom test directories.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from app.constants import APP_NAME


class AppPaths:
    """Resolves application resource and user-data paths across source and frozen environments."""

    _custom_data_dir: Optional[Path] = None

    @classmethod
    def set_custom_data_dir(cls, path: Optional[Path]) -> None:
        """Override the application data directory (used for isolated testing)."""
        cls._custom_data_dir = Path(path) if path else None
        if cls._custom_data_dir:
            cls.ensure_data_dirs()

    @classmethod
    def get_bundle_root(cls) -> Path:
        """Return root directory containing bundled read-only application assets."""
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(getattr(sys, "_MEIPASS"))
        return Path(__file__).resolve().parent.parent

    @classmethod
    def get_resources_dir(cls) -> Path:
        return cls.get_bundle_root() / "resources"

    @classmethod
    def get_icons_dir(cls) -> Path:
        return cls.get_resources_dir() / "icons"

    @classmethod
    def get_logo_dir(cls) -> Path:
        return cls.get_resources_dir() / "logo"

    @classmethod
    def get_styles_dir(cls) -> Path:
        return cls.get_resources_dir() / "styles"

    @classmethod
    def get_translations_dir(cls) -> Path:
        return cls.get_resources_dir() / "translations"

    @classmethod
    def get_data_dir(cls) -> Path:
        """
        Return the persistent user data directory.
        On Windows: %LOCALAPPDATA%\\SNIPLY
        On Linux/macOS fallback: ~/.local/share/SNIPLY
        """
        if cls._custom_data_dir is not None:
            return cls._custom_data_dir

        env_override = os.environ.get("SNIPLY_DATA_DIR")
        if env_override:
            return Path(env_override)

        if sys.platform == "win32":
            local_app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
            if local_app_data:
                return Path(local_app_data) / APP_NAME
            return Path.home() / "AppData" / "Local" / APP_NAME
        else:
            xdg_data = os.environ.get("XDG_DATA_HOME")
            if xdg_data:
                return Path(xdg_data) / APP_NAME
            return Path.home() / ".local" / "share" / APP_NAME

    @classmethod
    def get_database_path(cls) -> Path:
        cls.ensure_data_dirs()
        return cls.get_data_dir() / "sniply.db"

    @classmethod
    def get_images_storage_dir(cls) -> Path:
        path = cls.get_data_dir() / "images"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_thumbnails_dir(cls) -> Path:
        path = cls.get_data_dir() / "thumbnails"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_logs_dir(cls) -> Path:
        path = cls.get_data_dir() / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_backups_dir(cls) -> Path:
        path = cls.get_data_dir() / "backups"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def ensure_data_dirs(cls) -> None:
        base = cls.get_data_dir()
        base.mkdir(parents=True, exist_ok=True)
        (base / "images").mkdir(parents=True, exist_ok=True)
        (base / "thumbnails").mkdir(parents=True, exist_ok=True)
        (base / "logs").mkdir(parents=True, exist_ok=True)
        (base / "backups").mkdir(parents=True, exist_ok=True)
