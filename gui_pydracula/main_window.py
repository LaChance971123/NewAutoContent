from __future__ import annotations

import logging
import subprocess
import traceback
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui

from pipeline.config import Config
from pipeline.pipeline import VideoPipeline
from pipeline.helpers import now_ts_folder, sanitize_filename, validate_video

from .pages.home import HomePage
from .pages.settings import SettingsPage
from .pages.batch import BatchPage
from .pages.help import HelpPage
from .pages.about import AboutPage


class QTextLogger(logging.Handler):
    """Send logging output to a QPlainTextEdit widget."""

    def __init__(self, edit: QtWidgets.QPlainTextEdit) -> None:
        super().__init__()
        self.edit = edit
        self.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        QtCore.QMetaObject.invokeMethod(
            self.edit,
            "appendPlainText",
            QtCore.Qt.ConnectionType.QueuedConnection,
        QtCore.Q_ARG(str, msg),
        )


class WalkthroughOverlay(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Tool)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        msg = QtWidgets.QLabel(
            "<h2>Welcome to AutoContent</h2><p>Fill in your script and options then click Generate.</p>"
        )
        msg.setStyleSheet("color:white;background:rgba(0,0,0,180);padding:20px;border-radius:8px")
        layout.addWidget(msg)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:  # type: ignore[override]
        self.close()

