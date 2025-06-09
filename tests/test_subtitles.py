from pathlib import Path
from pipeline.subtitles import SubtitleGenerator


def test_style_tags():
    sg = SubtitleGenerator("karaoke")
    assert sg._style_tag("hi") == "{\\k20}hi"
    sg = SubtitleGenerator("progressive")
    assert sg._style_tag("hi") == "{\\alpha&HFF&\\t(0,300,\\alpha&H00&)}hi"
    sg = SubtitleGenerator("simple")
    assert sg._style_tag("hi") == "hi"


def test_generate_ass(tmp_path):
    words = [{"start": 0.0, "end": 1.0, "text": "Hello"}]
    sg = SubtitleGenerator("simple")
    out = tmp_path / "sub.ass"
    sg.generate_ass(words, out)
    content = out.read_text()
    assert "Dialogue: 0,0:00:00.00,0:00:01.00,Default,Hello" in content

