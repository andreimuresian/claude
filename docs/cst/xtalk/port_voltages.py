"""Conductor voltages of CST port modes 5 and 6 (30 GHz) from the 1 um field
exports in '2D port simulation/*.zip'. Integrates Ey along y on the two grid
rows inside the 2 um metal (x = 0.5, 1.5 um), starting at the PEC port frame."""
import io, zipfile, numpy as np
D = "2D port simulation/Port1_e{}_30_1um.zip"
for m in (5, 6):
    z = zipfile.ZipFile(D.format(m)); A = np.loadtxt(io.TextIOWrapper(z.open(z.namelist()[0])), skiprows=2, usecols=(0, 1, 5, 6))
    for xr in (0.0005, 0.0015):
        r = A[np.isclose(A[:, 0], xr)]; r = r[np.argsort(r[:, 1])]
        y = r[:, 1]*1e-3; e = r[:, 2] + 1j*r[:, 3]
        V = -np.concatenate([[0], np.cumsum(0.5*(e[1:]+e[:-1])*np.diff(y))])
        zero = e == 0; edges = np.flatnonzero(np.diff(np.r_[0, zero.astype(int), 0]))
        Vc = [V[a:b].real.mean() for a, b in zip(edges[::2], edges[1::2])]   # G S G  G S G
        line = [Vc[1]-(Vc[0]+Vc[2])/2, Vc[4]-(Vc[3]+Vc[5])/2]
        print(f"mode {m} x={xr*1e3:.1f} um  conductors {np.round(Vc,3)}  line A {line[0]:.3f}  line B {line[1]:.3f}")
