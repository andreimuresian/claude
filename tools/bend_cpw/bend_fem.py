"""
2D RF cross-section of the electrode BEND, adapted from the user's validated
notebook (unetched_nmZ0_aRF_Claude.ipynb: femwell/scikit-fem, anisotropic
quasi-static + vector eigensolve, PEC electrodes with first-order IBC loss and
internal inductance, the COMSOL three-filter mode pick).

What changed relative to the notebook (modulation section) -- geometry only:
  * a 3.6 um SiO2 buffer between the electrodes and the LN slab
  * the LN slab is 0.275 um, un-etched, no ribs, no SiO2 caps
  * electrodes: signal 35, gaps 4.15, grounds 50, thickness 2 (um)
  * y = 0 is the electrode bottom (top of the buffer)
The materials, the solver, the loss and the impedance definitions are the
notebook's, copied verbatim where possible.
"""
import time
import warnings
from collections import OrderedDict

import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union
from skfem import (Basis, BilinearForm, ElementTriN1, ElementTriP0, ElementTriP1,
                   Functional, InteriorFacetBasis, MeshTri, asm, condense, solve)
from skfem.helpers import curl, dot, grad
from skfem.utils import solver_eigen_scipy
from femwell.mesh import mesh_from_OrderedDict

warnings.filterwarnings("ignore")

C0 = 299792458.0
EPS0 = 8.8541878128e-12
MU0 = 4.0e-7 * np.pi
DB_PER_NEPER = 20.0 * np.log10(np.e)
UM = 1e-6

BEND = dict(sig_w=35.0, gap=4.15, gnd_w=50.0, au_h=2.0, buf_h=3.6, slab_h=0.275,
            box_h=4.7, si_h=550.0, air_h=550.0, lat_pad=200.0)

SIGMA_AU = 4.56e7
MATERIALS = {
    "LN":   {"eps_rf": (28.0, 44.0, 44.0), "sigma": 1e-3},
    "SiO2": {"eps_rf": (3.9, 3.9, 3.9),    "sigma": 1e-13},
    "Si":   {"eps_rf": (11.7, 11.7, 11.7), "sigma": 1e-12},
    "air":  {"eps_rf": (1.0, 1.0, 1.0),    "sigma": 0.0},
    "Au":   {"eps_rf": (1.0, 1.0, 1.0),    "sigma": 0.0},
}
REGION_TO_MAT = {
    "corner_ring": "air", "skin_ring": "air",
    "buf_near": "SiO2", "buf_far": "SiO2",
    "slab_near": "LN", "slab_far": "LN",
    "box_near": "SiO2", "box_far": "SiO2",
    "si": "Si",
    "air_gap": "air", "air_near": "air", "air_far": "air",
    "el_sig": "Au", "el_gr": "Au", "el_gl": "Au",
}
METAL_REGIONS = ("el_sig", "el_gr", "el_gl")

MESH = dict(MESH_FACTOR=1.0, COLLAR_W=4.0, COLLAR_H=4.0, CORNER_BOX=0.25, CORNER_RES=0.050,
            SKIN_T=0.10, SKIN_REACH=5.0, SKIN_RES=0.100)


