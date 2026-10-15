"""Remove the 50-ohm port mismatch: re-express the CST S-matrices with
36.66-ohm reference impedance (about the line's own Zc) at all four ports."""
import numpy as np, matplotlib.pyplot as plt
from first_look_lib import load4

def renorm(S, z0=50.0, zr=36.66):
    I = np.eye(4)
    Z = z0*(I + S) @ np.linalg.inv(I - S)          # impedance matrix
    return (Z - zr*I) @ np.linalg.inv(Z + zr*I)     # S with new reference

db = lambda x: 20*np.log10(abs(x))
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for fn, lab, c in [("LINEA0_1MM_200UM_PITCH.s4p", "1 mm", "0.6"), ("LINEA0_5MM_200UM_PITCH.s4p", "5 mm", "k")]:
    f, S = load4(fn); G = f/1e9; Sr = renorm(S)
    for a, (r, name) in zip(ax, [(2, "NEXT S31"), (3, "FEXT S41")]):
        a.plot(G, db(S[:, r, 0]), color=c, lw=.8, ls=":", label=f"{lab}, 50 ohm ports (CST)")
        a.plot(G, db(Sr[:, r, 0]), color=c, lw=1.8, label=f"{lab}, 36.66 ohm ports (matched)")
        a.set_title(name); a.set_xlabel("Frequency (GHz)"); a.set_ylabel("dB"); a.grid(alpha=.3)
    k = lambda g: np.argmin(abs(G-g))
    print(lab, "matched: " + "  ".join(f"{g}GHz NEXT {db(Sr[k(g),2,0]):.1f} FEXT {db(Sr[k(g),3,0]):.1f}" for g in (1, 10, 15, 30, 60)))
ax[0].legend(fontsize=8)
plt.tight_layout(); plt.savefig("renorm.png", dpi=130)
