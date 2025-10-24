import tkinter as tk

class LogWindow(tk.Text):
    def insert_log(self, text):
        self.log(1.0, text)

    def append_log(self, text):
        self.log('end', text)

    def log(self, index, text: str):
        self['state'] = 'normal'
        self.insert(index, chars=f"{text}\n")
        self['state'] = 'disabled'
