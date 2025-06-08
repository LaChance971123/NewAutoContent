import logging
from pathlib import Path
from pipeline.renderer import VideoRenderer


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
