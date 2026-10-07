"""Quasi-static 3D unit cell: per-length C and L of the tee-loaded CPW.

Geometry and materials follow the CST Multilayer model (validated with the
author, notebooks/validation/GEOMETRY_SPEC.md): thick metal (MTX), LN slab of
TFLN - ETCH_DEPTH with (lateral 28, vertical 43, along-line 43), SiO2 3.9,
Si 11.7, T-slots through both 70 um grounds, centred in the 200 um cell.

Quarter cell: x >= 0 (mirror plane through the signal) and z in [0, P/2]
(mirror plane through the tee centre, cell boundary at P/2).  Cell-centred
finite volume on a graded tensor grid, classical AMG + CG.

Electrostatic (C):  phi = 1 on the signal, 0 on grounds and far frame;
                    Neumann on x = 0 and on both z planes.
Magnetostatic (L):  high-frequency limit (skin depth 0.3 um << MTX): PEC
                    conductors, H = -grad(psi), dpsi/dn = 0 on metal, psi = 0
                    on x = 0 (H tangential vanishes there by symmetry),
                    Neumann on the far frame (the dual of the grounded box)
                    and on both z planes.  psi jumps by I/2 across a cut in
                    the gap (signal -> nearest ground metal, at mid-thickness).
The lumped quantities of the author's extractor are then
    L_lump = L' P sin(th)/th,  C_lump = C' P sin(th)/th,  th = w P sqrt(L'C').
"""
import os
import sys

import numpy as np
import pyamg
from scipy import sparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'mom'))
import cpw_2d_static as cs          # graded-axis helper only
import stack_params as sp

EPS0, MU0, C0 = 8.8541878128e-12, 4e-7*np.pi, 299792458.0
P = 200e-6
EPS_LN = (28.0, 43.0, 43.0)          # (lateral x, vertical y, along-line z)


def _axis(breaks, fine, h_near, near, h_far, growth=0.25):
    out = [np.array([breaks[0]])]
    for a, b in zip(breaks[:-1], breaks[1:]):
        hm = h_near if (a < near[1] and b > near[0]) else h_far
        out.append(cs._seg(a, b, fine.get(a, hm), fine.get(b, hm), hm, growth)[1:])
    return np.unique(np.concatenate(out))


def build(g, etched=True, hz_min=0.5e-6, far=150e-6, h_near=6e-6, no_slot=False,
          rec=0.0, lines=0.0, hmin_scale=1.0):
    """Grid, materials and conductor masks.  g: dict in metres
    (WS, GAP, MTX, t_LN, W1, W2, L1, L2).  Unetched -> one z cell (exact:
    the solution is z-invariant).
    lines > 0 adds grid lines at distance `lines` inside every metal face (and
    outside every slot face), so a cell with every metal face receded by
    rec = lines (Wheeler's rule, loss.py) shares the grid of rec = 0."""
    WS, GAP, MTX, tLN = g['WS'], g['GAP'], g['MTX'], g['t_LN']
    WG = 70e-6
    x_si, x_gi, x_go = WS/2, WS/2 + GAP, WS/2 + GAP + WG
    xb1, xb2 = min(x_gi + g['W1'], x_go), min(x_gi + g['W1'] + g['W2'], x_go)
    hmin = max(min(tLN/4, GAP/40, MTX/4), 8e-9)*hmin_scale
    a = lines
    # tee lines are always present, so etched and unetched share the x-y grid
    xl = {x_si, x_gi, x_go, xb1, xb2}
    if a > 0:
        xl |= {x_si - a, x_gi + a, x_go - a, xb1 - a, xb1 + a, xb2 + a}
    xb = sorted({0.0, x_go + far, x_go + 1200e-6} | xl)
    fine = {v: hmin for v in xl}
    xf = _axis(xb, fine, h_near, (0, x_go + far), 200e-6)
    zL, zB, zS = -tLN, -tLN - sp.BOX_H, -tLN - sp.BOX_H - sp.SI_H
    yl = {0.0, MTX} | ({a, MTX - a} if a > 0 else set())
    yb = sorted({zS - 150e-6, zS, zB - far, zB, zL, MTX + far, MTX + 800e-6} | yl)
    yfine = {v: hmin for v in yl}
    yfine.update({zL: min(hmin, tLN/4), zB: hmin})
    yf = _axis(yb, yfine, h_near, (zB - far, MTX + far), 200e-6)
    if etched:
        zl = {g['L1']/2, g['L2']/2} | ({g['L1']/2 + a, g['L2']/2 + a} if a > 0 else set())
        zl = {v for v in zl if 0 < v < P/2}
        zb = sorted({0.0, P/2} | zl)
        zf = cs._grid(zb, {v: hz_min for v in zl}, h_near)
    else:
        zf = np.array([0.0, P/2])
    xc, yc, zc = [0.5*(a[1:] + a[:-1]) for a in (xf, yf, zf)]
    dx, dy, dz = [np.diff(a) for a in (xf, yf, zf)]
    X, Y, Z = np.meshgrid(xc, yc, zc, indexing='ij')
    ex = np.ones(X.shape); ey = np.ones(X.shape); ez = np.ones(X.shape)
    ln = (Y > zL) & (Y < 0)
    ex[ln], ey[ln], ez[ln] = EPS_LN
    for sel, e in (((Y > zB) & (Y < zL), sp.EPS_SIO2), ((Y > zS) & (Y < zB), sp.EPS_SI)):
        ex[sel] = ey[sel] = ez[sel] = e
    r = rec                                   # every metal face receded by r
    inmet = (Y > r) & (Y < MTX - r)
    sig = inmet & (X < x_si - r)
    gnd = inmet & (X > x_gi + r) & (X < x_go - r)
    if etched and not no_slot:
        slot = (((X >= x_gi) & (X < xb1 + r) & (Z < g['L1']/2 + r))
                | ((X >= xb1 - r) & (X < xb2 + r) & (Z < g['L2']/2 + r)))
        gnd &= ~slot
    return dict(d=(dx, dy, dz), c=(xc, yc, zc), eps=(ex, ey, ez), sig=sig, gnd=gnd,
                MTX=MTX, x_si=x_si, x_gi=x_gi, y_lo=r, y_hi=MTX - r, x_cut=x_go - r)


