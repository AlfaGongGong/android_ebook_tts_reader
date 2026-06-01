"""Cross-platform audio playback wrapper using Kivy's SoundLoader."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AudioPlayer:
    """Thin wrapper around Kivy's ``SoundLoader`` for sequential audio playback.

    Usage::

        player = AudioPlayer()
        player.play("/path/to/chunk.mp3")
        # ... later ...
        if not player.is_playing():
            player.play("/path/to/next_chunk.mp3")
        player.stop()
    """

    def __init__(self) -> None:
        self._sound = None
        self._backend = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play(self, audio_path: str) -> bool:
        """Load *audio_path* and start playback.

        Stops any currently playing sound first.
        Returns ``True`` if playback started successfully.
        """
        self.stop()
        try:
            from kivy.core.audio import SoundLoader  # imported lazily so tests can run without a display
        except Exception as exc:
            logger.warning("Kivy audio import failed: %s", exc)
            return self._play_with_simpleaudio(audio_path)

        sound = SoundLoader.load(audio_path)
        if sound is None:
            logger.warning("SoundLoader could not load: %s", audio_path)
            return self._play_with_simpleaudio(audio_path)
        self._sound = sound
        self._backend = "kivy"
        sound.play()
        logger.debug("Playing: %s", audio_path)
        return True

    def stop(self) -> None:
        """Stop playback and release the current sound object."""
        if self._sound is not None:
            try:
                self._sound.stop()
                if self._backend == "kivy":
                    self._sound.unload()
            except Exception as exc:
                logger.debug("Error stopping sound: %s", exc)
            self._sound = None
            self._backend = None

    def is_playing(self) -> bool:
        """Return ``True`` if audio is currently playing."""
        if self._sound is None:
            return False
        try:
            if self._backend == "simpleaudio":
                return self._sound.is_playing()
            return self._sound.state == "play"
        except Exception:
            return False

    def _play_with_simpleaudio(self, audio_path: str) -> bool:
        if not audio_path.lower().endswith(".wav"):
            logger.warning(
                "simpleaudio fallback supports WAV files only, cannot play: %s",
                audio_path,
            )
            return False
        try:
            import simpleaudio
        except Exception as exc:
            logger.warning("simpleaudio import failed: %s", exc)
            return False

        try:
            wave_object = simpleaudio.WaveObject.from_wave_file(audio_path)
            self._sound = wave_object.play()
            self._backend = "simpleaudio"
            logger.debug("Playing with simpleaudio: %s", audio_path)
            return True
        except Exception as exc:
            logger.warning("simpleaudio could not play %s: %s", audio_path, exc)
            self._sound = None
            self._backend = None
            return False
