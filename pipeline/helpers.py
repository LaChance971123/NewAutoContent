from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from datetime import datetime
import json
import re
import shutil


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
