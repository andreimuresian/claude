"""Checks for docs/coupled_lines_A1_A2.md (numpy + scipy)."""
import numpy as np
from scipy.linalg import expm
c0 = 299792458.0
f = 30e9; w = 2*np.pi*f
# per-unit-length values of the order extracted from the 1 mm pair at 30 GHz
Ls, Lm = 243e-9, 0.28e-9          # H/m
Cg, Cm = 180.7e-12, 0.225e-12     # F/m
Rs, Rm, Gs = 2540.0, 7.6, 0.0     # ohm/m, ohm/m, S/m
L = np.array([[Ls, Lm], [Lm, Ls]])
C = np.array([[Cg + Cm, -Cm], [-Cm, Cg + Cm]])          # Maxwell capacitance matrix
R = np.array([[Rs, Rm], [Rm, Rs]])
Z = R + 1j*w*L; Y = 1j*w*C + Gs*np.eye(2)
# 1. eigenvectors of ZY are (1,1) and (1,-1)
ze, zo = Z[0, 0] + Z[0, 1], Z[0, 0] - Z[0, 1]
ye, yo = Y[0, 0] + Y[0, 1], Y[0, 0] - Y[0, 1]
for v, g2, name in (([1, 1], ze*ye, "even"), ([1, -1], zo*yo, "odd")):
    v = np.array(v, float)
    print(f"{name}: |ZY v - gamma^2 v| = {np.linalg.norm(Z@Y@v - g2*v):.1e}")
ge, go = np.sqrt(ze*ye), np.sqrt(zo*yo); Ze, Zo = np.sqrt(ze/ye), np.sqrt(zo/yo)
print(f"y_e = jw Cg: {abs(ye - 1j*w*Cg):.1e};  y_o = jw (Cg+2Cm): {abs(yo - 1j*w*(Cg+2*Cm)):.1e}")
print(f"n_e = {ge.imag*c0/w:.5f}  n_o = {go.imag*c0/w:.5f}  Z_e = {Ze:.3f}  Z_o = {Zo:.3f}")
# 2. lossless: velocities equal iff kL = kC
for lm in (Lm, Cm/(Cg + Cm)*Ls):
    ve = 1/np.sqrt((Ls + lm)*Cg); vo = 1/np.sqrt((Ls - lm)*(Cg + 2*Cm))
    print(f"kL = {lm/Ls:.3e}, kC = {Cm/(Cg+Cm):.3e}:  v_e/v_o - 1 = {ve/vo - 1:+.2e}")
# 3. integrate the coupled telegrapher equations directly (no modes assumed)
M = np.block([[np.zeros((2, 2)), -Z], [-Y, np.zeros((2, 2))]])
V0 = np.array([1, 0], complex)
I0 = 0.5/Ze*np.array([1, 1]) + 0.5/Zo*np.array([1, -1])   # forward waves only
for zmm in (1, 5, 14):
    z = zmm*1e-3
    x = expm(M*z) @ np.concatenate([V0, I0])
    VB_modal = 0.5*(np.exp(-ge*z) - np.exp(-go*z))
    print(f"z = {zmm:2d} mm: V_B ODE {abs(x[1]):.3e}, modes {abs(VB_modal):.3e}, diff {abs(x[1]-VB_modal):.1e} ({20*np.log10(abs(x[1])):.1f} dB)")
