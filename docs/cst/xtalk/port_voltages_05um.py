"""Line voltages (signal minus mean of its two grounds) of CST port modes 5/6
from the 0.5 um sub-volume exports. Only differences across gaps are needed, so
the sub-volume need not reach the port frame."""
import io, zipfile, numpy as np
for m in (5, 6):
    z = zipfile.ZipFile(f"2D port simulation/Port1_e{m}_30_0.5um.zip")
    A = np.loadtxt(io.TextIOWrapper(z.open(z.namelist()[0])), skiprows=2, usecols=(0, 1, 5, 6))
    for xr in (0.0005, 0.0010, 0.0015, 0.0020):                 # rows inside the 2 um metal
        r = A[np.isclose(A[:, 0], xr)]; r = r[np.argsort(r[:, 1])]
        y = r[:, 1]*1e-3; e = r[:, 2] + 1j*r[:, 3]; zero = e == 0
        V = -np.concatenate([[0], np.cumsum(0.5*(e[1:]+e[:-1])*np.diff(y))])
        ed = np.flatnonzero(np.diff(np.r_[0, zero.astype(int), 0]))
        Vc = [V[a:b].real.mean() for a, b in zip(ed[::2], ed[1::2])]
        LA, LB = Vc[1]-(Vc[0]+Vc[2])/2, Vc[4]-(Vc[3]+Vc[5])/2
        print(f"mode {m} x={xr*1e3:.1f} um  line A {LA:.4f}  line B {LB:.4f}  sum V^2 {LA**2+LB**2:.3f}")
