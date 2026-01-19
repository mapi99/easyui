import tkinter as tk
from .base import BaseElement

class Input(BaseElement):
    def __init__(self, label=None, default=""):
        super().__init__(label)
        self.value = tk.StringVar(value=default)

    def render(self, parent):
        frame = tk.Frame(parent)
        frame.pack(side="left", padx=2)
        if self.label:
            tk.Label(frame, text=self.label).pack(side="top", anchor="w")
        self.widget = tk.Entry(frame, textvariable=self.value)
        self.widget.pack(fill="x")

    def get(self):
        return self.value.get()

    def set(self, val):
        self.value.set(val)
