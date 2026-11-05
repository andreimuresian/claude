"""
ALD impact on one wafer of CORDOBA 8 mm lines (15 lines, measured before = noALD and after = ALD).

Usage: python3 wafer_analysis.py <wafer>      (files raw/<wafer>/<wafer>_<noALD|ALD>_NN.s2p)

Per file, the MZM Studio extractor (mzm_interconnect.extractor.extract_line_fit, L = 8 mm, fit from 0.5 GHz) gives the
raw de-embedded n_m(f), Zc(f), alpha(f) and their fitted models; S11 and S21 are the measured ones.
Figures (in out_<wafer>/):
 1. <q>_all_lines.png : raw curves of all 15 lines, noALD (left) and ALD (right), same axes; q = n_m, Z0 (real part),
    alpha (dB/cm), |S11| (dB), |S21| (dB).
 2. <q>_mean.png      : at each frequency, the plain mean over the 15 lines of the raw quantity (dB values for S11
    and S21), noALD vs ALD in one graph; shaded band = +-1 standard deviation across lines.
 3. boxplots_60GHz.png : one value per line and state at 60 GHz from the fitted line model: n_m, Re Z0, alpha from
    the fits; S21 synthesised from the fitted line (gamma = alpha + j 2 pi f n_m / c, fitted Zc, L = 8 mm) between
    50 ohm source and load. Box: median and quartiles; whiskers: 1.5 x IQR; each line as a dot, before and after
    joined.
Also: file checks (reciprocity |S21 - S12|, passivity |S11|^2 + |S21|^2), lines outside median +- 3 MAD flagged,
and a CSV of the 60 GHz values.
"""
import os, sys, glob, re, csv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect.extractor import extract_line_fit
from mzm_interconnect.physics import C0

wafer = sys.argv[1] if len(sys.argv) > 1 else "4CA0162"
L_MM = 8.0; F60 = 60.0; Z_REF = 50.0
OUT = os.path.join(HERE, f"out_{wafer}"); os.makedirs(OUT, exist_ok=True)
STATES = ("noALD", "ALD"); COL = {"noALD": "#2a78d6", "ALD": "#eb6834"}
data = {s: {} for s in STATES}
for fn in sorted(glob.glob(os.path.join(HERE, "raw", wafer, f"{wafer}_*_*.s2p"))):
    m = re.search(r"_(noALD|ALD)_(\d{2})\.s2p$", fn); s, nn = m.group(1), m.group(2)
    net = rf.Network(fn); fit = extract_line_fit(fn, L_MM)
    data[s][nn] = dict(net=net, fit=fit)
lines = sorted(set(data["noALD"]) & set(data["ALD"]))
print(f"{wafer}: lines with both states: {len(lines)} ({', '.join(lines)})")

# ---- file checks ----
print("\nFile checks: |S21 - S12| / |S21| (reciprocity: median over 0.5-60 GHz and max), max |S11|^2 + |S21|^2 (passivity, <= 1)")
for s in STATES:
    for nn in lines:
        S = data[s][nn]["net"].s
        r = abs(S[:, 1, 0] - S[:, 0, 1]) / abs(S[:, 1, 0]); pas = np.max(abs(S[:, 0, 0]) ** 2 + abs(S[:, 1, 0]) ** 2)
        flag = "  <-- check" if np.median(r) > 0.05 or pas > 1.02 else ""
        print(f"  {s:5s} {nn}: reciprocity median {np.median(r):.3f}, max {np.max(r):.3f}; passivity {pas:.3f}{flag}")

# ---- raw curves on the de-embedding grid ----
f = data["noALD"][lines[0]]["fit"].raw_f_GHz
def raw_q(d):
    fit, net = d["fit"], d["net"]
    fn = net.f / 1e9; sel = fn > 0.5
    assert np.allclose(fn[sel], fit.raw_f_GHz)
    return {"n_m": fit.raw_nm, "Re Z0 (ohm)": np.real(fit.raw_Zc), "alpha (dB/cm)": fit.raw_alpha_dB_cm,
            "|S11| (dB)": 20 * np.log10(abs(net.s[sel, 0, 0])), "|S21| (dB)": 20 * np.log10(abs(net.s[sel, 1, 0]))}
Q = {s: {nn: raw_q(data[s][nn]) for nn in lines} for s in STATES}
QN = list(Q["noALD"][lines[0]].keys())
fname = {"n_m": "n_m", "Re Z0 (ohm)": "Z0", "alpha (dB/cm)": "alpha", "|S11| (dB)": "S11", "|S21| (dB)": "S21"}
band = f >= 5
def ylim(q):
    v = np.concatenate([Q[s][nn][q][band] for s in STATES for nn in lines]); lo, hi = np.percentile(v, [0.5, 99.5])
    pad = 0.05 * (hi - lo); return lo - pad, hi + pad
