"""Step 1 gate: does 3D ohmic loss (quasi-static, converged IBC) explain the
dataset's alpha_delta?  Tee cell and no-slot cell per row, loss.py.
Writes run_loss.json; report_loss.py prints the tables.
Run: python run_loss.py            (14 rows of ../xsec + grid checks on rows 49, 118)
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import json
import sys
import time
from multiprocessing import Pool

import pandas as pd

import loss as Lo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mom'))
import stack_params as sp

HERE = os.path.dirname(os.path.abspath(__file__))
D = pd.read_excel(os.path.join(HERE, '..', 'mom', 'data', 'EVALUATED_FULL_LHS_DATASET.xlsx'))
ROWS = [118, 416, 121, 38, 49, 355, 206, 398, 130, 363, 302, 220, 448, 408]     # ../xsec/run_rows.py
VARIANTS = {"base": {}, "a/2": dict(a=Lo.DELTA/4), "hmin/2": dict(hmin_scale=0.5),
            "hz/2 h_near/2": dict(hz_min=0.25e-6, h_near=3e-6)}


def geom(row):
    r = D.loc[row]
    return dict(WS=r.WS*1e-6, GAP=r.GAP*1e-6, MTX=r.MTX*1e-6, t_LN=sp.TFLN - r.ETCH_DEPTH*1e-6,
                W1=r.W1*1e-6, W2=r.W2*1e-6, L1=r.L1*1e-6, L2=r.L2*1e-6)


def job(arg):
    row, var = arg
    kw = dict(VARIANTS[var]); a = kw.pop("a", Lo.DELTA/2)
    t = time.time()
    g = geom(row)
    u = Lo.cell(g, False, a, **kw)
    e = Lo.cell(g, True, a, **kw)
    return f"{row}|{var}", dict(row=row, var=var, a=a, u=u, e=e, sec=time.time() - t)


def main():
    path = os.path.join(HERE, "run_loss.json")
    out = json.load(open(path)) if os.path.exists(path) else {}
    jobs = [(r, "base") for r in ROWS] + [(r, v) for r in (49, 118) for v in VARIANTS if v != "base"]
    jobs = [j for j in jobs if f"{j[0]}|{j[1]}" not in out]
    with Pool(4, maxtasksperchild=1) as p:
        for k, v in p.imap_unordered(job, jobs):
            out[k] = v
            json.dump(out, open(path, "w"))
            print(f"{k}: {v['e']['cells']/1e6:.2f}M cells, {v['sec']:.0f} s", flush=True)


if __name__ == "__main__":
    main()
