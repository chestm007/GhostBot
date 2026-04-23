import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import Variable, StringVar, BooleanVar
from typing import final

from GhostBot.config import Config, FunctionConfig


type VarConfig = tuple[str, type[str | bool]]

class TabFrame(tk.Frame, ABC):

    _vars: dict[str, Variable]

    @staticmethod
    def _nullable_string(x):
        return x if x and x != 'None' else None

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
            if isinstance(var, StringVar):
                var.set('')
            elif isinstance(var, BooleanVar):
                var.set(False)
