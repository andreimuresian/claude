"""What remains of B's CPW pattern after the five-mode fit (30 GHz): envelope along z and a
matrix-pencil of the remainder (cell positions outside the T stem, one sample per cell)."""
import numpy as np, fit30 as F
o = F.fit(["e_cpw", "e_slot"], ["o_cpw", "o_slot", "o_AvsB"])
cpw = lambda v: (v[0] - v[1]) / 2
rB = cpw(F.Bp) - cpw(o["mB"]); dB = cpw(F.Bp); zz = F.zz * 1e3
print(" z (mm)   |B'_cpw| data   |remainder|   (normalised to rms of data)")
nrm = np.sqrt(np.mean(abs(dB) ** 2))
for a in np.arange(0.5, 7.6, 0.5):
    m = abs(zz - a) < 0.25
    print(f" {a:4.1f}     {np.sqrt(np.mean(abs(dB[m])**2))/nrm:6.3f}        {np.sqrt(np.mean(abs(rB[m])**2))/nrm:6.3f}")
# pencil on the remainder: channels = cell positions kept, samples = cells
k0 = 2 * np.pi * F.F / F.C0; LAM = 0.18
pos = sorted(set(F.idx))
ch = []
for p in pos:
    m = F.idx == p
    ch.append(rB[m][:40])
X = np.array([c for c in ch if len(c) == 40]); X = X / np.abs(X).max()
N = X.shape[1]; Lp = N // 2
Hk = np.vstack([np.array([v[i:i + Lp + 1] for i in range(N - Lp)]) for v in X])
_, Sv, Vh = np.linalg.svd(Hk, full_matrices=False)
print("SV:", " ".join(f"{s/Sv[0]:.2e}" for s in Sv[:8]))
for M in (2, 3, 4, 5):
    V = Vh[:M].T; q = np.linalg.eigvals(np.linalg.pinv(V[:-1]) @ V[1:])
    Z = q[None, :] ** np.arange(N)[:, None]; Am, *_ = np.linalg.lstsq(Z, X.T, rcond=None)
    err = np.linalg.norm(Z @ Am - X.T) / np.linalg.norm(X)
    g = -np.log(q) / (LAM * 1e-3); n = g.imag / k0; a = g.real * 8.686 / 100
    amp = np.sqrt(np.mean(abs(Am) ** 2, axis=1)); o_ = np.argsort(-amp)
    print(f" M={M} resid {err:.2f}: " + "; ".join(f"n {n[i]:+.3f} a {a[i]:6.1f} dB/cm amp {amp[i]:.2f}" for i in o_))
