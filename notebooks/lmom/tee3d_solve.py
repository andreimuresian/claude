"""Bloch mode, n, alpha and Z0 of the periodic cell (tee3d.Cell + tee3d_kern).

Z(beta) is built at two nearby beta and taken linear in between (its beta dependence is smooth:
Bloch phases and Floquet wavenumbers).  The mode is the eigenvalue of the pencil
Z1 + lam (Z2 - Z1) closest to the guess (shift-invert Arnoldi: one LU).  Rebuilt once around the
root.  Z0 = N / I(0)^2 with N from reciprocity (fw.impedance), the partner mode being the mirror
image about z = 0 (the cell is symmetric about its centre): J_b = exp(j beta P) Mz J.
"""
import time
import numpy as np
from scipy import linalg
from scipy.sparse.linalg import eigs, LinearOperator

import stack as S
import fw
import tee3d as T
import tee3d_kern as K


class Stack:
    """The bits of fw.Line2D the kernels use."""

    def __init__(self, f, layers, bottom, eps_eff):
        self.f, self.w = f, 2*np.pi*f
        self.k0 = self.w/fw.C0
        self.layers, self.bottom = layers, bottom
        self.eps_bot = complex(bottom[0])
        self.K = (1 - eps_eff)/(1 + eps_eff)


