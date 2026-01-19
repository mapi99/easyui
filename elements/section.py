import tkinter as tk
from .label import Label
from .input import Input
from .button import Button

class Section:
    def __init__(self, title=None):
        self.title = title
        self.frame = None
        self.rows = []  # list of rows; each row is list of elements
        self.elements = []  # top-level elements (optional)

    def _attach(self, parent):
        # Create the section frame inside the tab
        self.frame = tk.LabelFrame(parent, text=self.title) if self.title else tk.Frame(parent)
        self.frame.pack(fill="x", pady=5, padx=5, anchor="n")

        # Render all rows
        for row in self.rows:
            row_frame = tk.Frame(self.frame)
            row_frame.pack(fill="x", pady=2)
            for el in row:
                el.render(row_frame)

        # Render top-level elements (not in a row)
        for el in self.elements:
            el.render(self.frame)

    # -------------------------
    # New API: add row + elements
    # -------------------------
    def add_row_elements(self, element_specs):
        """
        element_specs: list of dicts like
        {'type': 'input', 'label': 'Username', 'default': 'abc', 'on_click': func}
        """
        row = []
        for spec in element_specs:
            t = spec.get("type")
            if t == "input":
                el = Input(spec.get("label"), spec.get("default", ""))
            elif t == "button":
                el = Button(spec.get("label"), spec.get("on_click"))
            elif t == "label":
                el = Label(spec.get("label"))
            else:
                continue
            row.append(el)
        self.rows.append(row)
        return row
