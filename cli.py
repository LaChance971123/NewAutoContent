from __future__ import annotations

import argparse
from pathlib import Path


class CLI:
    @staticmethod
    def build_parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Video generation pipeline")
        parser.add_argument("--script-file", help="Path to script text file")
        parser.add_argument("--script-text", help="Inline script text")
        parser.add_argument(
            "--style",
            choices=["karaoke", "progressive", "simple"],
            default=None,
            help="Subtitle style",
        )
        parser.add_argument("--resolution", help="Video resolution e.g. 1080x1920")
        parser.add_argument("--background-style", help="Background style to use")
        parser.add_argument("--background", help=argparse.SUPPRESS)
        parser.add_argument("--output", help="Output video path")
        parser.add_argument("--no-watermark", action="store_true", help="Disable watermark")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--debug", action="store_true")
        parser.add_argument("--verbose", action="store_true", help="Verbose logging")
        parser.add_argument("--log-to-file", action="store_true")
        return parser

    @staticmethod
    def parse(args=None) -> argparse.Namespace:
        parser = CLI.build_parser()
        return parser.parse_args(args)


def _load_config() -> "Config":
    from pipeline.config import Config
    cfg_path = Path("config/config.json")
    config = Config.load(cfg_path)
    return config


def _read_script(args: argparse.Namespace) -> tuple[str, str]:
    if args.script_text:
        return args.script_text, "cli"
    if args.script_file:
        path = Path(args.script_file)
        if not path.exists():
            raise FileNotFoundError(f"Script file {path} does not exist")
        return path.read_text(), path.stem
    text = "".join(iter(input, ""))  # stdin
    return text, "stdin"


def main(argv=None) -> None:
    from dotenv import load_dotenv
    from pipeline.pipeline import VideoPipeline
    from pipeline.logger import setup_logger

    print("[INFO] Starting AutoContent CLI pipeline...")
    load_dotenv()
    args = CLI.parse(argv)
    if args.verbose:
        args.debug = True

    try:
        script_text, name = _read_script(args)
    except Exception as e:
        print(f"[ERROR] {e}")
        return

    config = _load_config()
    logger = setup_logger("cli", None, args.debug)
    config.validate(logger)

    if args.style:
        config.subtitle_style = args.style
    if args.resolution:
        config.resolution = args.resolution
    if args.no_watermark:
        config.watermark_enabled = False
    background = args.background_style or args.background
    output_path = Path(args.output) if args.output else None

    log_file = None
    if args.log_to_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "pipeline.log"

    pipeline = VideoPipeline(config, debug=args.debug, log_file=log_file)
    try:
        ctx = pipeline.run(script_text, name, background=background, output=output_path)
    except Exception as exc:
        print(f"[ERROR] Pipeline failed: {exc}")
        return

    print(f"[INFO] Output folder: {ctx.output_dir}")
    print(f"[INFO] Final video: {ctx.final_video_path}")


if __name__ == "__main__":
    main()

