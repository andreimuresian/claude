"""2D FEM of one CPW cross-section, ported from the author's notebook
(unetched_nmZ0_aRF_Claude.ipynb, "COMSOL Goldilocks" model).

The geometry, materials, mesh controls, quasi-static extraction (cell [1]), the
vector eigensolver (cell [2]), the mode filter (cell [3]) and the IBC correction
(cell [4]) are the notebook's.  The only generalisation: each ground electrode is
a list of metal pieces, so the cross-sections through the tee can be built:

    section C (no slot)      [(x_gi, x_go, 'gnd')]                  -> the notebook
    section A (stem + head)  [(x_gi + W1 + W2, x_go, 'gnd')]
    section B, L2 > L1       [(x_gi, x_gi + W1, 'finger'), (x_gi + W1 + W2, x_go, 'gnd')]
    section B, L1 > L2       [(x_gi + W1, x_go, 'gnd')]

A 'finger' is the ground metal between the gap and the overhanging tee head.  It is
a cantilever: joined to the ground only at one end along the line.  The
quasi-static solve returns it both ways: grounded (it is at ground potential) and
floating (zero net current along it, which is what a cantilever carries).

Lengths in um unless stated.  `section()` returns SI per-unit-length quantities.
"""
import time
import warnings
from collections import OrderedDict

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from shapely.affinity import scale as _scale
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from skfem import (Basis, BilinearForm, ElementTriN1, ElementTriP0, ElementTriP1,
                   Functional, InteriorFacetBasis, MeshTri, asm, condense, solve)
from skfem.helpers import curl, dot, grad
from skfem.utils import solver_eigen_scipy
from femwell.mesh import mesh_from_OrderedDict

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------- constants (notebook)
f0 = 60.0e9
C0 = 299792458.0
EPS0 = 8.8541878128e-12
MU0 = 4.0e-7 * np.pi
DB_PER_NEPER = 20.0 * np.log10(np.e)
SIGMA_AU = 4.56e7
skin_au = np.sqrt(2.0 / (2 * np.pi * f0 * MU0 * SIGMA_AU))
Rs_au = 1.0 / (SIGMA_AU * skin_au)
OMEGA = 2.0 * np.pi * f0

aul_w, cap_h, tfln, wg_top, theta = 70.0, 1.40, 0.460, 0.80, 60.0
box_h, si_h, air_h, lat_pad = 4.7, 550.0, 550.0, 200.0

MATERIALS = {
    "LN":   {"eps_rf": (28.0, 44.0, 44.0), "sigma": 1e-3},
    "SiO2": {"eps_rf": (3.9, 3.9, 3.9),    "sigma": 1e-13},
    "Si":   {"eps_rf": (11.7, 11.7, 11.7), "sigma": 1e-12},
    "air":  {"eps_rf": (1.0, 1.0, 1.0),    "sigma": 0.0},
    "Au":   {"eps_rf": (1.0, 1.0, 1.0),    "sigma": 0.0},
}

# ---------------------------------------------------------------- mesh controls (notebook)
COLLAR_W, COLLAR_H = 4.0, 4.0
CORNER_BOX, CORNER_RES = 0.25, 0.050
SKIN_T, SKIN_REACH, SKIN_RES = 0.10, 5.0, 0.100
BASE_RES = {"corner_ring": CORNER_RES, "skin_ring": SKIN_RES,
            "cap_r": 0.20, "cap_l": 0.20, "rib_r": 0.12, "rib_l": 0.12,
            "air_gap": 0.30, "slab_near": 0.25, "box_near": 2.0, "el": 0.80,
            "air_near": 2.0, "slab_far": 6.0, "box_far": 6.0, "si": 30.0, "air_far": 30.0}
BASE_DIST = {"corner_ring": 0.6, "skin_ring": 1.0, "cap_r": 1.0, "cap_l": 1.0,
             "rib_r": 1.0, "rib_l": 1.0, "air_gap": 3.0, "slab_near": 3.0,
             "box_near": 5.0, "el": 3.0, "air_near": 10.0, "slab_far": 10.0,
             "box_far": 10.0, "si": 30.0, "air_far": 30.0}


def mirror(p):
    return _scale(p, xfact=-1.0, yfact=1.0, origin=(0, 0))


