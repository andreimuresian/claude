"""
(Production copy of tools/bend_cpw/bem_pec.py.)

PEC surface current of a thick CPW and its perturbational (IBC / Wheeler)
conductor resistance, by a boundary-element method in a homogeneous medium.

For a quasi-TEM line the surface current is proportional to the surface charge
of the electrostatic problem in a homogeneous medium (the "air" problem), so
    R'_IBC = Rs * contour (J_s / I)^2 dl = Rs * contour (rho / Q)^2 dl = Rs * G_pec.
This is exactly the quantity the femwell/COMSOL IBC post-processing integrates.
Here it is computed with panels graded geometrically into the electrode
corners (smallest panel 1e-6 of the metal thickness), so the r^(-1/3) corner
singularity is resolved and G_pec is converged; a volume mesh cannot afford
that grading.

Method: constant charge density per straight panel, collocation at the panel
mid-points, exact integral of ln r over a panel, images for the two symmetry
planes (x = 0, and y = t/2: the homogeneous problem is symmetric about the
metal mid-plane), net charge zero.
"""
import numpy as np

EPS0 = 8.8541878128e-12
C0 = 299792458.0


def _seg_logint(px, py, ax, ay, bx, by):
    """int over the segment A->B of ln|P - r'| dl' (arrays broadcast)."""
    L = np.hypot(bx - ax, by - ay)
    tx, ty = (bx - ax) / L, (by - ay) / L
    s1 = (ax - px) * tx + (ay - py) * ty
    s2 = s1 + L
    d = np.abs((ax - px) * ty - (ay - py) * tx)

    def prim(s):
        r2 = s * s + d * d
        lg = np.where(r2 > 0, 0.5 * np.log(np.where(r2 > 0, r2, 1.0)), 0.0)
        with np.errstate(divide="ignore", invalid="ignore"):
            at = np.where(d > 0, d * np.arctan(s / np.where(d > 0, d, 1.0)), 0.0)
        return s * lg - s + at
    return prim(s2) - prim(s1)


def graded_side(length, h_min, ratio, h_max, fine_start=True, fine_end=True):
    """Panel end-points on [0, length], geometric from h_min at fine ends."""
    def run(n_target):
        e, h = [0.0], h_min
        while e[-1] < n_target:
            e.append(e[-1] + h); h = min(h * ratio, h_max)
        return np.array(e)
    if fine_start and fine_end:
        a = run(length / 2); a = a[a < length / 2]
        pts = np.concatenate([a, length - a[::-1], [length / 2]])
    elif fine_start:
        a = run(length); pts = a[a < length]
    elif fine_end:
        a = run(length); pts = length - a[a < length]
    else:
        pts = np.linspace(0, length, max(2, int(np.ceil(length / h_max)) + 1))
    pts = np.unique(np.concatenate([[0.0, length], pts]))
    return pts


def panels(S, W, Wg, t, h_min_rel=1e-6, ratio=1.15, h_max_rel=0.05):
    """Quarter structure (x >= 0, y >= t/2). Returns panel end points and conductor id."""
    xs, xgi = S / 2, S / 2 + W
    xgo = xgi + Wg
    hmin, hmax = h_min_rel * t, h_max_rel * t
    hmax_wide = max(hmax, 0.02 * min(S, Wg))
    segs = []

    def add(p0, p1, cid, fine0, fine1, hm):
        L = np.hypot(p1[0] - p0[0], p1[1] - p0[1])
        u = graded_side(L, hmin, ratio, hm, fine0, fine1) / L
        P = np.array(p0)[None, :] + u[:, None] * (np.array(p1) - np.array(p0))[None, :]
        for a, b in zip(P[:-1], P[1:]):
            segs.append((a[0], a[1], b[0], b[1], cid))
    ym = t / 2
    add((0.0, t), (xs, t), 1, False, True, hmax_wide)        # signal top, corner at x = xs
    add((xs, t), (xs, ym), 1, True, False, hmax)             # signal sidewall (upper half)
    add((xgi, ym), (xgi, t), 2, False, True, hmax)           # ground inner sidewall
    add((xgi, t), (xgo, t), 2, True, True, hmax_wide)        # ground top
    add((xgo, t), (xgo, ym), 2, True, False, hmax)           # ground outer sidewall
    return np.array(segs)


def solve(S, W, Wg, t, **kw):
    """Returns dict(C_air [F/m], G_pec [1/m], rho/Q per panel, panels)."""
    P = panels(S, W, Wg, t, **kw)
    ax, ay, bx, by, cid = P.T
    mx, my = (ax + bx) / 2, (ay + by) / 2
    L = np.hypot(bx - ax, by - ay)
    n = len(P)
    # images: (x, y), (-x, y), (x, t - y), (-x, t - y)
    K = np.zeros((n, n))
    for sx in (1, -1):
        for flip in (False, True):
            ay2 = t - ay if flip else ay
            by2 = t - by if flip else by
            K += _seg_logint(mx[:, None], my[:, None], (sx * ax)[None, :], ay2[None, :],
                             (sx * bx)[None, :], by2[None, :])
    K *= -1.0 / (2 * np.pi * EPS0)
    # unknowns: rho (n), constant c; phi_m = K rho + c = V_m ; sum rho L = 0
    A = np.zeros((n + 1, n + 1))
    A[:n, :n] = K
    A[:n, n] = 1.0
    A[n, :n] = L
    rhs = np.concatenate([(cid == 1).astype(float), [0.0]])
    sol = np.linalg.solve(A, rhs)
    rho = sol[:n]
    Q = 4 * np.sum(rho[cid == 1] * L[cid == 1])          # full signal charge for 1 V
    G = 4 * np.sum(rho ** 2 * L) / Q ** 2
    # corner amplitudes: J/I = rho/Q ~ K r^(-1/3) next to each corner
    xs, xgi = S / 2, S / 2 + W
    Kc = []
    for cx in (xs, xgi, xgi + Wg):
        r = np.hypot(mx - cx, my - t)
        sel = (r > 3 * kw.get("h_min_rel", 1e-6) * t) & (r < 1e-4 * t)
        Kc.append(float(np.median(np.abs(rho[sel] / Q) * r[sel] ** (1 / 3))) if sel.any() else 0.0)
    return dict(C_air=Q, G_pec=G, rho_over_Q=rho / Q, panels=P, n=n, K_corners=Kc)


def R_ibc(f, S, W, Wg, t, sigma=4.56e7, **kw):
    Rs = np.sqrt(np.pi * np.asarray(f) * 4e-7 * np.pi / sigma)
    return Rs * solve(S, W, Wg, t, **kw)["G_pec"]
