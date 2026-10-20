"""
INTERCONNECT check of the "Coupled TL" scripted element (crosstalk between two
adjacent electrodes A and B) against its Python twin, coupled_line.py.

One session, saved BEFORE it runs. Three rows, each its own copy of the
circuit inside a Compound with scattering data analysis on (the Step 0 result:
only there are reflections exact) and its own Network Analyzer:

      ENA out -> SRC(Zs) -> A1 ==== A2 -> LOAD(Rt)
                  LOAD(Zs) -> B1 ==== B2 -> LOAD(Rt)

  MOD   'modulation A' -> ENA input 1,  'modulation B' -> ENA input 2
  FE    'far end A'    -> input 1,      'far end B'    -> input 2   (FEXT)
  NE    'near end A'   -> input 1,      'near end B'   -> input 2   (NEXT)

The line is the 200 um pitch dataset (coupled_line.load_dataset) at length
xt_L_mm, with the worse impedance split; the sidebar Touchstone file is not
used. The victim's input B1 ends in its own idle driver, Zs. Source and loads are
the scripted TL source / TL load (resistive, as in Step 0).

The report compares each trace with the twin after removing, from the
aggressor trace of the same analyser, the phase convention, the filter
latency and the overall scale (compare_traces); the victim trace gets the
SAME corrections, so its error is the coupling error alone. It also gives the
victim/aggressor ratio, which needs no correction at all. Victim points more
than 40 dB below the victim's own maximum are left out (deep nulls).

Nothing here imports lumapi unless run_xtalk_check() is called.
"""

from __future__ import annotations

import csv
import os
import traceback
from typing import Callable, Optional

import numpy as np

from . import coupled_line as CL
from . import scripted_line as SL
from .interconnect import P_IN1, P_IN2, P_OUT
from .scripted_test import FIR_TAPS, FULL_POINTS_PER_GHZ, Step0Builder, _step0_params
from .tl_schematic import ScriptedElementUnavailable

ROWS = (("MOD", "modulation", ("modulation A", "modulation B"), "H"),
        ("FE", "far end", ("far end A", "far end B"), "FE"),
        ("NE", "near end", ("near end A", "near end B"), "NE"))
NULL_DB = 40.0


class XtalkBuilder(Step0Builder):
    """Step 0's analyser and Compound helpers, with the coupled element."""

    def build(self, p: dict, tables: dict, L: float, Zs: float, Rt: float, ng: float) -> list:
        sim = self.sim
        sim.new()
        sim.switchtodesign()
        sim.deleteall()
        self._wiring = []
        self._pos = {}
        self.pending_manual = []
        sim.set("sample rate", float(p["ic_sample_rate_GHz"]) * 1e9)
        built, y = [], 0
        for label, kind, outs, _ in ROWS:
            ena, cs, ct = f"ENA_{label}", f"SRC_{label}", f"CTL_{label}"
            la, lb1, lb2 = f"LOAD_A2_{label}", f"LOAD_B1_{label}", f"LOAD_B2_{label}"
            self._ena(ena, 0, y, p)
            # A Network Analyzer has one input by default. Set two BEFORE any
            # wire: changing the count rebuilds its ports and drops links.
            if not self.setp(ena, ['number of input ports', 'number of inputs', 'input ports'],
                             2, required=False):
                self.log(f"  {ena}: could not set 2 input ports; the victim trace will be missing")
            self.make_source(cs, 200, y, Zs)
            self.make_coupled(ct, 360, y + 40, tables["even"], tables["odd"], L, ng,
                              modulating=(kind == "modulation"), far_end=(kind == "far end"),
                              near_end=(kind == "near end"), fir_taps=FIR_TAPS)
            self.make_load(lb1, 200, y + 80, Zs)
            self.make_load(la, 540, y, Rt)
            self.make_load(lb2, 540, y + 80, Rt)
            self.connect(ena, P_OUT, cs, ['port 1'])
            self.connect(cs, ['port 2'], ct, ['A1'])
            self.connect(lb1, ['port 1'], ct, ['B1'])
            self.connect(ct, ['A2'], la, ['port 1'])
            self.connect(ct, ['B2'], lb2, ['port 1'])
            ok = self.make_compound(f"PAIR_{label}", [cs, ct, lb1, la, lb2],
                                    [(ct, outs[0], outs[0], ena, P_IN1),
                                     (ct, outs[1], outs[1], ena, P_IN2)])
            if not ok:
                raise RuntimeError(f"the Compound for {ct} could not be made")
            built.append((label, ena))
            y += 220
        return built


