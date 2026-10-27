"""
Wave extraction from the E and H planes (x = 1 um, y -0.40..0.40, z 0..5 mm).
Channels: Ex, Ey, eta0*Hx, eta0*Hy at every y with a non-zero field, averaged over the
200 um cell, z restricted to the uniform interior, every 5th sample (dz = 25 um).
Count: singular values of the stacked Hankel matrices. beta and direction: shift
invariance (matrix pencil). Check: sign of each wave's own power flow
P_z = Re sum_y (Ex Hy* - Ey Hx*) against the direction given by beta.
"""
import sys, numpy as np
ETA0 = 376.730313668
W = 40
def cav(v): return np.convolve(v, np.ones(W) / W, mode="valid")

def channels(fG, zr=(0.3, 4.7), dec=5, ysel=None):
    d = np.load(f"/tmp/claude-0/-home-user-claude/7930b8bd-7239-59e6-a8de-284bb11bf7ea/scratchpad/eh/eh_{fG}.npz")
    ys, zs, E, H = d["ys"], d["zs"], d["E"], d["H"]
    zc = cav(zs); idx = np.where((zc > zr[0]) & (zc < zr[1]))[0][::dec]
    raw, info = [], []
    for j in range(len(ys)):
        if ysel is not None and not ysel(ys[j]): continue
        comps = [cav(E[j, :, 0])[idx], cav(E[j, :, 1])[idx], ETA0 * cav(H[j, :, 0])[idx], ETA0 * cav(H[j, :, 1])[idx]]
        if max(np.max(abs(c)) for c in comps) == 0: continue
        for c, v in enumerate(comps):
            raw.append(v); info.append((j, c))
    return ys, zc[idx], np.array(raw), info

def pencil(raw, dz, M):
    nrm = np.sqrt(np.mean(abs(raw) ** 2, axis=1)); nrm[nrm == 0] = 1
    X = raw / nrm[:, None]
    N = X.shape[1]; Lp = N // 2
    Hk = np.vstack([np.array([v[i:i + Lp + 1] for i in range(N - Lp)]) for v in X])
    _, Sv, Vh = np.linalg.svd(Hk, full_matrices=False)
    V = Vh[:M].T
    q = np.linalg.eigvals(np.linalg.pinv(V[:-1]) @ V[1:])
    Z = q[None, :] ** np.arange(N)[:, None]
    A, *_ = np.linalg.lstsq(Z, raw.T, rcond=None)           # amplitudes per channel (physical units)
    err = np.linalg.norm(Z @ A - raw.T) / np.linalg.norm(raw)
    return q, A, err, Sv / Sv[0]

def analyse(fG, Ms=(3, 4, 5, 6)):
    ys, z, raw, info = channels(fG)
    dz = (z[1] - z[0]) * 1e-3
    k0 = 2 * np.pi * fG * 1e9 / 2.99792458e8
    q, A, err, sv = pencil(raw, dz, 2)
    print(f"\n=== {fG} GHz: {len(raw)} channels; singular values {np.round(sv[:8], 3)}")
    jj = np.array([i[0] for i in info]); cc = np.array([i[1] for i in info])
    out = {}
    for M in Ms:
        q, A, err, _ = pencil(raw, dz, M)
        rows = []
        for m in range(M):
            s = np.log(q[m]) / dz                               # e^{s z}
            n = -s.imag / k0; a_dBcm = -s.real * 8.686 / 100    # n>0: forward (+z), a>0: decays along +z
            amp = A[m]
            Ex = np.zeros(len(ys), complex); Ey = Ex.copy(); Hx = Ex.copy(); Hy = Ex.copy()
            for val, j, c in zip(amp, jj, cc):
                [Ex, Ey, Hx, Hy][c][j] = val
            Pz = np.sum(np.real(Ex * np.conj(Hy / ETA0) - Ey * np.conj(Hx / ETA0)))
            dir_beta = np.sign(n); dir_P = np.sign(Pz)
            # wave strength: rms E over the plane at the reference z
            w = np.sqrt(np.mean(abs(Ex) ** 2 + abs(Ey) ** 2))
            rows.append((n, a_dBcm, w, dir_beta == dir_P, Pz))
        rows.sort(key=lambda r: -r[2])
        out[M] = (err, rows)
        print(f"  M={M} residual {err:.4f}: " + "  ".join(
            f"[n={r[0]:+.3f} a={r[1]:+5.1f} |E|={r[2]:.3g} {'ok' if r[3] else 'DIR?'}]" for r in rows))
    return out

if __name__ == "__main__":
    for fG in [int(a) for a in sys.argv[1:]] or [10, 20, 30, 45, 60, 80]:
        analyse(fG)
