import logging
import tkinter as tk


class WidgetLogger(logging.Handler):
    def __init__(self, widget):
        logging.Handler.__init__(self)
        self.setLevel(logging.INFO)
        self.widget = widget
        self.widget.config(state='disabled')

    def emit(self, record):
        msg = self.format(record) + '\n'
        self.widget.after(0, self.append_text, msg)

    def append_text(self, msg):
        self.widget.config(state='normal')
        self.widget.insert(tk.END, msg)
        self.widget.see(tk.END)
        self.widget.config(state='disabled')
