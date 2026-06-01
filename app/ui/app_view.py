"""Kivy application screen logic."""

from __future__ import annotations

from pathlib import Path

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from ..book_sources import find_books
from ..models import Book
from ..parser import load_book
from ..state import AppState
from ..text_chunker import chunk_book
from .kv import KV_LAYOUT

Builder.load_string(KV_LAYOUT)


class ReaderRoot(BoxLayout):
    books = ListProperty([])
    status_text = StringProperty("Ready")
    selected_book_title = StringProperty("No book selected")
    progress_text = StringProperty("No saved progress")
    chapter_summary = StringProperty("Chapters: 0 | Sentences: 0")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = AppState()
        Clock.schedule_once(lambda *_: self.refresh_books(), 0)
        self._refresh_progress_label()

    def refresh_books(self) -> None:
        self.books = [str(path) for path in find_books()]
        self.status_text = f"Discovered {len(self.books)} supported book(s)."

    def select_book(self, path: str) -> None:
        try:
            book = load_book(Path(path))
            self.state.set_book(book)
            self._apply_book(book)
            self.status_text = f"Loaded: {book.title}"
        except Exception as exc:
            self.status_text = f"Failed to load book: {exc}"

    def _apply_book(self, book: Book) -> None:
        self.selected_book_title = book.title
        self.chapter_summary = f"Chapters: {book.chapter_count} | Sentences: {book.sentence_count}"
        self._refresh_progress_label()

    def simulate_beginning(self) -> None:
        self.state.update_position(chapter_index=0, sentence_index=0, chunk_index=0, char_offset=0)
        self.status_text = "Start position set to beginning."
        self._refresh_progress_label()

    def simulate_from_chapter(self) -> None:
        if not self.state.current_book or not self.state.current_book.chapters:
            self.status_text = "Load a book first."
            return
        chapter_index = min(1, len(self.state.current_book.chapters) - 1)
        self.state.update_position(chapter_index=chapter_index, sentence_index=0, chunk_index=0)
        self.status_text = f"Start position set to chapter {chapter_index + 1}."
        self._refresh_progress_label()

    def simulate_from_sentence(self) -> None:
        self.state.update_position(sentence_index=3, chunk_index=0)
        self.status_text = "Start position set to a sample sentence offset."
        self._refresh_progress_label()

    def simulate_buffering(self) -> None:
        book = self.state.current_book
        if not book:
            self.status_text = "Load a book first."
            return
        chunks = chunk_book(book.chapters)
        preview = ", ".join(chunk.id for chunk in chunks[:3]) or "none"
        self.status_text = f"Prepared {len(chunks)} chunks. Prefetch preview: {preview}"

    def _refresh_progress_label(self) -> None:
        pos = self.state.position
        self.progress_text = (
            f"Book: {pos.book_path or '-'} | "
            f"Chapter: {pos.chapter_index} | Sentence: {pos.sentence_index} | Chunk: {pos.chunk_index}"
        )
