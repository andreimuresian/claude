"""
Conductor-interior R' at 60 GHz for the 13 COMSOL rows of the user's notebook
(cell [5]), compared with the COMSOL IBC attenuation of the same rows.

alpha_new = R'_interior / (2 Z0_COMSOL) (+ the dielectric part, < 0.01 dB/cm in
these rows). Only the electrode geometry enters R' (auc_w, gap, au_h, grounds
70 um); the dielectrics do not change the current distribution.
Also reported: the converged IBC limit (boundary elements), i.e. what the
COMSOL/femwell IBC would give with an infinitely fine corner mesh.
"""
import json

import numpy as np

import bem_pec
import eddy_tensor as ET

DB = 20 * np.log10(np.e)
ROWS = [
    (60.952, 4.448, 13.336, 3.340, 0.267, 1.65277, 21.5855, 21.4999, 0.49823, 4.39295),
    (78.739, 5.662, 13.680, 3.145, 0.319, 1.68009, 23.5443, 23.3862, 0.49775, 3.51817),
    (63.592, 5.053, 10.779, 3.152, 0.283, 1.71652, 24.7213, 24.5936, 0.49802, 3.88527),
    (75.167, 6.486, 12.843, 2.751, 0.179, 1.74925, 25.2278, 25.0621, 0.49780, 3.21756),
    (78.024, 7.285, 14.935, 5.671, 0.280, 1.72163, 25.4456, 25.2575, 0.49759, 2.92163),
    (8.011, 6.820, 14.028, 3.798, 0.220, 1.50951, 37.7845, 37.7902, 0.49920, 3.44720),
    (79.683, 13.729, 3.198, 6.626, 0.253, 2.06870, 40.9653, 40.5784, 0.49771, 1.90493),
    (49.485, 4.098, 7.693, 2.525, 0.329, 1.72715, 26.2526, 26.1627, 0.49826, 4.54752),
    (50.995, 19.998, 7.615, 4.543, 0.124, 2.00253, 46.9215, 46.5939, 0.49768, 1.56550),
    (56.365, 13.964, 1.006, 9.639, 0.314, 2.09527, 47.5107, 47.1921, 0.49807, 1.97977),
    (16.961, 14.051, 14.994, 2.996, 0.350, 1.63038, 48.0871, 48.0078, 0.49843, 1.90944),
    (10.625, 17.794, 4.964, 14.997, 0.238, 1.88020, 71.5774, 71.4678, 0.49877, 2.15844),
    (78.509, 9.642, 12.150, 6.779, 0.100, 1.85910, 29.7362, 29.4948, 0.49754, 2.41693),
]
UM = 1e-6

if __name__ == "__main__":
    out = []
    Rs = np.sqrt(np.pi * 60e9 * 4e-7 * np.pi / 4.56e7)
    print(f"{'auc_w':>7}{'gap':>7}{'au_h':>7} | {'COMSOL a':>9}{'interior a':>11}{'delta':>8} | {'IBC limit a':>12}")
    for r in ROWS:
        S, W, t = r[:3]
        res, info = ET.solve_Z([60e9], hfine=0.04, sig_w=S, gap=W, gnd_w=70.0, t=t)
        R_int = res[0]["R"]
        Z0 = r[6]
        a_new = DB * R_int / (2 * Z0) / 100
        R_lim = Rs * bem_pec.solve(S * UM, W * UM, 70 * UM, t * UM, h_min_rel=1e-7)["G_pec"]
        a_lim = DB * R_lim / (2 * Z0) / 100
        out.append(dict(auc_w=S, gap=W, au_h=t, alpha_comsol=r[9], alpha_interior=a_new, alpha_ibc_limit=a_lim,
                        R_interior=R_int, R_ibc_limit=R_lim, Z0=Z0, t_s=info["t_s"]))
        print(f"{S:7.2f}{W:7.2f}{t:7.2f} | {r[9]:9.3f}{a_new:11.3f}{(a_new / r[9] - 1) * 100:7.1f}% | {a_lim:12.3f}",
              flush=True)
    json.dump(out, open("results/comsol_rows.json", "w"), indent=1)
    d = np.array([o["alpha_interior"] / o["alpha_comsol"] - 1 for o in out]) * 100
    print(f"interior vs COMSOL IBC: mean {d.mean():+.1f} %, min {d.min():+.1f} %, max {d.max():+.1f} %")
