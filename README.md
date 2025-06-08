# NewAutoContent Pipeline

This project provides a modular pipeline for generating short-form storytelling videos. The output videos are sized for TikTok, Instagram Reels, and YouTube Shorts (1080x1920).

## Features
- Voiceover generation with ElevenLabs TTS and automatic fallback to Coqui TTS. If the configured voice ID is missing or invalid, a warning is logged and Coqui is used instead.
- Subtitle generation via Whisper with support for karaoke, progressive, and simple styles.
- Final rendering using FFmpeg with random background videos and optional watermark overlay.
- Background styles are loaded from folders under `assets/backgrounds` and must contain at least one `.mp4` or `.webm` video. Folder names are resolved case-insensitively and the renderer falls back to the first style containing videos if needed.
- Command line interface with flags for subtitle style, resolution, watermark toggle, dry runs, debug mode, and optional log file output.
- Configuration through `config/config.json` and environment variables in `.env`.
- The config file also defines `coqui_model_name` for automatic download of the
  Coqui model when needed.
- The PyQt5 GUI provides a multi-page interface styled with the PyDracula theme. It offers live logging, a fixed preview pane and export features.

## Usage
```
python main.py --script-file scripts/sample.txt
```
Use `--script-text` to pass a script inline or provide input via `stdin`.
Other useful flags:
```
--style karaoke|progressive|simple
--background-style <style>
--output <path/to/output.mp4>
--resolution 1080x1920
--no-watermark
--dry-run
--debug
--log-to-file
```

Each run creates a timestamped folder inside `output/` such as
`output/my_script_20250608_153000/`.  All generated assets, `metadata.json`, `summary.txt`, and `pipeline.log`
are stored there.  The folder is zipped automatically for easy sharing.

You can also launch a PyQt GUI with:
```
python gui.py
```
The GUI offers pages for creation, batch mode, planning, settings and more. Paste or load a script, choose voices, subtitle style and other options. Logs appear live while the pipeline runs and a phone-style preview pane shows the latest render. You can export the result as a zip when finished.

### Troubleshooting
- If no voiceover is produced, check that your ElevenLabs API key and voice ID are valid. The app will fall back to Coqui if they are missing or incorrect.
- Ensure background videos exist under `assets/backgrounds/<style>` in `.mp4` or `.webm` format. If none are found, another style will be used.
