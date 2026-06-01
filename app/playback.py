"""Buffered synthesis and playback pipeline scaffold."""

from __future__ import annotations

import queue
import threading
from typing import Iterable, List, Optional

from .config import PREFETCH_BLOCKS
from .models import PlaybackChunk
from .tts_engine import XTTSEngine


class BufferedPlaybackController:
    """Generates upcoming chunks while current chunks are being consumed.

    This initial version prepares synthesis jobs and tracks readiness.
    Real-time audio playback should be added in a later iteration.
    """

    def __init__(self, engine: Optional[XTTSEngine] = None, prefetch_blocks: int = PREFETCH_BLOCKS) -> None:
        self.engine = engine or XTTSEngine()
        self.prefetch_blocks = prefetch_blocks
        self._job_queue: queue.Queue[PlaybackChunk | None] = queue.Queue()
        self._ready: List[PlaybackChunk] = []
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._started = False

    def start(self) -> None:
        if not self._started:
            self._worker.start()
            self._started = True

    def enqueue_chunks(self, chunks: Iterable[PlaybackChunk]) -> None:
        for chunk in chunks:
            self._job_queue.put(chunk)

    def stop(self) -> None:
        self._job_queue.put(None)

    def _run(self) -> None:
        while True:
            chunk = self._job_queue.get()
            if chunk is None:
                return
            try:
                audio_path = self.engine.synthesize_to_file(chunk.text, chunk.id)
                chunk.audio_path = str(audio_path)
                self._ready.append(chunk)
            except Exception:
                # Keep the scaffold resilient during local UI development.
                self._ready.append(chunk)

    def ready_chunks(self) -> List[PlaybackChunk]:
        return list(self._ready)
