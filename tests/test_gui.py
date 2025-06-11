import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6 import QtWidgets, QtTest
from gui_pydracula.main_window import MainWindow


def test_gui_stress(tmp_path):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    QtTest.QTest.qWait(100)
    win.stack.setCurrentWidget(win.batch_page)
    QtTest.QTest.qWait(50)
    win.stack.setCurrentWidget(win.settings_page)
    QtTest.QTest.qWait(50)
    win.stack.setCurrentWidget(win.home_page)
    QtTest.QTest.qWait(50)
    win.home_page.adv_box.setChecked(True)
    QtTest.QTest.qWait(50)
    win.home_page.adv_box.setChecked(False)
    win.home_page.reset_form()
    QtTest.QTest.qWait(50)
    win.settings_page.top_check.toggle()
    QtTest.QTest.qWait(50)
    win.settings_page.top_check.toggle()
    QtTest.QTest.qWait(50)
    win.close()
    app.quit()
