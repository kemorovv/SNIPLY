"""
Main Application Window for SNIPLY.
Assembles the three primary visual areas:
A. Left Sidebar (navigation, collapse toggle, storage & privacy status)
B. Center Stacked View Area (All Clips, Pinned, Favorites, Collections, Colors, Images, Snippets, Insights, Settings)
C. Right Collapsible Inspector Panel
Along with Toast Notifications, Global Shortcut handling (WM_HOTKEY), and System Tray integration.
"""

import ctypes
from ctypes import wintypes
import sys
from typing import List, Optional

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QCloseEvent, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.constants import (
    APP_NAME,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
)
from app.paths import AppPaths
from core.clipboard_manager import ClipboardManager
from core.i18n import tr
from core.shortcut_manager import ShortcutManager, WM_HOTKEY
from core.window_manager import WindowManager
from models.clip import Clip
from ui.collections_view import CollectionsView
from ui.colors_view import ColorsView
from ui.history_view import HistoryView
from ui.images_view import ImagesView
from ui.insights_view import InsightsView
from ui.inspector import InspectorPanel
from ui.quick_paste import QuickPasteWindow
from ui.settings_view import SettingsView
from ui.sidebar import SidebarWidget
from ui.snippets_view import SnippetsView
from ui.system_tray import SystemTrayController
from ui.widgets.toast import ToastNotification


