"""Terminal interface for scanning, inspecting, and reading books."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .audio_player import AudioPlayer
from .book_sources import find_books
from .state import AppState
from .text_chunker import chunk_book
from .tts_engine import EdgeTTSEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the ebook reader without the Kivy Android GUI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List discovered books in default folders.")

    inspect_parser = subparsers.add_parser("inspect", help="Show book metadata.")
    inspect_parser.add_argument("book", help="Path to a .txt or .epub file.")

    read_parser = subparsers.add_parser("read", help="Read a book from the terminal.")
    read_parser.add_argument("book", help="Path to a .txt or .epub file.")
    read_parser.add_argument("--chapter", type=int, default=0, help="Zero-based chapter index.")
    read_parser.add_argument("--sentence", type=int, default=0, help="Zero-based sentence index.")
    read_parser.add_argument(
        "--max-chunks",
        type=int,
        default=0,
        help="Stop after N chunks (0 means read until the end).",
    )
    read_parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Only print chunks without synthesis or audio playback.",
    )
    return parser


def run_cli(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        return _list_books()
    if args.command == "inspect":
        return _inspect_book(args.book)
    if args.command == "read":
        return _read_book(
            book_path=args.book,
            chapter=args.chapter,
            sentence=args.sentence,
            max_chunks=args.max_chunks,
            no_audio=args.no_audio,
        )
    parser.print_help()
    return 1


def _list_books() -> int:
    books = find_books()
    if not books:
        print("No books found in the default folders.", file=sys.stderr)
        return 1
    for path in books:
        print(path)
    return 0


def _inspect_book(book_path: str) -> int:
    from .parser import load_book

    book = load_book(Path(book_path))
    print(f"Title: {book.title}")
    print(f"Path: {book.path}")
    print(f"Chapters: {book.chapter_count}")
    print(f"Sentences: {book.sentence_count}")
    for index, chapter in enumerate(book.chapters):
        print(f"[{index}] {chapter.title} ({len(chapter.sentences)} sentence(s))")
    return 0


def _read_book(
    book_path: str,
    chapter: int,
    sentence: int,
    max_chunks: int,
    no_audio: bool,
) -> int:
    from .parser import load_book

    book = load_book(Path(book_path))
    state = AppState()
    state.set_book(book)
    chunks = chunk_book(book.chapters)
    if not chunks:
        print("Book does not contain readable text chunks.", file=sys.stderr)
        return 1

    chapter_index = max(0, min(chapter, book.chapter_count - 1))
    sentence_index = max(
        0,
        min(sentence, len(book.chapters[chapter_index].sentences) - 1),
    )
    state.update_position(
        chapter_index=chapter_index,
        sentence_index=sentence_index,
        chunk_index=0,
        char_offset=0,
    )

    start_index = _resolve_start_chunk(chunks, chapter_index, sentence_index)
    engine = EdgeTTSEngine() if not no_audio else None
    player = AudioPlayer()

    print(f"Reading: {book.title}")
    print(f"Start position: chapter={chapter_index}, sentence={sentence_index}")
    print("Press Ctrl+C to stop.")

    processed = 0
    try:
        for chunk_index, chunk in enumerate(chunks[start_index:], start=start_index):
            if max_chunks and processed >= max_chunks:
                break
            state.update_position(
                chapter_index=chunk.chapter_index,
                sentence_index=chunk.sentence_start,
                chunk_index=chunk_index,
            )
            print(
                f"\n--- Chunk {chunk_index} | chapter={chunk.chapter_index} "
                f"| sentence={chunk.sentence_start}-{chunk.sentence_end} ---"
            )
            print(chunk.text)
            if no_audio:
                processed += 1
                continue
            audio_path = engine.synthesize_to_file(chunk.text, chunk.id)
            print(f"Audio: {audio_path}")
            if not no_audio:
                started = player.play(str(audio_path))
                if not started:
                    print("Audio playback backend is unavailable.", file=sys.stderr)
                    return 1
                while player.is_playing():
                    time.sleep(0.1)
            processed += 1
    except KeyboardInterrupt:
        print("\nStopped by user.")
        return 130
    finally:
        player.stop()

    print("\nDone.")
    return 0


def _resolve_start_chunk(chunks, chapter_index: int, sentence_index: int) -> int:
    start_index = 0
    for index, chunk in enumerate(chunks):
        if chunk.chapter_index < chapter_index:
            start_index = index + 1
        elif chunk.chapter_index == chapter_index:
            if chunk.sentence_start <= sentence_index:
                start_index = index
            else:
                break
        else:
            break
    return min(start_index, len(chunks) - 1)
