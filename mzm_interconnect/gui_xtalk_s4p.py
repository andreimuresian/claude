"""
The Crosstalk-from-s4p window: a coupled pair (A aggressor, driven; B victim,
idle) taken straight from its 4-port Touchstone file, at the simulated length.
Separate from the 200 um pitch window (gui_xtalk.py), which has its own
dataset and length extrapolation.

  * Load the .s4p, give its length and port order. xtalk_s4p.py splits it into
    even and odd 2-ports and turns each into an equivalent uniform line.
  * Compute: electrical NEXT / FEXT (the file itself, at its reference), the
    victim voltages with the sidebar's source and termination, the voltage the
    light integrates on each line, and the EO crosstalk B/A, for both
    equivalent lines ('exact terminals' and 'Ze = Zo (forward waves)'; see
    xtalk_s4p.py for why they differ).
  * Export tables / full cascade: as in the 200 um window, on the chosen
    equivalent line.
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, ttk

import numpy as np
from matplotlib.figure import Figure

from . import parameters as P
from .gui_xtalk import AGG_C, BAND_C, FE_C, MARK_GHZ, VIC_C, XtalkWindow, _db


class XtalkS4PWindow(XtalkWindow):

    def __init__(self, app):                       # noqa: C901 (layout code)
        tk.Toplevel.__init__(self, app)
        import queue
        from .gui import Collapsible, FigurePane, ScrollFrame, Tooltip
        self._Tooltip = Tooltip
        self.app = app
        t = self.theme = app.theme
        self.title("Crosstalk from s4p  --  coupled pair at its simulated length")
        self.geometry("1450x900")
        self.minsize(1050, 680)
        self.configure(bg=t["bg"])
        self._q = queue.Queue()
        self._closing = False
        self._busy = None
        self.result = None

        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=10, pady=8)
        left = ttk.Frame(pane, style="Panel.TFrame", width=480)
        pane.add(left, weight=0)
        right = ttk.Frame(pane, style="Bg.TFrame")
        pane.add(right, weight=1)
        sf = ScrollFrame(left, t)
        sf.pack(fill="both", expand=True)
        body = sf.inner
        self._wrapped = []
        left.bind("<Configure>", self._rewrap, add="+")

        def muted(parent, text):
            lab = ttk.Label(parent, text=text, style="Muted.TLabel", wraplength=400, justify="left")
            lab.pack(fill="x", padx=4, pady=(2, 4))
            self._wrapped.append(lab)
            return lab

        # ---- the pair -------------------------------------------------------
        box = Collapsible(body, "Pair (4-port Touchstone)", t)
        box.pack(fill="x", padx=4)
        muted(box.body, "The pair as simulated: no length extrapolation. The length must be "
                        "the simulated one; it is also the device length.")
        row = ttk.Frame(box.body, style="Panel.TFrame")
        row.pack(fill="x", pady=2)
        ttk.Entry(row, textvariable=app.vars["xs_s4p_path"]).pack(side="left", fill="x",
                                                                  expand=True, padx=(4, 4))
        ttk.Button(row, text="Browse", command=self._browse).pack(side="left")
        self._entry_row(box.body, app.vars["xs_L_mm"], P.BY_KEY["xs_L_mm"].display,
                        P.BY_KEY["xs_L_mm"].help)
        for key in ("xs_port_order", "xs_variant"):
            row = ttk.Frame(box.body, style="Panel.TFrame")
            row.pack(fill="x", pady=2)
            lab = ttk.Label(row, text=P.BY_KEY[key].label, style="Muted.TLabel", width=24,
                            anchor="w")
            lab.pack(side="left", padx=(4, 4))
            cb = ttk.Combobox(row, textvariable=app.vars[key], state="readonly",
                              values=P.BY_KEY[key].choices)
            cb.pack(side="left", fill="x", expand=True)
            if P.BY_KEY[key].help:
                Tooltip(lab, P.BY_KEY[key].help, t)
                Tooltip(cb, P.BY_KEY[key].help, t)
        muted(box.body, "Both equivalent lines are plotted. 'Exact terminals' gives the file "
                        "back exactly, NEXT included, but turns a NEXT that is not two-mode "
                        "physics into an impedance split that can overstate the EO crosstalk "
                        "by ~20 dB. 'Ze = Zo' (default) is closer, but not exact either: "
                        "against EO crosstalk computed from CST's own gap fields (Istanbul "
                        "5 mm) it is off by -7..+12 dB between 10 and 80 GHz (e.g. 4 dB high at "
                        "30 GHz, 6.7 dB low at 45 GHz). Read it as an estimate only. The "
                        "choice sets what the tables and "
                        "INTERCONNECT use.")

        # ---- circuit (from the sidebar) ------------------------------------
        box = Collapsible(body, "Circuit (from the main window)", t)
        box.pack(fill="x", padx=4)
        self.dev_lbl = ttk.Label(box.body, text="", style="Muted.TLabel", wraplength=400,
                                 justify="left", font=("Consolas", 9))
        self.dev_lbl.pack(fill="x", padx=4, pady=(0, 6))
        self._wrapped.append(self.dev_lbl)

        # ---- actions --------------------------------------------------------
        box = Collapsible(body, "Run", t)
        box.pack(fill="x", padx=4)
        ttk.Button(box.body, text="Compute (Python twin)", style="Accent.TButton",
                   command=self.action_compute).pack(fill="x", padx=4, pady=2)
        ttk.Button(box.body, text="Export tables for INTERCONNECT",
                   command=self.action_export).pack(fill="x", padx=4, pady=2)
        ttk.Button(box.body, text="Full MZM cascade in INTERCONNECT: ENA + check",
                   command=lambda: self.action_cascade("ena")).pack(fill="x", padx=4, pady=2)
        ttk.Button(box.body, text="Full MZM cascade in INTERCONNECT: eyes",
                   command=lambda: self.action_cascade("eye")).pack(fill="x", padx=4, pady=2)
        muted(box.body, "Full cascade: modulators A and B (the sidebar's optics, bias, drive "
                        "and source/load) on the coupled electrode of this file. ENA input 1 "
                        "= A's EO response, input 2 = B's; their ratio is checked against the "
                        "twin. Eyes: EYE_1 = A, EYE_2 = what reaches B with its driver idle. "
                        "Tables above the file's top frequency hold the last values.")

        # ---- numbers --------------------------------------------------------
        box = Collapsible(body, "Extraction and numbers", t)
        box.pack(fill="x", padx=4)
        tf = ttk.Frame(box.body, style="Panel.TFrame")
        tf.pack(fill="x", padx=4, pady=(0, 6))
        self.num_txt = tk.Text(tf, height=18, bg=t["card"], fg=t["fg"], relief="flat",
                               font=("Consolas", 8), wrap="none")
        xs = ttk.Scrollbar(tf, orient="horizontal", command=self.num_txt.xview)
        self.num_txt.configure(xscrollcommand=xs.set)
        self.num_txt.pack(fill="x")
        xs.pack(fill="x")

        st = tk.Frame(self, bg=t["bg"])
        st.pack(fill="x", padx=10, pady=(0, 8))
        self.status = tk.Label(st, text="", bg=t["bg"], fg=t["muted"], anchor="w",
                               font=("Segoe UI", 9))
        self.status.pack(side="left", fill="x", expand=True)
        self.fig = FigurePane(right, t)
        self.fig.pack(fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(80, self._pump)
        self._show_device()
        if str(app.vars["xs_s4p_path"].get()).strip():
            self.action_compute()
        else:
            self.status.config(text="choose the pair's .s4p file, then Compute")

    # ------------------------------------------------------------------ widgets
    def _browse(self):
        path = filedialog.askopenfilename(
            parent=self, filetypes=[("Touchstone 4-port", "*.s4p"), ("All files", "*.*")])
        if path:
            self.app.vars["xs_s4p_path"].set(path)

    def _out_dir(self, p) -> str:
        out = str(p["out_dir"]).strip() or os.path.join(os.getcwd(), "crosstalk_s4p")
        os.makedirs(out, exist_ok=True)
        return os.path.abspath(out)

    def close(self):
        self._closing = True
        try:
            self.app.xtalk_s4p_window = None
        except Exception:
            pass
        self.destroy()

    # ------------------------------------------------------------------ actions
    def action_compute(self):
        self._show_device()
        p = self.app._get_params()

        def work():
            from .xtalk_s4p import device_crosstalk_s4p, pair_from_params
            pair = pair_from_params(p)
            return dict(p=p, d=device_crosstalk_s4p(p, pair))
        self._run("Compute", work, self._show_result)

    def action_export(self):
        p = self.app._get_params()

        def work():
            from .xtalk_s4p import export_tables
            r = export_tables(p, self._out_dir(p))
            self.app.log(f"Crosstalk tables ({r['name']}, {r['variant']}) written: {r['even']}, "
                         f"{r['odd']} (up to {r['table_top_GHz']:.1f} GHz; data to "
                         f"{r['data_top_GHz']:.0f} GHz)", "ok")
            return r
        self._run("Export tables", work,
                  lambda r: self.status.config(text=f"tables in {os.path.dirname(r['even'])}"))

    def action_cascade(self, mode: str):
        p = self.app._get_params()
        app = self.app

        def work():
            from .xtalk_cascade import run_xtalk_cascade
            if app.ic_builder is not None:          # one INTERCONNECT session at a time
                try:
                    app.ic_builder.close()
                except Exception:
                    pass
                app.ic_builder = None
            out = os.path.join(self._out_dir(p), "xtalk_cascade_s4p")
            app.log(f"Crosstalk from s4p, full cascade ({mode}): files in {out}")
            keep = bool(app.lum_keep.get()) or mode == "eye"
            rep, b = run_xtalk_cascade(p, out_dir=out, mode=mode, log=lambda m: app.log(m),
                                       keep_open=keep, source="s4p")
            app.ic_builder = b
            return rep
        self._run(f"Full cascade ({mode})", work, lambda rep: (
            self.num_txt.delete("1.0", "end"), self.num_txt.insert("1.0", rep)))

    # ------------------------------------------------------------------ display
    def _show_result(self, res):
        from .xtalk_s4p import VARIANTS, summary
        self.result = res
        d, p = res["d"], res["p"]
        f = d["f_GHz"]
        eq, full = d["eq"], d["full"]
        chosen_eq = str(p["xs_variant"]) == VARIANTS[0]
        th = self.theme["fig"]
        F = Figure(figsize=(10, 7), dpi=100, facecolor=th["bg"])
        axs = F.subplots(2, 2, sharex=True)
        lw = lambda is_eq: 1.9 if is_eq == chosen_eq else 1.0

        a = axs[0, 0]
        sf = d["s_file"]
        a.plot(f, _db(sf[:, 2, 0]), color=BAND_C, lw=1.8, label="NEXT  |S(B1,A1)|, file")
        a.plot(f, _db(sf[:, 3, 0]), color=FE_C, lw=1.8, label="FEXT  |S(B2,A1)|, file")
        a.plot(f, _db(eq["block"]["S"][2][0]), ":", color=BAND_C, lw=1.2, label="NEXT, Ze = Zo")
        a.plot(f, _db(eq["block"]["S"][3][0]), ":", color=FE_C, lw=1.2, label="FEXT, Ze = Zo")
        a.set_title(f"Electrical crosstalk, all ports {d['pair']['z0']:g} ohm (the file)")
        a.set_ylabel("dB")

        a = axs[0, 1]
        for blk, ls, is_eq, tag in ((full, "-", False, "exact terminals"),
                                    (eq, "--", True, "Ze = Zo")):
            r = blk["resp"]
            a.plot(f, _db(r["NE_B"] / r["V"][0]), ls, color=BAND_C, lw=lw(is_eq),
                   label=f"near end B / V(A1), {tag}")
            a.plot(f, _db(r["FE_B"] / r["V"][0]), ls, color=FE_C, lw=lw(is_eq),
                   label=f"far end B / V(A1), {tag}")
        a.set_title("Victim voltages (device source / load)")
        a.set_ylabel("dB re aggressor input voltage")

        a = axs[1, 0]
        h0 = np.abs(full["resp"]["H_A"][0])
        a.plot(f, _db(full["resp"]["H_A"] / h0), color=AGG_C, lw=1.6, label="aggressor A")
        a.plot(f, _db(full["resp"]["H_B"] / h0), "-", color=VIC_C, lw=lw(False),
               label="victim B, exact terminals")
        a.plot(f, _db(eq["resp"]["H_B"] / h0), "--", color=VIC_C, lw=lw(True),
               label="victim B, Ze = Zo")
        a.set_title("Voltage the light integrates (device source / load)")
        a.set_ylabel("dB re aggressor at low f")

        a = axs[1, 1]
        a.plot(f, _db(full["resp"]["H_B"] / full["resp"]["H_A"]), "-", color=VIC_C,
               lw=lw(False), label="exact terminals")
        a.plot(f, _db(eq["resp"]["H_B"] / eq["resp"]["H_A"]), "--", color=VIC_C, lw=lw(True),
               label="Ze = Zo (forward waves)")
        a.set_title("EO crosstalk: victim / aggressor modulation")
        a.set_ylabel("dB")

        for ax in axs.flat:
            ax.set_facecolor(th["axes"])
            for s in ax.spines.values():
                s.set_color(th["grid"])
            ax.tick_params(colors=th["fg"], labelsize=8)
            ax.yaxis.label.set_color(th["fg"])
            ax.xaxis.label.set_color(th["fg"])
            ax.title.set_color(th["fg"])
            ax.title.set_fontsize(9)
            ax.grid(alpha=0.25, color=th["grid"])
            leg = ax.legend(fontsize=7, loc="lower right", facecolor=th["axes"],
                            edgecolor=th["grid"])
            for txt in leg.get_texts():
                txt.set_color(th["fg"])
        for ax in axs[1]:
            ax.set_xlabel("frequency (GHz)")
        F.suptitle(f"{d['pair']['name']},  L = {d['L']*1e3:.2f} mm  (as simulated; "
                   f"thick lines: {p['xs_variant']})", color=th["fg"], fontsize=10)
        F.tight_layout()
        self.fig.show(F)

        rows = summary(d["pair"]) + [""]
        rows.append(f"{'GHz':>3s} {'NEXT dB':>8s} {'FEXT dB':>8s} {'EO B/A, Ze=Zo':>14s} "
                    f"{'EO B/A, exact':>14s}")
        for g in MARK_GHZ:
            if g > f[-1] + 1e-9:
                continue
            q = int(np.argmin(np.abs(f - g)))
            rows.append(f"{f[q]:3.0f} {_db(sf[q, 2, 0]):8.1f} {_db(sf[q, 3, 0]):8.1f} "
                        f"{_db(eq['resp']['H_B'][q] / eq['resp']['H_A'][q]):14.1f} "
                        f"{_db(full['resp']['H_B'][q] / full['resp']['H_A'][q]):14.1f}")
        rows += ["", "NEXT/FEXT: the file (4-port at its reference).",
                 "EO: with the device's source and load."]
        self.num_txt.delete("1.0", "end")
        self.num_txt.insert("1.0", "\n".join(rows))
