"""dC, dL on the 5 reference rows, scored with the author's lumped definition."""
import json, sys, time
from multiprocessing import Pool
import numpy as np, pandas as pd
import qs3d as q
sys.path.insert(0, '../mom'); import stack_params as sp
D = pd.read_excel('../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx')
ROWS = [int(a) for a in sys.argv[1:]] or [118, 416, 121, 38, 49]

def job(row):
    r = D.loc[row]; t = time.time()
    g = dict(WS=r.WS*1e-6, GAP=r.GAP*1e-6, MTX=r.MTX*1e-6, t_LN=sp.TFLN-r.ETCH_DEPTH*1e-6,
             W1=r.W1*1e-6, W2=r.W2*1e-6, L1=r.L1*1e-6, L2=r.L2*1e-6)
    mu, me = q.build(g, etched=False), q.build(g, etched=True)
    Cu, _, cu = q.capacitance(mu); Lu, _, lu = q.inductance(mu)
    Ce, rc, ce = q.capacitance(me); Le, rl, le = q.inductance(me)
    Lul, Cul, tu = q.lumped(Lu, Cu); Lel, Cel, te = q.lumped(Le, Ce)
    Lud, Cud = q.cell_abcd_lumped(lu, cu); Led, Ced = q.cell_abcd_lumped(le, ce)
    return dict(row=row, Cu=Cu, Lu=Lu, Ce=Ce, Le=Le, dC=Ced-Cud, dL=Led-Lud,
                dC_uniform=Cel-Cul, dL_uniform=Lel-Lul, uni_check=(Lud/Lul-1, Cud/Cul-1),
                prof=dict(le=le.tolist(), ce=ce.tolist()),
                dCp=(Ce-Cu)*q.P, dLp=(Le-Lu)*q.P, th_u=tu, th_e=te,
                ref_dC=float(r['deltaC lumped']), ref_dL=float(r['deltaL lumped']),
                res=(rc, rl), sec=time.time()-t, n=int(me['sig'].size))

if __name__ == '__main__':
    t0 = time.time()
    with Pool(4) as p:
        out = p.map(job, ROWS)
    json.dump(out, open('run5.json', 'w'), indent=1)
    print(f"{'row':>4} | {'dC model':>11} {'dC CST':>11} {'err':>7} | {'dL model':>11} {'dL CST':>11} {'err':>7} | cells  time")
    eC, eL = [], []
    for o in out:
        ec = (o['dC']/o['ref_dC']-1)*100; el = (o['dL']/o['ref_dL']-1)*100; eC.append(abs(ec)); eL.append(abs(el))
        print(f"{o['row']:4d} | {o['dC']:+.4e} {o['ref_dC']:+.4e} {ec:+6.1f}% | {o['dL']:+.4e} {o['ref_dL']:+.4e} {el:+6.1f}% | {o['n']/1e6:.2f}M {o['sec']:4.0f}s")
    print("uniform-cell scoring (previous):  " + "  ".join(f"{o['row']}: dC {(o['dC_uniform']/o['ref_dC']-1)*100:+.1f}% dL {(o['dL_uniform']/o['ref_dL']-1)*100:+.1f}%" for o in out))
    print("check, unetched slice cascade == uniform formula:", max(max(abs(a) for a in o['uni_check']) for o in out))
    print(f"median |err|: dC {np.median(eC):.1f}%   dL {np.median(eL):.1f}%    wall {time.time()-t0:.0f}s")
