from cli import CLI

def test_cli_flags_parsing():
    args = CLI.parse(["--script-text", "hello", "--background-style", "Minecraft", "--output", "out.mp4"])
    assert args.background_style == "Minecraft"
    assert args.output == "out.mp4"
