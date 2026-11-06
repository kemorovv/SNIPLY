"""
Windows System Tray Integration for SNIPLY.
Provides localized tray context menu:
- Open SNIPLY
- Quick Paste (Ctrl+Shift+V)
- Pause / Resume Monitoring
- Settings
- Exit SNIPLY
"""

from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from app.constants import APP_NAME
from app.paths import AppPaths
from core.clipboard_manager import ClipboardManager
from core.i18n import LocalizationManager, tr


class SystemTrayController(QObject):
    """Manages QSystemTrayIcon and localized tray menu actions."""

    open_main_requested = Signal()
    open_quick_paste_requested = Signal()
    open_settings_requested = Signal()
    monitoring_toggled = Signal(bool)
    exit_requested = Signal()

    def __init__(
        self,
        clipboard_manager: ClipboardManager,
        parent_widget: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent_widget)
        self.clipboard_manager = clipboard_manager
        self.parent_widget = parent_widget

        icon_path = AppPaths.get_logo_dir() / "sniply.ico"
        if not icon_path.exists():
            icon_path = AppPaths.get_logo_dir() / "sniply_64.png"

        self.tray_icon = QSystemTrayIcon(QIcon(str(icon_path)), parent_widget)
        self.tray_icon.setToolTip(APP_NAME)

        self.menu = QMenu(parent_widget)
        self.act_open = QAction(tr("tray.open_sniply"), self.menu)
        self.act_open.triggered.connect(self.open_main_requested.emit)
        self.menu.addAction(self.act_open)

        self.act_qp = QAction(tr("tray.quick_paste"), self.menu)
        self.act_qp.triggered.connect(self.open_quick_paste_requested.emit)
        self.menu.addAction(self.act_qp)

        self.menu.addSeparator()

        self.act_toggle_mon = QAction("", self.menu)
        self.act_toggle_mon.triggered.connect(self._toggle_monitoring)
        self.menu.addAction(self.act_toggle_mon)

        self.act_settings = QAction(tr("tray.settings"), self.menu)
        self.act_settings.triggered.connect(self.open_settings_requested.emit)
        self.menu.addAction(self.act_settings)

        self.menu.addSeparator()

        self.act_exit = QAction(tr("tray.exit"), self.menu)
        self.act_exit.triggered.connect(self.exit_requested.emit)
        self.menu.addAction(self.act_exit)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.activated.connect(self._on_tray_activated)

        self.refresh_menu_labels()
        LocalizationManager.instance().subscribe(lambda _l: self.refresh_menu_labels())

    def show(self) -> None:
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()

    def hide(self) -> None:
        self.tray_icon.hide()

    def refresh_menu_labels(self) -> None:
        self.act_open.setText(tr("tray.open_sniply"))
        self.act_qp.setText(tr("tray.quick_paste"))
        is_running = self.clipboard_manager.monitor.is_running
        self.act_toggle_mon.setText(
            tr("tray.pause_monitoring") if is_running else tr("tray.resume_monitoring")
        )
        self.act_settings.setText(tr("tray.settings"))
        self.act_exit.setText(tr("tray.exit"))

    def _toggle_monitoring(self) -> None:
        new_state = not self.clipboard_manager.monitor.is_running
        self.clipboard_manager.set_monitoring_enabled(new_state)
        self.refresh_menu_labels()
        self.monitoring_toggled.emit(new_state)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.open_main_requested.emit()
