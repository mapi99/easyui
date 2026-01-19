from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Dict, List

from tkinter import ttk


@dataclass
class _IORowSpec:
    label: str
    key: str
    button: str
    on_click: Optional[Callable[[], None]] = None
    extra: Optional[str] = None
    default: str = ""
    output: bool = False
    width: int = 24



class IOField:
    """Small handle returned to users so they can get/set easily."""
    def __init__(self, var):
        self._var = var

    def get(self) -> str:
        return self._var.get()

    def set(self, value: str) -> None:
        self._var.set(value)


class Tab:
    def __init__(self, title: str):
        self.title = title
        self.frame = None  # ttk.Frame after attach
        self._rows: List[_IORowSpec] = []

        # public storage: users/callbacks can access values by key
        self.values: Dict[str, IOField] = {}

    def _attach(self, notebook: ttk.Notebook):
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text=self.title)

        # Make the tab content expand nicely
        self.frame.columnconfigure(0, weight=1)

        # Render all queued rows
        for i, spec in enumerate(self._rows):
            self._render_io_row(i, spec)

    def add_io_row(
        self,
        label: str,
        key: str,
        button: str = "",
        on_click: Optional[Callable[[], None]] = None,
        extra: Optional[str] = None,
        default: str = "",
        output: bool = False,
        width: int = 24,
    ) -> IOField:
        """
        One-liner: creates a compact row with:
        [Label + Input (expands)] | [Button (compact)] | [Extra (optional)]
        """
        spec = _IORowSpec(
            label=label,
            key=key,
            button=button,
            on_click=on_click,
            extra=extra,
            default=default,
            output=output,
            width=width,
        )

        self._rows.append(spec)

        # If already attached, render immediately
        if self.frame is not None:
            self._render_io_row(len(self._rows) - 1, spec)

        # Return handle (will be bound after render)
        # If not rendered yet, we return a placeholder that will be replaced in self.values later.
        # To keep it simple, we return the eventual object by key after render; if not rendered yet,
        # create a temporary IOField and overwrite it on render.
        if key not in self.values:
            from tkinter import StringVar
            self.values[key] = IOField(StringVar(value=default))
        return self.values[key]

    def _render_io_row(self, row_index: int, spec: _IORowSpec) -> None:
        assert self.frame is not None

        # Row container
        row = ttk.Frame(self.frame, padding=(8, 6))
        row.grid(row=row_index, column=0, sticky="ew")
        row.columnconfigure(1, weight=0)  # input expands

        # Label
        lbl = ttk.Label(row, text=spec.label)
        lbl.grid(row=0, column=0, sticky="w", padx=(0, 8))

        # Input (StringVar)
        from tkinter import StringVar
        var = getattr(self.values.get(spec.key), "_var", None)
        if var is None:
            var = StringVar(value=spec.default)
            self.values[spec.key] = IOField(var)
        else:
            # ensure default is applied if it was a placeholder
            if var.get() == "" and spec.default:
                var.set(spec.default)

        # Input vs Output field (readonly)
        entry_state = "readonly" if spec.output else "normal"

        entry = ttk.Entry(row, textvariable=var, width=spec.width, state=entry_state)
        entry.grid(row=0, column=1, sticky="w")


        # Button (compact)
        btn = ttk.Button(row, text=spec.button, command=spec.on_click)
        btn.grid(row=0, column=2, sticky="e", padx=(8, 0))

        # Extra (optional)
        if spec.extra:
            extra_lbl = ttk.Label(row, text=spec.extra)
            extra_lbl.grid(row=0, column=3, sticky="w", padx=(10, 0))
