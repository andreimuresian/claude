"""Even/odd line impedance of the uniform 200 um pitch line from CST eigenmode
fields (10 um periodic cell, symmetry plane y = 0, line A at y = +100 um).
Exports: mode 3 E and H on z = 5 um, x -60..60 um, y 0..200 um, step 0.5 um.

Per mode: V = gap voltage (signal minus mean of its own grounds), from the line
integral of E_y across y on rows inside the metal height (as port_voltages_sweep.py);
P = 1/2 Re int (E x H*)_z dA over the half domain (= power carried by line A);
Z = |V|^2 / (2 P). CST's eigenmode normalisation cancels."""
import numpy as np
import io, os, zipfile
import sys
ZIP = sys.argv[1] if len(sys.argv) > 1 else "mode3_fields_10um_cell.zip"
def load(fn):
    if not os.path.exists(fn):
        fn = io.TextIOWrapper(zipfile.ZipFile(ZIP).open(fn))
    A = np.loadtxt(fn, skiprows=2)
    x, y = np.unique(A[:, 0]), np.unique(A[:, 1])
    i = np.searchsorted(x, A[:, 0]); j = np.searchsorted(y, A[:, 1])
    F = np.zeros((len(x), len(y), 3), complex)
    for k in range(3):
        F[i, j, k] = A[:, 3 + 2*k] + 1j*A[:, 4 + 2*k]
    return x*1e-3, y*1e-3, F
def analyse(tag):
    x, y, E = load(f"Mode_3_e_{tag}.txt"); _, _, H = load(f"Mode_3_h_{tag}.txt")
    Sz = 0.5*np.real(E[..., 0]*np.conj(H[..., 1]) - E[..., 1]*np.conj(H[..., 0]))
    P = abs(np.trapezoid(np.trapezoid(Sz, y, axis=1), x))   # sign = direction of travel
    Sz = np.abs(Sz)
    rows = []
    for xr in (0.5e-6, 1.0e-6, 1.5e-6):
        ix = np.argmin(abs(x - xr)); e = E[ix, :, 1]; zero = np.abs(e) < 1e-9*np.abs(e).max()
        V = -np.concatenate([[0], np.cumsum(0.5*(e[1:] + e[:-1])*np.diff(y))])
        ed = np.flatnonzero(np.diff(np.r_[0, zero.astype(int), 0]))
        Vc = [V[a:b].mean() for a, b in zip(ed[::2], ed[1::2])]
        if len(Vc) != 3:
            raise RuntimeError(f"{tag} row {xr}: found {len(Vc)} conductors")
        rows.append(Vc[1] - (Vc[0] + Vc[2])/2)
    V = np.array(rows)
    return P, V, np.abs(V)**2/(2*P), Sz, x, y
Pe, Ve, Ze, Se, x, y = analyse("even"); Po, Vo, Zo, So, _, _ = analyse("odd")
print("rows x = 0.5/1.0/1.5 um")
print("Z_even (ohm):", np.round(Ze, 3))
print("Z_odd  (ohm):", np.round(Zo, 3))
print("Ze/Zo - 1 (%):", np.round(100*(Ze/Zo - 1), 3), " mean %.3f %%" % (100*np.mean(Ze/Zo - 1)))
# power inside the window vs near the edges (tail check)
for tag, S in (("even", Se), ("odd", So)):
    tot = np.trapezoid(np.trapezoid(S, y, axis=1), x)
    inner = np.abs(x) <= 40e-6
    pin = np.trapezoid(np.trapezoid(S[inner], y, axis=1), x[inner])
    print(f"{tag}: power within |x| <= 40 um = {100*pin/tot:.2f} % of the +-60 um window; "
          f"S_z at window edge x=-60um / max = {np.abs(S[0]).max()/np.abs(S).max():.1e}")
