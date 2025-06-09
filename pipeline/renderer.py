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
            # if folder is a root containing subfolders, try them
            subdirs = [p for p in folder.iterdir() if p.is_dir()]
            for sub in subdirs:
                vids = self._list_videos(sub)
                if vids:
                    self.logger.warning(
                        f"Falling back to {sub} due to missing videos in {folder}"
                    )
                    return sub
            self.logger.warning(
                f"No background videos found in '{folder}'. Please add videos or pick another style."
            )
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
        # fallback to default 'Rain' folder if available
        for cand in root.iterdir():
            if cand.is_dir() and cand.name.lower() == "rain" and self._list_videos(cand):
                self.logger.warning(
                    f"Falling back to {cand} due to missing {folder.name} videos"
                )
                return cand
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

    def render(self, audio_path: Path, subtitles: Path | None, output_path: Path):
        """Render the final video using *audio_path* and optional *subtitles*.

        Automatically switches to ``-filter_complex`` when a watermark and
        subtitles are both present. All paths are converted to POSIX style to
        avoid Windows escaping issues.
        """
        self.logger.info("Starting FFmpeg render")

        if output_path.suffix.lower() != ".mp4":
            raise ValueError("Output path must end with .mp4")

        bg_video = self.pick_background()

        # simple wav validation
        try:
            import wave

            with wave.open(str(audio_path), "rb") as _:
                pass
        except Exception as e:
            self.logger.error(f"Invalid audio file {audio_path}: {e}")
            raise

        self.logger.info(f"Using background video {bg_video}")

        bg = bg_video.as_posix()
        audio = audio_path.as_posix()
        subs = subtitles.as_posix() if subtitles and subtitles.exists() else None
        wm = self.watermark.as_posix() if self.watermark else None

        base_cmd = [self.ffmpeg, "-y", "-i", bg, "-i", audio]

        # Determine filters
        if subs and wm:
            filter_complex = (
                f"[0:v]subtitles='{subs}'[vsubs];"
                f"movie={wm}[wm];"
                f"[vsubs][wm]overlay=W-w-10:H-h-10,format=yuv420p[v]"
            )
            cmd = base_cmd + [
                "-filter_complex",
                filter_complex,
                "-map",
                "[v]",
                "-map",
                "1:a",
            ]
        else:
            vf_parts = []
            if subs:
                vf_parts.append(f"subtitles='{subs}'")
            if wm:
                vf_parts.append(
                    "movie="
                    + wm
                    + "[wm];[in][wm]overlay=W-w-10:H-h-10:format=auto"
                )
            vf_parts.append("format=yuv420p")
            vf = ";".join(vf_parts) if wm and not subs else ",".join(vf_parts)
            cmd = base_cmd + ["-vf", vf]

        cmd += ["-s", self.resolution, output_path.as_posix()]

        self.logger.debug("FFmpeg command: " + " ".join(cmd))

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.stdout:
                self.logger.debug(result.stdout)
            if result.stderr:
                self.logger.debug(result.stderr)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ffmpeg failed: {e.stderr}")
            raise

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("Render produced no output")

        self.logger.info(f"Render complete: {output_path}")
