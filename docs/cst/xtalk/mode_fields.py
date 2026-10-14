"""Cross-section fields of a coupled pair (2-D electrostatics, textbook geometry:
two strips on a substrate over a ground plane). Illustration of even/odd modes."""
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spl
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
nx, ny, d = 321, 161, 1.0                       # grid (um-like units)
x = np.arange(nx)*d - (nx-1)/2*d; y = np.arange(ny)*d
X, Y = np.meshgrid(x, y)                        # Y[j,i]
h, w, s, t = 20, 24, 16, 2                      # substrate height, strip width, gap between strips, strip thickness
eps = np.where(Y < h, 10.0, 1.0)
def strip(xc): return (abs(X-xc) <= w/2) & (Y >= h) & (Y <= h+t)
mA, mB = strip(-(s+w)/2), strip((s+w)/2)
gnd = (Y == 0)
box = (X == x[0]) | (X == x[-1]) | (Y == y[-1])
def solve(vA, vB):
    fixed = mA | mB | gnd | box
    val = np.where(mA, vA, 0.0) + np.where(mB, vB, 0.0)
    N = nx*ny; idx = np.arange(N).reshape(ny, nx)
    rows, cols, data = [], [], []; b = np.zeros(N)
    for j in range(ny):
        for i in range(nx):
            k = idx[j, i]
            if fixed[j, i]:
                rows.append(k); cols.append(k); data.append(1.0); b[k] = val[j, i]; continue
            diag = 0.0
            for dj, di in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                jj, ii = j+dj, i+di
                e = 0.5*(eps[j, i] + eps[jj, ii])
                rows.append(k); cols.append(idx[jj, ii]); data.append(e); diag -= e
            rows.append(k); cols.append(k); data.append(diag)
    A = sp.csr_matrix((data, (rows, cols)), shape=(N, N))
    return spl.spsolve(A, b).reshape(ny, nx)
cases = [("drive A only:  (1, 0)", 1, 0), ("pair EVEN mode:  (1, 1)", 1, 1), ("pair ODD mode:  (1, −1)", 1, -1)]
fig, axs = plt.subplots(3, 1, figsize=(11, 11.5))
for ax, (title, va, vb) in zip(axs, cases):
    phi = solve(va, vb)
    Ey, Ex = np.gradient(-phi, d)
    E = np.hypot(Ex, Ey)
    im = ax.pcolormesh(X, Y, np.log10(E + 1e-4), cmap="inferno", vmin=-3, vmax=-0.5, shading="auto")
    ax.contour(X, Y, phi, levels=np.linspace(-0.95, 0.95, 20), colors="w", linewidths=0.5, alpha=0.6)
    ax.streamplot(x, y, Ex, Ey, color="#7fd3ff", density=1.3, linewidth=0.7, arrowsize=0.7)
    for m, v in ((mA, va), (mB, vb)):
        ax.contourf(X, Y, m.astype(float), levels=[0.5, 1.5], colors=["#c62828" if v > 0 else ("#1565c0" if v < 0 else "#bbbbbb")])
    ax.axhline(h, color="w", lw=0.8, ls="--"); ax.axvline(0, color="#7fff7f", lw=1, ls=":")
    ax.set_xlim(-110, 110); ax.set_ylim(0, 75); ax.set_aspect("equal"); ax.set_title(title, fontsize=12)
    ax.set_xticks([]); ax.set_yticks([])
axs[1].text(0, 70, "symmetry plane: no field crosses it\n(magnetic wall)", color="#7fff7f", ha="center", va="top", fontsize=9)
axs[2].text(0, 70, "symmetry plane at 0 V: field crosses it\n(electric wall)", color="#7fff7f", ha="center", va="top", fontsize=9)
fig.text(0.5, 0.01, "Colour: |E| (log). Blue lines: electric field lines. White: equipotentials. Dashed: substrate surface (εr = 10 below, air above).\n"
         "Textbook geometry (two strips over a ground plane), spacing exaggerated for visibility. In the odd mode more field sits in the air gap\n"
         "between the strips, in the even mode more in the substrate: different effective index and impedance, so the two modes drift apart.",
         ha="center", fontsize=9.5)
plt.tight_layout(rect=(0, 0.06, 1, 1)); plt.savefig("mode_fields.png", dpi=130)
