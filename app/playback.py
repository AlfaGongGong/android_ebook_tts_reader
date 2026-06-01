"""Buffered TTS synthesis and sequential playback controller.

Architecture
------------
* A daemon *synthesis thread* iterates over pending chunks, calls XTTSEngine to
  produce WAV files, and stores results in ``_ready``.
* A Kivy Clock interval (running on the main thread) polls every
  ``_POLL_INTERVAL`` seconds.  If the current sound has finished and the next
  chunk is ready, playback advances automatically.
* Progress and status callbacks are always dispatched via
  ``Clock.schedule_once`` so callers can safely update UI properties.
* Prefetch is capped at ``PREFETCH_BLOCKS`` chunks ahead of the current
  playback position to avoid exhausting memory on resource-limited devices.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Dict, List, Optional

from .audio_player import AudioPlayer
from .config import PREFETCH_BLOCKS
from .models import PlaybackChunk, ReadingPosition
from .tts_engine import XTTSEngine

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 0.3  # seconds between playback-advance polls


class PlaybackController:
    """Controls buffered TTS synthesis and sequential audio playback."""

    def __init__(
        self,
        on_progress: Optional[Callable[[ReadingPosition], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        engine: Optional[XTTSEngine] = None,
        prefetch_blocks: int = PREFETCH_BLOCKS,
    ) -> None:
        self._on_progress = on_progress
        self._on_status = on_status
        self.engine = engine or XTTSEngine()
        self.prefetch = prefetch_blocks

        # Chunk list and navigation indices
        self._chunks: List[PlaybackChunk] = []
        self._next_play: int = 0       # next chunk index to hand off to audio player
        self._current_play: int = -1   # chunk index currently (or last) playing

        # Synthesis results: chunk-index → wav-path (empty string = synthesis failed)
        self._ready: Dict[int, str] = {}
        self._ready_lock = threading.Lock()

        # Synthesis thread management
        self._synth_index: int = 0     # next chunk index queued for synthesis
        self._synth_stop = threading.Event()
        self._synth_thread: Optional[threading.Thread] = None

        self._audio = AudioPlayer()
        self._state: str = "stopped"   # "stopped" | "playing" | "paused"
        self._poll_clock = None        # Kivy scheduled event handle

    # ------------------------------------------------------------------
    # Public API (call from the Kivy main thread)
    # ------------------------------------------------------------------

    def start(self, chunks: List[PlaybackChunk], from_index: int = 0) -> None:
        """Begin playback of *chunks* starting at *from_index*."""
        self._stop_internals()
        self._chunks = list(chunks)
        self._next_play = from_index
        self._current_play = -1
        self._synth_index = from_index
        with self._ready_lock:
            self._ready.clear()
        self._state = "playing"
        self._start_synth_thread()
        self._start_poll()
        self._notify_status(f"Playback starting from chunk {from_index} …")

    def pause(self) -> None:
        """Pause; the current chunk will restart when resumed."""
        if self._state != "playing":
            return
        self._state = "paused"
        self._audio.stop()
        # rewind so resume replays the interrupted chunk
        if self._current_play >= 0:
            self._next_play = self._current_play
        self._notify_status("Paused.")

    def resume(self) -> None:
        """Resume from where playback was paused."""
        if self._state != "paused":
            return
        self._state = "playing"
        self._notify_status("Resuming …")
        self._try_play_next()

    def stop(self) -> None:
        """Stop playback and synthesis entirely."""
        self._stop_internals()
        self._notify_status("Stopped.")

    def is_playing(self) -> bool:
        return self._state == "playing"

    def is_paused(self) -> bool:
        return self._state == "paused"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _stop_internals(self) -> None:
        self._state = "stopped"
        self._synth_stop.set()
        self._audio.stop()
        if self._poll_clock is not None:
            try:
                self._poll_clock.cancel()
            except Exception:
                pass
            self._poll_clock = None
        # Synthesis thread is a daemon; it will terminate when _synth_stop is set.

    def _start_synth_thread(self) -> None:
        self._synth_stop.clear()
        self._synth_thread = threading.Thread(
            target=self._synth_worker, daemon=True, name="tts-synth"
        )
        self._synth_thread.start()

    def _synth_worker(self) -> None:
        """Background: synthesise chunks up to prefetch limit."""
        while not self._synth_stop.is_set():
            # Count how many chunks are synthesised and still ahead of playback
            with self._ready_lock:
                ahead = sum(1 for k in self._ready if k >= self._next_play)
            if ahead > self.prefetch:
                time.sleep(0.1)
                continue
            if self._synth_index >= len(self._chunks):
                break   # nothing left to synthesise
            chunk = self._chunks[self._synth_index]
            idx = self._synth_index
            self._synth_index += 1
            try:
                path = self.engine.synthesize_to_file(chunk.text, chunk.id)
                with self._ready_lock:
                    self._ready[idx] = str(path)
                logger.debug("Synthesised chunk %d → %s", idx, path)
            except Exception as exc:
                logger.warning("Synthesis failed for chunk %d: %s", idx, exc)
                with self._ready_lock:
                    self._ready[idx] = ""   # empty = failed, skip on playback
                self._notify_status(f"TTS error on chunk {idx}: {exc}")

    def _start_poll(self) -> None:
        from kivy.clock import Clock  # imported here to keep module importable without display
        if self._poll_clock is not None:
            try:
                self._poll_clock.cancel()
            except Exception:
                pass
        self._poll_clock = Clock.schedule_interval(self._poll, _POLL_INTERVAL)

    def _poll(self, _dt: float) -> None:
        """Called on the Kivy main thread; advance playback when audio is idle."""
        if self._state != "playing":
            return
        if self._audio.is_playing():
            return
        self._try_play_next()

    def _try_play_next(self) -> None:
        """Play the next ready chunk, or wait if synthesis is still pending."""
        if self._state != "playing":
            return

        # Walk past any consecutive failed chunks
        while self._next_play < len(self._chunks):
            with self._ready_lock:
                path = self._ready.get(self._next_play)
            if path is None:
                # Not yet synthesised – wait for next poll
                return
            idx = self._next_play
            self._current_play = idx
            self._next_play += 1
            chunk = self._chunks[idx]
            self._notify_progress(chunk)
            if path:
                self._audio.play(path)
                return  # audio is now playing; poll will advance when it stops
            # path == "" → synthesis failed, skip silently

        # All chunks exhausted
        self._state = "stopped"
        if self._poll_clock is not None:
            try:
                self._poll_clock.cancel()
            except Exception:
                pass
            self._poll_clock = None
        self._notify_status("Playback complete.")

    # ------------------------------------------------------------------
    # Callbacks (always dispatched on the Kivy main thread)
    # ------------------------------------------------------------------

    def _notify_progress(self, chunk: PlaybackChunk) -> None:
        if self._on_progress is None:
            return
        pos = ReadingPosition(
            chapter_index=chunk.chapter_index,
            sentence_index=chunk.sentence_start,
            chunk_index=self._current_play,
        )
        try:
            from kivy.clock import Clock
            Clock.schedule_once(lambda *_: self._on_progress(pos), 0)  # type: ignore[misc]
        except Exception:
            pass

    def _notify_status(self, text: str) -> None:
        if self._on_status is None:
            return
        try:
            from kivy.clock import Clock
            Clock.schedule_once(lambda *_: self._on_status(text), 0)  # type: ignore[misc]
        except Exception:
            pass

