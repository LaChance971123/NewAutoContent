from qt_core import *
from gui.core.json_settings import Settings
from gui.core.json_themes import Themes
from gui.widgets import PyPushButton, PyToggle, PyLineEdit


def _load_theme() -> dict:
    try:
        return Themes().items["app_color"]
    except Exception:
        return {
            "dark_one": "#1C1F22",
            "dark_three": "#2E3338",
            "text_foreground": "#F5F7FA",
            "context_color": "#377DFF",
            "context_hover": "#4A8BFF",
            "context_pressed": "#2554CE",
        }

_THEME = _load_theme()
_FONT_FAMILY = Settings().items["font"]["family"]


def _header(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"font-weight: bold; margin-bottom: 4px; font-family: '{_FONT_FAMILY}'"
    )
    return lbl


class HomePageWidget(QWidget):
    """Home page with basic placeholders."""

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(f"font-family: '{_FONT_FAMILY}'")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Script input
        main_layout.addWidget(_header("\U0001F3AC Script Input"))
        self.script_edit = QTextEdit()
        self.script_edit.setPlaceholderText("Enter or drop your story/script here...")
        self.script_edit.setStyleSheet(
            f"background: {_THEME['dark_three']}; color: {_THEME['text_foreground']};"
        )
        main_layout.addWidget(self.script_edit)

        # Controls area
        main_layout.addWidget(_header("\U0001F399\ufe0f Voice & Subtitle Controls"))
        ctrl_container = QWidget()
        ctrl_layout = QGridLayout(ctrl_container)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setHorizontalSpacing(10)
        ctrl_layout.setVerticalSpacing(10)

        ctrl_layout.addWidget(QLabel("Voice:"), 0, 0)
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["Default", "Voice 1", "Voice 2"])
        ctrl_layout.addWidget(self.voice_combo, 0, 1)

        ctrl_layout.addWidget(QLabel("Background:"), 1, 0)
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["Default", "Style 1", "Style 2"])
        ctrl_layout.addWidget(self.bg_combo, 1, 1)

        ctrl_layout.addWidget(QLabel("Resolution:"), 2, 0)
        self.res_combo = QComboBox()
        self.res_combo.addItems(["720p", "1080p"])
        ctrl_layout.addWidget(self.res_combo, 2, 1)

        ctrl_layout.addWidget(QLabel("Include Watermark:"), 3, 0)
        self.watermark_toggle = PyToggle(
            bg_color=_THEME["dark_three"],
            circle_color=_THEME["text_foreground"],
            active_color=_THEME["context_color"],
        )
        ctrl_layout.addWidget(self.watermark_toggle, 3, 1)

        main_layout.addWidget(ctrl_container)

        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)

        self.ai_btn = PyPushButton(
            "Generate with AI",
            8,
            _THEME["text_foreground"],
            _THEME["context_color"],
            _THEME["context_hover"],
            _THEME["context_pressed"],
        )
        self.random_btn = PyPushButton(
            "Randomize",
            8,
            _THEME["text_foreground"],
            _THEME["dark_one"],
            _THEME["dark_three"],
            _THEME["context_pressed"],
        )
        self.create_btn = PyPushButton(
            "Create Content",
            8,
            _THEME["text_foreground"],
            _THEME["context_color"],
            _THEME["context_hover"],
            _THEME["context_pressed"],
        )
        btn_layout.addWidget(self.ai_btn)
        btn_layout.addWidget(self.random_btn)
        btn_layout.addWidget(self.create_btn)

        main_layout.addWidget(btn_container)

        # Preview area
        main_layout.addWidget(_header("\U0001F3A5 Preview Pane"))
        self.preview = QLabel("Video preview placeholder")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(200)
        self.preview.setStyleSheet(
            f"background: {_THEME['dark_one']};"
            f"color: {_THEME['text_foreground']};"
            "padding: 40px; border-radius: 8px;"
        )
        main_layout.addWidget(self.preview)
        main_layout.addStretch()


class SettingsPageWidget(QWidget):
    """Placeholder settings page with basic fields."""

    status_request = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(f"font-family: '{_FONT_FAMILY}'")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        layout.addWidget(_header("\u2699\ufe0f General Settings"))
        self.api_edit = PyLineEdit(
            place_holder_text="API Key",
            radius=8,
            border_size=2,
            color=_THEME["text_foreground"],
            selection_color=_THEME["text_foreground"],
            bg_color=_THEME["dark_three"],
            bg_color_active=_THEME["dark_four"],
            context_color=_THEME["context_color"],
        )
        layout.addWidget(self.api_edit)

        layout.addWidget(_header("\U0001F5C2\ufe0f Output Options"))
        folder_row = QHBoxLayout()
        self.output_edit = PyLineEdit(
            place_holder_text="Output Folder",
            radius=8,
            border_size=2,
            color=_THEME["text_foreground"],
            selection_color=_THEME["text_foreground"],
            bg_color=_THEME["dark_three"],
            bg_color_active=_THEME["dark_four"],
            context_color=_THEME["context_color"],
        )
        self.browse_btn = PyPushButton(
            "Browse",
            8,
            _THEME["text_foreground"],
            _THEME["dark_one"],
            _THEME["dark_three"],
            _THEME["context_pressed"],
        )
        self.browse_btn.clicked.connect(lambda: self.status_request.emit("Browse not implemented"))
        folder_row.addWidget(self.output_edit)
        folder_row.addWidget(self.browse_btn)
        layout.addLayout(folder_row)

        layout.addWidget(_header("\U0001F50A Voice Settings"))
        layout.addWidget(QLabel("Voice settings placeholder"))
        layout.addStretch()


class HelpPageWidget(QWidget):
    """Scrollable help page."""

    status_request = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet(f"font-family: '{_FONT_FAMILY}'")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        cont_layout = QVBoxLayout(container)
        cont_layout.setContentsMargins(0, 0, 0, 0)
        cont_layout.setSpacing(10)

        def section(title: str, text: str) -> None:
            cont_layout.addWidget(_header(title))
            body = QLabel(text)
            body.setWordWrap(True)
            cont_layout.addWidget(body)

        section("Getting Started", "Instructions will appear here.")
        section("Output Overview", "Information about output folders.")
        section("Troubleshooting", "Common issues and solutions.")
        cont_layout.addStretch()

        layout.addWidget(scroll)
        self.copy_btn = PyPushButton(
            "Copy Logs",
            8,
            _THEME["text_foreground"],
            _THEME["dark_one"],
            _THEME["dark_three"],
            _THEME["context_pressed"],
        )
        self.copy_btn.clicked.connect(lambda: self.status_request.emit("Logs copied"))
        layout.addWidget(self.copy_btn, alignment=Qt.AlignLeft)
        layout.addStretch()


class AboutPageWidget(QWidget):
    """Simple about page."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        layout.addWidget(_header("About AutoContent"))
        layout.addWidget(QLabel("Version 0.1\nPowered by PyOneDark"))
        layout.addStretch()


__all__ = [
    "HomePageWidget",
    "SettingsPageWidget",
    "HelpPageWidget",
    "AboutPageWidget",
]
