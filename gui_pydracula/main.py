from PySide6 import QtWidgets, QtGui, QtCore
from .main_window import MainWindow

def main() -> None:
    app = QtWidgets.QApplication([])
    for fam in ["Inter", "Roboto", "Segoe UI"]:
        font = QtGui.QFont(fam)
        if QtGui.QFontInfo(font).family() == fam:
            app.setFont(font)
            break
    app.setStyleSheet(
        "QPushButton{border-radius:8px;padding:6px;}"
        "QPushButton:hover{background:rgba(59,130,246,80);}"
        "QPushButton:pressed{background:rgba(59,130,246,150);}"
    )
    pix = QtGui.QPixmap("gui/images/images/PyDracula.png")
    splash = QtWidgets.QSplashScreen(pix, QtCore.Qt.WindowType.WindowStaysOnTopHint)
    splash.showMessage(
        "AI-Powered Storytelling, Refined.",
        QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignHCenter,
        QtGui.QColor("white"),
    )
    effect = QtWidgets.QGraphicsOpacityEffect(splash)
    splash.setGraphicsEffect(effect)
    anim = QtCore.QPropertyAnimation(effect, b"opacity")
    anim.setDuration(800)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    splash.show()
    anim.start()
    QtWidgets.QApplication.processEvents()
    QtCore.QTimer.singleShot(1500, splash.close)
    win = MainWindow()
    win.show()
    app.exec()

if __name__ == "__main__":
    main()
