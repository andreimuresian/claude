"""Lumped dC, dL with the far frame grounded (default) vs floating (Neumann).

A grounded box collects about 13% of the signal charge; an open periodic line
(CST Multilayer: laterally infinite layers) carries zero net charge per cell on
signal + grounds, which the floating frame reproduces.  The magnetics already
use a zero-current frame.  Etched and no-slot cells share one grid.
Run: python frame_check.py 49 118
"""
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

import qs3d as q

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'mom'))
import stack_params as sp

D = pd.read_excel(os.path.join(HERE, '..', 'mom', 'data', 'EVALUATED_FULL_LHS_DATASET.xlsx'))


def job(a):
    row, etched = a
    r = D.loc[row]; t = time.time()
    g = dict(WS=r.WS*1e-6, GAP=r.GAP*1e-6, MTX=r.MTX*1e-6, t_LN=sp.TFLN - r.ETCH_DEPTH*1e-6,
             W1=r.W1*1e-6, W2=r.W2*1e-6, L1=r.L1*1e-6, L2=r.L2*1e-6)
    m = q.build(g, etched=True, no_slot=not etched)
    _, _, ls = q.inductance(m)
    out = {}
    for ff in (False, True):
        Cp, rc, cs = q.capacitance(m, float_frame=ff)
        out[ff] = (Cp, q.cell_abcd_lumped(ls, cs))
    return row, etched, out, time.time() - t


def main():
    rows = [int(a) for a in sys.argv[1:]] or [49, 118]
    with Pool(4) as p:
        res = {(o[0], o[1]): o for o in p.map(job, [(r, e) for r in rows for e in (True, False)])}
    for row in rows:
        r = D.loc[row]
        refC, refL = float(r['deltaC lumped']), float(r['deltaL lumped'])
        for ff in (False, True):
            (Ce, (Led, Ced)), (Cu, (Lud, Cud)) = res[(row, True)][2][ff], res[(row, False)][2][ff]
            dC, dL = Ced - Cud, Led - Lud
            L = r.z0_baseline_val*r.nm_baseline_val/q.C0 + dL/q.P
            C = r.nm_baseline_val/(r.z0_baseline_val*q.C0) + dC/q.P
            print(f"row {row:3d} {'floating' if ff else 'grounded'}: C' no-slot {Cu*1e12:7.2f} etched {Ce*1e12:7.2f} pF/m | "
                  f"dC err {(dC/refC-1)*100:+6.1f}% | dL err {(dL/refL-1)*100:+6.1f}% | "
                  f"n_final {(q.C0*np.sqrt(L*C)/r.nm_final_val-1)*100:+.2f}%  "
                  f"Z0_final {(np.sqrt(L/C)/r.z0_final_val-1)*100:+.2f}%")


if __name__ == '__main__':
    main()
