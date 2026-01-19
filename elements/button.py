import tkinter as tk
from .base import BaseElement

class Button(BaseElement):
    def __init__(self, label, on_click=None):
        super().__init__(label)
        self.on_click = on_click

    def render(self, parent):
        self.widget = tk.Button(parent, text=self.label, command=self.on_click)
        self.widget.pack(side="left", padx=2)
