from __future__ import annotations

import logging
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets, QtMultimedia, QtMultimediaWidgets

from pipeline.config import Config
from pipeline.pipeline import VideoPipeline
from pipeline.helpers import now_ts_folder, sanitize_filename

from .project_page import ProjectPage

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


class PreviewPane(QtWidgets.QFrame):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PreviewPhone")
        self.setFixedWidth(250)
        layout = QtWidgets.QVBoxLayout(self)
        self.player = QtMultimedia.QMediaPlayer(self)
        self.video = QtMultimediaWidgets.QVideoWidget(self)
        self.player.setVideoOutput(self.video)
        layout.addWidget(self.video)

    def load_video(self, path: Path) -> None:
        if path.exists():
            url = QtCore.QUrl.fromLocalFile(str(path.resolve()))
            self.player.setSource(url)
            self.player.setLoops(-1)
            self.player.play()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AutoContent")
        self.config = Config.load(Path("config/config.json"))
        self.config.validate()
        self._build_ui()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QHBoxLayout(central)

        # Sidebar
        side_layout = QtWidgets.QVBoxLayout()
        side_frame = QtWidgets.QFrame()
        side_frame.setLayout(side_layout)
        side_frame.setFixedWidth(150)

        self.button_group = QtWidgets.QButtonGroup(self)
        self.button_group.setExclusive(True)

        def add_button(text: str, page_index: int) -> None:
            btn = QtWidgets.QToolButton()
            btn.setText(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda: self.stack.setCurrentIndex(page_index))
            side_layout.addWidget(btn)
            self.button_group.addButton(btn, page_index)

        add_button("Project", 0)
        side_layout.addStretch(1)

        # Pages
        self.stack = QtWidgets.QStackedWidget()
        self.project_page = ProjectPage(self.config)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.project_page)
        self.stack.addWidget(scroll)

        # Preview pane
        self.preview = PreviewPane()

        main_layout.addWidget(side_frame)
        main_layout.addWidget(self.stack, 1)
        main_layout.addWidget(self.preview)

        # Logging
        self.log_handler = QTextLogger(self.project_page.log_edit)
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

        # Signals
        self.project_page.generateRequested.connect(self._run_pipeline)

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

        cfg = Config.load(Path("config/config.json"))
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
        self.project_page.log_edit.clear()
        try:
            ctx = pipeline.run(script, title, background=opts.get("background"))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return

        self.project_page.output_label.setText(str(ctx.output_dir))
        self.preview.load_video(ctx.final_video_path)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        logging.getLogger().removeHandler(self.log_handler)
        return super().closeEvent(event)


def main() -> None:
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    style_file = Path(__file__).with_name("style.qss")
    if style_file.exists():
        app.setStyleSheet(style_file.read_text())
    win = MainWindow()
    win.resize(1200, 700)
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
