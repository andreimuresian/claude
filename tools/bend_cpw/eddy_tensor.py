"""
Eddy-current (magneto-quasi-static) series impedance of the bend CPW on a
graded tensor mesh (no gmsh). Half domain x >= 0 by symmetry (A even in x:
natural Neumann condition on x = 0). See eddy_fem.py for the equations.

    -div(nu grad A) + j w sigma A + sigma V'_k = 0   in conductor k
    int_k sigma(-j w A - V'_k) = I_k,   I_sig = 1, I_gnd = -1/2 (each)
    A = 0 on the far boundary

Z' = V'_sig - V'_gnd ;  R = Re Z', L = Im Z' / w.
"""
import time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from skfem import Basis, BilinearForm, ElementTriP0, ElementTriP1, ElementTriP2, LinearForm, MeshTri, asm
from skfem.helpers import dot, grad

MU0 = 4e-7 * np.pi
SIGMA_AU = 4.56e7


def graded(a, b, ha, hb, hmax, r=1.15):
    """Points from a to b, spacing ha at a and hb at b, growing by r up to hmax."""
    L = b - a
    left, right = [0.0], [0.0]
    h = ha
    while left[-1] < L / 2:
        left.append(left[-1] + h)
        h = min(h * r, hmax)
    h = hb
    while right[-1] < L / 2:
        right.append(right[-1] + h)
        h = min(h * r, hmax)
    left = np.array(left)
    right = L - np.array(right)
    pts = np.concatenate([left[left < L / 2], right[right >= L / 2][::-1]])
    pts = np.unique(np.concatenate([[0.0, L], pts]))
    # drop points closer than half the local spacing to the mid join
    keep = [pts[0]]
    for p in pts[1:]:
        if p - keep[-1] > 0.3 * min(ha, hb):
            keep.append(p)
    keep[-1] = L
    return a + np.array(keep)


def axis(breaks, hfine, hmax_metal, hmax_air, metal_spans, r=1.15):
    out = []
    for a, b in zip(breaks[:-1], breaks[1:]):
        inside = any(lo <= a and b <= hi for lo, hi in metal_spans)
        hmax = hmax_metal if inside else hmax_air
        ha = hfine if a != breaks[0] else hmax_air
        hb = hfine if b != breaks[-1] else hmax_air
        if a == 0.0 and breaks[0] == 0.0:          # symmetry plane: no need to refine
            ha = min(hmax, 0.5)
        out.append(graded(a, b, ha, hb, hmax, r))
    return np.unique(np.concatenate(out))


def build(sig_w=35.0, gap=4.15, gnd_w=50.0, t=2.0, dom=600.0, hfine=0.03, hmax_metal=0.5,
          hmax_air=40.0, r=1.15):
    xs = sig_w / 2
    xgi = xs + gap
    xgo = xgi + gnd_w
    x = axis([0.0, xs, xgi, xgo, dom], hfine, hmax_metal, hmax_air, [(0, xs), (xgi, xgo)], r)
    y = axis([-dom, 0.0, t, dom], hfine, hmax_metal, hmax_air, [(0.0, t)], r)
    mesh = MeshTri.init_tensor(x * 1e-6, y * 1e-6)
    c = mesh.p[:, mesh.t].mean(axis=1) * 1e6
    insl = (c[1] > 0) & (c[1] < t)
    cond = np.where(insl & (c[0] < xs), 1, np.where(insl & (c[0] > xgi) & (c[0] < xgo), 2, 0))
    return mesh, cond


