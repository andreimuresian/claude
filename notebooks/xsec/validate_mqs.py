"""Checks of the gold-interior solve (mqs2d.py = notebook v2 cell [6]).

1. DC limit: at 1 kHz R' must equal the exact R_dc = 1/(sigma A_sig) + 1/(2 sigma A_gnd).
2. Exact skin effect: a round gold wire inside a PEC tube (coax), same equations,
   same P2 elements and same surface cell (0.03 um), against the Bessel solution
       Z = gamma I0(gamma a) / (2 pi a sigma I1(gamma a)) + j w mu0 ln(b/a) / (2 pi).
3. Mesh and box convergence on row 86, section C (the notebook's geometry).
4. Rows 49, 118, 408, section C: gold-interior R' against the notebook's IBC
   contour integral (conv_corner.json, notebook mesh) and against the converged
   sharp-corner IBC value (Wheeler, central difference, electrodes in free space).
Run: python validate_mqs.py      (-> validate_mqs.json, validate_mqs.txt)
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import json
import sys
import warnings
from multiprocessing import Pool

import numpy as np
from scipy.special import ive
from skfem import MeshTri

import mqs2d as q

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
ROW86 = dict(WS=8.749, GAP=14.422, MTX=9.136)            # notebook cell [0]
VARIANTS = {"notebook mesh": {}, "hfine 0.06": dict(hfine=0.06), "hfine 0.015": dict(hfine=0.015),
            "hmax_metal 0.25": dict(hmax_metal=0.25), "grading 1.08": dict(grow=1.08),
            "box 1200": dict(box=1200.0)}
DELTA = np.sqrt(2.0 / (2 * np.pi * q.F0 * q.MU0 * q.SIGMA_AU)) / q.UM


def cpw(WS, GAP, MTX, **kw):
    x_gi = WS / 2 + GAP
    return q.section(WS, MTX, [(x_gi, x_gi + 70.0, "gnd")], "float", **kw)


def coax(a, b=50.0, f=q.F0, N=256, hfine=q.HFINE):
    r = np.unique(np.concatenate([q.graded(0.0, a, 0.5, hfine, 0.5), q.graded(a, b, hfine, 2.0, 2.0)]))[1:]
    th = 2 * np.pi * np.arange(N) / N
    P = np.hstack([[[0.0], [0.0]], np.vstack([np.outer(r, np.cos(th)).ravel(), np.outer(r, np.sin(th)).ravel()])])
    idx = lambda i, j: 1 + i * N + (j % N)
    T = [(0, idx(0, j), idx(0, j + 1)) for j in range(N)]
    for i in range(len(r) - 1):
        for j in range(N):
            T += [(idx(i, j), idx(i + 1, j), idx(i + 1, j + 1)), (idx(i, j), idx(i + 1, j + 1), idx(i, j + 1))]
    m = MeshTri(P * q.UM, np.array(T).T)
    rc = np.hypot(*m.p[:, m.t].mean(axis=1)) / q.UM
    cond = (rc < a).astype(int)
    rb = b * np.cos(np.pi / N) * q.UM * (1 - 1e-6)
    out = q.solve_mqs(m, cond, [[1]], np.array([1.0]), f, dirichlet=lambda X: np.hypot(X[0], X[1]) > rb)
    return out, m.nelements


def coax_exact(a, b=50.0, f=q.F0, sigma=q.SIGMA_AU):
    w = 2 * np.pi * f
    g = np.sqrt(1j * w * q.MU0 * sigma)
    ga = g * a * q.UM
    Zi = g / (2 * np.pi * a * q.UM * sigma) * ive(0, ga) / ive(1, ga)
    return Zi.real, Zi.imag / w, q.MU0 * np.log(b / a) / (2 * np.pi)


def job(a):
    kind = a[0]
    if kind == "dc":
        return a, cpw(**ROW86, f=1e3)
    if kind == "conv":
        return a, cpw(**ROW86, **VARIANTS[a[1]])
    if kind == "coax":
        o, nel = coax(a[1])
        return a, dict(o, n_el=nel)
    if kind == "row":
        from average import load_rows
        r = load_rows().loc[a[1]]
        return a, cpw(r.WS, r.GAP, r.MTX)
    if kind == "wheeler":
        import wheeler_verify as wv
        from average import load_rows
        r = load_rows().loc[a[1]] if a[1] != 86 else type("R", (), ROW86)
        S, Rc, n = wv.solve_air(r, 0.0, a[2], 0.025)
        return a, dict(Cair_eps0=S, Rc=Rc, n_el=n)


def main():
    jobs = [("conv", v) for v in VARIANTS] + [("dc",), ("coax", 5.0), ("coax", 1.0)]
    jobs += [("row", r) for r in (49, 118, 408)]
    jobs += [("wheeler", r, s * DELTA / 8) for r in (86, 49, 118, 408) for s in (1, -1)]
    res = {}
    with Pool(4, maxtasksperchild=1) as p:
        for k, v in p.imap_unordered(job, jobs):
            res[json.dumps(k)] = {kk: (float(vv) if np.isscalar(vv) else vv) for kk, vv in v.items()}
            print("   done", k, file=sys.stderr, flush=True)
    json.dump(res, open(os.path.join(HERE, "validate_mqs.json"), "w"), indent=1)
    report(res)


def report(res):
    g = lambda *k: res[json.dumps(list(k))]
    w = 2 * np.pi * q.F0
    print("1. DC limit, row 86 (notebook geometry), f = 1 kHz")
    o = g("dc")
    Rdc = 1 / (q.SIGMA_AU * ROW86["WS"] * ROW86["MTX"] * q.UM ** 2) + 0.5 / (q.SIGMA_AU * 70.0 * ROW86["MTX"] * q.UM ** 2)
    print(f"   R' {o['R']:.4f}  exact R_dc {Rdc:.4f} ohm/m  ({(o['R'] / Rdc - 1) * 100:+.4f}%)")
    print("\n2. Round gold wire in a PEC tube (b = 50 um), 60 GHz, vs the exact Bessel solution")
    for a in (5.0, 1.0):
        o, (Re, Li, Le) = g("coax", a), coax_exact(a)
        print(f"   a = {a} um ({o['n_el']:.0f} el): R' {o['R']:9.2f} vs {Re:9.2f} ({(o['R'] / Re - 1) * 100:+.3f}%)"
              f"   L_int {(o['L'] - o['L_ext']) * 1e9:.4f} vs {Li * 1e9:.4f} nH/m ({((o['L'] - o['L_ext']) / Li - 1) * 100:+.3f}%)"
              f"   L_ext {(o['L_ext'] / Le - 1) * 100:+.4f}%")
    print("\n3. Row 86 section C: mesh and box (notebook cell [6] = first line)")
    print(f"   {'':16} {'DOF':>7} {'R_ohm/m':>9} {'L_int nH/m':>10} {'wL_int/R':>8} | notebook: {'L_int_box':>9} {'box share':>9}")
    b0 = g("conv", "notebook mesh")
    for v in VARIANTS:
        o = g("conv", v)
        print(f"   {v:16} {o['ndof']:7.0f} {o['R']:9.2f} {o['L_int'] * 1e9:10.4f} {w * o['L_int'] / o['R']:8.4f} |"
              f"           {o['L_int_box'] * 1e9:9.4f} {o['box_share'] * 100:8.2f}%"
              + ("" if v == "notebook mesh" else f"   R' {(o['R'] / b0['R'] - 1) * 100:+.3f}%  L_int {(o['L_int'] / b0['L_int'] - 1) * 100:+.2f}%"))
    print("\n4. Section C, gold interior vs IBC: notebook contour integral (notebook mesh) and its")
    print("   converged sharp-corner value (Wheeler, central difference, electrodes in free space)")
    cc = {(d["row"], d["cf"]): d["R"] for d in json.load(open(os.path.join(HERE, "conv_corner.json")))}
    nb86 = 3157.9440                                            # notebook v2 cell [4] output, row 86
    for row in (86, 49, 118, 408):
        o = b0 if row == 86 else g("row", row)
        L = {s: 1 / (299792458.0 ** 2 * 8.8541878128e-12 * g("wheeler", row, s * DELTA / 8)["Cair_eps0"]) for s in (1, -1)}
        Rw = 1 / (q.SIGMA_AU * DELTA * q.UM) * (L[1] - L[-1]) / (q.MU0 * 2 * DELTA / 8 * q.UM)
        Rn = nb86 if row == 86 else cc[(row, 1.0)]
        print(f"   row {row:3d}: gold {o['R']:7.1f} | IBC notebook mesh {Rn:7.1f} (gold {(o['R'] / Rn - 1) * 100:+5.1f}%)"
              f" | IBC converged (Wheeler) {Rw:7.1f} (gold {(o['R'] / Rw - 1) * 100:+5.1f}%) | wL_int/R {w * o['L_int'] / o['R']:.3f}")


if __name__ == "__main__":
    if sys.argv[1:] == ["report"]:
        report(json.load(open(os.path.join(HERE, "validate_mqs.json"))))
    else:
        main()