def python_prediction(p: dict, out_dir: str, L: float, dz: float) -> dict:
    """Tables up to the simulation's Nyquist frequency and the twin's response
    of the circuit above."""
    top = 0.5 * float(p["ic_sample_rate_GHz"])
    tables = CL.export_coupled_tables(p, out_dir, dz, f_top_GHz=top,
                                      points_per_GHz=FULL_POINTS_PER_GHZ)
    ng = float(p["ng"])
    blk = CL.coupled_sparams_from_tables(tables["even"], tables["odd"], L, ng=ng,
                                         R0=XtalkBuilder.R0)
    r = CL.terminated_response(blk, float(p["Zs_R"]), float(p["Rt_R"]), XtalkBuilder.R0)
    return dict(tables=tables, f_GHz=blk["f_Hz"] / 1e9, resp=r, top=top)


def _victim_compare(f_ref, A_ref, B_ref, f_t, A_t, B_t, band):
    """Victim error with the aggressor's corrections, and the ratio error."""
    cA = SL.compare_traces(f_ref, A_ref, f_t, A_t, band)

    def on_ref(H):
        H = np.interp(f_ref, f_t, H.real) + 1j * np.interp(f_ref, f_t, H.imag)
        return np.conj(H) if cA["convention"] == "physics" else H
    tau = cA["latency_ps"] * 1e-3                  # ns
    w = 2 * np.pi * f_ref                          # rad/ns
    Bt = on_ref(B_t) * np.exp(1j * w * tau) / cA["scale_abs"] / np.exp(1j * np.radians(cA["scale_deg"]))
    b = (f_ref >= band[0]) & (f_ref <= band[1])
    keep = b & (np.abs(B_ref) > np.max(np.abs(B_ref[b])) * 10 ** (-NULL_DB / 20))
    dB = 20 * np.log10(np.abs(Bt[keep]) / np.abs(B_ref[keep]))
    dph = np.degrees(np.angle(Bt[keep] / B_ref[keep]))
    ratio_t, ratio_r = on_ref(B_t) / on_ref(A_t), B_ref / A_ref
    dR = 20 * np.log10(np.abs(ratio_t[keep]) / np.abs(ratio_r[keep]))
    return cA, dict(max_dB=float(np.max(np.abs(dB))), max_deg=float(np.max(np.abs(dph))),
                    ratio_dB=float(np.max(np.abs(dR))), n=int(keep.sum()))


