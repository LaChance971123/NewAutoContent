from cli import CLI

def test_cli_flags_parsing():
    args = CLI.parse(["--script-text", "hello", "--background-style", "Minecraft", "--output", "out.mp4"])
    assert args.background_style == "Minecraft"
    assert args.output == "out.mp4"

def test_cli_new_flags():
    args = CLI.parse(["--script-text", "hi", "--force-coqui", "--whisper-disable"])
    assert args.force_coqui is True
    assert args.whisper_disable is True
