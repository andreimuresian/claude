"""Conductor loss R': the notebook's contour integral vs Wheeler's rule.

The notebook computes R' = Rs * contour of (dV_air/dn)^2 / S^2 on the mesh.  At
the 90 deg electrode corners this integrand is singular (|E| ~ r^-1/3); the
integral is finite but the P1 mesh value approaches it very slowly (conv_corner.py:
+2..3 % per halving of the corner cell, still at 6 nm cells).

Wheeler's incremental-inductance rule gives the same quantity from C_air alone:
recede every metal face by a, R' = Rs (L(a) - L(0)) / (mu0 a), L = 1/(c^2 C_air).
C_air converges fast, so this is the converged R'.  Checks: two mesh levels and
two recessions (delta/8, delta/2), which must agree.
Run: python wheeler_check.py 49 118 408   (-> wheeler_check.json)
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import json
import sys
from multiprocessing import Pool

import xsec2d as x
from average import load_rows

HERE = os.path.dirname(os.path.abspath(__file__))
DELTA = x.skin_au * 1e6                      # um
RECS = [0.0, DELTA / 8, DELTA / 2]
LEVELS = [(1.0, 1.0), (0.5, 0.5)]            # notebook mesh, then 2x finer everywhere


def job(a):
    row, rec, mf, cf = a
    r = load_rows().loc[row]
    x_gi = r.WS / 2 + r.GAP
    s = x.Section(r.WS - 2 * rec, r.GAP + 2 * rec, r.MTX - 2 * rec, r.CAP_W, r.ETCH_DEPTH,
                  [(x_gi + rec, x_gi + 70.0 - rec, "gnd")], mf, cf)
    qs = s.quasi_static()
    return [row, rec, mf, cf, float(qs["Cair_gnd"]), float(qs["R_gnd"]), int(s.mesh.nelements)]


def main():
    rows = [int(v) for v in sys.argv[1:]] or [49, 118, 408]
    with Pool(4) as p:
        res = p.map(job, [(r, a, mf, cf) for r in rows for (mf, cf) in LEVELS for a in RECS])
    json.dump(res, open(os.path.join(HERE, "wheeler_check.json"), "w"), indent=1)
    get = {(r, a, mf): (Ca, R, n) for r, a, mf, cf, Ca, R, n in res}
    for row in rows:
        print(f"row {row}   (skin depth {DELTA:.3f} um)")
        for mf, cf in LEVELS:
            Ca0, Rc, n = get[(row, 0.0, mf)]
            L0 = 1 / (x.C0 ** 2 * Ca0)
            Rw = [x.Rs_au * (1 / (x.C0 ** 2 * get[(row, a, mf)][0]) - L0) / (x.MU0 * a * 1e-6) for a in RECS[1:]]
            print(f"  mesh {mf}/{cf} ({n:6d} el): contour integral R' {Rc:7.1f} | Wheeler R' {Rw[0]:7.1f} (delta/8) "
                  f"{Rw[1]:7.1f} (delta/2) ohm/m | contour vs Wheeler {(Rc / Rw[1] - 1) * 100:+.1f}%")


if __name__ == "__main__":
    main()