class MainWindow(QMainWindow):
    """Primary desktop window for SNIPLY."""

    def __init__(
        self,
        clipboard_manager: ClipboardManager,
        shortcut_manager: Optional[ShortcutManager] = None,
        window_manager: Optional[WindowManager] = None,
    ) -> None:
        super().__init__()
        self.clipboard_manager = clipboard_manager
        self.storage = clipboard_manager.storage
        self.shortcut_manager = shortcut_manager or ShortcutManager()
        self.window_manager = window_manager or WindowManager()
        self._force_quit = False

        self.setWindowTitle(APP_NAME)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        icon_path = AppPaths.get_logo_dir() / "sniply.ico"
        if not icon_path.exists():
            icon_path = AppPaths.get_logo_dir() / "sniply_256.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # A. Left Sidebar
        self.sidebar = SidebarWidget(
            collapsed=self.clipboard_manager.settings.sidebar_collapsed,
            parent=central,
        )
        self.sidebar.section_selected.connect(self._on_section_selected)
        self.sidebar.demo_mode_toggled.connect(self._on_demo_mode_toggled)
        root_layout.addWidget(self.sidebar)

        # B. Center Stacked Views
        self.stack = QStackedWidget(central)
        root_layout.addWidget(self.stack, stretch=1)

        self.history_view = HistoryView(self.clipboard_manager, mode="all_clips", parent=self.stack)
        self.collections_view = CollectionsView(self.clipboard_manager, parent=self.stack)
        self.colors_view = ColorsView(self.clipboard_manager, parent=self.stack)
        self.images_view = ImagesView(self.clipboard_manager, parent=self.stack)
        self.snippets_view = SnippetsView(self.clipboard_manager, parent=self.stack)
        self.insights_view = InsightsView(self.clipboard_manager, parent=self.stack)
        self.settings_view = SettingsView(self.clipboard_manager, parent=self.stack)

        self.stack.addWidget(self.history_view)
        self.stack.addWidget(self.collections_view)
        self.stack.addWidget(self.colors_view)
        self.stack.addWidget(self.images_view)
        self.stack.addWidget(self.snippets_view)
        self.stack.addWidget(self.insights_view)
        self.stack.addWidget(self.settings_view)

        # C. Right Collapsible Inspector Panel
        self.inspector = InspectorPanel(parent=central)
        self.inspector.set_collections(self.storage.list_collections())
        self.inspector.setVisible(self.clipboard_manager.settings.inspector_visible)
        root_layout.addWidget(self.inspector)

        # Floating Toast Notification
        self.toast = ToastNotification(
            parent=self,
            reduced_motion=self.clipboard_manager.settings.reduced_motion,
        )

        # Quick Paste Floating Window
        self.quick_paste = QuickPasteWindow(
            clipboard_manager=self.clipboard_manager,
            window_manager=self.window_manager,
        )
        self.quick_paste.clip_restored.connect(lambda _c: self.show_toast(tr("toast.copied")))

        # System Tray Controller
        self.tray = SystemTrayController(self.clipboard_manager, parent_widget=self)
        self.tray.open_main_requested.connect(self.bring_to_front)
        self.tray.open_quick_paste_requested.connect(self.summon_quick_paste)
        self.tray.open_settings_requested.connect(self._open_settings_from_tray)
        self.tray.monitoring_toggled.connect(self._on_tray_monitoring_toggled)
        self.tray.exit_requested.connect(self.quit_application)
        self.tray.show()

        # Connect signals between views, inspector, and clipboard manager
        self.history_view.clip_selected.connect(self.inspector.inspect_clip)
        self.history_view.clip_copied.connect(lambda _c: self.show_toast(tr("toast.copied")))
        self.history_view.history_mutated.connect(self._refresh_sidebar_status)

        self.collections_view.clip_selected.connect(self.inspector.inspect_clip)
        self.collections_view.clip_copied.connect(lambda _c: self.show_toast(tr("toast.copied")))
        self.collections_view.collections_mutated.connect(self._on_collections_mutated)

        self.colors_view.clip_selected.connect(self.inspector.inspect_clip)
        self.colors_view.color_copied.connect(
            lambda fmt, val: self.show_toast(tr("colors.copied_format", format=fmt, value=val))
        )

        self.images_view.clip_selected.connect(self.inspector.inspect_clip)
        self.images_view.clip_copied.connect(lambda _c: self.show_toast(tr("toast.copied")))

        self.snippets_view.snippet_copied.connect(lambda _t: self.show_toast(tr("toast.copied")))

        self.inspector.copy_text_requested.connect(self._on_inspector_copy_text)
        self.inspector.copy_clip_requested.connect(self._on_inspector_copy_clip)
        self.inspector.collection_changed.connect(self._on_inspector_collection_changed)
        self.inspector.tags_changed.connect(self._on_inspector_tags_changed)

        self.settings_view.settings_updated.connect(self._on_settings_updated)
        self.settings_view.theme_changed.connect(self.apply_theme)
        self.settings_view.shortcuts_updated.connect(self.register_global_shortcuts)
        self.settings_view.toast_requested.connect(self.show_toast)

        self.clipboard_manager.on_clip_captured(self._on_clip_captured)
        self.clipboard_manager.on_notification(self._on_manager_notification)

        # In-window Qt fallback shortcut for Quick Paste
        self._local_qp_shortcut = QShortcut(QKeySequence("Ctrl+Shift+V"), self)
        self._local_qp_shortcut.activated.connect(self.summon_quick_paste)

        self.register_global_shortcuts()
        self.history_view.refresh_entries()
        self._refresh_sidebar_status()

    def apply_theme(self, theme_name: str) -> None:
        qss_file = "light.qss" if theme_name == "light" else "dark.qss"
        qss_path = AppPaths.get_styles_dir() / qss_file
        if qss_path.exists():
            app = QApplication.instance()
            if isinstance(app, QApplication):
                app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    def register_global_shortcuts(self) -> None:
        hwnd = int(self.winId()) if sys.platform == "win32" else None
        s = self.clipboard_manager.settings
        self.shortcut_manager.unregister_all(hwnd=hwnd)
        self.shortcut_manager.register_shortcut(
            "quick_paste", s.shortcut_quick_paste, self.summon_quick_paste, hwnd=hwnd
        )
        self.shortcut_manager.register_shortcut(
            "main_window", s.shortcut_main_window, self.toggle_main_window, hwnd=hwnd
        )
        self.shortcut_manager.register_shortcut(
            "pause_monitoring",
            s.shortcut_pause_monitoring,
            self._toggle_monitoring_hotkey,
            hwnd=hwnd,
        )

    def nativeEvent(self, eventType: QByteArray | bytes, message: int):
        """Intercept native Windows WM_HOTKEY messages for global shortcuts."""
        if sys.platform == "win32" and eventType in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            try:
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == WM_HOTKEY:
                    handled = self.shortcut_manager.handle_hotkey_id(int(msg.wParam))
                    if handled:
                        return True, 0
            except Exception:
                pass
        return super().nativeEvent(eventType, message)

    def summon_quick_paste(self) -> None:
        own_hwnds = {int(self.winId()), int(self.quick_paste.winId())} if sys.platform == "win32" else None
        self.quick_paste.summon(own_hwnds=own_hwnds)

    def toggle_main_window(self) -> None:
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.bring_to_front()

    def bring_to_front(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _open_settings_from_tray(self) -> None:
        self.bring_to_front()
        self.sidebar.select_section("settings")

    def _toggle_monitoring_hotkey(self) -> None:
        new_state = not self.clipboard_manager.monitor.is_running
        self.clipboard_manager.set_monitoring_enabled(new_state)
        self._on_tray_monitoring_toggled(new_state)

    def _on_tray_monitoring_toggled(self, active: bool) -> None:
        self.tray.refresh_menu_labels()
        self._refresh_sidebar_status()
        self.show_toast(
            tr("toast.monitoring_resumed") if active else tr("toast.monitoring_paused")
        )

    def _on_section_selected(self, section_id: str) -> None:
        show_inspector = section_id in (
            "all_clips",
            "pinned",
            "favorites",
            "collections",
            "colors",
            "images",
        )
        self.inspector.setVisible(
            show_inspector and self.clipboard_manager.settings.inspector_visible
        )

        if section_id in ("all_clips", "pinned", "favorites"):
            self.history_view.set_mode(section_id)
            self.stack.setCurrentWidget(self.history_view)
        elif section_id == "collections":
            self.collections_view.refresh_collections()
            self.stack.setCurrentWidget(self.collections_view)
        elif section_id == "colors":
            self.colors_view.refresh_colors()
            self.stack.setCurrentWidget(self.colors_view)
        elif section_id == "images":
            self.images_view.refresh_images()
            self.stack.setCurrentWidget(self.images_view)
        elif section_id == "snippets":
            self.snippets_view.refresh_snippets()
            self.stack.setCurrentWidget(self.snippets_view)
        elif section_id == "insights":
            self.insights_view.refresh_insights()
            self.stack.setCurrentWidget(self.insights_view)
        elif section_id == "settings":
            self.stack.setCurrentWidget(self.settings_view)

    def _on_demo_mode_toggled(self, active: bool) -> None:
        self.clipboard_manager.demo_mode = active
        self.history_view.refresh_entries()
        self.colors_view.refresh_colors()

    def _on_clip_captured(self, clip: Clip, _is_dup: bool) -> None:
        curr = self.stack.currentWidget()
        if curr == self.history_view:
            self.history_view.refresh_entries()
        elif curr == self.colors_view:
            self.colors_view.refresh_colors()
        elif curr == self.images_view:
            self.images_view.refresh_images()
        elif curr == self.insights_view:
            self.insights_view.refresh_insights()
        self._refresh_sidebar_status()

    def _on_manager_notification(self, trans_key: str, detail: str) -> None:
        if trans_key == "toast.image_too_large":
            self.show_toast(tr(trans_key, size=detail))
        else:
            self.show_toast(tr(trans_key))

    def _on_inspector_copy_text(self, text: str) -> None:
        self.clipboard_manager.copy_custom_text(text)
        self.show_toast(tr("toast.copied"))

    def _on_inspector_copy_clip(self, clip: Clip) -> None:
        self.clipboard_manager.restore_clip_to_clipboard(clip)
        self.show_toast(tr("toast.copied"))

    def _on_inspector_collection_changed(self, clip: Clip, col_id: Optional[int]) -> None:
        if clip.id is not None and not clip.is_demo:
            updated = self.storage.set_clip_collection(clip.id, col_id)
            self.history_view.refresh_entries()
            if updated:
                self.inspector.inspect_clip(updated)

    def _on_inspector_tags_changed(self, clip: Clip, tags: List[str]) -> None:
        if clip.id is not None and not clip.is_demo:
            updated = self.storage.set_clip_tags(clip.id, tags)
            if updated:
                self.inspector.inspect_clip(updated)

    def _on_collections_mutated(self) -> None:
        self.inspector.set_collections(self.storage.list_collections())

    def _on_settings_updated(self) -> None:
        s = self.clipboard_manager.settings
        self.toast.reduced_motion = s.reduced_motion
        self.sidebar.set_collapsed(s.sidebar_collapsed)
        self.tray.refresh_menu_labels()
        self.history_view.refresh_entries()
        self._refresh_sidebar_status()

    def _refresh_sidebar_status(self) -> None:
        metrics = self.storage.get_storage_metrics()
        self.sidebar.update_status(
            monitoring_active=self.clipboard_manager.monitor.is_running,
            storage_bytes=metrics["total_bytes"],
        )

    def show_toast(self, message: str) -> None:
        self.toast.show_message(message)

    def quit_application(self) -> None:
        self._force_quit = True
        hwnd = int(self.winId()) if sys.platform == "win32" else None
        self.shortcut_manager.unregister_all(hwnd=hwnd)
        self.clipboard_manager.monitor.stop()
        self.tray.hide()
        self.quick_paste.close()
        self.close()
        app = QApplication.instance()
        if app:
            app.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._force_quit and self.clipboard_manager.settings.close_to_tray:
            event.ignore()
            self.hide()
            return
        hwnd = int(self.winId()) if sys.platform == "win32" else None
        self.shortcut_manager.unregister_all(hwnd=hwnd)
        self.clipboard_manager.monitor.stop()
        self.tray.hide()
        super().closeEvent(event)
