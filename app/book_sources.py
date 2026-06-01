"""Book source discovery for Android and desktop development."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from .config import SUPPORTED_EXTENSIONS


def candidate_roots() -> List[Path]:
    """Return likely roots for local book discovery.

    On desktop Ubuntu, this uses common home directories for development.
    On Android, these paths act as placeholders until native storage APIs are wired in.
    """

    home = Path.home()
    roots = [
        home / "Books",
        home / "Documents",
        home / "Downloads",
        Path("/sdcard"),
        Path("/storage/emulated/0"),
    ]
    return [root for root in roots if root.exists()]


def find_books(roots: Iterable[Path] | None = None) -> List[Path]:
    """Scan folders recursively for supported ebook files."""

    discovered: List[Path] = []
    for root in roots or candidate_roots():
        try:
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    discovered.append(path)
        except PermissionError:
            continue
    return sorted(set(discovered))
