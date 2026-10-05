"""Section-average test on dataset rows (sections A, B, C per row).

Per section: the quasi-static solve (finger grounded and floating) and the
notebook's full-wave eigen solve + IBC correction (finger as plain metal, as a
2D port solve sees it).  Writes run_rows.json; report.py prints the tables.
Run: python run_rows.py [rows...]
"""
import json
import os
import resource
import sys
import time
from multiprocessing import Pool

import xsec2d as x
from average import load_rows

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = [118, 416, 121, 38, 49,                     # rows with 3D quasi-static results (../qs3d)
        355, 206, 398, 130, 363, 302, 220,         # 5..95 % quantiles of nm_final / nm_baseline
        448, 408]                                  # L1 > L2 (no finger)
MESH = (1.0, 1.0)                                  # notebook default; see conv.py


def job(a):
    row, sec = a
    r = load_rows().loc[row]
    t = time.time()
    s = x.Section(r.WS, r.GAP, r.MTX, r.CAP_W, r.ETCH_DEPTH,
                  x.pieces_for(sec, r.WS, r.GAP, r.W1, r.W2, r.L1, r.L2), *MESH)
    qs = {k: float(v) for k, v in s.quasi_static().items()}
    n_qs = x.line_fom(**x.qs_lines(qs, "gnd"))[0]
    try:
        fw = {k: float(v) for k, v in s.full_wave(n_qs).items()}
    except RuntimeError as e:
        fw = {"error": str(e)}
    return row, sec, dict(qs=qs, fw=fw, nel=int(s.mesh.nelements), t=time.time() - t,
                          maxrss_GB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6)


def main():
    rows = [int(a) for a in sys.argv[1:]] or ROWS
    path = os.path.join(HERE, "run_rows.json")
    out = json.load(open(path)) if os.path.exists(path) else {}
    jobs = [(r, s) for r in rows for s in "CAB" if f"{r}_{s}" not in out]
    with Pool(3, maxtasksperchild=1) as p:
        for row, sec, res in p.imap_unordered(job, jobs):
            out[f"{row}_{sec}"] = res
            json.dump(out, open(path, "w"), indent=1)
            print(f"row {row} {sec}: {res['nel']} el, {res['t']:.0f} s, {res['maxrss_GB']:.1f} GB"
                  + (f"  FW ERROR {res['fw']['error']}" if "error" in res["fw"] else ""), flush=True)


if __name__ == "__main__":
    main()
