"""Coqui XTTS integration with lazy loading and synthesis cache.

Mobile optimisation notes
-------------------------
* **Lazy loading**: The heavy ``TTS`` import and model-weight download/load
  happen only on the first synthesis call, not at app startup.
* **WAV cache**: Every synthesised chunk is stored under a SHA-256 key derived
  from the language + text.  Repeated playback of the same content (e.g.
  after a resume) costs zero synthesis time.
* **Prefetch cap**: ``PREFETCH_BLOCKS`` is kept low (default 2) so the
  background thread does not exhaust RAM on low-memory Android devices.
* **Model swap**: For devices where the full XTTS v2 model (~1.8 GB) is too
  large, replace ``_DEFAULT_MODEL`` with a lighter alternative or route
  synthesis to an off-device HTTP TTS server and save the response as a WAV.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

from .config import CACHE_DIR, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"


class XTTSEngine:
    """Coqui XTTS wrapper with lazy loading and per-text WAV caching."""

    def __init__(
        self,
        language: str = DEFAULT_LANGUAGE,
        model_name: str = _DEFAULT_MODEL,
        speaker_wav: Optional[str] = None,
    ) -> None:
        self.language = language
        self.model_name = model_name
        self.speaker_wav = speaker_wav
        self._tts = None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def is_loaded(self) -> bool:
        """Return ``True`` if the model is already in memory."""
        return self._tts is not None

    def ensure_loaded(self) -> None:
        """Lazily load the TTS model.

        This is a heavy operation (network download on first run, several
        seconds of CPU/GPU loading time).  Always call from a worker thread,
        never from the Kivy main thread.
        """
        if self._tts is not None:
            return
        try:
            from TTS.api import TTS  # type: ignore
            logger.info("Loading XTTS model: %s …", self.model_name)
            self._tts = TTS(self.model_name)
            logger.info("XTTS model ready.")
        except ImportError as exc:
            raise RuntimeError(
                "Coqui TTS library not found. "
                "Install it with:  pip install coqui-tts>=0.25.0"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"XTTS model failed to load: {exc}\n"
                "Ensure model assets are downloaded and all dependencies are met."
            ) from exc

    def synthesize_to_file(
        self,
        text: str,
        chunk_id: str,
        speaker_wav: Optional[str] = None,
    ) -> Path:
        """Return path to a WAV for *text*, synthesising only if not cached.

        The output filename is derived from a hash of the language and text so
        the same text is never re-synthesised even across app restarts.
        """
        output_path = self._cache_path(text)
        if output_path.exists():
            logger.debug("Cache hit for chunk %s", chunk_id)
            return output_path

        self.ensure_loaded()
        effective_speaker = speaker_wav or self.speaker_wav
        kwargs: dict = dict(
            text=text,
            file_path=str(output_path),
            language=self.language,
        )
        if effective_speaker:
            kwargs["speaker_wav"] = effective_speaker

        logger.info("Synthesising chunk %s …", chunk_id)
        self._tts.tts_to_file(**kwargs)  # type: ignore[union-attr]
        return output_path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cache_path(self, text: str) -> Path:
        key = hashlib.sha256(f"{self.language}:{text}".encode()).hexdigest()[:24]
        return CACHE_DIR / f"tts_{key}.wav"

