import curses
from logging import LogRecord

import npyscreen


class LogForm(npyscreen.BufferPager):
    def display_value(self, vl: LogRecord):
        if vl:
            return f'{vl.msg}'
        else:
            return ''

    def set_up_handlers(self):
        super().set_up_handlers()
        self.handlers.update({
            curses.KEY_LEFT: self.h_exit_left,
            curses.KEY_RIGHT: self.h_exit_right
        })


class BoxedLogForm(npyscreen.BoxTitle):
    _contained_widget = LogForm
    name = 'Log Panel'

    def add_log_message(self, message: str):
        self.entry_widget.buffer([message])
        self.display()

