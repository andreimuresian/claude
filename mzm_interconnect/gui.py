"""
MZM Studio -- a Tk front end over the whole toolkit.

Everything on the left is generated from ``parameters.PARAMS``: to expose a new
physical knob you add one ``ParamSpec`` and the widget, the tooltip, the sweep
menu entry and the CLI flag all appear by themselves.

Tabs
  Response          normalised EO S21 + electrical S11, with the KPI strip
  Line diagnostics  alpha(f), Zc(f), n_m(f): de-embedded points vs the fit
  Sweep             pick any sweepable parameter, sweep it, plot any metric
  INTERCONNECT      export tables, build the schematic, overlay the solver
  Log               everything the engine said
"""

from __future__ import annotations

import os
import queue
import threading
import traceback
import webbrowser
from typing import Callable, Optional

import matplotlib
matplotlib.use("TkAgg")

import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from tkinter import filedialog, messagebox, ttk

from . import parameters as P
from . import sweep as SW
from .extractor import (DARK as FIG_DARK, LIGHT as FIG_LIGHT, bandwidth_spread,
                        diagnostic_figure, eo_figure, export_lumerical_tables,
                        export_touchstone, extraction_warnings)
from .physics import eo_response, link_metrics

APP_TITLE = "MZM Studio  --  traveling-wave Mach-Zehnder modulator explorer"

THEMES = {
    "dark": dict(bg="#12151c", panel="#1b1f27", card="#232833", fg="#dfe4ec",
                 muted="#8a93a5", accent="#4f9cf9", ok="#4fae7c", warn="#d99b2e",
                 err="#e2504a", entry="#2a3040", border="#3a4152", fig=FIG_DARK),
    "light": dict(bg="#eef1f6", panel="#ffffff", card="#ffffff", fg="#1c2028",
                  muted="#66707f", accent="#2f6fd0", ok="#2e8b57", warn="#b8860b",
                  err="#c0392b", entry="#ffffff", border="#cfd6e0", fig=FIG_LIGHT),
}


# =====================================================================
# Small widgets
# =====================================================================
class Tooltip:
    """Hover help, so every parameter can carry its physical meaning."""

    DELAY_MS = 550

    def __init__(self, widget, text: str, theme: dict):
        self.widget, self.text, self.theme = widget, text, theme
        self.tip = None
        self._job = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<Button>", self._hide, add="+")

    def _schedule(self, _evt=None):
        # A hover delay keeps a pointer sweeping across the sidebar from
        # creating (and tearing down) dozens of override-redirect Toplevels.
        self._cancel()
        try:
            self._job = self.widget.after(self.DELAY_MS, self._show)
        except tk.TclError:
            pass

    def _cancel(self):
        if self._job is not None:
            try:
                self.widget.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _show(self, _evt=None):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, justify="left", wraplength=330,
                 bg=self.theme["card"], fg=self.theme["fg"],
                 relief="solid", bd=1, padx=8, pady=6,
                 font=("Segoe UI", 8)).pack()

    def _hide(self, _evt=None):
        self._cancel()
        if self.tip:
            try:
                self.tip.destroy()
            except tk.TclError:
                pass
            self.tip = None


class ScrollFrame(ttk.Frame):
    """Vertically scrollable container (the parameter sidebar)."""

    def __init__(self, master, theme, **kw):
        super().__init__(master, **kw)
        self.canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                                bg=theme["panel"], width=330)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = ttk.Frame(self.canvas, style="Panel.TFrame")
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfigure(self._win, width=e.width))
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.bind_all(seq, self._wheel, add="+")

    def _wheel(self, event):
        try:
            if not str(self.canvas.winfo_containing(event.x_root, event.y_root)
                       ).startswith(str(self.canvas)):
                return
        except Exception:
            return
        delta = 1 if getattr(event, "num", None) == 5 else (
            -1 if getattr(event, "num", None) == 4 else -int(event.delta / 120))
        self.canvas.yview_scroll(delta, "units")


class Collapsible(ttk.Frame):
    """A titled, click-to-fold group of parameters."""

    def __init__(self, master, title: str, theme: dict, open_: bool = True):
        super().__init__(master, style="Panel.TFrame")
        self.theme = theme
        self._open = tk.BooleanVar(value=open_)
        self.header = tk.Frame(self, bg=theme["card"], cursor="hand2")
        self.header.pack(fill="x", pady=(6, 0))
        self.arrow = tk.Label(self.header, text="v" if open_ else ">",
                              bg=theme["card"], fg=theme["accent"],
                              font=("Segoe UI", 8, "bold"), width=2)
        self.arrow.pack(side="left", padx=(8, 0), pady=4)
        self.title = tk.Label(self.header, text=title.upper(), bg=theme["card"],
                              fg=theme["muted"], font=("Segoe UI", 8, "bold"),
                              anchor="w")
        self.title.pack(side="left", fill="x", expand=True, pady=4)
        self.body = ttk.Frame(self, style="Panel.TFrame")
        if open_:
            self.body.pack(fill="x", padx=4)
        for w in (self.header, self.arrow, self.title):
            w.bind("<Button-1>", self.toggle)

    def toggle(self, _evt=None):
        self._open.set(not self._open.get())
        if self._open.get():
            self.body.pack(fill="x", padx=4)
            self.arrow.config(text="v")
        else:
            self.body.forget()
            self.arrow.config(text=">")


