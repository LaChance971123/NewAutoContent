import sys
import random
from pathlib import Path

GUI_DIR = Path(__file__).parent / "PyOneDark_GUI_Core"
sys.path.insert(0, str(GUI_DIR))
BASE_DIR = Path(__file__).parent

from qt_core import *
from gui.core.json_settings import Settings
from gui.core.json_themes import Themes
from gui.core.functions import Functions
from gui.widgets import (
    PyPushButton,
    PyLineEdit,
    PyToggle,
    PyGrips,
)
from gui.uis.windows.main_window.ui_main import UI_MainWindow
from gui.uis.windows.main_window.functions_main_window import MainFunctions


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.settings = Settings().items
        Themes.settings_path = str(GUI_DIR / f"gui/themes/{self.settings['theme_name']}.json")
        self.themes = Themes().items
        self.setup_ui()
        self.build_controls()
        self.reset_form()
        self.show()

    # ------------------------------------------------------------------
    def setup_ui(self):
        self.ui = UI_MainWindow()
        self.ui.setup_ui(self)

        # Apply frameless window and title
        if self.settings["custom_title_bar"]:
            self.setWindowFlag(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle(self.settings["app_name"])

        # Add grips for resizing
        if self.settings["custom_title_bar"]:
            self.left_grip = PyGrips(self, "left", True)
            self.right_grip = PyGrips(self, "right", True)
            self.top_grip = PyGrips(self, "top", True)
            self.bottom_grip = PyGrips(self, "bottom", True)
            self.top_left_grip = PyGrips(self, "top_left", True)
            self.top_right_grip = PyGrips(self, "top_right", True)
            self.bottom_left_grip = PyGrips(self, "bottom_left", True)
            self.bottom_right_grip = PyGrips(self, "bottom_right", True)

        # Configure menus
        menus = [
            {
                "btn_icon": "icon_home.svg",
                "btn_id": "btn_home",
                "btn_text": "Home",
                "btn_tooltip": "Home page",
                "show_top": True,
                "is_active": True,
            }
        ]
        self.ui.left_menu.add_menus(menus)
        self.ui.left_menu.clicked.connect(self.menu_clicked)
        self.ui.left_menu.released.connect(self.menu_released)
        self.ui.title_bar.add_menus([])
        self.ui.title_bar.clicked.connect(self.menu_clicked)
        self.ui.title_bar.released.connect(self.menu_released)
        self.ui.title_bar.set_title(self.settings["app_name"])

        # Hide unused columns
        self.ui.left_column_frame.setMinimumWidth(0)
        self.ui.left_column_frame.setMaximumWidth(0)
        self.ui.right_column_frame.setMinimumWidth(0)
        self.ui.right_column_frame.setMaximumWidth(0)

        # Set home page
        MainFunctions.set_page(self, self.ui.load_pages.page_1)

    # ------------------------------------------------------------------
    def build_controls(self):
        theme = self.themes["app_color"]
        layout = self.ui.load_pages.controls_layout

        self.script_edit = PyLineEdit(
            place_holder_text="Script text...",
            bg_color=theme["dark_one"],
            bg_color_active=theme["dark_three"],
            selection_color=theme["white"],
            context_color=theme["context_color"],
            color=theme["text_foreground"],
        )
        self.script_edit.setToolTip("Enter or load a script")
        layout.addWidget(self.script_edit)

        btn_row = QHBoxLayout()
        self.upload_btn = PyPushButton(
            text="Upload",
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["dark_one"],
            bg_color_hover=theme["dark_three"],
            bg_color_pressed=theme["dark_four"],
        )
        self.upload_btn.setToolTip("Open text file")
        self.upload_btn.clicked.connect(self.upload_script)
        btn_row.addWidget(self.upload_btn)

        self.ai_btn = PyPushButton(
            text="Generate with AI",
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["dark_one"],
            bg_color_hover=theme["dark_three"],
            bg_color_pressed=theme["dark_four"],
        )
        self.ai_btn.setToolTip("Generate script using AI")
        btn_row.addWidget(self.ai_btn)

        self.reset_btn = PyPushButton(
            text="Reset",
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["dark_one"],
            bg_color_hover=theme["dark_three"],
            bg_color_pressed=theme["dark_four"],
        )
        self.reset_btn.setToolTip("Clear script")
        self.reset_btn.clicked.connect(self.reset_form)
        btn_row.addWidget(self.reset_btn)

        layout.addLayout(btn_row)

        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["Alice", "Drew", "Bob"])
        self.voice_combo.setToolTip("Select voice")
        layout.addWidget(self.voice_combo)

        self.subtitle_combo = QComboBox()
        self.subtitle_combo.addItems(["karaoke", "progressive", "simple"])
        self.subtitle_combo.setToolTip("Subtitle style")
        layout.addWidget(self.subtitle_combo)

        bg_row = QHBoxLayout()
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["Default", "City", "Minecraft"])
        self.bg_combo.setToolTip("Background style")
        bg_row.addWidget(self.bg_combo)

        self.surprise_btn = PyPushButton(
            text="Surprise Me",
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["dark_one"],
            bg_color_hover=theme["dark_three"],
            bg_color_pressed=theme["dark_four"],
        )
        self.surprise_btn.setToolTip("Randomize background")
        self.surprise_btn.clicked.connect(self.surprise_me)
        bg_row.addWidget(self.surprise_btn)
        layout.addLayout(bg_row)

        self.watermark_toggle = PyToggle(
            bg_color=theme["dark_two"],
            circle_color=theme["icon_color"],
            active_color=theme["context_color"],
        )
        self.watermark_toggle.setToolTip("Toggle watermark")
        layout.addWidget(self.watermark_toggle)

        self.create_btn = PyPushButton(
            text="Create Content",
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["context_color"],
            bg_color_hover=theme["context_hover"],
            bg_color_pressed=theme["context_pressed"],
        )
        self.create_btn.setToolTip("Generate the video")
        layout.addWidget(self.create_btn)
        layout.addStretch()

        # Preview placeholder
        preview_label = QLabel("Video Preview")
        preview_label.setAlignment(Qt.AlignCenter)
        self.ui.load_pages.preview_layout.addWidget(preview_label)

    # ------------------------------------------------------------------
    def menu_clicked(self):
        pass

    def menu_released(self):
        pass

    def upload_script(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Script", "", "Text Files (*.txt)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.script_edit.setText(f.read())

    def surprise_me(self):
        combos = [self.voice_combo, self.subtitle_combo, self.bg_combo]
        for combo in combos:
            if combo.count():
                combo.setCurrentIndex(random.randrange(combo.count()))

    def reset_form(self):
        self.script_edit.clear()
        for combo in (self.voice_combo, self.subtitle_combo, self.bg_combo):
            combo.setCurrentIndex(0)
        self.watermark_toggle.setChecked(False)

    # Resize grips
    def resizeEvent(self, event):
        if self.settings["custom_title_bar"]:
            self.left_grip.setGeometry(5, 10, 10, self.height())
            self.right_grip.setGeometry(self.width() - 15, 10, 10, self.height())
            self.top_grip.setGeometry(5, 5, self.width() - 10, 10)
            self.bottom_grip.setGeometry(5, self.height() - 15, self.width() - 10, 10)
            self.top_right_grip.setGeometry(self.width() - 20, 5, 15, 15)
            self.bottom_left_grip.setGeometry(5, self.height() - 20, 15, 15)
            self.bottom_right_grip.setGeometry(self.width() - 20, self.height() - 20, 15, 15)
        super().resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