def _faces(d, kx, ky, kz):
    """Harmonic-mean transmissibilities along each axis for per-cell k."""
    dx, dy, dz = d
    out = []
    for ax, k in ((0, kx), (1, ky), (2, kz)):
        h = [dx[:, None, None], dy[None, :, None], dz[None, None, :]][ax]
        area = [dy[None, :, None]*dz[None, None, :], dx[:, None, None]*dz[None, None, :],
                dx[:, None, None]*dy[None, :, None]][ax]
        n = k.shape[ax]
        k0, k1 = np.take(k, range(n - 1), axis=ax), np.take(k, range(1, n), axis=ax)
        h0, h1 = np.take(h, range(n - 1), axis=ax), np.take(h, range(1, n), axis=ax)
        with np.errstate(invalid='ignore', divide='ignore'):
            T = np.broadcast_to(2*area*k0*k1/(k0*h1 + k1*h0), k0.shape)
        s0 = [slice(None)]*3; s1 = [slice(None)]*3
        s0[ax] = slice(0, n - 1); s1[ax] = slice(1, n)
        out.append((tuple(s0), tuple(s1), T))
    return out


def _solve(A, b):
    ml = pyamg.ruge_stuben_solver(A.tocsr(), max_coarse=500)
    res = []
    x = ml.solve(b, tol=1e-9, accel='cg', maxiter=3000, residuals=res)
    return x, res[-1]/res[0]


def _assemble(shape, faces, free, fixed_val, jump=None, extra_diag=None):
    """SPD system for sum_f T (u_i - u_j - j_f)^2 with fixed cells."""
    idx = -np.ones(shape, np.int64); idx[free] = np.arange(free.sum())
    N = int(free.sum()); rows, cols, vals = [], [], []
    diag = np.zeros(N); b = np.zeros(N)
    for fi, (s0, s1, T) in enumerate(faces):
        i0, i1, T = idx[s0].ravel(), idx[s1].ravel(), T.ravel()
        J = jump[fi].ravel() if jump is not None else None
        m = (i0 >= 0) & (i1 >= 0)
        rows += [i0[m], i1[m]]; cols += [i1[m], i0[m]]; vals += [-T[m], -T[m]]
        np.add.at(diag, i0[m], T[m]); np.add.at(diag, i1[m], T[m])
        if J is not None:
            np.add.at(b, i0[m], -T[m]*J[m]); np.add.at(b, i1[m], T[m]*J[m])
        if fixed_val is not None:
            fv0, fv1 = fixed_val[s0].ravel(), fixed_val[s1].ravel()
            m = (i0 >= 0) & (i1 < 0) & np.isfinite(fv1)
            np.add.at(diag, i0[m], T[m]); np.add.at(b, i0[m], T[m]*fv1[m])
            m = (i0 < 0) & (i1 >= 0) & np.isfinite(fv0)
            np.add.at(diag, i1[m], T[m]); np.add.at(b, i1[m], T[m]*fv0[m])
    if extra_diag is not None:
        diag += extra_diag[free]
    A = sparse.csr_matrix((np.concatenate(vals + [diag]),
                           (np.concatenate(rows + [np.arange(N)]),
                            np.concatenate(cols + [np.arange(N)]))), shape=(N, N))
    return A, b, idx


