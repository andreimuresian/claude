"""
Independent cross-check of the conductor-interior reference: a 2D PEEC
(partial-element equivalent circuit, the method of FastHenry / Ansys Q2D's
conductor solver) for the CPW series impedance R(f), L(f).

Method (no mesh outside the metal, no outer boundary, no FEM):
  * every electrode is cut into rectangular filaments, each carrying a uniform
    current I_i (graded: fine at the surfaces, where the skin current flows);
  * Ohm's law + Faraday's law along each filament, per unit length:
        I_i / (sigma A_i) + j w sum_j L_ij I_j = V_k      (filament i in conductor k)
    with the exact 2D partial inductance of two rectangles,
        L_ij = -mu0 / (2 pi) * < ln r >_ij   (mean log distance, closed form);
  * sum of I_i over conductor k = imposed current.
The free-space Green's function replaces the air mesh, so this shares nothing
with eddy_tensor.py except the geometry and sigma.
"""
import json
import time

import numpy as np

MU0 = 4e-7 * np.pi
SIGMA_AU = 4.56e7


def _F(u, v):
    """F_uuvv = ln(u^2 + v^2); even in u and v (derived and checked with sympy)."""
    u, v = np.abs(u), np.abs(v)
    r2 = u * u + v * v
    lg = np.where(r2 > 0, np.log(np.where(r2 > 0, r2, 1.0)), 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        at1 = np.where(u > 0, np.arctan(v / np.where(u > 0, u, 1.0)), 0.0)
        at2 = np.where(v > 0, np.arctan(u / np.where(v > 0, v, 1.0)), 0.0)
    return ((u * u * v * v / 4 - u ** 4 / 24 - v ** 4 / 24) * lg
            + u ** 3 * v * at1 / 3 + u * v ** 3 * at2 / 3 - 25 * u * u * v * v / 24)


def mean_log(ra, rb):
    """<ln r> between rectangles ra = (x1, x2, y1, y2) and rb (arrays broadcast)."""
    x1, x2, y1, y2 = ra
    x3, x4, y3, y4 = rb
    s = 0.0
    for xa, xb, sx in ((x2, x3, 1), (x1, x4, 1), (x1, x3, -1), (x2, x4, -1)):
        for ya, yb, sy in ((y2, y3, 1), (y1, y4, 1), (y1, y3, -1), (y2, y4, -1)):
            s = s + sx * sy * _F(xa - xb, ya - yb)
    area = (x2 - x1) * (y2 - y1) * (x4 - x3) * (y4 - y3)
    return 0.5 * s / area


def graded_edges(a, b, h_a, h_b, h_max, r=1.15):
    """Cell edges from a to b, size h_a at a and h_b at b (None = coarse)."""
    def side(h0):
        e, h = [0.0], h0
        while e[-1] < (b - a) / 2:
            e.append(e[-1] + h); h = min(h * r, h_max)
        return np.array(e)
    left = side(h_a if h_a else h_max)
    right = side(h_b if h_b else h_max)
    pts = np.concatenate([a + left[left < (b - a) / 2], b - right[right < (b - a) / 2]])
    pts = np.unique(np.concatenate([[a, b], pts]))
    keep = [pts[0]]
    for p in pts[1:-1]:
        if p - keep[-1] > 0.4 * min(h_a or h_max, h_b or h_max) and pts[-1] - p > 0.4 * min(h_a or h_max, h_b or h_max):
            keep.append(p)
    keep.append(pts[-1])
    return np.array(keep)


def filaments(sig_w, gap, gnd_w, t, h_s, h_max_x=1.0, h_max_y=0.3):
    """Half structure x >= 0: half signal [0, S/2] and the right ground."""
    xs, xgi = sig_w / 2, sig_w / 2 + gap
    xgo = xgi + gnd_w
    ey = graded_edges(0.0, t, h_s, h_s, h_max_y)
    rects, cond = [], []
    for k, ex in ((1, graded_edges(0.0, xs, None, h_s, h_max_x)),
                  (2, graded_edges(xgi, xgo, h_s, h_s, h_max_x))):
        X1, Y1 = np.meshgrid(ex[:-1], ey[:-1], indexing="ij")
        X2, Y2 = np.meshgrid(ex[1:], ey[1:], indexing="ij")
        for a in (X1, X2, Y1, Y2):
            pass
        rects.append(np.column_stack([X1.ravel(), X2.ravel(), Y1.ravel(), Y2.ravel()]))
        cond.append(np.full(X1.size, k))
    return np.vstack(rects) * 1e-6, np.concatenate(cond)


def solve_Z(f_list, sig_w=35.0, gap=4.15, gnd_w=50.0, t=2.0, h_s=0.04, sigma=SIGMA_AU, block=600):
    t0 = time.time()
    R, cond = filaments(sig_w, gap, gnd_w, t, h_s)
    n = len(R)
    Rm = R.copy(); Rm[:, 0], Rm[:, 1] = -R[:, 1], -R[:, 0]       # mirror images x -> -x
    L = np.empty((n, n))
    for i0 in range(0, n, block):
        a = tuple(R[i0:i0 + block, c][:, None] for c in range(4))
        b = tuple(R[:, c][None, :] for c in range(4))
        bm = tuple(Rm[:, c][None, :] for c in range(4))
        L[i0:i0 + block] = -MU0 / (2 * np.pi) * (mean_log(a, b) + mean_log(a, bm))
    area = (R[:, 1] - R[:, 0]) * (R[:, 3] - R[:, 2])
    Ik = np.array([0.5, -0.5])
    B = np.column_stack([(cond == k).astype(float) for k in (1, 2)])
    out = []
    for f in np.atleast_1d(f_list):
        w = 2 * np.pi * f
        Zm = 1j * w * L + np.diag(1.0 / (sigma * area))
        # [Zm  -B] [I]   [0 ]
        # [B^T  0] [V] = [Ik]
        M = np.block([[Zm, -B], [B.T, np.zeros((2, 2))]])
        x = np.linalg.solve(M, np.concatenate([np.zeros(n), Ik]))
        V = x[n:]
        Z = V[0] - V[1]
        out.append(dict(f_GHz=f / 1e9, R=Z.real, L=Z.imag / w))
    return out, dict(n_fil=n, t_s=time.time() - t0)


if __name__ == "__main__":
    # self-test of the closed form against brute-force quadrature
    ra, rb = (0.0, 1.0, 0.0, 0.5), (1.3, 2.0, -0.2, 0.9)
    g = (np.arange(60) + 0.5) / 60
    xa = ra[0] + (ra[1] - ra[0]) * g; ya = ra[2] + (ra[3] - ra[2]) * g
    xb = rb[0] + (rb[1] - rb[0]) * g; yb = rb[2] + (rb[3] - rb[2]) * g
    XA, YA, XB, YB = np.meshgrid(xa, ya, xb, yb, indexing="ij", sparse=True)
    brute = np.log(np.hypot(XA - XB, YA - YB)).mean()
    print("mean ln r: closed form", mean_log(ra, rb), " quadrature", brute)
    sq = (0.0, 1.0, 0.0, 1.0)
    print("self term of a unit square: closed form", mean_log(sq, sq), " exact ln(0.44705) =", np.log(0.447049))
    f = [1e9, 10e9, 20e9, 60e9, 100e9, 200e9]
    rows = []
    for hs in (0.06, 0.04, 0.025):
        r, info = solve_Z(f, h_s=hs)
        print(hs, info)
        for x in r:
            print("   ", {k: round(float(v), 6) for k, v in x.items()})
        rows.append(dict(h_s=hs, info=info, res=r))
    json.dump(rows, open("results/peec_bend.json", "w"), indent=1, default=float)
