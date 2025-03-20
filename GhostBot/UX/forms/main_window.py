import logging
import threading
import time

import npyscreen

from GhostBot import logger
from GhostBot.UX.forms.character_selector import BoxedCharacterSelector, CharacterSelectForm
from GhostBot.UX.forms.character_info import BoxedCharacterInfo
from GhostBot.UX.forms.function_menu import BoxedFunctionSelect
from GhostBot.UX.forms.log_panel import BoxedLogForm
from GhostBot.bot_controller import BotController


class TerminalLogger(logging.Handler):

    def __init__(self, log_func) -> None:
        logging.Handler.__init__(self, level=logger.level)
        self.sender = log_func

    def emit(self, record) -> None:
        self.sender(record)


class MainWindowForm(npyscreen.FormBaseNew):
    def __init__(self, bot_controller, *args, **kwargs):
        self.bot_controller: BotController = bot_controller
        super(MainWindowForm, self).__init__(*args, **kwargs)

    def create(self):
        x, y = self.useable_space()
        self.character_selector: CharacterSelectForm = self.add_widget(BoxedCharacterSelector, max_width=30)
        self.character_info: BoxedCharacterInfo = self.add_widget(BoxedCharacterInfo, max_width=30, max_height=10,
                                                                  relx=self.character_selector.width+2,
                                                                  rely=self.character_selector.rely)
        self.function_select: BoxedFunctionSelect = self.add_widget(BoxedFunctionSelect, max_width=30,
                                                                    relx=self.character_selector.width+2,
                                                                    rely=self.character_info.height+self.character_info.rely)
        self.log_window: BoxedLogForm = self.add_widget(BoxedLogForm,
                                                        relx=200, rely=self.character_selector.rely)

        self.term_log = TerminalLogger(self.log_window.add_log_message)

        logger.addHandler(self.term_log)

        self.display_char = list(self.bot_controller.clients.values())[0]
        self.refresh_char_list()
        self.char_info_thread = threading.Thread(target=self.char_info_thread_func)
        self.char_info_thread.start()
        logger.info('GhostBot loaded.')

    def refresh_char_list(self):
        self.character_selector.update_char_list(list(self.bot_controller.clients.values()))

    def char_info_thread_func(self):
        while True:
            self.character_info.update_char_info(self.display_char)
            time.sleep(0.5)

    def start_bot(self, client):
        self.bot_controller.start_bot(client)

    def stop_bot(self, client):
        self.bot_controller.stop_bot(client)

