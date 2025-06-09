from __future__ import annotations

from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets, QtMultimedia

from pipeline.config import Config
from pipeline.helpers import sanitize_filename
from pipeline.voiceover import VoiceOverGenerator

class ProjectPage(QtWidgets.QWidget):
    generateRequested = QtCore.Signal(dict)

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
        layout.addRow("Subtitle Style", self.style_combo)

        self.wm_check = QtWidgets.QCheckBox("Enable Watermark")
        self.wm_check.setChecked(self.config.watermark_enabled)
        layout.addRow(self.wm_check)

        self.ai_btn = QtWidgets.QPushButton("Create Story with AI")
        self.ai_btn.clicked.connect(self._show_ai_popup)
        layout.addRow(self.ai_btn)

        self.generate_btn = QtWidgets.QPushButton("Generate")
        self.generate_btn.clicked.connect(self._emit_generate)
        layout.addRow(self.generate_btn)

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
            text = Path(path).read_text()
            self.script_edit.setPlainText(text)
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
        temp = Path("_preview.wav")
        gen = VoiceOverGenerator("elevenlabs", self.voice_combo.currentData(), self.config.coqui_model_name)
        if gen.generate("This is a voice preview", temp):
            url = QtCore.QUrl.fromLocalFile(str(temp.resolve()))
            player = QtMultimedia.QMediaPlayer()
            player.setSource(url)
            player.play()
        else:
            QtWidgets.QMessageBox.warning(self, "Preview", "Failed to generate preview")

    def _show_ai_popup(self) -> None:
        QtWidgets.QMessageBox.information(self, "Create Story with AI", "Coming Soon")

    def _update_estimate(self) -> None:
        words = len(self.script_edit.toPlainText().split())
        secs = int(words / 2.5)
        self.output_label.setText(f"Est. {secs}s")


