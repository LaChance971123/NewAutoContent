from __future__ import annotations

import random
import subprocess
from pathlib import Path
from typing import Optional

from .logger import setup_logger


class VideoRenderer:
    def __init__(
        self,
        bg_folder: Path,
        watermark: Path | None = None,
        opacity: float = 1.0,
        resolution: str = "1080x1920",
        ffmpeg_path: str = "ffmpeg",
        log_file: Optional[Path] = None,
        debug: bool = False,
    ):
        self.bg_folder = bg_folder
        self.watermark = watermark if watermark and watermark.exists() else None
        self.opacity = opacity
        self.resolution = resolution
        self.ffmpeg = ffmpeg_path
        self.logger = setup_logger("renderer", log_file, debug)

    def pick_background(self) -> Path:
        videos = list(self.bg_folder.glob("*.mp4"))
        if not videos:
            raise FileNotFoundError("No background videos found")
        return random.choice(videos)

    def render(self, audio_path: Path, subtitles: Path, output_path: Path):
        bg_video = self.pick_background()
        # simple wav validation
        try:
            import wave
            with wave.open(str(audio_path), 'rb') as _:
                pass
        except Exception as e:
            self.logger.error(f"Invalid audio file {audio_path}: {e}")
            raise
        self.logger.info(f"Using background video {bg_video}")
        cmd = [
            self.ffmpeg,
            "-y",
            "-i",
            str(bg_video),
            "-i",
            str(audio_path),
            "-vf", f"subtitles={subtitles}",
            "-s", self.resolution
        ]
        if self.watermark:
            watermark_filter = f"movie={self.watermark}[wm];[in][wm]overlay=W-w-10:H-h-10:format=auto,format=yuv420p"
            cmd.extend(["-vf", watermark_filter])
        cmd.append(str(output_path))
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ffmpeg failed: {e}")
            raise
