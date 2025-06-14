import sys
import json
from pathlib import Path

GUI_DIR = Path(__file__).parent / "PyOneDark_GUI_Core"
sys.path.insert(0, str(GUI_DIR))

from qt_core import *
from gui.core.json_settings import Settings
from gui.core.json_themes import Themes
from gui.widgets import PyPushButton, PyGrips

# Pipeline imports retained for future use
from pipeline import generator
from pipeline.pipeline import VideoPipeline
from pipeline.config import Config
from pipeline.helpers import sanitize_name


class SettingsManager:
    """Load and save persistent settings"""

    def __init__(self):
        self.path = Path(Settings.settings_path)
        self.load()

    def load(self):
        try:
            self.data = json.loads(self.path.read_text())
        except Exception:
            self.data = {}

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings().items
        Themes.settings_path = str(
            GUI_DIR / f"gui/themes/{self.settings['theme_name']}.json"
        )
        self.themes = Themes().items
        self.app_settings = SettingsManager()

        self.setup_ui()
        self.build_sidebar()
        self.build_home_page()
        self.build_settings_page()
        self.build_help_page()
        self.show()

    # ------------------------------------------------------------------
    def setup_ui(self):
        from gui.uis.windows.main_window.ui_main import UI_MainWindow

        self.ui = UI_MainWindow()
        self.ui.setup_ui(self)

        if self.settings["custom_title_bar"]:
            self.setWindowFlag(Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle(self.settings["app_name"])

        if self.settings["custom_title_bar"]:
            self.left_grip = PyGrips(self, "left", True)
            self.right_grip = PyGrips(self, "right", True)
            self.top_grip = PyGrips(self, "top", True)
            self.bottom_grip = PyGrips(self, "bottom", True)
            self.top_left_grip = PyGrips(self, "top_left", True)
            self.top_right_grip = PyGrips(self, "top_right", True)
            self.bottom_left_grip = PyGrips(self, "bottom_left", True)
            self.bottom_right_grip = PyGrips(self, "bottom_right", True)

        # Clear existing left menu widgets
        lm = self.ui.left_menu_frame.layout()
        while lm.count():
            item = lm.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.menu_container = QFrame()
        self.sidebar_layout = QVBoxLayout(self.menu_container)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        lm.addWidget(self.menu_container)

        # Hide columns used by the original template
        self.ui.left_column_frame.setMinimumWidth(0)
        self.ui.left_column_frame.setMaximumWidth(0)
        self.ui.right_column_frame.setMinimumWidth(0)
        self.ui.right_column_frame.setMaximumWidth(0)

    # ------------------------------------------------------------------
    def build_sidebar(self):
        theme = self.themes["app_color"]
        btn_args = dict(
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["dark_three"],
            bg_color_hover=theme["context_hover"],
            bg_color_pressed=theme["context_pressed"],
        )

        self.home_btn = PyPushButton(text="Home", **btn_args)
        self.settings_btn = PyPushButton(text="Settings", **btn_args)
        self.help_btn = PyPushButton(text="Help", **btn_args)

        self.home_btn.clicked.connect(lambda: self.switch_page(0))
        self.settings_btn.clicked.connect(lambda: self.switch_page(1))
        self.help_btn.clicked.connect(lambda: self.switch_page(2))

        self.sidebar_layout.addWidget(self.home_btn)
        self.sidebar_layout.addWidget(self.settings_btn)
        self.sidebar_layout.addWidget(self.help_btn)
        self.sidebar_layout.addStretch()

    # ------------------------------------------------------------------
    def switch_page(self, index: int):
        stack = self.ui.load_pages.pages
        if index != stack.currentIndex():
            stack.setCurrentIndex(index)

    # Utility ------------------------------------------------------------
    def clear_layout(self, layout: QLayout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    # ------------------------------------------------------------------
    def build_home_page(self):
        self.clear_layout(self.ui.load_pages.page_1_layout)
        label = QLabel("\ud83d\udd27 Rebuilding GUI...")
        label.setAlignment(Qt.AlignCenter)
        self.ui.load_pages.page_1_layout.addWidget(label)

    # ------------------------------------------------------------------
    def build_settings_page(self):
        self.clear_layout(self.ui.load_pages.page_2_layout)
        label = QLabel("\u2699\ufe0f Settings under construction")
        label.setAlignment(Qt.AlignCenter)
        self.ui.load_pages.page_2_layout.addWidget(label)

    # ------------------------------------------------------------------
    def build_help_page(self):
        self.clear_layout(self.ui.load_pages.page_3_layout)
        label = QLabel("\ud83d\udcda Help content coming soon")
        label.setAlignment(Qt.AlignCenter)
        self.ui.load_pages.page_3_layout.addWidget(label)

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self.app_settings.save()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
