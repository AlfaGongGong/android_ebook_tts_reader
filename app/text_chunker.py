"""Text chunking utilities for punctuation-aware TTS synthesis."""

from __future__ import annotations

from typing import Iterable, List

from .config import DEFAULT_SENTENCES_PER_CHUNK
from .models import Chapter, PlaybackChunk


PUNCTUATION_WEIGHTS = {
    ".": 1.0,
    "!": 1.0,
    "?": 1.0,
    ";": 0.7,
    ":": 0.6,
    ",": 0.35,
}


def estimate_sentence_duration(text: str, words_per_minute: int = 140) -> float:
    words = max(1, len(text.split()))
    base = (words / words_per_minute) * 60
    pause_bonus = sum(PUNCTUATION_WEIGHTS.get(ch, 0.0) for ch in text)
    return base + pause_bonus


def chunk_chapter(
    chapter: Chapter,
    chapter_index: int,
    sentences_per_chunk: int = DEFAULT_SENTENCES_PER_CHUNK,
) -> List[PlaybackChunk]:
    chunks: List[PlaybackChunk] = []
    sentences = chapter.sentences

    for start in range(0, len(sentences), sentences_per_chunk):
        slice_ = sentences[start : start + sentences_per_chunk]
        text = " ".join(slice_)
        duration = sum(estimate_sentence_duration(sentence) for sentence in slice_)
        chunks.append(
            PlaybackChunk(
                id=f"{chapter_index}:{start}",
                chapter_index=chapter_index,
                sentence_start=start,
                sentence_end=min(start + len(slice_) - 1, len(sentences) - 1),
                text=text,
                estimated_duration_sec=duration,
            )
        )
    return chunks


def chunk_book(chapters: Iterable[Chapter]) -> List[PlaybackChunk]:
    all_chunks: List[PlaybackChunk] = []
    for chapter_index, chapter in enumerate(chapters):
        all_chunks.extend(chunk_chapter(chapter, chapter_index))
    return all_chunks
