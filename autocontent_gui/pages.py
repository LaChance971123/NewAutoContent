from qt_core import *
from gui.core.json_settings import Settings
from gui.core.json_themes import Themes
from gui.widgets import PyPushButton, PyToggle
import random


class HomePageWidget(QWidget):
    """Main page with script input, controls, and preview."""

    state_changed = Signal(str, object)
    create_requested = Signal()
    ai_requested = Signal()
    surprise_triggered = Signal()

    def __init__(self):
        super().__init__()
        theme = Themes().items["app_color"]
        self.theme = theme
        font_family = Settings().items["font"]["family"]

        self.state = {}
        self.processing = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # left side
        left_col = QVBoxLayout()
        left_col.setSpacing(15)

        def header(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"font-weight: bold; margin-bottom: 4px; font-family: '{font_family}'"
            )
            lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            return lbl

        # script area
        left_col.addWidget(header("\U0001F3AC Script Input"))
        self.script_edit = QPlainTextEdit()
        self.script_edit.setPlaceholderText("Enter or drop your story/script here...")
        self.script_edit.setStyleSheet(
            f"background-color: {self.theme['dark_one']}; color: {self.theme['text_foreground']}"
        )
        left_col.addWidget(self.script_edit)

        # controls section
        left_col.addWidget(header("\U0001F399\ufe0f Voice & Subtitle Controls"))

        controls = QVBoxLayout()

        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["Default", "Voice 1", "Voice 2"])
        self.voice_combo.setToolTip("Select narration voice")
        controls.addWidget(self.voice_combo)

        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["Style A", "Style B", "Style C"])
        self.bg_combo.setToolTip("Select background style")
        controls.addWidget(self.bg_combo)

        self.res_combo = QComboBox()
        self.res_combo.addItems(["720p", "1080p", "1440p"])
        self.res_combo.setToolTip("Select output resolution")
        controls.addWidget(self.res_combo)

        watermark_row = QHBoxLayout()
        self.watermark_toggle = PyToggle(
            bg_color=self.theme["dark_three"],
            circle_color=self.theme["icon_color"],
            active_color=self.theme["context_color"],
        )
        self.watermark_toggle.setToolTip("Toggle watermark on or off")
        watermark_row.addWidget(QLabel("Include Watermark"))
        watermark_row.addStretch()
        watermark_row.addWidget(self.watermark_toggle)
        controls.addLayout(watermark_row)

        btn_row = QHBoxLayout()
        self.ai_btn = PyPushButton(
            text="Generate with AI",
            radius=8,
            color=self.theme["text_foreground"],
            bg_color=self.theme["dark_three"],
            bg_color_hover=self.theme["context_hover"],
            bg_color_pressed=self.theme["context_pressed"],
        )
        self.ai_btn.setToolTip("Generate a script with AI")
        btn_row.addWidget(self.ai_btn)

        self.create_btn = PyPushButton(
            text="Create Content",
            radius=8,
            color=self.theme["text_foreground"],
            bg_color=self.theme["context_color"],
            bg_color_hover=self.theme["context_hover"],
            bg_color_pressed=self.theme["context_pressed"],
        )
        self.create_btn.setToolTip("Build final video content")
        btn_row.addWidget(self.create_btn)

        self.surprise_btn = PyPushButton(
            text="Surprise Me",
            radius=8,
            color=self.theme["text_foreground"],
            bg_color=self.theme["dark_three"],
            bg_color_hover=self.theme["context_hover"],
            bg_color_pressed=self.theme["context_pressed"],
        )
        self.surprise_btn.setToolTip("Randomize settings")
        btn_row.addWidget(self.surprise_btn)

        self.reset_btn = PyPushButton(
            text="Reset",
            radius=8,
            color=self.theme["text_foreground"],
            bg_color=self.theme["dark_three"],
            bg_color_hover=self.theme["context_hover"],
            bg_color_pressed=self.theme["context_pressed"],
        )
        self.reset_btn.setToolTip("Clear all fields")
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch()

        controls.addLayout(btn_row)

        left_col.addLayout(controls)
        left_col.addStretch()

        # preview side
        preview_col = QVBoxLayout()
        preview_col.setSpacing(15)
        preview_col.setAlignment(Qt.AlignTop)

        preview_col.addWidget(header("\U0001F3A5 Preview Pane"))
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("preview_frame")
        self.preview_frame.setStyleSheet(
            f"background-color: {self.theme['dark_one']}; border-radius: 8px;"
        )
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.setAlignment(Qt.AlignCenter)
        self.preview_label = QLabel("Video preview placeholder")
        self.preview_label.setStyleSheet("font-weight: bold; font-size: 12pt")
        preview_layout.addWidget(self.preview_label)
        preview_col.addWidget(self.preview_frame, alignment=Qt.AlignTop)
        preview_col.addStretch()

        content_layout.addLayout(left_col, 3)
        content_layout.addLayout(preview_col, 2)
        main_layout.addLayout(content_layout)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            f"QProgressBar{{background:{self.theme['dark_three']};border-radius:9px;}}"
            f"QProgressBar::chunk{{background:{self.theme['context_color']};border-radius:9px;}}"
        )
        main_layout.addWidget(self.progress_bar)
        main_layout.addStretch()

        # init state
        self.update_state("script", "")
        self.update_state("voice", self.voice_combo.currentText())
        self.update_state("background", self.bg_combo.currentText())
        self.update_state("resolution", self.res_combo.currentText())
        self.update_state("watermark", self.watermark_toggle.isChecked())
        
        self.script_edit.textChanged.connect(lambda: self.update_state("script", self.script_edit.toPlainText()))
        self.voice_combo.currentTextChanged.connect(lambda t: self.update_state("voice", t))
        self.bg_combo.currentTextChanged.connect(lambda t: self.update_state("background", t))
        self.res_combo.currentTextChanged.connect(lambda t: self.update_state("resolution", t))
        self.watermark_toggle.toggled.connect(lambda b: self.update_state("watermark", b))

        self.ai_btn.clicked.connect(self.ai_requested.emit)
        self.create_btn.clicked.connect(lambda: (self.create_requested.emit(), self.state_changed.emit("create", None)))
        self.reset_btn.clicked.connect(self.reset_form)
        self.surprise_btn.clicked.connect(self.surprise_me)
        
        self.check_inputs()
        self.update_preview_label()

    def update_state(self, key: str, value):
        self.state[key] = value
        self.state_changed.emit(key, value)
        if key in {"script", "voice", "resolution"}:
            self.check_inputs()
        if key == "background":
            self.update_preview_label()

    def apply_button_state(self, btn: QPushButton, enabled: bool) -> None:
        btn.setEnabled(enabled)
        if not hasattr(btn, "_fx"):
            btn._fx = QGraphicsOpacityEffect(btn)
            btn.setGraphicsEffect(btn._fx)
        btn._fx.setOpacity(1.0 if enabled else 0.5)

    def resizeEvent(self, event):
        self.update_preview_size()
        super().resizeEvent(event)

    def update_preview_size(self):
        width = int(self.width() * 0.38)
        height = int(width * 16 / 9)
        self.preview_frame.setFixedSize(width, height)

    def update_preview_label(self):
        if self.processing:
            self.preview_label.setText("Loading preview...")
        else:
            self.preview_label.setText(self.bg_combo.currentText())

    def check_inputs(self):
        text_ok = bool(self.script_edit.toPlainText().strip())
        voice_ok = self.voice_combo.currentIndex() >= 0
        res_ok = self.res_combo.currentIndex() >= 0
        enabled = text_ok and voice_ok and res_ok and not self.processing
        self.apply_button_state(self.create_btn, enabled)
        if not enabled:
            self.create_btn.setToolTip("Fill script, voice, and resolution")
        else:
            self.create_btn.setToolTip("Build final video content")

    def set_processing(self, running: bool, message: str = ""):
        self.processing = running
        for w in (
            self.script_edit,
            self.voice_combo,
            self.bg_combo,
            self.res_combo,
            self.watermark_toggle,
            self.ai_btn,
            self.create_btn,
            self.surprise_btn,
            self.reset_btn,
        ):
            w.setEnabled(not running)
        self.progress_bar.setVisible(running)
        if running:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            QTimer.singleShot(300, lambda: self.progress_bar.setVisible(False))
        if running:
            self.ai_btn.setToolTip("Please wait until processing finishes")
            self.create_btn.setToolTip("Please wait until processing finishes")
        else:
            self.ai_btn.setToolTip("Generate a script with AI")
            self.create_btn.setToolTip("Build final video content")
        self.apply_button_state(self.ai_btn, not running)
        self.apply_button_state(self.create_btn, not running)
        self.show_status(message)
        self.update_preview_label()
        self.check_inputs()

    def show_status(self, text: str, timeout: int = 2000, error: bool = False):
        if not text:
            self.status_label.setText("")
            return
        color = self.theme["red"] if error else self.theme["text_foreground"]
        self.status_label.setStyleSheet(f"color: {color}")
        self.status_label.setText(text)
        effect = QGraphicsOpacityEffect(self.status_label)
        self.status_label.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(200)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        QTimer.singleShot(
            timeout,
            lambda: self._fade_status(effect),
        )

    def _fade_status(self, effect: QGraphicsOpacityEffect):
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(200)
        anim.setStartValue(1)
        anim.setEndValue(0)
        anim.finished.connect(lambda: self.status_label.setText(""))
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def reset_form(self):
        self.script_edit.clear()
        self.voice_combo.setCurrentIndex(0)
        self.bg_combo.setCurrentIndex(0)
        self.res_combo.setCurrentIndex(0)
        self.watermark_toggle.setChecked(False)
        self.update_state("script", "")
        self.show_status("Reset")
        self.update_preview_label()
        self.check_inputs()

    def surprise_me(self):
        for combo in (self.voice_combo, self.bg_combo, self.res_combo):
            if combo.count() > 0:
                combo.setCurrentIndex(random.randrange(combo.count()))
        self.show_status("Randomized")
        self.surprise_triggered.emit()
        self.update_state("voice", self.voice_combo.currentText())
        self.update_state("background", self.bg_combo.currentText())
        self.update_state("resolution", self.res_combo.currentText())

        effect = QGraphicsColorizeEffect(self.preview_frame)
        self.preview_frame.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"strength", self)
        anim.setDuration(300)
        anim.setStartValue(0)
        anim.setEndValue(0.8)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        def clear():
            self.preview_frame.setGraphicsEffect(None)
        anim.finished.connect(clear)
        anim.start(QPropertyAnimation.DeleteWhenStopped)



class BatchModePageWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Batch Mode (Coming Soon…)", alignment=Qt.AlignCenter))
        layout.addStretch()


class SettingsPageWidget(QWidget):
    """Placeholder settings page with section headers."""

    def __init__(self):
        super().__init__()
        font_family = Settings().items["font"]["family"]
        theme = Themes().items["app_color"]
        self.theme = theme

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        def header(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"font-weight: bold; margin-bottom: 4px; font-family: '{font_family}'"
            )
            return lbl

        main_layout.addWidget(header("\u2699\ufe0f General Settings"))
        general_box = QVBoxLayout()
        general_box.setSpacing(10)
        general_box.addWidget(QLabel("API Key"))
        self.api_edit = QLineEdit()
        self.api_edit.setPlaceholderText("Enter API key")
        self.api_edit.setToolTip("API key for external services")
        general_box.addWidget(self.api_edit)
        main_layout.addLayout(general_box)

        main_layout.addWidget(header("\U0001F5C2\ufe0f Output Options"))
        output_box = QVBoxLayout()
        output_box.setSpacing(10)
        output_row = QHBoxLayout()
        self.output_edit = QLineEdit("/path/to/output")
        self.output_edit.setToolTip("Folder for rendered videos")
        output_row.addWidget(self.output_edit)
        self.output_btn = PyPushButton(
            text="Browse",
            radius=8,
            color=self.theme["text_foreground"],
            bg_color=self.theme["dark_three"],
            bg_color_hover=self.theme["context_hover"],
            bg_color_pressed=self.theme["context_pressed"],
        )
        self.output_btn.setToolTip("Select output directory")
        output_row.addWidget(self.output_btn)
        output_box.addLayout(output_row)
        main_layout.addLayout(output_box)

        main_layout.addWidget(header("\U0001F50A Voice Settings"))
        voice_box = QVBoxLayout()
        voice_box.setSpacing(10)
        voice_box.addWidget(QLabel("Default Voice"))
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["Default", "Voice 1", "Voice 2"])
        self.voice_combo.setToolTip("Voice used when creating videos")
        voice_box.addWidget(self.voice_combo)
        main_layout.addLayout(voice_box)

        self.save_btn = PyPushButton(
            text="Save Settings",
            radius=8,
            color=self.theme["text_foreground"],
            bg_color=self.theme["context_color"],
            bg_color_hover=self.theme["context_hover"],
            bg_color_pressed=self.theme["context_pressed"],
        )
        self.save_btn.setToolTip("Persist settings")
        main_layout.addWidget(self.save_btn, alignment=Qt.AlignLeft)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

        self.output_btn.clicked.connect(self.browse_output)

    def show_status(self, text: str, timeout: int = 2000):
        if not text:
            self.status_label.setText("")
            return
        self.status_label.setText(text)
        effect = QGraphicsOpacityEffect(self.status_label)
        self.status_label.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(200)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        QTimer.singleShot(
            timeout,
            lambda: self._fade_status(effect),
        )

    def _fade_status(self, effect: QGraphicsOpacityEffect):
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(200)
        anim.setStartValue(1)
        anim.setEndValue(0)
        anim.finished.connect(lambda: self.status_label.setText(""))
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def load_settings(self, data: dict):
        self.api_edit.setText(data.get("api_key", ""))
        self.output_edit.setText(data.get("output_folder", "output"))
        voice = data.get("last_voice", "Default")
        idx = self.voice_combo.findText(voice)
        if idx >= 0:
            self.voice_combo.setCurrentIndex(idx)

    def get_settings(self) -> dict:
        return {
            "api_key": self.api_edit.text().strip(),
            "output_folder": self.output_edit.text().strip(),
            "last_voice": self.voice_combo.currentText(),
        }

    def browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Folder", self.output_edit.text())
        if path:
            self.output_edit.setText(path)



