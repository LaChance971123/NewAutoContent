from __future__ import annotations

import os
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from .logger import setup_logger

load_dotenv()


class VoiceOverGenerator:
    def __init__(
        self,
        engine: str,
        voice_id: Optional[str] = None,
        coqui_model_name: str | None = None,
        coqui_vocoder_name: str | None = None,
        debug: bool = False,
        log_file: Optional[Path] = None,
    ):
        self.engine = engine
        self.voice_id = voice_id
        self.coqui_model_name = coqui_model_name or "tts_models/en/ljspeech/tacotron2-DDC"
        self.coqui_vocoder_name = coqui_vocoder_name
        self.logger = setup_logger("voiceover", log_file, debug)
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID")

    def generate(self, text: str, output_path: Path) -> bool:
        self.logger.info(f"Generating voiceover using {self.engine}")
        if self.engine == "elevenlabs":
            if not self.api_key or not self.voice_id:
                self.logger.error("ElevenLabs voice ID not found. Falling back to Coqui TTS.")
                return self._generate_coqui(text, output_path)
            if self._generate_elevenlabs(text, output_path):
                return True
            self.logger.error("ElevenLabs generation failed. Falling back to Coqui TTS.")
            return self._generate_coqui(text, output_path)

        return self._generate_coqui(text, output_path)

    def _generate_elevenlabs(self, text: str, output_path: Path) -> bool:
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {"xi-api-key": self.api_key}
            response = requests.post(url, json={"text": text}, headers=headers)
            if response.status_code >= 400:
                self.logger.error(
                    f"ElevenLabs API error {response.status_code}: {response.text}"
                )
                return False
            output_path.write_bytes(response.content)
            return True
        except Exception as e:
            self.logger.error(f"ElevenLabs generation failed: {e}")
            return False

    def _generate_coqui(self, text: str, output_path: Path) -> bool:
        try:
            from TTS.api import TTS
            from TTS.utils.manage import ModelManager
        except Exception as e:  # fallback import error or runtime
            self.logger.error(f"Coqui TTS not available: {e}")
            return False

        try:
            tts = TTS(
                model_name=self.coqui_model_name,
                vocoder_name=self.coqui_vocoder_name,
                progress_bar=False,
            )
        except Exception:
            self.logger.info("Downloading Coqui TTS model...")
            manager = ModelManager()
            try:
                manager.download_model(self.coqui_model_name)
                if self.coqui_vocoder_name:
                    manager.download_model(self.coqui_vocoder_name)
                tts = TTS(
                    model_name=self.coqui_model_name,
                    vocoder_name=self.coqui_vocoder_name,
                    progress_bar=False,
                )
            except Exception as e:
                self.logger.error(f"Coqui TTS download failed: {e}")
                return False

        try:
            tts.tts_to_file(text=text, file_path=str(output_path))
            return True
        except Exception as e:
            self.logger.error(f"Coqui TTS generation failed: {e}")
            return False
