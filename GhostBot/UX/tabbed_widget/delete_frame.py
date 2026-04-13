from GhostBot import logger
from GhostBot.UX.tabbed_widget.tab_frame import TabFrame
from GhostBot.config import Config, DeleteConfig
from GhostBot.lib.var_or_none import var_or_none


class DeleteFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            delete_trash=self._create_entry("Delete trash:", 0, 0, ("bot_config.delete.delete_trash", bool)),
            interval=self._create_entry("Interval:", 0, 2, ("bot_config.delete.interval", str)),
        )

    def _set_spot_as_current(self):
        self._vars['spot'].set(eval(self.master.getvar('char_info.position')))
        logger.debug(self.extract_config())

    def display_config(self, config: Config):
        if config.delete:
            self.setvar('bot_config.delete.delete_trash', bool(config.delete.delete_trash))
            self.setvar('bot_config.delete.interval', str(config.delete.interval) or '')
            pass
        else:
            self.clear()

    def extract_config(self) -> DeleteConfig:
        return DeleteConfig(
            delete_trash=var_or_none(self.getvar('bot_config.delete.delete_trash')),
            interval=var_or_none(self.getvar('bot_config.delete.interval')),
        )
