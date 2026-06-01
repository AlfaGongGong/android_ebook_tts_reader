"""Application state helpers."""

from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from .models import Book, ReadingPosition
from .progress import ProgressStore


class AppState:
    """Keeps currently selected book and reading position in memory."""

    def __init__(self, store: Optional[ProgressStore] = None) -> None:
        self.store = store or ProgressStore()
        self.current_book: Optional[Book] = None
        self.position: ReadingPosition = self.store.load()

    def set_book(self, book: Book) -> None:
        self.current_book = book
        self.position.book_path = str(book.path)
        self.position.chapter_index = 0
        self.position.sentence_index = 0
        self.position.chunk_index = 0
        self.position.char_offset = 0
        self.store.save(self.position)

    def update_position(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self.position, key, value)
        self.store.save(self.position)

    def snapshot(self) -> dict:
        return asdict(self.position)