def format_report(pred, meas, status, band) -> str:
    out = []
    A = out.append
    A("Coupled TL element: INTERCONNECT vs Python twin (coupled_line.py)")
    if "settings" in pred:
        A(pred["settings"])
    A(f"band {band[0]:.1f}-{band[1]:.1f} GHz; victim points within {NULL_DB:.0f} dB of its maximum")
    for s in status:
        A(f"  {s}")
    A("")
    A(f"{'row':5s} {'aggressor: scale':>16s} {'latency ps':>10s} {'max dB':>8s} {'max deg':>8s}"
      f" | {'victim max dB':>13s} {'max deg':>8s} {'ratio dB':>9s}")
    r = pred["resp"]
    for label, _, _, key in ROWS:
        if (label, 1) not in meas:
            A(f"{label:5s} not measured")
            continue
        fa, Ha = meas[(label, 1)][:2]
        if (label, 2) not in meas:
            cA = SL.compare_traces(pred["f_GHz"], r[key + "_A"], fa, Ha, band)
            A(f"{label:5s} {cA['scale_abs']:16.4f} {cA['latency_ps']:10.2f} {cA['max_dB']:8.4f} "
              f"{cA['max_deg']:8.3f} | victim not measured")
            continue
        fb, Hb = meas[(label, 2)][:2]
        if not np.allclose(fa, fb):
            Hb = np.interp(fa, fb, Hb.real) + 1j * np.interp(fa, fb, Hb.imag)
        cA, v = _victim_compare(pred["f_GHz"], r[key + "_A"], r[key + "_B"], fa, Ha, Hb, band)
        A(f"{label:5s} {cA['scale_abs']:16.4f} {cA['latency_ps']:10.2f} {cA['max_dB']:8.4f} "
          f"{cA['max_deg']:8.3f} | {v['max_dB']:13.4f} {v['max_deg']:8.3f} {v['ratio_dB']:9.4f}")
    A("")
    A("A pass: aggressor and victim within a few hundredths of a dB and a few tenths of a")
    A("degree (the FIR filter's own error), and the same scale and latency in every row.")
    return "\n".join(out)


def run_xtalk_check(p: dict, out_dir: Optional[str] = None,
                    log: Optional[Callable[[str], None]] = None) -> str:
    log = log or print
    p = _step0_params(p, log)
    out_dir = out_dir or os.path.join(str(p["out_dir"]) or ".", "xtalk_check")
    os.makedirs(out_dir, exist_ok=True)
    L = float(p["xt_L_mm"]) * 1e-3
    dz = float(CL.load_dataset()["dz_hi"])
    pred = python_prediction(p, out_dir, L, dz)
    pred["settings"] = (f"L = {L*1e3:.3f} mm, n_g = {float(p['ng']):.4f}, Zs = {float(p['Zs_R']):.2f} ohm, "
                        f"Rt = {float(p['Rt_R']):.2f} ohm, Ze/Zo - 1 = {dz:.4g}, sample rate "
                        f"{float(p['ic_sample_rate_GHz']):.0f} GHz")
    log(f"  Tables in {out_dir}: coupled_even.txt, coupled_odd.txt, up to {pred['top']:.1f} GHz.")
    meas, status, b = {}, [], None
    try:
        b = XtalkBuilder(str(p["lumapi_path"]), hide=bool(p["ic_hide"]), log=log)
        built = b.build(p, pred["tables"], L, float(p["Zs_R"]), float(p["Rt_R"]), float(p["ng"]))
        icp = os.path.join(out_dir, "xtalk_check.icp")
        b.sim.save(icp)
        if b.pending_manual:
            status.append("saved, not run -- draw by hand: " + "; ".join(b.pending_manual))
        else:
            log(f"  saved {icp}; running...")
            b.sim.run()
            for label, ena in built:
                for k in (1, 2):
                    try:
                        meas[(label, k)] = b.complex_trace(ena, input_port=k)
                    except Exception as exc:
                        log(f"  {ena} input {k}: {exc}")
            status.append(f"ran; {len(meas)}/{2 * len(built)} traces read; project {icp}")
    except ScriptedElementUnavailable:
        raise
    except Exception as exc:
        status.append(f"FAILED -- {type(exc).__name__}: {str(exc).strip()}")
        log("  " + traceback.format_exc().strip().splitlines()[-1])
    finally:
        if b is not None:
            try:
                b.close()
            except Exception:
                pass
    band = (1.0, 0.95 * float(p["f_max_GHz"]))
    rep = format_report(pred, meas, status, band)
    with open(os.path.join(out_dir, "xtalk_check_report.txt"), "w") as fh:
        fh.write(rep + "\n")
    with open(os.path.join(out_dir, "xtalk_check_traces.csv"), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["row", "input", "f_GHz", "re", "im"])
        for (label, k), (f, H, *_ ) in meas.items():
            for fi, h in zip(f, H):
                wr.writerow([label, k, f"{fi:.9g}", f"{h.real:.9e}", f"{h.imag:.9e}"])
    log(rep)
    return rep
