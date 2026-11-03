"""
Six-mode fit of the electric-bottom CORDOBA 8 mm TD gap fields (widened model, port-1 monitors at
5..60 GHz) with the 2 mm electric-bottom eigenmodes of the phase sweep (5, 10, 15, 20, 25, 30 deg).
Same machinery as ../modefit/fit30.py and ../../cordoba_8mm_wide_ebottom/fit_weighting.py:
exact sectors (A, B' = mirror of B), cell-periodic patterns u(zc) (backward export, forward = z-mirror),
interior z 0.31-7.69 mm, T-stem positions excluded, one weight per line, A's slot pattern x10.

Families (index in each run, checked on the gap patterns): even 1 strips vs bottom, 2 slot, 3 CPW;
odd 1 A vs B, 2 slot, 3 CPW.
Dispersion of each family at the TD frequency f: n(f) = n_inf + b/sqrt(f) + c f fitted through the eigen
points (b: internal inductance of the conductors; c: geometric dispersion); attenuation from
alpha_k = omega_k/(2 Q_k v_g,k), fitted as a sqrt(f) + b f + c f^2 (conductor, dielectric, radiation).
Pattern: from the eigen point nearest in frequency (PATTERN=nearest) or linear interpolation between the
two neighbours after phase/amplitude alignment (PATTERN=interp). Even and odd of a family always come from
the same phase (same pair of runs), so the even-odd difference is not mixed across meshes.
The CPW even-odd index split is taken from the eigen pairs (interpolated in f), applied as +-split/2.
"""
import os, sys, re
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../../.."))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(HERE, "../modefit"))
from fieldio import load_field_table
from mzm_interconnect.xtalk_fields import load_field_dir

C0 = 2.99792458e8; LAM = 0.18e-3; L = 8e-3; NG_OPT = 2.27
TD = os.path.join(HERE, "../../cordoba_8mm_wide_ebottom")
PH = [5, 10, 15, 20, 25, 30]
RUNS = {}
for p in PH:
    for sym in ("even", "odd"):
        d = os.path.join(HERE, f"p{p}_{sym}") if p != 15 else os.path.join(HERE, "../eigen_w2mm_mag_ebottom")
        if p != 15:
            rows = re.findall(r"^\s+(\d+)\s+([\d.]+) GHz\s+([\d.]+)", open(os.path.join(d, "log_excerpt.txt")).read(), re.M)
            fq = [(float(f), float(q)) for _, f, q in rows]
        else:
            fq = {"even": [(22.2635700716, 38.28), (28.7474073186, 30.33), (31.0442220176, 26.28), (57.6845, 6.1)],
                  "odd": [(23.8567966499, 13.61), (28.9257077157, 34.17), (31.0445460781, 26.28), (49.4865, 5.2),
                          (58.6331, 5.3)]}[sym]
        RUNS[(p, sym)] = [(f, q, os.path.join(d, f"eig_{sym}_mode{k+1}_e.txt")) for k, (f, q) in enumerate(fq)]
FAM = {"e_sb": ("even", 0), "e_slot": ("even", 1), "e_cpw": ("even", 2),
       "o_AvsB": ("odd", 0), "o_slot": ("odd", 1), "o_cpw": ("odd", 2)}
PAIR = {"cpw": ("e_cpw", "o_cpw"), "slot": ("e_slot", "o_slot")}


def points(fam):
    sym, k = FAM[fam]
    return [(p,) + RUNS[(p, sym)][k] for p in PH if len(RUNS[(p, sym)]) > k]


def _pattern_raw(fn):
    a = load_field_table(fn); ey = a[:, 5] + 1j * a[:, 6]
    zp = np.round(a[np.isclose(a[:, 1], 0.3325), 2], 4)
    p, m = ey[np.isclose(a[:, 1], 0.3325)], ey[np.isclose(a[:, 1], 0.2925)]
    s = p + m if np.linalg.norm(p + m) > np.linalg.norm(p - m) else p - m
    ph = np.angle(s[-1] / s[0])
    ub = (np.stack([p, m]) * np.exp(-1j * ph * zp * 1e-3 / LAM))[:, :-1]
    return ub / np.linalg.norm(ub)


_cache = {}
def pattern_raw(fn):
    if fn not in _cache:
        _cache[fn] = _pattern_raw(fn)
    return _cache[fn]


def align(u, ref):
    """u scaled by the complex factor that best matches ref (least squares)."""
    c = np.vdot(u.ravel(), ref.ravel()) / np.vdot(u.ravel(), u.ravel())
    return u * c


