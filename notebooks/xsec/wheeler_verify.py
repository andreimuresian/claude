"""Is Wheeler's rule the converged value of the notebook's conductor-loss integral?

Both use only the air problem (every eps = 1), so the test geometry is the three
electrodes of one row in free space, Neumann outer box as in the notebook.

  contour  R' = Rs * contour (dV/dn)^2 dl / S^2          (notebook, cell [1])
  Wheeler  R' = Rs (L(a) - L(0)) / (mu0 a),  L = 1/(c^2 C_air),
           every metal face receded by a

The two are the same quantity: receding the walls by a changes the magnetic
energy by (mu0/2) |H_t|^2 a per unit area, which is the contour integrand.
Test: round the electrode corners with radius rho.  For rho > 0 the integrand is
smooth, the contour integral converges normally, and it must match Wheeler.
For rho = 0 (the notebook's sharp corners) the contour integral converges only
slowly; Wheeler's value there is checked against the rho -> 0 trend.
Run: python wheeler_verify.py [row]     (-> wheeler_verify.txt)
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import sys
import warnings
from collections import OrderedDict
from multiprocessing import Pool

import numpy as np
from shapely.affinity import scale
from shapely.geometry import Point, box
from shapely.ops import unary_union
from skfem import Basis, BilinearForm, ElementTriP1, Functional, InteriorFacetBasis, MeshTri, asm, condense, solve
from skfem.helpers import grad
from femwell.mesh import mesh_from_OrderedDict

import xsec2d as x
from average import load_rows

warnings.filterwarnings("ignore")
DELTA = x.skin_au * 1e6


def electrodes(r, rho, a):
    """Signal and right/left grounds (um), corners rounded by rho, faces receded by a."""
    xs, xg = r.WS / 2, r.WS / 2 + r.GAP
    rects = [box(-xs, 0, xs, r.MTX), box(xg, 0, xg + 70.0, r.MTX)]
    rects.append(scale(rects[1], xfact=-1, origin=(0, 0)))
    out = []
    for p in rects:
        if rho > 0:
            p = p.buffer(-rho, join_style=2).buffer(rho, quad_segs=48)
        if a != 0:                                  # a < 0 grows the metal
            p = p.buffer(-a, join_style=2 if rho == 0 else 1, quad_segs=48)
        out.append(p)
    return out, [(sx * c[0], c[1]) for c in ((xs, 0), (xs, r.MTX), (xg, 0), (xg, r.MTX),
                                             (xg + 70, 0), (xg + 70, r.MTX)) for sx in (1, -1)]


def solve_air(r, rho, a, h):
    """C_air/eps0 and the contour integral; h = cell size at the corners/arcs (um)."""
    metals, corners = electrodes(r, rho, a)
    metal = unary_union(metals)
    xd = r.WS / 2 + r.GAP + 70 + 200
    rc = rho + 0.3
    corner = unary_union([Point(c).buffer(rc) for c in corners]).difference(metal)
    collar = metal.buffer(1.0, join_style=2).difference(unary_union([metal, corner]))
    air = box(-xd, -555, xd, r.MTX + 550).difference(unary_union([metal, corner, collar]))
    polys = OrderedDict([("corner", corner), ("collar", collar), ("m0", metals[0]),
                         ("m1", metals[1]), ("m2", metals[2]), ("air", air)])
    res = {"corner": {"resolution": h, "distance": 0.5}, "collar": {"resolution": 0.1, "distance": 1.0},
           "m0": {"resolution": 1.0, "distance": 2}, "m1": {"resolution": 1.0, "distance": 2},
           "m2": {"resolution": 1.0, "distance": 2}, "air": {"resolution": 30.0, "distance": 30}}
    raw = mesh_from_OrderedDict(polys, resolutions=res, default_resolution_min=0.4 * h,
                                default_resolution_max=35.0)
    mesh = MeshTri(raw.points[:, :2].T, raw.cells_dict["triangle"].T)
    tri = raw.cell_data_dict["gmsh:physical"]["triangle"]
    reg = np.empty(mesh.nelements, dtype=object)
    for name, sid in raw.field_data.items():
        reg[tri == (sid[0] if hasattr(sid, "__getitem__") else sid)] = name.split("___")[0]
    reg = reg.astype(str)
    area = 0.5 * np.abs(np.cross((mesh.p[:, mesh.t[1]] - mesh.p[:, mesh.t[0]]).T,
                                 (mesh.p[:, mesh.t[2]] - mesh.p[:, mesh.t[0]]).T))
    for k, pm in zip(("m0", "m1", "m2"), metals):         # every electrode must be meshed as metal
        got = area[reg == k].sum()
        if abs(got / pm.area - 1) > 1e-3:
            raise RuntimeError(f"rho {rho} a {a} h {h}: {k} meshed area {got:.3f} vs polygon {pm.area:.3f}")
    bf = mesh.boundary_facets()                           # the mesh must be conforming:
    mid = mesh.p[:, mesh.facets[:, bf]].mean(axis=1)      # no boundary facet inside the box
    inner = ~((np.abs(np.abs(mid[0]) - xd) < 1e-6) | (np.abs(mid[1] + 555) < 1e-6)
              | (np.abs(mid[1] - r.MTX - 550) < 1e-6))
    if inner.any():
        raise RuntimeError(f"rho {rho} a {a} h {h}: {inner.sum()} internal boundary facets")
    is_metal = np.isin(reg, ("m0", "m1", "m2")); is_sig = reg == "m0"
    bq = Basis(mesh, ElementTriP1())

    @BilinearForm
    def lap(u, v, w):
        return grad(u)[0] * grad(v)[0] + grad(u)[1] * grad(v)[1]

    @Functional
    def dvdn2(w):
        return (w.gu.grad[0] * w.nx + w.gu.grad[1] * w.ny) ** 2

    K = asm(lap, bq)
    ed = lambda m: np.unique(bq.element_dofs[:, np.where(m)[0]])
    ds, dm = ed(is_sig), ed(is_metal)
    uD = np.zeros(bq.N); uD[ds] = 1.0
    Kc, fc, uc, I = condense(K, np.zeros(bq.N), x=uD, D=dm)
    u = uc.copy(); u[I] = solve(Kc, fc)
    S = float((K @ u)[ds].sum())
    f2t = mesh.f2t
    on = (f2t[1] >= 0) & (is_metal[f2t[0]] ^ is_metal[f2t[1]])
    tot = 0.0
    for side in (0, 1):
        other = 1 - side
        fac = np.where(on & is_metal[f2t[other]] & ~is_metal[f2t[side]])[0]
        if fac.size == 0:
            continue
        p = mesh.p[:, mesh.facets[:, fac]]
        tan = p[:, 1, :] - p[:, 0, :]
        nrm = np.vstack([tan[1], -tan[0]]); nrm /= np.linalg.norm(nrm, axis=0)
        cen = mesh.p[:, mesh.t[:, f2t[other][fac]]].mean(axis=1)
        nrm *= np.sign(((p.mean(axis=1) - cen) * nrm).sum(axis=0))
        fb = InteriorFacetBasis(mesh, ElementTriP1(), facets=fac, side=side)
        tot += dvdn2.assemble(fb, gu=fb.interpolate(u), nx=nrm[0][:, None], ny=nrm[1][:, None])
    return S, x.Rs_au * 1e6 * tot / S ** 2, mesh.nelements


def job(args):
    row, rho, a, h = args
    return args, solve_air(load_rows().loc[row], rho, a, h)


def main():
    row = int(sys.argv[1]) if len(sys.argv) > 1 else 49
    r = load_rows().loc[row]
    RHO = [0.0, 0.1, 0.3]                      # 1 um: gmsh fails on the merged arcs
    H = {0.0: [0.05, 0.025, 0.0125]}
    for rho in RHO[1:]:
        H[rho] = [rho / 4, rho / 8, rho / 16]
    jobs = [(row, rho, 0.0, h) for rho in RHO for h in H[rho]]
    A = {rho: min(DELTA / 8, rho / 4) if rho > 0 else DELTA / 8 for rho in RHO}
    jobs += [(row, rho, s * A[rho], H[rho][-1]) for rho in RHO for s in (1, -1)]
    res = {}
    with Pool(4) as p:
        for k, v in p.imap_unordered(job, jobs):
            res[k] = v
            print(f"   done rho {k[1]} a {k[2]*1e3:+.0f} nm h {k[3]*1e3:.2f} nm: {v[2]} el", file=sys.stderr, flush=True)
    print(f"row {row}: WS {r.WS:.2f}  GAP {r.GAP:.2f}  MTX {r.MTX:.2f} um, electrodes in free space")
    for rho in RHO:
        L = {s: 1 / (x.C0 ** 2 * x.EPS0 * res[(row, rho, s * A[rho], H[rho][-1])][0]) for s in (0, 1, -1)}
        Rf = x.Rs_au * (L[1] - L[0]) / (x.MU0 * A[rho] * 1e-6)
        Rw = x.Rs_au * (L[1] - L[-1]) / (x.MU0 * 2 * A[rho] * 1e-6)
        print(f" corner radius {rho:4.2f} um   Wheeler R' {Rw:7.1f} ohm/m central, {Rf:7.1f} one-sided"
              f"  (step {A[rho]*1e3:.0f} nm)")
        for h in H[rho]:
            _, Rc, n = res[(row, rho, 0.0, h)]
            print(f"     contour, cell {h*1e3:6.2f} nm ({n:7d} el): R' {Rc:7.1f}   vs Wheeler {(Rc/Rw-1)*100:+6.2f}%")


if __name__ == "__main__":
    main()
