from __future__ import annotations

from pathlib import Path
from PySide6 import QtCore, QtWidgets
from pipeline.config import Config


class BatchPage(QtWidgets.QWidget):
    batchRequested = QtCore.Signal(list, dict)

    def __init__(self, config: Config, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.files: list[Path] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QFormLayout(self)

        file_layout = QtWidgets.QHBoxLayout()
        self.file_list = QtWidgets.QListWidget()
        file_layout.addWidget(self.file_list, 1)
        add_btn = QtWidgets.QPushButton("Add Files")
        add_btn.clicked.connect(self._add_files)
        file_layout.addWidget(add_btn)
        layout.addRow("Scripts", file_layout)

        self.voice_combo = QtWidgets.QComboBox()
        for name, vid in (self.config.voices or {}).items():
            self.voice_combo.addItem(name, vid)
        layout.addRow("Voice", self.voice_combo)

        self.bg_combo = QtWidgets.QComboBox()
        for name in (self.config.background_styles or {}).keys():
            self.bg_combo.addItem(name)
        layout.addRow("Background", self.bg_combo)

        self.platform_combo = QtWidgets.QComboBox()
        self.platform_combo.addItems(["TikTok", "Reels", "Shorts", "Square"])
        layout.addRow("Platform", self.platform_combo)

        run_btn = QtWidgets.QPushButton("Run Batch")
        run_btn.clicked.connect(self._emit_batch)
        layout.addRow(run_btn)

    def _add_files(self) -> None:
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Select Scripts", "scripts", "Text Files (*.txt *.docx)"
        )
        for p in paths:
            path = Path(p)
            if path not in self.files:
                self.files.append(path)
                self.file_list.addItem(path.name)

    def _emit_batch(self) -> None:
        opts = {
            "voice": self.voice_combo.currentData(),
            "background": self.bg_combo.currentText(),
            "platform": self.platform_combo.currentText(),
        }
        self.batchRequested.emit(self.files, opts)
