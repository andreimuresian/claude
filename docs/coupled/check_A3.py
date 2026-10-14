"""Checks for docs/coupled_lines_A3.md."""
import numpy as np
from scipy.linalg import expm
c0 = 299792458.0; w = 2*np.pi*30e9
def ZY(Ls, Lm, L22, Cg1, Cg2, Cm, R1, R2, Rm):
    Z = np.array([[R1, Rm], [Rm, R2]]) + 1j*w*np.array([[Ls, Lm], [Lm, L22]])
    Y = 1j*w*np.array([[Cg1 + Cm, -Cm], [-Cm, Cg2 + Cm]])
    return Z, Y
def modes(Z, Y):
    g2, TV = np.linalg.eig(Z @ Y)
    G = np.diag(np.sqrt(g2))
    TI = np.linalg.inv(TV).T                                  # current eigenvectors (reciprocity)
    Zc = TV @ np.linalg.inv(G) @ np.linalg.inv(TV) @ Z         # characteristic impedance matrix
    return G, TV, TI, Zc
M = lambda Z, Y: np.block([[np.zeros((2, 2)), -Z], [-Y, np.zeros((2, 2))]])
# 1. identical lines
Z, Y = ZY(243e-9, 0.28e-9, 243e-9, 180.7e-12, 180.7e-12, 0.225e-12, 2540, 2540, 7.6)
G, TV, TI, Zc = modes(Z, Y)
print("identical: eigenvectors (normalised to first entry):", np.round(TV[1]/TV[0], 12))
print("  YZ eigenvectors = (TV^-1)^T:", np.allclose((Y @ Z) @ TI, TI @ G @ G))
Ze, Zo = Zc[0, 0] + Zc[0, 1], Zc[0, 0] - Zc[0, 1]
print(f"  Zc matrix = [[{Zc[0,0]:.3f}, {Zc[0,1]:.4f}], ...];  (Ze+Zo)/2, (Ze-Zo)/2 -> Ze {Ze:.3f}, Zo {Zo:.3f}")
# forward-only check: start with V, I = Zc^-1 V and propagate; backward part must stay zero
for name, (Z_, Y_) in (("identical", (Z, Y)),
                       ("unequal", ZY(243e-9, 0.6e-9, 300e-9, 180e-12, 150e-12, 0.5e-12, 2500, 3000, 10))):
    G_, TV_, TI_, Zc_ = modes(Z_, Y_)
    V0 = np.array([1, 0], complex); I0 = np.linalg.solve(Zc_, V0)
    x = expm(M(Z_, Y_)*14e-3) @ np.concatenate([V0, I0])
    print(f"  {name}: after 14 mm, |V - Zc I| (should be 0 for forward waves only) = {np.linalg.norm(x[:2] - Zc_ @ x[2:]):.1e}")
# 2. unequal lines: eigenvectors are not (1, +-1)
Z2, Y2 = ZY(243e-9, 0.6e-9, 300e-9, 180e-12, 150e-12, 0.5e-12, 2500, 3000, 10)
G2, TV2, *_ = modes(Z2, Y2)
print("unequal: voltage ratios V2/V1 of the two modes:", np.round(TV2[1]/TV2[0], 3))
# 3. beat length of our pair
for f, dn in ((10e9, 2e-4), (30e9, 1.7e-4)):
    Lb = c0/(f*dn)
    print(f"{f/1e9:.0f} GHz, dn = {dn}: full exchange after {Lb/2:.0f} m; at 14 mm |V2/V1| = {np.tan(np.pi*14e-3/Lb):.2e}")
