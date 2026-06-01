"""Cross-platform audio playback wrapper using Kivy's SoundLoader.

On desktop (Linux/macOS/Windows) Kivy uses GStreamer or SDL2.
On Android Kivy uses the android audio backend (MediaPlayer).
Both support WAV files without additional native dependencies.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AudioPlayer:
    """Thin wrapper around Kivy's ``SoundLoader`` for sequential WAV playback.

    Usage::

        player = AudioPlayer()
        player.play("/path/to/chunk.wav")
        # ... later ...
        if not player.is_playing():
            player.play("/path/to/next_chunk.wav")
        player.stop()
    """

    def __init__(self) -> None:
        self._sound = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play(self, wav_path: str) -> bool:
        """Load *wav_path* and start playback.

        Stops any currently playing sound first.
        Returns ``True`` if playback started successfully.
        """
        self.stop()
        try:
            from kivy.core.audio import SoundLoader  # imported lazily so tests can run without a display
        except Exception as exc:
            logger.warning("Kivy audio import failed: %s", exc)
            return False

        sound = SoundLoader.load(wav_path)
        if sound is None:
            logger.warning("SoundLoader could not load: %s", wav_path)
            return False
        self._sound = sound
        sound.play()
        logger.debug("Playing: %s", wav_path)
        return True

    def stop(self) -> None:
        """Stop playback and release the current sound object."""
        if self._sound is not None:
            try:
                self._sound.stop()
                self._sound.unload()
            except Exception as exc:
                logger.debug("Error stopping sound: %s", exc)
            self._sound = None

    def is_playing(self) -> bool:
        """Return ``True`` if audio is currently playing."""
        if self._sound is None:
            return False
        try:
            return self._sound.state == "play"
        except Exception:
            return False
