"""
Touchstone -> fitted line physics -> Lumerical-ready tables.

This is the former EXTRACTOR script, split into reusable pieces:

  ``extract_line_fit``        .s2p  ->  LineFit          (the slow part, once)
  ``export_lumerical_tables`` LineFit -> loss/z0/nm.txt + sim_params.json
  ``diagnostic_figure``       LineFit -> matplotlib Figure (alpha, Zc, n_m)
  ``eo_figure``               EOResult -> matplotlib Figure

Figures are returned as bare ``Figure`` objects rather than being pushed
through ``pyplot``, so the same call works embedded in the Tk GUI and headless
in the CLI.
"""

from __future__ import annotations

import json
import os
import warnings

import numpy as np
import skrf as rf
from matplotlib.figure import Figure
from scipy.optimize import curve_fit

from .physics import (C0, EOResult, LineFit, eo_response, fit_alpha_scaled,
                      fit_beta, fit_impedance_imag, fit_impedance_physical)

warnings.filterwarnings("ignore")


# =====================================================================
# 1. De-embedding + fitting
# =====================================================================
def extract_line_fit(filepath: str, L_meas_mm: float, z0_sys: float = 50.0,
                     f_fit_min_GHz: float = 0.5) -> LineFit:
    """
    ABCD de-embedding of a 2-port electrode measurement into per-unit-length
    alpha(f), beta(f) and Zc(f), followed by a physically-motivated fit of each.

    Because alpha and beta are divided by the *measured* length here, the
    result is intrinsic to the cross-section and independent of whatever
    length you later extrapolate to.
    """
    net = rf.Network(filepath)
    L_meas = L_meas_mm * 1e-3

    valid = net.f > f_fit_min_GHz * 1e9
    if valid.sum() < 8:
        raise ValueError(
            f"Only {int(valid.sum())} points above {f_fit_min_GHz} GHz in "
            f"{os.path.basename(filepath)} -- lower the fit cut-off.")

    f_Hz = net.f[valid]
    f_GHz = f_Hz / 1e9
    omega = 2 * np.pi * f_Hz

    S11, S21 = net.s[valid, 0, 0], net.s[valid, 1, 0]
    S12, S22 = net.s[valid, 0, 1], net.s[valid, 1, 1]

    # --- ABCD matrix de-embedding ---
    A = ((1 + S11) * (1 - S22) + S12 * S21) / (2 * S21)
    B = z0_sys * ((1 + S11) * (1 + S22) - S12 * S21) / (2 * S21)
    C = (1 / z0_sys) * ((1 - S11) * (1 - S22) - S12 * S21) / (2 * S21)

    Zc_raw = np.sqrt(B / C)
    Zc_raw = np.where(np.real(Zc_raw) < 0, -Zc_raw, Zc_raw)
    exp_gammad = A + (B / Zc_raw)

    alpha_raw_Np_m = np.log(np.abs(exp_gammad)) / L_meas
    beta_raw = np.unwrap(np.angle(exp_gammad)) / L_meas
    alpha_raw_dB_cm = alpha_raw_Np_m * 8.686 / 100

    # --- physical regression, so every quantity extrapolates sensibly ---
    popt_a, _ = curve_fit(fit_alpha_scaled, f_GHz, alpha_raw_dB_cm, maxfev=20000)
    popt_z, _ = curve_fit(fit_impedance_physical, f_GHz, np.real(Zc_raw), maxfev=20000)
    popt_zi, _ = curve_fit(fit_impedance_imag, f_GHz, np.imag(Zc_raw), maxfev=20000)
    popt_b, _ = curve_fit(fit_beta, f_Hz, beta_raw, maxfev=20000)

    return LineFit(
        popt_alpha=popt_a, popt_zre=popt_z, popt_zim=popt_zi, popt_beta=popt_b,
        L_meas_m=L_meas, z0_sys=z0_sys,
        f_min_sim_GHz=float(f_GHz.min()), f_max_sim_GHz=float(f_GHz.max()),
        source_file=os.path.basename(filepath),
        raw_f_GHz=f_GHz, raw_alpha_dB_cm=alpha_raw_dB_cm, raw_Zc=Zc_raw,
        raw_nm=(C0 * beta_raw) / omega,
    )


