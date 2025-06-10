from cli import CLI

def test_cli_flags_parsing():
    args = CLI.parse(["--script-text", "hello", "--background-style", "Minecraft", "--output", "out.mp4"])
    assert args.background_style == "Minecraft"
    assert args.output == "out.mp4"

def test_cli_new_flags():
    args = CLI.parse(["--script-text", "hi", "--force-coqui", "--whisper-disable"])
    assert args.force_coqui is True
    assert args.whisper_disable is True

def test_cli_preset_flags():
    args = CLI.parse(["--script-text", "hi", "--preset", "default", "--preview-voice", "v"])
    assert args.preset == "default"
    assert args.preview_voice == "v"
    args = CLI.parse(["--batch", "folder", "--randomize"])
    assert args.batch == "folder"
    assert args.randomize is True
