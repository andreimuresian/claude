"""EME tee cell, row 49: n, alpha, Z_B of the Bloch mode."""
import sys, time
import numpy as np
import pandas as pd
sys.path.insert(0, "../mom")
import stack_params as sp
import eme

d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, t_LN=sp.TFLN - d.ETCH_DEPTH*1e-6,
         L1=d.L1*1e-6, L2=d.L2*1e-6, W1=d.W1*1e-6, W2=d.W2*1e-6)
args = [a for a in sys.argv[1:] if "=" not in a]
kw = {a.split("=")[0]: float(a.split("=")[1]) for a in sys.argv[1:] if "=" in a}
nm = int(kw.pop("nmodes", 60))
for f in [float(a)*1e9 for a in args]:
    t = time.time()
    secs, S = eme.tee_cell(g, f, nmodes=nm, **kw)
    k0 = secs["A"].k0
    lam, a, b = eme.bloch(S)
    # forward Bloch mode with the largest fundamental-CPW content (mode index of section A's CPW)
    cpw = int(np.argmax(np.abs(secs["A"].V)/np.sqrt(np.abs(secs["A"].beta))))
    w = np.abs(a[cpw])/np.linalg.norm(np.r_[a, b], axis=0)
    fwd = np.abs(lam) <= 1 + 1e-9
    i = int(np.argmax(np.where(fwd, w, -1)))
    gam = -np.log(lam[i])/eme.P
    n = gam.imag/k0
    alpha = gam.real*8.686/100
    V = np.sum((a[:, i] + b[:, i])*secs["A"].V); I = np.sum((a[:, i] - b[:, i])*secs["A"].I)
    nA = secs["A"].beta[cpw].real/k0
    print(f"{f/1e9:5.0f} GHz M={nm} | n {n:.4f} (plain {nA:.4f}, ratio {n/nA:.4f})  alpha {alpha:.3f} dB/cm"
          f"  Z_B {V/I:.2f} | CPW weight {w[i]:.3f} | biortho {[round(s.biortho, 6) for s in secs.values()]}"
          f"  {time.time() - t:.0f} s", flush=True)
