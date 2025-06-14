import sys
import os
import json
from pathlib import Path
from typing import Callable, Any

GUI_DIR = Path(__file__).parent / "PyOneDark_GUI_Core"
sys.path.insert(0, str(GUI_DIR))

from qt_core import *
from gui.core.json_settings import Settings
from gui.core.json_themes import Themes
from gui.core.functions import Functions
from gui.widgets import PyGrips

from pipeline import generator
from pipeline.pipeline import VideoPipeline
from pipeline.config import Config
from pipeline.helpers import sanitize_name


class SettingsManager:
    """Load and store global settings.json."""

    def __init__(self) -> None:
        self.path = Path(Settings.settings_path)
        self.load()

    def load(self) -> None:
        try:
            self.data = json.loads(self.path.read_text())
        except Exception:
            self.data = {}

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=4))


class WorkerThread(QThread):
    finished = Signal(object)
    failed = Signal(Exception)

    def __init__(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            result = self.func(*self.args, **self.kwargs)
        except Exception as e:  # pragma: no cover - runtime errors
            self.failed.emit(e)
        else:
            self.finished.emit(result)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        Themes.settings_path = str(GUI_DIR / "gui/themes/default.json")
        self.settings = Settings().items
        self.themes = Themes().items
        self.app_settings = SettingsManager()
        self._threads: list[WorkerThread] = []

        self.setup_ui()
        self.setup_sidebar()
        self.setup_pages()
        self.show()

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
            self.top_left_grip = PyGrips(self, "top_left", True)
            self.top_right_grip = PyGrips(self, "top_right", True)
            self.bottom_left_grip = PyGrips(self, "bottom_left", True)
            self.bottom_right_grip = PyGrips(self, "bottom_right", True)
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
                "btn_icon": Functions.set_svg_icon("icon_file.svg"),
                "btn_id": "btn_batch",
                "btn_text": "Batch",
                "btn_tooltip": "Batch mode",
                "show_top": True,
                "is_active": False,
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
                "btn_tooltip": "Help and info",
                "show_top": False,
                "is_active": False,
            },
        ]
        self.ui.left_menu.add_menus(menus)
        self.ui.left_menu.clicked.connect(self.handle_left_menu_clicked)
        self.ui.left_menu.released.connect(self.menu_released)
        self.ui.title_bar.add_menus([])
        self.ui.title_bar.clicked.connect(self.menu_clicked)
        self.ui.title_bar.released.connect(self.menu_released)

    # ---------------------------------------------------------------
    def setup_pages(self) -> None:
        from autocontent_gui.pages import (
            HomePageWidget,
            BatchModePageWidget,
            SettingsPageWidget,
            HelpPageWidget,
        )

        self.ui.load_pages.load_pages(
            {
                "home": HomePageWidget,
                "batch": BatchModePageWidget,
                "settings": SettingsPageWidget,
                "help": HelpPageWidget,
            }
        )
        self.home_page = self.ui.load_pages._widgets.get("home")
        if self.home_page:
            self.home_page.state_changed.connect(self.handle_home_state)
            self.home_page.ai_requested.connect(self.handle_ai_request)
            self.home_page.create_requested.connect(self.handle_create_request)
            self.home_page.surprise_triggered.connect(lambda: self.home_page.show_status("Surprise!"))
        self.settings_page = self.ui.load_pages._widgets.get("settings")
        if self.settings_page:
            self.settings_page.load_settings(self.app_settings.data)
            self.settings_page.save_btn.clicked.connect(self.save_settings)
        self.help_page = self.ui.load_pages._widgets.get("help")
        if self.help_page:
            self.help_page.copy_logs_requested.connect(self.handle_copy_logs)
        self.home_state: dict[str, Any] = {}
        self.processing = False

    # ---------------------------------------------------------------
    def menu_clicked(self, btn: QPushButton) -> None:
        if isinstance(btn, QPushButton):
            self.handle_left_menu_clicked(btn)

    # ---------------------------------------------------------------
    def menu_released(self, btn: QPushButton) -> None:
        # Stub for future behavior
        pass

    # ---------------------------------------------------------------
    def handle_left_menu_clicked(self, btn: QPushButton) -> None:
        mapping = {
            "btn_home": "home",
            "btn_batch": "batch",
            "btn_settings": "settings",
            "btn_help": "help",
        }
        page = mapping.get(btn.objectName())
        if page:
            self.ui.left_menu.select_only_one(btn.objectName())
            self.ui.load_pages.set_current(page)
            if page == "home" and self.home_page:
                self.home_page.update_preview_size()

    # ---------------------------------------------------------------
    def show_status(self, text: str, error: bool = False) -> None:
        if self.home_page:
            self.home_page.show_status(text, error=error)

    # ---------------------------------------------------------------
    def handle_home_state(self, key: str, value: Any) -> None:
        self.home_state[key] = value

    # ---------------------------------------------------------------
    def handle_ai_request(self) -> None:
        if self.processing or not self.home_page:
            return
        self.processing = True
        self.home_page.set_processing(True, "Generating AI...")
        thread = WorkerThread(generator.generate_story)
        thread.finished.connect(self.finish_ai_request)
        thread.failed.connect(self.ai_failed)
        thread.start()
        self._threads.append(thread)

    def ai_failed(self, exc: Exception) -> None:
        if self.home_page:
            self.home_page.set_processing(False, f"AI error: {exc}")
            self.home_page.show_status(f"AI failed: {exc}", error=True)
        self.processing = False

    def finish_ai_request(self, text: str) -> None:
        if self.home_page:
            self.home_page.script_edit.setPlainText(text)
            self.home_page.update_state("script", text)
            self.home_page.set_processing(False, "AI generation complete")
            self.home_page.show_status("AI generation complete")
        self.processing = False

    # ---------------------------------------------------------------
    def handle_create_request(self) -> None:
        if self.processing or not self.home_page:
            return
        self.processing = True
        self.home_page.set_processing(True, "Running pipeline...")
        cfg = Config.load(Path("config/config.json"))
        cfg.default_voice_id = self.home_state.get("voice")
        cfg.resolution = self.home_state.get("resolution", cfg.resolution)
        cfg.watermark_enabled = bool(self.home_state.get("watermark"))
        thread = WorkerThread(
            self._run_pipeline,
            cfg,
            self.home_page.script_edit.toPlainText(),
            self.home_state.get("voice") or "",
            self.home_state.get("background"),
        )
        thread.finished.connect(self.finish_create_request)
        thread.failed.connect(self.create_failed)
        thread.start()
        self._threads.append(thread)

    def create_failed(self, exc: Exception) -> None:
        if self.home_page:
            self.home_page.set_processing(False, f"Pipeline error: {exc}")
            self.home_page.show_status(f"Pipeline failed: {exc}", error=True)
        self.processing = False

    def finish_create_request(self, ctx) -> None:
        if self.home_page:
            self.home_page.set_processing(False, "Video saved.")
            self.home_page.show_status("Video saved")
            if ctx and hasattr(ctx, "final_video_path"):
                self.home_page.preview_label.setText(str(ctx.final_video_path))
        self.processing = False

    def _run_pipeline(self, cfg: Config, script: str, title: str, background: str | None):
        vp = VideoPipeline(cfg)
        out_dir = Path(self.app_settings.data.get("output_folder", "output"))
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{sanitize_name(title or 'session')}.mp4"
        return vp.run(script, title or "session", background=background, output=out_path)

    # ---------------------------------------------------------------
    def handle_copy_logs(self) -> None:
        path = Path("logs/pipeline.log").resolve()
        QGuiApplication.clipboard().setText(str(path))
        self.show_status("Log path copied")

    # ---------------------------------------------------------------
    def save_settings(self) -> None:
        if not self.settings_page:
            return
        self.app_settings.data.update(self.settings_page.get_settings())
        self.app_settings.save()
        self.settings_page.load_settings(self.app_settings.data)
        self.show_status("Settings saved")

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.save_settings()
        for thread in self._threads:
            thread.wait(100)
        super().closeEvent(event)


if __name__ == "__main__":
    if not QT_OK:
        sys.exit("Qt environment not available")
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
