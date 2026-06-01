"""Edge TTS integration with lazy import and synthesis cache."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from pathlib import Path

from .config import CACHE_DIR, DEFAULT_LANGUAGE, DEFAULT_VOICE

logger = logging.getLogger(__name__)

_DEFAULT_RATE = "+0%"
_DEFAULT_VOLUME = "+0%"
_DEFAULT_PITCH = "+0Hz"


class EdgeTTSEngine:
    """Edge TTS wrapper with lazy import and per-text audio caching."""

    def __init__(
        self,
        language: str = DEFAULT_LANGUAGE,
        voice: str = DEFAULT_VOICE,
        rate: str = _DEFAULT_RATE,
        volume: str = _DEFAULT_VOLUME,
        pitch: str = _DEFAULT_PITCH,
    ) -> None:
        self.language = language
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self._communicate_cls = None

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def is_loaded(self) -> bool:
        """Return ``True`` if the Edge TTS client has been imported."""
        return self._communicate_cls is not None

    def ensure_loaded(self) -> None:
        """Lazily import the Edge TTS client."""
        if self._communicate_cls is not None:
            return
        try:
            from edge_tts import Communicate  # type: ignore

            self._communicate_cls = Communicate
            logger.info("Edge TTS client ready for voice %s.", self.voice)
        except ImportError as exc:
            raise RuntimeError(
                "edge-tts library not found. "
                "Install it with: pip install edge-tts>=6.1.12"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Edge TTS failed to initialize: {exc}\n"
                "Ensure internet access is available and dependencies are installed."
            ) from exc

    def synthesize_to_file(
        self,
        text: str,
        chunk_id: str,
    ) -> Path:
        """Return path to an MP3 for *text*, synthesising only if not cached.

        The output filename is derived from a hash of the voice and text so
        the same text is never re-synthesised even across app restarts.
        """
        output_path = self._cache_path(text)
        if output_path.exists():
            logger.debug("Cache hit for chunk %s", chunk_id)
            return output_path

        self.ensure_loaded()
        logger.info(
            "Synthesising chunk %s with Edge TTS voice %s …",
            chunk_id,
            self.voice,
        )
        temp_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
        try:
            asyncio.run(self._write_audio(text, temp_path))
            temp_path.replace(output_path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
        return output_path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _write_audio(self, text: str, output_path: Path) -> None:
        communicate = self._communicate_cls(  # type: ignore[misc]
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch,
        )
        with output_path.open("wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])

    def _cache_path(self, text: str) -> Path:
        key = hashlib.sha256(
            f"{self.language}:{self.voice}:{self.rate}:{self.volume}:{self.pitch}:{text}".encode()
        ).hexdigest()[:24]
        return CACHE_DIR / f"tts_{key}.mp3"
