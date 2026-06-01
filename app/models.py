"""Domain models for books, navigation, and playback state."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class SentenceRef:
    chapter_index: int
    sentence_index: int
    text: str


@dataclass
class Chapter:
    title: str
    sentences: List[str] = field(default_factory=list)


@dataclass
class Book:
    path: Path
    title: str
    chapters: List[Chapter] = field(default_factory=list)

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    @property
    def sentence_count(self) -> int:
        return sum(len(chapter.sentences) for chapter in self.chapters)


@dataclass
class ReadingPosition:
    book_path: str = ""
    chapter_index: int = 0
    sentence_index: int = 0
    chunk_index: int = 0
    char_offset: int = 0


@dataclass
class PlaybackChunk:
    id: str
    chapter_index: int
    sentence_start: int
    sentence_end: int
    text: str
    estimated_duration_sec: float
    audio_path: Optional[str] = None
