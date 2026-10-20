"""
The Crosstalk window: two identical adjacent electrodes, A (aggressor, driven)
and B (victim, idle), modelled as one coupled line.

How it works
  * The crosstalk model knows ONE line: the 200 um pitch, uniform (non
    slow-wave) GSG line, from its own CST crosstalk simulations
    (data/xtalk_200um): the line from the 3-D pair runs (even/odd average),
    the even/odd split from the 2-D port modes. The sidebar Touchstone file
    and 'Extract + analyse' are not used, and the single-line model is not
    touched.
  * From the sidebar it takes only circuit settings: n_g, source and
    termination. The length is its own (xt_L_mm).
  * "Compute" runs the Python twin (coupled_line.py): electrical NEXT and FEXT
    at 50 ohm (as a VNA would measure the pair), and, with the device's own
    source and termination, the voltage the light integrates on each line.
    The band is the impedance split Ze/Zo - 1 = 0.30-0.45 %.
  * "Export tables" writes coupled_even.txt / coupled_odd.txt (0.45 %) for the
    "Coupled TL" scripted element.
  * "INTERCONNECT check" builds the element in INTERCONNECT and compares it,
    number by number, with the twin (xtalk_test.py).
"""
from __future__ import annotations

import os
import queue
import threading
import traceback

import numpy as np
import tkinter as tk
from matplotlib.figure import Figure
from tkinter import ttk

from . import parameters as P

BAND_C, AGG_C, VIC_C, FE_C = "#4f9cf9", "#8a93a5", "#e2504a", "#d99b2e"
MARK_GHZ = (10.0, 30.0, 60.0)


def _db(x):
    return 20 * np.log10(np.abs(x) + 1e-30)


