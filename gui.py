from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia, QtMultimediaWidgets

from pipeline.pipeline import VideoPipeline
from pipeline.config import Config
from pipeline.helpers import sanitize_filename, now_ts_folder, zip_folder
from pipeline.downloader import Downloader


class QTextLogger(logging.Handler):
    """Logging handler that writes to a QPlainTextEdit."""

    def __init__(self, edit: QtWidgets.QPlainTextEdit) -> None:
        super().__init__()
        self.edit = edit
        self.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        QtCore.QMetaObject.invokeMethod(
            self.edit, "appendPlainText", QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, msg)
        )


def load_config() -> Config:
    cfg = Config.load(Path("config/config.json"))
    cfg.validate()
    return cfg


class SidebarButton(QtWidgets.QToolButton):
    def __init__(self, text: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)


class PreviewPane(QtWidgets.QFrame):
    """Phone-styled preview pane with video playback."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(250)
        layout = QtWidgets.QVBoxLayout(self)
        self.player = QtMultimedia.QMediaPlayer(self)
        self.video = QtMultimediaWidgets.QVideoWidget(self)
        self.player.setVideoOutput(self.video)
        layout.addWidget(self.video)

    def load_video(self, path: Path) -> None:
        if path.exists():
            url = QtCore.QUrl.fromLocalFile(str(path.resolve()))
            self.player.setMedia(QtMultimedia.QMediaContent(url))
            self.player.setLoops(-1)
            self.player.play()


class CreatePage(QtWidgets.QWidget):
    generateRequested = QtCore.pyqtSignal(dict)

    def __init__(self, config: Config, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QFormLayout(self)

        self.title_edit = QtWidgets.QLineEdit()
        layout.addRow("Title", self.title_edit)

        self.script_edit = QtWidgets.QPlainTextEdit()
        self.script_edit.setAcceptDrops(True)
        self.script_edit.installEventFilter(self)
        layout.addRow("Script", self.script_edit)

        self.load_btn = QtWidgets.QPushButton("Load Script")
        self.load_btn.clicked.connect(self._load_script)
        layout.addRow(self.load_btn)

        self.voice_combo = QtWidgets.QComboBox()
        for name, vid in (self.config.voices or {}).items():
            self.voice_combo.addItem(name, vid)
        self.preview_voice_btn = QtWidgets.QPushButton("Preview Voice")
        self.preview_voice_btn.clicked.connect(self._preview_voice)
        layout.addRow("Voice", self.voice_combo)
        layout.addRow(self.preview_voice_btn)

        self.bg_combo = QtWidgets.QComboBox()
        for name, path in (self.config.background_styles or {}).items():
            self.bg_combo.addItem(name, path)
        layout.addRow("Background", self.bg_combo)

        self.res_combo = QtWidgets.QComboBox()
        for r in (self.config.resolutions or [self.config.resolution]):
            self.res_combo.addItem(r)
        layout.addRow("Resolution", self.res_combo)

        self.style_combo = QtWidgets.QComboBox()
        self.style_combo.addItems(["simple", "karaoke", "progressive"])
        self.preview_sub_btn = QtWidgets.QPushButton("Preview Subtitle")
        self.preview_sub_btn.clicked.connect(self._preview_subs)
        layout.addRow("Subtitle Style", self.style_combo)
        layout.addRow(self.preview_sub_btn)

        self.wm_check = QtWidgets.QCheckBox("Enable Watermark")
        self.wm_check.setChecked(self.config.watermark_enabled)
        layout.addRow(self.wm_check)

        self.generate_btn = QtWidgets.QPushButton("Generate")
        self.generate_btn.clicked.connect(self._emit_generate)
        layout.addRow(self.generate_btn)

        self.estimate_label = QtWidgets.QLabel()
        layout.addRow("Est. Duration", self.estimate_label)

        self.output_label = QtWidgets.QLabel()
        layout.addRow("Output", self.output_label)

        self.log_edit = QtWidgets.QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumHeight(150)
        layout.addRow(self.log_edit)

        self.script_edit.textChanged.connect(self._update_estimate)
        self.res_combo.currentTextChanged.connect(self._update_estimate)
        self._update_estimate()

    def _load_script(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Script", "scripts", "Text Files (*.txt)")
        if path:
            self.script_edit.setPlainText(Path(path).read_text())
            self.title_edit.setText(Path(path).stem)

    def _emit_generate(self) -> None:
        opts = {
            "title": self.title_edit.text().strip(),
            "script": self.script_edit.toPlainText().strip(),
            "voice": self.voice_combo.currentData(),
            "background": self.bg_combo.currentText(),
            "resolution": self.res_combo.currentText(),
            "style": self.style_combo.currentText(),
            "watermark": self.wm_check.isChecked(),
        }
        self.generateRequested.emit(opts)

    def eventFilter(self, obj, event):
        if obj is self.script_edit and event.type() == QtCore.QEvent.Drop:
            for url in event.mimeData().urls():
                path = Path(url.toLocalFile())
                if path.suffix.lower() in {'.txt', '.docx'}:
                    self.script_edit.setPlainText(Path(path).read_text())
                    self.title_edit.setText(path.stem)
                    return True
        return super().eventFilter(obj, event)

    def _preview_voice(self) -> None:
        from pipeline.voiceover import VoiceOverGenerator

        temp = Path("_preview.wav")
        gen = VoiceOverGenerator("elevenlabs", self.voice_combo.currentData(), self.config.coqui_model_name)
        if gen.generate("This is a voice preview", temp):
            url = QtCore.QUrl.fromLocalFile(str(temp.resolve()))
            player = QtMultimedia.QMediaPlayer()
            player.setMedia(QtMultimedia.QMediaContent(url))
            player.play()
        else:
            QtWidgets.QMessageBox.warning(self, "Preview", "Failed to generate preview")

    def _preview_subs(self) -> None:
        QtWidgets.QMessageBox.information(self, "Preview", "Subtitle preview not implemented")

    def _update_estimate(self) -> None:
        words = len(self.script_edit.toPlainText().split())
        secs = int(words / 2.5)
        self.estimate_label.setText(f"{secs}s")


class BatchPage(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.file_list = QtWidgets.QListWidget()
        self.add_btn = QtWidgets.QPushButton("Add Files")
        self.start_btn = QtWidgets.QPushButton("Start Batch")
        layout.addWidget(self.file_list)
        layout.addWidget(self.add_btn)
        layout.addWidget(self.start_btn)


class DownloaderPage(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.url_edit = QtWidgets.QPlainTextEdit()
        self.folder_btn = QtWidgets.QPushButton("Select Folder")
        self.start_btn = QtWidgets.QPushButton("Start Download")
        self.list = QtWidgets.QListWidget()
        layout.addWidget(QtWidgets.QLabel("URLs (one per line)"))
        layout.addWidget(self.url_edit)
        layout.addWidget(self.folder_btn)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.list)


class PlannerPage(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.calendar = QtWidgets.QCalendarWidget()
        self.notes = QtWidgets.QPlainTextEdit()
        layout.addWidget(self.calendar)
        layout.addWidget(self.notes)


class SettingsPage(QtWidgets.QWidget):
    configSaved = QtCore.pyqtSignal(Config)

    def __init__(self, config: Config, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QFormLayout(self)
        self.api_edit = QtWidgets.QLineEdit()
        self.api_edit.setText(self.config.default_voice_id or "")
        layout.addRow("Default Voice ID", self.api_edit)

        self.ffmpeg_edit = QtWidgets.QLineEdit()
        self.ffmpeg_edit.setText(self.config.ffmpeg_path)
        layout.addRow("FFmpeg Path", self.ffmpeg_edit)

        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.clicked.connect(self._save)
        layout.addRow(self.save_btn)

    def _save(self) -> None:
        self.config.default_voice_id = self.api_edit.text().strip() or None
        self.config.ffmpeg_path = self.ffmpeg_edit.text().strip() or "ffmpeg"
        self.config.save(Path("config/config.json"))
        self.configSaved.emit(self.config)


class HelpPage(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        txt = QtWidgets.QLabel("See README.md for help. If rendering fails, check your log file.")
        txt.setWordWrap(True)
        layout.addWidget(txt)


class StorePage(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Upgrade to Pro coming soon!"))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AutoContent")
        self.config = load_config()
        self._build_ui()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QHBoxLayout(central)

        # Sidebar
        self.sidebar = QtWidgets.QVBoxLayout()
        side_frame = QtWidgets.QFrame()
        side_frame.setLayout(self.sidebar)
        side_frame.setFixedWidth(150)

        self.button_group = QtWidgets.QButtonGroup(self)
        self.button_group.setExclusive(True)

        def add_button(text: str, page_index: int) -> None:
            btn = SidebarButton(text)
            self.sidebar.addWidget(btn)
            self.button_group.addButton(btn, page_index)
            btn.clicked.connect(lambda: self.stack.setCurrentIndex(page_index))

        add_button("Create", 0)
        add_button("Batch", 1)
        add_button("Planner", 2)
        add_button("Downloader", 3)
        add_button("Settings", 4)
        add_button("Help", 5)
        add_button("Store", 6)
        self.sidebar.addStretch(1)

        # Pages
        self.stack = QtWidgets.QStackedWidget()
        self.create_page = CreatePage(self.config)
        self.batch_page = BatchPage()
        self.planner_page = PlannerPage()
        self.downloader_page = DownloaderPage()
        self.settings_page = SettingsPage(self.config)
        self.help_page = HelpPage()
        self.store_page = StorePage()

        self.stack.addWidget(self.create_page)
        self.stack.addWidget(self.batch_page)
        self.stack.addWidget(self.planner_page)
        self.stack.addWidget(self.downloader_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.help_page)
        self.stack.addWidget(self.store_page)

        # Preview pane
        self.preview = PreviewPane()

        main_layout.addWidget(side_frame)
        main_layout.addWidget(self.stack, 1)
        main_layout.addWidget(self.preview)

        # Logging
        self.log_handler = QTextLogger(self.create_page.log_edit)
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

        # Signals
        self.create_page.generateRequested.connect(self._run_pipeline)
        self.settings_page.configSaved.connect(self._reload_config)
        self.downloader_page.start_btn.clicked.connect(self._start_downloads)

    def _reload_config(self, config: Config) -> None:
        config.validate()
        self.config = config

    def _run_pipeline(self, opts: dict) -> None:
        script = opts.get("script", "")
        if not script:
            QtWidgets.QMessageBox.warning(self, "Validation", "Script is empty")
            return

        title = sanitize_filename(opts.get("title") or script.splitlines()[0][:20] or "session")
        script_name = f"{title}_{now_ts_folder()}"
        script_path = Path("scripts") / f"{script_name}.txt"
        script_path.parent.mkdir(exist_ok=True)
        script_path.write_text(script)

        cfg = load_config()
        cfg.subtitle_style = opts.get("style", cfg.subtitle_style)
        if opts.get("voice"):
            cfg.default_voice_id = opts["voice"]
        if opts.get("background"):
            for key, path in (cfg.background_styles or {}).items():
                if key.lower() == opts["background"].lower():
                    cfg.background_videos_path = path
                    break
        cfg.resolution = opts.get("resolution", cfg.resolution)
        cfg.watermark_enabled = opts.get("watermark", True)
        cfg.validate()

        pipeline = VideoPipeline(cfg, debug=True)
        self.create_page.log_edit.clear()
        try:
            ctx = pipeline.run(script, title, background=opts.get("background"))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return

        self.create_page.output_label.setText(str(ctx.output_dir))
        self.preview.load_video(ctx.final_video_path)

    def _start_downloads(self) -> None:
        urls = self.downloader_page.url_edit.toPlainText().splitlines()
        if not urls:
            return
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Download Folder", str(Path("downloads")))
        if not folder:
            return
        log_dir = Path("downloads/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{now_ts_folder()}.txt"
        dl = Downloader(Path(folder), log_file=log_file, debug=True)
        self.downloader_page.list.clear()
        for u in urls:
            item = QtWidgets.QListWidgetItem(u)
            self.downloader_page.list.addItem(item)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            dl.download_batch(urls)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Download Error", str(e))
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        logging.getLogger().removeHandler(self.log_handler)
        return super().closeEvent(event)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.resize(1200, 700)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

