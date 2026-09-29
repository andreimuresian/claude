"""50-row 2D baseline with anisotropic LiNbO3 vs the dataset (COMSOL baseline).

Rows 0, 10, ..., 490, production grid (same set as cpw2d_50row.json, which
holds the isotropic-34.7 run of the identical solver).
Writes data/cpw2d_50row_aniso.json.  Run: python diagnostics/aniso_50row.py
"""
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import cpw_2d_static as cs
import stack_params as sp

KW = dict(hmax=6e-6, pad_x=1200e-6, pad_up=800e-6)
D = pd.read_excel(os.path.join(HERE, '..', 'data', 'EVALUATED_FULL_LHS_DATASET.xlsx'))
VARIANTS = {'cst_28_43': sp.EPS_LN_ANISO, 'comsol_28_44': sp.EPS_LN_ANISO_COMSOL}


def job(args):
    row, tag = args
    r = D.loc[row]
    C, Ca, _ = cs.solve_cs(r.WS*1e-6, r.GAP*1e-6, 70e-6, r.MTX*1e-6,
                           sp.TFLN - r.ETCH_DEPTH*1e-6, sp.BOX_H, sp.SI_H,
                           VARIANTS[tag], sp.EPS_SIO2, sp.EPS_SI, **KW)
    n, z = cs.observables(C, Ca)
    return dict(row=int(row), tag=tag, n=n, z=z)


def main():
    rows = list(D.index[::10][:50])
    t0 = time.time()
    with Pool(4) as p:
        out = p.map(job, [(r, t) for t in VARIANTS for r in rows])
    iso = {r['row']: r for r in json.load(open(os.path.join(HERE, '..', 'data', 'cpw2d_50row.json')))}
    res = []
    for o in out:
        r = D.loc[o['row']]
        o['dn'] = o['n']/r.nm_baseline_val - 1
        o['dz'] = o['z']/r.z0_baseline_val - 1
        o['n_iso'], o['z_iso'] = iso[o['row']]['n'], iso[o['row']]['z']
        res.append(o)
    json.dump(res, open(os.path.join(HERE, '..', 'data', 'cpw2d_50row_aniso.json'), 'w'), indent=1)
    print(f'{len(out)} solves in {time.time()-t0:.0f} s')
    for tag in ['iso_34.7'] + list(VARIANTS):
        if tag == 'iso_34.7':
            sub = [o for o in res if o['tag'] == 'cst_28_43']
            dn = np.array([o['n_iso']/D.loc[o['row']].nm_baseline_val - 1 for o in sub])
            dz = np.array([o['z_iso']/D.loc[o['row']].z0_baseline_val - 1 for o in sub])
        else:
            sub = [o for o in res if o['tag'] == tag]
            dn = np.array([o['dn'] for o in sub]); dz = np.array([o['dz'] for o in sub])
        print(f'{tag:13s} n_m: mean {dn.mean()*100:+.2f}%  median|err| {np.median(abs(dn))*100:.2f}%'
              f'  max|err| {abs(dn).max()*100:.2f}%   |  Z0: mean {dz.mean()*100:+.2f}%'
              f'  median|err| {np.median(abs(dz))*100:.2f}%  max|err| {abs(dz).max()*100:.2f}%')


if __name__ == '__main__':
    main()
