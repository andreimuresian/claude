"""
Universal finite-skin-depth correction of the IBC loss at a 90-degree metal
corner, from a canonical problem that is NOT part of the CPW validation set:
an isolated square gold bar (side a), its return current on a far box.

Near a corner the PEC surface current behaves as  J/I = K r^(-1/3)  on both
faces. The IBC integral  Rs * int (J/I)^2 dl  is finite, but it treats the
corner as if every point of each face were a flat half-space. The real current
spreads over a skin depth there, and dimensional analysis of the local problem
(a conducting wedge in a singular field) gives

    R_true = Rs * ( G_pec - c * sum_corners K^2 * delta^(1/3) ) + O(delta)

with c a pure number for a right-angle corner. This script extracts c from the
eddy-current solution of the bar at several frequencies, and checks that the
deficit really scales as delta^(1/3).
"""
import json

import numpy as np
from skfem import MeshTri

import eddy_tensor as ET

MU0, SIG = ET.MU0, ET.SIGMA_AU
EPS0 = 8.8541878128e-12


def bem_isolated_square(a, h_min_rel=1e-7, ratio=1.12, h_max_rel=0.02):
    """Isolated square conductor (side a), total charge 1: rho on the quarter
    perimeter (x, y >= 0) with images. Returns G_pec and the corner K."""
    from bem_pec import _seg_logint, graded_side
    h = a / 2
    segs = []
    for p0, p1 in (((0.0, h), (h, h)), ((h, h), (h, 0.0))):
        L = np.hypot(p1[0] - p0[0], p1[1] - p0[1])
        fine0 = p0 == (h, h)
        u = graded_side(L, h_min_rel * a, ratio, h_max_rel * a, fine0, not fine0) / L
        P = np.array(p0)[None, :] + u[:, None] * (np.array(p1) - np.array(p0))[None, :]
        segs += [(q0[0], q0[1], q1[0], q1[1]) for q0, q1 in zip(P[:-1], P[1:])]
    ax, ay, bx, by = np.array(segs).T
    mx, my = (ax + bx) / 2, (ay + by) / 2
    Ls = np.hypot(bx - ax, by - ay)
    n = len(ax)
    K = np.zeros((n, n))
    for sx in (1, -1):
        for sy in (1, -1):
            K += _seg_logint(mx[:, None], my[:, None], (sx * ax)[None], (sy * ay)[None],
                             (sx * bx)[None], (sy * by)[None])
    K *= -1 / (2 * np.pi * EPS0)
    A = np.zeros((n + 1, n + 1))
    A[:n, :n] = K
    A[:n, n] = -1.0
    A[n, :n] = 4 * Ls
    rho = np.linalg.solve(A, np.concatenate([np.zeros(n), [1.0]]))[:n]
    G = 4 * np.sum(rho ** 2 * Ls)
    r = np.hypot(mx - h, my - h)
    sel = (r > 1e-6 * a) & (r < 1e-4 * a)
    Kc = np.median(rho[sel] * r[sel] ** (1 / 3))
    return G, Kc


def eddy_square(a, f_list, hfine, box=60.0):
    """Quarter domain of the bar, A = 0 on the far box, symmetry planes natural."""
    h = a / 2
    x = ET.axis([0.0, h * 1e6, box * h * 1e6], hfine, 0.25 * h * 1e6, 0.5 * box * h * 1e6, [(0, h * 1e6)], 1.12)
    mesh = MeshTri.init_tensor(x * 1e-6, x * 1e-6)
    c = mesh.p[:, mesh.t].mean(axis=1)
    cond = ((c[0] < h) & (c[1] < h)).astype(int)
    xm = mesh.p.max()
    Vs, info = ET.solve_on_mesh(mesh, cond, [0.25], lambda X: (np.abs(X[0] - xm) < 1e-15) | (np.abs(X[1] - xm) < 1e-15),
                                f_list)
    return np.array([(-V[0]).real for V in Vs]), info


if __name__ == "__main__":
    a = 10e-6
    G, Kc = bem_isolated_square(a)
    print(f"square a = {a*1e6} um: G_pec = {G:.2f} 1/m, corner K = {Kc:.4e} m^-2/3,  G*a = {G*a:.5f}")
    f = np.array([20e9, 50e9, 100e9, 200e9, 400e9, 800e9])
    out = []
    for hf in (0.02, 0.01):
        R, info = eddy_square(a, f, hf)
        Rs = np.sqrt(np.pi * f * MU0 / SIG)
        delta = 1 / np.sqrt(np.pi * f * MU0 * SIG)
        dG = G - R / Rs                                   # deficit of the true R vs IBC
        c = dG / (4 * Kc ** 2 * delta ** (1 / 3))
        print("hfine", hf, info)
        for fi, d, ri, dg, ci in zip(f, delta, R, dG, c):
            print(f"   f {fi/1e9:6.0f} GHz  delta/a {d/a:.4f}  R {ri:10.3f}  R_IBC {np.sqrt(np.pi*fi*MU0/SIG)*G:10.3f}"
                  f"  deficit {dg/G*100:6.3f} %   c = {ci:.4f}")
        out.append(dict(hfine=hf, f=f.tolist(), R=R.tolist(), c=c.tolist(), G=G, K=Kc))
    json.dump(out, open("results/corner_constant.json", "w"), indent=1)
