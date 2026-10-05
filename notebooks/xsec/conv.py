"""Mesh convergence of the section solves (quasi-static + IBC).

Levels (mesh_factor, corner_factor): the notebook default (1, 1), then the bulk
mesh refined (0.7, 1), (0.5, 1), then the corner/skin collars refined (0.5, 0.5).
For each row: per-section n, Z0, alpha and the weighted-average result, both
finger treatments.  Run: python conv.py 49 118 408   (-> conv.json)
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

import xsec2d as x
from average import average, load_rows

HERE = os.path.dirname(os.path.abspath(__file__))
LEVELS = [(1.0, 1.0), (0.7, 1.0), (0.5, 1.0), (0.5, 0.5)]


def job(a):
    row, sec, mf, cf = a
    r = load_rows().loc[row]
    t = time.time()
    s = x.Section(r.WS, r.GAP, r.MTX, r.CAP_W, r.ETCH_DEPTH,
                  x.pieces_for(sec, r.WS, r.GAP, r.W1, r.W2, r.L1, r.L2), mf, cf)
    qs = s.quasi_static()
    qs = {k: float(v) for k, v in qs.items()}
    qs.update(nel=int(s.mesh.nelements), t=time.time() - t)
    return row, sec, mf, cf, qs


def main():
    rows = [int(a) for a in sys.argv[1:]] or [49, 118, 408]
    jobs = [(r, s, mf, cf) for r in rows for (mf, cf) in LEVELS for s in "CAB"]
    with Pool(3) as p:
        res = p.map(job, jobs)
    out = {f"{r}_{s}_{mf}_{cf}": q for r, s, mf, cf, q in res}
    json.dump(out, open(os.path.join(HERE, "conv.json"), "w"), indent=1)
    D = load_rows()
    for row in rows:
        print(f"\nrow {row}  (L1 {D.L1[row]:.1f}  L2 {D.L2[row]:.1f}  W1 {D.W1[row]:.1f}  W2 {D.W2[row]:.1f})")
        ref = None
        for mf, cf in LEVELS[::-1]:
            qs = {s: out[f"{row}_{s}_{mf}_{cf}"] for s in "CAB"}
            secs = []
            for s in "CAB":
                ln = x.qs_lines(qs[s], "float" if s == "B" else "gnd")
                secs.append(x.line_fom(**ln))
            res = [average(D.loc[row], qs, f) for f in ("gnd", "float")]
            vals = np.array([v for t in secs for v in t] + [v for d in res for v in (d["n"], d["Z0"], d["alpha"])])
            if ref is None:
                ref = vals
            nel = sum(qs[s]["nel"] for s in "CAB")
            print(f"  mf {mf:.1f} cf {cf:.1f}  {nel:7d} el  " + " ".join(f"{(v/r0-1)*100:+7.3f}" for v, r0 in zip(vals, ref)))
        print("  columns: C n,Z,a | A n,Z,a | B(float) n,Z,a | avg-gnd n,Z,a | avg-float n,Z,a   (% vs finest)")
        print("  finest:  " + " ".join(f"{v:.4g}" for v in ref))


if __name__ == "__main__":
    main()
