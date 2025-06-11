from PySide6 import QtWidgets, QtCore
from pipeline import __version__


class AboutPage(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(
            f"<h2>AutoContent {__version__}</h2>"
            "<p>Author: Michael LaChance</p>"
            "<p><a href='https://github.com'>GitHub</a></p>"
        )
        label.setOpenExternalLinks(True)
        label.setWordWrap(True)
        layout.addWidget(label, alignment=QtCore.Qt.AlignTop)
