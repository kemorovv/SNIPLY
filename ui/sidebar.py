"""
Sidebar Navigation Component for SNIPLY.
Displays SNIPLY logo, product name, version badge, 9 primary navigation items with active purple styling,
collapsible mode, demo mode toggle, storage usage indicator, and privacy status badge.
"""

from typing import Dict, List, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.constants import (
    APP_NAME,
    APP_VERSION,
    SIDEBAR_COLLAPSED_WIDTH,
    SIDEBAR_EXPANDED_WIDTH,
)
from app.paths import AppPaths
from core.i18n import LocalizationManager, tr


class SidebarWidget(QFrame):
    """Left navigation sidebar supporting expanded and collapsed states and immediate localization."""

    section_selected = Signal(str)
    demo_mode_toggled = Signal(bool)

    NAV_ITEMS: List[tuple[str, str, str]] = [
        ("all_clips", "navigation.all_clips", "all_clips"),
        ("pinned", "navigation.pinned", "pinned"),
        ("favorites", "navigation.favorites", "favorites"),
        ("collections", "navigation.collections", "collections"),
        ("colors", "navigation.colors", "colors"),
        ("images", "navigation.images", "images"),
        ("snippets", "navigation.snippets", "snippets"),
        ("insights", "navigation.insights", "insights"),
        ("settings", "navigation.settings", "settings"),
    ]

    def __init__(self, collapsed: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("SidebarContainer")
        self._collapsed = collapsed
        self._current_section = "all_clips"
        self._demo_active = False
        self._nav_buttons: Dict[str, QPushButton] = {}

        self.setFixedWidth(SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_EXPANDED_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 14)
        layout.setSpacing(6)

        # Header: Logo + Brand Name + Version + Collapse Toggle
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        self.logo_label = QLabel(self)
        self.logo_label.setFixedSize(32, 32)
        logo_file = AppPaths.get_logo_dir() / "sniply_64.png"
        if logo_file.exists():
            pix = QPixmap(str(logo_file)).scaled(
                32,
                32,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.logo_label.setPixmap(pix)
        header_row.addWidget(self.logo_label)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(0)
        self.title_label = QLabel(APP_NAME, self)
        self.title_label.setStyleSheet(
            "font-size: 15px; font-weight: 700; letter-spacing: 0.6px; color: #F4F2FA; background: transparent;"
        )
        self.version_badge = QLabel(tr("app.version_label", version=APP_VERSION), self)
        self.version_badge.setStyleSheet("font-size: 11px; color: #72717E; background: transparent;")
        brand_col.addWidget(self.title_label)
        brand_col.addWidget(self.version_badge)
        header_row.addLayout(brand_col, stretch=1)

        self.collapse_btn = QPushButton(self)
        self.collapse_btn.setFixedSize(28, 28)
        self.collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sidebar_svg = AppPaths.get_icons_dir() / "sidebar.svg"
        if sidebar_svg.exists():
            self.collapse_btn.setIcon(QIcon(str(sidebar_svg)))
        self.collapse_btn.clicked.connect(self.toggle_collapsed)
        header_row.addWidget(self.collapse_btn)

        layout.addLayout(header_row)
        layout.addSpacing(12)

        # Navigation Buttons
        for section_id, trans_key, icon_name in self.NAV_ITEMS:
            btn = QPushButton(tr(trans_key), self)
            btn.setObjectName("NavButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setIconSize(QSize(18, 18))
            btn.clicked.connect(lambda checked=False, s=section_id: self.select_section(s))
            self._nav_buttons[section_id] = btn
            layout.addWidget(btn)

        layout.addStretch(1)

        # Optional Demo Gallery Toggle Button
        self.demo_btn = QPushButton(tr("sidebar.demo_mode"), self)
        self.demo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        zap_svg = AppPaths.get_icons_dir() / "zap_active.svg"
        if zap_svg.exists():
            self.demo_btn.setIcon(QIcon(str(zap_svg)))
        self.demo_btn.clicked.connect(self._on_demo_clicked)
        layout.addWidget(self.demo_btn)

        # Footer: Storage Usage + Privacy & Monitoring Indicator
        self.footer_frame = QFrame(self)
        self.footer_frame.setStyleSheet(
            "background-color: #22232A; border: 1px solid #292A32; border-radius: 9px;"
        )
        footer_layout = QVBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(10, 8, 10, 8)
        footer_layout.setSpacing(4)

        priv_row = QHBoxLayout()
        priv_row.setSpacing(6)
        self.status_dot = QLabel("●", self.footer_frame)
        self.status_dot.setStyleSheet("color: #6DD6A5; font-size: 12px; background: transparent;")
        priv_row.addWidget(self.status_dot)

        self.privacy_lbl = QLabel(tr("sidebar.privacy_active"), self.footer_frame)
        self.privacy_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #F4F2FA; background: transparent;"
        )
        priv_row.addWidget(self.privacy_lbl, stretch=1)
        footer_layout.addLayout(priv_row)

        self.storage_lbl = QLabel(tr("sidebar.storage_usage", size="0 KB"), self.footer_frame)
        self.storage_lbl.setStyleSheet("font-size: 11px; color: #A3A1AE; background: transparent;")
        footer_layout.addWidget(self.storage_lbl)

        layout.addWidget(self.footer_frame)

        self._update_button_states()
        self._apply_collapsed_state()
        LocalizationManager.instance().subscribe(self._on_language_changed)

    def select_section(self, section_id: str) -> None:
        if section_id not in self._nav_buttons:
            return
        self._current_section = section_id
        self._update_button_states()
        self.section_selected.emit(section_id)

    def _update_button_states(self) -> None:
        icons_dir = AppPaths.get_icons_dir()
        for section_id, trans_key, icon_name in self.NAV_ITEMS:
            btn = self._nav_buttons[section_id]
            is_active = section_id == self._current_section
            btn.setProperty("active", "true" if is_active else "false")
            svg_file = icons_dir / (f"{icon_name}_active.svg" if is_active else f"{icon_name}.svg")
            if svg_file.exists():
                btn.setIcon(QIcon(str(svg_file)))
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def toggle_collapsed(self) -> None:
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self.setFixedWidth(SIDEBAR_COLLAPSED_WIDTH if collapsed else SIDEBAR_EXPANDED_WIDTH)
        self._apply_collapsed_state()

    def _apply_collapsed_state(self) -> None:
        self.title_label.setVisible(not self._collapsed)
        self.version_badge.setVisible(not self._collapsed)
        self.footer_frame.setVisible(not self._collapsed)
        self.demo_btn.setText("" if self._collapsed else tr("sidebar.demo_mode"))
        self.collapse_btn.setToolTip(
            tr("navigation.expand_sidebar") if self._collapsed else tr("navigation.collapse_sidebar")
        )
        for section_id, trans_key, _ in self.NAV_ITEMS:
            btn = self._nav_buttons[section_id]
            btn.setText("" if self._collapsed else tr(trans_key))
            btn.setToolTip(tr(trans_key))

    def _on_demo_clicked(self) -> None:
        self._demo_active = not self._demo_active
        self.demo_mode_toggled.emit(self._demo_active)

    def set_demo_active(self, active: bool) -> None:
        self._demo_active = active

    def update_status(self, monitoring_active: bool, storage_bytes: int) -> None:
        size_str = LocalizationManager.instance().format_file_size(storage_bytes)
        self.storage_lbl.setText(tr("sidebar.storage_usage", size=size_str))
        if monitoring_active:
            self.status_dot.setStyleSheet("color: #6DD6A5; font-size: 12px; background: transparent;")
            self.privacy_lbl.setText(tr("sidebar.monitoring_active"))
        else:
            self.status_dot.setStyleSheet("color: #E9BB70; font-size: 12px; background: transparent;")
            self.privacy_lbl.setText(tr("sidebar.monitoring_paused"))

    def _on_language_changed(self, _lang: str) -> None:
        self._apply_collapsed_state()
        self.version_badge.setText(tr("app.version_label", version=APP_VERSION))