# =====================================================================
# 2. Export for INTERCONNECT
# =====================================================================
def export_lumerical_tables(fit: LineFit, p: dict, res: EOResult,
                            out_dir: str, points_per_GHz: float | None = None) -> dict:
    """
    Write loss.txt / z0.txt / nm.txt / sim_params.json.

    The tables carry the *intrinsic* per-unit-length physics, so they never
    depend on the target length -- only ``TW_1.length`` does, and that is
    carried in sim_params.json. The tables are extended past the measured
    range only when the -3 dB point actually lands there, which keeps the
    export honest about where it stops being data and starts being a fit.
    """
    os.makedirs(out_dir, exist_ok=True)
    if points_per_GHz is None:
        points_per_GHz = int(p["n_points"]) / float(p["f_max_GHz"])

    extrapolated = res.bw_GHz > fit.f_max_sim_GHz
    table_f_max = float(p["f_max_GHz"]) if extrapolated else fit.f_max_sim_GHz
    n_table = max(int(table_f_max * points_per_GHz), 200)
    f_table = np.linspace(float(p["f_norm_GHz"]), table_f_max, n_table)

    alpha = fit.alpha_dB_cm(f_table,
                            scale=float(p["alpha_scale"]),
                            skin_scale=float(p["alpha_skin_scale"]),
                            diel_scale=float(p["alpha_diel_scale"]),
                            offset=float(p["alpha_offset_dB_cm"]))
    Zc = fit.Zc(f_table, offset=float(p["zc_offset_ohm"]))
    nm = fit.nm(f_table, offset=float(p["nm_offset"]))

    paths = {
        "loss": os.path.join(out_dir, "loss.txt"),
        "z0": os.path.join(out_dir, "z0.txt"),
        "nm": os.path.join(out_dir, "nm.txt"),
        "json": os.path.join(out_dir, "sim_params.json"),
    }

    np.savetxt(paths["loss"], np.column_stack([f_table * 1e9, alpha * 100.0]),
               fmt="%.6e", delimiter="\t",
               header="Frequency (Hz)\tLoss (dB/m)", comments="# ")
    np.savetxt(paths["z0"], np.column_stack([f_table * 1e9, np.real(Zc), np.imag(Zc)]),
               fmt="%.6e", delimiter="\t",
               header="Frequency (Hz)\tReal(Z0)\tImag(Z0)", comments="# ")
    np.savetxt(paths["nm"], np.column_stack([f_table * 1e9, nm]),
               fmt="%.6e", delimiter="\t",
               header="Frequency (Hz)\tnm", comments="# ")

    meta = {
        "source_file": fit.source_file,
        "Zs": float(p["Zs_R"]), "Zs_L_pH": float(p["Zs_L_pH"]), "Zs_C_fF": float(p["Zs_C_fF"]),
        "Rt": float(p["Rt_R"]), "Rt_L_pH": float(p["Rt_L_pH"]), "Rt_C_fF": float(p["Rt_C_fF"]),
        "ng": float(p["ng"]),
        "L_meas_m": fit.L_meas_m,
        "L_target_m": float(p["L_target_mm"]) * 1e-3,
        "f_norm_GHz": float(p["f_norm_GHz"]),
        "f_max_GHz": float(p["f_max_GHz"]),
        "table_f_max_GHz": float(table_f_max),
        "eo_bw_GHz_python": float(res.bw_GHz),
        "bw_level_dB": float(p["bw_level_dB"]),
        "nm_at_60GHz": float(fit.nm(np.array([60.0]), offset=float(p["nm_offset"]))[0]),
        "extrapolated": bool(extrapolated),
        "Vpi_V": float(p["Vpi_V"]),
        "drive_config": str(p["drive_config"]),
        "bias_phase_deg": float(p["bias_phase_deg"]),
        "arm_loss_imbalance_dB": float(p["arm_loss_imbalance_dB"]),
        "arm_phase_imbalance_deg": float(p["arm_phase_imbalance_deg"]),
        "vpi_imbalance_frac": float(p["vpi_imbalance_frac"]),
        "P_laser_dBm": float(p["P_laser_dBm"]),
        "lambda_nm": float(p["lambda_nm"]),
        "ic_sample_rate_GHz": float(p["ic_sample_rate_GHz"]),
        "ic_ena_points": int(p["ic_ena_points"]),
    }
    with open(paths["json"], "w") as fh:
        json.dump(meta, fh, indent=2)

    paths["table_f_max_GHz"] = table_f_max
    paths["n_points"] = n_table
    paths["extrapolated"] = extrapolated
    return paths


# =====================================================================
# 3. Figures
# =====================================================================
def _style(ax, theme):
    ax.set_facecolor(theme["axes"])
    ax.grid(True, alpha=0.25, color=theme["grid"])
    ax.tick_params(colors=theme["fg"], labelsize=8)
    for s in ax.spines.values():
        s.set_color(theme["grid"])
    ax.xaxis.label.set_color(theme["fg"])
    ax.yaxis.label.set_color(theme["fg"])
    ax.title.set_color(theme["fg"])


LIGHT = {"bg": "#ffffff", "axes": "#fbfbfd", "fg": "#20232a", "grid": "#c9ced6"}
DARK = {"bg": "#1b1f27", "axes": "#232833", "fg": "#dfe4ec", "grid": "#3a4152"}


