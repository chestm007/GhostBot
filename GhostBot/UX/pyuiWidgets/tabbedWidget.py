# Author: Paul: https://github.com/PaulleDemon
# Made using PyUibuilder: https://pyuibuilder.com
# MIT License - keep the copy of this license

import tkinter as tk
from tkinter import ttk


class TabbedWidget(ttk.Notebook):

    def __init__(self, master = None, enable_reorder=False, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        if enable_reorder:
            self.bind("<B1-Motion>", self.reorder)


    def reorder(self, event):
        try:
            index = self.index(f"@{event.x},{event.y}")
            self.insert(index, child=self.select())

        except tk.TclError:
            pass