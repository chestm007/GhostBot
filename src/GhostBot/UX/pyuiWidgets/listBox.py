# Author: Paul: https://github.com/PaulleDemon
# Made using PyUibuilder: https://pyuibuilder.com
# MIT License - keep the copy of this license

import tkinter as tk

class ScrollableListbox(tk.Frame):
    def __init__(self, parent, scrollx=False, scrolly=True, **kwargs):
        super().__init__(parent)

        # Create the listbox itself
        self.listbox = tk.Listbox(self, exportselection=False, **kwargs)
        self.listbox.grid(row=0, column=0, sticky="nsew")

        # Configure grid to allow stretching
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Add vertical scrollbar if enabled
        if scrolly:
            self.v_scroll = tk.Scrollbar(self, orient="vertical", command=self.listbox.yview)
            self.v_scroll.grid(row=0, column=1, sticky="ns")
            self.listbox.config(yscrollcommand=self.v_scroll.set)

        # Add horizontal scrollbar if enabled
        if scrollx:
            self.h_scroll = tk.Scrollbar(self, orient="horizontal", command=self.listbox.xview)
            self.h_scroll.grid(row=1, column=0, sticky="ew")
            self.listbox.config(xscrollcommand=self.h_scroll.set)

    def on_list_select(self, callback):
        self.listbox.bind('<<ListboxSelect>>', callback)

    def insert(self, *args, **kwargs):
        self.listbox.insert(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.listbox.delete(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.listbox.get(*args, **kwargs)

    def bind(self, *args, **kwargs):
        self.listbox.bind(*args, **kwargs)

    def curselection(self):
        return self.listbox.curselection()

    def configure(self, **kwargs):
        self.listbox.configure(**kwargs)

    def config(self, **kwargs):
        self.configure(**kwargs)