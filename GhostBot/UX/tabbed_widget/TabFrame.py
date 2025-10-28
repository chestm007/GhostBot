import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk
from typing import final

from GhostBot.config import Config, FunctionConfig


VarConfig = tuple[str, str | bool]

class TabFrame(tk.Frame, ABC):

    _vars: dict

    _nullable_string = lambda x: x if x and x != 'None' else None

    def __init__(self, master, *args, **kwargs):
        super().__init__(master)
        self.config(bg="#EDECEC", width=650, height=459)

        self._init(*args, **kwargs)

    def _create_entry(
            self,
            label: str,
            row: int,
            column: int,
            var_config: VarConfig = None,
    ) -> tk.Variable | None:

        v_name, v_type = var_config
        if v_type is str:  # Entry
            var = tk.StringVar(master=self, name=v_name, value="")
            ttk.Label(master=self, text=label, width=15).grid(row=row, column=column)
            tk.Entry(master=self, textvariable=var).grid(row=row, column=column + 1)

        elif v_type is bool:  # Checkbutton
            var = tk.BooleanVar(master=self, name=v_name, value=False)
            ttk.Checkbutton(master=self, text=label, variable=var, width=13).grid(row=row, column=column)

        else:
            raise TypeError(f"v_type must be str or bool, not {type(v_type)}")

        return var


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
