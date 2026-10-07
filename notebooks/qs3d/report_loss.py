"""Tables for step 1 (run_loss.json).  Run: python report_loss.py  (-> report_loss.txt)

Dataset convention (checked to 1e-8 on rows 49, 118, 130, 408):
    L_final = L_base + dL_lumped / P,   C_final = C_base + dC_lumped / P,
    alpha_final = alpha_base + alpha_delta,
dL, dC from one CST cell (Im B / w, Im C / w); alpha_delta = Re(gamma) per cell
from 2- and 3-cell CST lines (full wave).

3D quasi-static (this step):
    per-length factors  F = tee cell / no-slot cell  (L includes R'/w)
        n = n_base F_n,  Z0 = Z_base F_Z,  alpha = alpha_base F_alpha
    lumped convention   dL, dC from the cell's own slice cascade (qs3d README),
                        plus the internal-inductance change (R'_e - R'_u) P / w.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

import loss as Lo
import qs3d as q

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "xsec"))
import average as xa          # noqa: E402  (../xsec: 2D section average, for comparison)
import report_mqs as xr       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
D = pd.read_excel(os.path.join(HERE, '..', 'mom', 'data', 'EVALUATED_FULL_LHS_DATASET.xlsx'))
W2D = {49: 2520.9, 118: 2783.8, 408: 3134.2}          # ../xsec/validate_mqs.txt, 2D converged IBC
C0 = q.C0
_QS = json.load(open(os.path.join(HERE, "..", "xsec", "run_rows.json")))
_MQ = json.load(open(os.path.join(HERE, "..", "xsec", "run_mqs.json")))


def bloch_ratio(u, e):
    """Bloch index of the slice cascade over sqrt(L'C') (external L only)."""
    out = []
    for c in (u, e):
        Ls, Cs = np.array(c["ls"]), np.array(c["cs"])
        Ls = np.concatenate([Ls[::-1], Ls]); Cs = np.concatenate([Cs[::-1], Cs])
        M = np.eye(2, dtype=complex)
        for Lk, Ck in zip(Ls, Cs):
            th, Z = Lo.W*np.sqrt(Lk*Ck), np.sqrt(Lk/Ck)
            M = M @ np.array([[np.cos(th), 1j*Z*np.sin(th)], [1j*np.sin(th)/Z, np.cos(th)]])
        bP = np.arccos(((M[0, 0] + M[1, 1])/2).real)
        out.append(bP/(Lo.W*q.P*np.sqrt(c["L"]*c["C"])))
    return out[1]/out[0]


def da_2d(r, row):
    """d_alpha of the 2D section average (gold model, floating finger; ../xsec/report_mqs.py)."""
    qs = {s: _QS[f"{row}_{s}"]["qs"] for s in "ABC"}
    lines = {s: xr.lines_gold(qs[s], _MQ[f"{row}_{s}"], "float" if s == "B" else "gnd") for s in "ABC"}
    d = xa.combine(r, lines)
    return d["alpha"] - d["alphaC"]


def lumped_final(r, u, e):
    Lud, Cud = q.cell_abcd_lumped(np.array(u["ls"]), np.array(u["cs"]))
    Led, Ced = q.cell_abcd_lumped(np.array(e["ls"]), np.array(e["cs"]))
    dL = Led - Lud + (e["R_wh"] - u["R_wh"])/Lo.W*q.P
    dC = Ced - Cud
    Lb = r.z0_baseline_val*r.nm_baseline_val/C0; Cb = r.nm_baseline_val/(r.z0_baseline_val*C0)
    L, C = Lb + dL/q.P, Cb + dC/q.P
    return C0*np.sqrt(L*C), np.sqrt(L/C)


def main():
    res = json.load(open(os.path.join(HERE, "run_loss.json")))
    g = lambda row, var="base": res.get(f"{row}|{var}")
    gold = json.load(open(os.path.join(HERE, "..", "xsec", "run_mqs.json")))
    pct = lambda a, b: (a/b - 1)*100

    print("1. No-slot cell: 3D Wheeler R' vs the 2D converged IBC (xsec), and the 2D gold value")
    for row in (49, 118, 408):
        o = g(row)
        if o:
            u = o["u"]
            print(f"   row {row}: 3D Wheeler {u['R_wh']:7.1f}  2D Wheeler {W2D[row]:7.1f} ({pct(u['R_wh'], W2D[row]):+.1f}%)"
                  f"   3D surface integral {u['R_surf']:7.1f} ({pct(u['R_surf'], u['R_wh']):+.1f}%)"
                  f"   2D gold {gold[f'{row}_C']['R']:7.1f}")

    print("\n2. Grid and recession checks (tee factors)")
    print(f"   {'row':>4} {'variant':14} {'cells':>7} {'F_R':>7} {'F_alpha':>8} {'F_n':>7} {'F_Z':>7} {'F_R surf':>8}  s")
    for row in (49, 118):
        for var in ("base", "a/2", "hmin/2", "hz/2 h_near/2"):
            o = g(row, var)
            if not o:
                continue
            f, fs = Lo.factors(o["u"], o["e"]), Lo.factors(o["u"], o["e"], "R_surf")
            print(f"   {row:4d} {var:14} {o['e']['cells']/1e6:6.2f}M {f['F_R']:7.4f} {f['F_alpha']:8.4f} {f['F_n']:7.4f}"
                  f" {f['F_Z']:7.4f} {fs['F_R']:8.4f}  {o['sec']:.0f}")

    print("\n3. 14 rows: dataset (CST) vs 3D quasi-static")
    print("   F = final / baseline.  n, Z0: per-length factor (Bloch) and dataset lumped convention.")
    print("   d_alpha [dB/cm] on the COMSOL baseline: CST (alpha_delta) vs 3D ohmic, alpha_base (F_alpha - 1)")
    print(f"   {'row':>4} {'strip':>5} | {'F_n CST':>7} {'3D':>6} {'n err':>6} {'lump':>6} | {'F_Z CST':>7} {'3D':>6} {'Z err':>6} {'lump':>6} |"
          f" {'F_R 3D':>6} {'F_a 3D':>6} | {'da CST':>6} {'da 3D':>6} {'da 2D':>6} | bloch/hom")
    rows = sorted([int(k.split("|")[0]) for k in res if k.endswith("|base")],
                  key=lambda r: D.alpha_delta_val[r])
    E = []
    for row in rows:
        r, o = D.loc[row], g(row)
        f = Lo.factors(o["u"], o["e"])
        Fn, FZ = r.nm_final_val/r.nm_baseline_val, r.z0_final_val/r.z0_baseline_val
        nl, Zl = lumped_final(r, o["u"], o["e"])
        da3 = r.alpha_baseline_val*(f["F_alpha"] - 1)
        d2 = da_2d(r, row)
        E.append((pct(f["F_n"], Fn), pct(f["F_Z"], FZ), pct(nl, r.nm_final_val), pct(Zl, r.z0_final_val),
                  r.alpha_delta_val, da3))
        print(f"   {row:4d} {70 - r.W1 - r.W2:5.1f} | {Fn:7.3f} {f['F_n']:6.3f} {E[-1][0]:+5.1f}% {E[-1][2]:+5.1f}% |"
              f" {FZ:7.3f} {f['F_Z']:6.3f} {E[-1][1]:+5.1f}% {E[-1][3]:+5.1f}% | {f['F_R']:6.3f} {f['F_alpha']:6.3f} |"
              f" {r.alpha_delta_val:+6.2f} {da3:+6.2f} {d2:+6.2f} | {bloch_ratio(o['u'], o['e']):.4f}")
    E = np.array(E)
    print("   median / max |err|: n per-length {:.1f} / {:.1f} %, lumped {:.1f} / {:.1f} %;  Z0 per-length {:.1f} / {:.1f} %,"
          " lumped {:.1f} / {:.1f} %".format(*(f(np.abs(E[:, k])) for k in (0, 2, 1, 3) for f in (np.median, np.max))))
    big = E[:, 4] > 0.5
    print(f"   d_alpha: {(~big).sum()} rows with CST d_alpha <= +0.5: |3D - CST| median {np.median(np.abs(E[~big, 5] - E[~big, 4])):.2f},"
          f" max {np.abs(E[~big, 5] - E[~big, 4]).max():.2f} dB/cm")
    print(f"            {big.sum()} rows with CST d_alpha  > +0.5: 3D reproduces {np.median(E[big, 5]/E[big, 4])*100:.0f} % (median)"
          f" of it, range {(E[big, 5]/E[big, 4]).min()*100:.0f}-{(E[big, 5]/E[big, 4]).max()*100:.0f} %")


if __name__ == "__main__":
    main()
