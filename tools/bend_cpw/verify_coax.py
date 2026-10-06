"""
Code verification of the conductor-interior solver (eddy_tensor.solve_on_mesh)
against an exact solution: a gold coax (wire of radius a, return tube b..c),
whose series impedance is known in closed form from Bessel functions:

    Z = Z_wire(a) + Z_tube(b, c) + j w mu0/(2 pi) ln(b/a)

The FEM solve uses the very same function, element order and current
constraints as the CPW reference; only the mesh differs (a graded polar mesh).
"""
import json

import numpy as np
from scipy.special import hankel1e, hankel2e, jve
from skfem import MeshTri

import eddy_tensor as E

MU0, SIG = E.MU0, E.SIGMA_AU
A_W, B_T, C_T, R_BOX = 3e-6, 6e-6, 8e-6, 10e-6


def exact(f):
    w = 2 * np.pi * f
    k = np.sqrt(-1j * w * MU0 * SIG)                 # E'' + E'/r + k^2 E = 0, Im k < 0
    z_wire = k * jve(0, k * A_W) / (2 * np.pi * A_W * SIG * jve(1, k * A_W))
    # tube b..c carrying -1: E = p H0(1)(kr) e^{ik(r-c)}/s1 + q H0(2)(kr) e^{-ik(r-b)}/s2
    # (scaled Hankel functions, each factor bounded), E'(c) = 0, int sigma E dA = -1
    eb, ec = np.exp(1j * k * (B_T - C_T)), np.exp(-1j * k * (C_T - B_T))
    M = np.array([[hankel1e(1, k * C_T), hankel2e(1, k * C_T) * ec],
                  [hankel1e(1, k * B_T) * eb, hankel2e(1, k * B_T)]])
    rhs = np.array([0.0, k / (2 * np.pi * SIG * B_T)])   # -E'(b)/k
    p, q = np.linalg.solve(M, rhs)
    e_b = p * hankel1e(0, k * B_T) * eb + q * hankel2e(0, k * B_T)
    z_tube = -e_b                                     # drop per unit current, tube carries -1
    return z_wire + z_tube + 1j * w * MU0 / (2 * np.pi) * np.log(B_T / A_W)


def radii(h_surf, h_max, r=1.12):
    """Graded radial nodes, fine at every metal surface."""
    def seg(r0, r1, h0, h1):
        x, h = [r0], h0
        while x[-1] < (r0 + r1) / 2:
            x.append(x[-1] + h); h = min(h * r, h_max)
        y, h = [r1], h1
        while y[-1] > (r0 + r1) / 2:
            y.append(y[-1] - h); h = min(h * r, h_max)
        pts = np.array(sorted(set(x[:-1]) | set(y[:-1])))
        return pts
    hc = 0.25e-6
    out = np.concatenate([seg(0, A_W, hc, h_surf), seg(A_W, B_T, h_surf, h_surf),
                          seg(B_T, C_T, h_surf, h_surf), seg(C_T, R_BOX, h_surf, 1e-6), [R_BOX]])
    return np.unique(np.round(out, 12))


def polar_mesh(h_surf, n_theta, h_max=0.25e-6):
    rr = radii(h_surf, h_max)
    rr = rr[rr > 0]
    th = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    pts = [np.zeros(2)]
    for r in rr:
        pts.append(np.column_stack([r * np.cos(th), r * np.sin(th)]))
    p = np.vstack([pts[0][None, :]] + pts[1:]).T
    tri = []
    nt = n_theta
    for j in range(nt):                               # centre fan
        tri.append([0, 1 + j, 1 + (j + 1) % nt])
    for i in range(len(rr) - 1):
        o0, o1 = 1 + i * nt, 1 + (i + 1) * nt
        for j in range(nt):
            a, b = o0 + j, o0 + (j + 1) % nt
            c, d = o1 + j, o1 + (j + 1) % nt
            tri += [[a, b, d], [a, d, c]]
    mesh = MeshTri(p, np.array(tri).T)
    rc = np.hypot(*mesh.p[:, mesh.t].mean(axis=1))
    cond = np.where(rc < A_W, 1, np.where((rc > B_T) & (rc < C_T), 2, 0))
    return mesh, cond


def fem(f_list, h_surf, n_theta):
    mesh, cond = polar_mesh(h_surf, n_theta)
    rmax = np.hypot(*mesh.p).max()
    Vs, info = E.solve_on_mesh(mesh, cond, [1.0, -1.0],
                               lambda x: np.hypot(x[0], x[1]) > rmax * (1 - 1e-9), f_list)
    return [-(V[0] - V[1]) for V in Vs], info


if __name__ == "__main__":
    f = np.array([1e6, 1e9, 10e9, 60e9, 200e9])
    rows = []
    # the polygonal circle has area (n/2pi) sin(2pi/n) of the true one
    for h, nth in ((0.06e-6, 192), (0.04e-6, 320)):
        Zf, info = fem(f, h, nth)
        poly = nth / (2 * np.pi) * np.sin(2 * np.pi / nth)
        for fi, zf in zip(f, Zf):
            ze = exact(fi)
            w = 2 * np.pi * fi
            rows.append(dict(h_um=h * 1e6, n_theta=nth, f_GHz=fi / 1e9, R_exact=ze.real, R_fem=zf.real,
                             dR_pct=(zf.real / ze.real - 1) * 100,
                             L_exact=ze.imag / w, L_fem=zf.imag / w, dL_pct=(zf.imag / ze.imag - 1) * 100,
                             polygon_area_pct=(poly - 1) * 100))
            print({k: (round(v, 5) if isinstance(v, float) else v) for k, v in rows[-1].items()})
        print(info)
    print("DC check: R_dc exact =", 1 / (SIG * np.pi * A_W ** 2) + 1 / (SIG * np.pi * (C_T ** 2 - B_T ** 2)))
    json.dump(rows, open("results/verify_coax.json", "w"), indent=1, default=float)
