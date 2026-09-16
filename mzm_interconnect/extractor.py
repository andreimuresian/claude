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
                      fit_beta, fit_impedance_imag, fit_impedance_physical,
                      fit_nm_saturating)

warnings.filterwarnings("ignore")


# =====================================================================
# 1. De-embedding + fitting
# =====================================================================
NM_MODELS = ("saturating", "cubic-beta")


def _robust_fit(fn, x, y, p0=None, bounds=None, maxfev=40000):
    """
    Least-squares fit, then refit with a soft-L1 loss scaled to the residual
    spread.

    De-embedded parameters carry outliers -- mismatch resonances, the ends of
    the band, numerical noise where the inversion is ill-conditioned -- and a
    plain least-squares fit lets a handful of them steer the extrapolation. On
    a real CST file the Im(Zc) fit came out as two large cancelling terms
    (-31.1/sqrt(f) + 30.2/f) that overstated the reactance by up to 10x and
    produced a badly exaggerated ripple in the EO response.

    The residual scale is measured from the data (MAD of the first fit), so
    there is no magic constant, and a fit that is already clean -- synthetic
    data, or a well-conditioned measurement -- skips the refit entirely and
    returns exactly what plain least squares gave.

    Returns (popt, refitted).
    """
    kw = {}
    if p0 is not None:
        kw["p0"] = p0
    if bounds is not None:
        kw["bounds"] = bounds
    popt, _ = curve_fit(fn, x, y, maxfev=maxfev, **kw)

    resid = fn(x, *popt) - y
    scale = 1.4826 * float(np.median(np.abs(resid - np.median(resid))))
    floor = 1e-6 * max(float(np.max(np.abs(y))), 1e-12)
    if not np.isfinite(scale) or scale <= floor:
        return popt, False

    try:
        popt_r, _ = curve_fit(fn, x, y, p0=popt, method="trf", loss="soft_l1",
                              f_scale=scale, max_nfev=maxfev,
                              bounds=bounds if bounds is not None
                              else (-np.inf, np.inf))
        return popt_r, True
    except Exception:
        return popt, False


def extract_line_fit(filepath: str, L_meas_mm: float, z0_sys: float = 50.0,
                     f_fit_min_GHz: float = 0.5,
                     nm_model: str = "saturating") -> LineFit:
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

    nm_raw = (C0 * beta_raw) / omega
    f_max = float(f_GHz.max())

    # --- physical regression, so every quantity extrapolates sensibly ---
    # alpha: try the free fit first (so results that were already physical are
    # reproduced exactly), and only fall back to a sign-constrained fit if the
    # free one lands somewhere unphysical. A negative sqrt(f) coefficient means
    # the conductor-loss term is being used to cancel the dielectric one, and
    # the two then diverge from each other outside the measured band.
    popt_a, robust_a = _robust_fit(fit_alpha_scaled, f_GHz, alpha_raw_dB_cm)
    alpha_constrained = bool(popt_a[0] < 0 or popt_a[1] < 0)
    if alpha_constrained:
        popt_a, _ = _robust_fit(fit_alpha_scaled, f_GHz, alpha_raw_dB_cm,
                                bounds=([0.0, 0.0, -np.inf], [np.inf, np.inf, np.inf]))

    popt_z, _ = _robust_fit(fit_impedance_physical, f_GHz, np.real(Zc_raw))
    popt_zi, robust_zi = _robust_fit(fit_impedance_imag, f_GHz, np.imag(Zc_raw))
    popt_b, _ = curve_fit(fit_beta, f_Hz, beta_raw, maxfev=20000)   # legacy model

    # n_m: bounded dispersion, with the corner pinned inside the measured range
    # so the model cannot claim dispersion the data never resolved.
    try:
        popt_nm, _ = _robust_fit(
            fit_nm_saturating, f_GHz, nm_raw,
            p0=(float(np.median(nm_raw)), 0.01, min(30.0, f_max)),
            bounds=([1.0, -1.0, 1e-3], [10.0, 1.0, f_max]), maxfev=80000)
    except Exception:
        popt_nm = np.array([float(np.median(nm_raw)), 0.0, f_max])

    # --- how trustworthy is this extraction? ---
    top = f_GHz >= 0.75 * f_max
    resid_a = fit_alpha_scaled(f_GHz, *popt_a) - alpha_raw_dB_cm
    quality = {
        "alpha_rms_dB_cm": float(np.sqrt(np.mean(resid_a ** 2))),
        "alpha_mean_top_dB_cm": float(alpha_raw_dB_cm[top].mean()) if top.any() else float("nan"),
        "alpha_std_top_dB_cm": float(alpha_raw_dB_cm[top].std()) if top.any() else float("nan"),
        "nm_spread": float(nm_raw.max() - nm_raw.min()),
        "total_IL_dB": float(-20 * np.log10(np.abs(S21)).min()),
        "robust_refit": bool(robust_a or robust_zi),
    }
    m, sd = quality["alpha_mean_top_dB_cm"], quality["alpha_std_top_dB_cm"]
    quality["alpha_scatter"] = float(sd / m) if m else float("nan")

    return LineFit(
        popt_alpha=popt_a, popt_zre=popt_z, popt_zim=popt_zi, popt_beta=popt_b,
        L_meas_m=L_meas, z0_sys=z0_sys,
        f_min_sim_GHz=float(f_GHz.min()), f_max_sim_GHz=f_max,
        source_file=os.path.basename(filepath),
        nm_model=nm_model, popt_nm=popt_nm, alpha_constrained=alpha_constrained,
        quality=quality,
        raw_f_GHz=f_GHz, raw_alpha_dB_cm=alpha_raw_dB_cm, raw_Zc=Zc_raw,
        raw_nm=nm_raw,
    )


