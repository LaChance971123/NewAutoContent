import json
import random
from pathlib import Path
from PySide6 import QtWidgets, QtCore

THEME_PATH = Path(__file__).parent / "PyOneDark_GUI_Core" / "gui" / "themes" / "default.json"

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoContent")
        self._apply_theme()
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.left_scroll = QtWidgets.QScrollArea()
        self.left_scroll.setWidgetResizable(True)
        self.left_widget = QtWidgets.QWidget()
        self.left_scroll.setWidget(self.left_widget)
        self.left_layout = QtWidgets.QVBoxLayout(self.left_widget)
        self.left_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self.left_scroll)

        self.right_panel = QtWidgets.QFrame()
        self.right_layout = QtWidgets.QVBoxLayout(self.right_panel)
        self.preview = QtWidgets.QLabel("Video Preview")
        self.preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.right_layout.addWidget(self.preview)
        layout.addWidget(self.right_panel)

        self._build_left()
        self.reset_form()

    # ----- UI helpers -----
    def _apply_theme(self):
        if THEME_PATH.exists():
            theme = json.loads(THEME_PATH.read_text())
            colors = theme.get("app_color", {})
            bg = colors.get("bg_one", "#2c313c")
            fg = colors.get("text_foreground", "#ffffff")
            self.setStyleSheet(f"background:{bg};color:{fg};")

    def _build_left(self):
        self.script_edit = QtWidgets.QLineEdit()
        self.script_edit.setPlaceholderText("Upload or generate script...")
        self.script_edit.setToolTip("Enter or load the script text.")
        self.left_layout.addWidget(self.script_edit)

        self.voice_combo = QtWidgets.QComboBox()
        self.voice_combo.addItems(["Alice", "Bob", "Robot"])
        self.voice_combo.setToolTip("Select the narrator voice.")
        self.left_layout.addWidget(self.voice_combo)

        self.subtitle_combo = QtWidgets.QComboBox()
        self.subtitle_combo.addItems(["karaoke", "progressive", "simple"])
        self.subtitle_combo.setToolTip("Choose subtitle style.")
        self.left_layout.addWidget(self.subtitle_combo)

        self.bg_combo = QtWidgets.QComboBox()
        self.bg_combo.addItems(["Default", "Minecraft", "City"])
        self.bg_combo.setToolTip("Select background style.")
        self.left_layout.addWidget(self.bg_combo)

        btn_row = QtWidgets.QHBoxLayout()
        self.surprise_btn = QtWidgets.QPushButton("Surprise Me")
        self.surprise_btn.setToolTip("Randomize settings")
        self.surprise_btn.clicked.connect(self.surprise_me)
        self.reset_btn = QtWidgets.QPushButton("Reset")
        self.reset_btn.setToolTip("Reset form")
        self.reset_btn.clicked.connect(self.reset_form)
        btn_row.addWidget(self.surprise_btn)
        btn_row.addWidget(self.reset_btn)
        self.left_layout.addLayout(btn_row)

        self.create_btn = QtWidgets.QPushButton("Create Content")
        self.create_btn.setToolTip("Start generating the video")
        self.left_layout.addWidget(self.create_btn)
        self.left_layout.addStretch()

    # ----- Actions -----
    def surprise_me(self):
        for combo in (self.voice_combo, self.subtitle_combo, self.bg_combo):
            if combo.count():
                combo.setCurrentIndex(random.randrange(combo.count()))

    def reset_form(self):
        self.script_edit.clear()
        for combo in (self.voice_combo, self.subtitle_combo, self.bg_combo):
            combo.setCurrentIndex(0)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    win = MainWindow()
    win.show()
    app.exec()
