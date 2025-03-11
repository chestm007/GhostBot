import npyscreen

from GhostBot.client_window import ClientWindow


class CharacterInfoForm(npyscreen.MultiLine):
    def display_value(self, vl):
        return str(vl)


class BoxedCharacterInfo(npyscreen.BoxTitle):
    _contained_widget = CharacterInfoForm

    def __init__(self, *args, **kwargs):
        self.name = 'Info'
        super(BoxedCharacterInfo, self).__init__(*args, **kwargs)

    def update_char_info(self, client: ClientWindow):
        self.name = client.name
        self.values = [
            f'HP  : {client.hp}',
            f'MANA: [{client.mana}/{client.max_mana}]',
            f'Pos :  {client.location}'
        ]
        self.display()
