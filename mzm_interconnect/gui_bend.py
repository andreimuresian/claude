"""
The Bend window: the electrode bend as a coplanar line of its own.

How it works
  * The cross-section fields at the top are WORKING values. As you type, they
    drive everything in this window at once: the drawing, the figures of merit
    at 60 GHz and the alpha / n_m / |Zc| curves. They do NOT change the device.
  * "Apply to device" copies the working values into the device (and, if
    ticked, sets the bend length to the delay-matched one). Only then do the
    device response, the sweeps and the INTERCONNECT export use them.
  * "Optimise" runs the inverse design on the ranges; "Apply proposal" loads
    its result into the working fields and applies it to the device.
  * The device's own bend is always shown next to the working one (dashed
    curves, "Device" lines), so you see what changes before you apply it.
  * "Verify" solves the working cross-section with the 2D FEM reference and
    draws the points over the curves.
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
WORK_C, DEV_C, PROP_C, FEM_C, TARGET_C = "#4f9cf9", "#8a93a5", "#4fae7c", "#e2504a", "#d99b2e"
GOLD, SIO2, LN, SI = "#d4a72c", "#9fb7d6", "#b58ad6", "#7d8590"


def _fmt(v):
    return f"{float(v):.6g}"


def _same(a, b, tol=1e-3):
    """Two cross-sections equal to within tol (um, or relative for sigma)."""
    if a is None or b is None:
        return a is b
    ta, tb = a.astuple(), b.astuple()
    return all(abs(x - y) <= tol * (abs(x) if i == 8 else 1.0) for i, (x, y) in enumerate(zip(ta, tb)))


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
        self.current = None               # last evaluation (working, device, proposal)
        self.fem = None                   # last FEM verification (with its geometry)
        self.proposal = None              # last inverse-design result
        self._traces = []

        p0 = app._get_params()
        self.dvars = {k: tk.StringVar(value=_fmt(p0[k])) for k, _ in GEOM}

        pane = ttk.Panedwindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=10, pady=8)
        left = ttk.Frame(pane, style="Panel.TFrame", width=440)
        pane.add(left, weight=0)
        right = ttk.Frame(pane, style="Bg.TFrame")
        pane.add(right, weight=1)
        sf = ScrollFrame(left, t)
        sf.pack(fill="both", expand=True)
        body = sf.inner

        def muted(parent, text):
            lab = ttk.Label(parent, text=text, style="Muted.TLabel", wraplength=300, justify="left")
            lab.pack(fill="x", padx=4, pady=(2, 4))
            return lab

        # ---- working cross-section ------------------------------------------
        box = Collapsible(body, "Bend cross-section (working values)", t)
        box.pack(fill="x", padx=4)
        muted(box.body, "Type here: the drawing, the 60 GHz values and the curves follow at once. "
                        "The device changes only when you press Apply to device.")
        for key, label in GEOM:
            self._entry_row(box.body, self.dvars[key], f"{label} [{P.BY_KEY[key].unit}]", P.BY_KEY[key].tooltip)
        muted(box.body, "Materials: SiO2 eps 3.9; LN slab eps 28 (x) / 44 (y); Si 550 um, eps 11.7; "
                        "air above and in the gaps.")
        self.apply_len = tk.BooleanVar(value=True)
        ttk.Checkbutton(box.body, text="Apply also sets the bend length",
                        variable=self.apply_len).pack(anchor="w", padx=4)
        b = ttk.Frame(box.body, style="Panel.TFrame")
        b.pack(fill="x", padx=4, pady=4)
        ttk.Button(b, text="Apply to device", style="Accent.TButton",
                   command=self.action_apply_working).pack(side="left", fill="x", expand=True)
        ttk.Button(b, text="Reload from device", command=self.action_reload).pack(side="left", padx=(4, 0))
        self.dev_lbl = ttk.Label(box.body, text="", style="Muted.TLabel", wraplength=300, justify="left")
        self.dev_lbl.pack(fill="x", padx=4, pady=(0, 6))

        # ---- figures of merit ---------------------------------------------
        box = Collapsible(body, f"Bend line at {F_REF_GHZ:g} GHz (working values)", t)
        box.pack(fill="x", padx=4)
        self.kpi = {}
        grid = tk.Frame(box.body, bg=t["panel"])
        grid.pack(fill="x", padx=4, pady=2)
        rows = (("Z0", "|Zc|", "ohm"), ("Zt", "target |Zc|", "ohm"), ("dZ", "|Zc| - target", "ohm"),
                ("nm", "n_m", ""), ("alpha", "alpha", "dB/cm"), ("tau", "RF delay in the bend", "ps"),
                ("Lb", "length for that delay", "mm"), ("loss", "loss per bend", "dB"))
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
        self._entry_row(box.body, app.vars["bend_opt_delay_ps"], "Bend optical delay [ps]",
                        P.BY_KEY["bend_opt_delay_ps"].tooltip, device=True)

        # ---- inverse design -----------------------------------------------
        box = Collapsible(body, "Inverse design", t)
        box.pack(fill="x", padx=4)
        muted(box.body, "Finds S, W, Wg inside these ranges such that |Zc| at 60 GHz equals the target, "
                        "with the smallest loss per bend (alpha x bend length for the RF delay above). "
                        "Gold thickness, conductivity and the layer stack are the working values above.")
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
        self._entry_row(box.body, app.vars["bend_Z_target_ohm"], "Target |Zc| [ohm] (0 = line)",
                        P.BY_KEY["bend_Z_target_ohm"].tooltip)
        b = ttk.Frame(box.body, style="Panel.TFrame")
        b.pack(fill="x", padx=4, pady=4)
        self.btn_opt = ttk.Button(b, text="Optimise", style="Accent.TButton", command=self.action_optimise)
        self.btn_opt.pack(side="left", fill="x", expand=True)
        self.btn_apply = ttk.Button(b, text="Apply proposal", command=self.action_apply_proposal,
                                    state="disabled")
        self.btn_apply.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.prop_lbl = ttk.Label(box.body, text="", style="Muted.TLabel", wraplength=300, justify="left")
        self.prop_lbl.pack(fill="x", padx=4, pady=(0, 6))

        # ---- FEM verification -----------------------------------------------
        box = Collapsible(body, "Verify with the 2D FEM reference", t)
        box.pack(fill="x", padx=4)
        muted(box.body, "Solves the working cross-section with the validated reference: quasi-static FEM "
                        "capacitance and the current inside the gold (no surface-impedance "
                        "approximation). About 10 s per frequency.")
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

        # ---- figures: created once, redrawn in place ------------------------
        th = self.theme["fig"]
        self.fig_xs = FigurePane(right, t, toolbar=False)
        self.fig_xs.pack(fill="x", expand=False)
        self.fig_xs.configure(height=300)
        self.fig_xs.pack_propagate(False)
        self.fig_f = FigurePane(right, t)
        self.fig_f.pack(fill="both", expand=True, pady=(6, 0))
        self.F_xs = Figure(figsize=(10, 2.9), dpi=100, facecolor=th["bg"])
        self.F_f = Figure(figsize=(10, 4.2), dpi=100, facecolor=th["bg"])
        self.fig_xs.show(self.F_xs)
        self.fig_f.show(self.F_f)

        for var in self.dvars.values():
            self._traces.append((var, var.trace_add("write", lambda *a: self._changed())))
        for key in ("bend_opt_delay_ps", "bend_len_mm", "bend_Z_target_ohm", "bend_model") + \
                tuple(k for k, _ in GEOM):
            var = app.vars[key]                    # device values: refresh the "Device" lines
            self._traces.append((var, var.trace_add("write", lambda *a: self._changed())))
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(80, self._pump)
        self._changed(delay=10)

    # ------------------------------------------------------------------ widgets
    def _entry_row(self, parent, var, label, tip="", device=False):
        """One labelled entry. device=True: the variable is a device parameter,
        committed (device re-analysed) on Return / leaving the field."""
        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x", pady=2)
        lab = ttk.Label(row, text=label, style="Muted.TLabel", width=26, anchor="w")
        lab.pack(side="left", padx=(4, 4))
        e = ttk.Entry(row, textvariable=var, width=12)
        e.pack(side="left", fill="x", expand=True)
        if device:
            e.bind("<Return>", lambda ev: self._commit_device())
            e.bind("<FocusOut>", lambda ev: self._commit_device())
        if tip:
            self._Tooltip(lab, tip, self.theme)
            self._Tooltip(e, tip, self.theme)
        return e

    def _commit_device(self):
        try:
            self.app._on_change()
        except Exception:
            pass

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
        """Run work() on a thread, then done(result) on the UI thread. The
        thread never touches Tk: everything goes through the queue."""
        if self._busy:
            self.status.config(text=f"busy: {self._busy} -- wait or press Cancel")
            return False
        self._busy = name
        self._cancel.clear()
        self.status.config(text=f"{name}...")

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
    def _working_params(self):
        """Device parameters with the working cross-section in place of the
        device's. Raises ValueError naming the field that is not a number."""
        p = self.app._get_params()
        for key, label in GEOM:
            raw = self.dvars[key].get().strip()
            try:
                p[key] = float(raw)
            except ValueError:
                raise ValueError(f"{label}: '{raw}' is not a number") from None
        return p

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
        """RF delay (ps) the bend length is set for, and where it comes from."""
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
    def _changed(self, delay=250):
        if self._closing:
            return
        if self._refresh_job is not None:
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass
        try:
            self._refresh_job = self.after(delay, self.refresh)
        except tk.TclError:
            pass

    def refresh(self):
        """Redraw the cross-section now; compute the line (thread) and update the
        numbers and curves when it is ready."""
        self._refresh_job = None
        try:
            p = self._working_params()
            g = geometry_from_params(p)
        except Exception as exc:
            self.status.config(text=f"working cross-section: {exc}")
            return
        pdev = self.app._get_params()
        try:
            gdev = geometry_from_params(pdev) if str(pdev.get("bend_model")) == "cross-section" else None
        except Exception:
            gdev = None
        gprop = self.proposal.geometry if self.proposal is not None else None
        zt, zt_note = self._z_target(p)
        tau, tau_note = self._tau(p)
        self._seq += 1
        seq = self._seq
        self._draw_xs(g, gdev)
        for v in self.kpi.values():
            v.config(fg=self.theme["muted"])
        self.status.config(text="line model: computing...")
        fmax = max(200.0, float(p.get("f_max_GHz", 200.0)))
        ctx = dict(p=p, pdev=pdev, g=g, gdev=gdev, gprop=gprop, zt=zt, zt_note=zt_note, tau=tau,
                   tau_note=tau_note)

        def runner():
            try:
                ref = line_model(g).at_ref(F_REF_GHZ)          # the working values first
                self._post("call", lambda: self._show_kpis(seq, ctx, ref))
                dref = line_model(gdev).at_ref(F_REF_GHZ) if gdev is not None else None
                self._post("call", lambda: self._show_device(seq, ctx, dref))
                if seq != self._seq:
                    return
                self._post("status", "line model: frequency curves...")
                f = np.linspace(0.25, fmax, 400)
                curves = {"work": line_model(g).evaluate(f * 1e9)}
                if gdev is not None and not _same(gdev, g):
                    curves["dev"] = line_model(gdev).evaluate(f * 1e9)
                if gprop is not None and not _same(gprop, g) and not _same(gprop, gdev):
                    curves["prop"] = line_model(gprop).evaluate(f * 1e9)
                self._post("call", lambda: self._show_curves(seq, ctx, ref, f, curves))
                self._post("status", "line model: up to date")
            except Exception as exc:
                self._post("status", f"line model: {exc}")
        threading.Thread(target=runner, daemon=True).start()

    def _show_kpis(self, seq, ctx, ref):
        if seq != self._seq or self._closing:
            return
        k = self.kpi
        zt, tau = ctx["zt"], ctx["tau"]
        Lb = C0 * tau * 1e-12 / ref["n_m"] * 1e3
        k["Z0"].config(text=f"{ref['Z0']:.2f}")
        k["Zt"].config(text="-" if zt is None else f"{zt:.2f}")
        k["dZ"].config(text="-" if zt is None else f"{ref['Z0'] - zt:+.2f}")
        k["nm"].config(text=f"{ref['n_m']:.4f}")
        k["alpha"].config(text=f"{ref['alpha_dB_cm']:.3f}")
        k["tau"].config(text=f"{tau:.3f}")
        k["Lb"].config(text=f"{Lb:.4f}")
        k["loss"].config(text=f"{ref['alpha_dB_cm'] * Lb / 10:.4f}")
        for v in k.values():
            v.config(fg=self.theme["fg"])
        bits = [ctx["tau_note"], f"target: {ctx['zt_note']}"]
        if int(ctx["pdev"].get("n_bends", 0)) == 0:
            bits.append("the device has no bends (Device geometry > Number of bends)")
        self.note.config(text="\n".join(bits))

    def _show_device(self, seq, ctx, dref):
        if seq != self._seq or self._closing:
            return
        pdev, g, gdev = ctx["pdev"], ctx["g"], ctx["gdev"]
        Ld = float(pdev.get("bend_len_mm", 0.0))
        if gdev is None:
            txt = ("DEVICE uses the fitted bend values (Bend line from = fitted values), not a "
                   "cross-section. Apply to device switches it to the working cross-section.")
        else:
            same = _same(gdev, g)
            skew = dref["n_m"] * Ld * 1e-3 / C0 * 1e12 - ctx["tau"]
            txt = (f"DEVICE: S {gdev.S_um:g}, W {gdev.W_um:g}, Wg {gdev.Wg_um:g}, t {gdev.t_um:g} um"
                   f"{'  (= working values)' if same else '  (differs from the working values)'}\n"
                   f"|Zc| {dref['Z0']:.2f} ohm, n_m {dref['n_m']:.4f}, alpha {dref['alpha_dB_cm']:.3f} dB/cm; "
                   f"bend length {Ld:.4f} mm -> loss {dref['alpha_dB_cm'] * Ld / 10:.4f} dB, "
                   f"skew {skew:+.3f} ps")
        self.dev_lbl.config(text=txt)

    def _show_curves(self, seq, ctx, ref, f, curves):
        if seq != self._seq or self._closing:
            return
        self.current = dict(g=ctx["g"], ref=ref, f=f, curves=curves, ctx=ctx)
        self._draw_curves()

    # ------------------------------------------------------------------ figures
    def _style(self, ax, th):
        ax.set_facecolor(th["axes"])
        for s in ax.spines.values():
            s.set_color(th["grid"])
        ax.tick_params(colors=th["fg"], labelsize=8)
        ax.xaxis.label.set_color(th["fg"])
        ax.yaxis.label.set_color(th["fg"])
        ax.title.set_color(th["fg"])

    def _redraw(self, pane):
        try:
            if pane.canvas is not None:
                pane.canvas.draw_idle()
        except Exception:
            pass

    def _draw_xs(self, g, gdev):
        th = self.theme["fig"]
        fig = self.F_xs
        fig.clear()
        fig.set_facecolor(th["bg"])
        ax = fig.add_axes([0.04, 0.14, 0.80, 0.72])
        self._style(ax, th)
        S, W, Wg, t = g.S_um, g.W_um, g.Wg_um, g.t_um
        xo = S / 2 + W + Wg
        X = 1.12 * max(xo, (gdev.S_um / 2 + gdev.W_um + gdev.Wg_um) if gdev is not None else 0)
        ys = [0.0, -g.buf_um, -g.buf_um - g.slab_um, -g.buf_um - g.slab_um - g.box_um]
        ys.append(ys[-1] - 3.0)
        cols = (SIO2, LN, SIO2, SI)
        names = (f"SiO2 {g.buf_um:g}", f"LN {g.slab_um:g}", f"SiO2 {g.box_um:g}", f"Si {g.si_um:g} (cut)")
        for (y0, y1, c, nm) in zip(ys[:-1], ys[1:], cols, names):
            ax.add_patch(Rectangle((-X, y1), 2 * X, y0 - y1, color=c, lw=0, alpha=0.55))
            ax.text(X * 1.01, (y0 + y1) / 2, nm + " um", va="center", ha="left", fontsize=8, color=th["fg"],
                    clip_on=False)
        for x0, w in ((-S / 2, S), (S / 2 + W, Wg), (-xo, Wg)):
            ax.add_patch(Rectangle((x0, 0), w, t, color=GOLD, lw=0))
        if gdev is not None and not _same(gdev, g):   # the device's electrodes, outlined
            Sd, Wd, Wgd, td = gdev.S_um, gdev.W_um, gdev.Wg_um, gdev.t_um
            xod = Sd / 2 + Wd + Wgd
            for x0, w in ((-Sd / 2, Sd), (Sd / 2 + Wd, Wgd), (-xod, Wgd)):
                ax.add_patch(Rectangle((x0, 0), w, td, fill=False, ec=th["fg"], lw=1.0, ls="--"))
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
        extra = "" if gdev is None or _same(gdev, g) else "   dashed outline: the device's bend"
        ax.set_title(f"Working cross-section: Au {g.sigma / 1e6:.1f} MS/m, air above and in the gaps "
                     f"(x to scale, y stretched){extra}", fontsize=9, loc="left")
        self._redraw(self.fig_xs)

    def _draw_curves(self):
        cur = self.current
        if cur is None:
            return
        th = self.theme["fig"]
        fig = self.F_f
        fig.clear()
        fig.set_facecolor(th["bg"])
        axs = [fig.add_subplot(1, 3, i) for i in (1, 2, 3)]
        f, curves, ctx, g = cur["f"], cur["curves"], cur["ctx"], cur["g"]
        zt = ctx["zt"]
        fem = self.fem if (self.fem is not None and _same(self.fem["g"], g)) else None
        styles = (("work", WORK_C, "-", 2.2, "working values"),
                  ("dev", DEV_C, "--", 1.6, "device now"),
                  ("prop", PROP_C, ":", 2.0, "proposal"))
        for ax, key, title in zip(axs, ("alpha_dB_cm", "n_m", "Z0"),
                                  ("Attenuation (dB/cm)", "Microwave index n_m", "|Zc| (ohm)")):
            self._style(ax, th)
            ax.grid(True, color=th["grid"], lw=0.6)
            for name, col, ls, lw, lab in styles:
                if name in curves:
                    ax.plot(f, curves[name][key], color=col, ls=ls, lw=lw, label=lab)
            if fem is not None:
                ax.plot(fem["f_GHz"], fem[key], "o", ms=7, mfc="none", mew=2, color=FEM_C,
                        label="2D FEM reference")
            ax.axvline(F_REF_GHZ, color=th["grid"], ls="--", lw=1)
            ax.set_xlabel("Frequency (GHz)", fontsize=8)
            ax.set_title(title, fontsize=9)
        if zt is not None:
            axs[2].axhline(zt, color=TARGET_C, ls="--", lw=1.4, label=f"target {zt:.2f}")
        allc = list(curves.values())
        sel = f > 5
        nlo = min(np.nanmin(c["n_m"][sel]) for c in allc)
        nhi = max(np.nanmax(c["n_m"][sel]) for c in allc)
        axs[1].set_ylim(nlo - 0.03, nhi + 0.05)
        zlo = min(np.nanmin(c["Z0"][sel]) for c in allc)
        zhi = max(np.nanmax(c["Z0"][sel]) for c in allc)
        if zt is not None:
            zlo, zhi = min(zlo, zt), max(zhi, zt)
        axs[2].set_ylim(zlo - 1.5, zhi + 2.5)
        for ax in axs:
            leg = ax.legend(fontsize=7.5, frameon=False)
            for txt in leg.get_texts():
                txt.set_color(th["fg"])
        fig.subplots_adjust(left=0.06, right=0.985, bottom=0.13, top=0.9, wspace=0.28)
        self._redraw(self.fig_f)

    # ------------------------------------------------------------------ actions
    def _apply(self, geom_vals: dict, L_b_mm, what):
        """Write a cross-section (and optionally the bend length) into the device."""
        v = self.app.vars
        v["bend_model"].set("cross-section")
        for key, _ in GEOM:
            v[key].set(_fmt(geom_vals[key]))
        msg = f"{what} applied to the device: " + ", ".join(
            f"{lab.split()[-1]} {_fmt(geom_vals[k])}" for k, lab in GEOM[:3])
        if L_b_mm is not None:
            v["bend_len_mm"].set(f"{L_b_mm:.4f}")
            msg += f"; bend length {L_b_mm:.4f} mm"
        self.app.log(msg + ".")
        self.status.config(text=msg)
        self._commit_device()
        self._changed(delay=10)

    def action_apply_working(self):
        try:
            p = self._working_params()
            geometry_from_params(p)
        except Exception as exc:
            self.status.config(text=f"not applied: {exc}")
            return
        L_b = None
        if self.apply_len.get():
            cur = self.current
            g = geometry_from_params(p)
            n = (cur["ref"]["n_m"] if cur is not None and _same(cur["g"], g)
                 else line_model(g).at_ref(F_REF_GHZ)["n_m"])
            L_b = C0 * self._tau(p)[0] * 1e-12 / n * 1e3
        self._apply({k: p[k] for k, _ in GEOM}, L_b, "Working cross-section")

    def action_apply_proposal(self):
        res = self.proposal
        if res is None:
            return
        g = res.geometry
        vals = {"bend_S_um": g.S_um, "bend_W_um": g.W_um, "bend_Wg_um": g.Wg_um}
        for key, val in vals.items():                # load it into the working fields
            self.dvars[key].set(_fmt(round(val, 4)))
        p = self._working_params()
        self._apply({k: p[k] for k, _ in GEOM}, res.L_b_mm if self.apply_len.get() else None, "Proposal")

    def action_reload(self):
        p = self.app._get_params()
        for key, _ in GEOM:
            self.dvars[key].set(_fmt(p[key]))

    def action_optimise(self):
        from .bend_cpw.design import optimise
        try:
            p = self._working_params()
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
                f"{'PROPOSAL' if res.feasible else 'NOT FEASIBLE -- closest'}: S {g.S_um:.3f}, W {g.W_um:.3f}, "
                f"Wg {g.Wg_um:.3f} um\n|Zc| {res.Z0:.2f} ohm (target {zt:.2f}, {zt_note}), n_m {res.n_m:.4f}, "
                f"alpha {res.alpha_dB_cm:.3f} dB/cm\nbend {res.L_b_mm:.4f} mm for {tau:.3f} ps, "
                f"loss {res.loss_dB:.4f} dB per bend at {F_REF_GHZ:g} GHz\n{res.message}\n"
                f"(response surface vs line model at the result: {chk[0]:+.3f} / {chk[1]:+.3f} / "
                f"{chk[2]:+.3f} % on |Zc| / n_m / alpha)\nGreen dotted curves: the proposal. "
                f"Apply proposal loads it into the working fields and the device."))
            self.btn_apply.config(state="normal")
            self.app.log(f"Bend inverse design: {res.message}; S {g.S_um:.3f}, W {g.W_um:.3f}, "
                         f"Wg {g.Wg_um:.3f} um, n_m {res.n_m:.4f}, alpha {res.alpha_dB_cm:.3f} dB/cm, "
                         f"L_b {res.L_b_mm:.4f} mm", "ok" if res.feasible else "warn")
            self._changed(delay=10)

        self._run("inverse design", lambda: optimise(base, ranges, zt, tau, progress=self._progress,
                                                     cancel=self._cancel), done)

    def action_verify(self):
        from .bend_cpw import fem
        try:
            g = geometry_from_params(self._working_params())
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
            lines.append(f"% = line model vs FEM, for S {g.S_um:g}, W {g.W_um:g}, Wg {g.Wg_um:g} um. "
                         f"FEM: {res['t_s']:.0f} s, {res['mesh']['n_el']} elements.")
            self.fem_txt.delete("1.0", "end")
            self.fem_txt.insert("end", "\n".join(lines))
            self.app.log("Bend FEM verification:\n  " + "\n  ".join(lines))
            self._draw_curves()

        self._run("FEM verification", lambda: fem.verify(g, fl, progress=self._progress), done)
