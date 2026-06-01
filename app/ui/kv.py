KV_LAYOUT = r'''
#:import dp kivy.metrics.dp

<ReaderRoot>:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(6)

    # ── Header ────────────────────────────────────────────────────────
    Label:
        text: 'Ebook TTS Reader'
        size_hint_y: None
        height: dp(38)
        bold: True
        font_size: dp(17)
        halign: 'center'
        text_size: self.size

    Label:
        id: status_label
        text: root.status_text
        size_hint_y: None
        height: dp(28)
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'
        color: 0.9, 0.9, 0.9, 1

    Label:
        text: 'Book: ' + root.selected_book_title
        size_hint_y: None
        height: dp(24)
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'

    Label:
        text: root.chapter_summary
        size_hint_y: None
        height: dp(22)
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'
        color: 0.7, 0.9, 0.7, 1

    Label:
        text: root.progress_text
        size_hint_y: None
        height: dp(22)
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'
        color: 0.7, 0.85, 1, 1

    # ── Chapter / sentence navigation ─────────────────────────────────
    BoxLayout:
        size_hint_y: None
        height: dp(46)
        spacing: dp(6)

        Label:
            text: 'Chapter:'
            size_hint_x: None
            width: dp(65)

        TextInput:
            id: chapter_input
            text: '0'
            input_filter: 'int'
            multiline: False
            size_hint_x: None
            width: dp(55)
            hint_text: '0'

        Label:
            text: 'Sentence:'
            size_hint_x: None
            width: dp(65)

        TextInput:
            id: sentence_input
            text: '0'
            input_filter: 'int'
            multiline: False
            size_hint_x: None
            width: dp(55)
            hint_text: '0'

        Button:
            text: 'Jump'
            on_release: root.jump_to_position()

    # ── Playback controls ─────────────────────────────────────────────
    BoxLayout:
        size_hint_y: None
        height: dp(50)
        spacing: dp(8)

        Button:
            id: play_pause_btn
            text: root.play_pause_label
            font_size: dp(16)
            on_release: root.toggle_play_pause()

        Button:
            text: 'Stop'
            size_hint_x: None
            width: dp(90)
            font_size: dp(15)
            on_release: root.stop_playback()

    # ── Book discovery ─────────────────────────────────────────────────
    BoxLayout:
        size_hint_y: None
        height: dp(46)
        spacing: dp(8)

        Button:
            text: 'Pick File'
            on_release: root.pick_file()

        Button:
            text: 'Scan Books'
            on_release: root.refresh_books()

    # ── Book list ─────────────────────────────────────────────────────
    Label:
        text: 'Discovered books'
        size_hint_y: None
        height: dp(26)
        bold: True
        halign: 'left'
        text_size: self.size

    ScrollView:
        do_scroll_x: False
        bar_width: dp(8)

        GridLayout:
            id: book_list_grid
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(4)
            padding: dp(2)
'''