def capacitance(m, vacuum=False, full=False, float_frame=False):
    """Per-length C' [F/m] (full cell, both halves).  float_frame=True: the far
    frame is dielectric with a Neumann outer face (zero net charge on signal +
    grounds, the open-boundary condition of a periodic line) instead of a
    grounded box."""
    ex, ey, ez = (np.ones_like(m['eps'][0]),)*3 if vacuum else m['eps']
    faces = _faces(m['d'], EPS0*ex, EPS0*ey, EPS0*ez)
    shape = ex.shape
    frame = np.zeros(shape, bool)
    if not float_frame:
        frame[-1, :, :] = True; frame[:, 0, :] = True; frame[:, -1, :] = True
    fixed = m['sig'] | m['gnd'] | frame
    val = np.full(shape, np.nan); val[fixed] = 0.0; val[m['sig']] = 1.0
    A, b, idx = _assemble(shape, faces, ~fixed, val)
    x, rr = _solve(A, b)
    phi = np.where(np.isfinite(val), val, 0.0); phi[~fixed] = x
    sl = _slices([T*(phi[s0] - phi[s1])**2 for s0, s1, T in faces], ex.shape[2])
    if full:
        return 4*sl.sum()/P, rr, 2*sl, phi, faces, fixed
    return 4*sl.sum()/P, rr, 2*sl                      # 2*sl: full-width slice C [F]


def inductance(m, sign=1.0, full=False):
    """Per-length L' [H/m] in the high-frequency (PEC) limit, full cell.

    Multivalued psi is handled so that no cut ends in open space:
      * psi = +I/4 on x = 0 above the signal and -I/4 below it (the half-
        domain path through the gap encloses I/2);
      * a cut with jump I/2 from the ground's OUTER edge to the far frame at
        mid-thickness (slots never reach the outer edge: W1 + W2 <= 65 < 70
        um), so loops around the ground carry -I/2 and loops around both
        conductors carry 0.
    The previous gap cut ended in open air inside the tee head whenever
    L2 > L1, which injected a spurious line current."""
    dx, dy, dz = m['d']; xc, yc, zc = m['c']
    shape = m['sig'].shape
    metal = m['sig'] | m['gnd']
    k = np.where(metal, 0.0, MU0)                    # no flux into metal
    faces = [(s0, s1, np.nan_to_num(T)) for s0, s1, T in _faces(m['d'], k, k, k)]
    jc = int(np.argmin(np.abs(yc - m['MTX']/2)))
    jumps = [np.zeros(f[2].shape) for f in faces]
    x_go = m.get('x_cut', m['x_si'] + (m['x_gi'] - m['x_si']) + 70e-6)   # ground outer edge
    jumps[1][xc > x_go, jc, :] = sign*0.5
    free = ~metal
    ed = np.zeros(shape); dv = np.zeros(shape)
    ed[0, :, :] = MU0*dy[:, None]*dz[None, :]/(dx[0]/2)
    ylo, yhi = m.get('y_lo', 0.0), m.get('y_hi', m['MTX'])             # signal extent in y
    dv[0, :, :] = np.where(yc > yhi, 0.25, np.where(yc < ylo, -0.25, 0.0))[:, None]
    A, b, idx = _assemble(shape, faces, free, None, jump=jumps, extra_diag=ed)
    b += (ed*dv)[free]
    x, rr = _solve(A, b)
    psi = np.zeros(shape); psi[free] = x
    e = [T*(psi[s1] - psi[s0] - jp)**2 for (s0, s1, T), jp in zip(faces, jumps)]
    sl = _slices(e, shape[2])
    sl += np.sum(np.where(free[0], ed[0]*(psi[0] - dv[0])**2, 0.0), axis=0)
    if full:
        return 4*sl.sum()/P, rr, 2*sl, dict(psi=psi, faces=faces, jumps=jumps, dv=dv, free=free)
    return 4*sl.sum()/P, rr, 2*sl                      # 2*sl: full-width slice L [H]


def _slices(face_energy, nz):
    """Sum face energies per z cell (z-faces shared half/half)."""
    ex_, ey_, ez_ = face_energy
    sl = ex_.sum(axis=(0, 1)) + ey_.sum(axis=(0, 1))
    zf = ez_.sum(axis=(0, 1))
    if nz > 1:
        sl[:-1] += zf/2; sl[1:] += zf/2
    return sl


def cell_abcd_lumped(Ls, Cs, f=60e9):
    """The author's extractor applied to the cell built from its own L and C
    distribution: slices from the tee centre to the cell edge (Ls, Cs in H,
    F), mirrored to span edge -> centre -> edge, each a short line section,
    cascaded; returns (Im B / w, Im C / w) as in extract_RLC."""
    w = 2*np.pi*f
    Ls = np.concatenate([Ls[::-1], Ls]); Cs = np.concatenate([Cs[::-1], Cs])
    M = np.eye(2, dtype=complex)
    for Lk, Ck in zip(Ls, Cs):
        th, Z = w*np.sqrt(Lk*Ck), np.sqrt(Lk/Ck)
        M = M @ np.array([[np.cos(th), 1j*Z*np.sin(th)], [1j*np.sin(th)/Z, np.cos(th)]])
    return M[0, 1].imag/w, M[1, 0].imag/w


def lumped(Lp, Cp, f=60e9):
    """The author's extractor applied to a Bloch-uniform cell of length P."""
    th = 2*np.pi*f*P*np.sqrt(Lp*Cp)
    s = np.sin(th)/th
    return Lp*P*s, Cp*P*s, th
