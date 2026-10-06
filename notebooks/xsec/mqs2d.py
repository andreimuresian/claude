"""Conductor loss R' and internal inductance L_int from the current inside the gold.

Port of the author's notebook v2 (unetched_nmZ0_aRF_Claude_v2.ipynb), cell [6]:
same equations, same graded tensor mesh (`graded`, `axis` verbatim), same P2
elements, same half domain (x >= 0, A_z even in x, A_z = 0 on the far box):

    -div(grad A / mu0) + j w sigma A + sigma V'_k = 0     in conductor group k
    -div(grad A / mu0)                         = 0     outside
    int_k sigma (-j w A - V'_k) dS = I_k

    R' + j w L' = V'_gnd - V'_sig      (line current 1 A)

Generalised to the tee cross-sections: the ground is a list of pieces
(xsec2d.pieces_for), and the conductors form groups, each with its own V'_k and
net current I_k (half domain):

    finger = 'gnd'   : signal +1/2, ground pieces + finger -1/2   (one V')
    finger = 'float' : signal +1/2, ground pieces -1/2, finger 0  (its own V':
                       eddy current inside the finger, no net current along it)

External inductance of the same mesh and box, two ways:
    L_ext_box : the notebook's.  A = 1 on the signal, 0 on the ground AND on
                the box, so the box also returns current.
    L_ext     : A constant on every group (PEC) with the SAME net currents as
                the gold solve, so the box carries no net current, as in it.
L_int = L' - L_ext.  Lengths in um, results SI.
"""
import numpy as np
import scipy.sparse.linalg as spla
from skfem import (Basis, BilinearForm, ElementTriP0, ElementTriP2, LinearForm, MeshTri, asm,
                   condense, solve)
from skfem.helpers import grad

MU0 = 4.0e-7 * np.pi
UM = 1e-6
SIGMA_AU = 4.56e7
F0 = 60.0e9
HFINE, BOX, HMAX_METAL, HMAX_AIR, GROW = 0.03, 600.0, 0.5, 40.0, 1.15     # notebook cell [6]


def graded(a, b, ha, hb, hmax, r=GROW):
    L = b - a
    left, h = [0.0], ha
    while left[-1] < L / 2:
        left.append(left[-1] + h); h = min(h * r, hmax)
    right, h = [0.0], hb
    while right[-1] < L / 2:
        right.append(right[-1] + h); h = min(h * r, hmax)
    left, right = np.array(left), L - np.array(right)
    pts = np.unique(np.concatenate([[0.0, L], left[left < L / 2], right[right >= L / 2]]))
    keep = [pts[0]]
    for q in pts[1:]:
        if q - keep[-1] > 0.3 * min(ha, hb):
            keep.append(q)
    keep[-1] = L
    out = a + np.array(keep)
    out[-1] = b             # a + (b - a) can miss b by one ulp: np.unique then keeps both
    return out              # copies -> zero-width elements -> singular matrix (row 398 A)


def axis(breaks, hfine, hmax_metal, hmax_air, metal_spans, r=GROW):
    out = []
    for a, b in zip(breaks[:-1], breaks[1:]):
        inside = any(lo <= a and b <= hi for lo, hi in metal_spans)
        hmax = hmax_metal if inside else hmax_air
        ha = hfine if a != breaks[0] else hmax_air
        hb = hfine if b != breaks[-1] else hmax_air
        if a == 0.0 and breaks[0] == 0.0:       # x = 0 symmetry plane: no surface there
            ha = min(hmax, 0.5)
        out.append(graded(a, b, ha, hb, hmax, r))
    return np.unique(np.concatenate(out))


def section_mesh(WS, MTX, pieces, hfine=HFINE, box=BOX, hmax_metal=HMAX_METAL, grow=GROW):
    """Half-domain tensor mesh (m) and the conductor id per element:
    0 air, 1 signal, 2 + k ground piece k."""
    x_sig = WS / 2
    edges = {e for a, b, _ in pieces for e in (a, b)}
    xa = axis(sorted({0.0, x_sig, box} | edges), hfine, hmax_metal, HMAX_AIR,
              [(0.0, x_sig)] + [(a, b) for a, b, _ in pieces], grow)
    ya = axis([-box, 0.0, MTX, box], hfine, hmax_metal, HMAX_AIR, [(0.0, MTX)], grow)
    m = MeshTri.init_tensor(xa * UM, ya * UM)
    c = m.p[:, m.t].mean(axis=1) / UM
    inside = (c[1] > 0) & (c[1] < MTX)
    cond = np.zeros(m.nelements, int)
    cond[inside & (c[0] < x_sig)] = 1
    for k, (a, b, _) in enumerate(pieces):
        cond[inside & (c[0] > a) & (c[0] < b)] = 2 + k
    return m, cond


