from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable, Any
from datetime import datetime
import json
import re
import shutil
import threading
import traceback
import wave


def sanitize_name(name: str) -> str:
    """Return a filesystem-safe version of *name*."""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip())
    return cleaned or "session"


def now_ts_folder() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sanitize_filename(name: str) -> str:
    """Alias for sanitize_name for backward compatibility."""
    return sanitize_name(name)


def zip_folder(folder: Path, dest_zip: Path) -> Path:
    """Create a zip archive of *folder* at *dest_zip* (without extension)."""
    dest_zip = dest_zip.with_suffix(".zip")
    base = dest_zip.with_suffix("")
    shutil.make_archive(str(base), "zip", root_dir=folder)
    return dest_zip


def run_with_timeout(func: Callable[..., Any], timeout: float, *args, **kwargs) -> Any:
    """Run *func* with timeout. Raises TimeoutError if timeout exceeded."""
    result: dict[str, Any] = {}
    exc: list[BaseException] = []

    def target() -> None:
        try:
            result["value"] = func(*args, **kwargs)
        except BaseException as e:  # capture all
            exc.append(e)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError(f"{func.__name__} timed out after {timeout}s")
    if exc:
        raise exc[0]
    return result.get("value")


def create_silence(path: Path, duration: float = 1.0) -> None:
    """Create a silent WAV file of *duration* seconds."""
    n_frames = int(44100 * duration)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(b"\x00\x00" * n_frames)


def create_dummy_subtitles(path: Path) -> None:
    """Write a minimal subtitle file when generation fails."""
    text = "[Script Info]\nScriptType: v4.00+\n\n[V4+ Styles]\n" \
        "Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, " \
        "OutlineColour, Bold, Italic, Alignment, MarginL, MarginR, " \
        "MarginV, BorderStyle, Outline, Shadow, Encoding\n" \
        "Style: Default,Arial,48,&H00FFFFFF,&H00000000,&H00000000,0,0,2,10,10,10,1,2,0,0\n" \
        "[Events]\nFormat: Start, End, Style, Text\nDialogue: 0,0:00:00.00,0:00:02.00,Default,Subtitle generation failed\n"
    path.write_text(text)


@dataclass
class PipelineContext:
    script_text: str
    script_name: str
    output_dir: Path
    subtitle_style: str
    voice_engine: str
    voice_id: Optional[str] = None
    voiceover_path: Path = field(init=False)
    subtitles_path: Path = field(init=False)
    final_video_path: Path = field(init=False)
    script_path: Path = field(init=False)
    log_file: Optional[Path] = None
    debug: bool = False
    timestamp: str = field(default_factory=iso_timestamp)

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voiceover_path = self.output_dir / "voice.wav"
        self.subtitles_path = self.output_dir / "subtitles.ass"
        self.final_video_path = self.output_dir / "final_video.mp4"
        self.script_path = self.output_dir / f"{self.script_name}.txt"
        if not self.script_path.exists():
            self.script_path.write_text(self.script_text)

    def save_metadata(self, status: str = "success"):
        metadata = {
            "title": self.script_name,
            "subtitle_style": self.subtitle_style,
            "voice_id": self.voice_id or "",
            "voice_engine": self.voice_engine.capitalize(),
            "timestamp": self.timestamp,
            "status": status,
        }
        with open(self.output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    def write_summary(self):
        summary = (
            f"Title: {self.script_name}\n"
            f"Subtitle style: {self.subtitle_style}\n"
            f"Voice engine: {self.voice_engine}\n"
            f"Timestamp: {self.timestamp}\n"
        )
        (self.output_dir / "summary.txt").write_text(summary)

    def archive(self):
        zip_path = zip_folder(self.output_dir, self.output_dir)
        return zip_path

    def write_error_trace(self, exc: BaseException) -> None:
        """Write traceback of *exc* to error_trace.txt"""
        trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        (self.output_dir / "error_trace.txt").write_text(trace)

    def save_config_snapshot(self, config: dict) -> None:
        with open(self.output_dir / "session_config.json", "w") as f:
            json.dump(config, f, indent=2)


# ---------------------------------------------------------------------------
# Utility functions for CLI feedback
# ---------------------------------------------------------------------------

RESET = "\033[0m"
COLORS = {
    "INFO": "\033[36m",
    "ERROR": "\033[31m",
    "SUCCESS": "\033[32m",
}


def color_print(tag: str, message: str) -> None:
    """Print *message* with colored [TAG] prefix."""
    color = COLORS.get(tag.upper(), "")
    print(f"{color}[{tag.upper()}]{RESET} {message}")


LOG_DIR = Path("logs")
ERROR_TRACE_FILE = LOG_DIR / "error_trace.txt"


def log_trace(exc: BaseException) -> None:
    """Append traceback of *exc* to logs/error_trace.txt."""
    LOG_DIR.mkdir(exist_ok=True)
    trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    with open(ERROR_TRACE_FILE, "a") as f:
        f.write(f"{iso_timestamp()} - {type(exc).__name__}: {exc}\n")
        f.write(trace + "\n")


def validate_files(*paths: Path) -> list[Path]:
    """Return a list of paths that are missing or empty."""
    missing: list[Path] = []
    for p in paths:
        if not p.exists() or p.stat().st_size == 0:
            missing.append(p)
    return missing


def preview_voice(engine: str, voice_id: str, coqui_model: str) -> Path:
    """Generate and play a short voice preview."""
    from .voiceover import VoiceOverGenerator

    preview = Path("_preview.wav")
    generator = VoiceOverGenerator(engine, voice_id, coqui_model)
    try:
        generator.generate(f"This is a sample of {voice_id}", preview)
        try:
            from playsound import playsound  # pragma: no cover - optional dep

            playsound(str(preview))
        except Exception:
            pass
    except Exception as e:  # pragma: no cover - runtime failures
        color_print("ERROR", f"Voice preview failed: {e}")
        log_trace(e)
    return preview
