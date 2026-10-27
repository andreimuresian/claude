"""
Bloch-exact wave extraction. In a structure periodic with Lambda = 200 um, each wave is
F_m(y, z) = sum_p c_mp(y) e^{-j(beta_m + 2 pi p / Lambda) z}. Sampled at z = z0 + k Lambda,
every harmonic equals the fundamental: F_m(y, z0 + k Lambda) = C_m(y, z0) q_m^k with
q_m = e^{-j beta_m Lambda}. So each (y, component, cell position z0) is a channel of exact
exponentials in k, all sharing the q_m. No averaging, no approximation.
"""
import numpy as np
ETA0 = 376.730313668
DZ = 0.005; LAM = 0.2; STEP = int(round(LAM / DZ))          # 40 samples per cell

def channels(fG, zr=(0.3, 4.7), phases=range(0, 40, 4), ysel=None):
    d = np.load(f"/tmp/claude-0/-home-user-claude/7930b8bd-7239-59e6-a8de-284bb11bf7ea/scratchpad/eh/eh_{fG}.npz")
    ys, zs, E, H = d["ys"], d["zs"], d["E"], d["H"]
    i0 = int(np.searchsorted(zs, zr[0])); n = int((zr[1] - zr[0]) / LAM)
    raw, info = [], []
    for j in range(len(ys)):
        if ysel is not None and not ysel(ys[j]): continue
        for p in phases:
            idx = i0 + p + STEP * np.arange(n)
            comps = [E[j, idx, 0], E[j, idx, 1], ETA0 * H[j, idx, 0], ETA0 * H[j, idx, 1]]
            for c, v in enumerate(comps):
                if np.max(abs(v)) > 0:
                    raw.append(v); info.append((j, c, p))
    return ys, np.array(raw), info

def pencil(raw, M, Lp=None):
    nrm = np.sqrt(np.mean(abs(raw) ** 2, axis=1))
    X = raw / nrm[:, None]
    N = X.shape[1]; Lp = Lp or N // 2
    Hk = np.vstack([np.array([v[i:i + Lp + 1] for i in range(N - Lp)]) for v in X])
    _, Sv, Vh = np.linalg.svd(Hk, full_matrices=False)
    V = Vh[:M].T
    q = np.linalg.eigvals(np.linalg.pinv(V[:-1]) @ V[1:])
    Z = q[None, :] ** np.arange(N)[:, None]
    A, *_ = np.linalg.lstsq(Z, raw.T, rcond=None)
    err = np.linalg.norm(Z @ A - raw.T) / np.linalg.norm(raw)
    return q, A, err, Sv / Sv[0]

def describe(fG, q, A, info, ys):
    """beta (from q per cell), power-flow direction check, strength in gaps / between lines."""
    k0 = 2 * np.pi * fG * 1e9 / 2.99792458e8
    rows = []
    jj = np.array([i[0] for i in info]); cc = np.array([i[1] for i in info]); pp = np.array([i[2] for i in info])
    for m in range(len(q)):
        s = np.log(q[m]) / (LAM * 1e-3)
        n = -s.imag / k0; a = -s.real * 8.686 / 100
        Pz = 0.0
        for p in np.unique(pp):                                 # power flow summed over y and cell positions
            sel = pp == p
            f = {c: np.zeros(len(ys), complex) for c in range(4)}
            for val, j, c in zip(A[m][sel], jj[sel], cc[sel]):
                f[c][j] = val
            Pz += np.sum(np.real(f[0] * np.conj(f[3]) - f[1] * np.conj(f[2])))
        e = np.sqrt(np.mean(abs(A[m][cc < 2]) ** 2))
        rows.append(dict(n=n, a=a, E=e, ok=np.sign(Pz) == np.sign(n)))
    return sorted(rows, key=lambda r: -r["E"])
