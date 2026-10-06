"""Coworker's CST bend (S 35, gaps 4.5, grounds 49.5 um, Au 2 um, R 102.5 um,
180 deg, lumped ports) vs the 2D models of the same cross-section on the
user's bend stack. The CST curve is the fitted alpha = 0.3519 sqrt(f) + 0.03419 f."""
import json

import numpy as np

import eddy_tensor as ET
import qs_tensor
from cpw_analytic import BEND_LAYERS, BEND_SIGMA, C0, DB_PER_NEPER as DB, bend_cpw

UM = 1e-6
f = np.array([1, 5, 10, 20, 40, 60, 80, 100, 130, 160, 200.0])
Ce, Ca, _ = qs_tensor.capacitance(35.0, 4.5, 49.5, 2.0)
res, _ = ET.solve_Z(f * 1e9, hfine=0.06, sig_w=35.0, gap=4.5, gnd_w=49.5, t=2.0)
R = np.array([x["R"] for x in res]); L = np.array([x["L"] for x in res])
w = 2 * np.pi * f * 1e9
g = np.sqrt((R + 1j * w * L) * (1j * w * Ce))
a_ref, n_ref, Z_ref = DB * g.real / 100, g.imag / w * C0, np.abs(np.sqrt((R + 1j * w * L) / (1j * w * Ce)))
an = bend_cpw(f * 1e9, 35 * UM, 4.5 * UM, 49.5 * UM, 2 * UM, BEND_LAYERS, layer_sigma=BEND_SIGMA)
cst = 0.3519 * np.sqrt(f) + 0.03419 * f
print(f"{'f GHz':>6} | {'a_ref':>6} {'a_ana':>6} {'a_CST':>6} | {'n_ref':>6} {'n_ana':>6} | {'Z_ref':>6} {'Z_ana':>6}")
for i in range(len(f)):
    print(f"{f[i]:6.0f} | {a_ref[i]:6.2f} {an['alpha_dB_cm'][i]:6.2f} {cst[i]:6.2f} | {n_ref[i]:6.3f} {an['n_m'][i]:6.3f} |"
          f" {Z_ref[i]:6.2f} {an['Z0'][i]:6.2f}")
# slot-path difference of the 180-degree turn and the resulting CPW -> slotline conversion (no ground straps)
dL = np.pi * (35 + 4.5) * UM
dphi = 2 * np.pi * f * 1e9 * n_ref / C0 * dL
conv_dB = -10 * np.log10(np.cos(dphi / 2) ** 2)
print("slot path difference", round(dL / UM, 1), "um; CPW power converted to the slotline mode per turn (dB):",
      dict(zip(f.astype(int).tolist(), conv_dB.round(3).tolist())))
json.dump(dict(f=f.tolist(), a_ref=a_ref.tolist(), a_ana=an["alpha_dB_cm"].tolist(), a_cst=cst.tolist(),
               n_ref=n_ref.tolist(), Z_ref=Z_ref.tolist(), conv_dB=conv_dB.tolist()),
          open("results/coworker_check.json", "w"), indent=1)
