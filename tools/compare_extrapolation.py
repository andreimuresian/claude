#!/usr/bin/env python
"""
Validate the length extrapolation against a line that was actually simulated.

Take a short test-pattern .s2p, extrapolate it to the length of a long line
that exists as its own .s2p, and overlay the two. Occasional check, so it lives
here as a script rather than as a button in the GUI.

    python tools/compare_extrapolation.py SHORT.s2p LONG.s2p \
           --L-short 2.5 --L-long 14 --Rt 50 [--out FIG.png]

The comparison is only meaningful when the termination equals the S-parameter
reference impedance. The .s2p S11 of the long line is measured with port 2 in
50 ohm, and the model's S11 is (Zin - Z0)/(Zin + Z0) with the far end in Rt;
those are the same quantity only when Rt = Z0. The script refuses otherwise.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import skrf as rf

from mzm_interconnect import parameters as P
from mzm_interconnect import physics as ph
from mzm_interconnect.extractor import extract_line_fit

C0 = 299792458.0
PURPLE, BLUE, AMBER, INK, MUTED, GRID = ("#8a5cc4", "#2b6cb0", "#b5541f",
                                         "#20232a", "#6b7280", "#d8dde5")
SURF = "#fcfcfb"


def line_s_params(alpha_dB_cm, nm, Zc, L_m, f_GHz, Z0):
    """S11 and S21 of a uniform line of length L_m in a Z0 system."""
    gamma = alpha_dB_cm * 100.0 / 8.686 + 1j * nm * 2 * np.pi * f_GHz * 1e9 / C0
    gl = gamma * L_m
    ch, sh = np.cosh(gl), np.sinh(gl)
    A, B, C, D = ch, Zc * sh, sh / Zc, ch
    den = A + B / Z0 + C * Z0 + D
    return (A + B / Z0 - C * Z0 - D) / den, 2.0 / den


def style(ax, xlabel, ylabel, title):
    ax.set_facecolor(SURF)
    ax.grid(True, color=GRID, lw=.7, alpha=.9)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=10)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=10)
    ax.set_title(title, color=INK, fontsize=11.5, fontweight="bold", loc="left", pad=9)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("short"); ap.add_argument("long")
    ap.add_argument("--L-short", type=float, required=True, help="mm")
    ap.add_argument("--L-long", type=float, required=True, help="mm")
    ap.add_argument("--Rt", type=float, default=50.0, help="ohm (must equal Z0)")
    ap.add_argument("--Z0", type=float, default=50.0, help="ohm")
    ap.add_argument("--fit-min", type=float, default=0.5, help="GHz")
    ap.add_argument("--nm-model", default="saturating")
    ap.add_argument("--out", default="extrapolation_check.png")
    a = ap.parse_args(argv)

    if abs(a.Rt - a.Z0) > 1e-9:
        ap.error(f"Rt ({a.Rt}) must equal Z0 ({a.Z0}) for the S11 comparison to "
                 f"mean anything -- the long line's .s2p S11 is measured with its "
                 f"far end in {a.Z0:g} ohm.")

    net = rf.Network(a.long)
    f = net.f / 1e9
    s11_cst = net.s[:, 0, 0]
    s21_cst = net.s[:, 1, 0]

    short = extract_line_fit(a.short, a.L_short, a.Z0, a.fit_min, nm_model=a.nm_model)
    long_ = extract_line_fit(a.long, a.L_long, a.Z0, a.fit_min, nm_model=a.nm_model)

    fe = np.maximum(f, short.f_min_sim_GHz)
    s11_pred, s21_pred = line_s_params(short.alpha_dB_cm(fe), short.nm(fe),
                                       short.Zc(fe), a.L_long * 1e-3, f, a.Z0)

    m = (f >= 1.0) & (f <= short.f_max_sim_GHz)
    x = (f >= 1.0) & (f > short.f_max_sim_GHz)
    print(f"short pattern : {short.source_file}  ({a.L_short} mm, data to "
          f"{short.f_max_sim_GHz:.1f} GHz)")
    print(f"long line     : {long_.source_file}  ({a.L_long} mm, data to "
          f"{long_.f_max_sim_GHz:.1f} GHz)")
    print(f"extrapolation factor {a.L_long / a.L_short:.2f}x in length\n")

    def report(name, pred, meas, mask, unit="linear |S|"):
        e = np.abs(pred[mask] - meas[mask])
        print(f"  {name:34s} mean {e.mean():.4f}  max {e.max():.4f}  "
              f"({unit}; measured spans {np.abs(meas[mask]).min():.4f}-"
              f"{np.abs(meas[mask]).max():.4f})")

    print("AGREEMENT (complex amplitude, so nulls do not inflate it)")
    report("S11, inside the short-line band", s11_pred, s11_cst, m)
    if x.any():
        report("S11, beyond it (extrapolated)", s11_pred, s11_cst, x)
    report("S21, inside the short-line band", s21_pred, s21_cst, m)
    if x.any():
        report("S21, beyond it (extrapolated)", s21_pred, s21_cst, x)

    print("\nPER-UNIT-LENGTH PHYSICS, each line de-embedded on its own")
    print(f"  {'f GHz':>6} {'alpha short':>12} {'alpha long':>11} {'ratio':>7} "
          f"{'n_m short':>10} {'n_m long':>9} {'Zc short':>9} {'Zc long':>8}")
    for t in (10, 20, 40, 60, 79):
        i = int(np.argmin(np.abs(short.raw_f_GHz - t)))
        j = int(np.argmin(np.abs(long_.raw_f_GHz - t)))
        als = float(short.alpha_dB_cm(np.array([float(t)]))[0])
        all_ = float(long_.alpha_dB_cm(np.array([float(t)]))[0])
        print(f"  {t:6d} {als:12.3f} {all_:11.3f} {als / all_:7.2f} "
              f"{float(short.nm(np.array([float(t)]))[0]):10.4f} "
              f"{float(long_.nm(np.array([float(t)]))[0]):9.4f} "
              f"{np.real(short.Zc(np.array([float(t)])))[0]:9.2f} "
              f"{np.real(long_.Zc(np.array([float(t)])))[0]:8.2f}")

    # What the discrepancy costs where it matters: the EO bandwidth of the long
    # device, predicted from the short pattern vs from the long line itself.
    base = dict(s2p_path=a.long, L_meas_mm=a.L_long, L_target_mm=a.L_long,
                z0_sys_ohm=a.Z0, Rt_R=a.Rt, Zs_R=a.Z0, ng=2.27,
                f_max_GHz=max(200.0, 2 * long_.f_max_sim_GHz), n_points=4000,
                nm_model=a.nm_model)
    pn = P.normalise(base)
    bw_short = ph.eo_response(short, pn).bw_GHz
    bw_long = ph.eo_response(long_, pn).bw_GHz
    print(f"\nEO BANDWIDTH of the {a.L_long:g} mm device (n_g = 2.27, R_T = {a.Rt:g} ohm)")
    print(f"  predicted from the {a.L_short:g} mm pattern : {bw_short:7.2f} GHz")
    print(f"  from the {a.L_long:g} mm line's own data     : {bw_long:7.2f} GHz")
    print(f"  extrapolation error                  : {bw_short - bw_long:+7.2f} GHz "
          f"({100 * (bw_short - bw_long) / bw_long:+.1f} %)")

    nm_s = float(short.nm(np.array([60.0]))[0])
    nm_l = float(long_.nm(np.array([60.0]))[0])
    print(f"\n  ripple period c/(2 n_m L) at {a.L_long} mm:  "
          f"predicted {C0 / (2 * nm_s * a.L_long * 1e-3) / 1e9:.3f} GHz   "
          f"from the long line itself {C0 / (2 * nm_l * a.L_long * 1e-3) / 1e9:.3f} GHz")

    # ---- figure ----
    fig, axs = plt.subplots(3, 1, figsize=(13, 10.5), sharex=True)
    fig.patch.set_facecolor(SURF)
    fend = short.f_max_sim_GHz

    ax = axs[0]
    ax.plot(f, 20 * np.log10(np.abs(s11_cst)), lw=1.6, color=INK,
            label=f"CST, {a.L_long:g} mm simulated")
    ax.plot(f, 20 * np.log10(np.abs(s11_pred)), lw=1.4, color=PURPLE, ls="--",
            label=f"our model, {a.L_short:g} mm extrapolated to {a.L_long:g} mm")
    ax.set_ylim(-45, 0)
    style(ax, "", "$S_{11}$ (dB)", f"Input match — {a.L_long:g} mm line, $R_T$ = {a.Rt:g} $\\Omega$")
    ax.legend(fontsize=9, frameon=False, labelcolor=INK, loc="lower right")

    ax = axs[1]
    ax.plot(f, 20 * np.log10(np.abs(s21_cst)), lw=1.6, color=INK, label="CST")
    ax.plot(f, 20 * np.log10(np.abs(s21_pred)), lw=1.4, color=BLUE, ls="--",
            label="our model")
    style(ax, "", "$S_{21}$ (dB)", "Electrical transmission — the direct test of $\\alpha \\cdot L$")
    ax.legend(fontsize=9, frameon=False, labelcolor=INK, loc="lower left")

    ax = axs[2]
    ax.plot(short.raw_f_GHz, short.raw_alpha_dB_cm, ".", ms=2, alpha=.30, color=PURPLE)
    ax.plot(f[f <= fend], short.alpha_dB_cm(f[f <= fend]), lw=2, color=PURPLE,
            label=f"{a.L_short:g} mm pattern, de-embedded")
    ax.plot(long_.raw_f_GHz, long_.raw_alpha_dB_cm, ".", ms=2, alpha=.30, color=AMBER)
    ax.plot(f[f <= long_.f_max_sim_GHz], long_.alpha_dB_cm(f[f <= long_.f_max_sim_GHz]),
            lw=2, color=AMBER, label=f"{a.L_long:g} mm line, de-embedded")
    ax.set_ylim(0, max(8, float(long_.alpha_dB_cm(np.array([fend]))[0]) * 2))
    style(ax, "Frequency (GHz)", r"$\alpha$ (dB/cm)",
          "Per-unit-length loss — if these disagree, the scaling premise is broken")
    ax.legend(fontsize=9, frameon=False, labelcolor=INK, loc="upper left")

    for ax in axs:
        ax.axvline(fend, color=MUTED, ls=":", lw=1.2)
    axs[0].text(fend + 1.5, -42, f"short-pattern data ends ({fend:.0f} GHz)",
                fontsize=8.5, color=MUTED, style="italic")
    fig.tight_layout()
    fig.savefig(a.out, dpi=160, facecolor=SURF)
    print(f"\nfigure written to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
