"""2D quasi-TEM baseline for the thick-metal CPW cross-section.

PRODUCTION.  Promoted out of diagnostics/ after it reproduced the CST reference
to <=3 % on both observables where the 3D zero-thickness MoM was +10 to +30 %
high.  This is the absolute baseline of the extraction; the 3D periodic solver
supplies the FRACTIONAL tee perturbation on top of it.

Why it exists.  MTX (electrode thickness, 1-15 um against gaps of 4-20 um) is
the strongest single geometry predictor in the CST dataset -- t = -83 against
nm_baseline, spanning 2.7 standard deviations -- and a zero-thickness RWG sheet
has no representation for it at all.  Here it costs nothing: the electrodes are
just rectangles of cells.

    n_m = sqrt(C / C_air),        Z0 = 1 / (c sqrt(C C_air))

with C the cross-section capacitance per unit length for the real layer stack
and C_air the same geometry with every dielectric replaced by vacuum.

Validation (diagnostics/mtx_2d_run.py holds the record):
  * dn_m/dMTX  -0.02162 vs CST -0.02241  (ratio 0.96, 50-row regression)
  * dZ0/dMTX   -1.16667 vs CST -1.17387  (ratio 0.99)
  * absolute n_m within -0.8 to -2.9 % on the five test rows, Z0 within -3.2 %
  * setting MTX = 0 reproduces the zero-thickness pathology: n_m collapses to
    2.08-2.14 across five geometries and the per-row errors rank as the 3D
    MoM's do, which is what identified thickness as the cause
  * grid-converged to 0.016 % in n_m over a 4x refinement

It is quasi-TEM and gives no loss, so alpha still comes from the full-wave
solver.  It is a first-principles solve, not a fit: the dataset is never read.

Discretisation: cell-centred finite volume on a graded tensor grid.  eps is
constant per cell (layer interfaces are forced onto cell FACES), face
transmissibility uses the distance-weighted harmonic mean, so dielectric
interfaces are handled exactly.  Conductors are Dirichlet cell sets, the outer
boundary is Dirichlet 0 far away.  The discrete energy gives

    C = sum_faces T_f (phi_i - phi_j)^2     for V = 1,

which is exact for the discretised system (no post-hoc flux integration).
"""
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

C0 = 299792458.0
EPS0 = 8.8541878128e-12


def _seg(a, b, ha, hb, hmax, growth=0.25):
    """Graded node positions on [a, b], spacing ha at a and hb at b."""
    if b <= a:
        return np.array([a])
    xs = [a]
    while xs[-1] < b:
        x = xs[-1]
        s = min(hmax, ha + growth*(x - a), hb + growth*(b - x))
        xs.append(x + max(s, 1e-12))
    xs = np.array(xs)
    xs = a + (xs - a)*(b - a)/(xs[-1] - a)          # land exactly on b
    return xs


def _grid(breaks, hfine, hmax, growth=0.25):
    """Concatenate graded segments so every break lands exactly on a face."""
    out = [np.array([breaks[0]])]
    for a, b in zip(breaks[:-1], breaks[1:]):
        ha = hfine.get(a, hmax); hb = hfine.get(b, hmax)
        out.append(_seg(a, b, ha, hb, hmax, growth)[1:])
    return np.unique(np.concatenate(out))


