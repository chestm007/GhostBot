import tkinter as tk

class LogWindow(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master)

        self.text = tk.Text(self, exportselection=False, **kwargs)
        self.text.grid(row=0, column=0, sticky="nsew")

        # Configure grid to allow stretching
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.v_scroll = tk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.text.config(yscrollcommand=self.v_scroll.set)

    def configure(self, *args, **kwargs):
        self.text.configure(*args, **kwargs)

    def insert_log(self, text):
        self.log(1.0, text)

    def append_log(self, text):
        self.log('end', text)

    def log(self, index, text: str):
        self['state'] = 'normal'
        self.text.insert(index, chars=f"{text}\n")
        self['state'] = 'disabled'

