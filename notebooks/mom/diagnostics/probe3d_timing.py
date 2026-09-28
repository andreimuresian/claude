"""TIMING PROBE ONLY (not a solver): cost of one 3D electrostatic solve of a
tee-etched unit cell, to decide whether a quasi-static 3D perturbation route can
meet the budget of < 5 min per geometry on a 16 GB laptop.

Same FV scheme as cpw_2d_static (cell-centred, harmonic-mean faces, conductors
as Dirichlet cells), quarter cell (mirror in x and z -> Neumann), far field
coarsened beyond 150 um, AMG-preconditioned CG to rel. residual 1e-8.

Usage: python probe3d_timing.py {worst|typical} <hz_min_um> {1=etched|0=unetched} {rs|sa}

Measured 2026-09-28, 4-core container, 15 GB RAM (converged to 1e-8):
  case                 unknowns  solve   peak RAM   C [pF/m]   2D C [pF/m]
  worst   etched  rs   1.05 M     42 s    0.84 GB    231.79
  worst   etched  rs   1.64 M     73 s    1.27 GB    232.00    (hz_min 0.1 um)
  worst   unetched rs  1.00 M     36 s    0.81 GB    267.75      267.26 (+0.18 %)
  typical etched  rs   0.97 M     26 s    0.78 GB    149.46
  typical unetched rs  0.95 M     23 s    0.76 GB    152.74      152.54 (+0.13 %)
  worst   etched  sa   1.05 M    237 s    0.96 GB    231.79    smoothed aggregation:
                                                              688 CG iterations
Classical (Ruge-Stuben) AMG is required; smoothed aggregation stalls on the
25 nm x 6 um cell anisotropy (its first run hit maxiter=100 unconverged).
worst:   WS 80, GAP 4.1, MTX 15, ETCH 0.36 (t_LN 0.10), W1 60, W2 60, L1 60, L2 190 um
typical: WS 35, GAP 8,   MTX 5,  ETCH 0.25,             W1 20, W2 20, L1 20, L2 150 um
"""
import sys, time, resource
import numpy as np
from scipy import sparse
import pyamg
sys.path.insert(0, '/home/user/claude/notebooks/mom')
import cpw_2d_static as cs
import stack_params as sp

EPS0 = 8.8541878128e-12
P = 200e-6


def axis(breaks, fine, h_near, far_from, h_far, growth=0.25):
    """graded axis: spacing <= h_near within the near zone, <= h_far beyond."""
    out = [np.array([breaks[0]])]
    for a, b in zip(breaks[:-1], breaks[1:]):
        near = (a < far_from[1]) and (b > far_from[0])
        hm = h_near if near else h_far
        out.append(cs._seg(a, b, fine.get(a, hm), fine.get(b, hm), hm, growth)[1:])
    return np.unique(np.concatenate(out))


