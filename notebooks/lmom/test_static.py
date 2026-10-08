"""Electrostatic checks of the 2D thick-metal MoM, row 49 unetched.
Reference: ../xsec 2D FEM (converged): C_air = 47.011 pF/m (C with the stack: 180.60 pF/m)."""
import sys
import numpy as np, pandas as pd
import mom2d as M
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
WS, GAP, t = d.WS*1e-6, d.GAP*1e-6, d.MTX*1e-6
xs, xg, xo = WS/2, WS/2 + GAP, WS/2 + GAP + 70e-6
rects = [(-xs, xs, 0, t), (xg, xo, 0, t), (-xo, -xg, 0, t)]
for hmin, hmax in ((0.2e-6, 4e-6), (0.1e-6, 2e-6), (0.05e-6, 1e-6)):
    g = M.Geometry(rects, hmin, hmax)
    C, q = M.static_capacitance(g, [0])
    print(f"hmin {hmin*1e6:.2f} um, {g.nseg} segments: C_air = {C*1e12:.3f} pF/m  (FEM 47.011)", flush=True)

# with the stack: LN image extracted (K = (1 - sqrt(28*43))/(1 + sqrt(28*43))), rest spectral
import stack as S
L, bot = S.tfln_layers(3e-6 - 3e-6 + (0.46e-6 - d.ETCH_DEPTH*1e-6), 11.7)
eps_eff = np.sqrt(28*43)
K = (1 - eps_eff)/(1 + eps_eff)
for hmin, hmax in ((0.2e-6, 4e-6), (0.1e-6, 2e-6)):
    g = M.Geometry(rects, hmin, hmax)
    for kq in (dict(), dict(dk=5e2, ratio=1.005, kmax=4e8)):
        Pr = M.refl_static(g, L, bot, K, **kq)
        C, q = M.static_capacitance(g, [0], eps_image=eps_eff, refl=Pr)
        print(f"hmin {hmin*1e6:.2f} um, {g.nseg} seg, k-grid {'fine' if kq else 'base'}: C = {C*1e12:.3f} pF/m  (FEM 180.60, LN 44 vertical there)", flush=True)
