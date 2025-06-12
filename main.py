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
    PyToggle,
    PyGrips,
)


class ScriptEdit(QPlainTextEdit):
    """Text editor that accepts .txt drops and loads file contents."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            url = e.mimeData().urls()[0]
            if url.isLocalFile() and url.toLocalFile().lower().endswith(".txt"):
                e.acceptProposedAction()
                return
        super().dragEnterEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            url = e.mimeData().urls()[0]
            if url.isLocalFile() and url.toLocalFile().lower().endswith(".txt"):
                try:
                    with open(url.toLocalFile(), "r", encoding="utf-8") as f:
                        self.setPlainText(f.read())
                except Exception:
                    pass
                e.acceptProposedAction()
                return
        super().dropEvent(e)
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
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        def section(title):
            frame = QFrame()
            frame.setMaximumWidth(520)
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(10, 10, 10, 10)
            lbl = QLabel(title)
            lbl.setStyleSheet("font-weight: bold")
            fl.addWidget(lbl)
            layout.addWidget(frame, alignment=Qt.AlignHCenter)
            return fl

        # Script input section
        script_layout = section("Script Input")

        self.script_edit = ScriptEdit()
        self.script_edit.setPlaceholderText("Tip: Drag and drop a file to load it")
        self.script_edit.setMinimumHeight(120)
        self.script_edit.setMaximumWidth(500)
        self.script_edit.setStyleSheet(
            f"background-color: {theme['dark_one']}; color: {theme['text_foreground']};"
        )
        self.script_edit.textChanged.connect(self.update_create_btn)
        self.script_edit.setToolTip("Enter or load a script")
        script_layout.addWidget(self.script_edit)

        btn_row = QHBoxLayout()
        self.upload_btn = PyPushButton(
            text="Upload",
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["dark_three"],
            bg_color_hover=theme["context_hover"],
            bg_color_pressed=theme["context_pressed"],
        )
        self.upload_btn.setToolTip("Open text file")
        self.upload_btn.setIcon(QIcon(Functions.set_svg_icon("icon_folder_open.svg")))
        self.upload_btn.setMaximumWidth(500)
        self.upload_btn.clicked.connect(self.upload_script)
        btn_row.addWidget(self.upload_btn)

        self.ai_btn = PyPushButton(
            text="Generate with AI",
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["dark_three"],
            bg_color_hover=theme["context_hover"],
            bg_color_pressed=theme["context_pressed"],
        )
        self.ai_btn.setEnabled(False)
        self.ai_btn.setToolTip("Coming Soon")
        self.ai_btn.setMaximumWidth(500)
        btn_row.addWidget(self.ai_btn)

        self.reset_btn = PyPushButton(
            text="Reset",
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["dark_three"],
            bg_color_hover=theme["context_hover"],
            bg_color_pressed=theme["context_pressed"],
        )
        self.reset_btn.setToolTip("Clear script")
        self.reset_btn.setIcon(QIcon(Functions.set_svg_icon("icon_restore.svg")))
        self.reset_btn.setMaximumWidth(500)
        self.reset_btn.clicked.connect(self.reset_form)
        btn_row.addWidget(self.reset_btn)
        script_layout.addLayout(btn_row)

        # Voice selection
        voice_layout = section("Voice Selection")
        row1 = QHBoxLayout()
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["Alice", "Drew", "Bob"])
        self.voice_combo.setToolTip("Choose a voice")
        self.voice_combo.setMaximumWidth(500)
        row1.addWidget(self.voice_combo)

        self.preview_btn = PyPushButton(
            text="",
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["dark_three"],
            bg_color_hover=theme["context_hover"],
            bg_color_pressed=theme["context_pressed"],
        )
        self.preview_btn.setIcon(QIcon(Functions.set_svg_icon("icon_play.svg")))
        self.preview_btn.setToolTip("Preview selected voice")
        self.preview_btn.setMaximumWidth(500)
        self.preview_btn.clicked.connect(self.preview_voice)
        row1.addWidget(self.preview_btn)
        voice_layout.addLayout(row1)

        # Video settings
        video_layout = section("Video Settings")
        self.subtitle_combo = QComboBox()
        self.subtitle_combo.addItems(["karaoke", "progressive", "simple"])
        self.subtitle_combo.setToolTip("Choose subtitle style")
        self.subtitle_combo.setMaximumWidth(500)
        video_layout.addWidget(self.subtitle_combo)

        wm_row = QHBoxLayout()
        self.watermark_toggle = PyToggle(
            bg_color=theme["dark_three"],
            circle_color=theme["icon_color"],
            active_color=theme["context_color"],
        )
        self.watermark_toggle.setToolTip("Toggle watermark")
        self.watermark_toggle.toggled.connect(self.update_watermark_label)
        wm_row.addWidget(self.watermark_toggle)
        self.watermark_label = QLabel("Watermark: Off")
        wm_row.addWidget(self.watermark_label)
        wm_row.addStretch()
        video_layout.addLayout(wm_row)

        # Background style
        bg_layout = section("Background Style")
        row2 = QHBoxLayout()
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["Default", "City", "Minecraft"])
        self.bg_combo.setToolTip("Choose a background")
        self.bg_combo.setMaximumWidth(500)
        row2.addWidget(self.bg_combo)

        self.surprise_btn = PyPushButton(
            text="Surprise Me",
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["dark_three"],
            bg_color_hover=theme["context_hover"],
            bg_color_pressed=theme["context_pressed"],
        )
        self.surprise_btn.setToolTip("Randomly select a background category")
        self.surprise_btn.setIcon(QIcon(Functions.set_svg_icon("icon_more_options.svg")))
        self.surprise_btn.setMaximumWidth(500)
        self.surprise_btn.clicked.connect(self.surprise_me)
        row2.addWidget(self.surprise_btn)
        bg_layout.addLayout(row2)

        # Action buttons
        action_layout = section("Action Buttons")
        self.output_info = QLabel("MP4 | 1080p @30fps | Watermark Off")
        self.output_info.setAlignment(Qt.AlignCenter)
        action_layout.addWidget(self.output_info)

        self.create_btn = PyPushButton(
            text="Create Content",
            radius=8,
            color=theme["text_foreground"],
            bg_color=theme["context_color"],
            bg_color_hover=theme["context_hover"],
            bg_color_pressed=theme["context_pressed"],
        )
        self.create_btn.setToolTip("Start generating your AutoContent video")
        self.create_btn.setIcon(QIcon(Functions.set_svg_icon("icon_send.svg")))
        self.create_btn.setEnabled(False)
        self.create_btn.setMaximumWidth(500)
        self.create_btn.clicked.connect(self.run_pipeline)
        action_layout.addWidget(self.create_btn)

        status = QHBoxLayout()
        self.status_dot = QLabel("\u25CF")
        self.status_dot.setStyleSheet(f"color: {theme['green']}")
        status.addWidget(self.status_dot)
        self.status_text = QLabel("Idle")
        status.addWidget(self.status_text)
        status.addStretch()
        self.ready_label = QLabel("Ready")
        status.addWidget(self.ready_label, alignment=Qt.AlignRight)
        layout.addLayout(status)

        layout.addStretch()

        # Preview placeholder
        self.preview_container = QFrame()
        self.preview_container.setStyleSheet(
            f"background-color: {theme['dark_one']}; border-radius: 10px;"
        )
        self.preview_container.setFixedSize(270, 480)
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_label = QLabel("Video Preview")
        preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(preview_label, 1, Qt.AlignCenter)
        self.ui.load_pages.preview_layout.addWidget(self.preview_container, 0, Qt.AlignTop | Qt.AlignHCenter)

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

    def update_watermark_label(self, checked):
        state = "On" if checked else "Off"
        self.watermark_label.setText(f"Watermark: {state}")
        self.output_info.setText(f"MP4 | 1080p @30fps | Watermark {state}")

    def preview_voice(self):
        print(f"Previewing {self.voice_combo.currentText()}")

    def reset_form(self):
        self.script_edit.clear()
        for combo in (self.voice_combo, self.subtitle_combo, self.bg_combo):
            combo.setCurrentIndex(0)
        self.watermark_toggle.setChecked(False)
        self.update_create_btn()
        self.update_watermark_label(False)

    def update_create_btn(self):
        text = self.script_edit.toPlainText().strip()
        self.create_btn.setEnabled(bool(text))
        state = "On" if self.watermark_toggle.isChecked() else "Off"
        self.output_info.setText(f"MP4 | 1080p @30fps | Watermark {state}")

    def run_pipeline(self):
        print("Starting pipeline...")

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