def solve_cs(WS, GAP, WG, MTX, t_LN, BOX, SI, eps_LN, eps_SIO2, eps_SI,
             pad_x=600e-6, pad_up=400e-6, pad_dn=150e-6, hmin=None, hmax=12e-6):
    """Return (C, C_air) per unit length for the CPW cross-section.

    All lengths in metres.  MTX = 0 reproduces the zero-thickness limit."""
    x_si, x_gi, x_go = WS/2, WS/2 + GAP, WS/2 + GAP + WG
    if hmin is None:
        hmin = max(min(t_LN/4, GAP/40, max(MTX, 1e-7)/4), 8e-9)
    # ---- x grid: fine at every conductor edge --------------------------
    xb = sorted({-x_go - pad_x, -x_go, -x_gi, -x_si, 0.0, x_si, x_gi, x_go,
                 x_go + pad_x})
    hf = {v: hmin for v in (-x_go, -x_gi, -x_si, x_si, x_gi, x_go)}
    xf = _grid(xb, hf, hmax)
    # ---- z grid: layer interfaces are exact faces ----------------------
    zL, zB, zS = -t_LN, -t_LN - BOX, -t_LN - BOX - SI
    zb = sorted({zS - pad_dn, zS, zB, zL, 0.0, MTX, MTX + pad_up} - {None})
    hfz = {0.0: hmin, zL: min(hmin, t_LN/4), zB: hmin, float(MTX): hmin}
    zf = _grid(zb, hfz, hmax)

    xc = 0.5*(xf[1:] + xf[:-1]); dx = np.diff(xf)
    zc = 0.5*(zf[1:] + zf[:-1]); dz = np.diff(zf)
    nx, nz = len(xc), len(zc)

    # ---- per-cell permittivity ----------------------------------------
    er = np.ones((nz, nx))
    er[(zc > zL) & (zc < 0.0), :] = eps_LN
    er[(zc > zB) & (zc < zL), :] = eps_SIO2
    er[(zc > zS) & (zc < zB), :] = eps_SI

    # ---- conductors ----------------------------------------------------
    inmet = (zc[:, None] > 0.0) & (zc[:, None] < MTX) if MTX > 0 else np.zeros((nz, nx), bool)
    sig = inmet & (np.abs(xc)[None, :] < x_si)
    gnd = inmet & (np.abs(xc)[None, :] > x_gi) & (np.abs(xc)[None, :] < x_go)
    if MTX <= 0:      # zero-thickness limit: a single row of faces at z=0
        k0 = int(np.argmin(np.abs(zc)))
        sig = np.zeros((nz, nx), bool); gnd = np.zeros((nz, nx), bool)
        sig[k0, np.abs(xc) < x_si] = True
        gnd[k0, (np.abs(xc) > x_gi) & (np.abs(xc) < x_go)] = True

    def _cap(eps_cells):
        idx = -np.ones((nz, nx), int)
        free = ~(sig | gnd)
        idx[free] = np.arange(free.sum())
        N = int(free.sum())
        rows, cols, vals = [], [], []
        b = np.zeros(N)
        faces = []                      # (i0,j0,i1,j1,T)
        # horizontal faces
        Tx = (2*dz[:, None]*eps_cells[:, :-1]*eps_cells[:, 1:]
              / (eps_cells[:, :-1]*dx[None, 1:] + eps_cells[:, 1:]*dx[None, :-1]))
        Tz = (2*dx[None, :]*eps_cells[:-1, :]*eps_cells[1:, :]
              / (eps_cells[:-1, :]*dz[1:, None] + eps_cells[1:, :]*dz[:-1, None]))
        def add(ia, ja, ib, jb, T):
            faces.append((ia, ja, ib, jb, T))
        for (I, J, I2, J2, T) in (
                (np.repeat(np.arange(nz), nx-1), np.tile(np.arange(nx-1), nz),
                 np.repeat(np.arange(nz), nx-1), np.tile(np.arange(1, nx), nz), Tx.ravel()),
                (np.repeat(np.arange(nz-1), nx), np.tile(np.arange(nx), nz-1),
                 np.repeat(np.arange(1, nz), nx), np.tile(np.arange(nx), nz-1), Tz.ravel())):
            add(I, J, I2, J2, T)
        phiD = np.where(sig, 1.0, 0.0)
        for (I, J, I2, J2, T) in faces:
            a = idx[I, J]; c = idx[I2, J2]
            fa = a >= 0; fc = c >= 0
            m = fa & fc
            rows += [a[m], c[m], a[m], c[m]]
            cols += [a[m], c[m], c[m], a[m]]
            vals += [T[m], T[m], -T[m], -T[m]]
            m = fa & ~fc
            rows += [a[m]]; cols += [a[m]]; vals += [T[m]]
            np.add.at(b, a[m], T[m]*phiD[I2, J2][m])
            m = ~fa & fc
            rows += [c[m]]; cols += [c[m]]; vals += [T[m]]
            np.add.at(b, c[m], T[m]*phiD[I, J][m])
        A = sparse.coo_matrix((np.concatenate(vals),
                               (np.concatenate(rows), np.concatenate(cols))),
                              shape=(N, N)).tocsr()
        # outer boundary: Dirichlet 0 -> pin the frame cells
        frame = np.zeros((nz, nx), bool)
        frame[0, :] = frame[-1, :] = True; frame[:, 0] = frame[:, -1] = True
        fi = idx[frame & free]
        A = A.tolil()
        for i in fi:
            A.rows[i] = [i]; A.data[i] = [1.0]; b[i] = 0.0
        phi = np.zeros((nz, nx)); phi[sig] = 1.0
        phi[free] = spsolve(A.tocsr(), b)
        C = 0.0
        for (I, J, I2, J2, T) in faces:
            C += float(np.sum(T*(phi[I, J] - phi[I2, J2])**2))
        return C

    return _cap(EPS0*er), _cap(EPS0*np.ones_like(er)), (nx, nz)


def observables(C, Cair):
    return float(np.sqrt(C/Cair)), float(1.0/(C0*np.sqrt(C*Cair)))
