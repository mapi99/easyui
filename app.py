import tkinter as tk
from tkinter import ttk


class App:
    def __init__(self, title: str = "EasyUI", size=(900, 500)):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{size[0]}x{size[1]}")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

    def add_tab(self, tab):
        tab._attach(self.notebook)

    def run(self):
        self.root.mainloop()
