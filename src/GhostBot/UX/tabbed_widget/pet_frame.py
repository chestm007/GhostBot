import tkinter as tk

from GhostBot.UX.tabbed_widget.tab_frame import TabFrame


class PetFrame(TabFrame):
    """Aba Pet -- EM RECONSTRUCAO (zerada em 2026-05-26). Sera refeita do zero."""

    def _init(self, *args, **kwargs) -> None:
        self._vars = {}
        tk.Label(
            self, text="Aba Pet em reconstrucao -- sera refeita do zero.",
            anchor="w", justify="left",
        ).grid(row=0, column=0, padx=12, pady=12, sticky="w")

    def display_config(self, config) -> None:
        pass

    def extract_config(self):
        return None
