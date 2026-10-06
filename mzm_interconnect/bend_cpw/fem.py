"""
2D FEM verification of a bend geometry: the validated reference, not the line
model.

  * C: quasi-static Laplace with the layer stack (LN anisotropy), metal DOFs
    pinned at 1 V / 0 V, charge from the residual over the pinned DOFs, P2 on
    a tensor mesh graded at every metal surface (the equations of the FEM
    notebook's quasi-static step; mesh-converged to 0.01 % at hfine 0.025 um);
  * R, L: the longitudinal current solved INSIDE the gold (skin and proximity
    effect, no surface-impedance approximation):
        -div(grad A / mu0) + j w sigma A + sigma V'_k = 0  in electrode k,
        int_k sigma (-j w A - V'_k) = I_k,   Z = V'_gnd - V'_sig,
    checked against the exact Bessel solution of a gold coax (0.006 %), an
    independent PEEC integral equation (0.13 %) and a full-wave mode solve with
    the gold meshed (0.1 % on alpha);
  * G: the line model's dielectric conductance (1e-4 of the loss here);
  * gamma = sqrt((R + jwL)(G + jwC)), Zc = sqrt((R + jwL)/(G + jwC)).

Half domain x >= 0 by symmetry. Needs scikit-fem.
"""
from __future__ import annotations

import time

import numpy as np

from .model import C0, DB_PER_NEPER, EPS0, MU0, BendGeometry, line_model

MESSAGE_NO_SKFEM = ("The 2D FEM verification needs scikit-fem (pip install scikit-fem); "
                    "the line model and the inverse design do not.")


def _skfem():
    try:
        import skfem  # noqa: F401
    except ImportError as exc:                      # pragma: no cover
        raise RuntimeError(MESSAGE_NO_SKFEM) from exc


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
    v = np.unique(np.round(np.concatenate(out), 9))
    return v[np.concatenate([[True], np.diff(v) > 1e-6])]


# ---------------------------------------------------------------------------
# Capacitance
# ---------------------------------------------------------------------------
def capacitance(g: BendGeometry, hfine=0.025, air=550.0, pad=200.0, hmax_metal=0.5, hmax_far=30.0, r=1.2):
    """(C_eps, C_air) in F/m."""
    _skfem()
    from skfem import Basis, BilinearForm, ElementTriP0, ElementTriP2, MeshTri, asm, condense, solve
    from skfem.helpers import grad
    S, W, Wg, t = g.S_um, g.W_um, g.Wg_um, g.t_um
    stack = [(h / 1e-6, eh, ev) for h, eh, ev in g.layers()]
    xs, xgi = S / 2, S / 2 + W
    xgo = xgi + Wg
    x = axis([0.0, xs, xgi, xgo, xgo + pad], hfine, hmax_metal, hmax_far, [(0, xs), (xgi, xgo)], r)
    yb, y0 = [0.0], 0.0
    for h, _, _ in stack:
        y0 -= h
        yb.insert(0, y0)
    y = axis(yb + [t, t + air], hfine, hmax_metal, hmax_far, [(0.0, t)], r)
    mesh = MeshTri.init_tensor(x, y)
    cx, cy = mesh.p[:, mesh.t].mean(axis=1)
    in_t = (cy > 0) & (cy < t)
    metal = np.where(in_t & (cx < xs), 1, np.where(in_t & (cx > xgi) & (cx < xgo), 2, 0))
    ex, ey = np.ones(mesh.nelements), np.ones(mesh.nelements)
    top = 0.0
    for h, e1, e2 in stack:
        sel = (cy < top) & (cy > top - h)
        ex[sel], ey[sel] = e1, e2
        top -= h
    basis = Basis(mesh, ElementTriP2())
    b0 = basis.with_element(ElementTriP0())

    @BilinearForm
    def lap(u, v, w):
        return w.ex * grad(u)[0] * grad(v)[0] + w.ey * grad(u)[1] * grad(v)[1]

    d_sig = np.unique(basis.element_dofs[:, metal == 1])
    d_gnd = np.unique(basis.element_dofs[:, metal == 2])
    D = np.unique(np.concatenate([d_sig, d_gnd]))
    out = []
    for exx, eyy in ((ex, ey), (np.ones_like(ex), np.ones_like(ey))):
        K = asm(lap, basis, ex=b0.interpolate(exx), ey=b0.interpolate(eyy))
        u = np.zeros(basis.N)
        u[d_sig] = 1.0
        Kc, fc, uc, I = condense(K, np.zeros(basis.N), x=u, D=D)
        uu = uc.copy()
        uu[I] = solve(Kc, fc)
        out.append(2 * EPS0 * float((K @ uu)[d_sig].sum()))      # half domain -> x2
    return out[0], out[1]


