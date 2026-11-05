"""
Which fit and which evaluation frequency give reliable figures of merit? Criteria fixed before computing (the
agreement between wafers is NOT a criterion):
 (a) stability: |value from a fit to <= 50 GHz - value from the full fit| at the evaluation frequency;
 (b) agreement with the data: raw median in a window around the evaluation frequency (fe +- 2 GHz; 56-60 GHz for 60)
     minus the fitted value;
 (c) the same behaviour in all four groups (2 wafers x noALD/ALD), including how often the extractor's automatic
     sign-constrained refit of alpha is triggered.
Lines excluded as in wafer_analysis.py (4CA0163 line 04, both states).
Models: alpha  A0 extractor (a sqrt f + b f + c, robust, refit with a, b >= 0 if a free coefficient is negative)
               A1 a sqrt f + b f + c, robust, unconstrained;  A2 a sqrt f + b f, robust (no constant)
        n_m    N0 extractor saturating model;  N1 n_inf + k / sqrt f + c f, robust
        Re Z0  Z0 extractor model (kept; only assessed)
All fits from 0.5 GHz. Output: fit_check.log.
"""
import os, sys, glob, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../..")))
import numpy as np
from mzm_interconnect.extractor import extract_line_fit, _robust_fit
from mzm_interconnect.physics import fit_alpha_scaled, fit_nm_saturating, fit_impedance_physical
EXCL = {"4CA0163": ["04"]}
FE = (20, 30, 40, 50, 60)
A1 = lambda f, a, b, c: a * np.sqrt(f) + b * f + c
A2 = lambda f, a, b: a * np.sqrt(f) + b * f
N1 = lambda f, n, k, c: n + k / np.sqrt(f) + c * f


def a0_fit(f, y):
    p, _ = _robust_fit(fit_alpha_scaled, f, y); con = bool(p[0] < 0 or p[1] < 0)
    if con:
        p, _ = _robust_fit(fit_alpha_scaled, f, y, bounds=([0, 0, -np.inf], [np.inf, np.inf, np.inf]))
    return (lambda x: fit_alpha_scaled(x, *p)), con, p


def fitter(name, f, y):
    if name == "A0": return a0_fit(f, y)[0]
    if name == "A1": p, _ = _robust_fit(A1, f, y); return lambda x: A1(x, *p)
    if name == "A2": p, _ = _robust_fit(A2, f, y); return lambda x: A2(x, *p)
    if name == "N0":
        fm = float(f.max())
        p, _ = _robust_fit(fit_nm_saturating, f, y, p0=(float(np.median(y)), 0.01, min(30.0, fm)),
                           bounds=([1.0, -1.0, 1e-3], [10.0, 1.0, fm]), maxfev=80000)
        return lambda x: fit_nm_saturating(x, *p)
    if name == "N1": p, _ = _robust_fit(N1, f, y, p0=(2.2, 0.2, 0.0)); return lambda x: N1(x, *p)
    if name == "Z0": p, _ = _robust_fit(fit_impedance_physical, f, y); return lambda x: fit_impedance_physical(x, *p)


def window(f, fe):
    return (f >= 56) & (f <= 60) if fe >= 60 else (f >= fe - 2) & (f <= fe + 2)


rows = {}; constrained = {}
for w in ("4CA0162", "4CA0163"):
    for fn in sorted(glob.glob(os.path.join(HERE, "raw", w, f"{w}_*_*.s2p"))):
        m = re.search(r"_(noALD|ALD)_(\d{2})\.s2p$", fn); s, nn = m.group(1), m.group(2)
        if nn in EXCL.get(w, []):
            continue
        ft = extract_line_fit(fn, 8.0); f = ft.raw_f_GHz
        Y = {"alpha": ft.raw_alpha_dB_cm, "n_m": ft.raw_nm, "Re Z0": np.real(ft.raw_Zc)}
        constrained.setdefault((w, s), []).append(a0_fit(f, Y["alpha"])[1])
        for q, models in (("alpha", ("A0", "A1", "A2")), ("n_m", ("N0", "N1")), ("Re Z0", ("Z0",))):
            for mo in models:
                full = fitter(mo, f, Y[q]); trunc = fitter(mo, f[f <= 50], Y[q][f <= 50])
                for fe in FE:
                    rows.setdefault((q, mo, fe, w, s), []).append(
                        (float(full(fe)), abs(float(trunc(fe) - full(fe))), float(np.median(Y[q][window(f, fe)]) - full(fe)), nn))

print("Automatic sign-constrained alpha refit (A0) triggered, per group:")
for k, v in constrained.items():
    print(f"  {k[0]} {k[1]:5s}: {sum(v)}/{len(v)}")
groups = [(w, s) for w in ("4CA0162", "4CA0163") for s in ("noALD", "ALD")]
for q, models, unit in (("alpha", ("A0", "A1", "A2"), "dB/cm"), ("n_m", ("N0", "N1"), ""), ("Re Z0", ("Z0",), "ohm")):
    print(f"\n=== {q} ({unit}): per group  stability (a) median | bias (b) median [IQR]  ===")
    for mo in models:
        for fe in FE:
            line = f"  {mo} @{fe:2d}:"
            for g in groups:
                r = rows[(q, mo, fe) + g]; st = np.median([x[1] for x in r]); b = [x[2] for x in r]
                line += f" | {g[0][-1]}{g[1][:2]} {st:6.3f} {np.median(b):+6.3f} [{np.percentile(b, 25):+.3f},{np.percentile(b, 75):+.3f}]"
            print(line)
print("\n=== per-line change ALD - noALD, median over lines (for information; not a selection criterion) ===")
for q, models in (("alpha", ("A0", "A1", "A2")), ("n_m", ("N0", "N1")), ("Re Z0", ("Z0",))):
    for mo in models:
        for fe in FE:
            line = f"  {q:5s} {mo} @{fe:2d}:"
            for w in ("4CA0162", "4CA0163"):
                a = {x[3]: x[0] for x in rows[(q, mo, fe, w, "noALD")]}; b = {x[3]: x[0] for x in rows[(q, mo, fe, w, "ALD")]}
                d = [b[k] - a[k] for k in a]
                line += f"  {w}: {np.median(d):+.4f} ({sum(x > 0 for x in d)}/{len(d)} up)"
            print(line)
