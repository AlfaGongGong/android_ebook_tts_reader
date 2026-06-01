"""Application entry point."""

from kivy.app import App

from app.ui.app_view import ReaderRoot


class EbookTTSReaderApp(App):
    def build(self):
        self.title = "Android Ebook TTS Reader"
        return ReaderRoot()


if __name__ == "__main__":
    EbookTTSReaderApp().run()