def run(WS, GAP, MTX, ED, W1, W2, L1, L2, hz_min, etched=True, far=150e-6):
    WG = 70e-6
    t_LN = sp.TFLN - ED
    x_si, x_gi, x_go = WS/2, WS/2 + GAP, WS/2 + GAP + WG
    xb1, xb2 = min(x_gi + W1, x_go), min(x_gi + W1 + W2, x_go)
    hmin = max(min(t_LN/4, GAP/40, MTX/4), 8e-9)
    # x: 0 (symmetry) .. far pad; near zone = within `far` of the metal
    xb = sorted({0.0, x_si, x_gi, xb1, xb2, x_go, x_go + far, x_go + 1200e-6})
    xf = axis(xb, {v: hmin for v in (x_si, x_gi, xb1, xb2, x_go)}, 6e-6, (0, x_go + far), 200e-6)
    # vertical (called y here), same breaks as the 2D solver
    zL, zB, zS = -t_LN, -t_LN - sp.BOX_H, -t_LN - sp.BOX_H - sp.SI_H
    yb = sorted({zS - 150e-6, zS, zB - far, zB, zL, 0.0, MTX, MTX + far, MTX + 800e-6})
    yf = axis(yb, {0.0: hmin, zL: min(hmin, t_LN/4), zB: hmin, MTX: hmin},
              6e-6, (zB - far, MTX + far), 200e-6)
    # z: tee centre (symmetry) .. half period
    zb = sorted({0.0, L1/2, L2/2, P/2})
    zf = cs._grid(zb, {L1/2: hz_min, L2/2: hz_min}, 6e-6)

    xc, yc, zc = [0.5*(a[1:] + a[:-1]) for a in (xf, yf, zf)]
    dx, dy, dz = [np.diff(a) for a in (xf, yf, zf)]
    nx, ny, nz = len(xc), len(yc), len(zc)
    er = np.ones(ny)
    er[(yc > zL) & (yc < 0)] = sp.EPS_LN
    er[(yc > zB) & (yc < zL)] = sp.EPS_SIO2
    er[(yc > zS) & (yc < zB)] = sp.EPS_SI
    E = np.broadcast_to(er[None, :, None], (nx, ny, nz))          # [x, y, z]

    X, Y, Z = np.meshgrid(xc, yc, zc, indexing='ij')
    inmet = (Y > 0) & (Y < MTX)
    sig = inmet & (X < x_si)
    gnd = inmet & (X > x_gi) & (X < x_go)
    if etched:
        slot = ((X >= x_gi) & (X < xb1) & (Z < L1/2)) | ((X >= xb1) & (X < xb2) & (Z < L2/2))
        gnd &= ~slot
    fixed = sig | gnd
    frame = np.zeros_like(fixed)
    frame[-1] = True; frame[:, 0] = True; frame[:, -1] = True     # x=0, z=0, z=P/2: Neumann
    free = ~fixed & ~frame
    N = int(free.sum())
    idx = -np.ones(fixed.shape, np.int64); idx[free] = np.arange(N)
    phiD = sig.astype(float)

    t0 = time.time()
    rows, cols, vals = [], [], []
    diag = np.zeros(N); b = np.zeros(N)
    faces = []
    for ax, d in ((0, dx), (1, dy), (2, dz)):
        sl0 = [slice(None)]*3; sl1 = [slice(None)]*3
        sl0[ax] = slice(0, -1); sl1[ax] = slice(1, None)
        sl0, sl1 = tuple(sl0), tuple(sl1)
        area = [dy[None, :, None]*dz[None, None, :], dx[:, None, None]*dz[None, None, :],
                dx[:, None, None]*dy[None, :, None]][ax]
        dd = [d[:, None, None], d[None, :, None], d[None, None, :]][ax]
        e0, e1 = E[sl0], E[sl1]
        T = EPS0*2*area*e0*e1/(e0*dd[1:] if False else (e0*np.take(dd, range(1, dd.shape[ax]), axis=ax)
                                                         + e1*np.take(dd, range(0, dd.shape[ax]-1), axis=ax)))
        i0, i1 = idx[sl0].ravel(), idx[sl1].ravel(); T = np.broadcast_to(T, e0.shape).ravel()
        f0, f1 = i0 >= 0, i1 >= 0
        m = f0 & f1
        rows += [i0[m], i1[m]]; cols += [i1[m], i0[m]]; vals += [-T[m], -T[m]]
        np.add.at(diag, i0[m], T[m]); np.add.at(diag, i1[m], T[m])
        m = f0 & ~f1                       # neighbour fixed (Dirichlet: metal or frame=0)
        fx1 = (fixed[sl1].ravel() | frame[sl1].ravel())
        m &= fx1
        np.add.at(diag, i0[m], T[m]); np.add.at(b, i0[m], T[m]*phiD[sl1].ravel()[m])
        m = ~f0 & f1
        fx0 = (fixed[sl0].ravel() | frame[sl0].ravel()) & m
        np.add.at(diag, i1[fx0], T[fx0]); np.add.at(b, i1[fx0], T[fx0]*phiD[sl0].ravel()[fx0])
        faces.append((sl0, sl1, T))
    A = sparse.csr_matrix((np.concatenate(vals + [diag]),
                           (np.concatenate(rows + [np.arange(N)]), np.concatenate(cols + [np.arange(N)]))),
                          shape=(N, N))
    t_asm = time.time() - t0
    t0 = time.time()
    kind = sys.argv[4] if len(sys.argv) > 4 else 'sa'
    if kind == 'rs':
        ml = pyamg.ruge_stuben_solver(A, max_coarse=500)
    else:
        ml = pyamg.smoothed_aggregation_solver(A, symmetry='symmetric', max_coarse=500)
    t_setup = time.time() - t0
    t0 = time.time()
    res = []
    x = ml.solve(b, tol=1e-8, accel='cg', residuals=res, maxiter=3000)
    t_solve = time.time() - t0
    phi = phiD.copy(); phi[free] = x
    C = 0.0
    for sl0, sl1, T in faces:
        C += float(np.sum(T*(phi[sl0].ravel() - phi[sl1].ravel())**2))
    C_per_m = 4*C/P             # quarter cell -> full cell, per metre
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1e6
    print(f"grid {nx}x{ny}x{nz} = {nx*ny*nz/1e6:.2f} M cells, {N/1e6:.2f} M unknowns | "
          f"assemble {t_asm:.1f}s  AMG setup {t_setup:.1f}s  CG solve {t_solve:.1f}s ({len(res)} it, rel.res {res[-1]/res[0]:.1e}) | "
          f"peak RAM {rss:.2f} GB | C = {C_per_m*1e12:.2f} pF/m", flush=True)
    return C_per_m


if __name__ == '__main__':
    geo = sys.argv[1]; hz = float(sys.argv[2])*1e-6; etched = sys.argv[3] == '1'
    G = {'worst': dict(WS=80e-6, GAP=4.1e-6, MTX=15e-6, ED=0.36e-6, W1=60e-6, W2=60e-6, L1=60e-6, L2=190e-6),
         'typical': dict(WS=35e-6, GAP=8e-6, MTX=5e-6, ED=0.25e-6, W1=20e-6, W2=20e-6, L1=20e-6, L2=150e-6)}[geo]
    t = time.time()
    run(**G, hz_min=hz, etched=etched)
    print(f"  total wall {time.time()-t:.1f} s")
