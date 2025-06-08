from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class Config:
    subtitle_style: str = "simple"
    watermark_path: str | None = None
    watermark_opacity: float = 1.0
    watermark_enabled: bool = True
    voice_engine: str = "elevenlabs"
    default_voice_id: str | None = None
    coqui_model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"
    coqui_vocoder_name: str = "vocoder_models/en/ljspeech/hifigan_v2"
    background_videos_path: str = "assets/backgrounds"
    resolution: str = "1080x1920"
    ffmpeg_path: str = "ffmpeg"
    safe_mode: bool = False
    developer_mode: bool = False
    voices: dict[str, str] | None = None
    background_styles: dict[str, str] | None = None
    resolutions: list[str] | None = None

    @classmethod
    def load(cls, path: Path) -> "Config":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        return cls(**data)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=2)

