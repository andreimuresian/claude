"""Simplified figures for both wafers (out_<wafer>/v2_*.png):
 - v2_box_n_m.png, v2_box_Z0.png: boxplots of the per-line values (n_m at 60 GHz from the fit; Re Z0 averaged over
   10.0-42.8 GHz), no ALD vs ALD, every line a black dot, no pairing lines (from out_<wafer>/values_FOM.csv);
 - v2_S11.png, v2_S21.png: line mean of the measured |S| (dB) and line mean of the per-line fitted-line |S| (alpha,
   n_m, Zc fits, L = 8 mm, 50 ohm ends), no ALD and ALD in one graph.
Lines excluded as in wafer_analysis.py (4CA0163 line 04)."""
import os, sys, glob, re, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect.extractor import extract_line_fit
from mzm_interconnect.physics import C0
EXCL = {"4CA0163": ["04"]}; L = 8e-3; ZR = 50.0
YS = {"n_m": (2.20, 2.35, 0.01), "Z0": (40.0, 45.0, 0.5)}     # common axes for both wafers (user)
COL = {"noALD": "#2a78d6", "ALD": "#eb6834"}; LAB = {"noALD": "no ALD", "ALD": "ALD"}
def s_model(fit, f):
    a = fit.alpha_dB_cm(f) * 100 / 8.686; b = 2 * np.pi * f * 1e9 * fit.nm(f) / C0; g = (a + 1j * b) * L; zc = fit.Zc(f)
    den = 2 * zc * ZR * np.cosh(g) + (zc ** 2 + ZR ** 2) * np.sinh(g)
    return (zc ** 2 - ZR ** 2) * np.sinh(g) / den, 2 * zc * ZR / den
for w in ("4CA0162", "4CA0163"):
    out = os.path.join(HERE, f"out_{w}")
    rows = list(csv.DictReader(open(os.path.join(out, "values_FOM.csv"))))
    for key, col, ylab in (("n_m", "n_m @ 60 GHz", "n_m at 60 GHz (fit)"), ("Z0", "Re Z0 (ohm), 10-43 GHz avg", "Re Z0 (ohm), mean 10-43 GHz")):
        v = {s: [float(r[col]) for r in rows if r["state"] == s] for s in ("noALD", "ALD")}
        fig, ax = plt.subplots(figsize=(4.6, 4.6))
        ax.boxplot([v["noALD"], v["ALD"]], positions=[0, 1], widths=0.5, showfliers=False, medianprops=dict(color="k"))
        rng = np.random.default_rng(1)
        for i, s in enumerate(("noALD", "ALD")):
            ax.scatter(i + rng.uniform(-0.08, 0.08, len(v[s])), v[s], color="k", s=14, zorder=3)
        ax.set_xticks([0, 1]); ax.set_xticklabels(["no ALD", "ALD"]); ax.set_ylabel(ylab); ax.grid(alpha=0.3, axis="y")
        lo, hi, st = YS[key]; ax.set_ylim(lo, hi); ax.set_yticks(np.round(np.arange(lo, hi + st / 2, st), 3))
        ax.set_title(f"{w}: {ylab.split(' (')[0].split(' at')[0]} ({len(v['noALD'])} lines)", fontsize=10)
        fig.tight_layout(); fig.savefig(os.path.join(out, f"v2_box_{key}.png"), dpi=150); plt.close(fig)
    curves = {s: {"S11": [], "S21": [], "S11f": [], "S21f": []} for s in ("noALD", "ALD")}
    for fn in sorted(glob.glob(os.path.join(HERE, "raw", w, f"{w}_*_*.s2p"))):
        m = re.search(r"_(noALD|ALD)_(\d{2})\.s2p$", fn); s, nn = m.group(1), m.group(2)
        if nn in EXCL.get(w, []): continue
        net = rf.Network(fn); fit = extract_line_fit(fn, 8.0); f = fit.raw_f_GHz; sel = net.f / 1e9 > 0.5
        s11m, s21m = s_model(fit, f)
        fall = net.f / 1e9
        curves[s]["S11"].append(20 * np.log10(abs(net.s[:, 0, 0]))); curves[s]["S21"].append(20 * np.log10(abs(net.s[:, 1, 0])))
        curves[s]["S11f"].append(20 * np.log10(abs(s11m))); curves[s]["S21f"].append(20 * np.log10(abs(s21m)))
    for q in ("S11", "S21"):
        fig, ax = plt.subplots(figsize=(8, 4.4))
        for s in ("noALD", "ALD"):
            n = len(curves[s][q])
            ax.plot(fall, np.mean(curves[s][q], 0), color=COL[s], lw=0.8, alpha=0.6, label=f"{LAB[s]}: measured, mean of {n} lines")
            ax.plot(f, np.mean(curves[s][q + "f"], 0), color=COL[s], lw=2.2, ls="--", label=f"{LAB[s]}: fitted line, mean of {n} lines")
        ax.set_xlabel("frequency (GHz)"); ax.set_ylabel(f"|{q}| (dB)"); ax.grid(alpha=0.3); ax.legend(frameon=False, fontsize=8)
        if q == "S21": ax.set_ylim(-6.5, 0)
        else: ax.set_ylim(-32.5, 0)
        ax.set_title(f"{w}: |{q}|, measured vs fitted line (alpha, n_m, Z_c fits; 50 ohm ends)", fontsize=10)
        fig.tight_layout(); fig.savefig(os.path.join(out, f"v2_{q}.png"), dpi=150); plt.close(fig)
    print(w, "done")

# both wafers in one figure: n_m and Z0, four boxes each
fig, ax = plt.subplots(1, 2, figsize=(10, 4.8))
for a, (key, col, ylab) in zip(ax, (("n_m", "n_m @ 60 GHz", "n_m at 60 GHz (fit)"), ("Z0", "Re Z0 (ohm), 10-43 GHz avg", "Re Z0 (ohm), mean 10-43 GHz"))):
    groups, labels = [], []
    for w in ("4CA0162", "4CA0163"):
        rows = list(csv.DictReader(open(os.path.join(HERE, f"out_{w}", "values_FOM.csv"))))
        for s_ in ("noALD", "ALD"):
            groups.append([float(r[col]) for r in rows if r["state"] == s_]); labels.append(f"{w}\n{LAB[s_]}")
    pos = [0, 1, 2.6, 3.6]
    a.boxplot(groups, positions=pos, widths=0.5, showfliers=False, medianprops=dict(color="k"))
    rng = np.random.default_rng(1)
    for p, g in zip(pos, groups):
        a.scatter(p + rng.uniform(-0.08, 0.08, len(g)), g, color="k", s=12, zorder=3)
    a.set_xticks(pos); a.set_xticklabels(labels, fontsize=8.5); a.set_ylabel(ylab); a.grid(alpha=0.3, axis="y")
    lo, hi, st = YS[key]; a.set_ylim(lo, hi); a.set_yticks(np.round(np.arange(lo, hi + st / 2, st), 3))
    a.set_title(ylab.split(" (")[0].split(" at")[0] + ": both wafers", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "v2_box_both_wafers.png"), dpi=150); plt.close(fig)
