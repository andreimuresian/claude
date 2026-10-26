"""
Global (all-frequency) fit of a sector of the Istanbul pair over 3, 5, 8.75 mm.

Junction J (port, mode c [, mode x]): reciprocal, general (lossy), each element
a cubic polynomial in f over the band. gamma_c free per frequency. Optional mode
x: n_x one global constant (scanned), alpha_x = a0 + a1 (f/30 GHz) >= 0; its
elements t_x, kappa, rho_x are cubic polynomials too (rho_x free: the fit says
whether the far end reflects it fully).
"""
import os, sys, numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sector_fit import FILES, sectors, C0
LS = np.array([3.0, 5.0, 8.75]); NP_DB = np.log(10) / 20; DEG = 3

def load(sector, f_lo=10e9, f_hi=50e9, step=5):
    data = {}
    for L in LS:
        f, sec = sectors(FILES[L]); data[L] = sec[sector]
    sel = np.where((f >= f_lo) & (f <= f_hi))[0][::step]
    S11 = np.array([data[L][0][sel] for L in LS]); S21 = np.array([data[L][1][sel] for L in LS])
    return f[sel], S11, S21

class Model:
    def __init__(self, f, two, nx=None):
        self.f, self.two, self.nx = f, two, nx
        self.u = (f - f.mean()) / (f.max() - f.min()) * 2          # -1..1
        self.V = np.vander(self.u, DEG + 1, increasing=True)        # nf x 4
        self.nel = 5 if two else 3                                  # r,tc,rc [,tx,kap] ; rho_x extra
        if two: self.nel = 6                                        # + rho_x
        self.k0 = 2 * np.pi * f / C0
    def split(self, x):
        nf = len(self.f); p = 0
        el = []
        for _ in range(self.nel):
            c = x[p:p + 2 * (DEG + 1)]; p += 2 * (DEG + 1)
            el.append(self.V @ (c[:DEG + 1] + 1j * c[DEG + 1:]))
        nc = x[p:p + nf]; p += nf; ac = x[p:p + nf]; p += nf
        ax = None
        if self.two:
            ax = x[p] + x[p + 1] * self.f / 30e9; p += 2
        return el, nc, ac, ax
    def S(self, x):
        el, nc, ac, ax = self.split(x)
        gc = ac * 100 * NP_DB + 1j * self.k0 * nc
        out11, out21 = [], []
        for L in LS:
            Pc = np.exp(-gc * L * 1e-3)
            if not self.two:
                r, t, rc = el
                den = 1 - rc * rc * Pc * Pc
                out11.append(r + t * t * Pc * rc * Pc / den); out21.append(t * t * Pc / den)
            else:
                r, tc, rc, tx, kap, rx = el
                gx = np.abs(ax) * 100 * NP_DB + 1j * self.k0 * self.nx
                Px = np.exp(-gx * L * 1e-3)
                nf = len(self.f)
                R = np.zeros((nf, 2, 2), complex); R[:, 0, 0] = rc; R[:, 0, 1] = R[:, 1, 0] = kap; R[:, 1, 1] = rx
                P = np.zeros((nf, 2, 2), complex); P[:, 0, 0] = Pc; P[:, 1, 1] = Px
                t = np.stack([tc, tx], 1)
                M = R @ P @ R @ P
                a1 = np.linalg.solve(np.eye(2)[None] - M, t[..., None])[..., 0]
                b1 = np.einsum("nij,nj->ni", P @ R @ P, a1)
                out11.append(r + np.sum(t * b1, 1)); out21.append(np.sum(t * np.einsum("nij,nj->ni", P, a1), 1))
        return np.array(out11), np.array(out21)

def fit(sector, two=False, nx=None, x0=None, seed=0):
    f, S11, S21 = load(sector)
    m = Model(f, two, nx)
    prev = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sector_fit.npz"))[sector]
    nc0 = np.interp(f, prev[:, 0], prev[:, 2]); ac0 = np.interp(f, prev[:, 0], prev[:, 3])
    rng = np.random.default_rng(seed)
    def poly(val, scale=0.0):
        c = np.zeros(2 * (DEG + 1)); c[0] = np.real(val); c[DEG + 1] = np.imag(val)
        return c + rng.normal(0, scale, c.size)
    if x0 is None:
        els = [poly(0.05 + 0.05j, 0.02), poly(1.0, 0.05), poly(0.05, 0.02)]
        if two:
            els += [poly(0.1 * np.exp(2j * np.pi * rng.random()), 0.05),
                    poly(0.1 * np.exp(2j * np.pi * rng.random()), 0.05),
                    poly(0.9 * np.exp(2j * np.pi * rng.random()), 0.05)]
        x0 = np.concatenate(els + [nc0, ac0] + ([[rng.uniform(1, 6), 0.0]] if two else []))
    def res(x):
        a, b = m.S(x)
        e = np.concatenate([(a - S11).ravel(), (b - S21).ravel()])
        return np.concatenate([e.real, e.imag])
    sol = least_squares(res, x0, method="trf", max_nfev=400, x_scale="jac")
    a, b = m.S(sol.x)
    err = np.max(np.abs(np.concatenate([a - S11, b - S21])), axis=0)    # per frequency
    return dict(f=f, err=err, x=sol.x, model=m, cost=sol.cost)

if __name__ == "__main__":
    sector = sys.argv[1]
    one = fit(sector)
    print(f"{sector} one mode, smooth junction: median {np.median(one['err']):.4f}  90% {np.percentile(one['err'], 90):.4f}", flush=True)
    for nx in [float(v) for v in sys.argv[2:]]:
        best = None
        for seed in range(4):
            r = fit(sector, True, nx, seed=seed)
            if best is None or r["cost"] < best["cost"]:
                best = r
        el, nc, ac, ax = best["model"].split(best["x"])
        rx = el[5]
        print(f"{sector} two modes n_x={nx:.2f}: median {np.median(best['err']):.4f}  90% {np.percentile(best['err'], 90):.4f}"
              f"   |rho_x| median {np.median(np.abs(rx)):.2f}  |t_x| {np.median(np.abs(el[3])):.3f}"
              f"  alpha_x {np.median(np.abs(ax)):.1f} dB/cm", flush=True)
        np.savez(f"smooth_{sector}_{nx:.2f}.npz", f=best["f"], err=best["err"], x=best["x"])
