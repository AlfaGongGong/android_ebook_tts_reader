"""Runtime configuration values for the ebook TTS reader."""

from pathlib import Path
from platformdirs import user_data_dir

APP_NAME = "android_ebook_tts_reader"
APP_AUTHOR = "AlfaGongGong"
DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
CACHE_DIR = DATA_DIR / "cache"
PIPER_VOICE_DIR = DATA_DIR / "voices"
STATE_FILE = DATA_DIR / "state.json"
SUPPORTED_EXTENSIONS = {".txt", ".epub"}
DEFAULT_LANGUAGE = "hr"
PIPER_VOICE_NAME = "hr_HR-filip-medium"
DEFAULT_SENTENCES_PER_CHUNK = 4
PREFETCH_BLOCKS = 2
TARGET_CHUNK_SECONDS = (15, 30)

DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
PIPER_VOICE_DIR.mkdir(parents=True, exist_ok=True)