def solve_on_mesh(mesh, cond, I, dirichlet, f_list, order=2, sigma=SIGMA_AU):
    """Series impedance per unit length on any triangle mesh (metres).

    cond[e] = k > 0 marks the elements of conductor k (k = 1..N), 0 elsewhere.
    I[k-1] is the current imposed on conductor k (they must sum to zero over the
    full cross-section). dirichlet(x) -> bool marks the boundary where A = 0;
    every other boundary is a natural (Neumann) boundary, i.e. a symmetry plane
    with A even. Returns V'_k for every frequency: the longitudinal voltage drop
    per unit length of conductor k is -V'_k (E = -j w A - V')."""
    basis = Basis(mesh, ElementTriP2() if order == 2 else ElementTriP1())
    b0 = basis.with_element(ElementTriP0())
    ncond = int(cond.max())

    @BilinearForm
    def stiff(u, v, w):
        return dot(grad(u), grad(v)) / MU0

    @BilinearForm
    def mass(u, v, w):
        return w.s * u * v

    @LinearForm
    def lf(v, w):
        return w.s * v

    K = asm(stiff, basis)
    Ms = asm(mass, basis, s=b0.interpolate(np.where(cond > 0, sigma, 0.0)))
    p = mesh.p[:, mesh.t]
    areas_el = 0.5 * np.abs((p[0, 1] - p[0, 0]) * (p[1, 2] - p[1, 0])
                            - (p[0, 2] - p[0, 0]) * (p[1, 1] - p[1, 0]))
    ks = range(1, ncond + 1)
    B = np.column_stack([asm(lf, basis, s=b0.interpolate((cond == k) * sigma)) for k in ks])
    G = np.array([sigma * areas_el[cond == k].sum() for k in ks])
    D = basis.get_dofs(dirichlet).flatten()
    keep = np.setdiff1d(np.arange(basis.N), D)
    Kk, Mk, Bk = K.tocsr()[keep][:, keep], Ms.tocsr()[keep][:, keep], sp.csr_matrix(B[keep])
    out = []
    Bd = Bk.toarray()
    for f in np.atleast_1d(f_list):
        w = 2 * np.pi * f
        # [K + jwM   B] [A ]   [ 0]
        # [jw B^T    G] [V'] = [-I]   solved by its Schur complement on V'
        # (identical result; avoids LU fill from the dense constraint rows)
        lu = spla.splu((Kk + 1j * w * Mk).tocsc(), permc_spec="MMD_AT_PLUS_A")
        X = lu.solve(Bd.astype(complex))
        S = np.diag(G).astype(complex) - 1j * w * (Bd.T @ X)
        out.append(np.linalg.solve(S, -np.asarray(I, float)))
    return out, dict(n_el=mesh.nelements, ndof=basis.N)


def solve_Z(f_list, order=2, sigma=SIGMA_AU, **geom):
    """CPW (signal + two grounds) on the half domain x >= 0."""
    t0 = time.time()
    mesh, cond = build(**geom)
    xmax, ymin, ymax = mesh.p[0].max(), mesh.p[1].min(), mesh.p[1].max()

    def far(xx):
        return (np.abs(xx[0] - xmax) < 1e-12) | (np.abs(xx[1] - ymin) < 1e-12) | (np.abs(xx[1] - ymax) < 1e-12)
    # half domain: the signal carries 1/2 here, the right ground -1/2
    Vs, info = solve_on_mesh(mesh, cond, [0.5, -0.5], far, f_list, order, sigma)
    res = []
    for f, V in zip(np.atleast_1d(f_list), Vs):
        w = 2 * np.pi * f
        Z = -(V[0] - V[1])                   # E = -jwA - V': the voltage drop is -V'
        res.append(dict(f_GHz=f / 1e9, R=Z.real, L=Z.imag / w))
    info["t_s"] = time.time() - t0
    return res, info


if __name__ == "__main__":
    print("DC exact R =", 1 / (SIGMA_AU * 35e-6 * 2e-6) + 0.5 / (SIGMA_AU * 50e-6 * 2e-6), "ohm/m")
    for hf in (0.06, 0.03):
        r, info = solve_Z([1e5, 1e9, 10e9, 60e9, 200e9], hfine=hf)
        print("hfine", hf, info)
        for x in r:
            print("   ", {k: round(v, 6) for k, v in x.items()})