def pieces_for(sec, WS, GAP, W1, W2, L1, L2):
    """Right-hand ground pieces of section 'C', 'A' or 'B' (mirrored on the left)."""
    x_gi = WS / 2 + GAP
    x_go = x_gi + aul_w
    if sec == "C":
        return [(x_gi, x_go, "gnd")]
    if sec == "A":
        return [(x_gi + W1 + W2, x_go, "gnd")]
    if L2 > L1:
        return [(x_gi, x_gi + W1, "finger"), (x_gi + W1 + W2, x_go, "gnd")]
    return [(x_gi + W1, x_go, "gnd")]


def section_lengths(L1, L2, P=200.0):
    """Lengths along the line of sections A, B, C inside one period."""
    return {"A": min(L1, L2), "B": abs(L2 - L1), "C": P - max(L1, L2)}


class Section:
    """Mesh + materials of one cross-section (notebook cell [0])."""

    def __init__(self, WS, GAP, MTX, CAP_W, ETCH, pieces, mesh_factor=1.0, corner_factor=1.0):
        t0 = time.time()
        auc_w, gap, au_h, cap_w, wg_h = WS, GAP, MTX, CAP_W, ETCH
        slab_h = tfln - wg_h
        basetta = wg_h / np.tan(np.deg2rad(theta))
        wg_bottom = wg_top + 2.0 * basetta
        x_sig = auc_w / 2.0
        x_gi = x_sig + gap
        x_go = x_gi + aul_w
        x_dom = x_go + lat_pad
        x_wg = x_sig + gap / 2.0
        y_el = slab_h + au_h
        y_rib = slab_h + wg_h
        cb, cr, sr = CORNER_BOX, CORNER_RES * corner_factor, SKIN_RES * corner_factor
        self.slab_h, self.y_el, self.x_sig, self.x_gi = slab_h, y_el, x_sig, x_gi

        def rib(xc):
            return Polygon([(xc - wg_bottom / 2, slab_h), (xc - wg_top / 2, y_rib),
                            (xc + wg_top / 2, y_rib), (xc + wg_bottom / 2, slab_h)])

        rib_r = rib(x_wg); rib_l = mirror(rib_r)
        cap_r = box(x_wg - cap_w / 2, slab_h, x_wg + cap_w / 2, slab_h + cap_h).difference(rib_r)
        cap_l = mirror(cap_r)

        metal = OrderedDict()
        metal["el_sig"] = (box(-x_sig, slab_h, x_sig, y_el), "sig")
        for k, (a, b, kind) in enumerate(pieces):
            metal[f"el_gr{k}"] = (box(a, slab_h, b, y_el), kind)
            metal[f"el_gl{k}"] = (mirror(box(a, slab_h, b, y_el)), kind)
        solids = unary_union([v[0] for v in metal.values()] + [cap_r, cap_l, rib_r, rib_l])

        # every metal x-edge (right half), and the walls that face another conductor:
        # the notebook refines the signal walls and the ground's gap-facing wall; here
        # every wall except the outermost ground edge x_go.
        xs_edges = sorted({x_sig} | {a for a, _, _ in pieces} | {b for _, b, _ in pieces})
        walls_x = [x for x in xs_edges if x < x_go - 1e-9]
        corners = [box(s * xc - cb, yc - cb, s * xc + cb, yc + cb)
                   for xc in xs_edges for s in (1, -1) for yc in (slab_h, y_el)]
        corner_ring = unary_union(corners).difference(solids)
        walls = []
        for xc in walls_x:
            for s in (1, -1):
                walls.append(box(s * xc - SKIN_T, slab_h, s * xc + SKIN_T, y_el))
                lo, hi = (xc, xc + SKIN_REACH)            # notebook: away from the centre
                seg = (lo, hi) if s > 0 else (-hi, -lo)
                walls.append(box(seg[0], y_el, seg[1], y_el + SKIN_T))
                walls.append(box(seg[0], slab_h - SKIN_T, seg[1], slab_h))
        skin_ring = unary_union(walls).difference(unary_union([solids, corner_ring]))

        x_in = max(a for a, _, _ in pieces)            # inner edge of the outermost ground
        rings = unary_union([solids, corner_ring, skin_ring])
        air_gap = box(-x_in - COLLAR_W, slab_h, x_in + COLLAR_W, y_el + COLLAR_H).difference(rings)
        air_near = box(-x_go - 15.0, slab_h, x_go + 15.0, y_el + 15.0).difference(
            unary_union([rings, air_gap]))
        air_far = box(-x_dom, slab_h, x_dom, slab_h + air_h).difference(
            unary_union([rings, air_gap, air_near]))
        slab_near = box(-x_go - 15.0, 0.0, x_go + 15.0, slab_h).difference(
            unary_union([corner_ring, skin_ring]))
        slab_far = box(-x_dom, 0.0, x_dom, slab_h).difference(slab_near)
        box_near = box(-x_go - 15.0, -box_h, x_go + 15.0, 0.0)
        box_far = box(-x_dom, -box_h, x_dom, 0.0).difference(box_near)
        si = box(-x_dom, -box_h - si_h, x_dom, -box_h)

        polys = OrderedDict([("corner_ring", corner_ring), ("skin_ring", skin_ring),
                             ("cap_r", cap_r), ("cap_l", cap_l), ("rib_r", rib_r), ("rib_l", rib_l)])
        for k, (p, _) in metal.items():
            polys[k] = p
        for k, v in [("air_gap", air_gap), ("slab_near", slab_near), ("air_near", air_near),
                     ("box_near", box_near), ("slab_far", slab_far), ("box_far", box_far),
                     ("si", si), ("air_far", air_far)]:
            polys[k] = v
        polys = OrderedDict((k, v) for k, v in polys.items() if not v.is_empty)

        def res_of(k):
            base = "el" if k.startswith("el_") else k
            r = {"corner_ring": cr, "skin_ring": sr}.get(base, BASE_RES[base] * mesh_factor)
            return {"resolution": r, "distance": BASE_DIST[base]}

        raw = mesh_from_OrderedDict(polys, resolutions={k: res_of(k) for k in polys},
                                    default_resolution_min=0.4 * min(cr, sr),
                                    default_resolution_max=35.0)
        mesh = MeshTri(raw.points[:, :2].T, raw.cells_dict["triangle"].T)
        tri = raw.cell_data_dict["gmsh:physical"]["triangle"]
        name_to_id = {n: (d[0] if hasattr(d, "__getitem__") else d) for n, d in raw.field_data.items()}
        region = np.empty(mesh.nelements, dtype=object)
        for raw_name, s_id in name_to_id.items():
            base = raw_name.split("___")[0]
            if base in polys:
                region[tri == s_id] = base
        assert not any(r is None for r in region), "untagged elements"
        region = region.astype(str)

        r2m = {"cap_r": "SiO2", "cap_l": "SiO2", "rib_r": "LN", "rib_l": "LN",
               "slab_near": "LN", "slab_far": "LN", "box_near": "SiO2", "box_far": "SiO2",
               "si": "Si", "air_gap": "air", "air_near": "air", "air_far": "air"}
        mat = np.array([("Au" if r.startswith("el_") else r2m.get(r, "air")) for r in region], dtype=object)
        collar = np.isin(region, ("corner_ring", "skin_ring"))
        yc = mesh.p[1, mesh.t].mean(axis=0)
        layer = np.where(yc < 0.0, "SiO2", np.where(yc < slab_h, "LN", "air"))
        mat[collar] = layer[collar]

        self.mesh, self.region, self.mat = mesh, region, mat
        self.is_metal = np.array([r.startswith("el_") for r in region])
        kind = {k: v[1] for k, v in metal.items()}
        self.kind_of_el = np.array([kind.get(r, "") for r in region], dtype=object)
        self.is_signal = self.kind_of_el == "sig"
        self.is_finger = self.kind_of_el == "finger"
        self.finger_regions = [k for k, v in metal.items() if v[1] == "finger"]
        self.eps = [np.array([MATERIALS[m]["eps_rf"][i] for m in mat], float) for i in range(3)]
        self.sigma = np.array([MATERIALS[m]["sigma"] for m in mat], float)

        f2t = mesh.f2t
        has_two = f2t[1] >= 0
        self.on_contour = has_two & (self.is_metal[f2t[0]] ^ self.is_metal[f2t[1]])
        self.t_mesh = time.time() - t0

    # ------------------------------------------------------------ contours (notebook)
    def contour_groups(self, mask):
        mesh, f2t, is_metal = self.mesh, self.mesh.f2t, self.is_metal
        out = []
        for side in (0, 1):
            other = 1 - side
            fac = np.where(mask & is_metal[f2t[other]] & ~is_metal[f2t[side]])[0]
            if fac.size == 0:
                continue
            p = mesh.p[:, mesh.facets[:, fac]]
            tan = p[:, 1, :] - p[:, 0, :]
            nrm = np.vstack([tan[1], -tan[0]])
            nrm /= np.linalg.norm(nrm, axis=0)
            midpoint = p.mean(axis=1)
            centroid = mesh.p[:, mesh.t[:, f2t[other][fac]]].mean(axis=1)
            nrm *= np.sign(((midpoint - centroid) * nrm).sum(axis=0))
            out.append((fac, side, nrm))
        return out

    # ------------------------------------------------------------ quasi-static (cell [1])
    def quasi_static(self):
        """C (eps), C_air, Wheeler R', G with the finger grounded, and C_air, R'
        with the finger floating (zero net charge = zero net current).  SI units."""
        mesh = self.mesh
        bq = Basis(mesh, ElementTriP1())
        b0 = Basis(mesh, ElementTriP0())

        @BilinearForm
        def lap(u, v, w):
            return w.ex * grad(u)[0] * grad(v)[0] + w.ey * grad(u)[1] * grad(v)[1]

        @Functional
        def dVdn2(w):
            return (w.gu.grad[0] * w.nx + w.gu.grad[1] * w.ny) ** 2

        @Functional
        def joule(w):
            return w.s * (w.gu.grad[0] ** 2 + w.gu.grad[1] ** 2)

        el_dofs = lambda m: np.unique(bq.element_dofs[:, np.where(m)[0]])
        d_sig = el_dofs(self.is_signal)
        d_fin = el_dofs(self.is_finger)
        d_gnd = el_dofs(self.is_metal & ~self.is_signal & ~self.is_finger)
        fingers = [el_dofs(self.region == r) for r in self.finger_regions]

        def solve_static(ex, ey, floating):
            K = asm(lap, bq, ex=b0.interpolate(ex), ey=b0.interpolate(ey))
            D = np.unique(np.concatenate([d_sig, d_gnd] + ([] if floating else [d_fin])))
            uD = np.zeros(bq.N); uD[d_sig] = 1.0
            Kc, fc, uc, I = condense(K, np.zeros(bq.N), x=uD, D=D)
            if floating and fingers:
                # tie every finger's DOFs to one unknown potential (floating conductor)
                col = np.arange(I.size)
                pos = -np.ones(bq.N, int); pos[I] = np.arange(I.size)
                nxt = I.size
                for g in fingers:
                    col[pos[g]] = nxt; nxt += 1
                # renumber columns compactly
                uniq, colc = np.unique(col, return_inverse=True)
                Pm = sparse.csr_matrix((np.ones(I.size), (np.arange(I.size), colc)),
                                       shape=(I.size, uniq.size))
                y = spsolve((Pm.T @ Kc @ Pm).tocsc(), Pm.T @ fc)
                uI = Pm @ y
            else:
                uI = spsolve(Kc.tocsc(), fc)
            u = uc.copy(); u[I] = uI
            return u, float((K @ u)[d_sig].sum())          # Q/eps0 on the signal

        def contour_int(u):
            tot = 0.0
            for fac, side, nrm in self.contour_groups(self.on_contour):
                fb = InteriorFacetBasis(mesh, ElementTriP1(), facets=fac, side=side)
                tot += dVdn2.assemble(fb, gu=fb.interpolate(u), nx=nrm[0][:, None], ny=nrm[1][:, None])
            return tot

        ex, ey = self.eps[0], self.eps[1]
        one = np.ones(mesh.nelements)
        out = {}
        V_eps, S_eps = solve_static(ex, ey, False)
        out["C"] = EPS0 * S_eps
        out["G"] = float(joule.assemble(bq, gu=bq.interpolate(V_eps), s=b0.interpolate(self.sigma)))
        for tag, fl in (("gnd", False), ("float", True)):
            if fl and not fingers:
                out["Cair_float"], out["R_float"] = out["Cair_gnd"], out["R_gnd"]
                continue
            V_air, S_air = solve_static(one, one, fl)
            out[f"Cair_{tag}"] = EPS0 * S_air
            out[f"R_{tag}"] = Rs_au * 1e6 * contour_int(V_air) / S_air ** 2
        out["ndof_qs"] = bq.N
        return out

    # ------------------------------------------------------------ full wave (cells [2]-[4])
    def full_wave(self, n_guess, num_modes=10):
        """PEC eigenmode + IBC correction, the notebook's n_m, Z0_IBC, alpha (dB/cm)."""
        mesh = self.mesh
        UM = 1e-6
        k0 = 2.0 * np.pi / (C0 / f0 * 1e6)
        omega = OMEGA
        b0 = Basis(mesh, ElementTriP0())
        el = ElementTriN1() * ElementTriP1()
        brf = b0.with_element(el)
        beps = brf.with_element(ElementTriP0())
        ex, ey, ez = self.eps

        @BilinearForm(dtype=complex)
        def aform(e_t, e_z, v_t, v_z, w):
            return (curl(e_t) * curl(v_t) / k0 ** 2
                    - (w.exx * e_t[0] * v_t[0] + w.eyy * e_t[1] * v_t[1])
                    + dot(grad(e_z), v_t)
                    + (w.exx * e_t[0] * grad(v_z)[0] + w.eyy * e_t[1] * grad(v_z)[1])
                    - w.ezz * e_z * v_z * k0 ** 2)

        @BilinearForm(dtype=complex)
        def bform(e_t, e_z, v_t, v_z, w):
            return -dot(e_t, v_t) / k0 ** 2

        A = aform.assemble(brf, exx=beps.interpolate(ex), eyy=beps.interpolate(ey), ezz=beps.interpolate(ez))
        B = bform.assemble(brf)
        dofs_metal = np.unique(brf.element_dofs[:, np.where(self.is_metal)[0]])
        dofs_outer = brf.get_dofs(facets=mesh.boundary_facets()).flatten()
        dofs_pec = np.unique(np.concatenate([dofs_metal, dofs_outer]))
        lams, xs = solve(*condense(-A, -B, D=dofs_pec, x=brf.zeros(dtype=complex)),
                         solver=solver_eigen_scipy(k=num_modes, sigma=k0 ** 2 * n_guess ** 2))
        idx_t, idx_z = brf.split_indices()
        xs_raw = xs.copy()
        xs[idx_z, :] /= 1j * np.sqrt(lams[np.newaxis, :] / k0 ** 4)
        betas = np.sqrt(lams.astype(complex))
        neffs = betas / k0

        is_z = np.zeros(brf.N, bool); is_z[idx_z] = True
        dz = lambda m: (lambda d: d[is_z[d]])(np.unique(brf.element_dofs[:, np.where(m)[0]]))
        dofs_sig_z = dz(self.is_signal)
        dofs_gnd_z = dz(self.is_metal & ~self.is_signal)

        @Functional(dtype=complex)
        def f_poynting(w):
            Hx = (w.ez.grad[1] / UM - 1j * w.beta * w.et[1]) / (-1j * omega * MU0)
            Hy = (1j * w.beta * w.et[0] - w.ez.grad[0] / UM) / (-1j * omega * MU0)
            return 0.5 * np.real(w.et[0] * np.conj(Hy) - w.et[1] * np.conj(Hx)) * UM ** 2

        @Functional(dtype=complex)
        def f_dielectric(w):
            return 0.5 * w.sig * (np.abs(w.et[0]) ** 2 + np.abs(w.et[1]) ** 2 + np.abs(w.ez) ** 2) * UM ** 2

        @Functional(dtype=complex)
        def f_Js2(w):
            dEz_dn = (w.ez.grad[0] * w.nx + w.ez.grad[1] * w.ny) / UM
            E_n = w.et[0] * w.nx + w.et[1] * w.ny
            Jz = (-dEz_dn + 1j * w.beta * E_n) / (-1j * omega * MU0)
            Hz = (w.et.curl / UM) / (-1j * omega * MU0)
            return (np.abs(Jz) ** 2 + np.abs(Hz) ** 2) * UM

        groups = self.contour_groups(self.on_contour)

        def contour_mode(form, x, beta_m):
            tot = 0.0 + 0j
            for fac, side, nrm in groups:
                fb = InteriorFacetBasis(mesh, el, facets=fac, side=side)
                f = fb.interpolate(x)
                tot += form.assemble(fb, et=f[0], ez=f[1], nx=nrm[0][:, None], ny=nrm[1][:, None], beta=beta_m)
            return tot

        xpath = np.linspace(-self.x_gi, -self.x_sig, 801)
        probe = brf.split(np.zeros(brf.N))[0][1].probes(
            np.vstack([xpath, np.full_like(xpath, self.slab_h + (self.y_el - self.slab_h) / 2.0)]))

        rows = []
        for i in range(len(lams)):
            beta_m = betas[i] * 1e6
            if abs(beta_m) < 1e-9:
                continue
            x, xr = xs[:, i], xs_raw[:, i]
            fl = brf.interpolate(x)
            P = abs(float(np.real(f_poynting.assemble(brf, et=fl[0], ez=fl[1], beta=beta_m))))
            if P < 1e-30:
                continue
            res = A @ xr
            Q_sig = EPS0 * abs(res[dofs_sig_z].sum()) * 1e-6
            Q_gnd = EPS0 * abs(res[dofs_gnd_z].sum()) * 1e-6
            I_sig = omega / abs(beta_m) * Q_sig
            I_gnd = omega / abs(beta_m) * Q_gnd
            Ex = np.asarray(probe @ x[idx_t]).reshape(2, -1)[0]
            V_gap = abs(np.trapezoid(Ex, xpath) * UM)
            Z_PI = 2.0 * P / I_sig ** 2 if I_sig > 0 else np.inf
            Z_VP = V_gap ** 2 / (2.0 * P)
            score = I_sig / (I_sig + I_gnd) if (I_sig + I_gnd) > 0 else np.nan
            div = abs(Z_PI - Z_VP) / max(0.5 * (Z_PI + Z_VP), 1e-30)
            rows.append(dict(index=i, neff=complex(neffs[i]), P=P, I_sig=I_sig, Z_PI=Z_PI,
                             Z_VP=Z_VP, score=score, div=div, beta_m=beta_m))
        F1 = [r for r in rows if 0.0 < r["Z_PI"] < 150.0]
        F2 = [r for r in F1 if 0.45 <= r["score"] <= 0.55]
        F3 = sorted(F2, key=lambda r: r["div"])
        if not F3:
            raise RuntimeError("no quasi-TEM CPW mode survived the filters")
        fm = F3[0]
        x_sel = xs[:, fm["index"]]
        fl = brf.interpolate(x_sel)
        J2 = float(np.real(contour_mode(f_Js2, x_sel, fm["beta_m"])))
        P_diel = float(np.real(f_dielectric.assemble(brf, et=fl[0], ez=fl[1], sig=beps.interpolate(self.sigma))))
        R_prime = Rs_au * J2 / fm["I_sig"] ** 2
        n_pec, Z_pec = fm["neff"].real, fm["Z_PI"]
        L_ext = Z_pec * n_pec / C0
        kappa = np.sqrt(1.0 + R_prime / omega / L_ext)
        n_m, Z0 = n_pec * kappa, Z_pec * kappa
        alpha_np = R_prime / (2.0 * Z0) + P_diel / (2.0 * fm["P"])
        return dict(n=n_m, Z0=Z0, alpha_dB_cm=DB_PER_NEPER * alpha_np / 100.0, R=R_prime,
                    n_pec=n_pec, Z_pec=Z_pec, div=fm["div"], score=fm["score"], ndof_rf=brf.N)


def qs_lines(qs, finger="gnd"):
    """Per-unit-length L, C, R, G of a section from the quasi-static solve.
    L includes the IBC internal inductance R'/omega (notebook cell [4]).
    finger='gnd': the finger carries current (standalone uniform line);
    finger='float': the finger carries no net current (cantilever)."""
    Cair, R = qs[f"Cair_{finger}"], qs[f"R_{finger}"]
    L = 1.0 / (C0 ** 2 * Cair) + R / OMEGA
    return dict(L=L, C=qs["C"], R=R, G=qs["G"])


def line_fom(L, C, R, G):
    """n_m, Z0, alpha [dB/cm] of a uniform line with these per-length values."""
    Z = np.sqrt(L / C)
    a = R / (2 * Z) + G * Z / 2
    return C0 * np.sqrt(L * C), Z, DB_PER_NEPER * a / 100.0
