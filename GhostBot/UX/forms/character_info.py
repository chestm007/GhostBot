import curses

import npyscreen

from GhostBot.bot_controller import ExtendedClient


class CharacterInfoForm(npyscreen.Pager):
    pass


class BoxedCharacterInfo(npyscreen.BoxTitle):
    _contained_widget = CharacterInfoForm

    def __init__(self, *args, **kwargs):
        self.name = 'Info'
        super(BoxedCharacterInfo, self).__init__(*args, **kwargs)
        self.add_handlers({
            curses.KEY_LEFT: self.h_exit_left,
            curses.KEY_RIGHT: self.h_exit_right
        })

    def update_char_info(self, client: ExtendedClient):
        self.name = f'{client.name} - {client.level}'
        self.values = [
            f'HP      : [{client.hp}/{client.max_hp}]',
            f'MANA    : [{client.mana}/{client.max_mana}]',
            f'Pos     : [{int(client.location_x)}/{int(client.location_y)}]',
            f'Battle  : {client.in_battle}',
            f'Sitting : {client.sitting}',
            f'Tgt Name: {client.target_name}',
            f'Tgt HP  : {client.target_hp}',
            f'Status  : {client.bot_status_string}'
        ]
        self.display()
