"""
Complete Settings Interface for SNIPLY.
Covers General (including immediate English/Russian language switching and Windows startup),
Appearance (Dark/Light theme, density, reduced motion), Clipboard & Privacy (monitoring, retention,
max history, image limits, sensitive filter, excluded executables), Shortcuts (with conflict validation),
Storage & Backup (paths, sizes, backup, JSON export/import, history clear), and About.
"""

from pathlib import Path
from typing import Optional
import webbrowser

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.constants import APP_GITHUB_URL, APP_NAME, APP_VERSION, SUPPORTED_LANGUAGES
from app.paths import AppPaths
from core.clipboard_manager import ClipboardManager
from core.i18n import LocalizationManager, tr
from core.shortcut_manager import ShortcutManager
from core.window_manager import WindowManager


class SettingsView(QFrame):
    """Tabbed Settings interface where every control persists and takes immediate effect."""

    settings_updated = Signal()
    theme_changed = Signal(str)
    shortcuts_updated = Signal()
    toast_requested = Signal(str)

    def __init__(
        self,
        clipboard_manager: ClipboardManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.clipboard_manager = clipboard_manager
        self.storage = clipboard_manager.storage

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 20, 24, 20)
        self.main_layout.setSpacing(14)

        self.title_lbl = QLabel(tr("navigation.settings"), self)
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #F4F2FA;")
        self.main_layout.addWidget(self.title_lbl)

        self.tabs = QTabWidget(self)
        self.main_layout.addWidget(self.tabs, stretch=1)

        self._build_tabs()
        LocalizationManager.instance().subscribe(self._on_language_changed)

    def _build_tabs(self) -> None:
        current_idx = max(0, self.tabs.currentIndex())
        self.tabs.clear()

        self.tabs.addTab(self._create_general_tab(), tr("settings.tab.general"))
        self.tabs.addTab(self._create_appearance_tab(), tr("settings.tab.appearance"))
        self.tabs.addTab(self._create_clipboard_tab(), tr("settings.tab.clipboard"))
        self.tabs.addTab(self._create_shortcuts_tab(), tr("settings.tab.shortcuts"))
        self.tabs.addTab(self._create_storage_tab(), tr("settings.tab.storage"))
        self.tabs.addTab(self._create_about_tab(), tr("settings.tab.about"))
        self.tabs.setCurrentIndex(min(current_idx, self.tabs.count() - 1))

    # -------------------------------------------------------------------------
    # Tab 1: General (Language, Startup, System Tray, Auto-Paste)
    # -------------------------------------------------------------------------
    def _create_general_tab(self) -> QWidget:
        s = self.clipboard_manager.settings
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)

        lang_combo = QComboBox(page)
        for idx, (code, label) in enumerate(SUPPORTED_LANGUAGES.items()):
            lang_combo.addItem(f"{label} ({code})", code)
            if code == s.language:
                lang_combo.setCurrentIndex(idx)
        lang_combo.currentIndexChanged.connect(
            lambda _i: self._on_language_selected(lang_combo.currentData())
        )
        form.addRow(tr("settings.general.language"), lang_combo)

        layout.addLayout(form)

        chk_startup = QCheckBox(tr("settings.general.launch_startup"), page)
        chk_startup.setChecked(s.launch_at_startup)
        chk_startup.toggled.connect(self._on_startup_toggled)
        layout.addWidget(chk_startup)

        chk_min = QCheckBox(tr("settings.general.start_minimized"), page)
        chk_min.setChecked(s.start_minimized)
        chk_min.toggled.connect(lambda v: self._save_field("start_minimized", v))
        layout.addWidget(chk_min)

        chk_min_tray = QCheckBox(tr("settings.general.minimize_to_tray"), page)
        chk_min_tray.setChecked(s.minimize_to_tray)
        chk_min_tray.toggled.connect(lambda v: self._save_field("minimize_to_tray", v))
        layout.addWidget(chk_min_tray)

        chk_close_tray = QCheckBox(tr("settings.general.close_to_tray"), page)
        chk_close_tray.setChecked(s.close_to_tray)
        chk_close_tray.toggled.connect(lambda v: self._save_field("close_to_tray", v))
        layout.addWidget(chk_close_tray)

        chk_auto_mon = QCheckBox(tr("settings.general.auto_start_monitoring"), page)
        chk_auto_mon.setChecked(s.auto_start_monitoring)
        chk_auto_mon.toggled.connect(lambda v: self._save_field("auto_start_monitoring", v))
        layout.addWidget(chk_auto_mon)

        chk_auto_paste = QCheckBox(tr("settings.general.auto_paste"), page)
        chk_auto_paste.setChecked(s.auto_paste_on_quick_select)
        chk_auto_paste.toggled.connect(lambda v: self._save_field("auto_paste_on_quick_select", v))
        layout.addWidget(chk_auto_paste)

        layout.addStretch(1)
        return page

    # -------------------------------------------------------------------------
    # Tab 2: Appearance
    # -------------------------------------------------------------------------
    def _create_appearance_tab(self) -> QWidget:
        s = self.clipboard_manager.settings
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)

        theme_combo = QComboBox(page)
        theme_combo.addItem(tr("settings.appearance.theme_dark"), "dark")
        theme_combo.addItem(tr("settings.appearance.theme_light"), "light")
        theme_combo.setCurrentIndex(1 if s.theme == "light" else 0)
        theme_combo.currentIndexChanged.connect(
            lambda _i: self._on_theme_selected(theme_combo.currentData())
        )
        form.addRow(tr("settings.appearance.theme"), theme_combo)

        density_combo = QComboBox(page)
        density_combo.addItem(tr("settings.appearance.density_comfortable"), "comfortable")
        density_combo.addItem(tr("settings.appearance.density_compact"), "compact")
        density_combo.setCurrentIndex(1 if s.density == "compact" else 0)
        density_combo.currentIndexChanged.connect(
            lambda _i: self._save_field("density", density_combo.currentData())
        )
        form.addRow(tr("settings.appearance.density"), density_combo)

        layout.addLayout(form)

        chk_motion = QCheckBox(tr("settings.appearance.reduced_motion"), page)
        chk_motion.setChecked(s.reduced_motion)
        chk_motion.toggled.connect(lambda v: self._save_field("reduced_motion", v))
        layout.addWidget(chk_motion)

        chk_sidebar = QCheckBox(tr("settings.appearance.sidebar_collapsed"), page)
        chk_sidebar.setChecked(s.sidebar_collapsed)
        chk_sidebar.toggled.connect(lambda v: self._save_field("sidebar_collapsed", v))
        layout.addWidget(chk_sidebar)

        layout.addStretch(1)
        return page

    # -------------------------------------------------------------------------
    # Tab 3: Clipboard & Privacy
    # -------------------------------------------------------------------------
    def _create_clipboard_tab(self) -> QWidget:
        s = self.clipboard_manager.settings
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        chk_mon = QCheckBox(tr("settings.clipboard.monitoring_enabled"), page)
        chk_mon.setChecked(s.monitoring_enabled)
        chk_mon.toggled.connect(self._on_monitoring_toggled)
        layout.addWidget(chk_mon)

        chk_dedup = QCheckBox(tr("settings.clipboard.deduplicate"), page)
        chk_dedup.setChecked(s.deduplicate_enabled)
        chk_dedup.toggled.connect(lambda v: self._save_field("deduplicate_enabled", v))
        layout.addWidget(chk_dedup)

        chk_imgs = QCheckBox(tr("settings.clipboard.save_images"), page)
        chk_imgs.setChecked(s.save_images)
        chk_imgs.toggled.connect(lambda v: self._save_field("save_images", v))
        layout.addWidget(chk_imgs)

        chk_sens = QCheckBox(tr("settings.clipboard.filter_sensitive"), page)
        chk_sens.setChecked(s.filter_sensitive_content)
        chk_sens.toggled.connect(lambda v: self._save_field("filter_sensitive_content", v))
        layout.addWidget(chk_sens)

        form = QFormLayout()
        form.setSpacing(10)

        max_spin = QSpinBox(page)
        max_spin.setRange(50, 50000)
        max_spin.setSingleStep(250)
        max_spin.setValue(s.max_history_size)
        max_spin.valueChanged.connect(lambda v: self._save_field("max_history_size", int(v)))
        form.addRow(tr("settings.clipboard.max_history"), max_spin)

        ret_combo = QComboBox(page)
        ret_options = [
            (1, tr("settings.clipboard.retention_1d")),
            (7, tr("settings.clipboard.retention_7d")),
            (30, tr("settings.clipboard.retention_30d")),
            (90, tr("settings.clipboard.retention_90d")),
            (0, tr("settings.clipboard.retention_never")),
        ]
        for idx, (days, label) in enumerate(ret_options):
            ret_combo.addItem(label, days)
            if days == s.retention_days:
                ret_combo.setCurrentIndex(idx)
        ret_combo.currentIndexChanged.connect(
            lambda _i: self._save_field("retention_days", int(ret_combo.currentData()))
        )
        form.addRow(tr("settings.clipboard.retention_period"), ret_combo)

        img_mb_spin = QSpinBox(page)
        img_mb_spin.setRange(1, 100)
        img_mb_spin.setValue(s.max_image_size_mb)
        img_mb_spin.valueChanged.connect(lambda v: self._save_field("max_image_size_mb", int(v)))
        form.addRow(tr("settings.clipboard.max_image_mb"), img_mb_spin)

        layout.addLayout(form)

        # Excluded Applications List
        ex_lbl = QLabel(tr("settings.clipboard.excluded_apps"), page)
        ex_lbl.setStyleSheet("font-weight: 600; color: #F4F2FA;")
        layout.addWidget(ex_lbl)

        self.ex_list = QListWidget(page)
        self.ex_list.setMaximumHeight(110)
        for exe in self.storage.list_excluded_apps():
            self.ex_list.addItem(exe)
        layout.addWidget(self.ex_list)

        ex_row = QHBoxLayout()
        self.ex_input = QLineEdit(page)
        self.ex_input.setPlaceholderText(tr("settings.clipboard.add_exclusion_placeholder"))
        ex_row.addWidget(self.ex_input, stretch=1)

        add_ex_btn = QPushButton(tr("settings.clipboard.add_exclusion_btn"), page)
        add_ex_btn.clicked.connect(self._add_exclusion)
        ex_row.addWidget(add_ex_btn)

        rem_ex_btn = QPushButton(tr("settings.clipboard.remove_exclusion_btn"), page)
        rem_ex_btn.clicked.connect(self._remove_exclusion)
        ex_row.addWidget(rem_ex_btn)
        layout.addLayout(ex_row)

        layout.addStretch(1)
        return page

    # -------------------------------------------------------------------------
    # Tab 4: Shortcuts
    # -------------------------------------------------------------------------
    def _create_shortcuts_tab(self) -> QWidget:
        s = self.clipboard_manager.settings
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)

        self.sc_qp_edit = QLineEdit(s.shortcut_quick_paste, page)
        form.addRow(tr("settings.shortcuts.quick_paste"), self.sc_qp_edit)

        self.sc_mw_edit = QLineEdit(s.shortcut_main_window, page)
        form.addRow(tr("settings.shortcuts.main_window"), self.sc_mw_edit)

        self.sc_pm_edit = QLineEdit(s.shortcut_pause_monitoring, page)
        form.addRow(tr("settings.shortcuts.pause_monitoring"), self.sc_pm_edit)

        layout.addLayout(form)

        self.sc_error_lbl = QLabel("", page)
        self.sc_error_lbl.setStyleSheet("color: #F07886; font-size: 12px;")
        self.sc_error_lbl.hide()
        layout.addWidget(self.sc_error_lbl)

        btn_row = QHBoxLayout()
        save_sc_btn = QPushButton(tr("action.save"), page)
        save_sc_btn.setObjectName("PrimaryButton")
        save_sc_btn.clicked.connect(self._save_shortcuts)
        btn_row.addWidget(save_sc_btn)

        reset_sc_btn = QPushButton(tr("settings.shortcuts.reset_defaults"), page)
        reset_sc_btn.clicked.connect(self._reset_default_shortcuts)
        btn_row.addWidget(reset_sc_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        layout.addStretch(1)
        return page

    # -------------------------------------------------------------------------
    # Tab 5: Storage & Backup
    # -------------------------------------------------------------------------
    def _create_storage_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        metrics = self.storage.get_storage_metrics()
        i18n = LocalizationManager.instance()

        info = QLabel(
            f"{tr('settings.storage.db_path')}:  {self.storage.db.db_path}\n"
            f"{tr('settings.storage.images_path')}:  {AppPaths.get_images_storage_dir()}\n\n"
            f"{tr('settings.storage.db_size')}:  {i18n.format_file_size(metrics['db_bytes'])}\n"
            f"{tr('settings.storage.images_size')}:  {i18n.format_file_size(metrics['images_bytes'])}",
            page,
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #A3A1AE; font-size: 13px; line-height: 1.5;")
        layout.addWidget(info)

        btn_backup = QPushButton(tr("settings.storage.backup_btn"), page)
        btn_backup.clicked.connect(self._backup_db)
        layout.addWidget(btn_backup)

        btn_export = QPushButton(tr("settings.storage.export_btn"), page)
        btn_export.clicked.connect(self._export_data)
        layout.addWidget(btn_export)

        btn_import = QPushButton(tr("settings.storage.import_btn"), page)
        btn_import.clicked.connect(self._import_data)
        layout.addWidget(btn_import)

        btn_clear = QPushButton(tr("settings.storage.clear_all_btn"), page)
        btn_clear.setObjectName("DangerButton")
        btn_clear.clicked.connect(self._clear_history)
        layout.addWidget(btn_clear)

        layout.addStretch(1)
        return page

    # -------------------------------------------------------------------------
    # Tab 6: About
    # -------------------------------------------------------------------------
    def _create_about_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        logo_lbl = QLabel(page)
        logo_path = AppPaths.get_logo_dir() / "sniply_128.png"
        if logo_path.exists():
            logo_lbl.setPixmap(
                QPixmap(str(logo_path)).scaled(
                    72,
                    72,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(logo_lbl)

        name_lbl = QLabel(f"{APP_NAME}  v{APP_VERSION}", page)
        name_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #F4F2FA;")
        layout.addWidget(name_lbl)

        desc_lbl = QLabel(tr("settings.about.description"), page)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 13px; color: #A3A1AE;")
        layout.addWidget(desc_lbl)

        lic_lbl = QLabel(tr("settings.about.license"), page)
        lic_lbl.setStyleSheet("font-size: 12px; color: #6DD6A5; font-weight: 600;")
        layout.addWidget(lic_lbl)

        cred_lbl = QLabel(tr("settings.about.credits"), page)
        cred_lbl.setStyleSheet("font-size: 12px; color: #72717E;")
        layout.addWidget(cred_lbl)

        gh_btn = QPushButton(tr("settings.about.github"), page)
        gh_btn.setMaximumWidth(220)
        gh_btn.clicked.connect(lambda: webbrowser.open(APP_GITHUB_URL))
        layout.addWidget(gh_btn)

        layout.addStretch(1)
        return page

    # -------------------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------------------
    def _save_field(self, field_name: str, value: object) -> None:
        setattr(self.clipboard_manager.settings, field_name, value)
        self.storage.save_settings(self.clipboard_manager.settings)
        self.settings_updated.emit()

    def _on_language_selected(self, lang_code: str) -> None:
        if not lang_code:
            return
        self.clipboard_manager.settings.language = lang_code
        self.clipboard_manager.settings.language_manually_selected = True
        self.storage.save_settings(self.clipboard_manager.settings)
        LocalizationManager.instance().set_language(lang_code)
        self.settings_updated.emit()

    def _on_theme_selected(self, theme_name: str) -> None:
        self._save_field("theme", theme_name)
        self.theme_changed.emit(theme_name)

    def _on_startup_toggled(self, enabled: bool) -> None:
        self._save_field("launch_at_startup", enabled)
        WindowManager.set_windows_startup(enabled)

    def _on_monitoring_toggled(self, enabled: bool) -> None:
        self.clipboard_manager.set_monitoring_enabled(enabled)
        self.settings_updated.emit()

    def _add_exclusion(self) -> None:
        exe = self.ex_input.text().strip()
        if exe and self.storage.add_excluded_app(exe):
            self.ex_list.addItem(exe)
            self.ex_input.clear()

    def _remove_exclusion(self) -> None:
        item = self.ex_list.currentItem()
        if item and self.storage.remove_excluded_app(item.text()):
            self.ex_list.takeItem(self.ex_list.row(item))

    def _save_shortcuts(self) -> None:
        candidate = {
            "quick_paste": self.sc_qp_edit.text().strip(),
            "main_window": self.sc_mw_edit.text().strip(),
            "pause_monitoring": self.sc_pm_edit.text().strip(),
        }
        valid, conflict = ShortcutManager.validate_shortcut_set(candidate)
        if not valid:
            self.sc_error_lbl.setText(
                tr("settings.shortcuts.conflict_warning", shortcut=conflict or "")
            )
            self.sc_error_lbl.show()
            return

        self.sc_error_lbl.hide()
        self.clipboard_manager.settings.shortcut_quick_paste = candidate["quick_paste"]
        self.clipboard_manager.settings.shortcut_main_window = candidate["main_window"]
        self.clipboard_manager.settings.shortcut_pause_monitoring = candidate["pause_monitoring"]
        self.storage.save_settings(self.clipboard_manager.settings)
        self.shortcuts_updated.emit()
        self.toast_requested.emit(tr("toast.saved"))

    def _reset_default_shortcuts(self) -> None:
        self.sc_qp_edit.setText("Ctrl+Shift+V")
        self.sc_mw_edit.setText("Ctrl+Shift+S")
        self.sc_pm_edit.setText("Ctrl+Shift+P")
        self._save_shortcuts()

    def _backup_db(self) -> None:
        self.storage.backup_database()
        self.toast_requested.emit(tr("toast.backup_created"))

    def _export_data(self) -> None:
        target, _ = QFileDialog.getSaveFileName(
            self,
            tr("settings.storage.export_btn"),
            "sniply_export.json",
            "JSON Files (*.json)",
        )
        if target:
            self.storage.export_to_json(Path(target))
            self.toast_requested.emit(tr("toast.export_success"))

    def _import_data(self) -> None:
        target, _ = QFileDialog.getOpenFileName(
            self,
            tr("settings.storage.import_btn"),
            "",
            "JSON Files (*.json)",
        )
        if target:
            self.storage.import_from_json(Path(target))
            self.toast_requested.emit(tr("toast.import_success"))
            self.settings_updated.emit()

    def _clear_history(self) -> None:
        resp = QMessageBox.question(
            self,
            tr("dialog.confirm_clear_history.title"),
            tr("dialog.confirm_clear_history.body"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            self.storage.clear_unprotected_history(include_favorites=False)
            self.settings_updated.emit()

    def _on_language_changed(self, _lang: str) -> None:
        self.title_lbl.setText(tr("navigation.settings"))
        self._build_tabs()