def build(g, m):
    x_sig = g["sig_w"] / 2.0
    x_gi = x_sig + g["gap"]
    x_go = x_gi + g["gnd_w"]
    x_dom = x_go + g["lat_pad"]
    y_el = g["au_h"]
    y_buf = -g["buf_h"]
    y_slab = y_buf - g["slab_h"]
    y_box = y_slab - g["box_h"]
    y_si = y_box - g["si_h"]
    CB, ST, SR = m["CORNER_BOX"], m["SKIN_T"], m["SKIN_REACH"]

    el_sig = box(-x_sig, 0.0, x_sig, y_el)
    el_gr = box(x_gi, 0.0, x_go, y_el)
    el_gl = box(-x_go, 0.0, -x_gi, y_el)
    solids = unary_union([el_sig, el_gr, el_gl])

    corners = [box(xc - CB, yc - CB, xc + CB, yc + CB)
               for xc in (-x_sig, x_sig, -x_gi, x_gi, -x_go, x_go) for yc in (0.0, y_el)]
    corner_ring = unary_union(corners).difference(solids)
    walls = []
    for xa, xb in ((x_sig, x_sig + ST), (-x_sig - ST, -x_sig),
                   (x_gi - ST, x_gi), (-x_gi, -x_gi + ST)):
        walls.append(box(xa, 0.0, xb, y_el))
    for xc in (-x_sig, x_sig, -x_gi, x_gi):
        lo, hi = (xc, xc + SR) if xc > 0 else (xc - SR, xc)
        walls.append(box(lo, y_el, hi, y_el + ST))
        walls.append(box(lo, -ST, hi, 0.0))
    skin_ring = unary_union(walls).difference(unary_union([solids, corner_ring]))
    fine = unary_union([solids, corner_ring, skin_ring])

    air_gap = box(-x_gi - m["COLLAR_W"], 0.0, x_gi + m["COLLAR_W"],
                  y_el + m["COLLAR_H"]).difference(fine)
    air_near = box(-x_go - 15.0, 0.0, x_go + 15.0, y_el + 15.0).difference(
        unary_union([fine, air_gap]))
    air_far = box(-x_dom, 0.0, x_dom, g["air_h"]).difference(
        unary_union([fine, air_gap, air_near]))
    buf_near = box(-x_go - 15.0, y_buf, x_go + 15.0, 0.0).difference(unary_union([corner_ring, skin_ring]))
    buf_far = box(-x_dom, y_buf, x_dom, 0.0).difference(box(-x_go - 15.0, y_buf, x_go + 15.0, 0.0))
    slab_near = box(-x_go - 15.0, y_slab, x_go + 15.0, y_buf)
    slab_far = box(-x_dom, y_slab, x_dom, y_buf).difference(slab_near)
    box_near = box(-x_go - 15.0, y_box, x_go + 15.0, y_slab)
    box_far = box(-x_dom, y_box, x_dom, y_slab).difference(box_near)
    si = box(-x_dom, y_si, x_dom, y_box)

    polys = OrderedDict()
    for k, v in [("corner_ring", corner_ring), ("skin_ring", skin_ring),
                 ("el_sig", el_sig), ("el_gr", el_gr), ("el_gl", el_gl),
                 ("air_gap", air_gap), ("buf_near", buf_near), ("slab_near", slab_near),
                 ("air_near", air_near), ("box_near", box_near), ("buf_far", buf_far),
                 ("slab_far", slab_far), ("box_far", box_far), ("si", si), ("air_far", air_far)]:
        polys[k] = v
    lm = dict(x_sig=x_sig, x_gi=x_gi, x_go=x_go, x_dom=x_dom, y_el=y_el, y_buf=y_buf,
              y_slab=y_slab, y_box=y_box)
    return polys, lm


def make_mesh(g, m):
    polys, lm = build(g, m)
    mf = m["MESH_FACTOR"]
    base_res = {"corner_ring": m["CORNER_RES"], "skin_ring": m["SKIN_RES"],
                "air_gap": 0.30 * mf, "buf_near": 0.30 * mf, "slab_near": 0.25 * mf,
                "box_near": 2.0 * mf, "el_sig": 0.80 * mf, "el_gr": 0.80 * mf,
                "el_gl": 0.80 * mf, "air_near": 2.0 * mf, "buf_far": 6.0 * mf,
                "slab_far": 6.0 * mf, "box_far": 6.0 * mf, "si": 30.0 * mf, "air_far": 30.0 * mf}
    base_dist = {"corner_ring": 0.6, "skin_ring": 1.0, "air_gap": 3.0, "buf_near": 3.0,
                 "slab_near": 3.0, "box_near": 5.0, "el_sig": 3.0, "el_gr": 3.0, "el_gl": 3.0,
                 "air_near": 10.0, "buf_far": 10.0, "slab_far": 10.0, "box_far": 10.0,
                 "si": 30.0, "air_far": 30.0}
    res = {k: {"resolution": base_res[k], "distance": base_dist[k]} for k in polys}
    raw = mesh_from_OrderedDict(polys, resolutions=res,
                                default_resolution_min=0.4 * min(m["CORNER_RES"], m["SKIN_RES"]),
                                default_resolution_max=35.0)
    mesh = MeshTri(raw.points[:, :2].T, raw.cells_dict["triangle"].T)
    sub = raw.cell_data_dict["gmsh:physical"]["triangle"]
    name_to_id = {n: (d[0] if hasattr(d, "__getitem__") else d) for n, d in raw.field_data.items()}
    region_of = np.empty(mesh.nelements, dtype=object)
    for raw_name, s_id in name_to_id.items():
        b = raw_name.split("___")[0]
        if b in polys:
            region_of[sub == s_id] = b
    assert not any(r is None for r in region_of), "untagged elements"
    mat = np.array([REGION_TO_MAT[r] for r in region_of], dtype=object)
    coll = np.isin(region_of.astype(str), ("corner_ring", "skin_ring"))
    yc = mesh.p[1, mesh.t].mean(axis=0)
    mat[coll] = np.where(yc < 0.0, "SiO2", "air")[coll]     # buffer below, air above
    return mesh, region_of, mat, lm


