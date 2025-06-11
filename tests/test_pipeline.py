import json
from pathlib import Path
from pipeline.pipeline import VideoPipeline
from pipeline.config import Config


def test_pipeline_success(monkeypatch, tmp_path):
    cfg = Config()
    cfg.background_styles = {"Rain": str(tmp_path / "rain")}
    rain = tmp_path / "rain"
    rain.mkdir()
    (rain / "vid.mp4").write_text("v")
    cfg.background_videos_path = str(rain)
    cfg.watermark_path = None
    cfg.validate()

    def fake_generate(self, text, out):
        out.write_text("voice")
        return True

    def fake_transcribe(self, path):
        return [{"start": 0.0, "end": 1.0, "text": "hi"}]

    def fake_generate_ass(self, words, path):
        path.write_text("sub")

    def fake_render(self, audio, subs, output, intro=None, outro=None, **kwargs):
        output.write_text("video")

    monkeypatch.setattr("pipeline.voiceover.VoiceOverGenerator.generate", fake_generate)
    monkeypatch.setattr("pipeline.subtitles.SubtitleGenerator.transcribe", fake_transcribe)
    monkeypatch.setattr("pipeline.subtitles.SubtitleGenerator.generate_ass", fake_generate_ass)
    monkeypatch.setattr("pipeline.renderer.VideoRenderer.render", fake_render)

    vp = VideoPipeline(cfg, debug=True)
    ctx = vp.run("hello", "test", background="Rain")
    assert ctx.final_video_path.exists()
    summary = json.loads((ctx.output_dir / "run_summary.json").read_text())
    assert summary["success"] is True


def test_pipeline_whisper_disabled(monkeypatch, tmp_path):
    cfg = Config()
    cfg.background_styles = {"Rain": str(tmp_path / "rain")}
    rain = tmp_path / "rain"
    rain.mkdir()
    (rain / "vid.mp4").write_text("v")
    cfg.background_videos_path = str(rain)
    cfg.watermark_path = None
    cfg.validate()

    def fake_generate(self, text, out):
        out.write_text("voice")
        return True

    def fake_render(self, audio, subs, output, intro=None, outro=None, **kwargs):
        output.write_text("video")

    monkeypatch.setattr("pipeline.voiceover.VoiceOverGenerator.generate", fake_generate)
    monkeypatch.setattr("pipeline.renderer.VideoRenderer.render", fake_render)

    vp = VideoPipeline(cfg, debug=True)
    ctx = vp.run("hello", "test", background="Rain", whisper_disable=True)
    assert ctx.final_video_path.exists()


def test_config_apply_preset():
    cfg = Config()
    cfg.presets = {
        "basic": {"voice": "v1", "background_style": "Rain", "subtitles": False}
    }
    bg, subs = cfg.apply_preset("basic")
    assert bg == "Rain"
    assert subs is False
    assert cfg.default_voice_id == "v1"


def test_pipeline_no_subtitles(monkeypatch, tmp_path):
    cfg = Config()
    cfg.background_styles = {"Rain": str(tmp_path / "rain")}
    rain = tmp_path / "rain"
    rain.mkdir()
    (rain / "vid.mp4").write_text("v")
    cfg.background_videos_path = str(rain)
    cfg.watermark_path = None
    cfg.validate()

    def fake_generate(self, text, out):
        out.write_text("voice")
        return True

    def fake_render(self, audio, subs, output, intro=None, outro=None, **kwargs):
        output.write_text("video")

    monkeypatch.setattr("pipeline.voiceover.VoiceOverGenerator.generate", fake_generate)
    monkeypatch.setattr("pipeline.renderer.VideoRenderer.render", fake_render)

    vp = VideoPipeline(cfg, debug=True)
    ctx = vp.run("hello", "test", background="Rain", no_subtitles=True)
    assert ctx.final_video_path.exists()
    assert ctx.subtitles_path.exists()
