import curses
import time

import npyscreen

from GhostBot import logger
from GhostBot.lib import vk_codes


class CharacterSelectForm(npyscreen.MultiSelect):
    parent: 'MainWindowForm'

    def __init__(self, *args, **kwargs):
        super(CharacterSelectForm, self).__init__(*args, always_show_cursor=True, **kwargs)
        self.add_handlers({
            curses.KEY_LEFT: self.h_exit_left,
            curses.KEY_RIGHT: self.h_exit_right
        })

    def display_value(self, vl):
        return f'[{vl.level}] - {vl.name}'

    def _get_client_at_cursor(self):
        return self.values[self.cursor_line]

    def update(self, clear=True):
        logger.debug(self.values)
        super(CharacterSelectForm, self).update(clear)
        self.parent.select_char(self._get_client_at_cursor())

    def h_select_toggle(self, input):
        super(CharacterSelectForm, self).h_select_toggle(input)
        if self.cursor_line in self.value:
            self.parent.start_bot(self._get_client_at_cursor())
        else:
            self.parent.stop_bot(self._get_client_at_cursor())


class BoxedCharacterSelector(npyscreen.BoxTitle):
    _contained_widget = CharacterSelectForm

    def __init__(self, *args, **kwargs):
        self.name = 'Characters'
        super(BoxedCharacterSelector, self).__init__(*args, **kwargs)

    def update_char_list(self, in_chars):
        self.values = in_chars
