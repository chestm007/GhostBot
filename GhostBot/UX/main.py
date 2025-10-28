import npyscreen
from GhostBot import logger

from GhostBot.UX.forms.main_window import MainWindowForm, BoxedMainWindow
from GhostBot.bot_controller import BotController


class BotApplication(npyscreen.NPSAppManaged):
    def __init__(self, *args, **kwargs):
        self.bot_controller = BotController()

        super(BotApplication, self).__init__(*args, **kwargs)
        self.main_window = None

    def onStart(self):
        self.bot_window = self.addForm('MAIN', MainWindowForm, name='GhostBot v0.0.1', bot_controller=self.bot_controller)


if __name__ == '__main__':
    logger.debug('starting')
    print(1)
    app = BotApplication()
    logger.debug('bot backend loaded')
    print(2)
    app.run()
    print(3)
    logger.debug('bot backend loaded-ed')
