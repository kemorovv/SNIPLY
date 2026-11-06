"""
Single-Instance Application Bootstrapper for SNIPLY.
Manages QLocalServer / QLocalSocket single-instance lock, High-DPI scaling,
Windows AppUserModelID taskbar icon grouping, first-run language detection,
onboarding consent wizard, and clean shutdown.
"""

import ctypes
import sys
from typing import List, Optional

from app.constants import APP_NAME, APP_VERSION, SINGLE_INSTANCE_KEY
from app.paths import AppPaths
from core.clipboard_adapter import QtClipboardAdapter
from core.clipboard_manager import ClipboardManager
from core.database import Database
from core.i18n import LocalizationManager
from core.logger import get_logger
from core.storage import StorageRepository

logger = get_logger("application")


class SniplyApplication:
    """Application lifecycle manager with single-instance protection."""

    def __init__(self, argv: Optional[List[str]] = None) -> None:
        self.argv = argv if argv is not None else sys.argv

    @staticmethod
    def _configure_windows_app_id() -> None:
        """Set explicit Windows AppUserModelID so the taskbar uses the SNIPLY icon instead of python.exe."""
        if sys.platform == "win32":
            try:
                windll = getattr(ctypes, "windll", None)
                if windll is not None:
                    app_id = f"SNIPLY.SmartClipboardManager.Desktop.{APP_VERSION}"
                    windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            except Exception:
                pass

    def run(self) -> int:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QIcon
        from PySide6.QtNetwork import QLocalServer, QLocalSocket
        from PySide6.QtWidgets import QApplication

        from ui.main_window import MainWindow
        from ui.onboarding import OnboardingDialog

        self._configure_windows_app_id()

        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        app = QApplication(self.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        app.setQuitOnLastWindowClosed(False)

        # Single-Instance Check via QLocalSocket / QLocalServer
        socket = QLocalSocket()
        socket.connectToServer(SINGLE_INSTANCE_KEY)
        if socket.waitForConnected(250):
            socket.write(b"SHOW_WINDOW")
            socket.flush()
            socket.waitForBytesWritten(250)
            socket.disconnectFromServer()
            logger.info("Another SNIPLY instance is already running; activating existing window.")
            return 0

        local_server = QLocalServer(app)
        QLocalServer.removeServer(SINGLE_INSTANCE_KEY)
        local_server.listen(SINGLE_INSTANCE_KEY)

        # Load application icon
        ico_path = AppPaths.get_logo_dir() / "sniply.ico"
        if ico_path.exists():
            app.setWindowIcon(QIcon(str(ico_path)))

        # Initialize Database, Storage, and Localization
        db = Database()
        storage = StorageRepository(db)
        settings = storage.load_settings()

        detected_sys_lang = LocalizationManager.detect_system_language()
        if not settings.onboarding_completed and not settings.language_manually_selected:
            # Default to English on first launch, or offer Russian when Windows is configured in Russian
            if detected_sys_lang == "ru":
                settings.language = "ru"
                storage.save_settings(settings)

        LocalizationManager.instance().set_language(settings.language)

        # Apply QSS Theme
        qss_name = "light.qss" if settings.theme == "light" else "dark.qss"
        qss_path = AppPaths.get_styles_dir() / qss_name
        if qss_path.exists():
            app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

        # Initialize Clipboard Manager
        adapter = QtClipboardAdapter()
        clipboard_manager = ClipboardManager(storage=storage, adapter=adapter)

        # Show First-Run Onboarding if not yet completed
        if not clipboard_manager.settings.onboarding_completed:
            wizard = OnboardingDialog(
                clipboard_manager=clipboard_manager,
                detected_language=detected_sys_lang,
            )
            wizard.exec()
        else:
            clipboard_manager.initialize_monitoring()

        main_window = MainWindow(clipboard_manager=clipboard_manager)

        def _on_new_instance_connection() -> None:
            conn = local_server.nextPendingConnection()
            if conn is not None:
                conn.waitForReadyRead(200)
                conn.close()
            main_window.bring_to_front()

        local_server.newConnection.connect(_on_new_instance_connection)

        start_min = "--minimized" in self.argv or clipboard_manager.settings.start_minimized
        if not start_min:
            main_window.show()

        return app.exec()
