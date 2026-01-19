# easyui/widgets/live_graph.py
from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional, Union

Number = Union[int, float]

# Minimal but nice-looking palette (no external libs)
_SERIES_COLORS = ["#00D1B2", "#FF6B6B", "#FFD93D", "#6BCBFF", "#B28DFF", "#A3E635"]


class LiveGraph:
    """
    Minimal live graph using Tk Canvas (no fancy deps).
    - Auto-scrolling time window (last N seconds)
    - Axes + grid + labels
    - Multiple series (dict name->value) or single number if series has length 1
    - Start/Stop, optional "Sample once" button
    """

    def __init__(
        self,
        parent,
        title: str,
        interval_ms: int,
        sampler: Callable[[], Union[Number, Dict[str, Number]]],
        series: List[str],
        max_points: int = 2000,
        window_seconds: float = 30.0,
        y_padding: float = 0.10,
        smooth_y: float = 0.20,  # 0..1, higher = faster scale adaptation
        show_log: bool = True,
        height: int = 280,
        sample_once_button: bool = True,
    ):
        self.parent = parent
        self.title = title
        self.interval_ms = int(interval_ms)
        self.sampler = sampler
        self.series = list(series)
        self.max_points = int(max_points)
        self.window_seconds = float(window_seconds)
        self.y_padding = float(y_padding)
        self.smooth_y = float(smooth_y)
        self.show_log = bool(show_log)

        self._running = False
        self._after_id: Optional[str] = None

        # data: name -> list[(t, y)]
        self.data: Dict[str, List[tuple[float, float]]] = {name: [] for name in self.series}

        # smoothed y-range
        self._y_min: Optional[float] = None
        self._y_max: Optional[float] = None

        # --- UI ---
        self.frame = ttk.Frame(parent, padding=(10, 10))
        self.frame.pack(fill="both", expand=True)

        header = ttk.Frame(self.frame)
        header.pack(fill="x")

        ttk.Label(header, text=self.title).pack(side="left")

        self.status = ttk.Label(
            header,
            text=f"window={self.window_seconds:g}s  interval={self.interval_ms}ms",
        )
        self.status.pack(side="left", padx=(12, 0))

        self.btn = ttk.Button(header, text="Start", command=self.toggle)
        self.btn.pack(side="right")

        if sample_once_button:
            self.btn_once = ttk.Button(header, text="Sample once", command=self.sample_once)
            self.btn_once.pack(side="right", padx=(0, 8))
        else:
            self.btn_once = None

        self.canvas = tk.Canvas(self.frame, height=height, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=(10, 0))

        if self.show_log:
            self.log = tk.Text(self.frame, height=6)
            self.log.pack(fill="x", pady=(10, 0))
            self.log.configure(state="disabled")
        else:
            self.log = None

        # redraw on resize
        self.canvas.bind("<Configure>", lambda e: self.redraw())

    # ----------------- Controls -----------------

    def toggle(self):
        if self._running:
            self.stop()
        else:
            self.start()

    def start(self):
        if self._running:
            return
        self._running = True
        self.btn.configure(text="Stop")
        self._tick()

    def stop(self):
        self._running = False
        self.btn.configure(text="Start")
        if self._after_id is not None:
            try:
                self.parent.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def sample_once(self):
        """Run the sampler once and redraw (does not start the periodic loop)."""
        self._append_sample()
        self.redraw()

    # ----------------- Sampling -----------------

    def _tick(self):
        if not self._running:
            return

        self._append_sample()
        self.redraw()

        self._after_id = self.parent.after(self.interval_ms, self._tick)

    def _append_sample(self):
        now = time.time()
        result = self.sampler()

        # Allow number for single-series shortcut
        if isinstance(result, (int, float)):
            if len(self.series) != 1:
                raise ValueError("Sampler returned a number but series has multiple names.")
            result = {self.series[0]: float(result)}

        if not isinstance(result, dict):
            raise ValueError("Sampler must return dict{name: value} or a single number for 1 series.")

        line_parts = []
        for idx, name in enumerate(self.series):
            if name not in result:
                continue
            y = float(result[name])
            self.data[name].append((now, y))

            # hard cap
            if len(self.data[name]) > self.max_points:
                self.data[name] = self.data[name][-self.max_points :]

            line_parts.append(f"{name}={y:.3f}")

        # Auto-scroll (time window)
        cutoff = now - self.window_seconds
        for name in self.series:
            self.data[name] = [(t, y) for (t, y) in self.data[name] if t >= cutoff]

        if self.log is not None and line_parts:
            self._log(f"{time.strftime('%H:%M:%S')}  " + "  ".join(line_parts))

    def _log(self, msg: str):
        if self.log is None:
            return
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    # ----------------- Drawing -----------------

    def redraw(self):
        w = max(10, self.canvas.winfo_width())
        h = max(10, self.canvas.winfo_height())
        pad_left = 54
        pad_right = 16
        pad_top = 16
        pad_bottom = 44

        self.canvas.delete("all")

        # Collect points within window
        all_points: List[tuple[float, float]] = []
        for name in self.series:
            all_points.extend(self.data.get(name, []))

        if len(all_points) < 2:
            # draw empty frame
            self._draw_frame(w, h, pad_left, pad_top, pad_right, pad_bottom)
            self.canvas.create_text(
                w // 2,
                h // 2,
                text="Waiting for data…",
                fill="#777",
            )
            return

        t_min = min(t for t, _ in all_points)
        t_max = max(t for t, _ in all_points)

        raw_min = min(y for _, y in all_points)
        raw_max = max(y for _, y in all_points)

        # Smooth Y scaling (optional)
        if self._y_min is None or self._y_max is None:
            self._y_min, self._y_max = raw_min, raw_max
        else:
            a = max(0.0, min(1.0, self.smooth_y))
            # Move towards new bounds smoothly
            self._y_min = (1 - a) * self._y_min + a * raw_min
            self._y_max = (1 - a) * self._y_max + a * raw_max
            # Ensure bounds still contain the current raw values
            self._y_min = min(self._y_min, raw_min)
            self._y_max = max(self._y_max, raw_max)

        y_min = float(self._y_min)
        y_max = float(self._y_max)

        # Avoid zero range + pad
        if t_max == t_min:
            t_max = t_min + 1.0
        if y_max == y_min:
            y_max = y_min + 1.0

        y_rng = y_max - y_min
        y_min -= y_rng * self.y_padding
        y_max += y_rng * self.y_padding
        if y_max == y_min:
            y_max = y_min + 1.0

        x0 = pad_left
        x1 = w - pad_right
        y0 = pad_top
        y1 = h - pad_bottom

        def x_of(t: float) -> float:
            return x0 + (t - t_min) / (t_max - t_min) * (x1 - x0)

        def y_of(y: float) -> float:
            return y1 - (y - y_min) / (y_max - y_min) * (y1 - y0)

        # Background + border
        self._draw_frame(w, h, pad_left, pad_top, pad_right, pad_bottom)

        # Grid + axis labels
        self._draw_grid_and_labels(
            x0, x1, y0, y1, t_min, t_max, y_min, y_max,
            w, h, pad_left, pad_bottom
        )

        # Plot each series
        for idx, name in enumerate(self.series):
            pts = self.data.get(name, [])
            if len(pts) < 2:
                continue

            coords = []
            for t, y in pts:
                coords.extend([x_of(t), y_of(y)])

            color = _SERIES_COLORS[idx % len(_SERIES_COLORS)]
            self.canvas.create_line(*coords, width=2, fill=color)

            # draw last value marker
            lx, ly = coords[-2], coords[-1]
            self.canvas.create_oval(lx - 3, ly - 3, lx + 3, ly + 3, fill=color, outline="")

        # Legend (top-right)
        self._draw_legend(x1, y0)

    def _draw_frame(self, w, h, pad_left, pad_top, pad_right, pad_bottom):
        x0 = pad_left
        x1 = w - pad_right
        y0 = pad_top
        y1 = h - pad_bottom
        # Background
        self.canvas.create_rectangle(x0, y0, x1, y1, fill="#111111", outline="#444444")

    def _draw_grid_and_labels(
        self,
        x0, x1, y0, y1,
        t_min, t_max,
        y_min, y_max,
        w, h,
        pad_left, pad_bottom
    ):
        # Y grid lines (5)
        for i in range(5):
            frac = i / 4
            yv = y_min + frac * (y_max - y_min)
            y = y1 - frac * (y1 - y0)
            self.canvas.create_line(x0, y, x1, y, fill="#2A2A2A")
            self.canvas.create_text(6, y, anchor="w", fill="#AAAAAA", text=f"{yv:.2f}")

        # X grid lines (5) + time labels as wall-clock timestamps within the window
        window = max(1e-6, (t_max - t_min))
        for i in range(5):
            frac = i / 4
            tv = t_min + frac * window           # actual time value at this tick mark
            x = x0 + frac * (x1 - x0)

            self.canvas.create_line(x, y0, x, y1, fill="#2A2A2A")


            label = time.strftime("%H:%M:%S", time.localtime(tv))
            if i == 0:
                anchor = "nw"   # text grows right
            elif i == 4:
                anchor = "ne"   # text grows left
            else:
                anchor = "n"

            self.canvas.create_text(
                x,
                h - pad_bottom + 4,
                anchor=anchor,
                fill="#AAAAAA",
                text=label
            )

        # Axis titles (light)
        self.canvas.create_text(pad_left, 2, anchor="nw", fill="#AAAAAA", text="Value")
        self.canvas.create_text(w // 2, h - 2, anchor="s", fill="#AAAAAA", text="Time")

    def _draw_legend(self, x1, y0):
        # Simple legend at top-right inside plot box
        x = x1 - 6
        y = y0 + 6
        for idx, name in enumerate(self.series):
            color = _SERIES_COLORS[idx % len(_SERIES_COLORS)]
            self.canvas.create_rectangle(x - 90, y, x - 76, y + 10, fill=color, outline="")
            self.canvas.create_text(x - 72, y + 5, anchor="w", fill="#DDDDDD", text=name)
            y += 14
