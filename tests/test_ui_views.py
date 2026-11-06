"""
Automated UI Instantiation & Functional Interaction Test Suite using a lightweight PySide6 harness.
Verifies that MainWindow, Sidebar, HistoryView, CollectionsView, ColorsView, ImagesView,
SnippetsView, InsightsView, SettingsView, QuickPasteWindow, OnboardingDialog, and SystemTrayController
instantiate, wire signals, switch views, and switch languages (EN <-> RU) without errors.
"""

from pathlib import Path
import sys
import tempfile
from types import ModuleType
from typing import Any, Callable, List
import unittest

from app.paths import AppPaths
from core.clipboard_adapter import InMemoryClipboardAdapter
from core.clipboard_manager import ClipboardManager
from core.database import Database
from core.i18n import LocalizationManager
from core.storage import StorageRepository


def _install_pyside6_test_harness() -> None:
    """Install a lightweight headless PySide6 stub if native PySide6 is not installed in the Linux test container."""
    try:
        import PySide6  # noqa: F401
        return
    except ImportError:
        pass

    class _BoundSignal:
        def __init__(self) -> None:
            self._slots: List[Callable[..., Any]] = []

        def connect(self, slot: Callable[..., Any]) -> None:
            if slot not in self._slots:
                self._slots.append(slot)

        def disconnect(self, slot: Callable[..., Any] = None) -> None:
            if slot is None:
                self._slots.clear()
            elif slot in self._slots:
                self._slots.remove(slot)

        def emit(self, *args: Any, **kwargs: Any) -> None:
            for s in list(self._slots):
                try:
                    s(*args, **kwargs)
                except TypeError:
                    s()

    class Signal:
        def __init__(self, *_types: Any) -> None:
            self._name = ""

        def __set_name__(self, _owner: Any, name: str) -> None:
            self._name = f"_sig_{name}"

        def __get__(self, instance: Any, _owner: Any = None) -> Any:
            if instance is None:
                return self
            if not hasattr(instance, self._name):
                setattr(instance, self._name, _BoundSignal())
            return getattr(instance, self._name)

    class _DummyStyle:
        def unpolish(self, *_a: Any) -> None:
            pass

        def polish(self, *_a: Any) -> None:
            pass

    class QObject:
        def __init__(self, parent: Any = None) -> None:
            self._parent = parent
            self._props: dict[str, Any] = {}
            self._signals_blocked = False

        def setObjectName(self, name: str) -> None:
            self._obj_name = name

        def setProperty(self, k: str, v: Any) -> None:
            self._props[k] = v

        def property(self, k: str) -> Any:
            return self._props.get(k)

        def blockSignals(self, b: bool) -> None:
            self._signals_blocked = b

        def deleteLater(self) -> None:
            pass

        def style(self) -> _DummyStyle:
            return _DummyStyle()

    class QWidget(QObject):
        def __init__(self, parent: Any = None) -> None:
            super().__init__(parent)
            self._visible = True
            self._w = 1280
            self._h = 820
            self._title = ""

        def setWindowTitle(self, t: str) -> None:
            self._title = t

        def windowTitle(self) -> str:
            return self._title

        def setFixedSize(self, w: int, h: int) -> None:
            self._w, self._h = w, h

        def setMinimumSize(self, w: int, h: int) -> None:
            pass

        def resize(self, w: int, h: int) -> None:
            self._w, self._h = w, h

        def setFixedWidth(self, w: int) -> None:
            self._w = w

        def setMaximumWidth(self, w: int) -> None:
            pass

        def setMinimumWidth(self, w: int) -> None:
            pass

        def setFixedHeight(self, h: int) -> None:
            self._h = h

        def setMinimumHeight(self, h: int) -> None:
            pass

        def setMaximumHeight(self, h: int) -> None:
            pass

        def width(self) -> int:
            return self._w

        def height(self) -> int:
            return self._h

        def setStyleSheet(self, _s: str) -> None:
            pass

        def setCursor(self, *_a: Any) -> None:
            pass

        def setToolTip(self, *_a: Any) -> None:
            pass

        def setWindowFlags(self, *_a: Any) -> None:
            pass

        def setAttribute(self, *_a: Any) -> None:
            pass

        def setGraphicsEffect(self, *_a: Any) -> None:
            pass

        def setWindowIcon(self, *_a: Any) -> None:
            pass

        def show(self) -> None:
            self._visible = True

        def showNormal(self) -> None:
            self._visible = True

        def hide(self) -> None:
            self._visible = False

        def close(self) -> None:
            self._visible = False

        def isVisible(self) -> bool:
            return self._visible

        def isMinimized(self) -> bool:
            return False

        def setVisible(self, v: bool) -> None:
            self._visible = v

        def raise_(self) -> None:
            pass

        def activateWindow(self) -> None:
            pass

        def adjustSize(self) -> None:
            pass

        def move(self, *_a: Any) -> None:
            pass

        def update(self) -> None:
            pass

        def parentWidget(self) -> Any:
            return self._parent

        def winId(self) -> int:
            return 10101

        def setFocus(self) -> None:
            pass

    class QFrame(QWidget):
        class Shape:
            NoFrame = 0

        def setFrameShape(self, *_a: Any) -> None:
            pass

    class QMainWindow(QWidget):
        def setCentralWidget(self, w: Any) -> None:
            self._central = w

    class QDialog(QWidget):
        class DialogCode:
            Accepted = 1
            Rejected = 0

        def setModal(self, _m: bool) -> None:
            pass

        def accept(self) -> None:
            pass

        def reject(self) -> None:
            pass

        def exec(self) -> int:
            return 1

    class QLabel(QWidget):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__()
            self._text = args[0] if args and isinstance(args[0], str) else ""

        def setText(self, t: str) -> None:
            self._text = t

        def text(self) -> str:
            return self._text

        def setAlignment(self, *_a: Any) -> None:
            pass

        def setWordWrap(self, *_a: Any) -> None:
            pass

        def setPixmap(self, *_a: Any) -> None:
            pass

    class QPushButton(QWidget):
        clicked = Signal(bool)

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__()
            self._text = args[0] if args and isinstance(args[0], str) else ""

        def setText(self, t: str) -> None:
            self._text = t

        def text(self) -> str:
            return self._text

        def setIcon(self, *_a: Any) -> None:
            pass

        def setIconSize(self, *_a: Any) -> None:
            pass

    class QCheckBox(QWidget):
        toggled = Signal(bool)

        def __init__(self, text: str = "", parent: Any = None) -> None:
            super().__init__(parent)
            self._checked = False

        def setChecked(self, c: bool) -> None:
            self._checked = c

        def isChecked(self) -> bool:
            return self._checked

    class QLineEdit(QWidget):
        textChanged = Signal(str)
        editingFinished = Signal()

        def __init__(self, *args: Any) -> None:
            super().__init__()
            self._text = args[0] if args and isinstance(args[0], str) else ""

        def setText(self, t: str) -> None:
            self._text = t
            if not self._signals_blocked:
                self.textChanged.emit(t)

        def text(self) -> str:
            return self._text

        def clear(self) -> None:
            self.setText("")

        def selectAll(self) -> None:
            pass

        def setPlaceholderText(self, _p: str) -> None:
            pass

        def setClearButtonEnabled(self, _b: bool) -> None:
            pass

    class QPlainTextEdit(QWidget):
        def __init__(self, text: str = "", parent: Any = None) -> None:
            super().__init__(parent)
            self._text = text

        def toPlainText(self) -> str:
            return self._text

    class QTextBrowser(QWidget):
        def setHtml(self, _h: str) -> None:
            pass

        def setPlainText(self, _t: str) -> None:
            pass

    class QComboBox(QWidget):
        currentIndexChanged = Signal(int)

        def __init__(self, parent: Any = None) -> None:
            super().__init__(parent)
            self._items: List[tuple[str, Any]] = []
            self._idx = 0

        def addItem(self, label: str, data: Any = None) -> None:
            self._items.append((label, data))

        def clear(self) -> None:
            self._items.clear()
            self._idx = 0

        def setCurrentIndex(self, idx: int) -> None:
            self._idx = idx
            if not self._signals_blocked:
                self.currentIndexChanged.emit(idx)

        def currentData(self) -> Any:
            if 0 <= self._idx < len(self._items):
                return self._items[self._idx][1]
            return None

    class QSpinBox(QWidget):
        valueChanged = Signal(int)

        def setRange(self, _a: int, _b: int) -> None:
            pass

        def setSingleStep(self, _s: int) -> None:
            pass

        def setValue(self, _v: int) -> None:
            pass

    class _LayoutItem:
        def __init__(self, w: Any = None, l: Any = None) -> None:
            self._w = w
            self._l = l

        def widget(self) -> Any:
            return self._w

        def layout(self) -> Any:
            return self._l

    class _BaseLayout(QObject):
        def __init__(self, parent: Any = None) -> None:
            super().__init__(parent)
            self._children: List[_LayoutItem] = []

        def setContentsMargins(self, *_a: Any) -> None:
            pass

        def setSpacing(self, *_a: Any) -> None:
            pass

        def setAlignment(self, *_a: Any) -> None:
            pass

        def addSpacing(self, *_a: Any) -> None:
            pass

        def addStretch(self, *_a: Any) -> None:
            pass

        def addWidget(self, w: Any, *_a: Any, **_k: Any) -> None:
            self._children.append(_LayoutItem(w=w))

        def addLayout(self, l: Any, *_a: Any, **_k: Any) -> None:
            self._children.append(_LayoutItem(l=l))

        def addRow(self, *_a: Any) -> None:
            pass

        def count(self) -> int:
            return len(self._children)

        def takeAt(self, idx: int) -> _LayoutItem:
            return self._children.pop(idx)

    class QVBoxLayout(_BaseLayout):
        pass

    class QHBoxLayout(_BaseLayout):
        pass

    class QGridLayout(_BaseLayout):
        pass

    class QFormLayout(_BaseLayout):
        pass

    class QScrollArea(QFrame):
        def setWidgetResizable(self, _b: bool) -> None:
            pass

        def setWidget(self, w: Any) -> None:
            self._w = w

    class QStackedWidget(QWidget):
        def __init__(self, parent: Any = None) -> None:
            super().__init__(parent)
            self._pages: List[QWidget] = []
            self._idx = 0

        def addWidget(self, w: QWidget) -> None:
            self._pages.append(w)

        def removeWidget(self, w: QWidget) -> None:
            if w in self._pages:
                self._pages.remove(w)

        def widget(self, i: int) -> QWidget:
            return self._pages[i]

        def count(self) -> int:
            return len(self._pages)

        def currentIndex(self) -> int:
            return self._idx

        def setCurrentIndex(self, i: int) -> None:
            self._idx = i

        def setCurrentWidget(self, w: QWidget) -> None:
            if w in self._pages:
                self._idx = self._pages.index(w)

        def currentWidget(self) -> Any:
            return self._pages[self._idx] if self._pages else None

    class QTabWidget(QWidget):
        def __init__(self, parent: Any = None) -> None:
            super().__init__(parent)
            self._tabs: List[QWidget] = []
            self._idx = 0

        def addTab(self, w: QWidget, _title: str) -> None:
            self._tabs.append(w)

        def clear(self) -> None:
            self._tabs.clear()

        def count(self) -> int:
            return len(self._tabs)

        def currentIndex(self) -> int:
            return self._idx

        def setCurrentIndex(self, i: int) -> None:
            self._idx = i

    class QListWidgetItem:
        def __init__(self, text: str = "") -> None:
            self._text = text
            self._data: dict[Any, Any] = {}

        def text(self) -> str:
            return self._text

        def setData(self, role: Any, val: Any) -> None:
            self._data[role] = val

        def setIcon(self, *_a: Any) -> None:
            pass

    class QListWidget(QWidget):
        currentRowChanged = Signal(int)
        itemDoubleClicked = Signal(object)

        def __init__(self, parent: Any = None) -> None:
            super().__init__(parent)
            self._items: List[Any] = []
            self._row = 0

        def addItem(self, item: Any) -> None:
            self._items.append(item if isinstance(item, QListWidgetItem) else QListWidgetItem(str(item)))

        def clear(self) -> None:
            self._items.clear()

        def count(self) -> int:
            return len(self._items)

        def currentRow(self) -> int:
            return self._row

        def setCurrentRow(self, r: int) -> None:
            self._row = r
            if not self._signals_blocked:
                self.currentRowChanged.emit(r)

        def currentItem(self) -> Any:
            return self._items[self._row] if 0 <= self._row < len(self._items) else None

        def row(self, item: Any) -> int:
            return self._items.index(item)

        def takeItem(self, r: int) -> Any:
            return self._items.pop(r)

    class QTreeWidgetItem:
        def __init__(self, parent: Any = None, labels: Any = None) -> None:
            pass

    class QTreeWidget(QWidget):
        def setHeaderHidden(self, _b: bool) -> None:
            pass

        def invisibleRootItem(self) -> QTreeWidgetItem:
            return QTreeWidgetItem()

        def expandToDepth(self, _d: int) -> None:
            pass

    class QMenu(QWidget):
        def addAction(self, *_a: Any) -> None:
            pass

        def addSeparator(self) -> None:
            pass

        def addMenu(self, _title: str) -> "QMenu":
            return QMenu(self)

        def exec(self, *_a: Any) -> None:
            pass

    class QSystemTrayIcon(QObject):
        class ActivationReason:
            Trigger = 1
            DoubleClick = 2

        activated = Signal(int)

        def __init__(self, *_a: Any) -> None:
            super().__init__()

        @staticmethod
        def isSystemTrayAvailable() -> bool:
            return True

        def setToolTip(self, _t: str) -> None:
            pass

        def setContextMenu(self, _m: Any) -> None:
            pass

        def show(self) -> None:
            pass

        def hide(self) -> None:
            pass

    class QGraphicsOpacityEffect(QObject):
        def opacity(self) -> float:
            return 1.0

        def setOpacity(self, _v: float) -> None:
            pass

    class QApplication(QObject):
        _inst: Any = None

        def __init__(self, _argv: Any = None) -> None:
            super().__init__()
            QApplication._inst = self

        @classmethod
        def instance(cls) -> Any:
            return cls._inst

        def setStyleSheet(self, _s: str) -> None:
            pass

        def quit(self) -> None:
            pass

    class Qt:
        class AlignmentFlag:
            AlignCenter = 1
            AlignTop = 2
            AlignLeft = 4

        class WindowType:
            SubWindow = 1
            FramelessWindowHint = 2
            Tool = 4
            WindowStaysOnTopHint = 8

        class WidgetAttribute:
            WA_ShowWithoutActivating = 1
            WA_TranslucentBackground = 2

        class CursorShape:
            PointingHandCursor = 1

        class AspectRatioMode:
            KeepAspectRatio = 1

        class TransformationMode:
            SmoothTransformation = 1

        class MouseButton:
            LeftButton = 1

        class ItemDataRole:
            UserRole = 32

        class PenStyle:
            NoPen = 0

        class Key:
            Key_Escape = 1
            Key_Return = 2
            Key_Enter = 3
            Key_Down = 4
            Key_Up = 5
            Key_F = 6

        class KeyboardModifier:
            ControlModifier = 1

    class QTimer(QObject):
        timeout = Signal()

        def setSingleShot(self, _b: bool) -> None:
            pass

        def setInterval(self, _i: int) -> None:
            pass

        def start(self, *_a: Any) -> None:
            pass

    class QPropertyAnimation(QObject):
        finished = Signal()

        def __init__(self, *_a: Any) -> None:
            super().__init__()

        def setDuration(self, _d: int) -> None:
            pass

        def setEasingCurve(self, _c: Any) -> None:
            pass

        def setStartValue(self, _v: Any) -> None:
            pass

        def setEndValue(self, _v: Any) -> None:
            pass

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

    class QEasingCurve:
        class Type:
            OutCubic = 1

    class QSize:
        def __init__(self, w: int = 0, h: int = 0) -> None:
            pass

    class QRectF:
        def __init__(self, *_a: Any) -> None:
            pass

    class QByteArray(bytes):
        pass

    class QPixmap:
        def __init__(self, *_a: Any) -> None:
            pass

        def loadFromData(self, _b: bytes) -> None:
            pass

        def scaled(self, *_a: Any) -> "QPixmap":
            return self

    class QIcon:
        def __init__(self, *_a: Any) -> None:
            pass

        def pixmap(self, *_a: Any) -> QPixmap:
            return QPixmap()

    class QAction(QObject):
        triggered = Signal(bool)

        def __init__(self, text: str = "", parent: Any = None) -> None:
            super().__init__(parent)
            self._text = text

        def setText(self, t: str) -> None:
            self._text = t

    class QShortcut(QObject):
        activated = Signal()

        def __init__(self, *_a: Any) -> None:
            super().__init__()

    class QKeySequence:
        def __init__(self, *_a: Any) -> None:
            pass

    class QCursor:
        @staticmethod
        def pos() -> Any:
            class _P:
                def x(self) -> int:
                    return 500

                def y(self) -> int:
                    return 400

            return _P()

    class QGuiApplication:
        @staticmethod
        def screenAt(_p: Any) -> None:
            return None

        @staticmethod
        def primaryScreen() -> None:
            return None

    class QColor:
        def __init__(self, *_a: Any) -> None:
            pass

    class QFont:
        def __init__(self, *_a: Any) -> None:
            pass

    class QPainter:
        class RenderHint:
            Antialiasing = 1

        def __init__(self, *_a: Any) -> None:
            pass

        def setRenderHint(self, *_a: Any) -> None:
            pass

        def end(self) -> None:
            pass

    class QMessageBox(QDialog):
        class StandardButton:
            Yes = 1
            No = 2

        class ButtonRole:
            AcceptRole = 1
            DestructiveRole = 2
            RejectRole = 3

    class QFileDialog:
        @staticmethod
        def getSaveFileName(*_a: Any) -> tuple[str, str]:
            return "", ""

        @staticmethod
        def getOpenFileName(*_a: Any) -> tuple[str, str]:
            return "", ""

    qt_pkg = ModuleType("PySide6")
    qt_core = ModuleType("PySide6.QtCore")
    qt_gui = ModuleType("PySide6.QtGui")
    qt_widgets = ModuleType("PySide6.QtWidgets")

    for name, obj in {
        "Qt": Qt,
        "Signal": Signal,
        "QObject": QObject,
        "QTimer": QTimer,
        "QPropertyAnimation": QPropertyAnimation,
        "QEasingCurve": QEasingCurve,
        "QSize": QSize,
        "QRectF": QRectF,
        "QByteArray": QByteArray,
    }.items():
        setattr(qt_core, name, obj)

    for name, obj in {
        "QIcon": QIcon,
        "QPixmap": QPixmap,
        "QAction": QAction,
        "QShortcut": QShortcut,
        "QKeySequence": QKeySequence,
        "QCursor": QCursor,
        "QGuiApplication": QGuiApplication,
        "QColor": QColor,
        "QFont": QFont,
        "QPainter": QPainter,
        "QPaintEvent": object,
        "QMouseEvent": object,
        "QKeyEvent": object,
        "QCloseEvent": object,
    }.items():
        setattr(qt_gui, name, obj)

    for name, obj in {
        "QApplication": QApplication,
        "QWidget": QWidget,
        "QFrame": QFrame,
        "QMainWindow": QMainWindow,
        "QDialog": QDialog,
        "QLabel": QLabel,
        "QPushButton": QPushButton,
        "QCheckBox": QCheckBox,
        "QLineEdit": QLineEdit,
        "QPlainTextEdit": QPlainTextEdit,
        "QTextBrowser": QTextBrowser,
        "QComboBox": QComboBox,
        "QSpinBox": QSpinBox,
        "QVBoxLayout": QVBoxLayout,
        "QHBoxLayout": QHBoxLayout,
        "QGridLayout": QGridLayout,
        "QFormLayout": QFormLayout,
        "QScrollArea": QScrollArea,
        "QStackedWidget": QStackedWidget,
        "QTabWidget": QTabWidget,
        "QListWidget": QListWidget,
        "QListWidgetItem": QListWidgetItem,
        "QTreeWidget": QTreeWidget,
        "QTreeWidgetItem": QTreeWidgetItem,
        "QMenu": QMenu,
        "QSystemTrayIcon": QSystemTrayIcon,
        "QGraphicsOpacityEffect": QGraphicsOpacityEffect,
        "QMessageBox": QMessageBox,
        "QFileDialog": QFileDialog,
    }.items():
        setattr(qt_widgets, name, obj)

    sys.modules["PySide6"] = qt_pkg
    sys.modules["PySide6.QtCore"] = qt_core
    sys.modules["PySide6.QtGui"] = qt_gui
    sys.modules["PySide6.QtWidgets"] = qt_widgets


