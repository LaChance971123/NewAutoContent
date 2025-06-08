import os
import sys
from pathlib import Path
from pipeline.voiceover import VoiceOverGenerator


def test_elevenlabs_generation(monkeypatch, tmp_path):
    called = {"eleven": False, "coqui": False}

    def fake_eleven(text, path):
        called["eleven"] = True
        path.write_text("data")
        return True

    def fake_coqui(text, path):
        called["coqui"] = True
        return True

    monkeypatch.setenv("ELEVENLABS_API_KEY", "key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "voice")
    gen = VoiceOverGenerator("elevenlabs", coqui_model_name="model")
    monkeypatch.setattr(gen, "_generate_elevenlabs", fake_eleven)
    monkeypatch.setattr(gen, "_generate_coqui", fake_coqui)
    out = tmp_path / "out.wav"
    result = gen.generate("hi", out)
    assert result is True
    assert called["eleven"] is True
    assert called["coqui"] is False
    assert out.exists()


def test_coqui_fallback(monkeypatch, tmp_path):
    called = {"eleven": False, "coqui": False}

    def fake_eleven(text, path):
        called["eleven"] = True
        return False

    def fake_coqui(text, path):
        called["coqui"] = True
        path.write_text("data")
        return True

    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_VOICE_ID", raising=False)
    gen = VoiceOverGenerator("elevenlabs", coqui_model_name="model")
    monkeypatch.setattr(gen, "_generate_elevenlabs", fake_eleven)
    monkeypatch.setattr(gen, "_generate_coqui", fake_coqui)
    out = tmp_path / "out.wav"
    result = gen.generate("hi", out)
    assert result is True
    assert called["eleven"] is False
    assert called["coqui"] is True
    assert out.exists()


def test_invalid_voice_id_fallback(monkeypatch, tmp_path):
    called = {"eleven": False, "coqui": False}

    def fake_eleven(text, path):
        called["eleven"] = True
        return False

    def fake_coqui(text, path):
        called["coqui"] = True
        path.write_text("data")
        return True

    monkeypatch.setenv("ELEVENLABS_API_KEY", "key")
    monkeypatch.setenv("ELEVENLABS_VOICE_ID", "bad")
    gen = VoiceOverGenerator("elevenlabs", coqui_model_name="model")
    monkeypatch.setattr(gen, "_generate_elevenlabs", fake_eleven)
    monkeypatch.setattr(gen, "_generate_coqui", fake_coqui)
    out = tmp_path / "out.wav"
    result = gen.generate("hi", out)
    assert result is True
    assert called["eleven"] is True
    assert called["coqui"] is True
    assert out.exists()


def test_coqui_download(monkeypatch, tmp_path):
    events = {"download": False}

    class FakeTTS:
        def __init__(self, *args, **kwargs):
            if not events.get("tried"):
                events["tried"] = True
                raise RuntimeError("model missing")

        def tts_to_file(self, text: str, file_path: str):
            Path(file_path).write_text("ok")

    class FakeManager:
        def download_model(self, name):
            events["download"] = True

    import types

    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_VOICE_ID", raising=False)
    api_mod = types.ModuleType("TTS.api")
    api_mod.TTS = FakeTTS
    manage_mod = types.ModuleType("TTS.utils.manage")
    manage_mod.ModelManager = lambda: FakeManager()
    utils_mod = types.ModuleType("TTS.utils")
    utils_mod.manage = manage_mod
    monkeypatch.setitem(sys.modules, "TTS", types.ModuleType("TTS"))
    monkeypatch.setitem(sys.modules, "TTS.api", api_mod)
    monkeypatch.setitem(sys.modules, "TTS.utils", utils_mod)
    monkeypatch.setitem(sys.modules, "TTS.utils.manage", manage_mod)

    gen = VoiceOverGenerator(
        "elevenlabs",
        coqui_model_name="model",
    )

    out = tmp_path / "out.wav"
    result = gen.generate("hi", out)

    assert result is True
    assert events["download"] is True
    assert out.exists()

