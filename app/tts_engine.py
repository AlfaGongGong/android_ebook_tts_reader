"""Piper integration with lazy loading, voice download, and synthesis cache.

Mobile optimisation notes
-------------------------
* **Lazy loading**: Piper is imported and the voice model is loaded only on the
  first synthesis call, not at app startup.
* **WAV cache**: Every synthesised chunk is stored under a SHA-256 key derived
  from the selected voice + text. Repeated playback of the same content (e.g.
  after a resume) costs zero synthesis time.
* **Prefetch cap**: ``PREFETCH_BLOCKS`` is kept low (default 2) so the
  background thread does not exhaust RAM on low-memory Android devices.
* **Voice bootstrap**: The default Piper voice is downloaded automatically on
  first use if the ONNX model/config are not already present in the app data
  directory.
"""

from __future__ import annotations

import hashlib
import logging
import re
import shutil
import wave
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

from .config import CACHE_DIR, DEFAULT_LANGUAGE, PIPER_VOICE_DIR, PIPER_VOICE_NAME

logger = logging.getLogger(__name__)

_VOICE_PATTERN = re.compile(
    r"^(?P<lang_family>[^_]+)_(?P<lang_region>[^-]+)-(?P<voice_name>[^-]+)-(?P<voice_quality>.+)$"
)
_VOICE_URL_FORMAT = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
    "{lang_family}/{lang_code}/{voice_name}/{voice_quality}/"
    "{voice_code}{extension}?download=true"
)


class PiperEngine:
    """Piper wrapper with lazy loading, voice bootstrap, and per-text WAV caching."""

    def __init__(
        self,
        language: str = DEFAULT_LANGUAGE,
        voice_name: str = PIPER_VOICE_NAME,
        voice_dir: Path = PIPER_VOICE_DIR,
    ) -> None:
        self.language = language
        self.voice_name = voice_name
        self.voice_dir = Path(voice_dir)
        self._voice = None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def is_loaded(self) -> bool:
        """Return ``True`` if the Piper voice is already in memory."""
        return self._voice is not None

    def ensure_loaded(self) -> None:
        """Lazily load the Piper voice.

        This may download the voice assets on the first run and should always be
        called from a worker thread, never from the Kivy main thread.
        """
        if self._voice is not None:
            return
        model_path = self._ensure_voice_files()
        try:
            from piper import PiperVoice  # type: ignore

            logger.info("Loading Piper voice: %s …", model_path.name)
            self._voice = PiperVoice.load(model_path)
            logger.info("Piper voice ready.")
        except ImportError as exc:
            raise RuntimeError(
                "Piper TTS library not found. "
                "Install it with: pip install piper-tts>=1.4.2"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Piper voice failed to load: {exc}\n"
                "Ensure model assets are downloaded and all dependencies are met."
            ) from exc

    def synthesize_to_file(
        self,
        text: str,
        chunk_id: str,
    ) -> Path:
        """Return path to a WAV for *text*, synthesising only if not cached.

        The output filename is derived from a hash of the selected voice and
        text so the same text is never re-synthesised even across app restarts.
        """
        output_path = self._cache_path(text)
        if output_path.exists():
            logger.debug("Cache hit for chunk %s", chunk_id)
            return output_path

        self.ensure_loaded()
        logger.info("Synthesising chunk %s …", chunk_id)
        with wave.open(str(output_path), "wb") as wav_file:
            self._voice.synthesize_wav(text, wav_file)  # type: ignore[union-attr]
        return output_path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cache_path(self, text: str) -> Path:
        key = hashlib.sha256(f"{self.voice_name}:{self.language}:{text}".encode()).hexdigest()[:24]
        return CACHE_DIR / f"tts_{key}.wav"

    def _ensure_voice_files(self) -> Path:
        model_path = self.voice_dir / f"{self.voice_name}.onnx"
        config_path = self.voice_dir / f"{self.voice_name}.onnx.json"
        voice_parts = self._voice_parts()

        for path, extension in ((model_path, ".onnx"), (config_path, ".onnx.json")):
            if path.exists() and path.stat().st_size > 0:
                continue
            url = _VOICE_URL_FORMAT.format(
                voice_code=self.voice_name,
                extension=extension,
                **voice_parts,
            )
            logger.info("Downloading Piper voice asset: %s", path.name)
            try:
                with urlopen(url) as response, open(path, "wb") as output_file:
                    shutil.copyfileobj(response, output_file)
            except Exception as exc:
                if path.exists():
                    path.unlink()
                raise RuntimeError(
                    f"Failed to download Piper voice asset '{path.name}': {exc}"
                ) from exc

        return model_path

    def _voice_parts(self) -> dict:
        match = _VOICE_PATTERN.match(self.voice_name)
        if match is None:
            raise RuntimeError(
                "Unsupported Piper voice name format. "
                "Expected <lang>_<REGION>-<name>-<quality>."
            )

        lang_family = match.group("lang_family")
        lang_region = match.group("lang_region")
        return {
            "lang_family": lang_family,
            "lang_code": f"{lang_family}_{lang_region}",
            "voice_name": match.group("voice_name"),
            "voice_quality": match.group("voice_quality"),
        }
