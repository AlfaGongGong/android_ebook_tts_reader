"""Coqui XTTS integration scaffold."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .config import CACHE_DIR, DEFAULT_LANGUAGE


class XTTSEngine:
    """Thin wrapper around Coqui XTTS v2.

    This scaffold intentionally keeps model loading optional because full XTTS
    integration on Android may require additional optimization and testing.
    """

    def __init__(self, language: str = DEFAULT_LANGUAGE, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2") -> None:
        self.language = language
        self.model_name = model_name
        self._tts = None

    def ensure_loaded(self) -> None:
        if self._tts is not None:
            return
        try:
            from TTS.api import TTS

            self._tts = TTS(self.model_name)
        except Exception as exc:
            raise RuntimeError(
                "XTTS engine could not be loaded in the current environment. "
                "Install compatible Coqui TTS dependencies and model assets."
            ) from exc

    def synthesize_to_file(self, text: str, chunk_id: str, speaker_wav: Optional[str] = None) -> Path:
        output_path = CACHE_DIR / f"chunk_{chunk_id.replace(':', '_')}.wav"
        self.ensure_loaded()
        self._tts.tts_to_file(
            text=text,
            file_path=str(output_path),
            language=self.language,
            speaker_wav=speaker_wav,
        )
        return output_path
