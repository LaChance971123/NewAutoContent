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
        self.logger = setup_logger("renderer", log_file, debug)
        self.bg_root = bg_folder.parent
        self.bg_folder = self._resolve_folder(bg_folder)
        self.watermark = watermark if watermark and watermark.exists() else None
        self.opacity = opacity
        self.resolution = resolution
        self.ffmpeg = ffmpeg_path

    def _list_videos(self, folder: Path) -> list[Path]:
        return [p for p in folder.glob("*") if p.suffix.lower() in {".mp4", ".webm"}]

    def _resolve_folder(self, folder: Path) -> Path:
        folder = folder.resolve()
        if folder.exists():
            videos = self._list_videos(folder)
            if videos:
                return folder
            self.logger.error(f"No background videos found in {folder}")
        # try case-insensitive search in root
        root = folder.parent
        if not root.exists():
            raise FileNotFoundError(f"Background root {root} does not exist")
        target = folder.name.lower()
        for cand in root.iterdir():
            if cand.is_dir() and cand.name.lower() == target:
                videos = self._list_videos(cand)
                if videos:
                    self.logger.info(f"Resolved background folder to {cand}")
                    return cand
                self.logger.error(f"No background videos found in {cand}")
                break
        # fallback to any folder with videos
        for cand in root.iterdir():
            if cand.is_dir() and self._list_videos(cand):
                self.logger.warning(
                    f"Falling back to {cand} due to missing {folder.name} videos"
                )
                return cand
        raise FileNotFoundError(f"No background videos found in {root}")

    def pick_background(self) -> Path:
        videos = self._list_videos(self.bg_folder)
        if not videos:
            self.logger.error(f"No background videos found in {self.bg_folder}")
            raise FileNotFoundError("No background videos found")
        choice = random.choice(videos)
        self.logger.info(f"Selected background video {choice}")
        return choice

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