# ---------------------------------------------------------------------------
# Series impedance from the current inside the gold
# ---------------------------------------------------------------------------
def series_impedance(g: BendGeometry, f_Hz, hfine=0.05, dom=600.0, hmax_metal=0.5, hmax_air=40.0, r=1.15,
                     progress=None):
    """R (ohm/m), L (H/m) at each frequency."""
    _skfem()
    import scipy.sparse.linalg as spla
    from skfem import Basis, BilinearForm, ElementTriP0, ElementTriP2, LinearForm, MeshTri, asm
    from skfem.helpers import dot, grad
    S, W, Wg, t = g.S_um, g.W_um, g.Wg_um, g.t_um
    xs, xgi = S / 2, S / 2 + W
    xgo = xgi + Wg
    x = axis([0.0, xs, xgi, xgo, dom], hfine, hmax_metal, hmax_air, [(0, xs), (xgi, xgo)], r)
    y = axis([-dom, 0.0, t, dom], hfine, hmax_metal, hmax_air, [(0.0, t)], r)
    mesh = MeshTri.init_tensor(x * 1e-6, y * 1e-6)
    c = mesh.p[:, mesh.t].mean(axis=1) * 1e6
    insl = (c[1] > 0) & (c[1] < t)
    cond = np.where(insl & (c[0] < xs), 1, np.where(insl & (c[0] > xgi) & (c[0] < xgo), 2, 0))
    basis = Basis(mesh, ElementTriP2())
    b0 = basis.with_element(ElementTriP0())
    sigma = g.sigma

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
    area = 0.5 * np.abs((p[0, 1] - p[0, 0]) * (p[1, 2] - p[1, 0]) - (p[0, 2] - p[0, 0]) * (p[1, 1] - p[1, 0]))
    B = np.column_stack([asm(lf, basis, s=b0.interpolate((cond == k) * sigma)) for k in (1, 2)])
    Gk = np.array([sigma * area[cond == k].sum() for k in (1, 2)])
    xm, ymn, ymx = mesh.p[0].max(), mesh.p[1].min(), mesh.p[1].max()
    D = basis.get_dofs(lambda X: (np.abs(X[0] - xm) < 1e-15) | (np.abs(X[1] - ymn) < 1e-15)
                       | (np.abs(X[1] - ymx) < 1e-15)).flatten()
    keep = np.setdiff1d(np.arange(basis.N), D)
    Kk, Mk, Bd = K.tocsr()[keep][:, keep], Ms.tocsr()[keep][:, keep], B[keep]
    R, L = [], []
    fl = np.atleast_1d(np.asarray(f_Hz, float))
    for i, f in enumerate(fl):
        if progress:
            progress(f"current inside the gold: {f / 1e9:g} GHz ({i + 1}/{len(fl)})", i / len(fl))
        w = 2 * np.pi * f
        # [K + jwM   B] [A ]   [ 0]       solved through its Schur complement on V'
        # [jw B^T    G] [V'] = [-I]
        lu = spla.splu((Kk + 1j * w * Mk).tocsc(), permc_spec="MMD_AT_PLUS_A")
        X = lu.solve(Bd.astype(complex))
        V = np.linalg.solve(np.diag(Gk).astype(complex) - 1j * w * (Bd.T @ X), -np.array([0.5, -0.5]))
        Z = -(V[0] - V[1])
        R.append(Z.real)
        L.append(Z.imag / w)
    return np.array(R), np.array(L), dict(n_el=mesh.nelements, ndof=basis.N)


def verify(g: BendGeometry, f_GHz=(10.0, 20.0, 60.0, 100.0, 200.0), hfine_c=0.025, hfine_rl=0.05,
           progress=None) -> dict:
    """Reference alpha, n_m, Z0 of the geometry at f_GHz, with the line model's
    values on the same grid for comparison."""
    t0 = time.time()
    f = np.atleast_1d(np.asarray(f_GHz, float)) * 1e9

    def sub(lo, hi):
        return (lambda m, x: progress(m, lo + (hi - lo) * x)) if progress else None
    if progress:
        progress("quasi-static capacitance (FEM)", 0.0)
    C, C_air = capacitance(g, hfine=hfine_c)
    R, L, info = series_impedance(g, f, hfine=hfine_rl, progress=sub(0.1, 1.0))
    w = 2 * np.pi * f
    m = line_model(g)
    Gd = m.G_diel(f)
    gam = np.sqrt((R + 1j * w * L) * (Gd + 1j * w * C))
    Zc = np.sqrt((R + 1j * w * L) / (Gd + 1j * w * C))
    model = m.evaluate(f)
    if progress:
        progress("done", 1.0)
    return dict(f_GHz=f / 1e9, alpha_dB_cm=DB_PER_NEPER * gam.real / 100, n_m=gam.imag / w * C0,
                Z0=np.abs(Zc), Zc=Zc, R=R, L=L, C=C, C_air=C_air, model=model,
                t_s=time.time() - t0, mesh=info)
