"""Application entry point."""

from __future__ import annotations

import sys

from app.cli import run_cli


def run_gui() -> None:
    from kivy.app import App

    from app.ui.app_view import ReaderRoot

    class EbookTTSReaderApp(App):
        def build(self):
            self.title = "Android Ebook TTS Reader"
            return ReaderRoot()

    EbookTTSReaderApp().run()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "gui":
        run_gui()
        return 0
    return run_cli(argv)


if __name__ == "__main__":
    raise SystemExit(main())
