from tkinter import ttk


class Tab:
    def __init__(self, title: str):
        self.title = title
        self.frame = None

    def _attach(self, notebook: ttk.Notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text=self.title)