class XtalkWindow(tk.Toplevel):

    def __init__(self, app):
        super().__init__(app)
        from .gui import Collapsible, FigurePane, ScrollFrame, Tooltip
        self._Tooltip = Tooltip
        self.app = app
        t = self.theme = app.theme
        self.title("Crosstalk  --  two adjacent electrodes (coupled line)")
        self.geometry("1450x900")
        self.minsize(1050, 680)
        self.configure(bg=t["bg"])
        self._q: queue.Queue = queue.Queue()
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

        def muted(parent, text):
            lab = ttk.Label(parent, text=text, style="Muted.TLabel", wraplength=400, justify="left")
            lab.pack(fill="x", padx=4, pady=(2, 4))
            return lab

        # ---- the line: fixed dataset -------------------------------------
        from .coupled_line import load_dataset
        self.ds = load_dataset()
        box = Collapsible(body, "Line (fixed: 200 um pitch uniform line)", t)
        box.pack(fill="x", padx=4)
        muted(box.body, "Crosstalk is modelled for this line only, from its own CST crosstalk "
                        "simulations. The sidebar Touchstone file is not used.")
        ds = self.ds
        tk.Label(box.body, bg=t["panel"], fg=t["fg"], justify="left", anchor="w",
                 font=("Consolas", 8), wraplength=400, text=(
                     f"{ds['name']}\n"
                     f"line   {ds['sources']['line']}\n"
                     f"split  {ds['sources']['split']}\n"
                     f"Ze/Zo - 1 = {ds['dz_lo']*100:.2f} .. {ds['dz_hi']*100:.2f} %\n"
                     f"data to {ds['data_top_GHz']:.0f} GHz; INTERCONNECT tables above it use the "
                     f"single-line fit forms")).pack(fill="x", padx=4, pady=(0, 6))
        self._entry_row(box.body, app.vars["xt_L_mm"], P.BY_KEY["xt_L_mm"].display,
                        P.BY_KEY["xt_L_mm"].help)

        # ---- circuit (from the sidebar) ------------------------------------
        box = Collapsible(body, "Circuit (from the main window)", t)
        box.pack(fill="x", padx=4)
        self.dev_lbl = ttk.Label(box.body, text="", style="Muted.TLabel", wraplength=400,
                                 justify="left", font=("Consolas", 9))
        self.dev_lbl.pack(fill="x", padx=4, pady=(0, 6))

        # ---- actions --------------------------------------------------------
        box = Collapsible(body, "Run", t)
        box.pack(fill="x", padx=4)
        ttk.Button(box.body, text="Compute (Python twin)", style="Accent.TButton",
                   command=self.action_compute).pack(fill="x", padx=4, pady=2)
        ttk.Button(box.body, text="Export tables for INTERCONNECT",
                   command=self.action_export).pack(fill="x", padx=4, pady=2)
        ttk.Button(box.body, text="INTERCONNECT check: element vs twin",
                   command=self.action_ic_check).pack(fill="x", padx=4, pady=2)
        muted(box.body, "The element: lumerical/coupled_element_setup.lsf (made by the check, or "
                        "by hand with lumerical/create_coupled_element.lsf). Ports A1, A2, B1, B2; "
                        "outputs 'modulation A/B', optionally 'far end A/B' and 'near end A/B'. "
                        "Tables and INTERCONNECT use Ze/Zo - 1 = 0.45 % (the worse case).")

        # ---- numbers --------------------------------------------------------
        box = Collapsible(body, "At 10 / 30 / 60 GHz", t)
        box.pack(fill="x", padx=4)
        self.num_txt = tk.Text(box.body, height=7, bg=t["card"], fg=t["fg"], relief="flat",
                               font=("Consolas", 8), wrap="none")
        self.num_txt.pack(fill="x", padx=4, pady=(0, 6))

        # ---- status + figure ------------------------------------------------
        st = tk.Frame(self, bg=t["bg"])
        st.pack(fill="x", padx=10, pady=(0, 8))
        self.status = tk.Label(st, text="", bg=t["bg"], fg=t["muted"], anchor="w",
                               font=("Segoe UI", 9))
        self.status.pack(side="left", fill="x", expand=True)
        self.fig = FigurePane(right, t)
        self.fig.pack(fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(80, self._pump)
        self.action_compute()

    # ------------------------------------------------------------------ widgets
    def _entry_row(self, parent, var, label, tip=""):
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", pady=2)
        lab = ttk.Label(row, text=label, style="Muted.TLabel", width=24, anchor="w")
        lab.pack(side="left", padx=(4, 4))
        e = ttk.Entry(row, textvariable=var, width=12)
        e.pack(side="left", fill="x", expand=True)
        if tip:
            self._Tooltip(lab, tip, self.theme)
            self._Tooltip(e, tip, self.theme)
        return e

    def _show_device(self):
        p = self.app._get_params()
        self.dev_lbl.config(text=(
            f"n_g      {float(p['ng']):.4f}\n"
            f"source   {float(p['Zs_R']):.1f} ohm, {float(p['Zs_L_pH']):.0f} pH, "
            f"{float(p['Zs_C_fF']):.0f} fF\n"
            f"load     {float(p['Rt_R']):.1f} ohm, {float(p['Rt_L_pH']):.0f} pH, "
            f"{float(p['Rt_C_fF']):.0f} fF\n"
            f"victim input ends in its own idle source"))

    # ------------------------------------------------------------------ plumbing
    def close(self):
        self._closing = True
        try:
            self.app.xtalk_window = None
        except Exception:
            pass
        self.destroy()

    def _post(self, kind, payload=None):
        self._q.put((kind, payload))

    def _pump(self):
        if self._closing:
            return
        try:
            while True:
                try:
                    kind, payload = self._q.get_nowait()
                except queue.Empty:
                    break
                try:
                    if kind == "status":
                        self.status.config(text=payload)
                    elif kind == "call":
                        payload()
                except Exception:
                    self.status.config(text="display error: "
                                       + traceback.format_exc().splitlines()[-1])
        finally:
            if not self._closing:
                try:
                    self.after(80, self._pump)
                except tk.TclError:
                    pass

    def _run(self, name, work, done=None):
        """work() on a thread, done(result) on the UI thread."""
        if self._busy:
            self.status.config(text=f"busy: {self._busy}")
            return
        self._busy = name
        self.status.config(text=f"{name}...")

        def runner():
            try:
                res = work()
                if done is not None:
                    self._post("call", lambda: done(res))
                self._post("status", f"{name}: done")
            except Exception as exc:
                msg = str(exc) or type(exc).__name__
                self._post("status", f"{name}: {msg}")
                self.app.log(f"[Crosstalk window: {name}] {type(exc).__name__}: {exc}\n"
                             + traceback.format_exc(), "err")
            finally:
                self._busy = None
        threading.Thread(target=runner, daemon=True).start()

    # ------------------------------------------------------------------ actions
    def action_compute(self):
        self._show_device()
        p = self.app._get_params()
        ds = self.ds

        def work():
            from .coupled_line import device_crosstalk
            lo = device_crosstalk(p, float(ds["dz_lo"]))
            hi = device_crosstalk(p, float(ds["dz_hi"]))
            return dict(p=p, lo=lo, hi=hi)
        self._run("Compute", work, self._show_result)

    def action_export(self):
        p = self.app._get_params()
        ds = self.ds

        def work():
            from .coupled_line import export_coupled_tables
            out = self.app._resolve_out_dir(p)
            r = export_coupled_tables(p, out, float(ds["dz_hi"]))
            self.app.log(f"Crosstalk tables (200 um pitch line) written: {r['even']}, {r['odd']} "
                         f"(Ze/Zo - 1 = {r['dz']:.4g}, up to {r['table_top_GHz']:.1f} GHz)", "ok")
            return r
        self._run("Export tables", work,
                  lambda r: self.status.config(text=f"tables in {os.path.dirname(r['even'])}"))

    def action_ic_check(self):
        p = self.app._get_params()
        app = self.app

        def work():
            from .xtalk_test import run_xtalk_check
            if app.ic_builder is not None:          # one INTERCONNECT session at a time
                try:
                    app.ic_builder.close()
                except Exception:
                    pass
                app.ic_builder = None
            out = os.path.join(app._resolve_out_dir(p), "xtalk_check")
            return run_xtalk_check(p, out_dir=out, log=lambda m: app.log(m))
        self._run("INTERCONNECT check", work, lambda rep: (
            self.num_txt.delete("1.0", "end"), self.num_txt.insert("1.0", rep)))

    # ------------------------------------------------------------------ display
    def _show_result(self, res):
        self.result = res
        lo, hi = res["lo"], res["hi"]
        f = lo["f_GHz"]
        th = self.theme["fig"]
        F = Figure(figsize=(10, 7), dpi=100, facecolor=th["bg"])
        axs = F.subplots(2, 2, sharex=True)

        def band(ax, a, b, color, label):
            ya, yb = _db(a), _db(b)
            ax.fill_between(f, np.minimum(ya, yb), np.maximum(ya, yb), color=color, alpha=0.45,
                            lw=0, label=label)
            ax.plot(f, yb, color=color, lw=1.0)

        S = lambda d, i: d["block"]["S"][i][0]
        band(axs[0, 0], S(lo, 2), S(hi, 2), BAND_C, "NEXT  |S(B1,A1)|")
        band(axs[0, 0], S(lo, 3), S(hi, 3), FE_C, "FEXT  |S(B2,A1)|")
        axs[0, 0].set_title("Electrical crosstalk, all ports 50 ohm (as a VNA)")
        axs[0, 0].set_ylabel("dB")

        ra, rl = hi["resp"], lo["resp"]
        h0 = np.abs(ra["H_A"][0])
        axs[0, 1].plot(f, _db(ra["H_A"] / h0), color=AGG_C, lw=1.6, label="aggressor A")
        band(axs[0, 1], rl["H_B"] / h0, ra["H_B"] / h0, VIC_C, "victim B")
        axs[0, 1].set_title("Voltage the light integrates (device source / load)")
        axs[0, 1].set_ylabel("dB re aggressor at low f")

        band(axs[1, 0], rl["H_B"] / rl["H_A"], ra["H_B"] / ra["H_A"], VIC_C, "victim / aggressor")
        axs[1, 0].set_title("EO crosstalk: victim / aggressor modulation")
        axs[1, 0].set_ylabel("dB")

        band(axs[1, 1], rl["NE_B"] / rl["V"][0], ra["NE_B"] / ra["V"][0], BAND_C,
             "near end B / V(A1)")
        band(axs[1, 1], rl["FE_B"] / rl["V"][0], ra["FE_B"] / ra["V"][0], FE_C,
             "far end B / V(A1)")
        axs[1, 1].set_title("Victim voltages (device source / load)")
        axs[1, 1].set_ylabel("dB re aggressor input voltage")

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
        F.suptitle(f"200 um pitch uniform line,  L = {lo['L']*1e3:.2f} mm,  Ze/Zo - 1 = {lo['dz']*100:.2f}-"
                   f"{hi['dz']*100:.2f} %,  dn = {np.min(lo['dn']):.5f}-{np.max(lo['dn']):.5f}",
                   color=th["fg"], fontsize=10)
        F.tight_layout()
        self.fig.show(F)

        rows = [f"{'GHz':>3s} {'NEXT dB':>12s} {'FEXT dB':>12s} {'EO vic/agg':>12s}"]
        for g in MARK_GHZ:
            if g > f[-1] + 1e-9:
                continue
            q = int(np.argmin(np.abs(f - g)))
            def rng(x, y):
                a, b = sorted((float(x), float(y)))
                return f"{a:5.1f}..{b:5.1f}"
            rows.append(f"{f[q]:3.0f} {rng(_db(S(lo, 2)[q]), _db(S(hi, 2)[q])):>12s} "
                        f"{rng(_db(S(lo, 3)[q]), _db(S(hi, 3)[q])):>12s} "
                        f"{rng(_db(rl['H_B'][q] / rl['H_A'][q]), _db(ra['H_B'][q] / ra['H_A'][q])):>12s}")
        rows += ["", "NEXT/FEXT: 4-port at 50 ohm.", "EO: with the device's source and load."]
        self.num_txt.delete("1.0", "end")
        self.num_txt.insert("1.0", "\n".join(rows))
