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
        parser.add_argument("--background", help="Background style to use")
        parser.add_argument("--output", help="Output video path")
        parser.add_argument("--no-watermark", action="store_true", help="Disable watermark")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--debug", action="store_true")
        parser.add_argument("--log-to-file", action="store_true")
        return parser

    @staticmethod
    def parse(args=None) -> argparse.Namespace:
        parser = CLI.build_parser()
        return parser.parse_args(args)

