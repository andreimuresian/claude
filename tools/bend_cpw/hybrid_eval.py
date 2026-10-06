"""Hybrid model on the 23 validation geometries: C from qs_tensor (P2 tensor FEM,
seconds), L_ext from boundary elements, R and L_int from the analytical
thick-conductor model. Compared with the reference (conductor-interior R, L +
notebook-FEM C) at 20 / 60 / 150 GHz."""
import json

import numpy as np

import bem_pec
import qs_tensor
from cpw_analytic import C0, DB_PER_NEPER as DB, conductor_impedance

UM = 1e-6
doe = [json.loads(l) for l in open("results/doe_eddy.jsonl")]
E = {"n": [], "Z": [], "a": []}
rows = []
for r in doe:
    stack = [(r["h"], 3.9, 3.9)] + qs_tensor.BEND_STACK[1:]
    Ce, Ca, info = qs_tensor.capacitance(r["S"], r["W"], 50.0, r["t"], stack)
    S, W, t = r["S"] * UM, r["W"] * UM, r["t"] * UM
    f = np.array(r["f"]) * 1e9
    w = 2 * np.pi * f
    L_ext = 1 / (C0 ** 2 * bem_pec.solve(S, W, 50 * UM, t)["C_air"])
    R, L_int, _ = conductor_impedance(f, S, W, 50 * UM, t, L_ext=L_ext)
    def line(R, L, C):
        g = np.sqrt((R + 1j * w * L) * (1j * w * C))
        return DB * g.real / 100, g.imag / w * C0, np.abs(np.sqrt((R + 1j * w * L) / (1j * w * C)))
    a_h, n_h, Z_h = line(R, L_ext + L_int, Ce)
    a_r, n_r, Z_r = line(np.array(r["R"]), np.array(r["L"]), r["C_eps"])
    E["n"].append((n_h / n_r - 1) * 100); E["Z"].append((Z_h / Z_r - 1) * 100); E["a"].append((a_h / a_r - 1) * 100)
    rows.append(dict(S=r["S"], W=r["W"], t=r["t"], h=r["h"], C_tensor=Ce, C_fem=r["C_eps"], t_s=info["t_s"]))
    print(r["S"], r["W"], r["t"], np.round(E["n"][-1], 2), np.round(E["Z"][-1], 2), np.round(E["a"][-1], 2), flush=True)
for k in E:
    e = np.array(E[k])
    print(f"{k}: mean {e.mean(0).round(2)} rms {np.sqrt((e**2).mean(0)).round(2)} max|.| {np.abs(e).max(0).round(2)}")
json.dump(dict(rows=rows, err={k: np.array(v).tolist() for k, v in E.items()}), open("results/hybrid_eval.json", "w"), indent=1)