cmap = plt.cm.viridis
for q in QN:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    for a, s in zip(ax, STATES):
        for i, nn in enumerate(lines):
            a.plot(f, Q[s][nn][q], color=cmap(i / (len(lines) - 1)), lw=0.8, label=nn)
        a.set_title(f"{wafer}, {s}: {len(lines)} lines (raw)", fontsize=10); a.set_xlabel("frequency (GHz)"); a.grid(alpha=0.3)
    ax[0].set_ylabel(q); ax[0].set_ylim(*ylim(q)); ax[1].legend(fontsize=6.5, ncol=3, frameon=False, title="line", title_fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{fname[q]}_all_lines.png"), dpi=150); plt.close(fig)
for q in QN:
    fig, ax = plt.subplots(figsize=(8, 4.4))
    for s in STATES:
        A = np.array([Q[s][nn][q] for nn in lines]); mu, sd = A.mean(0), A.std(0)
        ax.plot(f, mu, color=COL[s], lw=1.3, label=f"{s}: mean of {len(lines)} lines")
        ax.fill_between(f, mu - sd, mu + sd, color=COL[s], alpha=0.18, lw=0)
    ax.set_ylim(*ylim(q)); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel(q); ax.grid(alpha=0.3)
    ax.set_title(f"{wafer}: {q}, mean over lines at each frequency (band: +-1 std across lines)", fontsize=10)
    ax.legend(frameon=False, fontsize=8); fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{fname[q]}_mean.png"), dpi=150); plt.close(fig)

# ---- fitted values at 60 GHz ----
def s21_model(fit, fg):
    a_np = fit.alpha_dB_cm(fg) * 100 / 8.686; b = 2 * np.pi * fg * 1e9 * fit.nm(fg) / C0
    g = (a_np + 1j * b) * L_MM * 1e-3; zc = fit.Zc(fg)
    return 2 / (2 * np.cosh(g) + (zc / Z_REF + Z_REF / zc) * np.sinh(g))
V = {s: {} for s in STATES}
for s in STATES:
    for nn in lines:
        fit = data[s][nn]["fit"]
        V[s][nn] = {"n_m": float(fit.nm(F60)), "Re Z0 (ohm)": float(np.real(fit.Zc(F60))),
                    "alpha (dB/cm)": float(fit.alpha_dB_cm(F60)), "|S21| (dB)": float(20 * np.log10(abs(s21_model(fit, F60))))}
BQ = ["n_m", "Re Z0 (ohm)", "alpha (dB/cm)", "|S21| (dB)"]
with open(os.path.join(OUT, "values_60GHz.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["line", "state"] + BQ)
    for s in STATES:
        for nn in lines:
            w.writerow([nn, s] + [f"{V[s][nn][q]:.5g}" for q in BQ])
print("\nFitted values at 60 GHz: median noALD -> ALD (median of per-line change); lines outside median +- 3 MAD")
for q in BQ:
    a = np.array([V["noALD"][nn][q] for nn in lines]); b = np.array([V["ALD"][nn][q] for nn in lines])
    out = []
    for s, v in (("noALD", a), ("ALD", b)):
        mad = np.median(abs(v - np.median(v))) * 1.4826
        out += [f"{s} {lines[i]}" for i in np.where(abs(v - np.median(v)) > 3 * mad)[0]] if mad > 0 else []
    print(f"  {q:14s} {np.median(a):9.4f} -> {np.median(b):9.4f}  (change {np.median(b - a):+.4f})  outliers: {', '.join(out) or 'none'}")
fig, ax = plt.subplots(1, 4, figsize=(16.5, 4.8))
for a, q in zip(ax, BQ):
    va = [V["noALD"][nn][q] for nn in lines]; vb = [V["ALD"][nn][q] for nn in lines]
    a.boxplot([va, vb], positions=[0, 1], widths=0.45, showfliers=False, medianprops=dict(color="k"))
    for i, (nn, y0, y1) in enumerate(zip(lines, va, vb)):
        c = cmap(i / (len(lines) - 1))
        a.plot([0, 1], [y0, y1], color=c, lw=0.8, alpha=0.7, zorder=1)
        a.scatter([0], [y0], color=c, marker="o", s=22, zorder=3, edgecolor="white", linewidth=0.5, label=nn)
        a.scatter([1], [y1], color=c, marker="s", s=22, zorder=3, edgecolor="white", linewidth=0.5)
    a.set_xticks([0, 1]); a.set_xticklabels(["no ALD (o)", "ALD (s)"]); a.set_title(f"{q} at 60 GHz (fitted)", fontsize=10); a.grid(alpha=0.3, axis="y")
ax[-1].legend(fontsize=7, frameon=False, title="line", title_fontsize=8, loc="center left", bbox_to_anchor=(1.02, 0.5))
fig.suptitle(f"{wafer}: fitted 60 GHz values per line, before and after 40 nm Al2O3 ({len(lines)} lines; each colour one line, joined before -> after)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "boxplots_60GHz.png"), dpi=150); plt.close(fig)
# ---- fitted curves behind the 60 GHz values: raw (thin, light) and fitted model (thick), per line ----
def model_curve(fit, q, fg):
    if q == "n_m": return fit.nm(fg)
    if q == "Re Z0 (ohm)": return np.real(fit.Zc(fg))
    if q == "alpha (dB/cm)": return fit.alpha_dB_cm(fg)
    return 20 * np.log10(abs(s21_model(fit, fg)))
for q in BQ:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)
    for a, s in zip(ax, STATES):
        for i, nn in enumerate(lines):
            c = cmap(i / (len(lines) - 1)); fit = data[s][nn]["fit"]
            a.plot(f, Q[s][nn][q], color=c, lw=0.5, alpha=0.35)
            a.plot(f, model_curve(fit, q, f), color=c, lw=1.6, label=nn)
            a.plot([F60], [V[s][nn][q]], "o", color=c, ms=4, mec="k", mew=0.4)
        a.axvline(F60, color="0.5", ls=":", lw=1)
        a.set_title(f"{wafer}, {s}: raw (thin) and fitted (thick); dots: 60 GHz values", fontsize=10)
        a.set_xlabel("frequency (GHz)"); a.grid(alpha=0.3)
    ax[0].set_ylabel(q + (" (fitted line, 50 ohm ends)" if q == "|S21| (dB)" else "")); ax[0].set_ylim(*ylim(q))
    ax[1].legend(fontsize=6.5, ncol=3, frameon=False, title="line", title_fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{fname[q]}_fits.png"), dpi=150); plt.close(fig)
print(f"\nfigures in {OUT}")
