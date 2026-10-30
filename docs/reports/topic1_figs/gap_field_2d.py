"""
Electrostatic (quasi-static) field of the CORDOBA cross-section without T slots, 2D finite
volume: div(eps grad phi) = 0, signal at 1 V, grounds at 0 V. Geometry and permittivities from
the CST history and s4p header: signal 35 um, gap 4.15 um, ground 49.85 um, Au 2 um (perfect
conductor here), LN 0.2 um (eps_x = 43 vertical, eps_y = 28 lateral), SiO2 4.7 um (3.9),
Si 525 um (11.9), no rib. One line, mirror plane at the signal centre (y = 0); the outer
boundary (0 V) is 400 um away. x = 0 is the LN top, as in CST.

Prints how E_y varies across the gap and with height, and saves f5_gapfield.png.
"""
import os
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

HERE = os.path.dirname(os.path.abspath(__file__))
WS2, G, WG, T = 17.5, 4.15, 49.85, 2.0          # um
Y_SIG, Y_GND, Y_OUT = WS2, WS2 + G, WS2 + G + WG
X_LN, X_OX, X_SI = -0.2, -4.9, -529.9


def axis(lo, hi, pts, fine_lo, fine_hi, h=0.02, grow=1.08):
    """Nodes from lo to hi: step h inside [fine_lo, fine_hi], growing geometrically outside;
    every value in *pts* is a node."""
    def run(a, b, h0):                               # from a towards b, start step h0
        out, x, s = [a], a, h0
        d = np.sign(b - a)
        while abs(b - x) > s * 1.5:
            x += d * s; out.append(x); s *= grow
        out.append(b); return out
    left = run(fine_lo, lo, h)[::-1]
    mid = list(np.linspace(fine_lo, fine_hi, int(round((fine_hi - fine_lo) / h)) + 1))
    right = run(fine_hi, hi, h)
    n = np.unique(np.round(np.array(left + mid + right + list(pts)), 6))
    return n


y = axis(0.0, 400.0, [Y_SIG, Y_GND, Y_OUT], Y_SIG - 1.0, Y_GND + 1.0)
x = axis(-600.0, 400.0, [0.0, T, X_LN, X_OX, X_SI], X_LN - 0.3, T + 0.5)
ny, nx = len(y), len(x)
# cell permittivities (cells between nodes), cell centre decides the material
xc, yc = 0.5 * (x[1:] + x[:-1]), 0.5 * (y[1:] + y[:-1])
XC, YC = np.meshgrid(xc, yc, indexing="ij")
ex = np.ones_like(XC); ey = np.ones_like(XC)
ln = (XC < 0) & (XC > X_LN); ex[ln], ey[ln] = 43.0, 28.0
ox = (XC < X_LN) & (XC > X_OX); ex[ox] = ey[ox] = 3.9
si = (XC < X_OX) & (XC > X_SI); ex[si] = ey[si] = 11.9
# node classes
X, Y = np.meshgrid(x, y, indexing="ij")
metal = (X >= 0) & (X <= T)
sig = metal & (Y <= Y_SIG); gnd = metal & (Y >= Y_GND) & (Y <= Y_OUT)
outer = (X == x[0]) | (X == x[-1]) | (Y == y[-1])
fixed = sig | gnd | outer
val = np.where(sig, 1.0, 0.0)
idx = -np.ones((nx, ny), int); free = ~fixed
idx[free] = np.arange(free.sum())
rows, cols, data = [], [], []; b = np.zeros(free.sum())
dxm = np.diff(x); dym = np.diff(y)
for i in range(nx):
    for j in range(ny):
        k = idx[i, j]
        if k < 0:
            continue
        diag = 0.0
        # neighbours: (di, dj, coefficient); coefficient = eps_face * dual_length / spacing
        nb = []
        hy_lo = dym[j - 1] if j > 0 else 0.0; hy_hi = dym[j] if j < ny - 1 else 0.0
        hx_lo = dxm[i - 1] if i > 0 else 0.0; hx_hi = dxm[i] if i < nx - 1 else 0.0
        if i < nx - 1:   # +x link: cells (i, j-1) and (i, j)
            e = (ex[i, j - 1] * hy_lo if j > 0 else 0) + (ex[i, j] * hy_hi if j < ny - 1 else 0)
            nb.append((i + 1, j, 0.5 * e / dxm[i]))
        if i > 0:
            e = (ex[i - 1, j - 1] * hy_lo if j > 0 else 0) + (ex[i - 1, j] * hy_hi if j < ny - 1 else 0)
            nb.append((i - 1, j, 0.5 * e / dxm[i - 1]))
        if j < ny - 1:
            e = (ey[i - 1, j] * hx_lo if i > 0 else 0) + (ey[i, j] * hx_hi if i < nx - 1 else 0)
            nb.append((i, j + 1, 0.5 * e / dym[j]))
        if j > 0:        # j = 0 is the mirror plane: no link beyond it (zero flux)
            e = (ey[i - 1, j - 1] * hx_lo if i > 0 else 0) + (ey[i, j - 1] * hx_hi if i < nx - 1 else 0)
            nb.append((i, j - 1, 0.5 * e / dym[j - 1]))
        for (ii, jj, c) in nb:
            diag += c
            kk = idx[ii, jj]
            if kk >= 0:
                rows.append(k); cols.append(kk); data.append(-c)
            else:
                b[k] += c * val[ii, jj]
        rows.append(k); cols.append(k); data.append(diag)
