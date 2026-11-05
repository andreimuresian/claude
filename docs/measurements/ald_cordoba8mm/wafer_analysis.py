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
 3. <q>_mean_fit.png and mean_fit_panel.png: line mean of the raw curve (thin) and line mean of the per-line fitted
    curves (thick); for Re Z0 the band average 10.0-42.8 GHz (4 pad-ripple periods) instead of a fit.
 4. boxplots_FOM.png: one value per line and state: n_m at 60 GHz (fit); Re Z0 averaged over 10.0-42.8 GHz (raw);
    alpha at 30 and 60 GHz (fit a sqrt f + b f + c with a, b >= 0, the extractor's fit); |S21| at 30 and 60 GHz
    synthesised from the fitted line (gamma = alpha + j 2 pi f n_m / c, fitted Zc, L = 8 mm) between 50 ohm ends.
    Box: median and quartiles; whiskers: 1.5 x IQR; each line a colour, before (o) and after (s) joined.
 5. <q>_fits.png: per-line raw and fitted curves (reference).
Also: file checks (reciprocity |S21 - S12|, passivity |S11|^2 + |S21|^2), lines outside median +- 3 MAD flagged,
values_FOM.csv (per line), summary_FOM.csv (median change, all lines and without the TOXIC lines).
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
# bad measurements, excluded from all comparisons with their partner (paired analysis), decided with the user
EXCLUDE = {"4CA0163": {"04": "ALD measurement bad: |S21| -8 dB at 10 GHz rising to -4.6 dB at 16 GHz, reciprocity 4.9 % median"}}
lines = sorted(set(data["noALD"]) & set(data["ALD"]))
for nn, why in EXCLUDE.get(wafer, {}).items():
    if nn in lines:
        lines.remove(nn); print(f"{wafer}: line {nn} excluded (both states): {why}")
print(f"{wafer}: lines with both states used: {len(lines)} ({', '.join(lines)})")

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
            a.plot(f, Q[s][nn][q], color=cmap(int(nn) / 14), lw=0.8, label=nn)
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

# ---- figures of merit per line ----
ZB = (10.0, 42.8)                       # 4 periods of the pad ripple c / (2 n L) ~ 8.2 GHz
TOXIC = {"4CA0162": ["00", "04"]}       # consistent high-loss lines (decided with the user); 4CA0163 04 excluded above
def s21_model(fit, fg):
    a_np = fit.alpha_dB_cm(fg) * 100 / 8.686; b = 2 * np.pi * fg * 1e9 * fit.nm(fg) / C0
    g = (a_np + 1j * b) * L_MM * 1e-3; zc = fit.Zc(fg)
    return 2 / (2 * np.cosh(g) + (zc / Z_REF + Z_REF / zc) * np.sinh(g))
zb = (f >= ZB[0]) & (f <= ZB[1])
FOM = ["n_m @ 60 GHz", "Re Z0 (ohm), 10-43 GHz avg", "alpha (dB/cm) @ 30 GHz", "alpha (dB/cm) @ 60 GHz",
       "|S21| (dB) @ 30 GHz", "|S21| (dB) @ 60 GHz"]
V = {s: {} for s in STATES}
for s in STATES:
    for nn in lines:
        fit = data[s][nn]["fit"]
        V[s][nn] = dict(zip(FOM, [float(fit.nm(60.0)), float(np.mean(Q[s][nn]["Re Z0 (ohm)"][zb])),
                                  float(fit.alpha_dB_cm(30.0)), float(fit.alpha_dB_cm(60.0)),
                                  float(20 * np.log10(abs(s21_model(fit, 30.0)))), float(20 * np.log10(abs(s21_model(fit, 60.0))))]))
with open(os.path.join(OUT, "values_FOM.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["line", "state"] + FOM)
    for s in STATES:
        for nn in lines:
            w.writerow([nn, s] + [f"{V[s][nn][q]:.6g}" for q in FOM])
sets = {"all": lines}
if TOXIC.get(wafer):
    sets["without " + ",".join(TOXIC[wafer])] = [x for x in lines if x not in TOXIC[wafer]]
print("\nFigures of merit: median noALD -> ALD, median per-line change, lines up; outliers (median +- 3 MAD)")
with open(os.path.join(OUT, "summary_FOM.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["set", "n", "FOM", "median_noALD", "median_ALD", "median_change", "IQR_change_lo", "IQR_change_hi", "lines_up"])
    for sn, ls in sets.items():
        print(f"  [{sn}: {len(ls)} lines]")
        for q in FOM:
            a = np.array([V["noALD"][nn][q] for nn in ls]); b = np.array([V["ALD"][nn][q] for nn in ls]); d = b - a
            out = []
            for st, v in (("noALD", a), ("ALD", b)):
                mad = np.median(abs(v - np.median(v))) * 1.4826
                out += [f"{st} {ls[i]}" for i in np.where(abs(v - np.median(v)) > 3 * mad)[0]] if mad > 0 else []
            q1, q3 = np.percentile(d, [25, 75])
            print(f"    {q:28s} {np.median(a):9.4f} -> {np.median(b):9.4f}  change {np.median(d):+.4f} [{q1:+.4f},{q3:+.4f}]"
                  f"  up {np.sum(d > 0)}/{len(d)}  outliers: {', '.join(out) or 'none'}")
            w.writerow([sn, len(ls), q, f"{np.median(a):.6g}", f"{np.median(b):.6g}", f"{np.median(d):.6g}", f"{q1:.6g}", f"{q3:.6g}", int(np.sum(d > 0))])
fig, ax = plt.subplots(2, 3, figsize=(14, 8.4)); ax = ax.ravel()
for a, q in zip(ax, FOM):
    va = [V["noALD"][nn][q] for nn in lines]; vb = [V["ALD"][nn][q] for nn in lines]
    a.boxplot([va, vb], positions=[0, 1], widths=0.45, showfliers=False, medianprops=dict(color="k"))
    for nn, y0, y1 in zip(lines, va, vb):
        c = cmap(int(nn) / 14)
        a.plot([0, 1], [y0, y1], color=c, lw=0.8, alpha=0.7, zorder=1)
        a.scatter([0], [y0], color=c, marker="o", s=22, zorder=3, edgecolor="white", linewidth=0.5, label=nn)
        a.scatter([1], [y1], color=c, marker="s", s=22, zorder=3, edgecolor="white", linewidth=0.5)
    a.set_xticks([0, 1]); a.set_xticklabels(["no ALD (o)", "ALD (s)"]); a.set_title(q, fontsize=10.5); a.grid(alpha=0.3, axis="y")
ax[2].legend(fontsize=7, frameon=False, title="line", title_fontsize=8, loc="center left", bbox_to_anchor=(1.02, 0.5))
fig.suptitle(f"{wafer}: per-line figures of merit before and after 40 nm Al2O3 ({len(lines)} lines)", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "boxplots_FOM.png"), dpi=150); plt.close(fig)
old = os.path.join(OUT, "boxplots_60GHz.png")
if os.path.exists(old): os.remove(old)
old = os.path.join(OUT, "values_60GHz.csv")
if os.path.exists(old): os.remove(old)

# ---- line mean of the raw curves with the line mean of the per-line fits ----
def model_curve(fit, q, fg):
    if q == "n_m": return fit.nm(fg)
    if q == "Re Z0 (ohm)": return np.real(fit.Zc(fg))
    if q == "alpha (dB/cm)": return fit.alpha_dB_cm(fg)
    return 20 * np.log10(abs(s21_model(fit, fg)))
MQ = ["n_m", "Re Z0 (ohm)", "alpha (dB/cm)", "|S21| (dB)"]
def mean_fit(a, q, legend=True):
    for s in STATES:
        R = np.array([Q[s][nn][q] for nn in lines]).mean(0)
        a.plot(f, R, color=COL[s], lw=0.8, alpha=0.55, label=f"{s}: line mean (raw)")
        if q == "Re Z0 (ohm)":
            v = np.mean([V[s][nn][FOM[1]] for nn in lines])
            a.plot(ZB, [v, v], color=COL[s], lw=2.6, label=f"{s}: mean over 10-43 GHz = {v:.2f}")
        else:
            M = np.array([model_curve(data[s][nn]["fit"], q, f) for nn in lines]).mean(0)
            a.plot(f, M, color=COL[s], lw=2.2, ls="--", label=f"{s}: line mean of the fits")
            for fe in ((60.0,) if q == "n_m" else (30.0, 60.0)):
                i = np.argmin(abs(f - fe)); a.plot([f[i]], [M[i]], "o", color=COL[s], ms=6, mec="k", mew=0.6)
    a.set_ylim(*ylim(q)); a.set_xlabel("frequency (GHz)"); a.set_ylabel(q); a.grid(alpha=0.3)
    if legend: a.legend(frameon=False, fontsize=7.5)
for q in MQ:
    fig, a = plt.subplots(figsize=(8, 4.4)); mean_fit(a, q)
    a.set_title(f"{wafer}: {q}, mean over {len(lines)} lines; dots: evaluation points", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{fname[q]}_mean_fit.png"), dpi=150); plt.close(fig)
fig, ax = plt.subplots(2, 2, figsize=(12, 7.6))
for a, q in zip(ax.ravel(), MQ):
    mean_fit(a, q); a.set_title(q, fontsize=10.5)
fig.suptitle(f"{wafer}: mean over {len(lines)} lines, raw (thin) and fitted (thick); dots: values used in the boxplots", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "mean_fit_panel.png"), dpi=150); plt.close(fig)

# ---- per-line fitted curves (reference) ----
for q in MQ:
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)
    for a, s in zip(ax, STATES):
        for nn in lines:
            c = cmap(int(nn) / 14); fit = data[s][nn]["fit"]
            a.plot(f, Q[s][nn][q], color=c, lw=0.5, alpha=0.35)
            a.plot(f, model_curve(fit, q, f), color=c, lw=1.6, label=nn)
        a.set_title(f"{wafer}, {s}: raw (thin) and fitted (thick)", fontsize=10); a.set_xlabel("frequency (GHz)"); a.grid(alpha=0.3)
    ax[0].set_ylabel(q); ax[0].set_ylim(*ylim(q)); ax[1].legend(fontsize=6.5, ncol=3, frameon=False, title="line", title_fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"{fname[q]}_fits.png"), dpi=150); plt.close(fig)
print(f"\nfigures in {OUT}")
