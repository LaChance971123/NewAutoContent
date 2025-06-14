import sys
import json
import random
from pathlib import Path

GUI_DIR = Path(__file__).parent / "PyOneDark_GUI_Core"
sys.path.insert(0, str(GUI_DIR))

from qt_core import *
from gui.core.json_settings import Settings
from gui.core.json_themes import Themes
from gui.widgets import PyPushButton, PyToggle, PyGrips
from pipeline import generator
from pipeline.pipeline import VideoPipeline
from pipeline.config import Config
from pipeline.helpers import sanitize_name
from docx import Document

DEFAULTS = {
    "api_key": "",
    "output_folder": "output",
    "use_coqui_fallback": False,
    "subtitle_font": "Noto Sans",
    "output_resolution": "1080x1920",
    "watermark": False,
    "ai_prompt": "",
    "max_story_len": 200,
    "last_voice": "Default",
}

SECTION_STYLE = (
    "font-weight: bold; font-size: 12pt; margin-bottom: 12px;"
)
PAD = 10


class ScriptEdit(QPlainTextEdit):
    """Editor that supports drag-and-drop for text and docx files."""

    fileLoaded = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            url = e.mimeData().urls()[0]
            if url.isLocalFile() and url.toLocalFile().lower().endswith((".txt", ".docx")):
                e.acceptProposedAction()
                return
        super().dragEnterEvent(e)

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            path = e.mimeData().urls()[0].toLocalFile()
            lower = path.lower()
            try:
                if lower.endswith(".txt"):
                    with open(path, "r", encoding="utf-8") as f:
                        self.setPlainText(f.read())
                    self.fileLoaded.emit(Path(path).name)
                    e.acceptProposedAction()
                    return
                elif lower.endswith(".docx"):
                    doc = Document(path)
                    text = "\n".join(p.text for p in doc.paragraphs)
                    self.setPlainText(text)
                    self.fileLoaded.emit(Path(path).name)
                    e.acceptProposedAction()
                    return
                else:
                    QMessageBox.warning(self, "Unsupported", "Only .txt and .docx files are supported")
                    e.ignore()
                    return
            except Exception as exc:
                QMessageBox.warning(self, "Error", str(exc))
                e.ignore()
                return
        super().dropEvent(e)


