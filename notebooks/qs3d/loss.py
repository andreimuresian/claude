"""Step 1: conductor loss of the 3D unit cell, and the tee's perturbation factors.

R' (ohm/m) from the high-frequency magnetostatic solve of qs3d.inductance (PEC
metal, current I = 1 A, quarter cell), with the surface resistance
Rs = 1/(sigma delta), two ways:

  surface : Rs * 4 * sum over metal faces of |H_t|^2 dA / P        (IBC)
            H_t from the cell-centred gradient of psi next to the face.
  wheeler : Rs * (L'(a) - L'(0)) / (mu0 a), every metal face receded by a
            (Wheeler's incremental-inductance rule = the converged value of the
            same IBC integral, ../xsec/README.md).  Both solves on one grid:
            the lines at distance a inside every metal face are in both.

Perturbation factors, tee cell over the no-slot cell of the same grid:
  L = L'(0) + R'/w (internal inductance),  n ~ sqrt(L C),  Z0 ~ sqrt(L / C),
  alpha_c = R' / (2 Z0)  ->  F_n, F_Z, F_R, F_alpha = F_R / F_Z.
"""
import numpy as np

import qs3d as q

SIGMA_AU, F0 = 4.56e7, 60e9
W = 2*np.pi*F0
DELTA = np.sqrt(2.0/(W*q.MU0*SIGMA_AU))
RS = 1.0/(SIGMA_AU*DELTA)


def _cell_grad(m, info):
    """d psi / d axis at every cell centre (zero-gradient on metal and Neumann faces)."""
    psi, faces, jumps, dv, free = (info[k] for k in ("psi", "faces", "jumps", "dv", "free"))
    shape = psi.shape
    out = []
    for ax, ((s0, s1, T), jp) in enumerate(zip(faces, jumps)):
        h = m['d'][ax]
        dist = 0.5*(h[:-1] + h[1:])
        dist = dist.reshape([-1 if i == ax else 1 for i in range(3)])
        ok = free[s0] & free[s1]
        gf = np.where(ok, (psi[s1] - psi[s0] - jp)/dist, 0.0)        # face gradients
        lo = np.zeros(shape); hi = np.zeros(shape)
        s_lo = [slice(None)]*3; s_lo[ax] = slice(1, None)            # cell i: lower face i-1
        s_hi = [slice(None)]*3; s_hi[ax] = slice(0, -1)              # cell i: upper face i
        lo[tuple(s_lo)] = gf; hi[tuple(s_hi)] = gf
        if ax == 0:                                                  # x = 0: Dirichlet psi = dv
            lo[0] = np.where(free[0], (psi[0] - dv[0])/(h[0]/2), 0.0)
        out.append(0.5*(lo + hi))
    return out


def surface_R(m, info):
    """IBC conductor resistance R' [ohm/m] of the full cell from the quarter-cell solve."""
    free = info["free"]
    G = _cell_grad(m, info)
    dx, dy, dz = m['d']
    widths = (dx[:, None, None], dy[None, :, None], dz[None, None, :])
    S = 0.0
    n = free.shape
    for ax in range(3):
        tang = [b for b in range(3) if b != ax]
        Ht2 = G[tang[0]]**2 + G[tang[1]]**2
        area = np.broadcast_to(widths[tang[0]]*widths[tang[1]], n)
        s0 = [slice(None)]*3; s0[ax] = slice(0, n[ax] - 1)
        s1 = [slice(None)]*3; s1[ax] = slice(1, n[ax])
        s0, s1 = tuple(s0), tuple(s1)
        a_free = free[s0] & ~free[s1]                                # free cell below a metal face
        b_free = ~free[s0] & free[s1]                                # free cell above a metal face
        S += (Ht2[s0]*area[s0])[a_free].sum() + (Ht2[s1]*area[s1])[b_free].sum()
    return RS*4*S/q.P


def cell(g, etched, a, **kw):
    """C', L'(0), L'(a), R'_surface, R'_wheeler and the slice profiles of one cell."""
    m0 = q.build(g, etched, lines=a, **kw)
    ma = q.build(g, etched, lines=a, rec=a, **kw)
    C, rc, cs = q.capacitance(m0)
    L0, r0, ls, info = q.inductance(m0, full=True)
    La, ra, _ = q.inductance(ma)
    Rs_ = surface_R(m0, info)
    Rw = RS*(La - L0)/(q.MU0*a)
    return dict(C=C, L=L0, La=La, R_surf=Rs_, R_wh=Rw, cells=int(m0['sig'].size),
                res=max(rc, r0, ra), cs=cs.tolist(), ls=ls.tolist())


def factors(u, e, R="R_wh"):
    """Tee cell e over no-slot cell u."""
    Lu, Le = u["L"] + u[R]/W, e["L"] + e[R]/W
    Fn = np.sqrt(Le*e["C"]/(Lu*u["C"]))
    FZ = np.sqrt((Le/e["C"])/(Lu/u["C"]))
    FR = e[R]/u[R]
    return dict(F_n=Fn, F_Z=FZ, F_R=FR, F_alpha=FR/FZ)
