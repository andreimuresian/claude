"""What quantity are the dataset's `deltaL lumped` / `deltaC lumped`?

The author's extractor (touchstone_extractor_lumped_delta.py) simulates ONE
200 um cell (etched, unetched) with discrete ports and takes, at 60 GHz,
    L = Im(B)/w,   C = Im(C_abcd)/w          (ABCD of the whole cell)
For a (Bloch-)uniform cell B = Z sin(theta), C = sin(theta)/Z with
theta = beta*P, so these are the per-length values x P x sin(theta)/theta.
theta differs between etched and unetched (~0.48 vs ~0.57 rad), so the
sinc factor does NOT cancel in the difference.

Part 1 inverts that exactly for all 500 rows (sin(theta) = w sqrt(L C) for a
lossless uniform section), using the COMSOL baseline for the unetched cell.
Part 2 re-scores the stored Phase-3 MoM results with the author's definition
(Phase 3 compared per-length (Ce - Cu)*P against the lumped value).
"""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
MOM = os.path.join(HERE, '..', 'mom')
C0, W, P = 299792458.0, 2 * np.pi * 60e9, 200e-6
sinc = lambda t: np.sin(t) / t


def part1():
    d = pd.read_excel(os.path.join(MOM, 'data', 'EVALUATED_FULL_LHS_DATASET.xlsx'))
    n, Z = d.nm_baseline_val.values, d.z0_baseline_val.values
    Lu, Cu = n * Z / C0 * P, n / (C0 * Z) * P
    tu = W * n * P / C0
    Le_l = Lu * sinc(tu) + d['deltaL lumped'].values
    Ce_l = Cu * sinc(tu) + d['deltaC lumped'].values
    te = np.arcsin(np.clip(W * np.sqrt(Le_l * Ce_l), 0, 1))
    rC = d['deltaC lumped'].values / (Ce_l / sinc(te) - Cu)
    rL = d['deltaL lumped'].values / (Le_l / sinc(te) - Lu)
    pc = lambda v: np.round(np.percentile(v, [5, 25, 50, 75, 95]), 2)
    print('lumped dC / per-length dC*P   p5 p25 p50 p75 p95:', pc(rC))
    print('lumped dL / per-length dL*P   p5 p25 p50 p75 p95:', pc(rL))
    print('rows with |ratio_C - 1| > 0.3:', int((np.abs(rC - 1) > 0.3).sum()), '/ 500')


def part2():
    for fn in ('phase3r_h9.json', 'phase3r_h9_nearfield.json'):
        J = json.load(open(os.path.join(MOM, 'data', fn)))
        old_c, new_c, old_l, new_l = [], [], [], []
        for r in J:
            Cu, Lu = r['C_u_svd'], r['L_u_svd']
            Ce, Le = Cu + r['dC_svd'] / P, Lu + r['dL_svd'] / P
            tu, te = W * P * np.sqrt(Lu * Cu), W * P * np.sqrt(Le * Ce)
            dC = Ce * P * sinc(te) - Cu * P * sinc(tu)
            dL = Le * P * sinc(te) - Lu * P * sinc(tu)
            e = lambda a, b: abs(a - b) / abs(b) * 100
            old_c.append(e(r['dC_svd'], r['ref']['dC'])); new_c.append(e(dC, r['ref']['dC']))
            old_l.append(e(r['dL_svd'], r['ref']['dL'])); new_l.append(e(dL, r['ref']['dL']))
        print(f'{fn}: median dC error {np.median(old_c):.1f}% -> {np.median(new_c):.1f}% ;'
              f' dL {np.median(old_l):.1f}% -> {np.median(new_l):.1f}%')


if __name__ == '__main__':
    part1()
    part2()