class SettingsManager:
    """Simple wrapper around the global settings.json"""

    def __init__(self):
        self.path = Path(Settings.settings_path)
        self.load()

    def load(self):
        try:
            self.data = json.loads(self.path.read_text())
        except Exception:
            self.data = {}
        for k, v in DEFAULTS.items():
            self.data.setdefault(k, v)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings().items
        Themes.settings_path = str(GUI_DIR / f"gui/themes/{self.settings['theme_name']}.json")
        self.themes = Themes().items
        self.app_settings = SettingsManager()
        self.auto_filename = True

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

        # clear default left menu
        lm = self.ui.left_menu_frame.layout()
        while lm.count():
            item = lm.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.menu_container = QFrame()
        self.sidebar_layout = QVBoxLayout(self.menu_container)
        self.sidebar_layout.setContentsMargins(PAD, PAD, PAD, PAD)
        lm.addWidget(self.menu_container)

        # hide left/right columns by default
        self.ui.left_column_frame.setMinimumWidth(0)
        self.ui.left_column_frame.setMaximumWidth(0)
        self.ui.right_column_frame.setMinimumWidth(0)
        self.ui.right_column_frame.setMaximumWidth(0)

    # ------------------------------------------------------------------
    def clear_layout(self, layout: QLayout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

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
        if index == stack.currentIndex():
            return
        new = stack.widget(index)
        effect = QGraphicsOpacityEffect(new)
        new.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(200)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        stack.setCurrentIndex(index)
        if hasattr(self, "preview_container"):
            self.preview_container.setVisible(index == 0)

    # ------------------------------------------------------------------
    def build_home_page(self):
        layout = self.ui.load_pages.page_1_layout
        self.clear_layout(layout)
        placeholder = QLabel("\ud83d\udd27 Rebuilding GUI...")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)

    # ------------------------------------------------------------------
    def build_settings_page(self):
        layout = self.ui.load_pages.page_2_layout
        self.clear_layout(layout)
        placeholder = QLabel("\ud83d\udd27 Rebuilding GUI...")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)

    # ------------------------------------------------------------------
    def build_help_page(self):
        layout = self.ui.load_pages.page_3_layout
        self.clear_layout(layout)
        placeholder = QLabel("\ud83d\udd27 Rebuilding GUI...")
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)

    # ------------------------------------------------------------------
    def set_status(self, text: str, color: str | None = None):
        """Update bottom status bar and reset after 5 seconds."""
        if not hasattr(self, "status_text"):
            return
        self.status_text.setText(text)
        if color:
            self.status_dot.setStyleSheet(f"color: {color}")
        effect = QGraphicsOpacityEffect(self.status_text)
        self.status_text.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(200)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        if hasattr(self, "status_timer"):
            self.status_timer.start(5000)

    # ------------------------------------------------------------------
    def update_setting(self, key: str, value):
        self.app_settings.data[key] = value
        self.app_settings.save()

    # ------------------------------------------------------------------
    def menu_clicked(self):
        pass

    def menu_released(self):
        pass

    def upload_script(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Script", "", "Text Files (*.txt *.docx)")
        if path:
            if path.lower().endswith(".txt"):
                with open(path, "r", encoding="utf-8") as f:
                    self.script_edit.setPlainText(f.read())
            elif path.lower().endswith(".docx"):
                doc = Document(path)
                text = "\n".join(p.text for p in doc.paragraphs)
                self.script_edit.setPlainText(text)
            else:
                QMessageBox.warning(self, "Unsupported", "Only .txt and .docx files are supported")
                return
            self.on_script_loaded(Path(path).name)

    def choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.output_edit.text())
        if folder:
            path = Path(folder)
            if not path.exists():
                QMessageBox.warning(self, "Folder Missing", "Selected directory does not exist")
                return
            self.output_edit.setText(str(path))
            self.update_setting("output_folder", str(path))

    def surprise_me(self):
        combos = [self.voice_combo, self.subtitle_combo, self.bg_combo]
        for combo in combos:
            if combo.count():
                combo.setCurrentIndex(random.randrange(combo.count()))

    def generate_ai_story(self):
        prompt = (
            "Generate a 150-200 word horror story tailored for social media "
            "(TikTok/Shorts)."
        )
        theme = self.themes["app_color"]
        self.ai_btn.setEnabled(False)
        self.set_status("Generating AI...", theme.get("yellow"))
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            text = generator.generate_story(prompt=prompt)
            if not text:
                raise RuntimeError("No response from model")
            self.script_edit.setPlainText(text)
        except Exception as e:
            QMessageBox.critical(self, "AI Error", f"Story generation failed: {e}")
            self.set_status(f"\u274C Error: {e}", theme.get("red"))
        else:
            self.set_status("\u2705 Story Generated", theme.get("green"))
        finally:
            QApplication.restoreOverrideCursor()
            self.ai_btn.setEnabled(True)
            self.update_create_btn()

    def copy_logs(self):
        log_path = Path("logs/pipeline.log").resolve()
        if not log_path.exists():
            QMessageBox.warning(self, "Logs", "Log file not found")
            return
        QGuiApplication.clipboard().setText(str(log_path))
        self.set_status("Log path copied", self.themes["app_color"].get("green"))

    def on_script_loaded(self, name: str):
        self.set_status(f"Script loaded: {name}", self.themes["app_color"].get("green"))
        self.auto_filename = True
        self.on_script_changed()

    def disable_auto_title(self):
        self.auto_filename = False

    def on_script_changed(self):
        self.update_create_btn()
        if self.auto_filename:
            for line in self.script_edit.toPlainText().splitlines():
                if line.strip():
                    name = sanitize_name(line)[:50]
                    self.title_edit.blockSignals(True)
                    self.title_edit.setText(name)
                    self.title_edit.blockSignals(False)
                    break

    def sync_voice_combo(self, voice: str):
        i = self.voice_combo.findText(voice)
        if i >= 0:
            self.voice_combo.setCurrentIndex(i)

    def preview_voice(self):
        print(f"Previewing {self.voice_combo.currentText()}")

    def reset_form(self):
        self.script_edit.clear()
        self.title_edit.clear()
        for combo in (self.voice_combo, self.subtitle_combo, self.bg_combo):
            combo.setCurrentIndex(0)
        self.watermark_toggle.setChecked(False)
        self.auto_filename = True
        self.update_create_btn()
        self.update_watermark_label(False)

    def update_watermark_label(self, checked: bool):
        state = "On" if checked else "Off"
        self.watermark_label.setText(f"Watermark: {state}")
        self.output_info.setText(f"1080p @30fps | Watermark {state}")

    def update_create_btn(self):
        text = self.script_edit.toPlainText().strip()
        self.create_btn.setEnabled(bool(text))

    def run_pipeline(self):
        theme = self.themes["app_color"]
        self.create_btn.setEnabled(False)
        self.ai_btn.setEnabled(False)
        self.set_status("Generating Video...", theme.get("blue"))
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            cfg = Config.load(Path("config/config.json"))
            cfg.subtitle_style = self.subtitle_combo.currentText()
            cfg.default_voice_id = self.voice_combo.currentText()
            cfg.watermark_enabled = self.watermark_toggle.isChecked()
            cfg.validate()

            vp = VideoPipeline(cfg)
            title = self.title_edit.text().strip() or "session"
            script = self.script_edit.toPlainText()
            output_dir = Path(self.output_edit.text())
            out_path = output_dir / f"{sanitize_name(title)}.mp4"
            ctx = vp.run(
                script,
                title,
                background=self.bg_combo.currentText(),
                output=out_path,
                force_coqui=self.coqui_toggle.isChecked(),
            )
            QMessageBox.information(
                self,
                "Pipeline",
                f"Video saved to {ctx.final_video_path}",
            )
            self.set_status("\u2705 Content Created", theme.get("green"))
        except Exception as e:
            QMessageBox.critical(self, "Pipeline Error", str(e))
            self.set_status(f"\u274C Error: {e}", theme.get("red"))
        finally:
            QApplication.restoreOverrideCursor()
            self.create_btn.setEnabled(True)
            self.ai_btn.setEnabled(True)
            self.update_create_btn()

    def save_settings(self):
        d = self.app_settings.data
        d["output_folder"] = self.output_edit.text()
        d["use_coqui_fallback"] = self.coqui_check.isChecked()
        d["output_resolution"] = self.resolution_combo.currentText()
        d["watermark"] = self.wm_check.isChecked()
        d["ai_prompt"] = self.prompt_edit.toPlainText()
        d["max_story_len"] = self.len_spin.value()
        d["last_voice"] = self.default_voice_combo.currentText()
        d["last_subtitle"] = self.subtitle_combo.currentText()
        d["last_background"] = self.bg_combo.currentText()
        d["last_title"] = self.title_edit.text()
        self.app_settings.save()

    def restore_state(self):
        data = self.app_settings.data
        self.output_edit.setText(data.get("output_folder", DEFAULTS["output_folder"]))
        self.coqui_check.setChecked(data.get("use_coqui_fallback", DEFAULTS["use_coqui_fallback"]))
        self.resolution_combo.setCurrentText(data.get("output_resolution", DEFAULTS["output_resolution"]))
        self.wm_check.setChecked(data.get("watermark", DEFAULTS["watermark"]))
        self.prompt_edit.setPlainText(data.get("ai_prompt", DEFAULTS["ai_prompt"]))
        self.len_spin.setValue(data.get("max_story_len", DEFAULTS["max_story_len"]))
        voice = data.get("last_voice", DEFAULTS["last_voice"]) 
        idx = self.default_voice_combo.findText(voice)
        if idx >= 0:
            self.default_voice_combo.setCurrentIndex(idx)
        # home page widgets
        for combo, key in [
            (self.voice_combo, "last_voice"),
            (self.subtitle_combo, "last_subtitle"),
            (self.bg_combo, "last_background"),
        ]:
            val = data.get(key)
            if val is not None:
                i = combo.findText(val)
                if i >= 0:
                    combo.setCurrentIndex(i)
        self.watermark_toggle.setChecked(data.get("watermark", DEFAULTS["watermark"]))
        last_title = data.get("last_title", "")
        self.title_edit.setText(last_title)
        self.auto_filename = not bool(last_title)

    def restore_defaults(self):
        for k, v in DEFAULTS.items():
            self.app_settings.data[k] = v
        self.app_settings.save()
        self.restore_state()
        self.set_status("Defaults restored", self.themes["app_color"].get("green"))

    def adjust_preview_size(self):
        if not hasattr(self, "preview_container"):
            return
        frame_width = self.ui.load_pages.preview_frame.width()
        width = int(max(200, min(self.width() * 0.4, frame_width)))
        height = int(width * 16 / 9)
        self.preview_container.setFixedSize(width, height)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

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
        self.adjust_preview_size()
        super().resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())

