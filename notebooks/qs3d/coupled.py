"""Coupled (second-order quasi-static) correction to the lumped C of the cell.

Symmetric cell, ports on the cell edges.  With the even (open centre) and odd
(shorted centre) half-cell input impedances
    Z_e = 1/(jw C_h) + jw L_e + ...,     Z_o = jw L_h + ...,
the author's extractor gives exactly
    C_lump = Im(C_abcd)/w = Im(2/(Z_e - Z_o))/w = 2 C_h / (1 - w^2 C_h (L_e - L_h))
to this order.  C_h: half-cell capacitance (open centre), L_h: half-cell loop
inductance (shorted centre), L_e: the inductance seen by the CHARGING currents
of the open half cell = 2 W_m / I_port^2, where W_m is the magnetic energy of
the displacement currents jw D0 in the dielectric plus the conduction currents
that bring the charge to every metal surface (incl. the tee fingers).

The slice cascade (qs3d.cell_abcd_lumped) is the same formula with L_e replaced
by the 1D estimate  sum_k l_k (I_k/I_port)^2  (each slice's charge fed through
the slice loop inductance).  The coupled correction is
    dC = f(L_e 3D) - f(L_e slice),   f(L) = 2 C_h / (1 - w^2 C_h (L - L_h)),
added to the cascade C_lump.  For a uniform line both L_e equal L_h/3.

Magnetics here are node-based so that H lives on primal edges and its curl on
primal faces, where the electrostatic fluxes (cell-centred phi) live:
H = T - grad(Omega),  curl T = I_face (built by integrating along x from the
x = 0 mirror plane),  metal and the grounded box are holes (B.n = 0, natural),
Omega = 0 on x = 0 (and on z = 0 for the even problem: PMC walls).
"""
import numpy as np
from scipy import sparse

import qs3d as q

MU0 = q.MU0


def _metal(m):
    shape = m['sig'].shape
    frame = np.zeros(shape, bool)
    frame[-1, :, :] = True; frame[:, 0, :] = True; frame[:, -1, :] = True
    return m['sig'] | m['gnd'] | frame, frame


def charging_currents(m, phi, faces, float_frame=False):
    """Face currents (per unit jw) of the open half cell driven at V = 1:
    displacement flux in the dielectric, conduction completion in the metal
    (each metal column carries its accumulated charge along z to the port).
    float_frame: the frame is dielectric (no box charge)."""
    metal = m['sig'] | m['gnd'] if float_frame else _metal(m)[0]
    nx, ny, nz = metal.shape
    I = [np.zeros((nx + 1, ny, nz)), np.zeros((nx, ny + 1, nz)), np.zeros((nx, ny, nz + 1))]
    inner = [np.s_[1:-1, :, :], np.s_[:, 1:-1, :], np.s_[:, :, 1:-1]]
    for ax, (s0, s1, T) in enumerate(faces):
        F = T*(phi[s0] - phi[s1])
        both = metal[s0] & metal[s1]
        I[ax][inner[ax]] = np.where(both, 0.0, F)        # metal-metal: completion below
    # net inflow into each metal cell through faces shared with the dielectric
    net = np.zeros(metal.shape)
    for ax in range(3):
        Ia = I[ax]
        lo = np.take(Ia, range(0, Ia.shape[ax] - 1), axis=ax)   # face on the cell's -side
        hi = np.take(Ia, range(1, Ia.shape[ax]), axis=ax)       # face on the cell's +side
        net += lo - hi
    net = np.where(metal, net, 0.0)
    # column completion along z (all metal segments reach the port plane)
    Iz = I[2]
    carry = np.zeros((nx, ny))
    worst = 0.0
    for k in range(nz):
        mk = metal[:, :, k]
        below = metal[:, :, k - 1] if k > 0 else np.zeros_like(mk)
        carry = np.where(mk, np.where(below, carry, 0.0) + net[:, :, k], 0.0)
        # net already contains the (displacement) z-faces shared with air; the
        # metal-metal z-face above carries 'carry'
        if k + 1 < nz:
            mm = mk & metal[:, :, k + 1]
            Iz[:, :, k + 1] = np.where(mm, carry, Iz[:, :, k + 1])
            end = mk & ~metal[:, :, k + 1]
            if end.any():
                worst = max(worst, float(np.abs(carry[end]).max()))
        else:
            Iz[:, :, nz] = np.where(mk, carry, 0.0)
    return I, worst


