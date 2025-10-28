from GhostBot.UX.tabbed_widget.TabFrame import TabFrame
from GhostBot.bot_controller import ExtendedClient
from GhostBot.config import Config, DeleteConfig
from GhostBot.lib.var_or_none import _int, _bool


class DeleteFrame(TabFrame):
    def _init(self, *args, **kwargs) -> None:
        self._vars = dict(
            delete_trash=self._create_entry("Delete trash:", 0, 0, ("bot_config.delete.delete_trash", bool)),
            interval=self._create_entry("Interval:", 0, 2, ("bot_config.delete.interval", str)),
        )

        #ttk.Button(
        #    master=self, text="Current", command=lambda: self._set_spot_as_current()
        #).grid(row=3, column=2)

    def _set_spot_as_current(self):
        self._vars['spot'].set(eval(self.master.getvar('char_info.position')))
        print(self.extract_config())

    def display_config(self, config: Config):
        if config.delete:
            self.setvar('bot_config.delete.delete_trash', bool(config.delete.delete_trash))
            self.setvar('bot_config.delete.interval', str(config.delete.delete_trash) or '')
            pass
        else:
            self.clear()

    def extract_config(self) -> DeleteConfig:
        return DeleteConfig(
            delete_trash=_bool(self.getvar('bot_config.delete.delete_trash')),
            interval=_int(self.getvar('bot_config.delete.interval')),
        )