def diagnostic_figure(fit: LineFit, p: dict, theme=LIGHT) -> Figure:
    """alpha(f), Zc(f) and n_m(f): raw de-embedded points vs the physical fit."""
    fig = Figure(figsize=(10.5, 3.4), dpi=100)
    fig.patch.set_facecolor(theme["bg"])
    f = fit.raw_f_GHz
    ax1, ax2, ax3 = (fig.add_subplot(1, 3, i) for i in (1, 2, 3))

    ax1.plot(f, fit.raw_alpha_dB_cm, ".", ms=3, alpha=0.35, color=theme["fg"], label="de-embedded")
    ax1.plot(f, fit.alpha_dB_cm(f, scale=float(p["alpha_scale"]),
                                skin_scale=float(p["alpha_skin_scale"]),
                                diel_scale=float(p["alpha_diel_scale"]),
                                offset=float(p["alpha_offset_dB_cm"])),
             "-", lw=2, color="#e2504a", label="fit (as used)")
    ax1.set_title(r"Microwave loss $\alpha$")
    ax1.set_xlabel("Frequency (GHz)"), ax1.set_ylabel("dB/cm")

    Zc = fit.Zc(f, offset=float(p["zc_offset_ohm"]))
    ax2.plot(f, np.real(fit.raw_Zc), ".", ms=3, alpha=0.35, color=theme["fg"])
    ax2.plot(f, np.real(Zc), "-", lw=2, color="#3f7fd0", label=r"Re$(Z_c)$")
    ax2.plot(f, np.imag(fit.raw_Zc), ".", ms=3, alpha=0.2, color="#b06bd0")
    ax2.plot(f, np.imag(Zc), "-", lw=2, color="#4fae7c", label=r"Im$(Z_c)$")
    ax2.axhline(float(p["Rt_R"]), color="#d99b2e", ls="--", lw=1.2,
                label=f"$R_T$ = {float(p['Rt_R']):.0f} $\\Omega$")
    ax2.set_ylim(-10, 80)
    ax2.set_title(r"Characteristic impedance $Z_c$")
    ax2.set_xlabel("Frequency (GHz)"), ax2.set_ylabel(r"$\Omega$")

    nm = fit.nm(f, offset=float(p["nm_offset"]))
    ax3.plot(f, fit.raw_nm, ".", ms=3, alpha=0.35, color=theme["fg"], label="de-embedded")
    ax3.plot(f, nm, "-", lw=2, color="#4fae7c", label="fit (as used)")
    ax3.axhline(float(p["ng"]), color="#d99b2e", ls="--", lw=1.4,
                label=f"$n_g$ = {float(p['ng']):.3f}")
    ax3.set_title(r"Microwave index $n_m$ vs $n_g$")
    ax3.set_xlabel("Frequency (GHz)"), ax3.set_ylabel("index")

    for ax in (ax1, ax2, ax3):
        _style(ax, theme)
        leg = ax.legend(fontsize=7, framealpha=0.25)
        for t in leg.get_texts():
            t.set_color(theme["fg"])
    fig.tight_layout()
    return fig


def eo_figure(fit: LineFit, res: EOResult, p: dict, theme=LIGHT,
              lumerical=None) -> Figure:
    """Normalised EO S21 with the bandwidth marker, plus electrical return loss."""
    fig = Figure(figsize=(10.5, 4.6), dpi=100)
    fig.patch.set_facecolor(theme["bg"])
    ax = fig.add_subplot(2, 1, 1)
    axr = fig.add_subplot(2, 1, 2, sharex=ax)

    level = float(p["bw_level_dB"])
    label = f"Python model (BW = {res.bw_GHz:.2f} GHz" + (" +" if res.bw_clipped else "") + ")"
    ax.plot(res.f_GHz, res.s21_dB, "-", lw=2, color="#3f7fd0", label=label)
    if lumerical is not None:
        f_l, s_l, bw_l = lumerical
        ax.plot(f_l, s_l, "--", lw=1.8, color="#e2504a",
                label=f"INTERCONNECT (BW = {bw_l:.2f} GHz)")
    ax.axhline(level, color="#e2504a", ls="--", lw=1.2, label=f"{level:.0f} dB")
    ax.axvline(res.bw_GHz, color="#4fae7c", ls=":", lw=1.4)
    ax.axvline(fit.f_max_sim_GHz, color=theme["grid"], ls=":", lw=1.2,
               label=f"end of S-param data ({fit.f_max_sim_GHz:.0f} GHz)")
    ax.set_ylabel("Normalised EO S21 (dB)")
    ax.set_ylim(min(-40, level - 10), 3)
    ax.set_title(f"EO response  |  {fit.source_file}  |  L = {float(p['L_target_mm']):.2f} mm, "
                 f"$R_T$ = {float(p['Rt_R']):.0f} $\\Omega$, $n_g$ = {float(p['ng']):.3f}")

    axr.plot(res.f_GHz, res.s11_dB, "-", lw=1.8, color="#b06bd0",
             label=f"$S_{{11}}$ into the loaded line (worst {res.s11_worst_dB:.1f} dB)")
    axr.axhline(-10, color=theme["grid"], ls="--", lw=1.0, label="-10 dB")
    axr.set_xlabel("Frequency (GHz)"), axr.set_ylabel("Electrical $S_{11}$ (dB)")
    axr.set_ylim(-40, 0)

    for a in (ax, axr):
        _style(a, theme)
        leg = a.legend(fontsize=7, framealpha=0.25, loc="lower left")
        for t in leg.get_texts():
            t.set_color(theme["fg"])
    fig.tight_layout()
    return fig
