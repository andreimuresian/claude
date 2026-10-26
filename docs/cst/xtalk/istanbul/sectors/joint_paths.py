"""
Three-path model of NEXT, fitted on two Istanbul lengths and used to predict the others.

    NEXT(f, L) = sum_k c_k(f) (L/5 mm)^p_k exp(-j 2 pi f (tau0_k + S_k L / c))

c_k(f): complex cubic in f (end conversions); tau0_k: port-region delay;
p_k: amplitude law in L (with two lengths, one L-parameter per path).
'3 paths': S = (2 n_c, n_c + n_x, 2 n_x), two group indices for three paths.
'1 path' : only the plain two-mode reflection path (control).
The 1 mm file (asymmetric ends, other mesh family) is only predicted.
"""
import os, sys, numpy as np, skrf
from scipy.optimize import least_squares
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sector_fit import FILES
UP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = 0.299792458                      # mm/ps
DEG = 3
ECHO = [(39.1, 4.33), (47.5, 4.48), (55.7, 4.75)]   # delays.py, 3 mm: tau (ps), n-sum

def load(L, band=(5, 60), step=3):
    n = skrf.Network(os.path.join(UP, FILES[L]))
    sel = np.where((n.f >= band[0] * 1e9) & (n.f <= band[1] * 1e9))[0][::step]
    return n.f[sel], n.s[sel, 2, 0]

def unpack(x, K):
    if K == 3:
        S = [2 * x[0], x[0] + x[1], 2 * x[1]]; p = 2
    else:
        S = [x[0]]; p = 1
    paths = []
    for k in range(K):
        c = x[p:p + 2 * (DEG + 1)]; p += 2 * (DEG + 1)
        paths.append((c, x[p], x[p + 1], S[k])); p += 2
    return paths

def model(x, K, f, L):
    V = np.vander((f - 32.5e9) / 27.5e9, DEG + 1, increasing=True)
    out = 0
    for c, tau0, pk, Sk in unpack(x, K):
        out = out + (V @ (c[:DEG + 1] + 1j * c[DEG + 1:])) * (L / 5.0) ** pk \
              * np.exp(-2j * np.pi * f * (tau0 + Sk * L / C) * 1e-12)
    return out

def fit(K, Ls, seeds=10):
    data = {L: load(L) for L in Ls}
    def res(x):
        e = np.concatenate([model(x, K, f, L) - y for L, (f, y) in data.items()])
        return np.concatenate([e.real, e.imag])
    rng = np.random.default_rng(1); best = None
    for s in range(seeds):
        x0 = [2.16 + rng.normal(0, .03), 2.38 + rng.normal(0, .05)] if K == 3 else [4.4 + rng.normal(0, .1)]
        for k in range(K):
            c = np.zeros(2 * (DEG + 1)); ph = rng.uniform(0, 2 * np.pi)
            c[0], c[DEG + 1] = 0.005 * np.cos(ph), 0.005 * np.sin(ph)
            x0 += list(c) + [ECHO[k][0] - ECHO[k][1] * 3 / C + rng.normal(0, 2), 1.0 + rng.normal(0, .3)]
        sol = least_squares(res, np.array(x0), max_nfev=5000)
        if best is None or sol.cost < best.cost:
            best = sol
    return best

def err_db(x, K, L):
    """rms complex error re rms |NEXT| (dB), and worst |NEXT| magnitude error 10-50 GHz (dB)."""
    f, y = load(L)
    m = model(x, K, f, L)
    band = (f >= 10e9) & (f <= 50e9)
    return (20 * np.log10(np.sqrt(np.mean(abs(m - y) ** 2)) / np.sqrt(np.mean(abs(y) ** 2))),
            np.max(np.abs(20 * np.log10(abs(m[band]) / abs(y[band])))))

if __name__ == "__main__":
    splits = [((3.0, 5.0), 8.75), ((3.0, 8.75), 5.0), ((5.0, 8.75), 3.0)]
    for train, test in splits:
        print(f"\n== fit on {train} mm, predict {test} mm (and 1 mm) ==")
        for K in (1, 3):
            sol = fit(K, train)
            tr = [err_db(sol.x, K, L)[0] for L in train]
            te, te1 = err_db(sol.x, K, test), err_db(sol.x, K, 1.0)
            print(f"  {K} path(s): fit {tr[0]:6.1f} / {tr[1]:6.1f} dB re NEXT | predicted {test} mm: "
                  f"{te[0]:6.1f} dB, worst |NEXT| error {te[1]:5.1f} dB | predicted 1 mm: {te1[0]:6.1f} dB, worst {te1[1]:5.1f} dB")
            if K == 3:
                print("     n_c = %.3f, n_x = %.3f; " % (sol.x[0], sol.x[1]) +
                      ", ".join(f"path {k+1}: L^{pk:.2f}, tau0 {t0:5.1f} ps"
                                for k, (c, t0, pk, S) in enumerate(unpack(sol.x, K))))
            np.save(f"joint_{K}p_{'_'.join(str(l) for l in train)}.npy", sol.x)
