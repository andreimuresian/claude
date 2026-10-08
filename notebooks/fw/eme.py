"""Full-wave periodic tee cell by eigenmode expansion (mode matching).

Along z the 200 um cell is piecewise uniform: plain line, head slot only, stem + head
slot.  Each uniform section is solved by the 2D full-wave mode solver (fw2d, open
boundaries with PML), on ONE common cross-section grid.  The cell field is expanded in
each section's modes (guided, leaky and PML/radiation modes); tangential E and H are
matched at every slot edge; the sections are cascaded as scattering matrices (stable
with evanescent modes); the Bloch modes are the eigenvectors of the cell's S-matrix
with E(z + P) = lambda E(z), lambda = exp(-gamma P).

Overlaps are unconjugated, <E_i, H_j> = int (E_i x H_j) . z dA over the stretched
(complex) area, for which the modes of one section are bi-orthogonal.  Each mode is
normalised to <E_i, H_i> = 1; branch: Im beta < 0 (decaying in +z).
Interface a -> b (a: incident in a, b: reflected in a, c: transmitted in b, d: incident
from b), with O = <E_a,i, H_b,j>:
    c + d = O^T (a + b),     a - b = O (c - d).
"""
import numpy as np
from scipy.linalg import eig, solve

import fw2d

P = 200e-6


class Section:
    def __init__(self, g, f, metal, extra_x, nmodes, n_shift=3.6, **kw):
        m = fw2d.Mode2D(g, f, metal_x=metal, extra_x=extra_x, **kw)
        self.m = m
        k0 = m.w/fw2d.C0
        from scipy.sparse.linalg import eigs
        vals, vecs = eigs(m.M, k=nmodes, sigma=(n_shift*k0)**2, which="LM", ncv=min(m.N - 2, 2*nmodes + 20))
        beta = np.sqrt(vals.astype(complex))
        beta = np.where(beta.imag > 0, -beta, beta)                  # decaying in +z
        beta = np.where((np.abs(beta.imag) < 1e-12*np.abs(beta)) & (beta.real < 0), -beta, beta)
        dx, dy, dxd, dyd = m.stretched
        self.Ax = dx[:, None]*dyd[None, :]                           # Ex / Hy points
        self.Ay = dxd[:, None]*dy[None, :]                           # Ey / Hx points
        E, H = [], []
        for b, v in zip(beta, vecs.T):
            Ex, Ey, Hx, Hy = m.fields(b, v)
            E.append((Ex, Ey)); H.append((Hx, Hy))
        self.beta, self.E, self.H = beta, E, H
        # normalise <E_i, H_i> = 1 and check bi-orthogonality
        O = self.overlap(self, raw=True)
        nrm = np.sqrt(np.diag(O))
        for i in range(len(beta)):
            self.E[i] = tuple(c/nrm[i] for c in self.E[i]); self.H[i] = tuple(c/nrm[i] for c in self.H[i])
        O = self.overlap(self)
        self.biortho = np.abs(O - np.eye(len(beta))).max()
        # gap voltage and signal current of each mode (for the Bloch impedance)
        self.V, self.I = [], []
        for b, v in zip(beta, vecs.T):
            r = m.line_params(b, v)
            self.V.append(r["V"]); self.I.append(r["I"])
        self.V = np.array(self.V)/nrm; self.I = np.array(self.I)/nrm
        self.k0 = k0

    def overlap(self, other, raw=False):
        """O[i, j] = <E_self,i, H_other,j>."""
        Ex = np.array([e[0].ravel() for e in self.E]); Ey = np.array([e[1].ravel() for e in self.E])
        Hx = np.array([h[0].ravel() for h in other.H]); Hy = np.array([h[1].ravel() for h in other.H])
        return (Ex*self.Ax.ravel()) @ Hy.T - (Ey*self.Ay.ravel()) @ Hx.T


def interface(a, b):
    """S-matrix of the junction a -> b: [b_out; c_out] = S [a_in; d_in]."""
    O = a.overlap(b)                                                  # (Ma, Mb)
    G = O.T @ O
    Ib = np.eye(G.shape[0]); Ia = np.eye(O.shape[0])
    S21 = solve(Ib + G, 2*O.T)
    S22 = solve(Ib + G, G - Ib)
    S11 = Ia - O @ S21
    S12 = O - O @ S22
    return [[S11, S12], [S21, S22]]


def prop(sec, L):
    p = np.diag(np.exp(-1j*sec.beta*L))
    Z = np.zeros_like(p)
    return [[Z, p], [p, Z]]


def star(A, B):
    """Redheffer star product: A then B (A's port 2 joined to B's port 1)."""
    (A11, A12), (A21, A22) = A
    (B11, B12), (B21, B22) = B
    I = np.eye(A22.shape[0])
    X = solve(I - B11 @ A22, B11)                                     # (I - B11 A22)^-1 B11
    Y = solve(I - A22 @ B11, A22)
    return [[A11 + A12 @ X @ A21, A12 @ solve(I - B11 @ A22, B12)],
            [B21 @ solve(I - A22 @ B11, A21), B22 + B21 @ Y @ B12]]


def bloch(S):
    """Bloch modes of a cell S-matrix (same section at both ends).
    Returns lambda = exp(-gamma P) and the amplitudes (a, b) at z = 0."""
    (R, Tp), (T, Rp) = S
    M = R.shape[0]
    I, Z = np.eye(M), np.zeros((M, M))
    A = np.block([[R, -I], [T, Z]])
    B = np.block([[Z, -Tp], [I, -Rp]])
    lam, X = eig(A, B)
    return lam, X[:M], X[M:]


def tee_cell(g, f, nmodes=80, **kw):
    """Sections and the cell S-matrix for the tee cell (tee centred at z = P/2)."""
    WS, GAP = g["WS"], g["GAP"]
    x_si, x_gi, x_go = WS/2, WS/2 + GAP, WS/2 + GAP + 70e-6
    xb1, xb2 = x_gi + g["W1"], x_gi + g["W1"] + g["W2"]
    extra = [xb1, xb2]
    plain = [(0, x_si), (x_gi, x_go)]
    head = [(0, x_si), (x_gi, xb1), (xb2, x_go)]                      # pad + outer strip
    stem = [(0, x_si), (xb1, x_go)] if g["W2"] == 0 else None
    both = [(0, x_si), (xb2, x_go)]                                   # outer strip only
    L1, L2 = g["L1"], g["L2"]
    # z layout from the cell boundary to the tee centre (mirrored after)
    if L2 >= L1:
        seq = [("A", P/2 - L2/2), ("H", (L2 - L1)/2), ("C", L1/2)]
        lay = {"A": plain, "H": head, "C": both}
    else:                                                              # stem longer than head
        stem_only = [(0, x_si), (x_gi + g["W1"], x_go)]  # placeholder, not needed for row 49
        raise NotImplementedError("L1 > L2")
    secs = {k: Section(g, f, lay[k], extra, nmodes, **kw) for k in lay}
    S = None
    order = seq + [(k, L) for k, L in seq[::-1]]
    prev = None
    for k, L in order:
        if prev is not None and prev != k:
            Sj = interface(secs[prev], secs[k])
            S = Sj if S is None else star(S, Sj)
        Sp = prop(secs[k], L)
        S = Sp if S is None else star(S, Sp)
        prev = k
    return secs, S
