"""
The Bend window: the electrode bend as a coplanar line of its own.

  * cross-section (signal S, gap W, ground Wg, gold, layer stack) drawn to
    scale in x, with the figures of merit at 60 GHz updated as you type;
  * alpha(f), n_m(f), |Zc|(f) of the bend line from the analytical line model
    (mzm_interconnect.bend_cpw.model);
  * the bend length that gives the required RF delay through the bend (bend
    optical delay, or walk-off compensated), and the loss of one bend;
  * inverse design: S, W, Wg inside editable ranges such that |Zc(60 GHz)|
    matches the modulating line and the bend loss alpha x L_b is smallest;
  * verification of the current cross-section with the 2D FEM reference
    (bend_cpw.fem), drawn over the model curves.

Every field here is the same parameter as in the sidebar (same variable), so
the device analysis, the sweeps and the INTERCONNECT export use exactly what
this window shows.
"""
from __future__ import annotations

import queue
import threading
import traceback

import numpy as np
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from tkinter import ttk

from . import parameters as P
from .bend_cpw import F_REF_GHZ, geometry_from_params, line_model
from .physics import C0, bend_walkoff_skew_ps, electrode_layout

GEOM = (("bend_S_um", "Signal width S"), ("bend_W_um", "Gap W"), ("bend_Wg_um", "Ground width Wg"),
        ("bend_t_um", "Gold thickness t"), ("bend_sigma_MSm", "Gold conductivity"),
        ("bend_buf_um", "SiO2 buffer"), ("bend_slab_um", "LN slab"), ("bend_box_um", "Buried oxide"))
RANGES = (("S", "bend_S_min_um", "bend_S_max_um"), ("W", "bend_W_min_um", "bend_W_max_um"),
          ("Wg", "bend_Wg_min_um", "bend_Wg_max_um"))
MODEL_C, FEM_C, TARGET_C = "#4f9cf9", "#e2504a", "#d99b2e"
GOLD, SIO2, LN, SI = "#d4a72c", "#9fb7d6", "#b58ad6", "#7d8590"


