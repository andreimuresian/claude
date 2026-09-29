import sys, time, json
from multiprocessing import Pool
import numpy as np, pandas as pd
import qs3d as q
sys.path.insert(0,'../mom'); import stack_params as sp
D=pd.read_excel('../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx')
def job(a):
    row,hz,hn=a; r=D.loc[row]; t=time.time()
    g=dict(WS=r.WS*1e-6,GAP=r.GAP*1e-6,MTX=r.MTX*1e-6,t_LN=sp.TFLN-r.ETCH_DEPTH*1e-6,W1=r.W1*1e-6,W2=r.W2*1e-6,L1=r.L1*1e-6,L2=r.L2*1e-6)
    mu,me=q.build(g,False,hz,h_near=hn),q.build(g,True,hz,h_near=hn)
    Cu,_,cu=q.capacitance(mu); Lu,_,lu=q.inductance(mu); Ce,_,ce=q.capacitance(me); Le,_,le=q.inductance(me)
    Lud,Cud=q.cell_abcd_lumped(lu,cu); Led,Ced=q.cell_abcd_lumped(le,ce)
    return dict(row=row,hz=hz,hn=hn,dC=Ced-Cud,dL=Led-Lud,ref_dC=float(r['deltaC lumped']),ref_dL=float(r['deltaL lumped']),n=int(me['sig'].size),sec=time.time()-t)
if __name__=='__main__':
    with Pool(4) as p: out=p.map(job,[(38,0.25e-6,3e-6),(118,0.25e-6,3e-6)])
    base={o['row']:o for o in json.load(open('run5.json'))}
    for o in out:
        b=base[o['row']]
        print(f"row {o['row']}: cells {o['n']/1e6:.2f}M ({o['sec']:.0f}s)  dC {o['dC']:+.4e} (base {b['dC']:+.4e}, change {(o['dC']/b['dC']-1)*100:+.1f}%) err vs CST {(o['dC']/o['ref_dC']-1)*100:+.1f}%"
              f" | dL change {(o['dL']/b['dL']-1)*100:+.1f}%, err {(o['dL']/o['ref_dL']-1)*100:+.1f}%")
