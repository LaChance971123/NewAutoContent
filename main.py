from __future__ import annotations

import sys
from pathlib import Path
from dotenv import load_dotenv

from pipeline.pipeline import VideoPipeline
from pipeline.logger import setup_logger
from pipeline.config import Config
from cli import CLI


def load_config() -> Config:
    cfg_path = Path("config/config.json")
    return Config.load(cfg_path)


def read_script(args) -> tuple[str, str]:
    if args.script_text:
        return args.script_text, "cli"
    if args.script_file:
        text = Path(args.script_file).read_text()
        name = Path(args.script_file).stem
        return text, name
    text = sys.stdin.read()
    return text, "stdin"


def main():
    load_dotenv()
    args = CLI.parse()

    script_text, name = read_script(args)
    config = load_config()

    log_file = None
    if args.log_to_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"{name}.log"

    logger = setup_logger("cli", log_file, args.debug)

    if args.dry_run:
        logger.info("Dry run enabled. Exiting without execution.")
        return

    if args.style:
        config.subtitle_style = args.style
    if args.resolution:
        config.resolution = args.resolution
    if args.no_watermark:
        config.watermark_enabled = False

    pipeline = VideoPipeline(config, debug=args.debug, log_file=log_file)
    try:
        ctx = pipeline.run(script_text, name)
        logger.info(f"Video created at {ctx.final_video_path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")


if __name__ == "__main__":
    main()
