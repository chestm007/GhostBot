import npyscreen

from GhostBot.UX.character_selector import BoxedCharacterSelector
from GhostBot.UX.forms.character_info import BoxedCharacterInfo
from GhostBot.UX.forms.function_menu import BoxedFunctionSelect
from GhostBot.mem_scanner import BotController


class MainWindowForm(npyscreen.FormBaseNew):
    def __init__(self, bot_controller, *args, **kwargs):
        self.bot_controller: BotController = bot_controller
        super(MainWindowForm, self).__init__(*args, **kwargs)

    def create(self):
        x, y = self.useable_space()
        self.character_selector: BoxedCharacterSelector = self.add_widget(BoxedCharacterSelector, max_width=30)
        self.character_info: BoxedCharacterInfo = self.add_widget(BoxedCharacterInfo, max_width=30, max_height=10,
                                                                  relx=self.character_selector.width+2,
                                                                  rely=self.character_selector.rely)
        self.function_select: BoxedFunctionSelect = self.add_widget(BoxedFunctionSelect, max_width=30,
                                                                    relx=self.character_selector.width+2,
                                                                    rely=self.character_info.height+self.character_info.rely)
        self.refresh_char_list()

    def refresh_char_list(self):
        self.character_selector.update_char_list(list(self.bot_controller.clients.values()))

    def select_char(self, client):
        self.character_info.update_char_info(client)

    def start_bot(self, client):
        self.bot_controller.start_bot(client)

    def stop_bot(self, client):
        self.bot_controller.stop_bot(client)

