# Android Ebook TTS Reader

A Kivy-based Android-first ebook reader built with **Python 3** on **Ubuntu**, packaged with **Buildozer**.  The application reads ebooks aloud using **Coqui XTTS v2**, with punctuation-aware pauses, buffered synthesis, and resumable playback.

## What works now

| Feature | Status |
|---|---|
| Kivy desktop UI (Ubuntu dev mode) | ✅ working |
| TXT / EPUB book loading | ✅ working |
| Chapter & sentence navigation (numeric input + Jump) | ✅ working |
| Reading position persistence (JSON) | ✅ working |
| Punctuation-aware chunking | ✅ working |
| Background synthesis thread | ✅ working |
| Prefetch (N+1 / N+2 ahead) | ✅ working |
| WAV cache (SHA-based, survives restarts) | ✅ working |
| Audio playback via Kivy SoundLoader | ✅ working (desktop) |
| Lazy XTTS model loading | ✅ working |
| Play / Pause / Resume / Stop controls | ✅ working |
| Native file picker (plyer) | ✅ desktop + Android best-effort |
| Android storage permissions (pyjnius) | ✅ on-device |
| `buildozer.spec` | ✅ included |
| XTTS on-device synthesis (Android) | ⚠️ not feasible yet (see below) |

## Project structure

```text
android_ebook_tts_reader/
├── main.py                  # App entry point
├── buildozer.spec           # Android build configuration
├── requirements.txt
├── .gitignore
├── app/
│   ├── config.py            # Runtime constants
│   ├── models.py            # Domain types (Book, Chapter, PlaybackChunk …)
│   ├── state.py             # In-memory app state
│   ├── book_sources.py      # Folder scan for .epub/.txt
│   ├── parser.py            # TXT/EPUB → Book
│   ├── progress.py          # JSON position persistence
│   ├── text_chunker.py      # Sentence → PlaybackChunk grouping
│   ├── audio_player.py      # Kivy SoundLoader wrapper
│   ├── playback.py          # Buffered controller (synth thread + Clock poll)
│   ├── tts_engine.py        # Coqui XTTS adapter (lazy load + WAV cache)
│   ├── android_utils.py     # Permission requests + plyer file picker
│   └── ui/
│       ├── app_view.py      # ReaderRoot widget logic
│       └── kv.py            # Kivy language layout
└── data/
    └── .gitkeep
```

## Development on Ubuntu

### 1. System dependencies

```bash
sudo apt update
sudo apt install python3-venv python3-dev ffmpeg espeak-ng \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
    zlib1g-dev libgstreamer1.0-dev gstreamer1.0-plugins-base
```

### 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note:** `coqui-tts` pulls in PyTorch (~2 GB) and may take a while.
> For UI-only development you can skip it:
> ```bash
> pip install kivy plyer ebooklib beautifulsoup4 lxml platformdirs
> ```

### 3. Run in desktop dev mode

```bash
python3 main.py
```

What you can do:

* **Scan Books** – scans `~/Books`, `~/Documents`, `~/Downloads` for `.epub` and `.txt` files.
* **Pick File** – opens a native file dialog (requires `zenity` or `kdialog` on Linux).
* Click a book button to load it.
* Set **Chapter** and **Sentence** numbers, then press **Jump** to seek.
* Press **▶ Play** to start synthesis and sequential audio playback.
* Press **⏸ Pause** / **▶ Resume** / **Stop** to control playback.

### 4. Playback pipeline

1. Book is parsed into chapters and sentences.
2. Sentences are grouped into `PlaybackChunk`s (~4 sentences each).
3. A background synthesis thread calls XTTS for each chunk; results are cached by SHA-256 hash of the text.
4. A Kivy Clock poll (every 300 ms) checks whether the current sound has finished and the next synthesised WAV is ready.
5. When both conditions are met, playback advances automatically.
6. Reading position is persisted after each chunk so the app can resume where it left off.

## Android build

### Build APK

```bash
source .venv/bin/activate
buildozer android debug
```

First build takes ~20 minutes (downloads Android SDK/NDK, builds python-for-android recipes).

The resulting APK is in `bin/`.

### Android permissions

The app requests:

* `READ_EXTERNAL_STORAGE` / `WRITE_EXTERNAL_STORAGE` – book files and WAV cache
* `MANAGE_EXTERNAL_STORAGE` – needed on API 30+ for broad storage access
* `INTERNET` – model download (if run on-device in a future iteration)

### File picker on Android

`plyer.filechooser` opens an `Intent.ACTION_GET_CONTENT` dialog.  On Android 10+, the returned path may be a `content://` URI; the app attempts to resolve it to a real filesystem path via `ContentResolver`.  If resolution fails, the raw URI is passed through (loading will likely fail with a clear error message).

## XTTS / synthesis notes

### Desktop (Ubuntu)

XTTS v2 works well on desktop with a CUDA GPU or a fast CPU.  The first run downloads the model weights (~1.8 GB).  Subsequent runs load from cache instantly.

### Android (current limitation)

Running full Coqui XTTS on-device on Android is **not currently feasible** because:

1. PyTorch for Android is not packaged as a python-for-android recipe.
2. The model requires ~2 GB RAM.

**Workarounds / roadmap:**

* **Pre-synthesise** all chunks on desktop and copy the WAV cache to the device.
* **Off-device server** – run `main.py` on a desktop/server and stream WAV files over HTTP.
* **Lighter model** – evaluate `piper-tts` or `edge-tts` (both have smaller footprints).

## Persistence

Reading progress is saved in a JSON file:

| Platform | Location |
|---|---|
| Linux | `~/.local/share/android_ebook_tts_reader/AlfaGongGong/state.json` |
| Android | `/data/data/org.alfagonggong.ebookttsreader/files/` |

Schema: `book_path`, `chapter_index`, `sentence_index`, `chunk_index`, `char_offset`.

## Supported book formats

| Format | Status |
|---|---|
| `.txt` | ✅ chapter split on "Chapter"/"Poglavlje" headings |
| `.epub` | ✅ one `Chapter` per EPUB document item |
| `.pdf` | ❌ not implemented |

## Known limitations

* Android file picker returns `content://` URIs that need OS-level resolution.
* XTTS synthesis is skipped gracefully if the library is not installed – WAV cache still plays.
* Chapter detection accuracy depends on how consistently the source book uses heading text.
* The Kivy `SoundLoader` audio backend on some Linux setups requires GStreamer plugins; install `gstreamer1.0-plugins-good` if audio is silent.

## License

No license has been added yet.  Add one before distribution.