def dispersion_check(fit: LineFit) -> dict:
    """
    Is the apparent n_m dispersion real, or is it noise?

    Fit each n_m model on the lower half of the measured band and score it on
    the upper half, which it has never seen. A model that is chasing ripple
    scores badly out of sample; one that is tracking real dispersion scores
    well. This is the only way to separate the two without more data.

    Returns the out-of-sample RMS for each model plus how far n_m actually
    moved between the halves.
    """
    fG, nm = fit.raw_f_GHz, fit.raw_nm
    if fG.size < 20:
        return {}
    split = 0.5 * (fG.min() + fG.max())
    lo, hi = fG <= split, fG > split
    if lo.sum() < 8 or hi.sum() < 8:
        return {}

    out = {"split_GHz": float(split),
           "nm_shift": float(nm[hi].mean() - nm[lo].mean()),
           "rms": {}}
    out["rms"]["constant"] = float(np.sqrt(np.mean((np.median(nm[lo]) - nm[hi]) ** 2)))
    try:
        ps, _ = curve_fit(fit_nm_saturating, fG[lo], nm[lo],
                          p0=(float(np.median(nm[lo])), 0.01, min(30.0, split)),
                          bounds=([1.0, -1.0, 1e-3], [10.0, 1.0, split]), maxfev=80000)
        out["rms"]["saturating"] = float(np.sqrt(np.mean(
            (fit_nm_saturating(fG[hi], *ps) - nm[hi]) ** 2)))
    except Exception:
        pass
    try:
        beta_lo = nm[lo] * 2 * np.pi * fG[lo] * 1e9 / C0
        pb, _ = curve_fit(fit_beta, fG[lo] * 1e9, beta_lo, maxfev=40000)
        pred = C0 * fit_beta(fG[hi] * 1e9, *pb) / (2 * np.pi * fG[hi] * 1e9)
        out["rms"]["cubic-beta"] = float(np.sqrt(np.mean((pred - nm[hi]) ** 2)))
    except Exception:
        pass
    if out["rms"]:
        out["best"] = min(out["rms"], key=out["rms"].get)
    return out


def extraction_warnings(fit: LineFit, res: EOResult | None = None) -> list[str]:
    """Plain-language warnings about how far this result is being trusted."""
    w = []
    q = fit.quality
    if fit.alpha_constrained:
        w.append("The free alpha fit came out unphysical (negative conductor- or "
                 "dielectric-loss coefficient) and was refitted with both constrained "
                 "to be non-negative. That usually means the de-embedded loss is noisy.")
    if q.get("alpha_scatter", 0) > 0.15:
        w.append(f"The de-embedded loss scatters by {100*q['alpha_scatter']:.0f}% of its "
                 f"own mean over the top quarter of the band "
                 f"({q['alpha_mean_top_dB_cm']:.2f} +/- {q['alpha_std_top_dB_cm']:.2f} dB/cm). "
                 f"The test pattern only shows {q.get('total_IL_dB', float('nan')):.2f} dB of "
                 f"insertion loss in total, so alpha is poorly determined and every "
                 f"bandwidth below inherits that.")
    dc = dispersion_check(fit)
    if dc and "saturating" in dc["rms"] and "constant" in dc["rms"]:
        sat, con = dc["rms"]["saturating"], dc["rms"]["constant"]
        if sat < 0.8 * con:
            w.append(f"n_m dispersion looks REAL: fitted on the lower half of the band, "
                     f"the saturating model predicts the upper half {con/sat:.1f}x better "
                     f"than a constant (RMS {sat:.5f} vs {con:.5f}). Keep nm_model="
                     f"'saturating'.")
        elif sat > 1.25 * con:
            w.append(f"n_m dispersion looks like NOISE: a constant predicts the unseen "
                     f"upper half {sat/con:.1f}x better than the saturating fit "
                     f"(RMS {con:.5f} vs {sat:.5f}). The 'constant n_m' variant in the "
                     f"spread below is the more trustworthy one here.")
        else:
            w.append(f"n_m moves only {dc['nm_shift']:+.4f} across the band and constant vs "
                     f"saturating predict the unseen upper half about equally well "
                     f"(RMS {con:.5f} vs {sat:.5f}). Any dispersion here is comparable to "
                     f"the noise; trust the spread between them, not either one alone.")
    if res is not None and res.ripple_pp_dB > 0.25:
        w.append(f"The low-frequency response ripples {res.ripple_pp_dB:.2f} dB "
                 f"peak-to-peak with a period of {res.ripple_period_GHz:.2f} GHz "
                 f"(= c/2.n_m.L), because Zc is not matched to the source and load. "
                 f"Normalisation = 'plateau' averages that out; switching to 'point' "
                 f"makes the answer depend on which frequency you anchor at.")
    if res is not None and res.bw_GHz > 1.15 * fit.f_max_sim_GHz:
        w.append(f"The -3 dB point ({res.bw_GHz:.0f} GHz) sits {res.bw_GHz/fit.f_max_sim_GHz:.1f}x "
                 f"beyond the end of the S-parameter data ({fit.f_max_sim_GHz:.0f} GHz). "
                 f"It is set entirely by how the fits extrapolate, not by the data.")
    return w