def through_currents(m, I0=1.0):
    """Face currents of the shorted half cell: I0 along the signal, -I0 back on
    the ground columns that are continuous over the half period."""
    metal, _ = _metal(m)
    nx, ny, nz = metal.shape
    dx, dy, dz = m['d']
    area = dx[:, None]*dy[None, :]
    I = [np.zeros((nx + 1, ny, nz)), np.zeros((nx, ny + 1, nz)), np.zeros((nx, ny, nz + 1))]
    sig = m['sig'].all(axis=2); gfull = m['gnd'].all(axis=2)
    col = np.where(sig, I0*area/area[sig].sum(), 0.0) - np.where(gfull, I0*area/area[gfull].sum(), 0.0)
    I[2][:] = col[:, :, None]
    return I


def magnetics(m, I, pmc_z0):
    """Node-based magnetostatics for given divergence-free face currents I.
    Returns (E = sum_edges M h^2 = 2 W_quarter, per-slice energies, curl residual)."""
    metal, _ = _metal(m)
    nx, ny, nz = metal.shape
    dx, dy, dz = m['d']
    Ix, Iy, Iz = I
    # source field on edges (x-edges carry 0)
    ty = np.concatenate([np.zeros((1, ny, nz + 1)), np.cumsum(Iz, axis=0)], axis=0)     # (nx+1, ny, nz+1)
    tz = -np.concatenate([np.zeros((1, ny + 1, nz)), np.cumsum(Iy, axis=0)], axis=0)    # (nx+1, ny+1, nz)
    resid = (tz[:, 1:, :] - tz[:, :-1, :]) - (ty[:, :, 1:] - ty[:, :, :-1]) - Ix
    curl_res = float(np.abs(resid).max()/max(np.abs(Ix).max(), 1e-300))
    # dual areas of the edges from surrounding NON-metal cells
    nm = (~metal).astype(float)
    P3 = np.pad(nm, 1)                                                # (nx+2, ny+2, nz+2)
    # x-edges (i, jn, kn): cells (i, jn-1|jn, kn-1|kn)
    wx = np.zeros((nx, ny + 1, nz + 1))
    wy = np.zeros((nx + 1, ny, nz + 1))
    wz = np.zeros((nx + 1, ny + 1, nz))
    hy = np.pad(dy, 1); hz = np.pad(dz, 1); hx = np.pad(dx, 1)
    for dj in (0, 1):
        for dk in (0, 1):
            c = P3[1:-1, dj:dj + ny + 1, dk:dk + nz + 1]
            wx += c*(hy[dj:dj + ny + 1][None, :, None]/2)*(hz[dk:dk + nz + 1][None, None, :]/2)
    for di in (0, 1):
        for dk in (0, 1):
            c = P3[di:di + nx + 1, 1:-1, dk:dk + nz + 1]
            wy += c*(hx[di:di + nx + 1][:, None, None]/2)*(hz[dk:dk + nz + 1][None, None, :]/2)
    for di in (0, 1):
        for dj in (0, 1):
            c = P3[di:di + nx + 1, dj:dj + ny + 1, 1:-1]
            wz += c*(hx[di:di + nx + 1][:, None, None]/2)*(hy[dj:dj + ny + 1][None, :, None]/2)
    Mx = MU0*wx/dx[:, None, None]; My = MU0*wy/dy[None, :, None]; Mz = MU0*wz/dz[None, None, :]
    # node numbering; Dirichlet Omega = 0 on x = 0 (and z = 0 for PMC)
    shp = (nx + 1, ny + 1, nz + 1)
    active = np.zeros(shp, bool)
    active[:-1, :, :] |= Mx > 0; active[1:, :, :] |= Mx > 0
    active[:, :-1, :] |= My > 0; active[:, 1:, :] |= My > 0
    active[:, :, :-1] |= Mz > 0; active[:, :, 1:] |= Mz > 0
    dirich = np.zeros(shp, bool); dirich[0] = True
    if pmc_z0:
        dirich[:, :, 0] = True
    free = active & ~dirich
    idx = -np.ones(shp, np.int64); idx[free] = np.arange(free.sum())
    N = int(free.sum())
    rows, cols, vals = [], [], []; diag = np.zeros(N); b = np.zeros(N)
    edge_sets = ((Mx, np.zeros_like(Mx), np.s_[:-1, :, :], np.s_[1:, :, :]),
                 (My, ty, np.s_[:, :-1, :], np.s_[:, 1:, :]),
                 (Mz, tz, np.s_[:, :, :-1], np.s_[:, :, 1:]))
    for M, t, sa, sb in edge_sets:
        a, bb, Mv, tv = idx[sa].ravel(), idx[sb].ravel(), M.ravel(), t.ravel()
        on = Mv > 0
        a, bb, Mv, tv = a[on], bb[on], Mv[on], tv[on]
        fa, fb = a >= 0, bb >= 0
        m2 = fa & fb
        rows += [a[m2], bb[m2]]; cols += [bb[m2], a[m2]]; vals += [-Mv[m2], -Mv[m2]]
        np.add.at(diag, a[fa], Mv[fa]); np.add.at(diag, bb[fb], Mv[fb])
        np.add.at(b, bb[fb], Mv[fb]*tv[fb]); np.add.at(b, a[fa], -Mv[fa]*tv[fa])
    A = sparse.csr_matrix((np.concatenate(vals + [diag]),
                           (np.concatenate(rows + [np.arange(N)]), np.concatenate(cols + [np.arange(N)]))),
                          shape=(N, N))
    x, rr = q._solve(A, b)
    Om = np.zeros(shp); Om[free] = x
    hx_ = -(Om[1:, :, :] - Om[:-1, :, :])
    hy_ = ty - (Om[:, 1:, :] - Om[:, :-1, :])
    hz_ = tz - (Om[:, :, 1:] - Om[:, :, :-1])
    ex_, ey_, ez_ = Mx*hx_**2, My*hy_**2, Mz*hz_**2
    E = float(ex_.sum() + ey_.sum() + ez_.sum())
    # per-slice (z cells) energies: x/y edges at z-nodes shared half/half
    nodal = ex_.sum(axis=(0, 1)) + ey_.sum(axis=(0, 1))              # (nz+1,)
    sl = ez_.sum(axis=(0, 1)).copy()
    sl += nodal[:-1]/2 + nodal[1:]/2
    sl[0] += nodal[0]/2; sl[-1] += nodal[-1]/2
    return E, sl, curl_res, rr


