"""Coupled (second-order) correction to the lumped dC on the 5 reference rows.

Each row: the etched cell and the same cell without the slot (no_slot=True, same
grid).  dC = [cascade C_lump + coupled dC](etched) - [same](no slot); the
no-slot cell carries the uniform-line part of the correction (box charge,
non-TEM field of the inhomogeneous stack), which the difference removes.
Writes run5_coupled.json.  Run: python run5_coupled.py [rows]
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

import coupled as cp
import qs3d as q

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'mom'))
import stack_params as sp

D = pd.read_excel(os.path.join(HERE, '..', 'mom', 'data', 'EVALUATED_FULL_LHS_DATASET.xlsx'))
ROWS = [int(a) for a in sys.argv[1:]] or [118, 416, 121, 38, 49]


def job(a):
    row, etched = a
    r = D.loc[row]; t = time.time()
    g = dict(WS=r.WS*1e-6, GAP=r.GAP*1e-6, MTX=r.MTX*1e-6, t_LN=sp.TFLN - r.ETCH_DEPTH*1e-6,
             W1=r.W1*1e-6, W2=r.W2*1e-6, L1=r.L1*1e-6, L2=r.L2*1e-6)
    m = q.build(g, etched=True, no_slot=not etched)
    c = cp.coupled_lumped_C(m)
    _, _, cs = q.capacitance(m); _, _, ls = q.inductance(m)
    Ld, Cd = q.cell_abcd_lumped(ls, cs)
    c.update(row=row, etched=etched, C_casc=Cd, L_casc=Ld, sec=time.time() - t,
             shape=list(m['sig'].shape))
    return {k: (list(v) if isinstance(v, tuple) else v) for k, v in c.items()}


def main():
    t0 = time.time()
    with Pool(4) as p:
        out = p.map(job, [(r, e) for r in ROWS for e in (True, False)])
    json.dump(out, open(os.path.join(HERE, 'run5_coupled.json'), 'w'), indent=1, default=float)
    print(f"{'row':>4} | {'L_e/L_h 3D':>10} {'1D':>6} | {'dC cascade':>11} {'err':>7} | "
          f"{'dC coupled':>11} {'err':>7} | {'dC CST':>11} | n_final, Z0_final err: cascade -> coupled")
    e0, e1 = [], []
    for row in ROWS:
        e = next(o for o in out if o['row'] == row and o['etched'])
        u = next(o for o in out if o['row'] == row and not o['etched'])
        r = D.loc[row]; ref = float(r['deltaC lumped'])
        dC0 = e['C_casc'] - u['C_casc']; dC1 = dC0 + e['dC'] - u['dC']
        dL = e['L_casc'] - u['L_casc']
        # final Z0 with the model deltas on the dataset baseline (per length: /P)
        z, n = [], []
        for dc in (dC0, dC1):
            L = r.z0_baseline_val*r.nm_baseline_val/q.C0 + dL/q.P
            C = r.nm_baseline_val/(r.z0_baseline_val*q.C0) + dc/q.P
            z.append((np.sqrt(L/C)/r.z0_final - 1)*100)
            n.append((q.C0*np.sqrt(L*C)/r.nm_final - 1)*100)
        e0.append(abs(dC0/ref - 1)); e1.append(abs(dC1/ref - 1))
        print(f"{row:4d} | {e['L_e']/e['L_h']:10.4f} {e['L_e_1d']/e['L_h']:6.4f} | {dC0:+.4e} {(dC0/ref-1)*100:+6.1f}% | "
              f"{dC1:+.4e} {(dC1/ref-1)*100:+6.1f}% | {ref:+.4e} | n {n[0]:+.2f}% -> {n[1]:+.2f}%   Z0 {z[0]:+.2f}% -> {z[1]:+.2f}%")
    print(f"no-slot cells: L_e/L_h 3D " + " ".join(f"{o['L_e']/o['L_h']:.4f}" for o in out if not o['etched'])
          + "  (1D: 1/3; excess = box charge + non-TEM, removed by the difference)")
    print(f"median |err| dC: cascade {np.median(e0)*100:.1f}%  coupled {np.median(e1)*100:.1f}%   wall {time.time()-t0:.0f}s")


if __name__ == '__main__':
    main()
