"""Row 49: the author's CST multilayer runs (gold and PEC electrodes; 400 and 600 um
lines, with and without tees; 20, 60, 100 GHz) against the 3D quasi-static cell.

Extraction exactly as the author's alpha extractor (Touchstone_extractor.py):
    A = ((1 + S11)(1 - S22) + S12 S21) / (2 S21),  alpha L = |Re acosh A|
    alpha per cell = (alpha L(600) - alpha L(400)) / 0.02 cm * 8.686   [dB/cm]
    d_alpha = alpha(tee) - alpha(no tee)
n from the same subtraction of beta L (the branch with 1 < n < 4).
Line-line check (no assumption on the ends): with M = ABCD of each line,
M400 = E_a T^2 E_b and M600 = E_a T^3 E_b for identical end transitions E and
identical cells T, so M600 M400^-1 = E_a T E_a^-1 has the cell's eigenvalues,
cosh(gamma P) = tr(M600 M400^-1)/2, whatever E is.  The same model gives
E_a E_b = (M600 M400^-1)^-2 M400, which must be a passive 2-port.
Power check: with PEC metal, 1 - |S11|^2 - |S21|^2 is power that leaves the line
other than by conductor loss (radiation, or absorption in the lossy dielectrics).
The header parameters that differ (CAP_W, SI_H, AIR_H) are not geometry
differences (author): the multilayer model has no caps, and Si is 550 um in all
runs (hard-coded in the no-tee projects).
Run: python cst_row49.py      (-> cst_row49.txt)
"""
import cmath
import json
import math
import os
import re

import numpy as np

import loss as Lo

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "..", "mom", "data", "MULTILAYER SOLVER TOUCHSTONES")
C0 = 299792458.0


def read(path):
    unit, fmt, out, params = 1e9, "MA", {}, {}
    for line in open(path):
        s = line.strip()
        if s.startswith("! Parameters"):
            params = dict((k, float(v)) for k, v in re.findall(r"(\w+)=([-\d.eE+]+)", s))
        if not s or s.startswith("!"):
            continue
        if s.startswith("#"):
            t = s[1:].upper().split()
            unit, fmt = {"HZ": 1, "KHZ": 1e3, "MHZ": 1e6, "GHZ": 1e9}[t[0]], t[2]
            continue
        p = [float(v) for v in s.split()]

        def c(a, b):
            if fmt == "MA":
                return cmath.rect(a, math.radians(b))
            if fmt == "DB":
                return cmath.rect(10**(a/20), math.radians(b))
            return complex(a, b)
        out[p[0]*unit] = [c(p[1 + 2*k], p[2 + 2*k]) for k in range(4)]     # S11 S21 S12 S22
    return out, params


def gamma_l(S, f, L):
    S11, S21, S12, S22 = S
    g = cmath.acosh(((1 + S11)*(1 - S22) + S12*S21)/(2*S21))
    g = g if g.real >= 0 else -g
    return g.real, [s*g.imag + 2*math.pi*k for s in (1, -1) for k in range(-3, 6)]


def abcd(S, Z0=50.0):
    S11, S21, S12, S22 = S
    d = 2*S21
    return np.array([[((1 + S11)*(1 - S22) + S12*S21)/d, Z0*((1 + S11)*(1 + S22) - S12*S21)/d],
                     [((1 - S11)*(1 - S22) - S12*S21)/(Z0*d), ((1 - S11)*(1 + S22) + S12*S21)/d]])


def s_of(M, Z0=50.0):
    A, B, C, D = M.ravel()
    den = A + B/Z0 + C*Z0 + D
    return np.array([[(A + B/Z0 - C*Z0 - D)/den, 2*(A*D - B*C)/den],
                     [2/den, (-A + B/Z0 - C*Z0 + D)/den]])


def line_line(S4, S6, f):
    """Per-cell alpha [dB/cm] and n from the eigenvalues of M600 M400^-1, and the
    joined end transitions K = E_a E_b with its largest singular value (> 1: active)."""
    M4, M6 = abcd(S4), abcd(S6)
    T = M6 @ np.linalg.inv(M4)
    g = cmath.acosh(np.trace(T)/2)
    g = g if g.real >= 0 else -g
    k = 2*math.pi*f/C0*200e-6
    n = sorted(x for x in ((s*g.imag + 2*math.pi*j)/k for s in (1, -1) for j in range(-3, 6)) if 1 < x < 4)
    K = np.linalg.inv(T @ T) @ M4
    SK = s_of(K)
    return g.real/0.02*8.686, n[0], np.linalg.svd(SK, compute_uv=False)[0], \
        100*(1 - abs(SK[0, 0])**2 - abs(SK[1, 0])**2)


