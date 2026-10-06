"""
Quasi-static capacitance of the bend CPW on a tensor-product mesh: the same
equations as cell [1] of the user's notebook (anisotropic Laplace, gold DOFs
pinned at 1 V / 0 V, charge from the residual over the pinned DOFs, natural
outer boundary), but without gmsh, on the half domain x >= 0. Seconds per
geometry, so it can run inside the GUI and in an inverse-design loop.

Layers are given from the metal down: [(h_um, eps_x, eps_y), ...]; the last
one is the substrate. Air above and in the gaps.
"""
import time

import numpy as np
from skfem import Basis, BilinearForm, ElementTriP0, ElementTriP2, MeshTri, asm, condense, solve
from skfem.helpers import grad

import eddy_tensor as ET

EPS0 = 8.8541878128e-12
BEND_STACK = [(3.6, 3.9, 3.9), (0.275, 28.0, 44.0), (4.7, 3.9, 3.9), (550.0, 11.7, 11.7)]


def build(S, W, Wg, t, stack, air=550.0, pad=200.0, hfine=0.05, hmax_metal=0.5, hmax_far=30.0, r=1.2):
    xs, xgi = S / 2, S / 2 + W
    xgo = xgi + Wg
    x = ET.axis([0.0, xs, xgi, xgo, xgo + pad], hfine, hmax_metal, hmax_far, [(0, xs), (xgi, xgo)], r)
    yb, y0 = [0.0], 0.0
    for h, _, _ in stack:
        y0 -= h
        yb.insert(0, y0)
    y = ET.axis(yb + [t, t + air], hfine, hmax_metal, hmax_far, [(0.0, t)], r)
    x, y = (np.unique(np.round(v, 9)) for v in (x, y))
    x, y = (v[np.concatenate([[True], np.diff(v) > 1e-6])] for v in (x, y))
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
    return mesh, metal, ex, ey


def capacitance(S, W, Wg, t, stack=BEND_STACK, **kw):
    """C_eps, C_air (F/m), all lengths in um."""
    t0 = time.time()
    mesh, metal, ex, ey = build(S, W, Wg, t, stack, **kw)
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
    return out[0], out[1], dict(n_el=mesh.nelements, ndof=basis.N, t_s=time.time() - t0)


if __name__ == "__main__":
    import json
    qs = [json.loads(l) for l in open("results/doe_qs.jsonl")]
    for r in qs[:6]:
        st = [(r["h"], 3.9, 3.9)] + BEND_STACK[1:]
        Ce, Ca, info = capacitance(r["S"], r["W"], 50.0, r["t"], st)
        print(f"S {r['S']:6.2f} W {r['W']:5.2f} t {r['t']:4.2f} h {r['h']:4.2f}: C_eps {Ce*1e12:8.3f} vs FEM "
              f"{r['C_eps']*1e12:8.3f} ({(Ce/r['C_eps']-1)*100:+.2f} %)  C_air {(Ca/r['C_air']-1)*100:+.2f} %  {info}")