class KpiStrip(ttk.Frame):
    """The row of headline numbers above the plots."""

    FIELDS = [
        ("bw", "EO bandwidth", "GHz", "accent"),
        ("vpi", "V_pi (device)", "V", "fg"),
        ("vpil", "V_pi x L", "V.cm", "fg"),
        ("er", "Extinction ratio", "dB", "fg"),
        ("chirp", "Chirp alpha", "", "fg"),
        ("walk", "|n_m - n_g| @BW", "", "fg"),
        ("s11", "Worst S11", "dB", "fg"),
    ]

    def __init__(self, master, theme):
        super().__init__(master, style="Panel.TFrame")
        self.theme = theme
        self.values = {}
        self.units = {}
        for i, (key, label, unit, color) in enumerate(self.FIELDS):
            card = tk.Frame(self, bg=theme["card"], bd=0,
                            highlightbackground=theme["border"], highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew", padx=3, pady=3)
            self.columnconfigure(i, weight=1)
            tk.Label(card, text=label.upper(), bg=theme["card"], fg=theme["muted"],
                     font=("Segoe UI", 7, "bold")).pack(anchor="w", padx=9, pady=(6, 0))
            v = tk.Label(card, text="--", bg=theme["card"], fg=theme[color],
                         font=("Segoe UI", 16, "bold"))
            v.pack(anchor="w", padx=9)
            u = tk.Label(card, text=unit, bg=theme["card"], fg=theme["muted"],
                         font=("Segoe UI", 7))
            u.pack(anchor="w", padx=9, pady=(0, 6))
            self.values[key] = v
            self.units[key] = u

    def set_unit(self, key, text):
        if key in self.units:
            self.units[key].config(text=text)

    def update_values(self, res, lm, clipped=False):
        def fmt(x, n=2):
            if x is None or not np.isfinite(x):
                return "inf"
            return f"{x:.{n}f}"
        self.values["bw"].config(
            text=fmt(res.bw_GHz) + (" +" if clipped else ""),
            fg=self.theme["warn"] if clipped else self.theme["accent"])
        self.values["vpi"].config(text=fmt(lm.vpi_eff_V))
        self.values["vpil"].config(text=fmt(lm.vpi_L_Vcm))
        self.values["er"].config(text=fmt(lm.er_dB, 1))
        self.values["chirp"].config(text=fmt(lm.chirp_alpha, 3))
        self.values["walk"].config(text=fmt(res.walkoff_at_bw, 3))
        self.values["s11"].config(text=fmt(res.s11_worst_dB, 1))


class FigurePane(ttk.Frame):
    """
    Holds one matplotlib figure and swaps it out cleanly on redraw.

    Matplotlib binds <Configure> straight to a full Agg re-render, and a single
    redraw of these figures costs ~90 ms. A window-manager resize drag emits
    Configure continuously, so the events arrive faster than they can be served
    and the whole application stops responding. We therefore take over the
    <Configure> binding and coalesce a storm of them into one redraw once the
    resize has settled, skipping panes on notebook tabs that are not visible.
    """

    RESIZE_DEBOUNCE_MS = 120

    class _SizeEvent:
        __slots__ = ("width", "height")

    def __init__(self, master, theme, toolbar=True):
        super().__init__(master, style="Panel.TFrame")
        self.theme, self.toolbar = theme, toolbar
        self.canvas = None
        self.tb = None
        self.figure = None
        self._resize_job = None
        self._pending_size = None
        self.placeholder = tk.Label(
            self, text="Load a Touchstone file and press  Extract + analyse",
            bg=theme["panel"], fg=theme["muted"], font=("Segoe UI", 10))
        self.placeholder.pack(expand=True)

    def show(self, fig):
        self._cancel_resize()
        if self.placeholder is not None:
            self.placeholder.destroy()
            self.placeholder = None
        if self.canvas is not None:
            self.canvas.get_tk_widget().destroy()
        if self.tb is not None:
            self.tb.destroy()
        self.figure = fig
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        if self.toolbar:
            # The toolbar's icons are light-background PNGs, so it keeps its
            # native colour even in the dark theme -- recolouring it makes the
            # icons unreadable.
            self.tb = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
            self.tb.update()
            self.tb.pack(side="bottom", fill="x")
        widget = self.canvas.get_tk_widget()
        widget.pack(side="top", fill="both", expand=True)
        # Replace matplotlib's own <Configure> -> resize binding with ours.
        widget.bind("<Configure>", self._queue_resize)
        widget.bind("<Map>", self._on_map, add="+")

    def _cancel_resize(self):
        if self._resize_job is not None:
            try:
                self.after_cancel(self._resize_job)
            except Exception:
                pass
            self._resize_job = None

    def _queue_resize(self, event):
        self._pending_size = (event.width, event.height)
        self._cancel_resize()
        try:
            self._resize_job = self.after(self.RESIZE_DEBOUNCE_MS, self._apply_resize)
        except tk.TclError:
            pass

    def _apply_resize(self):
        self._resize_job = None
        if self.canvas is None or self._pending_size is None:
            return
        widget = self.canvas.get_tk_widget()
        try:
            if not widget.winfo_ismapped():
                return            # hidden tab: keep the size, redraw on <Map>
        except tk.TclError:
            return
        w, h = self._pending_size
        self._pending_size = None
        evt = self._SizeEvent()
        evt.width, evt.height = w, h
        try:
            self.canvas.resize(evt)
        except Exception:
            pass

    def _on_map(self, _evt=None):
        if self._pending_size is not None:
            self._apply_resize()


# =====================================================================
# The application
# =====================================================================
class MZMStudio(tk.Tk):

    def __init__(self, theme_name: str = "dark", initial: Optional[dict] = None):
        super().__init__()
        self.theme_name = theme_name
        self.theme = THEMES[theme_name]
        self.title(APP_TITLE)
        self.geometry("1580x960")
        self.minsize(1180, 740)
        self.configure(bg=self.theme["bg"])

        self.vars: dict[str, tk.Variable] = {}
        self.fit = None
        self.result = None
        self.sweep_result = None
        self.lumerical_overlay = None
        # The lumapi session object owns the INTERCONNECT process: if nothing
        # holds a reference it is garbage-collected and the window closes by
        # itself. Keep it on the app, not in a local variable.
        self.ic_builder = None
        self._closing = False
        self._busy = False
        self._cancel = threading.Event()
        self._q: queue.Queue = queue.Queue()

        self._init_style()
        self._build_header()
        self._build_body()
        self._build_status()

        params = P.defaults()
        if initial:
            params.update(initial)
        self._set_params(params)

        self.bind("<F5>", lambda e: self.action_analyse())
        self.bind("<Control-s>", lambda e: self.action_save_session())
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(80, self._pump)

    def _on_close(self):
        self._closing = True
        if self.ic_builder is not None:
            try:
                self.ic_builder.close()
            except Exception:
                pass
            self.ic_builder = None
        self.destroy()

    # ---------------- styling ----------------------------------------
    def _init_style(self):
        t = self.theme
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=t["panel"], foreground=t["fg"],
                    fieldbackground=t["entry"], bordercolor=t["border"],
                    font=("Segoe UI", 9))
        s.configure("TFrame", background=t["panel"])
        s.configure("Panel.TFrame", background=t["panel"])
        s.configure("Bg.TFrame", background=t["bg"])
        s.configure("TLabel", background=t["panel"], foreground=t["fg"])
        s.configure("Muted.TLabel", background=t["panel"], foreground=t["muted"],
                    font=("Segoe UI", 8))
        s.configure("TEntry", fieldbackground=t["entry"], foreground=t["fg"],
                    insertcolor=t["fg"], bordercolor=t["border"])
        s.configure("TCombobox", fieldbackground=t["entry"], background=t["entry"],
                    foreground=t["fg"], arrowcolor=t["fg"], bordercolor=t["border"])
        s.map("TCombobox", fieldbackground=[("readonly", t["entry"])],
              foreground=[("readonly", t["fg"])])
        self.option_add("*TCombobox*Listbox.background", t["entry"])
        self.option_add("*TCombobox*Listbox.foreground", t["fg"])
        self.option_add("*TCombobox*Listbox.selectBackground", t["accent"])
        s.configure("TCheckbutton", background=t["panel"], foreground=t["fg"])
        s.map("TCheckbutton", background=[("active", t["panel"])])
        s.configure("TButton", background=t["card"], foreground=t["fg"],
                    bordercolor=t["border"], focuscolor=t["panel"], padding=(10, 5))
        s.map("TButton", background=[("active", t["border"])])
        s.configure("Accent.TButton", background=t["accent"], foreground="#ffffff",
                    font=("Segoe UI", 9, "bold"), padding=(14, 6))
        s.map("Accent.TButton", background=[("active", t["accent"])])
        s.configure("TNotebook", background=t["bg"], bordercolor=t["border"])
        s.configure("TNotebook.Tab", background=t["panel"], foreground=t["muted"],
                    padding=(16, 7), font=("Segoe UI", 9))
        s.map("TNotebook.Tab", background=[("selected", t["card"])],
              foreground=[("selected", t["fg"])])
        s.configure("TProgressbar", background=t["accent"], troughcolor=t["card"],
                    bordercolor=t["border"])
        s.configure("TPanedwindow", background=t["bg"])
        s.configure("TSeparator", background=t["border"])

    # ---------------- header ------------------------------------------
    def _build_header(self):
        t = self.theme
        bar = tk.Frame(self, bg=t["bg"])
        bar.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(bar, text="MZM STUDIO", bg=t["bg"], fg=t["fg"],
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(bar, text="traveling-wave Mach-Zehnder  |  CST S-parameters "
                           "-> EO bandwidth -> INTERCONNECT",
                 bg=t["bg"], fg=t["muted"], font=("Segoe UI", 9)).pack(side="left", padx=12)

        ttk.Button(bar, text="Load session", command=self.action_load_session).pack(side="right", padx=3)
        ttk.Button(bar, text="Save session", command=self.action_save_session).pack(side="right", padx=3)
        ttk.Button(bar, text=("Light theme" if self.theme_name == "dark" else "Dark theme"),
                   command=self.action_toggle_theme).pack(side="right", padx=3)

        # A non-modal banner. Errors must never be reported with a modal dialog
        # from a background job: INTERCONNECT takes focus when it launches, the
        # dialog ends up behind it, and its grab makes the app look frozen.
        self.banner = tk.Frame(self, bg=t["err"])
        self.banner_text = tk.Label(self.banner, text="", bg=t["err"], fg="#ffffff",
                                    anchor="w", justify="left", padx=12, pady=7,
                                    font=("Segoe UI", 9))
        self.banner_text.pack(side="left", fill="x", expand=True)
        tk.Button(self.banner, text="Show log", bg=t["err"], fg="#ffffff", bd=0,
                  activebackground=t["err"], cursor="hand2",
                  font=("Segoe UI", 8, "bold"),
                  command=lambda: self.nb.select(self.tab_log)).pack(side="right", padx=4)
        tk.Button(self.banner, text="X", bg=t["err"], fg="#ffffff", bd=0,
                  activebackground=t["err"], cursor="hand2",
                  font=("Segoe UI", 9, "bold"),
                  command=self.hide_banner).pack(side="right", padx=(4, 10))

    def show_banner(self, message: str):
        try:
            self.banner_text.config(text=message)
            self.banner.pack(fill="x", padx=12, pady=(0, 2), before=self._body_pane)
        except tk.TclError:
            pass

    def hide_banner(self):
        try:
            self.banner.pack_forget()
        except tk.TclError:
            pass

    # ---------------- body ---------------------------------------------
    def _build_body(self):
        t = self.theme
        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=12, pady=6)
        self._body_pane = pane

        # ---- left: parameters ----
        left = ttk.Frame(pane, style="Panel.TFrame")
        pane.add(left, weight=0)

        act = ttk.Frame(left, style="Panel.TFrame")
        act.pack(fill="x", padx=8, pady=8)
        ttk.Button(act, text="Extract + analyse   (F5)", style="Accent.TButton",
                   command=self.action_analyse).pack(fill="x")
        self.auto_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(act, text="Re-analyse when a value changes",
                        variable=self.auto_var).pack(anchor="w", pady=(6, 0))

        self.sidebar = ScrollFrame(left, t)
        self.sidebar.pack(fill="both", expand=True)
        self._build_param_widgets(self.sidebar.inner)

        # ---- right: results ----
        right = ttk.Frame(pane, style="Bg.TFrame")
        pane.add(right, weight=1)

        self.kpi = KpiStrip(right, t)
        self.kpi.pack(fill="x", padx=2, pady=(0, 6))

        self.nb = ttk.Notebook(right)
        self.nb.pack(fill="both", expand=True)

        self.tab_response = ttk.Frame(self.nb, style="Panel.TFrame")
        self.tab_diag = ttk.Frame(self.nb, style="Panel.TFrame")
        self.tab_sweep = ttk.Frame(self.nb, style="Panel.TFrame")
        self.tab_lum = ttk.Frame(self.nb, style="Panel.TFrame")
        self.tab_log = ttk.Frame(self.nb, style="Panel.TFrame")
        for f, n in ((self.tab_response, "Response"), (self.tab_diag, "Line diagnostics"),
                     (self.tab_sweep, "Sweep"), (self.tab_lum, "INTERCONNECT"),
                     (self.tab_log, "Log")):
            self.nb.add(f, text=n)

        rbar = ttk.Frame(self.tab_response, style="Panel.TFrame")
        rbar.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Button(rbar, text="Export Touchstone", style="Accent.TButton",
                   command=self.action_export_touchstone).pack(side="left")
        ttk.Label(rbar, text="writes both traces on this tab -- S11 and EO S21, "
                            "magnitude and phase -- at the settings currently in the "
                            "sidebar, with every one of them recorded in the header",
                  style="Muted.TLabel", wraplength=740, justify="left").pack(side="left", padx=12)
        self.fig_response = FigurePane(self.tab_response, t)
        self.fig_response.pack(fill="both", expand=True)
        self.fig_diag = FigurePane(self.tab_diag, t)
        self.fig_diag.pack(fill="both", expand=True)

        self._build_sweep_tab()
        self._build_lumerical_tab()
        self._build_log_tab()

    # ---------------- parameter widgets --------------------------------
    def _build_param_widgets(self, parent):
        t = self.theme
        for group in P.GROUPS:
            specs = [s for s in P.PARAMS if s.group == group]
            box = Collapsible(parent, group, t,
                              open_=group not in ("Lumerical", "Arm imbalance"))
            box.pack(fill="x", padx=4)
            for spec in specs:
                self._add_param_row(box.body, spec)

    def _add_param_row(self, parent, spec: P.ParamSpec):
        t = self.theme
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", pady=2)

        lab = ttk.Label(row, text=spec.display, style="Muted.TLabel", width=24, anchor="w")
        lab.pack(side="left", padx=(4, 4))
        if spec.help:
            Tooltip(lab, f"{spec.label}\n\n{spec.help}", t)

        if spec.kind == "bool":
            var = tk.BooleanVar(value=bool(spec.default))
            w = ttk.Checkbutton(row, variable=var, command=self._on_change)
            w.pack(side="left")
        elif spec.kind == "choice":
            var = tk.StringVar(value=str(spec.default))
            w = ttk.Combobox(row, textvariable=var, values=list(spec.choices),
                             state="readonly", width=14)
            w.pack(side="left", fill="x", expand=True)
            w.bind("<<ComboboxSelected>>", lambda e: self._on_change())
        elif spec.kind in ("path", "dirpath"):
            var = tk.StringVar(value=str(spec.default))
            w = ttk.Entry(row, textvariable=var)
            w.pack(side="left", fill="x", expand=True)
            ttk.Button(row, text="...", width=3,
                       command=lambda s=spec, v=var: self._browse(s, v)).pack(side="left", padx=2)
        else:
            var = tk.StringVar(value=str(spec.default))
            w = ttk.Entry(row, textvariable=var, width=12)
            w.pack(side="left", fill="x", expand=True)
            w.bind("<Return>", lambda e: self._on_change())
            w.bind("<FocusOut>", lambda e: self._on_change())
        if spec.help:
            Tooltip(w, f"{spec.label}\n\n{spec.help}", t)
        self.vars[spec.key] = var

    def _browse(self, spec, var):
        if spec.kind == "dirpath":
            path = filedialog.askdirectory(title=spec.label)
        else:
            path = filedialog.askopenfilename(
                title=spec.label,
                filetypes=[("Touchstone 2-port", "*.s2p"), ("All files", "*.*")])
        if path:
            var.set(path)
            if spec.key == "s2p_path":
                if not self.vars["out_dir"].get():
                    self.vars["out_dir"].set(os.path.dirname(path))
                self.fit = None
                self.action_analyse()

    # ---------------- sweep tab ----------------------------------------
    def _build_sweep_tab(self):
        t = self.theme
        ctrl = ttk.Frame(self.tab_sweep, style="Panel.TFrame")
        ctrl.pack(fill="x", padx=8, pady=8)

        self.sweep_labels = [s.display for s in P.SWEEPABLE]
        self._sweep_by_label = {s.display: s for s in P.SWEEPABLE}

        r1 = ttk.Frame(ctrl, style="Panel.TFrame"); r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="Sweep", style="Muted.TLabel").pack(side="left", padx=(0, 6))
        self.sw_param = tk.StringVar(value=P.BY_KEY["Rt_R"].display)
        cb = ttk.Combobox(r1, textvariable=self.sw_param, values=self.sweep_labels,
                          state="readonly", width=32)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self._autofill_sweep())

        ttk.Label(r1, text="from", style="Muted.TLabel").pack(side="left", padx=(12, 4))
        self.sw_start = tk.StringVar(value="10")
        ttk.Entry(r1, textvariable=self.sw_start, width=9).pack(side="left")
        ttk.Label(r1, text="to", style="Muted.TLabel").pack(side="left", padx=4)
        self.sw_stop = tk.StringVar(value="100")
        ttk.Entry(r1, textvariable=self.sw_stop, width=9).pack(side="left")
        ttk.Label(r1, text="points", style="Muted.TLabel").pack(side="left", padx=(12, 4))
        self.sw_n = tk.StringVar(value="46")
        ttk.Entry(r1, textvariable=self.sw_n, width=6).pack(side="left")
        self.sw_log = tk.BooleanVar(value=False)
        ttk.Checkbutton(r1, text="log spacing", variable=self.sw_log).pack(side="left", padx=12)

        r2 = ttk.Frame(ctrl, style="Panel.TFrame"); r2.pack(fill="x", pady=3)
        self.sw_use_series = tk.BooleanVar(value=False)
        ttk.Checkbutton(r2, text="Second parameter (family of curves)",
                        variable=self.sw_use_series,
                        command=self._toggle_series).pack(side="left")
        self.sw_series = tk.StringVar(value=P.BY_KEY["L_target_mm"].display)
        self.cb_series = ttk.Combobox(r2, textvariable=self.sw_series,
                                      values=self.sweep_labels, state="disabled", width=28)
        self.cb_series.pack(side="left", padx=8)
        ttk.Label(r2, text="from", style="Muted.TLabel").pack(side="left", padx=(6, 4))
        self.sw_s_start = tk.StringVar(value="4")
        self.e_s_start = ttk.Entry(r2, textvariable=self.sw_s_start, width=8, state="disabled")
        self.e_s_start.pack(side="left")
        ttk.Label(r2, text="to", style="Muted.TLabel").pack(side="left", padx=4)
        self.sw_s_stop = tk.StringVar(value="12")
        self.e_s_stop = ttk.Entry(r2, textvariable=self.sw_s_stop, width=8, state="disabled")
        self.e_s_stop.pack(side="left")
        ttk.Label(r2, text="curves", style="Muted.TLabel").pack(side="left", padx=(10, 4))
        self.sw_s_n = tk.StringVar(value="5")
        self.e_s_n = ttk.Entry(r2, textvariable=self.sw_s_n, width=5, state="disabled")
        self.e_s_n.pack(side="left")

        r3 = ttk.Frame(ctrl, style="Panel.TFrame"); r3.pack(fill="x", pady=(8, 0))
        ttk.Label(r3, text="Plot", style="Muted.TLabel").pack(side="left", padx=(0, 6))
        self.metric_labels = [m.display for m in SW.METRICS]
        self._metric_by_label = {m.display: m for m in SW.METRICS}
        self.sw_metric = tk.StringVar(value=SW.METRIC_BY_KEY["bw_GHz"].display)
        mcb = ttk.Combobox(r3, textvariable=self.sw_metric, values=self.metric_labels,
                           state="readonly", width=34)
        mcb.pack(side="left")
        mcb.bind("<<ComboboxSelected>>", lambda e: self._redraw_sweep())

        ttk.Button(r3, text="Run sweep", style="Accent.TButton",
                   command=self.action_sweep).pack(side="left", padx=(16, 4))
        ttk.Button(r3, text="Stop", command=lambda: self._cancel.set()).pack(side="left", padx=2)
        ttk.Button(r3, text="Export CSV", command=self.action_export_sweep).pack(side="left", padx=(16, 2))
        ttk.Button(r3, text="Save PNG", command=self.action_save_sweep_png).pack(side="left", padx=2)

        self.fig_sweep = FigurePane(self.tab_sweep, t)
        self.fig_sweep.pack(fill="both", expand=True, padx=4, pady=4)
        self._autofill_sweep()

    def _toggle_series(self):
        state = "readonly" if self.sw_use_series.get() else "disabled"
        estate = "normal" if self.sw_use_series.get() else "disabled"
        self.cb_series.config(state=state)
        for e in (self.e_s_start, self.e_s_stop, self.e_s_n):
            e.config(state=estate)

    def _autofill_sweep(self):
        spec = self._sweep_by_label.get(self.sw_param.get())
        if spec and spec.sweep_default:
            a, b, n = spec.sweep_default
            self.sw_start.set(f"{a:g}")
            self.sw_stop.set(f"{b:g}")
            self.sw_n.set(str(int(n)))
            self.sw_log.set(bool(spec.log_sweep))

    # ---------------- INTERCONNECT tab ---------------------------------
    def _build_lumerical_tab(self):
        t = self.theme
        ctrl = ttk.Frame(self.tab_lum, style="Panel.TFrame")
        ctrl.pack(fill="x", padx=8, pady=8)
        ttk.Button(ctrl, text="Export tables only",
                   command=self.action_export_tables).pack(side="left", padx=3)
        ttk.Button(ctrl, text="Build + run in INTERCONNECT", style="Accent.TButton",
                   command=self.action_build_interconnect).pack(side="left", padx=3)
        self.lum_keep = tk.BooleanVar(value=True)
        ttk.Checkbutton(ctrl, text="Leave INTERCONNECT open afterwards",
                        variable=self.lum_keep).pack(side="left", padx=14)
        ttk.Button(ctrl, text="Close INTERCONNECT session",
                   command=self.action_close_interconnect).pack(side="left", padx=3)

        info = tk.Text(self.tab_lum, height=9, bg=t["card"], fg=t["muted"],
                       insertbackground=t["fg"], relief="flat", wrap="word",
                       font=("Segoe UI", 9), padx=10, pady=8)
        info.pack(fill="x", padx=8)
        info.insert("1.0",
            "The Python model and INTERCONNECT solve the same device two different ways.\n\n"
            "Python evaluates the closed-form traveling-wave transfer function: milliseconds "
            "per point, which is what makes the Sweep tab usable.\n\n"
            "INTERCONNECT runs the real circuit solver on a schematic you and your colleagues "
            "can open, extend and reuse -- and it is the only one of the two that will take you "
            "to eye diagrams, PAM-4/BER, fibre propagation and nested IQ structures later.\n\n"
            "Exporting writes loss.txt, z0.txt, nm.txt and sim_params.json into the working "
            "folder; the build then wires the schematic from exactly the same numbers the "
            "Python model just used, so any disagreement is a real modelling difference and "
            "not a bookkeeping one.")
        info.config(state="disabled")

        self.fig_lum = FigurePane(self.tab_lum, t)
        self.fig_lum.pack(fill="both", expand=True, padx=4, pady=4)

    # ---------------- log tab ------------------------------------------
    def _build_log_tab(self):
        t = self.theme
        self.log_text = tk.Text(self.tab_log, bg=t["card"], fg=t["fg"], relief="flat",
                                insertbackground=t["fg"], wrap="word",
                                font=("Consolas", 9), padx=10, pady=8)
        sb = ttk.Scrollbar(self.tab_log, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log_text.pack(fill="both", expand=True)
        for tag, col in (("err", t["err"]), ("ok", t["ok"]), ("warn", t["warn"])):
            self.log_text.tag_config(tag, foreground=col)

    # ---------------- status bar ---------------------------------------
    def _build_status(self):
        t = self.theme
        bar = tk.Frame(self, bg=t["panel"])
        bar.pack(fill="x", side="bottom")
        self.status = tk.Label(bar, text="ready", bg=t["panel"], fg=t["muted"],
                               anchor="w", font=("Segoe UI", 8), padx=12, pady=5)
        self.status.pack(side="left", fill="x", expand=True)
        self.progress = ttk.Progressbar(bar, mode="determinate", length=260)
        self.progress.pack(side="right", padx=12, pady=5)

    # =================================================================
    # parameter I/O
    # =================================================================
    def _get_params(self) -> dict:
        raw = {}
        for k, v in self.vars.items():
            raw[k] = v.get()
        return P.normalise(raw)

    def _set_params(self, params: dict):
        for k, v in params.items():
            if k in self.vars:
                if isinstance(self.vars[k], tk.BooleanVar):
                    self.vars[k].set(bool(v))
                else:
                    self.vars[k].set(str(v))

    # =================================================================
    # background worker plumbing
    # =================================================================
    def log(self, msg, tag=None):
        self._q.put(("log", (str(msg), tag)))

    def _write_log(self, msg, tag=None):
        try:
            self.log_text.insert("end", msg + "\n", tag or ())
            self.log_text.see("end")
        except tk.TclError:
            pass

    def _dispatch(self, kind, payload):
        if kind == "log":
            msg, tag = payload
            self._write_log(msg, tag)
        elif kind == "status":
            self.status.config(text=payload)
        elif kind == "progress":
            done, total = payload
            self.progress["maximum"] = max(total, 1)
            self.progress["value"] = done
        elif kind == "call":
            payload()
        elif kind == "banner":
            self.show_banner(payload)

    def _pump(self):
        """
        Drain the worker queue.

        Every step is defended, and the next tick is scheduled in a finally
        block, because a single exception escaping here used to kill the
        rescheduling chain for good: after that no log line, status update,
        figure or error ever reached the window again and the application
        looked frozen while its widgets were still technically alive.
        """
        if self._closing:
            return
        try:
            while True:
                try:
                    kind, payload = self._q.get_nowait()
                except queue.Empty:
                    break
                try:
                    self._dispatch(kind, payload)
                except Exception:
                    self._write_log("UI update failed (the interface stays "
                                    "usable):\n" + traceback.format_exc(), "err")
        except Exception:
            try:
                self._write_log("pump error:\n" + traceback.format_exc(), "err")
            except Exception:
                pass
        finally:
            if not self._closing:
                try:
                    self.after(80, self._pump)
                except tk.TclError:
                    pass

    def _set_status(self, msg):
        self._q.put(("status", msg))

    def _ui(self, fn):
        self._q.put(("call", fn))

    def _run_async(self, work: Callable, name: str):
        if self._busy:
            self.log("busy -- wait for the current job to finish", "warn")
            return
        self._busy = True
        self._cancel.clear()
        self.hide_banner()
        self._set_status(f"{name}...")

        def runner():
            try:
                work()
                self._set_status(f"{name}: done")
            except Exception as exc:
                self.log(f"[{name}] {type(exc).__name__}: {exc}", "err")
                self.log(traceback.format_exc(), "err")
                self._set_status(f"{name}: failed -- see the Log tab")
                self._q.put(("banner", f"{name} failed -- {type(exc).__name__}: {exc}"))
            finally:
                self._busy = False
                self._q.put(("progress", (0, 1)))

        threading.Thread(target=runner, daemon=True).start()

    # =================================================================
    # actions
    # =================================================================
    def _on_change(self):
        if self.auto_var.get() and self.fit is not None and not self._busy:
            self.action_analyse()

    def action_analyse(self):
        p = self._get_params()
        if not p["s2p_path"] or not os.path.isfile(str(p["s2p_path"])):
            self._set_status("pick a Touchstone (.s2p) file first")
            return

        def work():
            fit = SW.get_fit(p)
            self.fit = fit
            self.log(f"Fitted {fit.source_file}: data {fit.f_min_sim_GHz:.2f}-"
                     f"{fit.f_max_sim_GHz:.2f} GHz, L_meas = {fit.L_meas_m*1e3:.2f} mm")
            res = eo_response(fit, p)
            lm = link_metrics(p)
            self.result = res
            if res.bw_clipped:
                self.log(f"EO S21 never reaches {p['bw_level_dB']:.0f} dB below "
                         f"{p['f_max_GHz']:.0f} GHz -- reported bandwidth is a lower bound.",
                         "warn")
            else:
                self.log(f"EO bandwidth = {res.bw_GHz:.2f} GHz "
                         f"({p['bw_level_dB']:.0f} dB), V_pi,eff = {lm.vpi_eff_V:.2f} V, "
                         f"chirp = {lm.chirp_alpha:.3f}", "ok")
            for w in extraction_warnings(fit, res):
                self.log("NOTE: " + w, "warn")

            spread = bandwidth_spread(fit, p)
            sub = "GHz"
            if spread:
                self.log(f"Bandwidth across every defensible fit of the same data: "
                         f"{spread['min']:.0f} - {spread['max']:.0f} GHz "
                         f"(median {spread['median']:.0f}).")
                for lbl, v in spread["rows"]:
                    self.log(f"    {lbl:46s} {v:7.2f} GHz")
                if spread["max"] - spread["min"] > 0.1 * max(spread["median"], 1e-9):
                    self.log("    The spread is the honest uncertainty: outside the measured "
                             "band the number is set by the fitting form, not by the data.",
                             "warn")
                    sub = f"GHz   (fit spread {spread['min']:.0f}-{spread['max']:.0f})"
            self._ui(lambda: self.kpi.set_unit("bw", sub))

            fig_theme = self.theme["fig"]
            f_eo = eo_figure(fit, res, p, fig_theme, lumerical=self.lumerical_overlay)
            f_dg = diagnostic_figure(fit, p, fig_theme)
            self._ui(lambda: (self.kpi.update_values(res, lm, res.bw_clipped),
                              self.fig_response.show(f_eo),
                              self.fig_diag.show(f_dg)))

        self._run_async(work, "analyse")

    def action_sweep(self):
        p = self._get_params()
        if not p["s2p_path"] or not os.path.isfile(str(p["s2p_path"])):
            self._set_status("pick a Touchstone (.s2p) file first")
            return
        spec = self._sweep_by_label.get(self.sw_param.get())
        if spec is None:
            return
        try:
            values = SW.make_values(float(self.sw_start.get()), float(self.sw_stop.get()),
                                    int(float(self.sw_n.get())), self.sw_log.get())
        except ValueError as exc:
            messagebox.showerror("Sweep range", str(exc))
            return

        series_key = series_values = None
        if self.sw_use_series.get():
            sspec = self._sweep_by_label.get(self.sw_series.get())
            if sspec is not None and sspec.key != spec.key:
                series_key = sspec.key
                series_values = SW.make_values(float(self.sw_s_start.get()),
                                               float(self.sw_s_stop.get()),
                                               int(float(self.sw_s_n.get())))
            elif sspec is not None:
                self.log("The second parameter must differ from the swept one; ignoring it.",
                         "warn")

        def work():
            n_total = len(values) * (len(series_values) if series_values is not None else 1)
            self.log(f"Sweeping {spec.label}: {len(values)} points"
                     + (f" x {len(series_values)} curves of {P.BY_KEY[series_key].label}"
                        if series_key else "")
                     + f"  ({n_total} evaluations)")

            def prog(done, total, msg):
                self._q.put(("progress", (done, total)))
                if "failed" in msg or "cancel" in msg:
                    self.log(f"  {msg}", "warn")

            r = SW.run_sweep(p, spec.key, values, series_key, series_values,
                             progress=prog, cancel=self._cancel.is_set)
            self.sweep_result = r
            y = r.metrics["bw_GHz"]
            finite = y[np.isfinite(y)]
            if finite.size:
                self.log(f"  EO bandwidth over the sweep: {finite.min():.2f} - "
                         f"{finite.max():.2f} GHz", "ok")
            if r.clipped.any():
                self.log(f"  {int(r.clipped.sum())} point(s) never crossed the criterion "
                         f"inside {p['f_max_GHz']:.0f} GHz -- shown as open triangles; "
                         f"raise 'Sweep ceiling' to resolve them.", "warn")
            self._ui(self._redraw_sweep)

        self._run_async(work, "sweep")

    def _redraw_sweep(self):
        if self.sweep_result is None:
            return
        mspec = self._metric_by_label.get(self.sw_metric.get())
        key = mspec.key if mspec else "bw_GHz"
        fig = SW.sweep_figure(self.sweep_result, key, self.theme["fig"])
        self.fig_sweep.show(fig)
        self.nb.select(self.tab_sweep)

    def action_export_sweep(self):
        if self.sweep_result is None:
            messagebox.showinfo("Export", "Run a sweep first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")],
                                            initialfile="mzm_sweep.csv")
        if path:
            self.sweep_result.to_csv(path)
            self.log(f"Sweep written to {path}", "ok")

    def action_save_sweep_png(self):
        if self.fig_sweep.figure is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG", "*.png")],
                                            initialfile="mzm_sweep.png")
        if path:
            self.fig_sweep.figure.savefig(path, dpi=200,
                                          facecolor=self.fig_sweep.figure.get_facecolor())
            self.log(f"Figure written to {path}", "ok")

    def _resolve_out_dir(self, p) -> str:
        out = str(p["out_dir"]).strip() or os.path.dirname(str(p["s2p_path"]))
        os.makedirs(out, exist_ok=True)
        return out

    def action_export_touchstone(self):
        p = self._get_params()
        if self.result is None or self.fit is None:
            self.log("Run 'Extract + analyse' first.", "warn")
            return
        stem = os.path.splitext(os.path.basename(str(p["s2p_path"])))[0]
        path = filedialog.asksaveasfilename(
            defaultextension=".s2p", initialdir=self._resolve_out_dir(p),
            initialfile=f"{stem}_L{float(p['L_target_mm']):g}mm_Rt{float(p['Rt_R']):g}.s2p",
            filetypes=[("Touchstone", "*.s2p"), ("All files", "*.*")])
        if not path:
            return

        def work():
            info = export_touchstone(self.fit, self.result, p, path)
            self.log(f"Touchstone written to {path}", "ok")
            self.log(f"  {info['points']} points, {info['format']} format, {info['ports']}, "
                     f"EO magnitude {'normalised' if info['normalised'] else 'raw'}.")
            if info["ports"] == "4-column":
                self.log("  4 data columns is not a valid 2-port .s2p -- fine for numpy, "
                         "Excel or MATLAB, but set 'Touchstone columns' to 'full 2-port' "
                         "for scikit-rf, ADS or CST.", "warn")
        self._run_async(work, "Touchstone export")

    def action_export_tables(self):
        p = self._get_params()
        if self.result is None or self.fit is None:
            self.log("Run 'Extract + analyse' first.", "warn")
            return

        def work():
            out = self._resolve_out_dir(p)
            paths = export_lumerical_tables(self.fit, p, self.result, out)
            self.log(f"Tables written to {out} "
                     f"(up to {paths['table_f_max_GHz']:.1f} GHz, {paths['n_points']} pts"
                     + (f"; data ends at {paths['f_measured_max_GHz']:.1f} GHz, "
                        f"above that the tables are the fitted model"
                        if paths["extrapolated"] else "")
                     + ")", "ok")
        self._run_async(work, "export")

    def action_build_interconnect(self):
        p = self._get_params()
        if self.result is None or self.fit is None:
            self.log("Run 'Extract + analyse' first.", "warn")
            return

        def work():
            from .interconnect import InterconnectBuilder
            out = self._resolve_out_dir(p)
            files = export_lumerical_tables(self.fit, p, self.result, out)
            self.log(f"Tables exported to {out}")
            # Close a previous session before opening another, otherwise each
            # build leaks an INTERCONNECT process.
            if self.ic_builder is not None:
                try:
                    self.ic_builder.close()
                except Exception:
                    pass
                self.ic_builder = None
            b = InterconnectBuilder(str(p["lumapi_path"]), hide=bool(p["ic_hide"]),
                                    log=lambda m: self.log(m))
            self.ic_builder = b            # keeps the process alive
            topo = b.build(p, files)
            self.log(f"Schematic built ({topo}).")
            b.run(os.path.join(out, "TWMZM_EO_response.icp"))
            # Same reference window the closed-form curve used -- without this
            # the two are normalised differently and the bandwidths disagree
            # even though the underlying physics is identical.
            f_GHz, s_dB, bw = b.ena_trace(p, norm_window=self.result.norm_window_GHz)
            self.lumerical_overlay = (f_GHz, s_dB, bw)
            py = self.result.bw_GHz
            self.log(f"Python  {py:.2f} GHz  |  INTERCONNECT  {bw:.2f} GHz  |  "
                     f"difference {abs(py-bw):.2f} GHz "
                     f"({abs(py-bw)/max(py,1e-9)*100:.1f} %)",
                     "ok" if abs(py - bw) < 0.05 * max(py, 1e-9) else "warn")
            fig = eo_figure(self.fit, self.result, p, self.theme["fig"],
                            lumerical=self.lumerical_overlay)
            fig2 = eo_figure(self.fit, self.result, p, self.theme["fig"],
                             lumerical=self.lumerical_overlay)
            self._ui(lambda: (self.fig_lum.show(fig), self.fig_response.show(fig2),
                              self.nb.select(self.tab_lum)))
            if self.lum_keep.get():
                self.log("  INTERCONNECT is left open. Use 'Close INTERCONNECT "
                         "session' when you are done with it, or it closes with "
                         "this window.")
            else:
                b.close()
                self.ic_builder = None
        self._run_async(work, "INTERCONNECT")

    def action_close_interconnect(self):
        if self.ic_builder is None:
            self.log("No INTERCONNECT session is open.", "warn")
            return
        try:
            self.ic_builder.close()
            self.log("INTERCONNECT session closed.", "ok")
        except Exception as exc:
            self.log(f"Could not close the session cleanly: {exc}", "warn")
        finally:
            self.ic_builder = None

    # ---------------- session save/load ---------------------------------
    def action_save_session(self):
        import json
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON", "*.json")],
                                            initialfile="mzm_session.json")
        if not path:
            return
        with open(path, "w") as fh:
            json.dump({k: v.get() for k, v in self.vars.items()}, fh, indent=2)
        self.log(f"Session saved to {path}", "ok")

    def action_load_session(self):
        import json
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        with open(path) as fh:
            self._set_params(json.load(fh))
        self.fit = None
        self.log(f"Session loaded from {path}", "ok")
        self.action_analyse()

    def action_toggle_theme(self):
        # Tearing the root down from inside a callback while the pump's own
        # after() is still pending leaves Tk trying to run a command that no
        # longer exists ("invalid command name ..._pump"). Stop the chain and
        # hand the Lumerical session over before destroying anything.
        params = {k: v.get() for k, v in self.vars.items()}
        new_theme = "light" if self.theme_name == "dark" else "dark"
        builder = self.ic_builder
        self.ic_builder = None
        self._closing = True
        self.after(1, lambda: self._restart(new_theme, params, builder))

    def _restart(self, theme_name, params, builder):
        try:
            self.destroy()
        except tk.TclError:
            pass
        app = MZMStudio(theme_name=theme_name, initial=params)
        app.ic_builder = builder
        app.mainloop()


def launch(initial: Optional[dict] = None, theme: str = "dark"):
    app = MZMStudio(theme_name=theme, initial=initial)
    app.mainloop()
