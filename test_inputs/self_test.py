"""Self test for the AutoContent pipeline."""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from pipeline.pipeline import VideoPipeline
from pipeline.config import Config
from pipeline.voiceover import VoiceOverGenerator
from pipeline.subtitles import SubtitleGenerator
from pipeline.renderer import VideoRenderer


def run_self_test():
    script = "This is a test script for the pipeline."
    cfg = Config.load(Path("config/config.json"))
    cfg.developer_mode = True
    cfg.validate()

    tmp = Path("self_test_temp")
    bg = tmp / "bg"
    bg.mkdir(parents=True, exist_ok=True)
    (bg / "clip.mp4").write_text("video")
    cfg.background_styles = {"Test": str(bg)}
    cfg.background_videos_path = str(tmp)

    def fake_generate(self, text, out):
        out.write_text("voice")
        return True

    def fake_transcribe(self, path):
        return [{"start": 0.0, "end": 1.0, "text": "hi"}]

    def fake_generate_ass(self, words, path):
        path.write_text("sub")

    def fake_render(self, audio, subs, output):
        output.write_text("video")

    VoiceOverGenerator.generate = fake_generate
    SubtitleGenerator.transcribe = fake_transcribe
    SubtitleGenerator.generate_ass = fake_generate_ass
    VideoRenderer.render = fake_render

    vp = VideoPipeline(cfg, debug=True)
    ctx = vp.run(script, "self_test", background="Test")
    assert ctx.final_video_path.exists(), "final video missing"
    assert (ctx.output_dir / "metadata.json").exists(), "metadata missing"
    print(f"Self test succeeded. Output folder: {ctx.output_dir}")


if __name__ == "__main__":
    run_self_test()
