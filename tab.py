from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Dict, List

from tkinter import ttk
import tkinter as tk





@dataclass
class _IORowSpec:
    label: str
    key: str
    button: str = ""
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
        self.frame: Optional[ttk.Frame] = None

        self._rows: List[_IORowSpec] = []
        self.values: Dict[str, IOField] = {}

        # created on attach
        self._pw: Optional[ttk.PanedWindow] = None
        self._col_io: Optional[ttk.Frame] = None
        self._col_btn: Optional[ttk.Frame] = None
        self._col_extra: Optional[ttk.Frame] = None

        # how many rows already rendered
        self._rendered_count: int = 0

    def _attach(self, notebook: ttk.Notebook) -> None:
        self.frame = ttk.Frame(notebook)
        if hasattr(self, "_post_attach"):
            for fn in self._post_attach:
                fn()
            self._post_attach.clear()

        notebook.add(self.frame, text=self.title)

        # Outer PanedWindow (draggable column sizing)
        self._pw = tk.PanedWindow(
            self.frame,
            orient="horizontal",
            sashwidth=3,
            sashrelief="raised",
            showhandle=True,
            bd=1,
        )
        self._pw.pack(fill="both", expand=True)

        # --- IO pane is itself a PanedWindow: [Label] | [Entry] ---
        self._io_pw = tk.PanedWindow(
            self._pw,
            orient="horizontal",
            sashwidth=3,
            sashrelief="raised",
            showhandle=True,
            bd=0,
        )

        self._col_label = ttk.Frame(self._io_pw, padding=(10, 10))
        self._col_entry = ttk.Frame(self._io_pw, padding=(10, 10))

        self._io_pw.add(self._col_label)
        self._io_pw.add(self._col_entry)

        # Other columns
        self._col_btn = ttk.Frame(self._pw, padding=(10, 10))
        self._col_extra = ttk.Frame(self._pw, padding=(10, 10))

        # Add panes to the OUTER PanedWindow
        self._pw.add(self._io_pw)
        self._pw.add(self._col_btn)
        self._pw.add(self._col_extra)

        # Grid behavior inside columns
        self._col_label.columnconfigure(0, weight=1)
        self._col_entry.columnconfigure(0, weight=1)
        self._col_btn.columnconfigure(0, weight=0)
        self._col_extra.columnconfigure(0, weight=1)

        # render queued rows
        self._render_pending_rows()


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
        One-liner row:
          IO column:    [Label][Entry]
          Button col:   [Button]   (optional)
          Extra col:    [Extra]    (optional)

        output=True -> Entry becomes readonly (still programmatically settable).
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

        # Create placeholder value immediately so callbacks can reference it
        if key not in self.values:
            from tkinter import StringVar
            self.values[key] = IOField(StringVar(value=default))

        # If already attached, render only what’s new
        if self.frame is not None:
            self._render_pending_rows()

        return self.values[key]

    def _render_pending_rows(self) -> None:
        # Only render if attached
        if (
            self._col_label is None
            or self._col_entry is None
            or self._col_btn is None
            or self._col_extra is None
        ):
            return

        while self._rendered_count < len(self._rows):
            spec = self._rows[self._rendered_count]
            self._render_io_row(self._rendered_count, spec)
            self._rendered_count += 1


    def _render_io_row(self, row_index: int, spec: _IORowSpec) -> None:
        # Safety
        assert (
            self._col_label is not None
            and self._col_entry is not None
            and self._col_btn is not None
            and self._col_extra is not None
        )

        # --- Label column ---
        lbl = ttk.Label(self._col_label, text=spec.label)
        lbl.grid(row=row_index, column=0, sticky="w", pady=4)

        # --- Entry column ---
        var = self.values[spec.key]._var
        entry_state = "readonly" if spec.output else "normal"
        entry = ttk.Entry(self._col_entry, textvariable=var, width=spec.width, state=entry_state)
        entry.grid(row=row_index, column=0, sticky="w", pady=4)

        # --- Button column cell ---
        if spec.button:
            btn = ttk.Button(self._col_btn, text=spec.button, command=spec.on_click)
            btn.grid(row=row_index, column=0, sticky="w", pady=4)
        else:
            spacer = ttk.Label(self._col_btn, text="")
            spacer.grid(row=row_index, column=0, sticky="w", pady=4)

        # --- Extra column cell ---
        if spec.extra:
            extra_lbl = ttk.Label(self._col_extra, text=spec.extra)
            extra_lbl.grid(row=row_index, column=0, sticky="w", pady=4)
        else:
            spacer = ttk.Label(self._col_extra, text="")
            spacer.grid(row=row_index, column=0, sticky="w", pady=4)


    def add_live_graph(self, title: str, interval_ms: int, sampler, series, max_points: int = 200, ):
        from .widgets.live_graph import LiveGraph
        if self.frame is None:
            # if not attached yet, queue it like your rows do.
            # simplest approach: store a callable to run on attach
            if not hasattr(self, "_post_attach"):
                self._post_attach = []
            self._post_attach.append(lambda: LiveGraph(self.frame, title, interval_ms, sampler, series, max_points))
            return None
        return LiveGraph(self.frame, title, interval_ms, sampler, series, max_points)
