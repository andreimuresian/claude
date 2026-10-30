"""
Five-mode fit of the CORDOBA 8 mm TD gap fields at 30 GHz with the eigenmode solutions
(1.2 mm cell, magnetic side wall, 15 deg, f = 22.4-31.03 GHz). T-stem cell positions excluded.

Exact pair sectors from the port-1 field F1 and its mirror (= port-3 field), written on line A:
  A  = F1 on A,  B' = mirror of F1 on B (same gap columns as A),  S_e = A + B', S_o = A - B'.
Model in sector s (gap columns k = + side y 0.3325, - side y 0.2925):
  E_k(z) = sum_m  a_m^+ u_{m,k}^f(zc) e^{-gamma_m z} + a_m^- u_{m,k}^b(zc) e^{-gamma_m (L - z)}
u: cell-periodic part of the eigenmode E_y (the export travels toward -z: its phase grows by
+15 deg per cell); forward pattern = z-mirror of the backward one (T cell symmetric about its
centre). zc = (z - 0.04) mod 0.18 (TD T centres at 0.13 + k 0.18, eigenmode cell centre 0.09).
gamma_m: beta at 30 GHz from the eigen beta (phi/Lambda at f_m) minus (f_m - 30 GHz) 2 pi n_g / c;
alpha = omega / (2 Q v_g). n_g = 2.227 (TD) for CPW, n_g = n for the others.
Fitted jointly on A and B' (block weights 1/rms), interior z = 0.31-7.69 mm.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))
import numpy as np
from mzm_interconnect.xtalk_fields import load_field_dir
C0 = 2.99792458e8; LAM = 0.18e-3; PHI = np.deg2rad(15.0); F = 30e9; L = 8e-3
HERE = os.path.dirname(os.path.abspath(__file__)); EIG = os.path.join(HERE, "../eigen_w1.2mm_mag")
MODES = {  # name: (file, f_GHz, Q_total, n_g or None); 1.2 mm cell, magnetic side wall
    "e_slot": ("eig_even_mode1_slot.txt", 28.6661571091, 29.144, None),
    "e_cpw":  ("eig_even_mode2_cpw.txt", 31.0298117061, 26.251, 2.227),
    "o_AvsB": ("eig_odd_mode1_AvsB.txt", 22.4143168874, 4.604, None),
    "o_slot": ("eig_odd_mode2_slot.txt", 28.8667173152, 33.498, None),
    "o_cpw":  ("eig_odd_mode3_cpw.txt", 31.0302771383, 26.260, 2.227),
}

def pattern(fn):
    a = np.loadtxt(os.path.join(EIG, fn), skiprows=2)
    ey = a[:, 5] + 1j * a[:, 6]
    zp = np.round(a[np.isclose(a[:, 1], 0.3325), 2], 4)
    p, m = ey[np.isclose(a[:, 1], 0.3325)], ey[np.isclose(a[:, 1], 0.2925)]
    ph = np.angle((p[-1] + m[-1]) / (p[0] + m[0])) if abs(p[0] + m[0]) > abs(p[0] - m[0]) else np.angle((p[-1] - m[-1]) / (p[0] - m[0]))
    zc = zp * 1e-3
    ub = np.stack([p, m]) * np.exp(-1j * ph * zc / LAM)          # periodic part (36 + endpoint)
    ub = ub[:, :-1]
    uf = ub[:, (-np.arange(36)) % 36]                             # z-mirror about the cell centre
    return ub, uf, np.rad2deg(ph)

def gamma(f_GHz, Q, ng, n_override=None):
    beta_e = PHI / LAM
    n_m = beta_e * C0 / (2 * np.pi * f_GHz * 1e9)
    ng = ng or n_m
    beta = beta_e - (f_GHz * 1e9 - F) * 2 * np.pi * ng / C0
    alpha = 2 * np.pi * f_GHz * 1e9 / (2 * Q * C0 / ng)
    return alpha + 1j * beta, beta * C0 / (2 * np.pi * F), alpha * 8.686 / 100

fd = load_field_dir(os.environ.get("FIELDS") or os.path.join(HERE, ".."))   # FIELDS: another run's gap fields
Fp = fd["ports"][30.0][1]
z = fd["z"]
A = np.stack([Fp["A"][0], Fp["A"][1]])                           # (+, -) on A
Bp = np.stack([-Fp["B"][1], -Fp["B"][0]])                        # mirror of B onto A
sel = (z >= 0.31e-3 - 1e-9) & (z <= 7.69e-3 + 1e-9)
zz = z[sel]; A = A[:, sel]; Bp = Bp[:, sel]
idx = np.round(((zz * 1e3 - 0.04) % 0.18) / 0.005).astype(int) % 36
# T-stem region (zc 65-115 um): TD and eigenmode resolve the field next to the stem corner
# differently (TD dip broad, eigen dip narrow); elsewhere both cell profiles are flat to 1 %.
STEM = (idx >= 13) & (idx <= 23)
if os.environ.get("KEEP_STEM") != "1":
    keep = ~STEM
    zz, A, Bp, idx = zz[keep], A[:, keep], Bp[:, keep], idx[keep]

def basis(names, dbeta_cpw=None):
    cols, labels = [], []
    for nm in names:
        fn, f, Q, ng = MODES[nm]
        ub, uf, ph = pattern(fn)
        g, n, adb = gamma(f, Q, ng)
        if dbeta_cpw is not None and nm.endswith("cpw"):
            g = g + (0.5j if nm.startswith("e") else -0.5j) * dbeta_cpw
        cols.append(uf[:, idx] * np.exp(-g * zz)); labels.append(nm + "+")
        cols.append(ub[:, idx] * np.exp(-g * (L - zz))); labels.append(nm + "-")
    return cols, labels

def fit(names_e, names_o, dbeta_cpw=None, verbose=True):
    ce, le = basis(names_e, dbeta_cpw); co, lo = basis(names_o, dbeta_cpw)
    wa, wb = 1 / np.sqrt(np.mean(abs(A) ** 2)), 1 / np.sqrt(np.mean(abs(Bp) ** 2))
    # A = (Se + So)/2, B' = (Se - So)/2
    rows_A = [c.ravel() * 0.5 * wa for c in ce] + [c.ravel() * 0.5 * wa for c in co]
    rows_B = [c.ravel() * 0.5 * wb for c in ce] + [-c.ravel() * 0.5 * wb for c in co]
    M = np.vstack([np.array(rows_A).T, np.array(rows_B).T])
    d = np.concatenate([A.ravel() * wa, Bp.ravel() * wb])
    x, *_ = np.linalg.lstsq(M, d, rcond=None)
    mA = (np.array(rows_A).T @ x / wa).reshape(A.shape); mB = (np.array(rows_B).T @ x / wb).reshape(Bp.shape)
    r = lambda a, b: np.linalg.norm(a - b) / np.linalg.norm(a)
    cpw = lambda v: (v[0] - v[1]) / 2; slot = lambda v: (v[0] + v[1]) / 2
    out = dict(rA=r(A, mA), rB=r(Bp, mB), rBc=r(cpw(Bp), cpw(mB)), rBs=r(slot(Bp), slot(mB)),
               rAc=r(cpw(A), cpw(mA)), x=dict(zip(le + lo, x)), mA=mA, mB=mB)
    return out

if __name__ == "__main__":
    for nm, (fn, f, Q, ng) in MODES.items():
        ub, uf, ph = pattern(fn); g, n, adb = gamma(f, Q, ng)
        print(f"{nm:7s} f {f:8.4f} GHz  phase/cell {ph:+6.2f} deg  n(30 GHz) {n:.5f}  alpha {adb:5.2f} dB/cm")
    ne = gamma(MODES['e_cpw'][1], 1, 2.227)[1]; no = gamma(MODES['o_cpw'][1], 1, 2.227)[1]
    print(f"CPW split at 30 GHz from the eigen runs: {ne-no:.2e}")
    k0 = 2 * np.pi * F / C0
    cases = [("CPW pair only", ["e_cpw"], ["o_cpw"]),
             ("CPW + slot", ["e_cpw", "e_slot"], ["o_cpw", "o_slot"]),
             ("all five", ["e_cpw", "e_slot"], ["o_cpw", "o_slot", "o_AvsB"])]
    print("\nmodel                     | resid A | A CPW | B' all | B' CPW | B' slot")
    for lab, ne_, no_ in cases:
        o = fit(ne_, no_)
        print(f"{lab:26s}| {o['rA']:.3f}   | {o['rAc']:.3f} | {o['rB']:.3f}  | {o['rBc']:.3f}  | {o['rBs']:.3f}")
    print("\nCPW split as a free check (all five modes), residual on B' CPW pattern:")
    for dn in (0, 3.1e-5, 5e-5, 7e-5, 1e-4, 1.5e-4):
        o = fit(["e_cpw", "e_slot"], ["o_cpw", "o_slot", "o_AvsB"], dbeta_cpw=k0 * (dn - (ne - no)))
        print(f"  dn {dn:.1e}: B' CPW resid {o['rBc']:.3f}, B' all {o['rB']:.3f}, A {o['rA']:.3f}")
    o = fit(["e_cpw", "e_slot"], ["o_cpw", "o_slot", "o_AvsB"])
    print("\namplitudes (all five, eigen split), |a| relative to e_cpw+:")
    ref = abs(o["x"]["e_cpw+"])
    for k, v in o["x"].items():
        print(f"  {k:9s} {abs(v)/ref:.3e}")
