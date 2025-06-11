from PySide6 import QtWidgets, QtCore
import json
import logging
import subprocess
import os
from pipeline.config import Config
from pipeline import config_loader


class SettingsPage(QtWidgets.QWidget):
    developerModeChanged = QtCore.Signal(bool)
    themeChanged = QtCore.Signal(str)

    def __init__(self, config: Config | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config or Config()
        layout = QtWidgets.QFormLayout(self)
        self.dev_check = QtWidgets.QCheckBox("Enable Developer Mode")
        self.dev_check.setChecked(self.config.developer_mode)
        layout.addRow(self.dev_check)
        self.top_check = QtWidgets.QCheckBox("Always on Top")
        self.top_check.setChecked(self.config.always_on_top)
        layout.addRow(self.top_check)
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.config.theme)
        layout.addRow("Theme", self.theme_combo)
        self.config_view = QtWidgets.QPlainTextEdit()
        self.config_view.setReadOnly(True)
        self.config_view.setVisible(self.config.developer_mode)
        layout.addRow("Config", self.config_view)
        self.check_btn = QtWidgets.QPushButton("System Check")
        self.check_btn.clicked.connect(self._run_check)
        layout.addRow(self.check_btn)
        self._update_config()
        self.dev_check.toggled.connect(self._toggle_dev)
        self.theme_combo.currentTextChanged.connect(self._emit_theme)
        self.top_check.toggled.connect(self._toggle_top)

    def _toggle_dev(self, state: bool) -> None:
        self.config.developer_mode = state
        self.config_view.setVisible(state)
        self._update_config()
        self.developerModeChanged.emit(state)

    def _emit_theme(self, theme: str) -> None:
        self.config.theme = theme
        self.themeChanged.emit(theme)

    def _toggle_top(self, state: bool) -> None:
        self.config.always_on_top = state
        self._update_config()

    def _update_config(self) -> None:
        self.config_view.setPlainText(json.dumps(self.config.__dict__, indent=2))

    def _run_check(self) -> None:
        logger = logging.getLogger("system_check")
        ffmpeg = self.config.ffmpeg_path
        try:
            out = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True)
            if out.returncode == 0:
                logger.info(out.stdout.splitlines()[0])
            else:
                logger.error(f"ffmpeg check failed: {out.stderr}")
        except Exception as e:
            logger.error(f"ffmpeg error: {e}")

        try:
            import requests
            r = requests.get("https://example.com", timeout=5)
            logger.info("Internet OK" if r.ok else "Internet check failed")
        except Exception as e:
            logger.warning(f"Internet check failed: {e}")

        if self.config.voice_engine == "elevenlabs":
            if config_loader.validate_elevenlabs(self.config.__dict__, logger):
                logger.info("ElevenLabs configured")
            else:
                logger.warning("ElevenLabs not configured")

        try:
            from TTS.utils.manage import ModelManager  # type: ignore
            ModelManager()
            logger.info("Coqui TTS available")
        except Exception:
            logger.warning("Coqui TTS not installed")
