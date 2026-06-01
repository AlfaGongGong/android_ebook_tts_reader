# Android Ebook TTS Reader

A Kivy-based Android-first ebook reader scaffold built with **Python 3** on **Ubuntu**, designed for future packaging with **Buildozer**. The application is intended to read ebooks aloud using **Coqui XTTS v2**, with punctuation-aware pauses, resumable playback, and buffered text-to-speech generation.

## Goals

- Browse books from phone storage / SD card folders
- Choose where reading starts:
  - from the beginning
  - from a chapter
  - from a specific sentence
- Remember where playback stopped
- Use natural Croatian (`hr`) reading
- Respect punctuation with natural pauses at commas, full stops, question marks, etc.
- Buffer upcoming TTS blocks while the current block is playing

## Current status

This repository currently contains an **initial scaffold**:

- Kivy application entry point
- basic UI layout for selecting and controlling a book session
- storage discovery stubs for Android and desktop development
- EPUB/text parsing helpers
- sentence and chapter navigation model
- playback progress persistence
- XTTS engine adapter placeholder
- punctuation-aware chunking logic
- buffered synthesis/playback queue skeleton

It is **not yet a finished production app**. Android permissions, storage APIs, real audio playback integration, and XTTS performance tuning still need implementation work.

## Project structure

```text
android_ebook_tts_reader/
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── state.py
│   ├── book_sources.py
│   ├── parser.py
│   ├── progress.py
│   ├── text_chunker.py
│   ├── playback.py
│   ├── tts_engine.py
│   ├── android_utils.py
│   └── ui/
│       ├── __init__.py
│       ├── app_view.py
│       └── kv.py
└── data/
    └── .gitkeep
```

## Development on Ubuntu

### 1. Install system dependencies

Typical packages you may need on Ubuntu:

- Python 3.10+
- `python3-venv`
- `ffmpeg`
- `espeak-ng` (optional for fallback experiments)
- build tools required by Kivy / Buildozer

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run the scaffold locally

```bash
python3 main.py
```

This currently launches a desktop Kivy development view that lets you:

- inspect discovered books from a folder
- simulate selecting a book
- view chapter/sentence metadata
- test progress persistence and chunking flow

## Android direction

This scaffold is designed to be extended into an Android app using Kivy + Buildozer.

Planned Android-specific work includes:

- runtime permission handling for media/storage access
- SAF or Android-compatible storage browsing
- optimized local cache directory handling
- packaged/native audio playback path
- integration with a suitable XTTS inference strategy

> Note: Running XTTS fully on-device on Android may be resource-intensive depending on the target hardware. A later iteration may need quantization, smaller models, caching, or hybrid/off-device inference options.

## XTTS v2 integration notes

The project includes an XTTS engine adapter scaffold in `app/tts_engine.py`.

Design expectations:

- use multilingual XTTS v2
- set the language to Croatian (`hr`)
- synthesize in buffered blocks of approximately 15–30 seconds
- preserve punctuation-driven pause behavior
- generate block N+1 and N+2 while block N is playing

## Buffering strategy

The intended pipeline is:

1. Parse the book into chapters and sentences
2. Build text chunks that correspond to natural speech windows
3. Queue the first chunk for synthesis
4. Start playback as soon as chunk 1 is ready
5. Continue synthesizing the next chunks in the background
6. Persist the current chapter/sentence/block position continuously

This should allow smoother reading with less waiting between chunks.

## Persistence

Reading progress is stored in a local JSON state file for now. The schema supports:

- selected book path
- chapter index
- sentence index
- chunk index
- last known character offset

## Supported book formats in this scaffold

- `.txt`
- `.epub`

Additional formats like PDF would require separate extraction and cleanup logic.

## Important limitations

- Android file picking is currently a stub/fallback design
- XTTS synthesis adapter is scaffolded but not production-ready
- Audio playback queue is a simulation-friendly implementation for local development
- No final packaging config (`buildozer.spec`) is included yet
- Real sentence seeking accuracy depends on the source ebook formatting

## Next recommended steps

1. Add a real Android file picker/storage integration
2. Connect `tts_engine.py` to a tested XTTS runtime path
3. Add actual streamed or cached WAV playback
4. Create a `buildozer.spec`
5. Add resume/start-point UI dialogs for chapter and sentence selection
6. Improve chapter detection for messy EPUB/TXT sources

## License

No license has been added yet. Add one before distribution.
