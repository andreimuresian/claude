"""EVALUATION ONLY -- not a production route, not committed to.

Question: can dC be obtained from the 2D cross-section solver by averaging over
the longitudinal profile of the tee, instead of differencing two full-wave 3D
solves (which is 50-116 % wrong and only 4-15 % of that is the near-field floor)?

The tee cuts the ground from its inner edge: a stem of depth W1 (in x) and
length L1 (in v), then a cap of depth W2 beyond it and length L2.  So along v the
cross-section takes exactly three forms, and with L2 > L1 (435/500 rows):

  A  full ground                                     fraction 1 - L2/P
  B  cap removed only -- an inner ground sliver
     [x_gi, x_gi+W1] survives, outer ground resumes
     at x_gi+W1+W2                                   fraction (L2 - L1)/P
  C  stem and cap removed -- ground starts at
     x_gi+W1+W2                                      fraction L1/P

  C_avg = f_A C_A + f_B C_B + f_C C_C ,   dC_lumped = (C_avg - C_unetched) P

KNOWN APPROXIMATION, stated up front: this is a quasi-static segment model.  It
assumes the longitudinal field rearrangement at the slot rims contributes
nothing, which is exactly the term a 2D average cannot see.  It should therefore
be read as a lower bound on |dC|, and its failure mode is under-prediction.

In case B the inner sliver is electrically floating in a 2D cross-section but is
connected to ground at both ends of the tee in 3D.  The tee is ~100 um against a
wavelength of ~5 mm in the stack, so the sliver is electrically short and is
treated as grounded.  Treating it as floating instead is the obvious sensitivity
to check if the model is ever taken further.
"""
import sys
import numpy as np
sys.path.insert(0, "/home/user/claude/notebooks/mom")
from scipy import sparse
from scipy.sparse.linalg import spsolve
import cpw_2d_static as cs

EPS0 = cs.EPS0
C0 = cs.C0


def solve_iv(WS, GAP, MTX, t_LN, BOX, SI, eps_LN, eps_SIO2, eps_SI,
             gnd_iv, pad_x=1200e-6, pad_up=800e-6, pad_dn=150e-6, hmax=6e-6):
    """Capacitance of a cross-section whose GROUND occupies the x-intervals in
    gnd_iv (mirrored to -x).  Signal is |x| < WS/2 as usual.  Same finite-volume
    scheme as cpw_2d_static; only the conductor mask differs."""
    x_si = WS/2
    edges = sorted({x_si} | {v for iv in gnd_iv for v in iv})
    hmin = max(min(t_LN/4, GAP/40, max(MTX, 1e-7)/4), 8e-9)
    xb = sorted({-edges[-1]-pad_x, 0.0, edges[-1]+pad_x}
                | {s*v for v in edges for s in (-1, 1)})
    hf = {s*v: hmin for v in edges for s in (-1, 1)}
    xf = cs._grid(xb, hf, hmax)
    zL, zB, zS = -t_LN, -t_LN-BOX, -t_LN-BOX-SI
    zb = sorted({zS-pad_dn, zS, zB, zL, 0.0, MTX, MTX+pad_up})
    hfz = {0.0: hmin, zL: min(hmin, t_LN/4), zB: hmin, float(MTX): hmin}
    zf = cs._grid(zb, hfz, hmax)
    xc = 0.5*(xf[1:]+xf[:-1]); dx = np.diff(xf)
    zc = 0.5*(zf[1:]+zf[:-1]); dz = np.diff(zf)
    nx, nz = len(xc), len(zc)
    er = np.ones((nz, nx))
    er[(zc > zL) & (zc < 0.0), :] = eps_LN
    er[(zc > zB) & (zc < zL), :] = eps_SIO2
    er[(zc > zS) & (zc < zB), :] = eps_SI
    inm = (zc[:, None] > 0.0) & (zc[:, None] < MTX)
    ax = np.abs(xc)[None, :]
    sig = inm & (ax < x_si)
    gnd = np.zeros((nz, nx), bool)
    for a, b in gnd_iv:
        gnd |= inm & (ax > a) & (ax < b)

    def cap(eps):
        idx = -np.ones((nz, nx), int); free = ~(sig | gnd)
        idx[free] = np.arange(free.sum()); N = int(free.sum())
        Tx = (2*dz[:, None]*eps[:, :-1]*eps[:, 1:]
              / (eps[:, :-1]*dx[None, 1:] + eps[:, 1:]*dx[None, :-1]))
        Tz = (2*dx[None, :]*eps[:-1, :]*eps[1:, :]
              / (eps[:-1, :]*dz[1:, None] + eps[1:, :]*dz[:-1, None]))
        faces = [(np.repeat(np.arange(nz), nx-1), np.tile(np.arange(nx-1), nz),
                  np.repeat(np.arange(nz), nx-1), np.tile(np.arange(1, nx), nz), Tx.ravel()),
                 (np.repeat(np.arange(nz-1), nx), np.tile(np.arange(nx), nz-1),
                  np.repeat(np.arange(1, nz), nx), np.tile(np.arange(nx), nz-1), Tz.ravel())]
        rows = []; cols = []; vals = []; b = np.zeros(N)
        phiD = np.where(sig, 1.0, 0.0)
        for (I, J, I2, J2, T) in faces:
            a_ = idx[I, J]; c_ = idx[I2, J2]
            fa = a_ >= 0; fc = c_ >= 0
            m = fa & fc
            rows += [a_[m], c_[m], a_[m], c_[m]]
            cols += [a_[m], c_[m], c_[m], a_[m]]
            vals += [T[m], T[m], -T[m], -T[m]]
            m = fa & ~fc
            rows += [a_[m]]; cols += [a_[m]]; vals += [T[m]]
            np.add.at(b, a_[m], T[m]*phiD[I2, J2][m])
            m = ~fa & fc
            rows += [c_[m]]; cols += [c_[m]]; vals += [T[m]]
            np.add.at(b, c_[m], T[m]*phiD[I, J][m])
        A = sparse.coo_matrix((np.concatenate(vals),
                               (np.concatenate(rows), np.concatenate(cols))),
                              shape=(N, N)).tolil()
        frame = np.zeros((nz, nx), bool)
        frame[0, :] = frame[-1, :] = True; frame[:, 0] = frame[:, -1] = True
        for k in idx[frame & free]:
            A.rows[k] = [k]; A.data[k] = [1.0]; b[k] = 0.0
        phi = np.zeros((nz, nx)); phi[sig] = 1.0
        phi[free] = spsolve(A.tocsr(), b)
        return float(sum(np.sum(T*(phi[I, J]-phi[I2, J2])**2)
                         for (I, J, I2, J2, T) in faces))

    return cap(EPS0*er), cap(EPS0*np.ones_like(er))


def profile(g):
    """The three cross-sections and their length fractions, from the geometry."""
    P = 2e-4
    x_gi = g["WS"]/2 + g["GAP"]; x_go = x_gi + g["WG"]
    b = min(x_gi + g["W1"], x_go)
    c = min(x_gi + g["W1"] + g["W2"], x_go)
    L1, L2 = g["L1"], g["L2"]
    lo, hi = min(L1, L2), max(L1, L2)
    full = [(x_gi, x_go)]
    both = [(c, x_go)] if c < x_go else []
    if L2 >= L1:                       # cap is the longer feature
        mid = ([(x_gi, b)] if b > x_gi else []) + ([(c, x_go)] if c < x_go else [])
    else:                              # stem longer: only the stem is cut here
        mid = [(b, x_go)] if b < x_go else []
    return [(1.0 - hi/P, full), ((hi - lo)/P, mid), (lo/P, both)]
