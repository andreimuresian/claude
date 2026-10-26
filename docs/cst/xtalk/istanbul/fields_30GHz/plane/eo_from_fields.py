"""
EO crosstalk at 30 GHz straight from the CST field plane (5 mm, w = 1 mm, ports 50 ohm).

E_y at the centre of each signal-ground gap is proportional to that gap's voltage.
For line k (centre y_k), with the gaps at y_k -+ 7.075 um (grid points used: A 0.305 / 0.320,
B -0.320 / -0.305 mm):
    V_k(z)  ~ [E_y(+ side gap) - E_y(- side gap)] / 2    push-pull (differential) gap field
    C_k(z)  ~ [E_y(+ side gap) + E_y(- side gap)] / 2    common part, cancels in push-pull
EO crosstalk (Step 1): X = int V_B e^{j beta_o z} dz / int V_A e^{j beta_o z} dz.
The proportionality constant is the same on A and B (mirror images), so it cancels.
gapV.npz holds z, V_A, V_B, C_A, C_B (complex, V/m, raw, not cell-averaged).
"""
import os, numpy as np
d = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gapV.npz"))
z = d["z"]; m = (z >= 0) & (z <= 5)
K0 = 2 * np.pi * 30e9 / 2.99792458e8 * 1e-3
H = lambda v, ng: np.trapezoid(v[m] * np.exp(1j * K0 * ng * z[m]), z[m])
for ng in (2.0, 2.1, 2.2, 2.27, 2.4):
    print(f"n_g = {ng:4.2f}: EO crosstalk B/A = {20*np.log10(abs(H(d['VB'], ng) / H(d['VA'], ng))):6.1f} dB")