class Dispersion:
    def __init__(self, fam):
        pts = points(fam)
        self.ph = np.array([q[0] for q in pts]); self.f = np.array([q[1] for q in pts])
        self.Q = np.array([q[2] for q in pts]); self.files = [q[3] for q in pts]
        self.n = C0 * np.deg2rad(self.ph) / LAM / (2 * np.pi * self.f * 1e9)
        X = np.stack([np.ones_like(self.f), 1 / np.sqrt(self.f), self.f], 1)
        self.cn, *_ = np.linalg.lstsq(X, self.n, rcond=None)
        self.ng_pts = self.n_g(self.f)
        self.alpha_pts = 2 * np.pi * self.f * 1e9 / (2 * self.Q * C0 / self.ng_pts)     # Np/m
        Xa = np.stack([np.sqrt(self.f), self.f, self.f ** 2], 1)
        self.ca, *_ = np.linalg.lstsq(Xa, self.alpha_pts, rcond=None)

    def n_of(self, f):
        f = np.asarray(f, float); return self.cn[0] + self.cn[1] / np.sqrt(f) + self.cn[2] * f

    def n_g(self, f):  # n_g = n + f dn/df
        f = np.asarray(f, float); return self.n_of(f) + f * (-0.5 * self.cn[1] * f ** -1.5 + self.cn[2])

    def alpha(self, f):
        f = np.asarray(f, float); return self.ca[0] * np.sqrt(f) + self.ca[1] * f + self.ca[2] * f ** 2

    def resid_n(self):
        return self.n - self.n_of(self.f)


DISP = {fam: Dispersion(fam) for fam in FAM}


def split_cpw(f):
    """Even - odd index split of the CPW pair at f, from the eigen pairs (linear in f, ends held)."""
    e, o = DISP["e_cpw"], DISP["o_cpw"]
    # at equal phase: n_e - n_o = n (f_o - f_e)/f  (index split at fixed f, to first order: x n/n_g * n_g/n)
    fs = e.f; d = (o.f - e.f) / e.f * e.ng_pts
    return np.interp(f, fs, d)


def pattern_at(fam, f, mode):
    D = DISP[fam]; partner = {"e_cpw": "o_cpw", "o_cpw": "e_cpw", "e_slot": "o_slot", "o_slot": "e_slot"}.get(fam)
    # choose the phase(s) on the family's own frequency axis (even member for pairs, so both use the same phase)
    ref = DISP[fam if fam.startswith("e") or partner is None else partner]
    if mode == "nearest" or f <= ref.f[0] or f >= ref.f[-1]:
        i = int(np.argmin(abs(ref.f - f)))
        ph = ref.ph[i]; j = int(np.where(D.ph == ph)[0][0])
        return pattern_raw(D.files[j]), ph
    i = int(np.searchsorted(ref.f, f)) - 1; t = (f - ref.f[i]) / (ref.f[i + 1] - ref.f[i])
    j0 = int(np.where(D.ph == ref.ph[i])[0][0]); j1 = int(np.where(D.ph == ref.ph[i + 1])[0][0])
    u0 = pattern_raw(D.files[j0]); u1 = align(pattern_raw(D.files[j1]), u0)
    u = (1 - t) * u0 + t * u1
    return u / np.linalg.norm(u), (ref.ph[i], ref.ph[i + 1], t)


class TDData:
    def __init__(self, f):
        fd = load_field_dir(TD); self.fd = fd
        Fp = fd["ports"][float(f)][1]; z = fd["z"]
        A = np.stack([Fp["A"][0], Fp["A"][1]]); Bp = np.stack([-Fp["B"][1], -Fp["B"][0]])
        self.z_full, self.A_full, self.Bp_full = z, A, Bp
        sel = (z >= 0.31e-3 - 1e-9) & (z <= 7.69e-3 + 1e-9)
        zz = z[sel]; A = A[:, sel]; Bp = Bp[:, sel]
        idx = np.round(((zz * 1e3 - 0.04) % 0.18) / 0.005).astype(int) % 36
        keep = ~((idx >= 13) & (idx <= 23))
        self.zz, self.A, self.Bp, self.idx = zz[keep], A[:, keep], Bp[:, keep], idx[keep]


cpw = lambda v: (v[0] - v[1]) / 2
slot = lambda v: (v[0] + v[1]) / 2


