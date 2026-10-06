"""
Full-wave check with the gold meshed as a conductor (no IBC, no quasi-static
assumption): the vector eigensolver of the user's notebook (same weak form,
same N1 x P1 elements), with the gold given eps = 1 - j sigma/(w eps0) and its
interior meshed down to a tenth of the skin depth. The complex n_eff gives the
total attenuation directly.

Geometry: the bend cross-section of bend_fem.py (Au 2 um: signal 35, gap 4.15,
ground 50 um; 3.6 um SiO2 / 0.275 um LN / 4.7 um SiO2 / 550 um Si, air above),
same outer box (200 um lateral padding, 550 um air, PEC walls). Half domain:
x = 0 is a magnetic wall (natural boundary), which is exact for the CPW mode.
Tensor-product mesh, graded at every metal surface.
"""
import json
import sys
import time

import numpy as np
from skfem import Basis, BilinearForm, ElementTriN1, ElementTriP0, ElementTriP1, MeshTri, condense, solve
from skfem.helpers import curl, dot, grad
from skfem.utils import solver_eigen_scipy

import eddy_tensor as ET

C0 = 299792458.0
EPS0 = 8.8541878128e-12
SIGMA_AU = 4.56e7


def build(sig_w=35.0, gap=4.15, gnd_w=50.0, t=2.0, buf=3.6, slab=0.275, box=4.7, si=550.0,
          air=550.0, pad=200.0, hfine=0.03, hmax_metal=0.4, hmax_far=30.0, r=1.15):
    xs, xgi = sig_w / 2, sig_w / 2 + gap
    xgo = xgi + gnd_w
    xd = xgo + pad
    y_buf, y_ln, y_box, y_si = -buf, -buf - slab, -buf - slab - box, -buf - slab - box - si
    x = ET.axis([0.0, xs, xgi, xgo, xd], hfine, hmax_metal, hmax_far, [(0, xs), (xgi, xgo)], r)
    # dielectric interfaces only need moderate grading
    yb = [y_si, y_box, y_ln, y_buf, 0.0, t, t + air]
    y = ET.axis(yb, hfine, hmax_metal, hmax_far, [(0.0, t)], r)
    x, y = (np.unique(np.round(v, 9)) for v in (x, y))
    x, y = (v[np.concatenate([[True], np.diff(v) > 1e-6])] for v in (x, y))   # no sliver cells
    mesh = MeshTri.init_tensor(x, y)
    cx, cy = mesh.p[:, mesh.t].mean(axis=1)
    in_t = (cy > 0) & (cy < t)
    metal = np.where(in_t & (cx < xs), 1, np.where(in_t & (cx > xgi) & (cx < xgo), 2, 0))
    mat = np.full(mesh.nelements, "air", dtype=object)
    mat[(cy < 0) & (cy > y_buf)] = "SiO2"
    mat[(cy < y_buf) & (cy > y_ln)] = "LN"
    mat[(cy < y_ln) & (cy > y_box)] = "SiO2"
    mat[cy < y_box] = "Si"
    mat[metal > 0] = "Au"
    return mesh, metal, mat


def run(f0=60e9, n_guess=1.70, num_modes=6, sigma=SIGMA_AU, **geom):
    t0 = time.time()
    mesh, metal, mat = build(**geom)
    omega = 2 * np.pi * f0
    eps_au = 1.0 - 1j * sigma / (omega * EPS0)
    table = {"air": (1, 1, 1), "SiO2": (3.9, 3.9, 3.9), "LN": (28.0, 44.0, 44.0),
             "Si": (11.7, 11.7, 11.7), "Au": (eps_au, eps_au, eps_au)}
    ex = np.array([table[m][0] for m in mat], dtype=complex)
    ey = np.array([table[m][1] for m in mat], dtype=complex)
    ez = np.array([table[m][2] for m in mat], dtype=complex)
    wl = C0 / f0 * 1e6
    k0 = 2 * np.pi / wl
    el = ElementTriN1() * ElementTriP1()
    basis = Basis(mesh, el)
    b0 = basis.with_element(ElementTriP0())

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

    A = aform.assemble(basis, exx=b0.interpolate(ex), eyy=b0.interpolate(ey), ezz=b0.interpolate(ez))
    B = bform.assemble(basis)
    xmax, ymin, ymax = mesh.p[0].max(), mesh.p[1].min(), mesh.p[1].max()
    pec = basis.get_dofs(lambda X: (np.abs(X[0] - xmax) < 1e-9) | (np.abs(X[1] - ymin) < 1e-9)
                         | (np.abs(X[1] - ymax) < 1e-9)).flatten()
    lams, xs = solve(*condense(-A, -B, D=pec, x=basis.zeros(dtype=complex)),
                     solver=solver_eigen_scipy(k=num_modes, sigma=k0 ** 2 * n_guess ** 2))
    idx_t, idx_z = basis.split_indices()
    neff = np.sqrt(lams.astype(complex)) / k0
    # conduction current in each electrode: I = int sigma E_z dA (E_z up to the
    # femwell scaling j beta / k0^2, common to both electrodes)
    bz = basis.with_element(ElementTriP1())
    rows = []
    for i in range(len(lams)):
        ezf = bz.interpolate(xs[idx_z, i])
        cur = []
        for k in (1, 2):
            from skfem import Functional

            @Functional(dtype=complex)
            def fI(w):
                return w.s * w.e

            cur.append(complex(fI.assemble(bz, e=ezf, s=b0.interpolate((metal == k) * sigma))))
        Is, Ig = cur
        score = abs(Is) / (abs(Is) + abs(Ig)) if abs(Is) + abs(Ig) > 0 else np.nan
        n = neff[i]
        if n.real < 0:
            n = -n
        alpha = abs(n.imag) * k0 * 1e6                     # Np/m
        rows.append(dict(n_re=n.real, n_im=n.imag, alpha_dB_cm=alpha * 20 / np.log(10) / 100,
                         score=score, Is_over_Ig=abs(Is / Ig) if abs(Ig) > 0 else np.inf))
    info = dict(n_el=mesh.nelements, ndof=basis.N, t_s=time.time() - t0, f_GHz=f0 / 1e9,
                hfine=geom.get("hfine", 0.03))
    return rows, info


if __name__ == "__main__":
    hf = float(sys.argv[1]) if len(sys.argv) > 1 else 0.03
    f = float(sys.argv[2]) * 1e9 if len(sys.argv) > 2 else 60e9
    rows, info = run(f0=f, hfine=hf)
    print(info)
    for r in rows:
        print({k: round(float(v), 6) for k, v in r.items()})
    with open("results/fullwave_metal.jsonl", "a") as fh:
        fh.write(json.dumps(dict(info=info, modes=rows), default=float) + "\n")
