import curses

import npyscreen


class FunctionSelectForm(npyscreen.SelectOne):
    def __init__(self, *args, **kwargs):
        super(FunctionSelectForm, self).__init__(*args, **kwargs)
        self.add_handlers({
            curses.KEY_LEFT: self.h_exit_left,
            curses.KEY_RIGHT: self.h_exit_right
        })

    def display_value(self, vl):
        return str(vl)


class BoxedFunctionSelect(npyscreen.BoxTitle):
    _contained_widget = FunctionSelectForm

    def __init__(self, *args, **kwargs):
        self.name = 'Functions'
        values = [
            'Bindings',
            'Thresholds',
            'Intervals',
            'Attack'
        ]
        super(BoxedFunctionSelect, self).__init__(*args, values=values, **kwargs)
