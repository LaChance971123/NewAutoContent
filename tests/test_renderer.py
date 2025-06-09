import logging
import subprocess
from pathlib import Path
import pytest

from pipeline.renderer import VideoRenderer
from pipeline.helpers import create_silence


def test_case_insensitive_folder(tmp_path):
    root = tmp_path / "assets" / "backgrounds"
    folder = root / "minecraft"
    folder.mkdir(parents=True)
    vid = folder / "clip.mp4"
    vid.write_text("data")

    renderer = VideoRenderer(root / "Minecraft", log_file=None, debug=True)
    assert renderer.pick_background() == vid


def test_fallback_folder(tmp_path, caplog):
    root = tmp_path / "assets" / "backgrounds"
    root.mkdir(parents=True)
    rain = root / "rain"
    rain.mkdir()
    vid = rain / "rain.mp4"
    vid.write_text("data")
    missing = root / "minecraft"

    caplog.set_level(logging.WARNING)
    renderer = VideoRenderer(missing, log_file=None, debug=True)
    choice = renderer.pick_background()
    assert choice == vid
    assert any("Falling back" in r.message for r in caplog.records)


def test_empty_background_folder(tmp_path):
    root = tmp_path / "assets" / "backgrounds"
    empty = root / "minecraft"
    empty.mkdir(parents=True)
    rain = root / "rain"
    rain.mkdir()
    vid = rain / "rain.mp4"
    vid.write_text("data")

    renderer = VideoRenderer(empty, log_file=None, debug=True)
    assert renderer.pick_background() == vid


def test_output_extension_validation(tmp_path):
    bg = tmp_path / "bg"
    bg.mkdir(parents=True)
    (bg / "vid.mp4").write_text("v")
    renderer = VideoRenderer(bg)

    audio = tmp_path / "voice.wav"
    create_silence(audio)
    subs = tmp_path / "sub.ass"
    subs.write_text("sub")

    with pytest.raises(ValueError):
        renderer.render(audio, subs, tmp_path / "out")


def test_filter_complex_switch(tmp_path, monkeypatch):
    bg = tmp_path / "bg"
    bg.mkdir(parents=True)
    (bg / "vid.mp4").write_text("v")
    wm = tmp_path / "wm.png"
    wm.write_text("img")

    renderer = VideoRenderer(bg, watermark=wm, debug=True)

    audio = tmp_path / "voice.wav"
    create_silence(audio)
    subs = tmp_path / "sub.ass"
    subs.write_text("sub")

    captured = {}

    def fake_run(cmd, check, capture_output, text):
        captured["cmd"] = cmd
        (tmp_path / "out.mp4").write_text("video")
        class R:
            stdout = ""
            stderr = ""
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)

    renderer.render(audio, subs, tmp_path / "out.mp4")
    assert "-filter_complex" in captured["cmd"]
    assert all("\\" not in part for part in captured["cmd"])
