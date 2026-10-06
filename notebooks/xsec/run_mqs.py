"""Gold-interior R' and L_int (mqs2d.py, notebook v2 cell [6]) for the 14 rows of
run_rows.py, sections A, B, C; the finger floating (its own V', zero net current).
Writes run_mqs.json; report_mqs.py combines it with the C, C_air, G of run_rows.json.
Run: python run_mqs.py [rows...]
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import json
import resource
import sys
import time
from multiprocessing import Pool

import mqs2d as q
import xsec2d as x
from average import load_rows
from run_rows import ROWS

HERE = os.path.dirname(os.path.abspath(__file__))


def job(a):
    row, sec = a
    r = load_rows().loc[row]
    t = time.time()
    o = q.section(r.WS, r.MTX, x.pieces_for(sec, r.WS, r.GAP, r.W1, r.W2, r.L1, r.L2), "float")
    o = {k: float(v) for k, v in o.items()}
    o.update(t=time.time() - t, maxrss_GB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6)
    return row, sec, o


def main():
    rows = [int(a) for a in sys.argv[1:]] or ROWS
    path = os.path.join(HERE, "run_mqs.json")
    out = json.load(open(path)) if os.path.exists(path) else {}
    jobs = [(r, s) for r in rows for s in "CAB" if f"{r}_{s}" not in out]
    with Pool(4, maxtasksperchild=1) as p:
        for row, sec, res in p.imap_unordered(job, jobs):
            out[f"{row}_{sec}"] = res
            json.dump(out, open(path, "w"), indent=1)
            print(f"row {row} {sec}: {res['ndof']:.0f} DOF, {res['t']:.0f} s, {res['maxrss_GB']:.1f} GB", flush=True)


if __name__ == "__main__":
    main()
