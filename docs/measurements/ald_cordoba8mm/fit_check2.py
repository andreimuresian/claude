"""Follow-up to fit_check.py, same criteria. (1) alpha with the coefficients a, b >= 0 imposed on EVERY file (A3) vs the
free fit on every file (A1). (2) Re Z0 as a plain average of the raw curve over a band spanning whole ripple periods
(period c/(2 n L) ~ 8.2 GHz): 10.0-42.8 GHz (4 periods) and, as a robustness check, bands shifted by half a period
and one period shorter. Output: fit_check2.log."""
import os, sys, glob, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../..")))
import numpy as np
from mzm_interconnect.extractor import extract_line_fit, _robust_fit
from mzm_interconnect.physics import fit_alpha_scaled
EXCL = {"4CA0163": ["04"]}
A3fit = lambda f, y: _robust_fit(fit_alpha_scaled, f, y, bounds=([0, 0, -np.inf], [np.inf, np.inf, np.inf]))[0]
A1fit = lambda f, y: _robust_fit(fit_alpha_scaled, f, y)[0]
win = lambda f, fe: (f >= 56) & (f <= 60) if fe >= 60 else (f >= fe - 2) & (f <= fe + 2)
BANDS = {"10.0-42.8 (4 periods)": (10.0, 42.8), "14.1-46.9 (shift 1/2)": (14.1, 46.9), "10.0-34.6 (3 periods)": (10.0, 34.6)}
R = {}
for w in ("4CA0162", "4CA0163"):
    for fn in sorted(glob.glob(os.path.join(HERE, "raw", w, f"{w}_*_*.s2p"))):
        m = re.search(r"_(noALD|ALD)_(\d{2})\.s2p$", fn); s, nn = m.group(1), m.group(2)
        if nn in EXCL.get(w, []): continue
        ft = extract_line_fit(fn, 8.0); f = ft.raw_f_GHz; y = ft.raw_alpha_dB_cm; z = np.real(ft.raw_Zc)
        for name, fit in (("A1 free", A1fit), ("A3 a,b>=0", A3fit)):
            pf = fit(f, y); pt = fit(f[f <= 50], y[f <= 50]); act = bool(name.startswith("A3") and (pf[0] < 1e-9 or pf[1] < 1e-9))
            for fe in (30, 40, 60):
                v = fit_alpha_scaled(fe, *pf)
                R.setdefault(("alpha", name, fe, w, s), []).append((v, abs(fit_alpha_scaled(fe, *pt) - v), np.median(y[win(f, fe)]) - v, nn, act))
        for bn, (lo, hi) in BANDS.items():
            R.setdefault(("Z0", bn, 0, w, s), []).append((np.mean(z[(f >= lo) & (f <= hi)]), 0, 0, nn, False))
G = [(w, s) for w in ("4CA0162", "4CA0163") for s in ("noALD", "ALD")]
print("alpha: per group stability | bias (median), and how many fits sit on a bound (A3)")
for name in ("A1 free", "A3 a,b>=0"):
    for fe in (30, 40, 60):
        line = f"  {name:10s} @{fe}:"
        for g in G:
            r = R[("alpha", name, fe) + g]
            line += f" | {g[0][-1]}{g[1][:2]} {np.median([x[1] for x in r]):.3f} {np.median([x[2] for x in r]):+.3f} bnd {sum(x[4] for x in r)}"
        print(line)
print("\nper-line change ALD - noALD (information only)")
for key in [("alpha", n, fe) for n in ("A1 free", "A3 a,b>=0") for fe in (30, 40, 60)] + [("Z0", b, 0) for b in BANDS]:
    line = f"  {key[0]} {key[1]:22s} {key[2] or '':>3}:"
    for w in ("4CA0162", "4CA0163"):
        a = {x[3]: x[0] for x in R[key + (w, "noALD")]}; b = {x[3]: x[0] for x in R[key + (w, "ALD")]}
        d = [b[k] - a[k] for k in a]; lvl = np.median(list(a.values()))
        line += f"  {w}: noALD {lvl:7.3f}  change {np.median(d):+.3f} ({sum(x > 0 for x in d)}/{len(d)} up)"
    print(line)
