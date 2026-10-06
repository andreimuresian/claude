"""
Corner constants for BOTH parts of the internal impedance, with the receded-
wall convention used by the line model (cpw_analytic / mzm_interconnect.bend_cpw):

    R_int      = Rs ( G(a - delta) - c_R Ks delta^(1/3) )
    w L_int    = Rs ( G(a - delta) - c_X Ks delta^(1/3) )

G(a - delta): PEC geometric factor of the bar receded by delta/2 on every face;
Ks = sum over the corners of K^2 (J/I = K r^-1/3 next to a corner).
Canonical problem, not the CPW: an isolated square gold bar of side a with its
return on a far box. L_int = L_total - L_ext, both in the same mesh and box
(L_ext: PEC bar, A pinned on the metal), so the box cancels.
"""
import json

import numpy as np
from skfem import Basis, BilinearForm, ElementTriP2, MeshTri, asm, condense, solve
from skfem.helpers import dot, grad

import eddy_tensor as ET
from corner_constant import bem_isolated_square

MU0, SIG = ET.MU0, ET.SIGMA_AU


def bar(a, f_list, hfine, box=60.0):
    h = a / 2
    x = ET.axis([0.0, h * 1e6, box * h * 1e6], hfine, 0.25 * h * 1e6, 0.5 * box * h * 1e6, [(0, h * 1e6)], 1.12)
    mesh = MeshTri.init_tensor(x * 1e-6, x * 1e-6)
    c = mesh.p[:, mesh.t].mean(axis=1)
    cond = ((c[0] < h) & (c[1] < h)).astype(int)
    xm = mesh.p.max()
    far = lambda X: (np.abs(X[0] - xm) < 1e-15) | (np.abs(X[1] - xm) < 1e-15)
    Vs, info = ET.solve_on_mesh(mesh, cond, [0.25], far, f_list)
    Z = np.array([-V[0] for V in Vs])
    # PEC bar in the same box: A = 1 on the metal, 0 on the box
    basis = Basis(mesh, ElementTriP2())

    @BilinearForm
    def stiff(u, v, w):
        return dot(grad(u), grad(v)) / MU0
    K = asm(stiff, basis)
    d_m = np.unique(basis.element_dofs[:, cond == 1])
    D = np.unique(np.concatenate([basis.get_dofs(far).flatten(), d_m]))
    u = np.zeros(basis.N); u[d_m] = 1.0
    Kc, fc, uc, I = condense(K, np.zeros(basis.N), x=u, D=D)
    uu = uc.copy(); uu[I] = solve(Kc, fc)
    I_q = float((K @ uu)[d_m].sum())
    L_ext = 1.0 / (4 * I_q)
    return Z, L_ext, info


if __name__ == "__main__":
    a = 10e-6
    f = np.array([20e9, 50e9, 100e9, 200e9, 400e9, 800e9])
    _G, K0 = bem_isolated_square(a)
    out = []
    for hf in (0.02, 0.01):
        Z, L_ext, info = bar(a, f, hf)
        w = 2 * np.pi * f
        print("hfine", hf, info, "L_ext", L_ext)
        rows = []
        for fi, wi, zi in zip(f, w, Z):
            delta = 1 / np.sqrt(np.pi * fi * MU0 * SIG)
            Rs = 1 / (SIG * delta)
            G, K = bem_isolated_square(a - delta)
            Ks = 4 * K * K
            X_int = zi.imag - wi * L_ext
            cR = (G - zi.real / Rs) / (Ks * delta ** (1 / 3))
            cX = (G - X_int / Rs) / (Ks * delta ** (1 / 3))
            print(f"   {fi/1e9:5.0f} GHz  delta/a {delta/a:.4f}  R {zi.real:9.3f}  X_int {X_int:9.3f}  "
                  f"Rs G_rec {Rs*G:9.3f}   c_R {cR:.4f}   c_X {cX:.4f}")
            rows.append(dict(f=fi, R=zi.real, X_int=X_int, G_rec=G, Ks=Ks, c_R=cR, c_X=cX))
        out.append(dict(hfine=hf, L_ext=L_ext, rows=rows))
    json.dump(out, open("results/corner_reactance.json", "w"), indent=1)