def groups_for(pieces, finger):
    """Conductor groups (lists of conductor ids) and their half-domain currents."""
    gnd = [2 + k for k, p in enumerate(pieces) if p[2] == "gnd"]
    fin = [2 + k for k, p in enumerate(pieces) if p[2] == "finger"]
    if fin and finger == "float":
        return [[1], gnd, fin], np.array([0.5, -0.5, 0.0])
    return [[1], gnd + fin], np.array([0.5, -0.5])


@BilinearForm
def _stiff(u, v, w):
    return (grad(u)[0] * grad(v)[0] + grad(u)[1] * grad(v)[1]) / MU0


@BilinearForm
def _mass(u, v, w):
    return w.s * u * v


@LinearForm
def _lf(v, w):
    return w.s * v


def solve_mqs(m, cond, groups, I, f=F0, sigma=SIGMA_AU, dirichlet=None):
    """Gold-interior solve.  Returns dict: R (ohm/m), L (H/m), L_ext, L_ext_box (H/m).
    `dirichlet(X)` selects the A = 0 boundary (default: the notebook's box sides)."""
    b2 = Basis(m, ElementTriP2())
    b0 = b2.with_element(ElementTriP0())
    K = asm(_stiff, b2)
    Ms = asm(_mass, b2, s=b0.interpolate(np.where(cond > 0, sigma, 0.0)))
    pp = m.p[:, m.t]
    area = 0.5 * np.abs((pp[0, 1] - pp[0, 0]) * (pp[1, 2] - pp[1, 0])
                        - (pp[0, 2] - pp[0, 0]) * (pp[1, 1] - pp[1, 0]))
    ing = [np.isin(cond, g) for g in groups]
    Bm = np.column_stack([asm(_lf, b2, s=b0.interpolate(g * sigma)) for g in ing])
    Gk = np.array([sigma * area[g].sum() for g in ing])
    if dirichlet is None:
        xm, ymn, ymx = m.p[0].max(), m.p[1].min(), m.p[1].max()
        dirichlet = lambda X: ((np.abs(X[0] - xm) < 1e-12) | (np.abs(X[1] - ymn) < 1e-12)
                               | (np.abs(X[1] - ymx) < 1e-12))
    D = b2.get_dofs(dirichlet).flatten()
    keep = np.setdiff1d(np.arange(b2.N), D)
    Kk, Mk, Bd = K.tocsr()[keep][:, keep], Ms.tocsr()[keep][:, keep], Bm[keep]
    w = 2 * np.pi * f
    lu = spla.splu((Kk + 1j * w * Mk).tocsc(), permc_spec="MMD_AT_PLUS_A")
    X = lu.solve(Bd.astype(complex))
    V = np.linalg.solve(np.diag(Gk) - 1j * w * (Bd.T @ X), -I)
    Z = -(V[0] - (V[1] if len(V) > 1 else 0.0))                # E = -j w A - V'; one group:
                                                                # the A = 0 boundary is the return
    # PEC external problems on the same mesh: A = a_g on group g, 0 on the box
    dg = [np.unique(b2.element_dofs[:, g]) for g in ing]
    DD = np.unique(np.concatenate([D] + dg))
    Gam = np.zeros((len(groups), len(groups)))
    for j in range(len(groups)):
        a_D = np.zeros(b2.N); a_D[dg[j]] = 1.0
        Kc, fc, ac, II = condense(K, np.zeros(b2.N), x=a_D, D=DD)
        a = ac.copy(); a[II] = solve(Kc, fc)
        r = K @ a
        Gam[:, j] = [r[d].sum() for d in dg]                  # half-domain currents
    L_ext_box = 1.0 / (2.0 * Gam[0, 0])                      # notebook cell [6]
    aa = np.linalg.solve(Gam, I)
    L_ext = aa[0] - (aa[1] if len(aa) > 1 else 0.0)           # line current 1 A
    return dict(R=Z.real, L=Z.imag / w, L_ext=L_ext, L_ext_box=L_ext_box,
                box_share=Gam[:, 0].sum() / Gam[0, 0],        # L_ext_box problem: share of the return on the box
                n_el=int(m.nelements), ndof=int(b2.N))


def section(WS, MTX, pieces, finger="float", f=F0, **mesh_kw):
    m, cond = section_mesh(WS, MTX, pieces, **mesh_kw)
    groups, I = groups_for(pieces, finger)
    out = solve_mqs(m, cond, groups, I, f)
    out["L_int"] = out["L"] - out["L_ext"]
    out["L_int_box"] = out["L"] - out["L_ext_box"]
    return out