_install_pyside6_test_harness()


class TestUIViewsAndInteractions(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.tmp_dir.name)
        AppPaths.set_custom_data_dir(self.base_path)
        self.storage = StorageRepository(Database(self.base_path / "ui_test.db"))
        self.adapter = InMemoryClipboardAdapter()
        self.manager = ClipboardManager(storage=self.storage, adapter=self.adapter)
        self.manager.set_monitoring_enabled(True)

    def tearDown(self) -> None:
        self.manager.monitor.stop()
        AppPaths.set_custom_data_dir(None)
        self.tmp_dir.cleanup()

    def test_main_window_and_all_views_interaction(self) -> None:
        from PySide6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        from ui.onboarding import OnboardingDialog

        _app = QApplication([])
        wizard = OnboardingDialog(self.manager, detected_language="ru")
        wizard._finish_onboarding()
        self.assertTrue(self.manager.settings.onboarding_completed)

        win = MainWindow(self.manager)

        # Simulate copying diverse items and verify UI updates across all sections
        self.adapter.simulate_user_copy(text="#A78BFA")
        self.adapter.simulate_user_copy(text="https://github.com/kemorovv/SNIPLY")
        self.adapter.simulate_user_copy(text='{"status": "ok", "count": 42}')
        self.adapter.simulate_user_copy(text="def hello_world():\n    return 'SNIPLY'")

        for section in (
            "all_clips",
            "pinned",
            "favorites",
            "collections",
            "colors",
            "images",
            "snippets",
            "insights",
            "settings",
        ):
            win.sidebar.select_section(section)

        # Summon Quick Paste and verify entries loaded
        win.summon_quick_paste()
        self.assertGreaterEqual(win.quick_paste.list_widget.count(), 4)

        # Inspect each clip type in InspectorPanel
        for clip in self.storage.query_clips():
            win.inspector.inspect_clip(clip)

        # Live switch language between English and Russian while UI is active
        LocalizationManager.instance().set_language("ru")
        self.assertEqual(LocalizationManager.instance().language, "ru")
        LocalizationManager.instance().set_language("en")
        self.assertEqual(LocalizationManager.instance().language, "en")

        win.quit_application()


if __name__ == "__main__":
    unittest.main()
