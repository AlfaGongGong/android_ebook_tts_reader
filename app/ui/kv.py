KV_LAYOUT = r'''
<ReaderRoot>:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(8)

    Label:
        text: 'Android Ebook TTS Reader'
        size_hint_y: None
        height: dp(40)
        bold: True

    Label:
        text: root.status_text
        size_hint_y: None
        height: dp(30)
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'

    Label:
        text: 'Selected: ' + root.selected_book_title
        size_hint_y: None
        height: dp(30)
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'

    Label:
        text: root.chapter_summary
        size_hint_y: None
        height: dp(30)
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'

    Label:
        text: root.progress_text
        size_hint_y: None
        height: dp(50)
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'

    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(8)

        Button:
            text: 'Refresh books'
            on_release: root.refresh_books()

        Button:
            text: 'From beginning'
            on_release: root.simulate_beginning()

        Button:
            text: 'From chapter'
            on_release: root.simulate_from_chapter()

        Button:
            text: 'From sentence'
            on_release: root.simulate_from_sentence()

    Button:
        text: 'Simulate buffering'
        size_hint_y: None
        height: dp(44)
        on_release: root.simulate_buffering()

    Label:
        text: 'Discovered books'
        size_hint_y: None
        height: dp(30)

    ScrollView:
        do_scroll_x: False

        GridLayout:
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(6)

            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.12, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            Label:
                size_hint_y: None
                height: dp(1)
                text: ''

            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: max(dp(40), len(root.books) * dp(44))
                spacing: dp(4)

                canvas.before:
                    Color:
                        rgba: 0, 0, 0, 0
                    Rectangle:
                        pos: self.pos
                        size: self.size

                Label:
                    text: 'No books found yet' if not root.books else ''
                    size_hint_y: None
                    height: dp(30)

                RecycleView:
                    viewclass: 'Button'
                    data: [{'text': item, 'size_hint_y': None, 'height': dp(40), 'on_release': lambda x=item: root.select_book(x)} for item in root.books]
                    RecycleBoxLayout:
                        default_size: None, dp(40)
                        default_size_hint: 1, None
                        size_hint_y: None
                        height: self.minimum_height
                        orientation: 'vertical'
'''