class Solver:
    def __init__(self, cell, line, Mc=8, Ks=3e6, verbose=True, cache=None, workers=4):
        """cache: path prefix naming this cell, mesh and frequency; every Z(beta) is stored as
        <cache>_n<beta/k0>.npy and reloaded instead of rebuilt (runs survive a restart)."""
        self.cell, self.line, self.Mc, self.Ks, self.v = cell, line, Mc, Ks, verbose
        self.cache = cache
        self.workers, self.sc = workers, None   # processes; StaticCache (built on the first Z)
        self.F = K.Faces(cell)
        self.maps = K.basis_maps(cell, self.F)
        self.xs = K.XS(cell)
        self.pm = K.piece_maps(cell)
        self._probe()
        self._mirror()

    def log(self, *a):
        if self.v:
            print(*a, flush=True)

    def Z(self, beta):
        if self.cache:
            beta = complex(beta)
            fn = f"{self.cache}_n{beta.real/self.line.k0:.9f}{beta.imag/self.line.k0:+.9f}j.npy"
            try:
                Z = np.load(fn)
                if Z.shape[0] == self.cell.N:
                    self.log(f"  Z({beta/self.line.k0:.5f} k0): from {fn}")
                    return Z
            except (OSError, ValueError):
                pass
            Z = self._Z(beta)
            np.save(fn, Z)
            return Z
        return self._Z(beta)

    def _Z(self, beta):
        t0 = time.time()
        if self.sc is None:                    # near-image static part: once per geometry
            self.sc = K.StaticCache(self.cell, self.F, self.maps, self.line.K, workers=self.workers)
            self.log(f"  static part precomputed ({time.time() - t0:.0f} s)")
            t0 = time.time()
        Zs = self.sc.Z(beta, self.line.w)
        t1 = time.time()
        Zh = K.harmonic_Z(self.cell, self.xs, self.line, beta, self.Mc, self.Ks, self.pm, workers=self.workers)
        self.log(f"  Z({beta/self.line.k0:.5f} k0): static {t1 - t0:.0f} s, harmonics {time.time() - t1:.0f} s, N {self.cell.N}")
        return Zs + Zh

    def _probe(self):
        """y: J_z through the signal across the plane z = 0 (current I(0) = y.J)."""
        c = self.cell
        y = np.zeros(c.N)
        for i, key in enumerate(c.bkey):
            if key[0] == "tp" and key[2] == 0:
                d, a, b = key[1]
                if d == "x":                                    # horizontal segment (X[a], Y[b]) -> (X[a+1], Y[b])
                    if c.X[a + 1] <= c.xs["x_si"] + 1e-12:
                        y[i] = c.X[a + 1] - c.X[a]
                else:
                    if c.X[a] <= c.xs["x_si"] + 1e-12:
                        y[i] = c.Y[b + 1] - c.Y[b]
        # orientation: current flowing toward +z at plane 0 counts positive
        for i in np.nonzero(y)[0]:
            p, f, coef = next((p, f, cf) for p, f, cf in c.B[i] if c.pieces[p][3] == "z")
            typ = c.zfs[f][0]
            # 'u' piece (edge at the cell top) with +coef, or 'd' piece with -coef means +z flow
            y[i] *= np.sign(coef)                               # 'u' or 'd' piece, coef > 0: +z flow
        self.y = 2*y                                            # both halves (x mirror)

    def _mirror(self):
        """Basis permutation and signs of the mirror about the cell centre (z -> P - z, J_z -> -J_z)."""
        c = self.cell
        nz = len(c.Zg) - 1
        idx = {k: i for i, k in enumerate(c.bkey)}
        perm = np.zeros(c.N, int); sgn = np.zeros(c.N)
        P = c.P
        for i, key in enumerate(c.bkey):
            if key[0] == "zl":
                mk = ("zl", key[1], nz - 1 - key[2])
            else:
                mk = ("tp", key[1], (nz - key[2]) % nz)
            j = idx[mk]
            perm[i] = j
            # sign from one current piece
            p, f, coef = c.B[i][0]
            typ, a, b = c.zfs[f]
            comp = c.pieces[p][3]
            if typ == "D":
                ma, mb, mt = (P - a) % P, (P - a) % P, "D"
            else:
                aa, bb = (a - P, b - P) if a >= P - 1e-15 else (a, b)
                ma, mb = P - bb, P - aa
                mt = {"p": "p", "u": "d", "d": "u"}[typ]
            cand = [(cf, c.zfs[ff]) for pp, ff, cf in c.B[j] if pp == p]
            match = None
            for cf, (t2, a2, b2) in cand:
                a2n = a2 - P if a2 >= P - 1e-15 and t2 != "D" else a2
                if t2 == "D":
                    a2n = a2 % P
                if t2 == mt and abs(a2n - ma) < 1e-12:
                    match = cf
            if match is None:
                raise RuntimeError(f"no mirror piece for basis {i} {key}")
            sgn[i] = (-1 if comp == "z" else 1)*coef/match
        self.perm, self.msgn = perm, sgn
        # bases on the plane z = 0 are stored centred at z = P (pieces on the last cell and the
        # first cell shifted by +P): their mirror image lies at z = 0, one period back
        self.wrap0 = np.array([k[0] == "tp" and k[2] == 0 for k in c.bkey])

    def partner(self, J, beta):
        Jb = np.zeros_like(J)
        Jb[self.perm] = self.msgn*J*np.where(self.wrap0, np.exp(1j*beta*self.cell.P), 1.0)
        return np.exp(1j*beta*self.cell.P)*Jb

    def solve(self, n0, rel=1e-3, rebuild=True, save=None, dense_max=5000, nshow=8):
        """save: path prefix; the two matrices of each pass are stored (re-selection without a
        rebuild).  Up to dense_max unknowns all eigenvalues are computed (tee cells have many
        spurious near-null modes close to the line mode); the line mode is the one carrying the
        largest signal current per unit norm."""
        k0 = self.line.k0
        b1 = n0*k0
        for it in range(2 if rebuild else 1):
            b2 = b1*(1 + rel)
            Z1, Z2 = self.Z(b1), self.Z(b2)
            if save:
                np.savez(f"{save}_pass{it}.npz", Z1=Z1, Z2=Z2, b1=b1, b2=b2)
            D = (Z2 - Z1)/(b2 - b1)
            t0 = time.time()
            # (Z1 + (beta - b1) D) v = 0  ->  Z1 v = mu (-D) v, mu = beta - b1; shift-invert at mu = 0
            if Z1.shape[0] <= dense_max:                # dense generalized eigenproblem, all modes
                mu, vecs = linalg.eig(Z1, -D)
                ok = np.isfinite(mu) & (np.abs(mu) < 0.3*abs(b1))
                mu, vecs = mu[ok], vecs[:, ok]
            else:
                lu = linalg.lu_factor(Z1)
                op = LinearOperator(Z1.shape, matvec=lambda x: linalg.lu_solve(lu, -D @ x), dtype=complex)
                vals, vecs = eigs(op, k=4, which="LM")
                mu = 1/vals
            # the line mode: largest signal current for a normalised eigenvector
            cur = np.abs(self.y @ vecs)/np.linalg.norm(vecs, axis=0)
            for o in np.argsort(-cur)[:nshow]:
                self.log(f"    candidate n {(b1 + mu[o])/k0:.5f}  |I|/|J| {cur[o]:.3e}")
            self.log(f"  ({time.time() - t0:.0f} s)")
            o = int(np.argmax(cur))
            beta = b1 + mu[o]; J = vecs[:, o]
            b1 = beta*(1 - rel/2)
        return self._finish(beta, J, D)

    def solve_driven(self, n0, rel=1e-3, tol=1e-3, outer=6):
        """Line mode as the zero of 1/h(beta), h = y^T Z(beta)^-1 y: the signal line is driven and
        the propagation constant at which its response diverges is found (Newton inside the local
        linear model Z(b1) + (beta - b1) D).  No choice among eigenvalues is involved.
        Pass 0 builds Z at two betas (D by difference); later passes build Z once at the new
        estimate and keep D (Z is analytic and D varies slowly); D is rebuilt at the last point
        for Z0.  Stops when a pass moves the
        estimate by < tol relative: the error of the linear model is second order in that move
        (row 161: pass 0 moved 5e-3 and was off by 2e-4; pass 1 moves ~2e-4 -> error ~1e-7).
        The current is J = Z(beta)^-1 y at the zero."""
        k0, y = self.line.k0, self.y
        beta = complex(n0*k0)
        D = None
        for it in range(outer):
            b1 = beta
            Z1 = self.Z(b1)
            if D is None:
                b2 = b1*(1 + rel)
                D = (self.Z(b2) - Z1)/(b2 - b1)
            for _ in range(40):
                lu = linalg.lu_factor(Z1 + (beta - b1)*D)
                x = linalg.lu_solve(lu, y); xt = linalg.lu_solve(lu, y, trans=1)
                step = -(y @ x)/(xt @ (D @ x))              # Newton on 1/h: beta += h/h', h' = -xt.D.x
                beta = beta + step
                if abs(step) < 1e-12*abs(beta):
                    break
            self.log(f"  pass {it}: built at n {b1.real/k0:.5f}{b1.imag/k0:+.5f}j -> n {beta.real/k0:.6f}"
                     f"  alpha {-beta.imag*8.686/100:.5f} dB/cm")
            if abs(beta - b1) < tol*abs(b1):
                break
        if it > 0:
            # D kept from pass 0 finds the zero (Z1 is built next to it) but Z0 needs dZ/dbeta at
            # the zero itself: with D from pass 0, Z0 was off by 4 % (row 161 plain, 40.8 vs 42.5 ohm)
            b2 = b1*(1 + rel)
            D = (self.Z(b2) - Z1)/(b2 - b1)
        lu = linalg.lu_factor(Z1 + (beta - b1)*D)
        J = linalg.lu_solve(lu, y)
        J = linalg.lu_solve(lu, J)                          # one more inverse-iteration step
        return self._finish(beta, J, D)

    def _finish(self, beta, J, D):
        k0 = self.line.k0
        self.D = D
        I = (self.y @ J)*np.exp(1j*beta*self.cell.P)          # probe bases are stored at z = P
        J = J/I
        Jb = self.partner(J, beta)
        N = 2*0.5j*(Jb @ D @ J)/self.cell.P                     # x2: tests cover the half structure
        return dict(n=beta.real/k0, alpha=-beta.imag*8.686/100, Z=N, beta=beta, J=J)
