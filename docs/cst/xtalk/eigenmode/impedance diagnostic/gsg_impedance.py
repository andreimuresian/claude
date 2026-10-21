"""GSG (signal vs its own tied grounds) impedance of line A, even and odd, from
the three eigenmodes of each symmetry (gold, 10 um cell, phase 0.6798 deg).

Per mode k: conductor potentials V_k = (V_s, V_g1, V_g2) relative to the PEC
side wall (y = 200 um), from E_y integrated along rows inside the metal, and
conductor currents I_k (Ampere loops). Multiconductor TL: Z = V I^-1 (3x3).
GSG launch: grounds tied (V_g1 = V_g2) and returning the full signal current
(I_g1 + I_g2 = -I_s)  ->  Z_GSG = (V_s - V_g)/I_s.
Approximation: the three modes share beta but sit at different frequencies
(even 25.66 / 27.00 / 28.86 GHz, odd 25.14 / 27.03 / 28.89 GHz)."""
import io, os, zipfile, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
G1, S, G2 = (28.5e-6, 78.35e-6), (82.5e-6, 117.5e-6), (121.65e-6, 171.5e-6)
def load(path):
    A = np.loadtxt(path, skiprows=2)
    x, y = np.unique(A[:, 0]), np.unique(A[:, 1])
    i = np.searchsorted(x, A[:, 0]); j = np.searchsorted(y, A[:, 1])
    F = np.zeros((len(x), len(y), 3), complex)
    for k in range(3):
        F[i, j, k] = A[:, 3 + 2*k] + 1j*A[:, 4 + 2*k]
    return x*1e-3, y*1e-3, F
def mode3(kind, tag):
    z = zipfile.ZipFile(os.path.join(HERE, "..", "mode3_fields_10um_cell_gold.zip"))
    return load(io.TextIOWrapper(z.open(f"Mode_3_{kind}_{tag}.txt")))
def potentials(x, y, E, rows=(0.5e-6, 1.0e-6)):
    out = []
    for xr in rows:
        ix = np.argmin(abs(x - xr)); e = E[ix, :, 1]; zero = np.abs(e) < 1e-9*np.abs(e).max()
        V = -np.concatenate([[0], np.cumsum(0.5*(e[1:] + e[:-1])*np.diff(y))]); V -= V[-1]
        ed = np.flatnonzero(np.diff(np.r_[0, zero.astype(int), 0]))
        c = [V[a:b].mean() for a, b in zip(ed[::2], ed[1::2])]
        if len(c) != 3:
            raise RuntimeError(f"row {xr}: {len(c)} conductors")
        out.append([c[1], c[0], c[2]])                       # order: s, g1, g2
    return np.mean(out, axis=0)
def loop(x, y, H, x0, x1, y0, y1):
    ix0, ix1 = np.argmin(abs(x - x0)), np.argmin(abs(x - x1))
    iy0, iy1 = np.argmin(abs(y - y0)), np.argmin(abs(y - y1))
    I = np.trapezoid(H[ix0, iy0:iy1+1, 1], y[iy0:iy1+1]) + np.trapezoid(H[ix0:ix1+1, iy1, 0], x[ix0:ix1+1])
    return I - np.trapezoid(H[ix1, iy0:iy1+1, 1], y[iy0:iy1+1]) - np.trapezoid(H[ix0:ix1+1, iy0, 0], x[ix0:ix1+1])
def currents(x, y, H):
    return np.array([loop(x, y, H, -1e-6, 3e-6, a - 1e-6, b + 1e-6) for a, b in (S, G1, G2)])
res = {}
for tag in ("even", "odd"):
    Vm, Im = [], []
    for m in (1, 2, 3):
        if m == 3:
            x, y, E = mode3("e", tag); _, _, H = mode3("h", tag)
        else:
            x, y, E = load(os.path.join(HERE, f"Mode_{m}_e_{tag}_gold.txt"))
            _, _, H = load(os.path.join(HERE, f"Mode_{m}_h_{tag}_gold.txt"))
        Vm.append(potentials(x, y, E)); Im.append(currents(x, y, H))
    V, I = np.array(Vm).T, np.array(Im).T                    # columns = modes
    Z = V @ np.linalg.inv(I)                                 # V = Z I, conductors s, g1, g2
    # I = I_s * [1, -a, -(1-a)];  V_g1 = V_g2  ->  solve for a
    d = Z[1] - Z[2]
    a = (d[0] - d[2]) / (d[1] - d[2])
    Iv = np.array([1, -a, -(1 - a)])
    Vv = Z @ Iv
    Zg = Vv[0] - Vv[1]
    res[tag] = Zg
    np.set_printoptions(precision=2, suppress=True)
    print(f"--- {tag}")
    print("Z matrix (ohm), conductors s/g1/g2:\n", Z)
    print(f"ground current split a (g1) = {a:.3f}   V_g/V_s = {Vv[1]/Vv[0]:.3f}")
    print(f"Z_GSG = {Zg.real:.2f} {Zg.imag:+.2f}j ohm  |Z| = {abs(Zg):.2f}")
print(f"\nZe/Zo - 1 (GSG) = {100*(abs(res['even'])/abs(res['odd']) - 1):+.3f} %   "
      f"(complex ratio {res['even']/res['odd']:.5f})")
