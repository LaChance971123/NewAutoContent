from qt_core import *

class HomePageWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.addWidget(QLabel("Script Input Placeholder"))
        layout.addWidget(QLabel("Subtitle/Voice Controls Placeholder"))
        layout.addStretch()

class BatchModePageWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        label = QLabel("Batch Mode (Coming Soon…)")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        layout.addStretch()

class SettingsPageWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.addWidget(QCheckBox("Option 1"))
        layout.addWidget(QCheckBox("Option 2"))
        combo = QComboBox()
        combo.addItems(["Choice A", "Choice B"])
        layout.addWidget(combo)
        layout.addStretch()

class HelpPageWidget(QWidget):
    def __init__(self):
        super().__init__()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cont = QWidget()
        scroll.setWidget(cont)
        vbox = QVBoxLayout(cont)
        for i in range(3):
            lbl = QLabel(f"Help section {i+1} placeholder text…")
            lbl.setWordWrap(True)
            vbox.addWidget(lbl)
        vbox.addStretch()
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

