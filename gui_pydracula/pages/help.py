from PySide6 import QtWidgets, QtCore


class HelpPage(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel(
            "<h2>Usage Tips</h2><ul>"
            "<li>Load or paste a script</li>"
            "<li>Select voice and background style</li>"
            "<li>Click Generate to run the pipeline</li>"
            "</ul>"
        )
        label.setWordWrap(True)
        layout.addWidget(label, alignment=QtCore.Qt.AlignTop)
