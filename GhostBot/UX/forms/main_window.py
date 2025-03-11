import npyscreen

from GhostBot.UX.character_selector import BoxedCharacterSelector
from GhostBot.UX.forms.character_info import BoxedCharacterInfo
from GhostBot.mem_scanner import BotController


class MainWindowForm(npyscreen.FormBaseNew):
    def __init__(self, bot_controller, *args, **kwargs):
        self.bot_controller: BotController = bot_controller
        super(MainWindowForm, self).__init__(*args, **kwargs)

    def create(self):
        x, y = self.useable_space()
        self.character_selector: BoxedCharacterSelector = self.add_widget(BoxedCharacterSelector, max_width=30)
        self.character_info: BoxedCharacterInfo = self.add_widget(BoxedCharacterInfo, max_width=50,
                                                                  relx=self.character_selector.width+2,
                                                                  rely=self.character_selector.rely)
        self.refresh_char_list()

    def refresh_char_list(self):
        self.character_selector.update_char_list(self.bot_controller.client_keys)

    def select_char(self, ch):
        self.character_info.update_char_info(self.bot_controller.clients.get(ch))

