"""
Echo decomposition of NEXT (S31) for each length: matrix pencil on the
frequency samples, y(f) = sum_k r_k exp(-j 2 pi f tau_k - d_k f). Each tau_k
is the travel time of one path. Paths expected for a line of length L:
  CPW out and back      tau = (n_c + n_c) L / c
  CPW out, wave x back  tau = (n_c + n_x) L / c
  wave x out and back   tau = (n_x + n_x) L / c
Fitting tau vs L across lengths gives the sum of the two group indices of each
path, independently of the port regions (they only add an offset).
"""
import sys, os, numpy as np, skrf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sector_fit import FILES
UP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = 0.299792458                       # mm/ps

def mpencil(y, dz, M):
    N = len(y); Lp = N // 3
    Y = np.array([y[i:i + Lp + 1] for i in range(N - Lp)])
    _, S, Vh = np.linalg.svd(Y, full_matrices=False)
    V = Vh[:M].T
    lam = np.linalg.eigvals(np.linalg.pinv(V[:-1]) @ V[1:])
    s = np.log(lam) / dz
    Z = np.exp(np.outer(np.arange(N) * dz, s))
    r, *_ = np.linalg.lstsq(Z, y, rcond=None)
    return s, r, np.linalg.norm(Z @ r - y) / np.linalg.norm(y)

def echoes(L, band, M, k=(2, 0)):
    n = skrf.Network(os.path.join(UP, FILES[L]))
    sel = (n.f >= band[0] * 1e9) & (n.f <= band[1] * 1e9)
    f = n.f[sel]; y = n.s[sel, k[0], k[1]]
    s, r, err = mpencil(y, f[1] - f[0], M)
    tau = -s.imag / (2 * np.pi) * 1e12
    amp = np.abs(r * np.exp(s * f[0]))                     # amplitude at the band start
    o = np.argsort(-amp)
    return tau[o], amp[o], err

if __name__ == "__main__":
    Ls = [3.0, 5.0, 8.75]
    for band in ((5, 60), (10, 50), (5, 70)):
        for M in (5, 6, 8):
            rows = {L: echoes(L, band, M) for L in Ls}
            # the three strongest echoes of each length, sorted by delay
            trip = {L: np.sort(rows[L][0][:3]) for L in Ls}
            slopes = [np.polyfit(Ls, [trip[L][j] for L in Ls], 1)[0] for j in range(3)]
            print(f"band {band[0]:2d}-{band[1]:2d} GHz, M={M}: " +
                  "  ".join(f"L={L}: {trip[L][0]:6.1f} {trip[L][1]:6.1f} {trip[L][2]:6.1f}" for L in Ls) +
                  "   | n-sum per path: " + " ".join(f"{s * C:5.2f}" for s in slopes))
    print("\nthrough (S21) main echo, band 5-60 GHz, M=6:")
    t = [echoes(L, (5, 60), 6, k=(1, 0))[0][0] for L in Ls]
    print("  ", [round(x, 1) for x in t], " n_g =", round(np.polyfit(Ls, t, 1)[0] * C, 3))