def run(f0=60e9, geom=None, mesh_opts=None, materials=None, num_modes=12, verbose=False,
        qs_only=False):
    g = dict(BEND, **(geom or {}))
    m = dict(MESH, **(mesh_opts or {}))
    mats = {k: dict(v) for k, v in MATERIALS.items()}
    for k, v in (materials or {}).items():
        mats[k].update(v)
    t0 = time.time()
    mesh, region_of, mat_of_el, lm = make_mesh(g, m)
    is_metal = np.isin(region_of.astype(str), METAL_REGIONS)
    is_signal = region_of.astype(str) == "el_sig"
    f2t = mesh.f2t
    has_two = f2t[1] >= 0
    on_c = has_two & (is_metal[f2t[0]] ^ is_metal[np.where(has_two, f2t[1], 0)])
    on_c &= has_two
    metal_side = np.where(is_metal[f2t[0]], f2t[0], f2t[1])

    def groups(mask):
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
            mid = p.mean(axis=1)
            cen = mesh.p[:, mesh.t[:, f2t[other][fac]]].mean(axis=1)
            nrm *= np.sign(((mid - cen) * nrm).sum(axis=0))
            out.append((fac, side, nrm))
        return out

    CONTOUR = {"sig": groups(on_c & is_signal[metal_side]),
               "all": groups(on_c)}
    skin = np.sqrt(2.0 / (2 * np.pi * f0 * MU0 * SIGMA_AU))
    Rs = 1.0 / (SIGMA_AU * skin)

    # ---- quasi-static (cell 1) --------------------------------------------
    basis_qs = Basis(mesh, ElementTriP1())
    basis_p0 = Basis(mesh, ElementTriP0())
    eps_x = np.array([mats[q]["eps_rf"][0] for q in mat_of_el], float)
    eps_y = np.array([mats[q]["eps_rf"][1] for q in mat_of_el], float)
    eps_z = np.array([mats[q]["eps_rf"][2] for q in mat_of_el], float)
    sigma = np.array([mats[q]["sigma"] for q in mat_of_el], float)
    ones = np.ones(mesh.nelements)

    @BilinearForm
    def lap(u, v, w):
        return w.ex * grad(u)[0] * grad(v)[0] + w.ey * grad(u)[1] * grad(v)[1]

    d_sig = np.unique(basis_qs.element_dofs[:, np.where(is_signal)[0]])
    d_gnd = np.unique(basis_qs.element_dofs[:, np.where(is_metal & ~is_signal)[0]])
    d_D = np.unique(np.concatenate([d_sig, d_gnd]))

    def static(ex, ey):
        K = asm(lap, basis_qs, ex=basis_p0.interpolate(ex), ey=basis_p0.interpolate(ey))
        uD = np.zeros(basis_qs.N)
        uD[d_sig] = 1.0
        Kc, fc, uc, I = condense(K, np.zeros(basis_qs.N), x=uD, D=d_D)
        u = uc.copy()
        u[I] = solve(Kc, fc)
        return u, EPS0 * float((K @ u)[d_sig].sum())

    V_eps, C_eps = static(eps_x, eps_y)
    V_air, C_air = static(ones, ones)
    n_qs = np.sqrt(C_eps / C_air)
    Z_qs = 1.0 / (C0 * np.sqrt(C_eps * C_air))

    @Functional
    def dVdn2(w):
        return (w.gu.grad[0] * w.nx + w.gu.grad[1] * w.ny) ** 2

    def cstat(key, field):
        tot = 0.0
        for fac, side, nrm in CONTOUR[key]:
            fb = InteriorFacetBasis(mesh, ElementTriP1(), facets=fac, side=side)
            tot += dVdn2.assemble(fb, gu=fb.interpolate(field), nx=nrm[0][:, None], ny=nrm[1][:, None])
        return tot

    S_charge = C_air / EPS0
    R_qs = Rs * 1e6 * cstat("all", V_air) / S_charge ** 2
    a_qs = DB_PER_NEPER * R_qs / (2 * Z_qs) / 100.0
    if qs_only:
        return dict(f_GHz=f0 / 1e9, n_qs=n_qs, Z_qs=Z_qs, C_eps=C_eps, C_air=C_air, R_qs=R_qs,
                    alpha_qs_dB_cm=a_qs, n_el=mesh.nelements, t_s=time.time() - t0)

    # ---- vector eigensolve (cell 2) ----------------------------------------
    wl = C0 / f0 * 1e6
    k0 = 2 * np.pi / wl
    omega = 2 * np.pi * f0
    el_rf = ElementTriN1() * ElementTriP1()
    basis_rf = basis_p0.with_element(el_rf)
    basis_eps = basis_rf.with_element(ElementTriP0())

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

    A = aform.assemble(basis_rf, exx=basis_eps.interpolate(eps_x),
                       eyy=basis_eps.interpolate(eps_y), ezz=basis_eps.interpolate(eps_z))
    B = bform.assemble(basis_rf)
    d_metal = np.unique(basis_rf.element_dofs[:, np.where(is_metal)[0]])
    d_outer = basis_rf.get_dofs(facets=mesh.boundary_facets()).flatten()
    d_pec = np.unique(np.concatenate([d_metal, d_outer]))
    lams, xs = solve(*condense(-A, -B, D=d_pec, x=basis_rf.zeros(dtype=complex)),
                     solver=solver_eigen_scipy(k=num_modes, sigma=k0 ** 2 * n_qs ** 2))
    idx_t, idx_z = basis_rf.split_indices()
    xs[idx_z, :] /= 1j * np.sqrt(lams[np.newaxis, :] / k0 ** 4)
    betas = np.sqrt(lams.astype(complex))
    neffs = betas / k0

    # ---- diagnostics and filters (cell 3) ----------------------------------
    xs_raw = xs.copy()
    xs_raw[idx_z, :] *= 1j * np.sqrt(lams[np.newaxis, :] / k0 ** 4)
    is_z = np.zeros(basis_rf.N, bool)
    is_z[idx_z] = True
    dsz = np.unique(basis_rf.element_dofs[:, np.where(is_signal)[0]])
    dsz = dsz[is_z[dsz]]
    dgz = np.unique(basis_rf.element_dofs[:, np.where(is_metal & ~is_signal)[0]])
    dgz = dgz[is_z[dgz]]

    @Functional(dtype=complex)
    def f_poy(w):
        Hx = (w.ez.grad[1] / UM - 1j * w.beta * w.et[1]) / (-1j * omega * MU0)
        Hy = (1j * w.beta * w.et[0] - w.ez.grad[0] / UM) / (-1j * omega * MU0)
        return 0.5 * np.real(w.et[0] * np.conj(Hy) - w.et[1] * np.conj(Hx)) * UM ** 2

    @Functional(dtype=complex)
    def f_diel(w):
        return 0.5 * w.sig * (np.abs(w.et[0]) ** 2 + np.abs(w.et[1]) ** 2 + np.abs(w.ez) ** 2) * UM ** 2

    @Functional(dtype=complex)
    def f_Js2(w):
        dEz = (w.ez.grad[0] * w.nx + w.ez.grad[1] * w.ny) / UM
        En = w.et[0] * w.nx + w.et[1] * w.ny
        Jz = (-dEz + 1j * w.beta * En) / (-1j * omega * MU0)
        Hz = (w.et.curl / UM) / (-1j * omega * MU0)
        return (np.abs(Jz) ** 2 + np.abs(Hz) ** 2) * UM

    @Functional(dtype=complex)
    def f_Jsz(w):
        dEz = (w.ez.grad[0] * w.nx + w.ez.grad[1] * w.ny) / UM
        En = w.et[0] * w.nx + w.et[1] * w.ny
        return (-dEz + 1j * w.beta * En) / (-1j * omega * MU0) * UM

    def cmode(form, key, x, beta_m):
        tot = 0.0 + 0j
        for fac, side, nrm in CONTOUR[key]:
            fb = InteriorFacetBasis(mesh, el_rf, facets=fac, side=side)
            fl = fb.interpolate(x)
            tot += form.assemble(fb, et=fl[0], ez=fl[1], nx=nrm[0][:, None], ny=nrm[1][:, None], beta=beta_m)
        return tot

    xpath = np.linspace(-lm["x_gi"], -lm["x_sig"], 801)
    probe = basis_rf.split(np.zeros(basis_rf.N))[0][1].probes(
        np.vstack([xpath, np.full_like(xpath, g["au_h"] / 2.0)]))

    def vgap(x):
        Ex = np.asarray(probe @ x[idx_t]).reshape(2, -1)[0]
        return np.trapezoid(Ex, xpath) * UM

    rows = []
    for i in range(len(lams)):
        bm = betas[i] * 1e6
        if abs(bm) < 1e-9:
            continue
        x, xr = xs[:, i], xs_raw[:, i]
        fl = basis_rf.interpolate(x)
        P = abs(float(np.real(f_poy.assemble(basis_rf, et=fl[0], ez=fl[1], beta=bm))))
        if P < 1e-30:
            continue
        r_ = A @ xr
        Qs = EPS0 * abs(r_[dsz].sum()) * 1e-6
        Qg = EPS0 * abs(r_[dgz].sum()) * 1e-6
        Is = omega / abs(bm) * Qs
        Ig = omega / abs(bm) * Qg
        Vg = abs(vgap(x))
        ZPI = 2 * P / Is ** 2 if Is > 0 else np.inf
        ZVP = Vg ** 2 / (2 * P)
        sc = Is / (Is + Ig) if Is + Ig > 0 else np.nan
        dv = abs(ZPI - ZVP) / max(0.5 * (ZPI + ZVP), 1e-30)
        rows.append(dict(index=i, neff=complex(neffs[i]), P=P, I_sig=Is, I_gnd=Ig, V_gap=Vg,
                         Z_PI=ZPI, Z_VP=ZVP, score=sc, div=dv, beta_m=bm))
    F1 = [r for r in rows if 0 < r["Z_PI"] < 150]
    F2 = [r for r in F1 if 0.45 <= r["score"] <= 0.55]
    F3 = sorted(F2, key=lambda r: r["div"])
    if not F3:
        raise RuntimeError(f"no quasi-TEM mode at {f0/1e9} GHz: {[(r['neff'].real, r['Z_PI'], r['score']) for r in rows]}")
    fu = F3[0]

    # ---- figures of merit (cell 4) -----------------------------------------
    x_sel = xs[:, fu["index"]]
    fl = basis_rf.interpolate(x_sel)
    J2 = float(np.real(cmode(f_Js2, "all", x_sel, fu["beta_m"])))
    Pd = float(np.real(f_diel.assemble(basis_rf, et=fl[0], ez=fl[1], sig=basis_eps.interpolate(sigma))))
    G = J2 / fu["I_sig"] ** 2
    Rp = Rs * G
    n_pec = fu["neff"].real
    Z_pec = fu["Z_PI"]
    L_ext = Z_pec * n_pec / C0
    L_int = Rp / omega
    kap = np.sqrt(1 + L_int / L_ext)
    n_m = n_pec * kap
    Z0 = Z_pec * kap
    a_c = Rp / (2 * Z0)
    a_d = Pd / (2 * fu["P"])
    Idir = abs(cmode(f_Jsz, "sig", x_sel, fu["beta_m"]))
    out = dict(f_GHz=f0 / 1e9, n_m=n_m, Z0=Z0, Z_VP=fu["Z_VP"] * kap,
               alpha_c_dB_cm=DB_PER_NEPER * a_c / 100, alpha_d_dB_cm=DB_PER_NEPER * a_d / 100,
               alpha_dB_cm=DB_PER_NEPER * (a_c + a_d) / 100, R_per_m=Rp, L_ext=L_ext, L_int=L_int,
               n_pec=n_pec, Z_pec=Z_pec, n_qs=n_qs, Z_qs=Z_qs, alpha_qs_dB_cm=a_qs,
               C_eps=C_eps, C_air=C_air, score=fu["score"], div=fu["div"],
               I_ratio=Idir / fu["I_sig"], n_el=mesh.nelements, t_s=time.time() - t0,
               neff_im=fu["neff"].imag)
    if verbose:
        print({k: (round(v, 6) if isinstance(v, float) else v) for k, v in out.items()})
    return out


if __name__ == "__main__":
    import sys
    f = float(sys.argv[1]) * 1e9 if len(sys.argv) > 1 else 60e9
    run(f, verbose=True)
