"""Potentials of line A's conductors relative to the PEC side wall (y = 200 um),
from the line integral of E_y along rows inside the metal height.
usage: python eig_conductor_potentials.py [zip]"""
import sys, numpy as np
src = open("eig_impedance.py").read().split("Pe, Ve")[0]
exec(src)
for tag in ("even", "odd"):
    x, y, E = load(f"Mode_3_e_{tag}.txt")
    for xr in (0.5e-6, 1.0e-6):
        ix = np.argmin(abs(x - xr)); e = E[ix, :, 1]; zero = np.abs(e) < 1e-9*np.abs(e).max()
        V = -np.concatenate([[0], np.cumsum(0.5*(e[1:] + e[:-1])*np.diff(y))])
        V = V - V[-1]                                   # wall at y = 200 um is 0 V
        ed = np.flatnonzero(np.diff(np.r_[0, zero.astype(int), 0]))
        g1, s, g2 = [V[a:b].mean() for a, b in zip(ed[::2], ed[1::2])]
        print(f"{tag} row {xr*1e6:.1f} um: V_g1/V_s {g1/s:+.4f}  V_g2/V_s {g2/s:+.4f}  "
              f"(V_s - V_g1)/(V_s - V_g2) {(s-g1)/(s-g2):.4f}")