A = sp.csr_matrix((data, (rows, cols)), shape=(free.sum(), free.sum()))
phi = val.copy(); phi[free] = spl.spsolve(A, b)

# E_y = -dphi/dy on y midpoints
Ey = -(phi[:, 1:] - phi[:, :-1]) / dym[None, :] * 1e6          # V/m for 1 V
E0 = 1.0 / (G * 1e-6)                                           # V/g, uniform-field value
ycen = Y_SIG + G / 2
jc = np.argmin(abs(yc - ycen))
def Ey_at(xv, yv):
    i = np.argmin(abs(x - xv)); j = np.argmin(abs(yc - yv)); return Ey[i, j]
gap = (yc > Y_SIG) & (yc < Y_GND)
i1 = np.argmin(abs(x - 1.0))
V_check = np.sum(Ey[i1, gap] * dym[gap]) * 1e-6
print(f"grid {nx} x {ny};  line integral across the gap at x = 1 um: {V_check:.4f} V (expected 1)")
print(f"E_y / (V/g) at the gap centre (y = gap centre):")
for xv in (2.0, 1.5, 1.0, 0.5, 0.2, 0.1, 0.02, -0.1):
    print(f"   x = {xv:5.2f} um : {Ey_at(xv, ycen) / E0:.3f}")
print("E_y / (V/g) across the gap at x = 1 um (distance from the signal edge):")
for d in (0.05, 0.25, 0.5, 1.0, 2.075, 3.15, 3.65, 3.9, 4.1):
    print(f"   {d:5.3f} um : {Ey_at(1.0, Y_SIG + d) / E0:.3f}")
print(f"E_y(x=0.1)/E_y(x=1) at the gap centre: {Ey_at(0.1, ycen) / Ey_at(1.0, ycen):.4f}")
print(f"E_y(x=1, centre) * g = {Ey_at(1.0, ycen) * G * 1e-6:.4f} V  (true V = 1)")

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
sel = (x >= -0.4) & (x <= 2.6); sy = (yc >= Y_SIG - 0.5) & (yc <= Y_GND + 0.5)
m = ax[0].pcolormesh(yc[sy] - Y_SIG, x[sel], Ey[np.ix_(sel, sy)] / E0, vmin=0, vmax=2, cmap="viridis", shading="auto")
for (a0, a1) in ((-0.5, 0), (G, G + 0.5)):
    ax[0].add_patch(plt.Rectangle((a0, 0), a1 - a0, T, color="#d9b13b"))
ax[0].axhline(0, color="w", lw=0.6, ls=":"); ax[0].axhline(-0.2, color="w", lw=0.6, ls=":")
ax[0].plot([G / 2], [1.0], "o", color="#2a78d6", mec="w"); ax[0].plot([G / 2], [0.1], "s", color="#eb6834", mec="w")
ax[0].set_xlabel("distance from the signal edge (um)"); ax[0].set_ylabel("height x (um)")
fig.colorbar(m, ax=ax[0], label="E_y / (V/g)")
for xv, c, lab in ((1.0, "#2a78d6", "x = 1 um (sample height)"), (0.1, "#eb6834", "x = 0.1 um (rib height)")):
    i = np.argmin(abs(x - xv)); ax[1].plot(yc[gap] - Y_SIG, Ey[i, gap] / E0, color=c, lw=2, label=lab)
ax[1].axhline(1, color="0.5", ls="--", lw=1, label="uniform field V/g")
ax[1].set_xlabel("distance from the signal edge (um)"); ax[1].set_ylabel("E_y / (V/g)")
ax[1].set_ylim(0, 2.5); ax[1].legend(frameon=False, fontsize=8); ax[1].grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "f5_gapfield.png"), dpi=150)
