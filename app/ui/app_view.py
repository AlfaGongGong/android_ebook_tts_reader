"""Kivy application screen logic – wired playback, navigation, and file picker."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from ..android_utils import is_android, open_file_picker, request_storage_permissions
from ..book_sources import find_books
from ..models import Book, ReadingPosition
from ..parser import load_book
from ..playback import PlaybackController
from ..state import AppState
from ..text_chunker import chunk_book
from .kv import KV_LAYOUT

Builder.load_string(KV_LAYOUT)

logger = logging.getLogger(__name__)


class ReaderRoot(BoxLayout):
    """Root widget: book selection, chapter/sentence navigation, and playback."""

    # KV-observable properties
    status_text = StringProperty("Ready")
    selected_book_title = StringProperty("No book selected")
    progress_text = StringProperty("No saved progress")
    chapter_summary = StringProperty("Chapters: 0 | Sentences: 0")
    play_pause_label = StringProperty("▶ Play")
    books: List[str] = ListProperty([])

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = AppState()
        self.controller = PlaybackController(
            on_progress=self._on_progress_update,
            on_status=self._on_status_update,
        )
        # Request Android permissions on startup
        if is_android():
            request_storage_permissions(callback=self._on_permissions)
        # Refresh book list after the first frame so the layout is ready
        Clock.schedule_once(lambda *_: self.refresh_books(), 0.1)
        self._refresh_progress_label()

    # ------------------------------------------------------------------
    # Book discovery
    # ------------------------------------------------------------------

    def refresh_books(self) -> None:
        """Scan default folders and rebuild the book list."""
        self.books = [str(p) for p in find_books()]
        self._rebuild_book_list()
        self.status_text = f"Found {len(self.books)} book(s)."

    def pick_file(self) -> None:
        """Open a native file picker to load a single ebook."""
        self.status_text = "Opening file picker …"
        open_file_picker(on_selection=self._on_file_picked)

    def _on_file_picked(self, selection: List[str]) -> None:
        if not selection:
            self.status_text = "No file selected."
            return
        path = selection[0]
        if path not in self.books:
            self.books = self.books + [path]
            self._rebuild_book_list()
        self.select_book(path)

    def _on_permissions(self, granted: bool) -> None:
        if granted:
            Clock.schedule_once(lambda *_: self.refresh_books(), 0)
        else:
            self.status_text = "Storage permission denied – book list may be empty."

    # ------------------------------------------------------------------
    # Book loading
    # ------------------------------------------------------------------

    def select_book(self, path: str) -> None:
        """Load *path* as the current book and reset reading position."""
        try:
            book = load_book(Path(path))
            self.state.set_book(book)
            self._apply_book(book)
            self.status_text = f"Loaded: {book.title}"
        except Exception as exc:
            logger.exception("Failed to load book: %s", path)
            self.status_text = f"Failed to load: {exc}"

    def _apply_book(self, book: Book) -> None:
        self.selected_book_title = book.title
        self.chapter_summary = (
            f"Chapters: {book.chapter_count} | Sentences: {book.sentence_count}"
        )
        # Reset chapter/sentence inputs
        self.ids.chapter_input.text = "0"
        self.ids.sentence_input.text = "0"
        self._refresh_progress_label()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def jump_to_position(self) -> None:
        """Read chapter/sentence inputs and update reading position."""
        book = self.state.current_book
        if not book:
            self.status_text = "Load a book first."
            return
        try:
            ch = int(self.ids.chapter_input.text or "0")
            sen = int(self.ids.sentence_input.text or "0")
        except ValueError:
            self.status_text = "Chapter and sentence must be numbers."
            return

        ch = max(0, min(ch, book.chapter_count - 1))
        max_sen = max(0, len(book.chapters[ch].sentences) - 1)
        sen = max(0, min(sen, max_sen))

        self.state.update_position(
            chapter_index=ch, sentence_index=sen, chunk_index=0, char_offset=0
        )
        self._refresh_progress_label()
        self.status_text = f"Position set → Chapter {ch + 1}, Sentence {sen + 1}."
        logger.info("Jumped to chapter=%d sentence=%d", ch, sen)

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def toggle_play_pause(self) -> None:
        """Toggle between play and pause."""
        if self.controller.is_playing():
            self.controller.pause()
            self.play_pause_label = "▶ Resume"
        elif self.controller.is_paused():
            self.controller.resume()
            self.play_pause_label = "⏸ Pause"
        else:
            self._start_playback()

    def stop_playback(self) -> None:
        """Stop playback entirely."""
        self.controller.stop()
        self.play_pause_label = "▶ Play"

    def _start_playback(self) -> None:
        book = self.state.current_book
        if not book:
            self.status_text = "Load a book first."
            return

        all_chunks = chunk_book(book.chapters)
        if not all_chunks:
            self.status_text = "No text chunks found in this book."
            return

        pos = self.state.position
        # Find the chunk that best covers the saved/user-selected position.
        # Walk forward: any chunk in an earlier chapter advances the candidate;
        # within the target chapter, update as long as sentence_start ≤ target.
        start_index = 0
        for i, chunk in enumerate(all_chunks):
            if chunk.chapter_index < pos.chapter_index:
                start_index = i + 1  # haven't reached target chapter yet
            elif chunk.chapter_index == pos.chapter_index:
                if chunk.sentence_start <= pos.sentence_index:
                    start_index = i   # this chunk covers or precedes the target sentence
                else:
                    break             # past the target sentence
            else:
                break                 # past the target chapter
        # Clamp to valid range
        start_index = min(start_index, len(all_chunks) - 1)

        self.controller.start(all_chunks, from_index=start_index)
        self.play_pause_label = "⏸ Pause"

    # ------------------------------------------------------------------
    # Callbacks from PlaybackController
    # ------------------------------------------------------------------

    def _on_progress_update(self, pos: ReadingPosition) -> None:
        """Called (on the main thread) whenever playback advances a chunk."""
        self.state.update_position(
            chapter_index=pos.chapter_index,
            sentence_index=pos.sentence_index,
            chunk_index=pos.chunk_index,
        )
        # Update chapter/sentence inputs to reflect current position
        self.ids.chapter_input.text = str(pos.chapter_index)
        self.ids.sentence_input.text = str(pos.sentence_index)
        self._refresh_progress_label()

    def _on_status_update(self, text: str) -> None:
        """Called (on the main thread) with status messages from the controller."""
        self.status_text = text
        # Reset play/pause label when playback completes or stops
        if text in ("Playback complete.", "Stopped."):
            self.play_pause_label = "▶ Play"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _refresh_progress_label(self) -> None:
        pos = self.state.position
        self.progress_text = (
            f"Ch: {pos.chapter_index} | Sen: {pos.sentence_index} | Chunk: {pos.chunk_index}"
        )

    def _rebuild_book_list(self) -> None:
        """Repopulate the book list grid with one button per book."""
        grid = self.ids.book_list_grid
        grid.clear_widgets()
        if not self.books:
            grid.add_widget(
                Label(
                    text=(
                        'No books found.\n'
                        'Use "Pick File" or place .epub/.txt files in\n'
                        '~/Books, ~/Documents, or ~/Downloads.'
                    ),
                    size_hint_y=None,
                    height=dp(70),
                    halign="left",
                    valign="top",
                )
            )
            return
        for path in self.books:
            label = Path(path).name
            btn = Button(
                text=label,
                size_hint_y=None,
                height=dp(46),
                halign="left",
                text_size=(None, None),
            )
            btn.bind(on_release=lambda b, p=path: self.select_book(p))
            grid.add_widget(btn)

