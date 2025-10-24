import tkinter as tk
from abc import ABC, abstractmethod
from typing import final

from GhostBot.config import Config, FunctionConfig


class TabFrame(tk.Frame, ABC):

    _vars: dict

    def __init__(self, master, *args, **kwargs):
        super().__init__(master)
        self.config(bg="#EDECEC", width=650, height=459)

        self._init(*args, **kwargs)

    @abstractmethod
    def _init(self, *args, **kwargs) -> None: ...

    @abstractmethod
    def display_config(self, config: Config) -> None: ...

    @abstractmethod
    def extract_config(self) -> FunctionConfig:
        """Function to create ``FunctionConfig`` for this tab"""

    def _clear(self) -> None:
        """Override this instead of ``self.clear()``"""

    @staticmethod
    def _populate_bindings(bindings: dict):
        return {k: v for k, v in bindings.items() if v is not None} or None

    @final
    def clear(self):
        """Override ``self._clear()`` instead."""
        self._clear()
        for var in self._vars.values():
            var.set('')
