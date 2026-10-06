"""Convergence rate of the conductor loss at the electrode corners.

Section C (the unslotted baseline) only; bulk mesh at the notebook default; the
corner and skin collars refined 1, 1/2, 1/4, 1/8 x the notebook (0.05 um corner
cells down to 0.00625 um).  Prints R' (= conductor loss, alpha_c ~ R'/2Z0) per
level, the successive differences, the observed rate p (difference ratio
= 2^p) and the Richardson limit R_inf = R_h + (R_h - R_2h)/(2^p - 1).
Run: python conv_corner.py 408 118 49   (-> conv_corner.json)
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import json
import sys
from multiprocessing import Pool

import numpy as np

import xsec2d as x
from average import load_rows

HERE = os.path.dirname(os.path.abspath(__file__))
CF = [1.0, 0.5, 0.25, 0.125]


def job(a):
    row, cf = a
    r = load_rows().loc[row]
    s = x.Section(r.WS, r.GAP, r.MTX, r.CAP_W, r.ETCH_DEPTH,
                  x.pieces_for("C", r.WS, r.GAP, r.W1, r.W2, r.L1, r.L2), 1.0, cf)
    qs = s.quasi_static()
    return row, cf, float(qs["R_gnd"]), int(s.mesh.nelements)


def main():
    rows = [int(a) for a in sys.argv[1:]] or [408, 118, 49]
    with Pool(4) as p:
        res = p.map(job, [(r, cf) for r in rows for cf in CF])
    json.dump([dict(row=r, cf=cf, R=R, nel=n) for r, cf, R, n in res],
              open(os.path.join(HERE, "conv_corner.json"), "w"), indent=1)
    D = load_rows()
    for row in rows:
        R = np.array([v[2] for v in res if v[0] == row])
        nel = [v[3] for v in res if v[0] == row]
        d = np.diff(R)
        p = np.log2(d[:-1] / d[1:])
        Rinf = R[-1] + d[-1] / (2 ** p[-1] - 1)
        print(f"row {row} (MTX {D.MTX[row]:.2f} um, GAP {D.GAP[row]:.2f} um)")
        for cf, Rv, n in zip(CF, R, nel):
            print(f"  corner cell {0.05*cf*1e3:5.2f} nm-scale x1e3 -> {0.05*cf:.5f} um  {n:7d} el  "
                  f"R' {Rv:8.1f} ohm/m  ({(Rv/R[-1]-1)*100:+.2f}% vs finest)")
        print(f"  successive increase: " + "  ".join(f"{v/R[0]*100:+.2f}%" for v in d)
              + f"   observed rate p: " + "  ".join(f"{v:.2f}" for v in p))
        print(f"  Richardson limit (last rate): R' {Rinf:.1f}  -> notebook mesh is "
              f"{(R[0]/Rinf-1)*100:+.1f}%, finest {(R[-1]/Rinf-1)*100:+.1f}%")


if __name__ == "__main__":
    main()
