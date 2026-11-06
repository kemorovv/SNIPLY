"""
Application settings model with typed defaults and serialization.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class AppSettings:
    # Onboarding & Consent
    onboarding_completed: bool = False
    monitoring_consent_given: bool = False
    language_manually_selected: bool = False

    # General
    language: str = "en"
    launch_at_startup: bool = False
    start_minimized: bool = False
    minimize_to_tray: bool = True
    close_to_tray: bool = True
    auto_start_monitoring: bool = True
    auto_paste_on_quick_select: bool = False

    # Appearance
    theme: str = "dark"  # 'dark' | 'light'
    accent_color: str = "#A78BFA"
    density: str = "comfortable"  # 'comfortable' | 'compact'
    reduced_motion: bool = False
    sidebar_collapsed: bool = False
    inspector_visible: bool = True
    view_mode: str = "list"  # 'list' | 'grid'

    # Clipboard & Privacy
    monitoring_enabled: bool = True
    max_history_size: int = 2500
    retention_days: int = 30  # 1, 7, 30, 90, or 0 for Never
    deduplicate_enabled: bool = True
    save_images: bool = True
    max_image_size_mb: int = 15
    filter_sensitive_content: bool = True

    # Global Shortcuts
    shortcut_quick_paste: str = "Ctrl+Shift+V"
    shortcut_main_window: str = "Ctrl+Shift+S"
    shortcut_pause_monitoring: str = "Ctrl+Shift+P"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "AppSettings":
        defaults = cls()
        kwargs: Dict[str, Any] = {}
        for field_name, default_val in asdict(defaults).items():
            if field_name not in raw:
                kwargs[field_name] = default_val
                continue
            val = raw[field_name]
            if isinstance(default_val, bool):
                if isinstance(val, str):
                    kwargs[field_name] = val.lower() in ("true", "1", "yes")
                else:
                    kwargs[field_name] = bool(val)
            elif isinstance(default_val, int):
                try:
                    kwargs[field_name] = int(val)
                except (ValueError, TypeError):
                    kwargs[field_name] = default_val
            else:
                kwargs[field_name] = str(val)
        return cls(**kwargs)
