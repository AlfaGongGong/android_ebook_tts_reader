"""Progress persistence for resumable reading."""

from __future__ import annotations

import json
from dataclasses import asdict

from .config import STATE_FILE
from .models import ReadingPosition


class ProgressStore:
    """Stores and restores last reading position."""

    def load(self) -> ReadingPosition:
        if not STATE_FILE.exists():
            return ReadingPosition()
        try:
            payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return ReadingPosition(**payload)
        except Exception:
            return ReadingPosition()

    def save(self, position: ReadingPosition) -> None:
        STATE_FILE.write_text(
            json.dumps(asdict(position), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
