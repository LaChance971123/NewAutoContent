import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

GUI_DIR = Path(__file__).parent / "PyOneDark_GUI_Core"
sys.path.insert(0, str(GUI_DIR))

from qt_core import *
from gui.core.json_settings import Settings
from gui.core.json_themes import Themes
from gui.core.functions import Functions
from gui.widgets import PyGrips


class FadeStatusBar(QStatusBar):
    """Status bar that fades messages in and out."""

    def __init__(self, theme: dict) -> None:
        super().__init__()
        self.setStyleSheet(
            f"background: {theme['dark_three']}; color: {theme['text_foreground']};"
        )
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity")
        self._anim.setDuration(300)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)

    def show_message(self, text: str, timeout: int = 3000) -> None:
        self.showMessage(text)
        self._effect.setOpacity(0)
        self._anim.stop()
        self._anim.setStartValue(0)
        self._anim.setEndValue(1)
        self._anim.start()
        self._timer.start(timeout)

    def _fade_out(self) -> None:
        self._anim.stop()
        self._anim.setStartValue(1)
        self._anim.setEndValue(0)
        self._anim.start()


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""

    def __init__(self) -> None:
        super().__init__()
        theme_path = GUI_DIR / "gui/themes/default.json"
        if theme_path.exists():
            Themes.settings_path = str(theme_path)
            self.themes = Themes().items
        else:
            print("[\u26a0] Theme file not found, using fallback colors")
            self.themes = {
                "app_color": {
                    "dark_one": "#1C1F22",
                    "dark_two": "#0E1012",
                    "dark_three": "#2E3338",
                    "dark_four": "#292D31",
                    "bg_one": "#0E1012",
                    "bg_two": "#1C1F22",
                    "bg_three": "#292D31",
                    "icon_color": "#F5F7FA",
                    "icon_hover": "#FFFFFF",
                    "icon_pressed": "#377DFF",
                    "icon_active": "#377DFF",
                    "context_color": "#377DFF",
                    "context_hover": "#4A8BFF",
                    "context_pressed": "#2554CE",
                    "text_title": "#F5F7FA",
                    "text_foreground": "#F5F7FA",
                    "text_description": "#F5F7FA",
                    "text_active": "#F5F7FA",
                    "white": "#F5F7FA",
                    "pink": "#ff007f",
                    "green": "#2ECC71",
                    "red": "#ff5555",
                    "yellow": "#f1fa8c",
                }
            }
        self.settings = Settings().items

        self.setup_ui()
        self.setup_sidebar()
        self.setup_pages()
        self.status_bar = FadeStatusBar(self.themes["app_color"])
        self.setStatusBar(self.status_bar)
        self.show()
        print("GUI started successfully")

    # ---------------------------------------------------------------
    def setup_ui(self) -> None:
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

        self.ui.left_column_frame.setMinimumWidth(0)
        self.ui.left_column_frame.setMaximumWidth(0)
        self.ui.right_column_frame.setMinimumWidth(0)
        self.ui.right_column_frame.setMaximumWidth(0)

    # ---------------------------------------------------------------
    def setup_sidebar(self) -> None:
        menus = [
            {
                "btn_icon": Functions.set_svg_icon("icon_home.svg"),
                "btn_id": "btn_home",
                "btn_text": "Home",
                "btn_tooltip": "Home page",
                "show_top": True,
                "is_active": True,
            },
            {
                "btn_icon": Functions.set_svg_icon("icon_settings.svg"),
                "btn_id": "btn_settings",
                "btn_text": "Settings",
                "btn_tooltip": "Application settings",
                "show_top": False,
                "is_active": False,
            },
            {
                "btn_icon": Functions.set_svg_icon("icon_info.svg"),
                "btn_id": "btn_help",
                "btn_text": "Help",
                "btn_tooltip": "Help and documentation",
                "show_top": False,
                "is_active": False,
            },
            {
                "btn_icon": Functions.set_svg_icon("icon_widgets.svg"),
                "btn_id": "btn_about",
                "btn_text": "About",
                "btn_tooltip": "About this app",
                "show_top": False,
                "is_active": False,
            },
        ]
        self.ui.left_menu.add_menus(menus)
        self.ui.left_menu.clicked.connect(self.handle_left_menu_clicked)

    # ---------------------------------------------------------------
    def setup_pages(self) -> None:
        from autocontent_gui.pages import (
            HomePageWidget,
            SettingsPageWidget,
            HelpPageWidget,
            AboutPageWidget,
        )

        self.ui.load_pages.load_pages(
            {
                "home": HomePageWidget,
                "settings": SettingsPageWidget,
                "help": HelpPageWidget,
                "about": AboutPageWidget,
            }
        )
        pages = self.ui.load_pages._widgets
        if "help" in pages:
            pages["help"].status_request.connect(self.show_status)
        if "settings" in pages:
            pages["settings"].status_request.connect(self.show_status)

    # ---------------------------------------------------------------
    def handle_left_menu_clicked(self, btn: QPushButton) -> None:
        mapping = {
            "btn_home": "home",
            "btn_settings": "settings",
            "btn_help": "help",
            "btn_about": "about",
        }
        page = mapping.get(btn.objectName())
        if page:
            self.ui.left_menu.select_only_one(btn.objectName())
            self.ui.load_pages.set_current(page)

    # ---------------------------------------------------------------
    def show_status(self, text: str, timeout: int = 3000) -> None:
        if hasattr(self, "status_bar"):
            self.status_bar.show_message(text, timeout)

    # ---------------------------------------------------------------
    def menu_released(self, btn: QPushButton) -> None:
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font_family = Settings().items["font"]["family"]
    app.setFont(QFont(font_family))
    window = MainWindow()
    sys.exit(app.exec())
