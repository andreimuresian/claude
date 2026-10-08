"""Diagnostic: stem slot through the WHOLE ground width (W1 = 70 um), no head.  The grounds
become isolated pads; no low-frequency CPW mode with n ~ 1.96 can exist (no DC return path)."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "../mom")
import stack_params as sp, fw3d
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, t_LN=sp.TFLN - d.ETCH_DEPTH*1e-6,
         L1=d.L1*1e-6, L2=d.L1*1e-6 - 1e-6, W1=70e-6, W2=0.0)
c = fw3d.Cell3D(g, tee=True, h_edge=0.8e-6, hz_min=2e-6, hz_max=20e-6, growth=1.5, side=250e-6, top=250e-6,
                pml=250e-6, si_extra=100e-6, hmax=60e-6,
                **{k: float(v) for k, v in (a.split("=") for a in sys.argv[1:])})
mEx = c.masks[0]; j = int(np.argmin(abs(c.yn - g["MTX"]/2)))
for k in range(0, len(c.zn), 4):
    print("z=%6.1f" % (c.zn[k]*1e6), "".join("M" if v else "." for v in mEx[:45, j, k]))
f = 20e9; k0 = 2*np.pi*f/fw3d.C0
lam, V = c.solve(1.96*k0, k0, k=10)
for l, v in sorted(zip(lam, V.T), key=lambda t: abs(t[0] - k0**2)):
    kk = np.sqrt(l)
    if kk.real*fw3d.C0/2/np.pi < 1e8: continue
    Vg = c.gap_voltage(v)
    print(f"  f {kk.real*fw3d.C0/2/np.pi/1e9:8.3f} GHz  Q {kk.real/(2*abs(kk.imag)+1e-30):10.1f}  n {1.96*k0/kk.real:.4f}"
          f"  score {abs(Vg).mean()/np.linalg.norm(v):.2e}  PML {c.pml_fraction(v):.3f}", flush=True)
