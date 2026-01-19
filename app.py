import tkinter as tk
from tkinter import ttk


class App:
    def __init__(self, title: str = "SimpleUI App", size=(800, 600)):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{size[0]}x{size[1]}")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self._tabs = []

    def add_tab(self, tab):
        tab._attach(self.notebook)
        self._tabs.append(tab)

    def run(self):
        self.root.mainloop()
