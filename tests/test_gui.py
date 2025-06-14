import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6 import QtWidgets, QtTest  # type: ignore
except Exception:  # pragma: no cover - Qt may be missing libs
    QtWidgets = None

try:
    from main import MainWindow  # type: ignore
except Exception:  # pragma: no cover - skip if Qt deps missing
    MainWindow = None


def test_gui_basic():
    if QtWidgets is None or MainWindow is None:
        pytest.skip("GUI dependencies missing")
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    QtTest.QTest.qWait(100)
    assert hasattr(win.ui, "left_menu")
    assert win.ui.load_pages.pages.count() >= 4
    win.close()
    app.quit()
