"""FW2 step a: plain (no-slot) 3D periodic cell vs the 2D full-wave solver, 60 GHz, row 49.
Real beta = 2D beta; the 3D eigenvalue must return f ~ 60 GHz and a small Im part."""
import sys, time
import numpy as np
import pandas as pd
sys.path.insert(0, "../mom")
import stack_params as sp
import fw3d

d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, t_LN=sp.TFLN - d.ETCH_DEPTH*1e-6,
         L1=d.L1*1e-6, L2=d.L2*1e-6, W1=d.W1*1e-6, W2=d.W2*1e-6)
tee = "tee" in sys.argv
K = int(next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("k=")), 8))
sys.argv = [a for a in sys.argv if not a.startswith("k=")]
f = float(next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("f=")), 60))*1e9
sys.argv = [a for a in sys.argv if not a.startswith("f=")]
nb = float(next((a.split("=")[1] for a in sys.argv[1:] if a.startswith("nb=")), 0))
sys.argv = [a for a in sys.argv if not a.startswith("nb=")]
n2d = 1.9542
kw = {a.split("=")[0]: (a.split("=")[1] if a.startswith("wall") else (a.split("=")[1] == "1") if a.startswith("ground_to_wall") else float(a.split("=")[1])) for a in sys.argv[1:] if "=" in a}
k0 = 2*np.pi*f/fw3d.C0
t = time.time()
c = fw3d.Cell3D(g, tee=tee, **kw)
print("grid", c.shape, "unknowns", c.N, flush=True)
beta = (nb or (2.7 if tee else n2d))*k0
lam, V = c.solve(beta, k0, k=int(kw.pop("k", 8)) if False else K)
for l, v in sorted(zip(lam, V.T), key=lambda t: abs(t[0] - k0**2)):
    kk = np.sqrt(l)
    Vg = c.gap_voltage(v)
    score = abs(Vg).mean()/np.linalg.norm(v)
    print(f"  f {kk.real*fw3d.C0/2/np.pi/1e9:8.3f} GHz  Q {kk.real/(2*abs(kk.imag)+1e-30):10.1f}  n {beta/kk.real:.4f}"
          f"  gap-V score {score:.3e}  |V| spread over z {abs(Vg).std()/abs(Vg).mean():.3f}  PML fraction {c.pml_fraction(v):.3f}", flush=True)
print(f"LU memory {c._last[2]:.2f} GB, {time.time()-t:.0f} s")