class HelpPageWidget(QWidget):
    """Scrollable help placeholder with sections."""

    copy_logs_requested = Signal()

    def __init__(self):
        super().__init__()
        font_family = Settings().items["font"]["family"]
        theme = Themes().items["app_color"]
        self.theme = theme

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        cont_layout = QVBoxLayout(container)
        cont_layout.setContentsMargins(0, 0, 0, 0)
        cont_layout.setSpacing(10)

        def section(title: str, text: str):
            lbl = QLabel(title)
            lbl.setStyleSheet(
                f"font-weight: bold; margin-bottom: 4px; font-family: '{font_family}'"
            )
            cont_layout.addWidget(lbl)
            body = QLabel(text)
            body.setWordWrap(True)
            cont_layout.addWidget(body)

        section("\U0001F4D6 Getting Started", """Step 1: Enter your script or generate one with AI.\nStep 2: Adjust voice and background settings.\nStep 3: Click Create to render your video.""")
        section("\U0001F39E\ufe0f Output Overview", """Videos and logs will be stored in the output folder defined in Settings. Each run creates its own timestamped subfolder.""")
        section("\u2699\ufe0f Troubleshooting", """If a step fails, check pipeline.log in the output folder. Ensure ffmpeg is installed and paths are correct.""")

        self.copy_btn = PyPushButton(
            text="Copy Logs",
            radius=8,
            color=self.theme["text_foreground"],
            bg_color=self.theme["dark_three"],
            bg_color_hover=self.theme["context_hover"],
            bg_color_pressed=self.theme["context_pressed"],
        )
        self.copy_btn.setToolTip("Copy log file path to clipboard")
        cont_layout.addWidget(self.copy_btn, alignment=Qt.AlignLeft)
        self.copy_btn.clicked.connect(self.copy_logs_requested.emit)
        cont_layout.addStretch()

        main_layout.addWidget(scroll)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def show_status(self, text: str, timeout: int = 2000):
        if not text:
            self.status_label.setText("")
            return
        self.status_label.setText(text)
        effect = QGraphicsOpacityEffect(self.status_label)
        self.status_label.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(200)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        QTimer.singleShot(
            timeout,
            lambda: self._fade_status(effect),
        )

    def _fade_status(self, effect: QGraphicsOpacityEffect):
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(200)
        anim.setStartValue(1)
        anim.setEndValue(0)
        anim.finished.connect(lambda: self.status_label.setText(""))
        anim.start(QPropertyAnimation.DeleteWhenStopped)