def basis(fams, f, td, mode="nearest", use_split=True, extra=None):
    cols, labels, info = [], [], {}
    w = 2 * np.pi * f * 1e9
    for nm in fams:
        D = DISP[nm]; u, src = pattern_at(nm, f, mode)
        n = float(D.n_of(f)); a = float(D.alpha(f))
        if use_split and nm.endswith("cpw"):
            pr = DISP["e_cpw"]; nmean = 0.5 * (float(DISP["e_cpw"].n_of(f)) + float(DISP["o_cpw"].n_of(f)))
            n = nmean + (0.5 if nm.startswith("e") else -0.5) * float(split_cpw(f))
        g = a + 1j * w * n / C0
        ub = u; uf = ub[:, (-np.arange(36)) % 36]
        cols.append(uf[:, td.idx] * np.exp(-g * td.zz)); labels.append(nm + "+")
        cols.append(ub[:, td.idx] * np.exp(-g * (L - td.zz))); labels.append(nm + "-")
        info[nm] = dict(n=n, alpha_dB_mm=a * 8.686e-3, src=src)
    if extra:
        for nm, (u, n, a) in extra.items():
            g = a + 1j * w * n / C0; uf = u[:, (-np.arange(36)) % 36]
            cols.append(uf[:, td.idx] * np.exp(-g * td.zz)); labels.append(nm + "+")
            cols.append(u[:, td.idx] * np.exp(-g * (L - td.zz))); labels.append(nm + "-")
            info[nm] = dict(n=n, alpha_dB_mm=a * 8.686e-3, src="extra")
    return cols, labels, info


def fit(f, td, fams_e=("e_cpw", "e_slot", "e_sb"), fams_o=("o_cpw", "o_slot", "o_AvsB"), mode="nearest",
        wslotA=10.0, use_split=True, extra_e=None, extra_o=None):
    ce, le, ie = basis(fams_e, f, td, mode, use_split, extra_e)
    co, lo, io = basis(fams_o, f, td, mode, use_split, extra_o)
    colsA = [0.5 * c for c in ce] + [0.5 * c for c in co]
    colsB = [0.5 * c for c in ce] + [-0.5 * c for c in co]
    wA = 1 / np.sqrt(np.mean(abs(td.A) ** 2)); wB = 1 / np.sqrt(np.mean(abs(td.Bp) ** 2))
    data = {"A CPW": cpw(td.A), "A slot": slot(td.A), "B CPW": cpw(td.Bp), "B slot": slot(td.Bp)}
    cols = {"A CPW": [cpw(c) for c in colsA], "A slot": [slot(c) for c in colsA],
            "B CPW": [cpw(c) for c in colsB], "B slot": [slot(c) for c in colsB]}
    w = {"A CPW": wA, "A slot": wA * wslotA, "B CPW": wB, "B slot": wB}
    M = np.vstack([np.array(cols[k]).T * w[k] for k in data]); d = np.concatenate([data[k] * w[k] for k in data])
    x, *_ = np.linalg.lstsq(M, d, rcond=None)
    model = {k: np.array(cols[k]).T @ x for k in data}
    res = {k: np.linalg.norm(data[k] - model[k]) / np.linalg.norm(data[k]) for k in data}
    labels = le + lo
    comp_B = {lab: (np.array(cols["B CPW"])[i] * x[i]) for i, lab in enumerate(labels)}
    comp_A = {lab: (np.array(cols["A CPW"])[i] * x[i]) for i, lab in enumerate(labels)}
    bo = 2 * np.pi * f * 1e9 * NG_OPT / C0
    H = lambda v: np.mean(v * np.exp(1j * bo * (td.zz - L)))
    eo = dict(Hd_B=H(data["B CPW"]), Hm_B=H(model["B CPW"]), Hd_A=H(data["A CPW"]), Hm_A=H(model["A CPW"]),
              HB_comp={k: H(v) for k, v in comp_B.items()})
    return dict(res=res, x=dict(zip(labels, x)), info={**ie, **io}, eo=eo, data=data, model=model)


def eo_full(td, f):
    """EO crosstalk B/A on the full line (trapezoid over 0-8 mm, all samples), CPW pattern, n_g 2.27."""
    bo = 2 * np.pi * f * 1e9 * NG_OPT / C0; z = td.z_full
    H = lambda v: np.trapezoid(v * np.exp(1j * bo * (z - z[-1])), z) / L
    return H(cpw(td.Bp_full)) / H(cpw(td.A_full))


FTD = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