def signal_charge_profile(m, I):
    """Charge per z-slice on the signal (quarter), from the charging currents."""
    Iz = I[2]
    sig = m['sig'].all(axis=2)
    port = Iz[:, :, 1:]; base = Iz[:, :, :-1]
    # column current difference = charge delivered to that slice of the column
    dq = (port - base)[sig].sum(axis=0)
    return dq


def coupled_lumped_C(m, f=60e9, float_frame=False):
    """C_lump from the coupled formula and from the 1D (slice) estimate of L_e,
    all quantities full-width half cell.  Returns a dict with diagnostics."""
    w = 2*np.pi*f
    Cp, rc, csl, phi, faces, _ = q.capacitance(m, full=True, float_frame=float_frame)
    Ie, worst = charging_currents(m, phi, faces, float_frame)
    Iq_e = float(Ie[2][:, :, -1][m['sig'][:, :, -1]].sum())       # signal port current (quarter)
    Ee, sle, cre, _ = magnetics(m, Ie, pmc_z0=True)
    It = through_currents(m)
    Eo, slo, cro, _ = magnetics(m, It, pmc_z0=False)
    L_e = Ee/(2*Iq_e**2)
    L_h = Eo/(2*1.0**2)
    C_h = Cp*q.P/2
    # 1D estimate of L_e from the same odd slices and the signal charge profile
    lk = slo/2.0                                                    # per-slice share of L_h
    dq = signal_charge_profile(m, Ie)
    Ik = np.cumsum(dq) - dq/2
    L_e_1d = float(np.sum(lk*(Ik/Iq_e)**2))
    fC = lambda Le: 2*C_h/(1 - w**2*C_h*(Le - L_h))
    return dict(C_h=C_h, L_h=L_h, L_e=L_e, L_e_1d=L_e_1d, dC=fC(L_e) - fC(L_e_1d),
                C_coupled=fC(L_e), C_1d=fC(L_e_1d), curl_res=(cre, cro), seg_end=worst,
                Iq_e=Iq_e, Qsig=float(dq.sum()), Cp=Cp)
