"""
Joint 3 mm + 5 mm wave fit with patterns shared between the lengths.

Channels: Ex, Ey, eta0 Hx, eta0 Hy at every y, at fixed positions within the 200 um cell
(Bloch-exact sampling, one sample per cell), interior z0 = 0.3 mm to L - 0.3 mm.
Model, per frequency, M modes = 2M waves (forward q_m, backward 1/q_m, q_m = exp(-gamma_m Lambda)):
    X_L(c, k) = sum_w P[c, w] alpha_w^L g_w^L(k)
shared:   P (patterns), gamma_m;   per length: alpha^L (alpha^5 = 1 absorbed in P).
Control ('separate'): the same gamma_m, but each length with its own patterns.
"""
import sys, numpy as np
from scipy.optimize import least_squares
ETA0 = 376.730313668; DZ = 0.005; LAM = 0.2; STEP = 40
S = "/tmp/claude-0/-home-user-claude/7930b8bd-7239-59e6-a8de-284bb11bf7ea/scratchpad/eh"
NP_DB = np.log(10) / 20

def raw(fG, L, phases):
    d = np.load(f"{S}/eh3_{fG}.npz" if L == 3 else f"{S}/eh_{fG}.npz")
    ys, zs, E, H = d["ys"], d["zs"], d["E"], d["H"]
    i0 = int(np.searchsorted(zs, 0.3 - 1e-9)); n = int(round((L - 0.6) / LAM)) + 1
    out = {}
    for j in range(len(ys)):
        for p in phases:
            idx = i0 + p + STEP * np.arange(n)
            if idx[-1] >= len(zs): idx = idx[idx < len(zs)]
            for c, v in enumerate((E[j, idx, 0], E[j, idx, 1], ETA0 * H[j, idx, 0], ETA0 * H[j, idx, 1])):
                out[(j, c, p)] = v
    return ys, out, n

def data(fG, phases=range(0, 40, 8)):
    ys, r3, n3 = raw(fG, 3, phases); _, r5, n5 = raw(fG, 5, phases)
    keys = [k for k in r5 if np.max(abs(r5[k])) > 0 and np.max(abs(r3[k])) > 0]
    nrm = np.array([np.sqrt(np.mean(abs(r5[k]) ** 2)) for k in keys])
    X3 = np.array([r3[k] for k in keys]) / nrm[:, None]
    X5 = np.array([r5[k] for k in keys]) / nrm[:, None]
    return ys, keys, X3, X5

def G(gam, n):
    q = np.exp(-gam * LAM * 1e-3)
    k = np.arange(n)
    fwd = q[:, None] ** k[None, :]
    bwd = q[:, None] ** (n - 1 - k)[None, :]
    return np.vstack([fwd, bwd])                     # 2M x n

def unpack(x, M, k0):
    n, a = x[:M], x[M:2 * M]                          # index, loss dB/cm
    gam = a * 100 * NP_DB + 1j * k0 * n
    al = x[2 * M:4 * M] + 1j * x[4 * M:6 * M]         # alpha^3 for the 2M waves
    return gam, al

def compress(X):
    """Rows of X only enter through X^H X: replace X (C x N) by an N x N matrix with the
    same Gram matrix (exact for every residual below)."""
    _, s, Vh = np.linalg.svd(X, full_matrices=False)
    return s[:, None] * Vh

def resid_shared(x, M, k0, X3, X5, Xc=None):
    gam, al = unpack(x, M, k0)
    Gc = np.hstack([al[:, None] * G(gam, X3.shape[1]), G(gam, X5.shape[1])])
    X = compress(np.hstack([X3, X5])) if Xc is None else Xc
    P, *_ = np.linalg.lstsq(Gc.T, X.T, rcond=None)
    R = X - (Gc.T @ P).T
    return R

def resid_separate(gam, X3, X5):
    out = []
    for X in (compress(X3), compress(X5)):
        Gl = G(gam, X.shape[1]); P, *_ = np.linalg.lstsq(Gl.T, X.T, rcond=None)
        out.append(X - (Gl.T @ P).T)
    return out

def fit(fG, M, starts=30, seed=0, X=None):
    starts = int(__import__("os").environ.get("STARTS", starts))
    ys, keys, X3, X5 = X if X is not None else data(fG)
    k0 = 2 * np.pi * fG * 1e9 / 2.99792458e8
    nrm = np.sqrt(np.sum(abs(X3) ** 2) + np.sum(abs(X5) ** 2))
    rng = np.random.default_rng(seed); sols = []
    Xc = compress(np.hstack([X3, X5]))
    def f(x):
        R = resid_shared(x, M, k0, X3, X5, Xc).ravel() / nrm
        return np.concatenate([R.real, R.imag])
    for s in range(starts):
        n0 = np.sort(rng.uniform(1.0, 3.4, M)); n0[0] = 2.1 + rng.normal(0, .05)
        x0 = np.concatenate([n0, rng.uniform(0, 8, M), rng.normal(0, 1, 2 * M), rng.normal(0, 1, 2 * M)])
        lb = [0.5] * M + [-20] * M + [-np.inf] * 4 * M; ub = [4.0] * M + [80] * M + [np.inf] * 4 * M
        try:
            sol = least_squares(f, np.clip(x0, np.array(lb) + 1e-6, np.array(ub) - 1e-6), bounds=(lb, ub), max_nfev=300)
        except Exception:
            continue
        gam, al = unpack(sol.x, M, k0)
        R3, R5 = resid_separate(gam, X3, X5)
        sep = np.sqrt(np.sum(abs(R3) ** 2) + np.sum(abs(R5) ** 2)) / nrm
        sols.append(dict(err=np.sqrt(2 * sol.cost), sep=sep, n=sol.x[:M].copy(), a=sol.x[M:2 * M].copy()))
    sols.sort(key=lambda s: s["err"])
    return sols

if __name__ == "__main__":
    fG = int(sys.argv[1]); Ms = [int(v) for v in sys.argv[2:]] or [2, 3, 4]
    X = data(fG)
    print(f"{fG} GHz: {X[2].shape[0]} channels, cells 3 mm {X[2].shape[1]}, 5 mm {X[3].shape[1]}")
    for M in Ms:
        sols = fit(fG, M, X=X)
        print(f"  M={M} modes ({2*M} waves): best shared-pattern residual {sols[0]['err']:.4f} (separate patterns, same gamma: {sols[0]['sep']:.4f})")
        seen = []
        for s in sols:
            key = tuple(np.round(np.sort(s["n"]), 2))
            if any(np.allclose(key, k, atol=0.03) for k in seen): continue
            seen.append(key)
            o = np.argsort(s["n"])
            print(f"     err {s['err']:.4f} sep {s['sep']:.4f}: n = {np.round(s['n'][o], 3)}  loss dB/cm {np.round(s['a'][o], 1)}")
            if len(seen) >= 5: break