def fit_family(fit: LineFit) -> list:
    """
    Every defensible way to fit the same de-embedded data.

    When the -3 dB point lands well outside the measured band its value is set
    by the choice of fitting form, not by the data. Rather than pretend one
    choice is the truth, evaluate them all and quote the spread: that spread is
    the real uncertainty of the number.
    """
    from dataclasses import replace
    fG, a_raw, nm_raw = fit.raw_f_GHz, fit.raw_alpha_dB_cm, fit.raw_nm
    f_max = fit.f_max_sim_GHz

    alphas = {"fitted": fit.popt_alpha}
    try:
        p_rob, _ = curve_fit(fit_alpha_scaled, fG, a_raw,
                             bounds=([0.0, 0.0, -np.inf], [np.inf, np.inf, np.inf]),
                             loss="soft_l1", f_scale=0.3, max_nfev=20000)
        alphas["outlier-robust"] = p_rob
    except Exception:
        pass

    # The legacy cubic-beta model is deliberately NOT in this family. It is not a
    # defensible alternative -- it is unbounded outside the measured band and
    # fits worse inside it -- so including it would inflate the quoted
    # uncertainty with a form we know to be wrong. It stays reachable through
    # the nm_model parameter only, for reproducing older numbers.
    nms = {"saturating": ("saturating", fit.popt_nm),
           "constant n_m": ("saturating", np.array([float(np.median(nm_raw)), 0.0, f_max]))}
    try:
        p_free, _ = curve_fit(fit_nm_saturating, fG, nm_raw,
                              p0=tuple(fit.popt_nm), maxfev=80000,
                              bounds=([1.0, -1.0, 1e-3], [10.0, 1.0, 1e6]))
        nms["saturating, free corner"] = ("saturating", p_free)
    except Exception:
        pass

    out = []
    for a_lbl, a_par in alphas.items():
        for n_lbl, (model, n_par) in nms.items():
            out.append((f"alpha={a_lbl}, n_m={n_lbl}",
                        replace(fit, popt_alpha=a_par, nm_model=model, popt_nm=n_par)))
    return out


def bandwidth_spread(fit: LineFit, p: dict) -> dict:
    """Bandwidth over the whole fit family -- min, median, max and per-variant."""
    rows = []
    for label, variant in fit_family(fit):
        try:
            rows.append((label, float(eo_response(variant, p).bw_GHz)))
        except Exception:
            continue
    if not rows:
        return {}
    vals = np.array([v for _, v in rows])
    return {"rows": rows, "min": float(vals.min()), "max": float(vals.max()),
            "median": float(np.median(vals))}


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
    # Start at the lowest measured frequency: the fitted 1/sqrt(f) and 1/f terms
    # are singular below it, so extending the table down to DC would export
    # nonsense for Zc.
    f_table = np.linspace(max(fit.f_min_sim_GHz, 1e-3), table_f_max, n_table)

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
    lo, hi = res.norm_window_GHz
    if hi > lo:
        ax.axvspan(lo, hi, color="#4fae7c", alpha=0.12, lw=0,
                   label=f"0 dB reference: mean over {lo:.1f}-{hi:.1f} GHz "
                         f"({res.ripple_pp_dB:.2f} dB ripple averaged out)")
    else:
        ax.axvline(lo, color="#4fae7c", ls="-.", lw=1.2,
                   label=f"0 dB reference: single point at {lo:.2f} GHz")
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