class UploadDialog(QtWidgets.QDialog):
    def __init__(self, folder: Path, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Upload Assistant")
        layout = QtWidgets.QVBoxLayout(self)
        results = validate_video(folder / "final_video.mp4", (folder / "subtitles.ass").exists())
        form = QtWidgets.QFormLayout()
        for key, val in results.items():
            if key == "exists":
                continue
            label = QtWidgets.QLabel("✅" if val else "❌")
            form.addRow(key.capitalize(), label)
        layout.addLayout(form)
        btn_row = QtWidgets.QHBoxLayout()
        copy_btn = QtWidgets.QPushButton("Copy Metadata")
        open_btn = QtWidgets.QPushButton("Open Folder")
        tiktok_btn = QtWidgets.QPushButton("TikTok")
        yt_btn = QtWidgets.QPushButton("YT Shorts")
        btn_row.addWidget(copy_btn)
        btn_row.addWidget(open_btn)
        btn_row.addWidget(tiktok_btn)
        btn_row.addWidget(yt_btn)
        layout.addLayout(btn_row)
        copy_btn.clicked.connect(lambda: QtWidgets.QApplication.clipboard().setText((folder / "summary.txt").read_text()))
        open_btn.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(folder))))
        tiktok_btn.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://www.tiktok.com/upload")))
        yt_btn.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://studio.youtube.com")))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AutoContent")
        self.resize(1200, 700)
        self.config = Config.load(Path("config/config.json"))
        self.config.validate()
        self._apply_theme(self.config.theme)
        self._apply_top(self.config.always_on_top)
        QtWidgets.QToolTip.setFont(QtGui.QFont("Arial", 10))
        self._build_ui()
        if self.config.first_launch:
            QtCore.QTimer.singleShot(300, self._show_walkthrough)
    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root_layout = QtWidgets.QVBoxLayout(central)

        # top bar
        top = QtWidgets.QFrame()
        top_layout = QtWidgets.QHBoxLayout(top)
        title = QtWidgets.QLabel("AutoContent")
        title.setObjectName("TopTitle")
        top_layout.addWidget(title)
        top_layout.addStretch(1)
        help_btn = QtWidgets.QToolButton()
        help_btn.setText("?")
        help_btn.clicked.connect(self._show_walkthrough)
        top_layout.addWidget(help_btn)
        root_layout.addWidget(top, 0)

        # center layout
        center = QtWidgets.QHBoxLayout()
        root_layout.addLayout(center, 1)

        # sidebar
        sidebar = QtWidgets.QFrame()
        sidebar.setFixedWidth(150)
        side_layout = QtWidgets.QVBoxLayout(sidebar)
        self.home_btn = QtWidgets.QPushButton("Home")
        self.home_btn.setIcon(QtGui.QIcon("gui/images/icons/cil-home.png"))
        self.batch_btn = QtWidgets.QPushButton("Batch")
        self.batch_btn.setIcon(QtGui.QIcon("gui/images/icons/cil-featured-playlist.png"))
        self.help_btn = QtWidgets.QPushButton("Help")
        self.help_btn.setIcon(QtGui.QIcon("gui/images/icons/cil-lightbulb.png"))
        self.about_btn = QtWidgets.QPushButton("About")
        self.about_btn.setIcon(QtGui.QIcon("gui/images/icons/cil-star.png"))
        self.settings_btn = QtWidgets.QPushButton("Settings")
        self.settings_btn.setIcon(QtGui.QIcon("gui/images/icons/cil-settings.png"))
        for btn in (
            self.home_btn,
            self.batch_btn,
            self.help_btn,
            self.about_btn,
            self.settings_btn,
        ):
            side_layout.addWidget(btn)
        side_layout.addStretch(1)
        center.addWidget(sidebar)

        # stacked pages
        self.stack = QtWidgets.QStackedWidget()
        self.home_page = HomePage(self.config)
        self.home_page.generateRequested.connect(self._run_pipeline)
        self.home_page.configChanged.connect(self._update_preview)
        self.stack.addWidget(self.home_page)
        self.batch_page = BatchPage(self.config)
        self.batch_page.batchRequested.connect(self._run_batch)
        self.stack.addWidget(self.batch_page)
        self.help_page = HelpPage()
        self.stack.addWidget(self.help_page)
        self.about_page = AboutPage()
        self.stack.addWidget(self.about_page)
        self.settings_page = SettingsPage(self.config)
        self.settings_page.developerModeChanged.connect(self._set_dev_mode)
        self.settings_page.themeChanged.connect(self._apply_theme)
        self.settings_page.top_check.toggled.connect(self._apply_top)
        self.stack.addWidget(self.settings_page)
        center.addWidget(self.stack, 1)

        # home page preview handled internally

        # log view (on homepage)
        self.log_edit = self.home_page.log_edit

        # connections
        self.home_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.home_page))
        self.batch_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.batch_page))
        self.help_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.help_page))
        self.about_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.about_page))
        self.settings_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.settings_page))

        self.log_handler = QTextLogger(self.log_edit)
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)
        self._update_preview(self.home_page._collect_opts())
        self.home_page.set_status("idle", "Idle")

        # shortcuts
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+N"), self, activated=self._new_project)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+O"), self, activated=self.home_page._load_script)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+G"), self, activated=self.home_page._emit_generate)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Q"), self, activated=self.close)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+D"), self, activated=lambda: self.settings_page.dev_check.toggle())

    def _run_pipeline(self, opts: dict) -> None:
        script = opts.get("script", "").strip()
        if not script:
            QtWidgets.QMessageBox.warning(self, "Validation", "Script is empty")
            return

        title = sanitize_filename(opts.get("title") or script.splitlines()[0][:20] or "session")
        folder = opts.get("folder") or f"output/{title}_{now_ts_folder()}"
        out_dir = Path(folder)
        if out_dir.exists():
            resp = QtWidgets.QMessageBox.question(
                self,
                "Folder Exists",
                f"{folder} exists. Overwrite?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            )
            if resp == QtWidgets.QMessageBox.StandardButton.No:
                new_name, ok = QtWidgets.QInputDialog.getText(self, "Rename", "New folder name", text=folder)
                if not ok:
                    return
                folder = new_name
                out_dir = Path(folder)
        script_name = out_dir.name
        script_path = Path("scripts") / f"{script_name}.txt"
        script_path.parent.mkdir(exist_ok=True)
        script_path.write_text(script)

        cfg = Config.load(Path("config/config.json"))
        cfg.subtitle_style = opts.get("subtitle_style", cfg.subtitle_style)
        if opts.get("voice"):
            cfg.default_voice_id = opts["voice"]
        if opts.get("background"):
            for key, path in (cfg.background_styles or {}).items():
                if key.lower() == opts["background"].lower():
                    cfg.background_videos_path = path
                    break
        platform = opts.get("platform")
        if platform == "Square":
            cfg.resolution = "1080x1080"
        elif platform:
            cfg.resolution = "1080x1920"
        cfg.validate()

        pipeline = VideoPipeline(cfg, debug=True)
        self.log_edit.clear()
        self.home_page.set_status("running", "Running")
        try:
            ctx = pipeline.run(
                script,
                title,
                background=opts.get("background"),
                output=out_dir / "final_video.mp4",
                intro=Path(opts.get("intro_path")) if opts.get("intro") else None,
                outro=Path(opts.get("outro_path")) if opts.get("outro") else None,
                trim_silence=opts.get("trim_silence", False),
                crop_safe=opts.get("crop_safe", False),
                summary_overlay=opts.get("summary_overlay", False),
            )
        except Exception as e:
            self.home_page.set_status("error", "Failed")
            trace = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            self.home_page.show_error(trace)
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return

        self.home_page.set_output(ctx.output_dir)
        thumb = ctx.output_dir / "thumb.jpg"
        try:
            subprocess.run([
                "ffmpeg",
                "-y",
                "-i",
                str(ctx.final_video_path),
                "-frames:v",
                "1",
                str(thumb),
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.home_page.set_thumbnail(thumb)
        except Exception:
            pass
        QtWidgets.QMessageBox.information(self, "Success", f"Video saved to {ctx.final_video_path}")
        self.home_page.set_status("success", "Done")
        self.home_page.show_error("")
        dlg = UploadDialog(ctx.output_dir, self)
        dlg.exec()

    def _run_batch(self, files: list[Path], opts: dict) -> None:
        if not files:
            QtWidgets.QMessageBox.warning(self, "Batch", "No files selected")
            return
        for idx, path in enumerate(files, 1):
            text = Path(path).read_text()
            name = Path(path).stem
            self.home_page.set_status("running", f"{idx}/{len(files)}")
            try:
                self._run_pipeline({
                    "title": name,
                    "script": text,
                    "voice": opts.get("voice"),
                    "subtitle_style": self.config.subtitle_style,
                    "background": opts.get("background"),
                    "platform": opts.get("platform"),
                })
            except Exception:
                continue
        self.home_page.set_status("success", "Batch Done")

    def _update_preview(self, opts: dict) -> None:
        text = (
            f"Voice: {opts.get('voice') or self.config.default_voice_id}\n"
            f"Style: {opts.get('subtitle_style')}\n"
            f"Background: {opts.get('background')}\n"
            f"Platform: {opts.get('platform')}\n"
            f"Resolution: {self.home_page.resolution_label.text()}"
        )
        self.home_page.set_preview_summary(text)

    def _set_dev_mode(self, state: bool) -> None:
        self.config.developer_mode = state
        self.config.save(Path("config/config.json"))

    def _apply_theme(self, theme: str) -> None:
        palette = QtGui.QPalette()
        if theme == "light":
            palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#FAFAFA"))
            palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#202020"))
            accent = "#1565C0"
        else:
            palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#0F111A"))
            palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#FFFFFF"))
            accent = "#448AFF"
        palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(accent))
        QtWidgets.QApplication.instance().setPalette(palette)
        self.config.theme = theme
        self.config.save(Path("config/config.json"))

    def _apply_top(self, state: bool) -> None:
        flags = self.windowFlags()
        if state:
            flags |= QtCore.Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~QtCore.Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self.config.always_on_top = state
        self.config.save(Path("config/config.json"))

    def _new_project(self) -> None:
        self.home_page.reset_form()

    def _show_walkthrough(self) -> None:
        overlay = WalkthroughOverlay(self)
        overlay.resize(self.size())
        overlay.show()
        self.config.first_launch = False

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # type: ignore[name-mismatch]
        logging.getLogger().removeHandler(self.log_handler)
        self.config.save(Path("config/config.json"))
        super().closeEvent(event)
