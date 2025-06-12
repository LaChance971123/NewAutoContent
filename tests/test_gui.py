import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6 import QtWidgets, QtTest
from main import MainWindow


def test_gui_basic():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    QtTest.QTest.qWait(100)
    assert win.create_btn.toolTip() != ""
    win.surprise_btn.click()
    QtTest.QTest.qWait(50)
    win.reset_btn.click()
    QtTest.QTest.qWait(50)
    win.close()
    app.quit()
