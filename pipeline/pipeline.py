from __future__ import annotations

from pathlib import Path
import time
import json
from .helpers import (
    PipelineContext,
    sanitize_name,
    now_ts_folder,
    run_with_timeout,
    create_silence,
    create_dummy_subtitles,
)
from .voiceover import VoiceOverGenerator
from .subtitles import SubtitleGenerator
from .renderer import VideoRenderer
from .logger import setup_logger
from .config import Config


class VideoPipeline:
    def __init__(self, config: Config, debug: bool = False, log_file: Path | None = None):
        self.config = config
        self.logger = setup_logger("pipeline", log_file, debug)
        self.debug = debug
        self.log_file = log_file
        self.timeout = config.step_timeout

    def run(
        self,
        script_text: str,
        script_name: str,
        background: str | None = None,
        output: Path | None = None,
    ) -> PipelineContext:
        style = self.config.subtitle_style
        engine = self.config.voice_engine
        voice_id = self.config.default_voice_id

        # resolve background folder
        bg_styles = self.config.background_styles or {}
        bg_folder = Path(self.config.background_videos_path)
        if background:
            for key, val in bg_styles.items():
                if key.lower() == background.lower():
                    bg_folder = Path(val)
                    break

        title = sanitize_name(script_name if script_name not in {"cli", "stdin"} else "session")
        if output:
            final_output = Path(output)
            out_dir = final_output.parent
        else:
            out_dir = Path("output") / f"{title}_{now_ts_folder()}"
            final_output = out_dir / "final_video.mp4"
        session_log = out_dir / "pipeline.log"

        ctx = PipelineContext(
            script_text=script_text,
            script_name=title,
            output_dir=out_dir,
            subtitle_style=style,
            voice_engine=engine,
            voice_id=voice_id,
            log_file=session_log,
            debug=self.debug,
        )
        ctx.final_video_path = final_output

        # Reconfigure logger to use session log as well
        setup_logger("pipeline", session_log, self.debug)
        self.logger.info("Starting pipeline")
        status = "success"
        start = time.time()
        try:
            # Voiceover
            voice = VoiceOverGenerator(
                engine,
                voice_id,
                self.config.coqui_model_name,
                debug=self.debug,
                log_file=session_log,
            )
            try:
                run_with_timeout(
                    lambda: voice.generate(ctx.script_text, ctx.voiceover_path),
                    self.timeout,
                )
                if not ctx.voiceover_path.exists() or ctx.voiceover_path.stat().st_size == 0:
                    raise RuntimeError("voiceover file invalid")
            except Exception as e:
                self.logger.error(f"Voiceover step failed: {e}")
                if self.config.developer_mode:
                    create_silence(ctx.voiceover_path)
                    self.logger.warning("Developer mode: using silent audio")
                else:
                    raise

            # Subtitles
            subs = SubtitleGenerator(style, log_file=session_log, debug=self.debug)
            try:
                words = run_with_timeout(subs.transcribe, self.timeout, ctx.voiceover_path)
                run_with_timeout(subs.generate_ass, self.timeout, words, ctx.subtitles_path)
            except Exception as e:
                self.logger.error(f"Subtitle step failed: {e}")
                if self.config.developer_mode:
                    create_dummy_subtitles(ctx.subtitles_path)
                    self.logger.warning("Developer mode: using dummy subtitles")
                else:
                    raise

            # Render
            watermark_path = (
                Path(self.config.watermark_path)
                if self.config.watermark_enabled and self.config.watermark_path
                else None
            )
            renderer = VideoRenderer(
                bg_folder,
                watermark_path,
                self.config.watermark_opacity,
                resolution=self.config.resolution,
                ffmpeg_path=self.config.ffmpeg_path,
                log_file=session_log,
                debug=self.debug,
            )
            run_with_timeout(
                renderer.render,
                self.timeout,
                ctx.voiceover_path,
                ctx.subtitles_path,
                ctx.final_video_path,
            )
        except Exception as e:
            status = "failed"
            self.logger.error(f"Pipeline failed: {e}")
            ctx.write_error_trace(e)
            ctx.save_metadata(status=status)
            ctx.save_config_snapshot(self.config.__dict__)
            ctx.write_summary()
            ctx.archive()
            raise

        duration = f"{int(time.time() - start)}s"
        ctx.save_metadata(status=status)
        run_summary = {
            "script": ctx.script_path.name,
            "voice": ctx.voice_engine.capitalize() if ctx.voice_engine else "",
            "style": ctx.subtitle_style,
            "duration": duration,
            "success": status == "success",
        }
        with open(ctx.output_dir / "run_summary.json", "w") as f:
            json.dump(run_summary, f, indent=2)
        ctx.save_config_snapshot(self.config.__dict__)
        ctx.write_summary()
        ctx.archive()
        self.logger.info("Pipeline completed")
        return ctx
