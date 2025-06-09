from pathlib import Path
from pipeline import config_loader
import logging


def test_validate_functions(tmp_path):
    cfg = {"default_voice_id": "id", "whisper_model": "base"}
    logger = logging.getLogger("test")
    assert config_loader.validate_elevenlabs(cfg, logger) in {True, False}
    assert config_loader.validate_whisper(cfg, logger) is True

    cfg2 = {}
    assert not config_loader.validate_whisper(cfg2, logger)
