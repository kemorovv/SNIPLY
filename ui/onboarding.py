"""
6-Screen First-Launch Onboarding Experience for SNIPLY.
Screens:
1. Welcome to SNIPLY + System Language Detection (English / Russian).
2. 100% Local & Private Clipboard History.
3. Instant Quick Paste & Global Keyboard Shortcut.
4. Smart Privacy & Password Manager Exclusions.
5. Explicit Monitoring Consent & Retention Preferences.
6. Ready to Start.
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.constants import SUPPORTED_LANGUAGES
from app.paths import AppPaths
from core.clipboard_manager import ClipboardManager
from core.i18n import LocalizationManager, tr


class OnboardingDialog(QDialog):
    """Polished 6-step first-run onboarding wizard with explicit privacy consent."""

    def __init__(
        self,
        clipboard_manager: ClipboardManager,
        detected_language: str = "en",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.clipboard_manager = clipboard_manager
        self.storage = clipboard_manager.storage
        self.detected_language = detected_language

        self.setWindowTitle(tr("onboarding.window_title"))
        self.setFixedSize(640, 460)
        self.setModal(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(28, 24, 28, 24)
        self.main_layout.setSpacing(16)

        # Top Bar: Step Indicator + Language Selector + Skip Button
        top_row = QHBoxLayout()
        self.step_indicator = QLabel("1 / 6", self)
        self.step_indicator.setStyleSheet("font-size: 12px; font-weight: 600; color: #A78BFA;")
        top_row.addWidget(self.step_indicator)
        top_row.addStretch(1)

        self.lang_combo = QComboBox(self)
        for idx, (code, label) in enumerate(SUPPORTED_LANGUAGES.items()):
            self.lang_combo.addItem(f"{label} ({code})", code)
            if code == LocalizationManager.instance().language:
                self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        top_row.addWidget(self.lang_combo)

        self.skip_btn = QPushButton(tr("onboarding.skip"), self)
        self.skip_btn.clicked.connect(self._jump_to_consent)
        top_row.addWidget(self.skip_btn)
        self.main_layout.addLayout(top_row)

        # Stacked Screens
        self.stack = QStackedWidget(self)
        self.main_layout.addWidget(self.stack, stretch=1)

        # Navigation Buttons
        nav_row = QHBoxLayout()
        self.back_btn = QPushButton(tr("onboarding.back"), self)
        self.back_btn.clicked.connect(self._go_back)
        nav_row.addWidget(self.back_btn)
        nav_row.addStretch(1)

        self.next_btn = QPushButton(tr("onboarding.next"), self)
        self.next_btn.setObjectName("PrimaryButton")
        self.next_btn.clicked.connect(self._go_next)
        nav_row.addWidget(self.next_btn)
        self.main_layout.addLayout(nav_row)

        self.consent_checkbox: Optional[QCheckBox] = None
        self.retention_combo: Optional[QComboBox] = None

        self._rebuild_screens()

    def _rebuild_screens(self) -> None:
        curr_idx = max(0, self.stack.currentIndex())
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()

        for step_num in range(1, 7):
            self.stack.addWidget(self._create_step_page(step_num))

        self.stack.setCurrentIndex(min(curr_idx, 5))
        self._update_nav_buttons()

    def _create_step_page(self, step_num: int) -> QWidget:
        card = QFrame(self)
        card.setObjectName("StatCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_lbl = QLabel(card)
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = AppPaths.get_logo_dir() / "sniply_128.png"
        if logo_path.exists():
            logo_lbl.setPixmap(
                QPixmap(str(logo_path)).scaled(
                    68,
                    68,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(logo_lbl)

        title = QLabel(tr(f"onboarding.step{step_num}.title"), card)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #F4F2FA; background: transparent;")
        layout.addWidget(title)

        body = QLabel(tr(f"onboarding.step{step_num}.body"), card)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        body.setStyleSheet("font-size: 13px; color: #A3A1AE; line-height: 1.5; background: transparent;")
        layout.addWidget(body)

        if step_num == 1 and self.detected_language == "ru":
            ru_note = QLabel(tr("onboarding.detected_ru"), card)
            ru_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ru_note.setStyleSheet("font-size: 12px; color: #6DD6A5; background: transparent;")
            layout.addWidget(ru_note)

        if step_num == 5:
            self.consent_checkbox = QCheckBox(tr("onboarding.step5.consent_checkbox"), card)
            self.consent_checkbox.setChecked(True)
            self.consent_checkbox.setStyleSheet("font-weight: 600; color: #F4F2FA; background: transparent;")
            layout.addWidget(self.consent_checkbox, alignment=Qt.AlignmentFlag.AlignCenter)

            self.retention_combo = QComboBox(card)
            self.retention_combo.setMinimumWidth(240)
            for days, key in (
                (30, "settings.clipboard.retention_30d"),
                (7, "settings.clipboard.retention_7d"),
                (90, "settings.clipboard.retention_90d"),
                (0, "settings.clipboard.retention_never"),
            ):
                self.retention_combo.addItem(tr(key), days)
            layout.addWidget(self.retention_combo, alignment=Qt.AlignmentFlag.AlignCenter)

        return card

    def _on_lang_changed(self, _idx: int) -> None:
        code = self.lang_combo.currentData()
        if code:
            self.clipboard_manager.settings.language = code
            self.clipboard_manager.settings.language_manually_selected = True
            LocalizationManager.instance().set_language(code)
            self.setWindowTitle(tr("onboarding.window_title"))
            self.skip_btn.setText(tr("onboarding.skip"))
            self._rebuild_screens()

    def _jump_to_consent(self) -> None:
        self.stack.setCurrentIndex(4)  # Step 5 (Consent screen is mandatory before capture)
        self._update_nav_buttons()

    def _go_back(self) -> None:
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
            self._update_nav_buttons()

    def _go_next(self) -> None:
        idx = self.stack.currentIndex()
        if idx < 5:
            self.stack.setCurrentIndex(idx + 1)
            self._update_nav_buttons()
        else:
            self._finish_onboarding()

    def _update_nav_buttons(self) -> None:
        idx = self.stack.currentIndex()
        self.step_indicator.setText(f"{idx + 1} / 6")
        self.back_btn.setVisible(idx > 0)
        self.skip_btn.setVisible(idx < 4)
        self.next_btn.setText(tr("onboarding.finish") if idx == 5 else tr("onboarding.next"))

    def _finish_onboarding(self) -> None:
        consent = True
        if self.consent_checkbox is not None:
            consent = self.consent_checkbox.isChecked()
        if self.retention_combo is not None:
            self.clipboard_manager.settings.retention_days = int(
                self.retention_combo.currentData() or 30
            )

        self.clipboard_manager.settings.onboarding_completed = True
        self.clipboard_manager.settings.monitoring_consent_given = consent
        self.clipboard_manager.settings.monitoring_enabled = consent
        self.storage.save_settings(self.clipboard_manager.settings)
        self.clipboard_manager.initialize_monitoring()
        self.accept()