def per_cell(d4, d6, f):
    a4, b4 = gamma_l(d4[f], f, 400e-6)
    a6, b6 = gamma_l(d6[f], f, 600e-6)
    k = 2*math.pi*f/C0*200e-6
    ns = sorted({(y - x)/k for x in b4 for y in b6 if 1.0 < (y - x)/k < 4.0})
    return (a6 - a4)/0.02*8.686, ns


def main():
    D, P = {}, {}
    for m in ("GOLD", "PEC"):
        for t in ("TEE", "NO TEE"):
            for L in (400, 600):
                D[(m, t, L)], P[(m, t, L)] = read(os.path.join(DIR, f"{L} {t} {m}.s2p"))
    freqs = sorted(D[("GOLD", "TEE", 400)])
    o49 = json.load(open(os.path.join(HERE, "run_loss.json")))["49|base"]
    f3 = Lo.factors(o49["u"], o49["e"])

    print("1. Header parameters that differ (mm; not geometry differences: no caps in the model, Si 550 um in all runs)")
    keys = sorted(set().union(*[p.keys() for p in P.values()]))
    for k in keys:
        vals = {key: P[key].get(k) for key in P}
        if len(set(vals.values())) > 1:
            print(f"   {k}: " + ", ".join(f"{t} {L}: {v}" for (m, t, L), v in vals.items() if m == "GOLD"))

    print("\n2. Per cell, 600 um - 400 um (author's extractor)")
    print(f"   {'metal':5} {'GHz':>4} | {'a tee':>7} {'a no tee':>8} {'d_alpha':>8} {'ratio':>6} | {'n tee':>6} {'n no tee':>8} {'ratio':>6}")
    res = {}
    for m in ("GOLD", "PEC"):
        for f in freqs:
            ae, ne = per_cell(D[(m, "TEE", 400)], D[(m, "TEE", 600)], f)
            au, nu = per_cell(D[(m, "NO TEE", 400)], D[(m, "NO TEE", 600)], f)
            res[(m, f)] = (ae, au, ne[0], nu[0])
            print(f"   {m:5} {f/1e9:4.0f} | {ae:7.3f} {au:8.3f} {ae - au:+8.3f} {ae/au:6.2f} | {ne[0]:6.3f} {nu[0]:8.3f} {ne[0]/nu[0]:6.4f}")
    print(f"   dataset row 49 at 60 GHz: d_alpha {8.290146:+.3f} dB/cm")
    print(f"   3D quasi-static cell (frequency-independent): alpha ratio {f3['F_alpha']:.3f}, n ratio {f3['F_n']:.4f}")

    print("\n3. Power not returned, 1 - |S11|^2 - |S21|^2 (%)")
    for m in ("PEC", "GOLD"):
        for t in ("TEE", "NO TEE"):
            for L in (400, 600):
                d = D[(m, t, L)]
                print(f"   {m:4} {t:6} {L} um: " + "  ".join(
                    f"{f/1e9:3.0f} GHz {100*(1 - abs(S[0])**2 - abs(S[1])**2):7.3f}" for f, S in sorted(d.items())))

    print("\n4. Line-line: per-cell alpha and n from the eigenvalues of M600 M400^-1 (independent of the end transitions),")
    print("   and the joined end transitions K = E_a E_b this implies (passive <=> sigma_max <= 1, power lost >= 0)")
    print(f"   {'metal':5} {'':6} {'GHz':>4} | {'alpha':>7} {'author':>7} | {'n':>6} | {'sigma_max K':>11} {'lost in K %':>11}")
    for m in ("GOLD", "PEC"):
        for t in ("TEE", "NO TEE"):
            for f in freqs:
                a, n, sv, lk = line_line(D[(m, t, 400)][f], D[(m, t, 600)][f], f)
                aa = per_cell(D[(m, t, 400)], D[(m, t, 600)], f)[0]
                print(f"   {m:5} {t:6} {f/1e9:4.0f} | {a:7.3f} {aa:7.3f} | {n:6.3f} | {sv:11.4f} {lk:+11.3f}")


if __name__ == "__main__":
    main()
