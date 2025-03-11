import curses

import npyscreen


class CharacterSelectForm(npyscreen.MultiSelect):
    def display_value(self, vl):
        return str(vl)

    def char_select(self, ch):
        self.parent.select_char(self.values[self.cursor_line])

    def set_up_handlers(self):
        super(CharacterSelectForm, self).set_up_handlers()
        self.handlers.update({
            curses.KEY_ENTER: self.char_select,
            curses.KEY_RIGHT: self.char_select
        })


class BoxedCharacterSelector(npyscreen.BoxTitle):
    _contained_widget = CharacterSelectForm

    def __init__(self, *args, **kwargs):
        self.name = 'Characters'
        super(BoxedCharacterSelector, self).__init__(*args, **kwargs)

    def update_char_list(self, in_chars):
        self.values = in_chars
