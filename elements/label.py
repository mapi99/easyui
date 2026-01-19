import tkinter as tk
from .base import BaseElement

class Label(BaseElement):
    def render(self, parent):
        self.widget = tk.Label(parent, text=self.label)
        self.widget.pack(side="left", padx=2)
