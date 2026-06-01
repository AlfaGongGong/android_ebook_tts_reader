"""Book parsing utilities for TXT and EPUB."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .models import Book, Chapter

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> List[str]:
    sentences = [item.strip() for item in SENTENCE_SPLIT_RE.split(text) if item.strip()]
    return sentences


def parse_txt(path: Path) -> Book:
    text = path.read_text(encoding="utf-8", errors="ignore")
    raw_chapters = re.split(r"\n\s*(?:chapter|poglavlje)\b", text, flags=re.IGNORECASE)
    chapters: List[Chapter] = []

    if len(raw_chapters) <= 1:
        chapters.append(Chapter(title="Full text", sentences=split_sentences(text)))
    else:
        for index, raw in enumerate(raw_chapters):
            raw = raw.strip()
            if not raw:
                continue
            chapters.append(Chapter(title=f"Chapter {index + 1}", sentences=split_sentences(raw)))

    return Book(path=path, title=path.stem, chapters=chapters)


def parse_epub(path: Path) -> Book:
    try:
        from ebooklib import epub
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise RuntimeError(
            "EPUB support requires ebooklib and beautifulsoup4. "
            "Install project dependencies with: pip install -r requirements.txt"
        ) from exc

    book = epub.read_epub(str(path))
    chapters: List[Chapter] = []

    for item in book.get_items_of_type(9):
        soup = BeautifulSoup(item.get_content(), "lxml")
        text = soup.get_text(" ", strip=True)
        if not text:
            continue
        title = soup.title.string.strip() if soup.title and soup.title.string else item.get_name()
        chapters.append(Chapter(title=title, sentences=split_sentences(text)))

    return Book(path=path, title=book.title or path.stem, chapters=chapters)


def load_book(path: str | Path) -> Book:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return parse_txt(path)
    if suffix == ".epub":
        return parse_epub(path)
    raise ValueError(f"Unsupported book format: {suffix}")
