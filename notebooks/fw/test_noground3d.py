"""3D plain cell: CPW vs signal strip alone.  The 2D solver finds no low-loss n ~ 2 mode
for the signal alone; the 3D cell must agree."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "../mom")
import stack_params as sp, fw3d
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, t_LN=sp.TFLN - d.ETCH_DEPTH*1e-6,
         L1=d.L1*1e-6, L2=d.L2*1e-6, W1=d.W1*1e-6, W2=d.W2*1e-6)
f = 20e9; k0 = 2*np.pi*f/fw3d.C0
for ng in (False, True):
    c = fw3d.Cell3D(g, tee=False, no_ground=ng, h_edge=0.8e-6, growth=1.5, side=250e-6, top=250e-6,
                    pml=250e-6, si_extra=100e-6, hmax=60e-6)
    lam, V = c.solve(1.95*k0, k0, k=8)
    print("no ground" if ng else "CPW", flush=True)
    for l, v in sorted(zip(lam, V.T), key=lambda t: abs(t[0] - k0**2)):
        kk = np.sqrt(l)
        if kk.real*fw3d.C0/2/np.pi < 1e8: continue
        Vg = c.gap_voltage(v)
        print(f"  f {kk.real*fw3d.C0/2/np.pi/1e9:8.3f} GHz  Q {kk.real/(2*abs(kk.imag)+1e-30):10.1f}  n {1.95*k0/kk.real:.4f}"
              f"  score {abs(Vg).mean()/np.linalg.norm(v):.2e}  PML {c.pml_fraction(v):.3f}", flush=True)
