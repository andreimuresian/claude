"""30 GHz plane exports of the widened run (port 1 driven): which waves fill the structure?
V1: y = 0 (midway between the lines), V2: y = -0.3125 (through line B's centre), both x -0.527..0.103 mm;
H: x = 1 um, y -1.03..1.03. Matrix pencil along z (interior 0.3-7.7 mm, field components as channels,
4 waves) per row: index n (sign = direction: + toward the far end, - toward the near end),
loss a (dB/cm; for a backward wave a < 0 means it decays as it travels), relative amplitude."""
import os, io, zipfile, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); C0 = 2.99792458e8; k0 = 2 * np.pi * 30e9 / C0

def load(tag):
    with zipfile.ZipFile(os.path.join(HERE, f"e-field (f=30.0000) [1]_{tag}.zip")) as zf:
        a = np.loadtxt(io.TextIOWrapper(zf.open(zf.namelist()[0])), skiprows=2)
    ax = [np.unique(np.round(a[:, j], 6)) for j in range(3)]
    ii = [np.searchsorted(ax[j], np.round(a[:, j], 6)) for j in range(3)]
    E = np.zeros([len(u) for u in ax] + [3], complex); E[ii[0], ii[1], ii[2]] = a[:, 3::2] + 1j * a[:, 4::2]
    return ax, E

def pencil(X, dz, M=4):
    N = X.shape[1]; Lp = N // 2
    H = np.vstack([np.array([v[i:i + Lp + 1] for i in range(N - Lp)]) for v in X])
    _, S, Vh = np.linalg.svd(H, full_matrices=False)
    V = Vh[:M].T; q = np.linalg.eigvals(np.linalg.pinv(V[:-1]) @ V[1:])
    Z = q[None, :] ** np.arange(N)[:, None]; A, *_ = np.linalg.lstsq(Z, X.T, rcond=None)
    err = np.linalg.norm(Z @ A - X.T) / np.linalg.norm(X)
    g = -np.log(q) / dz; n = g.imag / k0; a = g.real * 8.686 / 100
    amp = np.sqrt(np.sum(abs(A) ** 2, axis=1)); o = np.argsort(-amp)
    return err, [(n[i], a[i], amp[i] / amp[o[0]]) for i in o]

fmt = lambda w: "; ".join(f"n {n:+.3f} a {a:5.1f} amp {m:.2f}" for n, a, m in w)
for tag, rows in (("V1", (0.10255, 0.00255, -0.00245, -0.04745, -0.19745, -0.29745, -0.39745, -0.52745)),
                  ("V2", (0.10255, 0.00255, -0.00245, -0.04745, -0.19745, -0.29745, -0.39745, -0.52745))):
    (x, y, z), E = load(tag); sel = (z >= 0.3) & (z <= 7.7)
    print(f"\n{tag}: y = {y[0]} mm")
    for xi in rows:
        i = np.argmin(abs(x - xi)); F = E[i, 0][sel][::9].T
        err, w = pencil(F / abs(F).max(), 45e-6)
        print(f"  x {x[i]*1e3:8.2f} um | rms |E| {np.sqrt(np.mean(abs(E[i,0][sel])**2)):.2e} V/m | resid {err:.2f}: {fmt(w)}")
(x, y, z), E = load("H"); sel = (z >= 0.3) & (z <= 7.7)
print("\nH: x = 1 um (Ex excluded: it jumps at the LN surface)")
for yi in (-1.0, -0.8, -0.6, -0.45, -0.40, -0.15, 0.0, 0.15, 0.40, 0.45, 0.6, 0.8, 1.0):
    j = np.argmin(abs(y - yi)); F = E[0, j][sel][::4][:, 1:].T
    err, w = pencil(F / abs(F).max(), 40e-6)
    print(f"  y {y[j]:+.3f} mm | rms |Ey| {np.sqrt(np.mean(abs(E[0,j][sel][:,1])**2)):.2e} V/m | resid {err:.2f}: {fmt(w)}")