class BendWindow(tk.Toplevel):

    def __init__(self, app):
        super().__init__(app)
        from .gui import Collapsible, FigurePane, ScrollFrame, Tooltip
        self._Tooltip = Tooltip
        self.app = app
        t = self.theme = app.theme
        self.title("Bend line  --  cross-section, figures of merit, inverse design")
        self.geometry("1500x930")
        self.minsize(1100, 700)
        self.configure(bg=t["bg"])
        self._q: queue.Queue = queue.Queue()
        self._closing = False
        self._busy = None                 # name of the running job, or None
        self._cancel = threading.Event()
        self._seq = 0                     # drops results of superseded evaluations
        self._refresh_job = None
        self.current = None               # last evaluation of the current cross-section
        self.fem = None                   # last FEM verification (with its geometry)
        self.proposal = None              # last inverse-design result
        self._traces = []

        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=10, pady=8)
        left = ttk.Frame(pane, style="Panel.TFrame", width=440)
        pane.add(left, weight=0)
        right = ttk.Frame(pane, style="Bg.TFrame")
        pane.add(right, weight=1)

        sf = ScrollFrame(left, t)
        sf.pack(fill="both", expand=True)
        body = sf.inner

        # ---- cross-section ------------------------------------------------
        box = Collapsible(body, "Bend cross-section", t)
        box.pack(fill="x", padx=4)
        src = ttk.Frame(box.body, style="Panel.TFrame")
        src.pack(fill="x", pady=2)
        ttk.Label(src, text="Bend line from", style="Muted.TLabel", width=22).pack(side="left", padx=4)
        cb = ttk.Combobox(src, textvariable=app.vars["bend_model"], state="readonly", width=16,
                          values=list(P.BY_KEY["bend_model"].choices))
        cb.pack(side="left", fill="x", expand=True)
        cb.bind("<<ComboboxSelected>>", lambda e: self._changed(commit=True))
        Tooltip(cb, P.BY_KEY["bend_model"].tooltip, t)
        for key, label in GEOM:
            self._entry_row(box.body, key, f"{label} [{P.BY_KEY[key].unit}]")
        ttk.Label(box.body, text="Materials: SiO2 eps 3.9; LN slab eps 28 (x) / 44 (y); "
                                 "Si 550 um, eps 11.7; air above and in the gaps.",
                  style="Muted.TLabel", wraplength=300, justify="left").pack(fill="x", padx=4, pady=(2, 6))

        # ---- figures of merit ---------------------------------------------
        box = Collapsible(body, f"Bend line at {F_REF_GHZ:g} GHz", t)
        box.pack(fill="x", padx=4)
        self.kpi = {}
        grid = tk.Frame(box.body, bg=t["panel"])
        grid.pack(fill="x", padx=4, pady=2)
        rows = (("Z0", "|Zc|", "ohm"), ("Zt", "target |Zc|", "ohm"), ("nm", "n_m", ""),
                ("alpha", "alpha", "dB/cm"), ("tau", "RF delay in the bend", "ps"),
                ("Lb", "length for that delay", "mm"), ("loss", "loss per bend", "dB"),
                ("Lnow", "length now set", "mm"), ("skew", "skew, length now set", "ps"))
        for i, (k, lab, unit) in enumerate(rows):
            tk.Label(grid, text=lab, bg=t["panel"], fg=t["muted"], font=("Segoe UI", 9),
                     anchor="w").grid(row=i, column=0, sticky="w", pady=1)
            v = tk.Label(grid, text="-", bg=t["panel"], fg=t["fg"], font=("Segoe UI", 11, "bold"),
                         anchor="e", width=10)
            v.grid(row=i, column=1, sticky="e", padx=6)
            tk.Label(grid, text=unit, bg=t["panel"], fg=t["muted"], font=("Segoe UI", 9),
                     anchor="w").grid(row=i, column=2, sticky="w")
            self.kpi[k] = v
        grid.columnconfigure(0, weight=1)
        self.note = ttk.Label(box.body, text="", style="Muted.TLabel", wraplength=300, justify="left")
        self.note.pack(fill="x", padx=4, pady=(4, 2))
        rule = ttk.Frame(box.body, style="Panel.TFrame")
        rule.pack(fill="x", pady=2)
        ttk.Label(rule, text="Bend RF delay", style="Muted.TLabel", width=22).pack(side="left", padx=4)
        cr = ttk.Combobox(rule, textvariable=app.vars["bend_delay_rule"], state="readonly", width=22,
                          values=list(P.BY_KEY["bend_delay_rule"].choices))
        cr.pack(side="left", fill="x", expand=True)
        cr.bind("<<ComboboxSelected>>", lambda e: self._changed())
        Tooltip(cr, P.BY_KEY["bend_delay_rule"].tooltip, t)
        self._entry_row(box.body, "bend_opt_delay_ps", "Bend optical delay [ps]")
        ttk.Button(box.body, text="Set the bend length to this value",
                   command=self.action_set_length).pack(fill="x", padx=4, pady=(4, 6))

        # ---- inverse design -----------------------------------------------
        box = Collapsible(body, "Inverse design", t)
        box.pack(fill="x", padx=4)
        ttk.Label(box.body, text="Finds S, W, Wg inside these ranges such that |Zc| at 60 GHz "
                                 "equals the target, with the smallest loss per bend "
                                 "(alpha x bend length for the RF delay above). Gold thickness, "
                                 "conductivity and the layer stack stay as set above.",
                  style="Muted.TLabel", wraplength=300, justify="left").pack(fill="x", padx=4, pady=(2, 4))
        rg = tk.Frame(box.body, bg=t["panel"])
        rg.pack(fill="x", padx=4)
        for c, txt in enumerate(("", "min [um]", "max [um]")):
            tk.Label(rg, text=txt, bg=t["panel"], fg=t["muted"], font=("Segoe UI", 8)).grid(row=0, column=c)
        for r, (name, kmin, kmax) in enumerate(RANGES, start=1):
            tk.Label(rg, text={"S": "signal S", "W": "gap W", "Wg": "ground Wg"}[name], bg=t["panel"],
                     fg=t["muted"], font=("Segoe UI", 9), anchor="w").grid(row=r, column=0, sticky="w")
            for c, k in ((1, kmin), (2, kmax)):
                e = ttk.Entry(rg, textvariable=app.vars[k], width=9)
                e.grid(row=r, column=c, padx=3, pady=1)
                Tooltip(e, P.BY_KEY[k].help, t)
        self._entry_row(box.body, "bend_Z_target_ohm", "Target |Zc| [ohm] (0 = line)")
        b = ttk.Frame(box.body, style="Panel.TFrame")
        b.pack(fill="x", padx=4, pady=4)
        self.btn_opt = ttk.Button(b, text="Optimise", style="Accent.TButton", command=self.action_optimise)
        self.btn_opt.pack(side="left", fill="x", expand=True)
        self.btn_apply = ttk.Button(b, text="Apply proposal", command=self.action_apply, state="disabled")
        self.btn_apply.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.prop_lbl = ttk.Label(box.body, text="", style="Muted.TLabel", wraplength=300, justify="left")
        self.prop_lbl.pack(fill="x", padx=4, pady=(0, 6))

        # ---- FEM verification -----------------------------------------------
        box = Collapsible(body, "Verify with the 2D FEM reference", t)
        box.pack(fill="x", padx=4)
        ttk.Label(box.body, text="Solves the current cross-section with the validated reference: "
                                 "quasi-static FEM capacitance and the current inside the gold "
                                 "(no surface-impedance approximation). About 10 s per frequency.",
                  style="Muted.TLabel", wraplength=300, justify="left").pack(fill="x", padx=4, pady=(2, 4))
        fr = ttk.Frame(box.body, style="Panel.TFrame")
        fr.pack(fill="x", pady=2)
        ttk.Label(fr, text="Frequencies [GHz]", style="Muted.TLabel", width=22).pack(side="left", padx=4)
        self.fem_f = tk.StringVar(value="10, 20, 60, 100, 200")
        ttk.Entry(fr, textvariable=self.fem_f).pack(side="left", fill="x", expand=True)
        b = ttk.Frame(box.body, style="Panel.TFrame")
        b.pack(fill="x", padx=4, pady=4)
        self.btn_fem = ttk.Button(b, text="Verify", command=self.action_verify)
        self.btn_fem.pack(side="left", fill="x", expand=True)
        ttk.Button(b, text="Cancel", command=self._cancel.set).pack(side="left", padx=(4, 0))
        self.fem_txt = tk.Text(box.body, height=9, bg=t["entry"], fg=t["fg"], relief="flat",
                               font=("Consolas", 8), wrap="none")
        self.fem_txt.pack(fill="x", padx=4, pady=(0, 6))

        # ---- status ---------------------------------------------------------
        st = tk.Frame(self, bg=t["bg"])
        st.pack(fill="x", padx=10, pady=(0, 8))
        self.status = tk.Label(st, text="", bg=t["bg"], fg=t["muted"], anchor="w", font=("Segoe UI", 9))
        self.status.pack(side="left", fill="x", expand=True)
        self.progress = ttk.Progressbar(st, length=220, mode="determinate", maximum=1.0)
        self.progress.pack(side="right")

        # ---- figures --------------------------------------------------------
        self.fig_xs = FigurePane(right, t, toolbar=False)
        self.fig_xs.pack(fill="x", expand=False)
        self.fig_xs.configure(height=300)
        self.fig_xs.pack_propagate(False)
        self.fig_f = FigurePane(right, t)
        self.fig_f.pack(fill="both", expand=True, pady=(6, 0))

        for key in [k for k, _ in GEOM] + ["bend_opt_delay_ps", "bend_len_mm", "bend_Z_target_ohm"]:
            var = app.vars[key]
            self._traces.append((var, var.trace_add("write", lambda *a: self._changed())))
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(80, self._pump)
        self._changed()

    # ------------------------------------------------------------------ widgets
    def _entry_row(self, parent, key, label):
        t = self.theme
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", pady=2)
        lab = ttk.Label(row, text=label, style="Muted.TLabel", width=26, anchor="w")
        lab.pack(side="left", padx=(4, 4))
        e = ttk.Entry(row, textvariable=self.app.vars[key], width=12)
        e.pack(side="left", fill="x", expand=True)
        e.bind("<Return>", lambda ev: self._changed(commit=True))
        e.bind("<FocusOut>", lambda ev: self._changed(commit=True))
        spec = P.BY_KEY[key]
        if spec.help:
            self._Tooltip(lab, spec.tooltip, t)
            self._Tooltip(e, spec.tooltip, t)
        return e

    def close(self):
        self._closing = True
        self._cancel.set()
        for var, tid in self._traces:
            try:
                var.trace_remove("write", tid)
            except Exception:
                pass
        self._traces = []
        try:
            self.app.bend_window = None
        except Exception:
            pass
        self.destroy()

    # ------------------------------------------------------------------ plumbing
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
                    elif kind == "progress":
                        self.progress["value"] = float(payload)
                    elif kind == "call":
                        payload()
                except Exception:
                    self.status.config(text="display error: " + traceback.format_exc().splitlines()[-1])
        finally:
            if not self._closing:
                try:
                    self.after(80, self._pump)
                except tk.TclError:
                    pass

    def _run(self, name, work, done):
        """Run work() on a thread, then done(result) on the UI thread."""
        if self._busy:
            self._post("status", f"busy: {self._busy} -- wait or press Cancel")
            return False
        self._busy = name
        self._cancel.clear()
        self._post("status", f"{name}...")

        def runner():
            try:
                res = work()
                self._post("call", lambda: done(res))
                self._post("status", f"{name}: done")
            except Exception as exc:
                msg = str(exc) or type(exc).__name__
                self._post("status", f"{name}: {msg}")
                if msg != "cancelled":
                    self.app.log(f"[Bend window: {name}] {type(exc).__name__}: {exc}\n"
                                 + traceback.format_exc(), "err")
            finally:
                self._busy = None
                self._post("progress", 0.0)
        threading.Thread(target=runner, daemon=True).start()
        return True

    def _progress(self, msg, frac):
        self._post("status", msg)
        self._post("progress", frac)
        if self._cancel.is_set():
            raise RuntimeError("cancelled")

    # ------------------------------------------------------------------ inputs
    def _params(self):
        return self.app._get_params()

    def _z_target(self, p):
        zt = float(p.get("bend_Z_target_ohm", 0.0))
        if zt > 0:
            return zt, "typed target"
        fit = getattr(self.app, "fit", None)
        if fit is None:
            return None, "no line yet: run an analysis, or type a target |Zc|"
        z = fit.Zc(np.array([F_REF_GHZ]), offset=float(p.get("zc_offset_ohm", 0.0)))[0]
        return float(abs(z)), f"modulating line |Zc| at {F_REF_GHZ:g} GHz"

    def _tau(self, p):
        """RF delay (ps) the bend length is set for, and a note on where it comes from."""
        tau0 = float(p.get("bend_opt_delay_ps", 5.0))
        if str(p.get("bend_delay_rule")) != "walk-off compensated":
            return tau0, "RF delay = bend optical delay"
        fit, f_ref = self.app._walkoff_ref()
        if fit is None:
            return tau0, "walk-off compensation needs the line: run an analysis (bend optical delay used)"
        if sum(1 for x in electrode_layout(p) if x["kind"] == "mod") < 2:
            return tau0, "no bends in the device yet (bend optical delay used)"
        sk = bend_walkoff_skew_ps(fit, p, f_ref)
        return tau0 + sk, (f"RF delay = optical delay {tau0:.2f} ps {sk:+.2f} ps walk-off skew "
                           f"(line n_m at {f_ref:.0f} GHz vs n_g)")

    # ------------------------------------------------------------------ live evaluation
    def _changed(self, commit=False):
        if commit:
            try:
                self.app._on_change()
            except Exception:
                pass
        if self._refresh_job is not None:
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass
        try:
            self._refresh_job = self.after(350, self.refresh)
        except tk.TclError:
            pass

    def refresh(self):
        self._refresh_job = None
        try:
            p = self._params()
            g = geometry_from_params(p)
        except Exception as exc:
            self.status.config(text=f"cross-section: {exc}")
            return
        zt, zt_note = self._z_target(p)
        tau, tau_note = self._tau(p)
        self._seq += 1
        seq = self._seq
        fmax = max(200.0, float(p.get("f_max_GHz", 200.0)))
        self.status.config(text="line model...")

        def work():
            m = line_model(g)
            ref = m.at_ref(F_REF_GHZ)
            f = np.linspace(0.25, fmax, 400)
            return ref, f, m.evaluate(f * 1e9)

        def done(res):
            if seq != self._seq or self._closing:
                return
            ref, f, sw = res
            self.current = dict(g=g, ref=ref, f=f, sweep=sw, zt=zt, tau=tau, p=p)
            self._show_kpis(p, ref, zt, zt_note, tau, tau_note)
            self._draw(p, g, f, sw, zt)

        def runner():
            try:
                res = work()
                self._post("call", lambda: done(res))
                self._post("status", "line model: up to date")
            except Exception as exc:
                self._post("status", f"line model: {exc}")
        threading.Thread(target=runner, daemon=True).start()

    def _show_kpis(self, p, ref, zt, zt_note, tau, tau_note):
        k = self.kpi
        k["Z0"].config(text=f"{ref['Z0']:.2f}")
        k["Zt"].config(text="-" if zt is None else f"{zt:.2f}")
        k["nm"].config(text=f"{ref['n_m']:.4f}")
        k["alpha"].config(text=f"{ref['alpha_dB_cm']:.3f}")
        k["tau"].config(text=f"{tau:.3f}")
        Lb = C0 * tau * 1e-12 / ref["n_m"] * 1e3
        k["Lb"].config(text=f"{Lb:.4f}")
        k["loss"].config(text=f"{ref['alpha_dB_cm'] * Lb / 10:.4f}")
        Lnow = float(p.get("bend_len_mm", 0.0))
        k["Lnow"].config(text=f"{Lnow:.4f}")
        k["skew"].config(text=f"{ref['n_m'] * Lnow * 1e-3 / C0 * 1e12 - tau:+.3f}")
        bits = [tau_note, f"target: {zt_note}"]
        if zt is not None:
            bits.append(f"mismatch |Zc| - target = {ref['Z0'] - zt:+.2f} ohm")
        if int(p.get("n_bends", 0)) == 0:
            bits.append("the device has no bends (Device geometry > Number of bends)")
        if str(p.get("bend_model")) != "cross-section":
            bits.append("the device uses the FITTED bend values, not this cross-section "
                        "(Bend line from)")
        self.note.config(text="\n".join(bits))

    # ------------------------------------------------------------------ figures
    def _fig_theme(self):
        return self.theme["fig"]

    def _draw(self, p, g, f, sw, zt):
        th = self._fig_theme()
        self.fig_xs.show(self._xs_figure(g, th))
        self.fig_f.show(self._f_figure(g, f, sw, zt, th))

    def _style(self, ax, th):
        ax.set_facecolor(th["axes"])
        for s in ax.spines.values():
            s.set_color(th["grid"])
        ax.tick_params(colors=th["fg"], labelsize=8)
        ax.xaxis.label.set_color(th["fg"])
        ax.yaxis.label.set_color(th["fg"])
        ax.title.set_color(th["fg"])

    def _xs_figure(self, g, th):
        fig = Figure(figsize=(10, 2.9), dpi=100)
        fig.patch.set_facecolor(th["bg"])
        ax = fig.add_axes([0.04, 0.12, 0.80, 0.74])
        self._style(ax, th)
        S, W, Wg, t = g.S_um, g.W_um, g.Wg_um, g.t_um
        xo = S / 2 + W + Wg
        X = xo + 0.12 * xo
        si_show = 3.0
        ys = [0.0, -g.buf_um, -g.buf_um - g.slab_um, -g.buf_um - g.slab_um - g.box_um]
        ys.append(ys[-1] - si_show)
        cols = (SIO2, LN, SIO2, SI)
        names = (f"SiO2 {g.buf_um:g}", f"LN {g.slab_um:g}", f"SiO2 {g.box_um:g}", f"Si {g.si_um:g} (cut)")
        for (y0, y1, c, nm) in zip(ys[:-1], ys[1:], cols, names):
            ax.add_patch(Rectangle((-X, y1), 2 * X, y0 - y1, color=c, lw=0, alpha=0.55))
            ax.text(X * 1.01, (y0 + y1) / 2, nm + " um", va="center", ha="left", fontsize=8, color=th["fg"],
                    clip_on=False)
        for x0, w in ((-S / 2, S), (S / 2 + W, Wg), (-xo, Wg)):
            ax.add_patch(Rectangle((x0, 0), w, t, color=GOLD, lw=0))
        top = t + 1.2
        ann = dict(arrowstyle="<->", color=th["fg"], lw=0.9, shrinkA=0, shrinkB=0)
        for x0, x1, lab in ((-S / 2, S / 2, f"S {S:g}"), (S / 2, S / 2 + W, f"W {W:g}"),
                            (S / 2 + W, xo, f"Wg {Wg:g}")):
            ax.annotate("", (x0, top), (x1, top), arrowprops=ann)
            ax.text((x0 + x1) / 2, top + 0.35, lab, ha="center", va="bottom", fontsize=8.5, color=th["fg"])
        ax.annotate("", (-xo - 0.04 * xo, 0), (-xo - 0.04 * xo, t), arrowprops=ann)
        ax.text(-xo - 0.06 * xo, t / 2, f"t {t:g}", ha="right", va="center", fontsize=8.5, color=th["fg"])
        ax.set_xlim(-X, X)
        ax.set_ylim(ys[-1], top + 2.2)
        ax.set_xlabel("x (um)", fontsize=8)
        ax.set_yticks([])
        ax.set_title(f"Bend cross-section: Au {g.sigma / 1e6:.1f} MS/m, air above and in the gaps  "
                     f"(x to scale, y stretched)", fontsize=9, loc="left")
        return fig

    def _f_figure(self, g, f, sw, zt, th):
        fig = Figure(figsize=(10, 4.2), dpi=100)
        fig.patch.set_facecolor(th["bg"])
        axs = [fig.add_subplot(1, 3, i) for i in (1, 2, 3)]
        fem = self.fem if (self.fem is not None and self.fem["g"] == g) else None
        data = ((sw["alpha_dB_cm"], "alpha_dB_cm", "Attenuation (dB/cm)"),
                (sw["n_m"], "n_m", "Microwave index n_m"),
                (sw["Z0"], "Z0", "|Zc| (ohm)"))
        for ax, (y, key, title) in zip(axs, data):
            self._style(ax, th)
            ax.grid(True, color=th["grid"], lw=0.6)
            ax.plot(f, y, color=MODEL_C, lw=2, label="line model")
            if fem is not None:
                ax.plot(fem["f_GHz"], fem[key], "o", ms=7, mfc="none", mew=2, color=FEM_C,
                        label="2D FEM reference")
            ax.axvline(F_REF_GHZ, color=th["grid"], ls="--", lw=1)
            ax.set_xlabel("Frequency (GHz)", fontsize=8)
            ax.set_title(title, fontsize=9)
        if zt is not None:
            axs[2].axhline(zt, color=TARGET_C, ls="--", lw=1.4, label=f"target {zt:.1f}")
        lo = np.nanpercentile(sw["n_m"], 3)
        axs[1].set_ylim(lo - 0.05, max(sw["n_m"][f > 5].max(), lo) + 0.08)
        zlo = np.nanpercentile(sw["Z0"], 3)
        axs[2].set_ylim(min(zlo, zt or zlo) - 3, max(sw["Z0"][f > 5].max(), zt or 0) + 3)
        for ax in axs:
            leg = ax.legend(fontsize=7.5, frameon=False)
            for txt in leg.get_texts():
                txt.set_color(th["fg"])
        fig.subplots_adjust(left=0.06, right=0.985, bottom=0.13, top=0.9, wspace=0.28)
        return fig

    # ------------------------------------------------------------------ actions
    def action_set_length(self):
        cur = self.current
        if cur is None:
            return
        Lb = C0 * cur["tau"] * 1e-12 / cur["ref"]["n_m"] * 1e3
        self.app.vars["bend_len_mm"].set(f"{Lb:.4f}")
        self.app.log(f"Bend length set to {Lb:.4f} mm: RF delay {cur['tau']:.3f} ps at n_m "
                     f"{cur['ref']['n_m']:.4f} (bend line at {F_REF_GHZ:g} GHz).")
        self._changed(commit=True)

    def action_optimise(self):
        from .bend_cpw.design import optimise
        p = self._params()
        try:
            base = geometry_from_params(p)
            ranges = {"S_um": (p["bend_S_min_um"], p["bend_S_max_um"]),
                      "W_um": (p["bend_W_min_um"], p["bend_W_max_um"]),
                      "Wg_um": (p["bend_Wg_min_um"], p["bend_Wg_max_um"])}
        except Exception as exc:
            self.status.config(text=str(exc))
            return
        zt, zt_note = self._z_target(p)
        if zt is None:
            self.status.config(text=zt_note)
            return
        tau, _ = self._tau(p)

        def done(res):
            self.proposal = res
            g = res.geometry
            chk = res.surface_check["surface vs model at the result, %"]
            self.prop_lbl.config(text=(
                f"{'Proposal' if res.feasible else 'NOT FEASIBLE -- closest'}: S {g.S_um:.3f}, W {g.W_um:.3f}, "
                f"Wg {g.Wg_um:.3f} um\n|Zc| {res.Z0:.2f} ohm (target {zt:.2f}, {zt_note}), n_m {res.n_m:.4f}, "
                f"alpha {res.alpha_dB_cm:.3f} dB/cm\nbend {res.L_b_mm:.4f} mm for {tau:.3f} ps, "
                f"loss {res.loss_dB:.4f} dB per bend at {F_REF_GHZ:g} GHz\n{res.message}\n"
                f"(response surface vs line model at the result: {chk[0]:+.3f} / {chk[1]:+.3f} / "
                f"{chk[2]:+.3f} % on |Zc| / n_m / alpha)"))
            self.btn_apply.config(state="normal")
            self.app.log(f"Bend inverse design: {res.message}; S {g.S_um:.3f}, W {g.W_um:.3f}, "
                         f"Wg {g.Wg_um:.3f} um, n_m {res.n_m:.4f}, alpha {res.alpha_dB_cm:.3f} dB/cm, "
                         f"L_b {res.L_b_mm:.4f} mm", "ok" if res.feasible else "warn")

        self._run("inverse design", lambda: optimise(base, ranges, zt, tau, progress=self._progress,
                                                     cancel=self._cancel), done)

    def action_apply(self):
        res = self.proposal
        if res is None:
            return
        g = res.geometry
        v = self.app.vars
        v["bend_model"].set("cross-section")
        v["bend_S_um"].set(f"{g.S_um:.4g}")
        v["bend_W_um"].set(f"{g.W_um:.4g}")
        v["bend_Wg_um"].set(f"{g.Wg_um:.4g}")
        v["bend_len_mm"].set(f"{res.L_b_mm:.4f}")
        self.app.log(f"Bend proposal applied: S {g.S_um:.4g}, W {g.W_um:.4g}, Wg {g.Wg_um:.4g} um, "
                     f"bend length {res.L_b_mm:.4f} mm.")
        self._changed(commit=True)

    def action_verify(self):
        from .bend_cpw import fem
        p = self._params()
        try:
            g = geometry_from_params(p)
            fl = [float(x) for x in self.fem_f.get().replace(";", ",").split(",") if x.strip()]
            if not fl or min(fl) <= 0:
                raise ValueError("give positive frequencies in GHz, e.g. 10, 60, 200")
        except Exception as exc:
            self.status.config(text=str(exc))
            return

        def done(res):
            res["g"] = g
            self.fem = res
            m = res["model"]
            lines = [f"{'f GHz':>6} {'alpha FEM':>9} {'model':>7} {'%':>6} {'n_m FEM':>8} {'%':>6} "
                     f"{'|Zc| FEM':>8} {'%':>6}"]
            for i, fq in enumerate(res["f_GHz"]):
                lines.append(f"{fq:6.1f} {res['alpha_dB_cm'][i]:9.4f} {m['alpha_dB_cm'][i]:7.4f} "
                             f"{(m['alpha_dB_cm'][i] / res['alpha_dB_cm'][i] - 1) * 100:+6.2f} "
                             f"{res['n_m'][i]:8.4f} {(m['n_m'][i] / res['n_m'][i] - 1) * 100:+6.2f} "
                             f"{res['Z0'][i]:8.3f} {(m['Z0'][i] / res['Z0'][i] - 1) * 100:+6.2f}")
            lines.append(f"% = line model vs FEM. FEM: {res['t_s']:.0f} s, {res['mesh']['n_el']} elements.")
            self.fem_txt.delete("1.0", "end")
            self.fem_txt.insert("end", "\n".join(lines))
            self.app.log("Bend FEM verification (S %.4g, W %.4g, Wg %.4g um):\n  " % (g.S_um, g.W_um, g.Wg_um)
                         + "\n  ".join(lines))
            if self.current is not None and self.current["g"] == g:
                c = self.current
                self._draw(c["p"], g, c["f"], c["sweep"], c["zt"])

        self._run("FEM verification", lambda: fem.verify(g, fl, progress=self._progress), done)
