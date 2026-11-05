"""
Why does ALD raise the attenuation on 4CA0162 (+0.21 dB/cm at 60 GHz) but lower it on 4CA0163 (-0.06)?
Per wafer, over the paired lines (bad ones excluded as in wafer_analysis.py):
 1. per-line raw delta alpha(f) = alpha_ALD - alpha_noALD, median over lines, smoothed (1 GHz running median);
 2. delta of the fitted alpha components a sqrt(f), b f, c (conductor-like, dielectric-like, constant) at 60 GHz;
 3. delta n_m and delta Re Z0 (raw, 5-50 GHz mean): the dielectric loading by ALD, as a reference;
 4. pad/probe mismatch: Z0 ripple (std of raw Re Z0 minus its fit, 15-50 GHz) and mean |S11| (dB, 5-50 GHz), before
    and after;
 5. delta |S21| at low frequency (1-5 GHz), where the line loss is small and contact effects show.
Output: alpha_sign.png, alpha_sign.log.
"""
import os, sys, glob, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.ndimage import median_filter
from mzm_interconnect.extractor import extract_line_fit
EXCL = {"4CA0163": ["04"]}
res = {}
for w in ("4CA0162", "4CA0163"):
    D = {}
    for fn in sorted(glob.glob(os.path.join(HERE, "raw", w, f"{w}_*_*.s2p"))):
        m = re.search(r"_(noALD|ALD)_(\d{2})\.s2p$", fn); s, nn = m.group(1), m.group(2)
        if nn in EXCL.get(w, []):
            continue
        D.setdefault(nn, {})[s] = (extract_line_fit(fn, 8.0), rf.Network(fn))
    lines = sorted(k for k in D if len(D[k]) == 2)
    f = D[lines[0]]["noALD"][0].raw_f_GHz; k = int(round(1.0 / np.median(np.diff(f))))
    out = {"f": f, "lines": lines, "dalpha": [], "comp": [], "dn": [], "dz": [], "rip": [], "s11": [], "s21lo": []}
    for nn in lines:
        (fa, na), (fb, nb) = D[nn]["noALD"], D[nn]["ALD"]
        out["dalpha"].append(median_filter(fb.raw_alpha_dB_cm - fa.raw_alpha_dB_cm, size=k))
        comp = lambda p, x: np.array([p[0] * np.sqrt(x), p[1] * x, p[2]])
        out["comp"].append(comp(fb.popt_alpha, 60.0) - comp(fa.popt_alpha, 60.0))
        band = (f >= 5) & (f <= 50)
        out["dn"].append(np.mean(fb.raw_nm[band] - fa.raw_nm[band])); out["dz"].append(np.mean(np.real(fb.raw_Zc[band] - fa.raw_Zc[band])))
        rb = (f >= 15) & (f <= 50)
        rip = lambda ft: np.std(np.real(ft.raw_Zc[rb]) - np.real(ft.Zc(f[rb])))
        out["rip"].append((rip(fa), rip(fb)))
        s11 = lambda n: np.mean(20 * np.log10(abs(n.s[(n.f >= 5e9) & (n.f <= 50e9), 0, 0])))
        out["s11"].append((s11(na), s11(nb)))
        lo = lambda n: np.mean(20 * np.log10(abs(n.s[(n.f >= 1e9) & (n.f <= 5e9), 1, 0])))
        out["s21lo"].append(lo(nb) - lo(na))
    res[w] = out
    A = np.array(out["dalpha"]); C = np.array(out["comp"]); R = np.array(out["rip"]); S = np.array(out["s11"])
    print(f"\n{w} ({len(lines)} lines)")
    for fq in (2, 5, 10, 20, 30, 40, 50, 58):
        i = np.argmin(abs(f - fq)); print(f"  delta alpha at {fq:2d} GHz: median {np.median(A[:, i]):+.3f} dB/cm, lines up {np.sum(A[:, i] > 0)}/{len(lines)}")
    print(f"  delta of fitted components at 60 GHz (median): a sqrt(f) {np.median(C[:, 0]):+.3f}, b f {np.median(C[:, 1]):+.3f}, c {np.median(C[:, 2]):+.3f} dB/cm")
    print(f"  delta n_m (5-50 GHz mean): median {np.median(out['dn']):+.4f}; delta Re Z0: {np.median(out['dz']):+.3f} ohm")
    print(f"  Z0 ripple (std, 15-50 GHz): {np.median(R[:, 0]):.2f} -> {np.median(R[:, 1]):.2f} ohm; mean |S11| 5-50 GHz: {np.median(S[:, 0]):.2f} -> {np.median(S[:, 1]):.2f} dB")
    print(f"  delta |S21| 1-5 GHz: median {np.median(out['s21lo']):+.3f} dB, lines up {np.sum(np.array(out['s21lo']) > 0)}/{len(lines)}")
fig, ax = plt.subplots(figsize=(8.5, 4.6))
for w, c in (("4CA0162", "#eb6834"), ("4CA0163", "#2a78d6")):
    A = np.array(res[w]["dalpha"]); med = np.median(A, 0); q1, q3 = np.percentile(A, [25, 75], axis=0)
    ax.plot(res[w]["f"], med, color=c, lw=1.5, label=f"{w}: median over {A.shape[0]} lines")
    ax.fill_between(res[w]["f"], q1, q3, color=c, alpha=0.2, lw=0)
ax.axhline(0, color="0.4", lw=0.8); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("alpha(ALD) - alpha(no ALD) (dB/cm)")
ax.set_ylim(-0.8, 0.8); ax.grid(alpha=0.3); ax.legend(frameon=False, fontsize=8)
ax.set_title("Change of the de-embedded attenuation after ALD, per line (1 GHz running median); band: quartiles", fontsize=9.5)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "alpha_sign.png"), dpi=150)
