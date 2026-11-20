"""H-field analysis of the 10+5+5 mm run (EL_L 10.08, EL_L2 = EL_L3 5.04 mm), 0-130 GHz.

Current on the signal electrode: Ampere loop I = closed integral of H.dl in each exported plane, rectangle through the
two gap centres and along the outermost rows of the plane below and above the electrode that contain field everywhere.
  plane z = const (coordinates x, y): I_z = int Hx(y0) dx + int Hy(x1) dy - int Hx(y1) dx - int Hy(x0) dy
  plane y = const (bend apex, coordinates z, x): I_y = int Hz(x0) dz + int Hx(z1) dx - int Hz(x1) dz - int Hx(z0) dx
  sign: current counted along the direction of travel (L1, L3, raised L1/L3: +z; L2 and raised L2: -z; apexes: +y).
Voltage (signal to ground, mean of the two gaps):
  lines: point field at the gap centre x GAP; in each 0.18 mm cell the samples of the 20 um aperture (wider gap, lower field)
         are excluded (the 6 lowest |V| of every 36-sample window) -> voltage across the 4.45 um gap; forward/backward fit
         with gamma free; V and the wave amplitudes at the plane positions.
  raised straights: point field of the raised gap lines at the plane (gap 4.8 um, no apertures there).
  bend apexes (90 deg, grid-aligned): line integral of the radial field across each gap from the bend maps.
Results: Zc = (V+ e^{-g z} - V- e^{+g z}) / I on the lines (wave impedance, port-independent), compared with the L+S touchstone
Zc; net power P = 1/2 Re(V I*) at every plane along the path (standing waves do not change the net power), hence the loss
between consecutive planes. Outputs: h_field_analysis.npz, printed tables."""
import os, io, glob, zipfile, sys, contextlib, runpy, numpy as np, pandas as pd
from scipy.optimize import least_squares
HERE = os.path.dirname(os.path.abspath(__file__)); C0 = 299792458.0
D = os.path.join(HERE, "..", "full equalizer 10+5+5"); RB, WS, G1, G2, CLAD, MTX = 0.1025, 0.0347, 4.45e-6, 4.8e-6, 0.0036, 0.002
L1, L2, L3, TL = 10.08, 5.04, 5.04, 0.22434; ZB1, ZB2 = L1 + 0.05 + TL, L1 - L2 - 0.05 - TL
LINES = {"L1": (0.0, L1, +1, -RB), "L2": (L1 - L2, L1, -1, RB), "L3": (L1 - L3, L1, +1, 3 * RB)}
def plane(fn):
    d = pd.read_csv(os.path.join(D, fn), sep=r"\s+", skiprows=2, header=None).to_numpy(); F = np.unique(d[:, 0])
    return F, d
def grid(d, F, a, b):
    """field arrays H[f, ia, ib] on the plane coordinates (column indices a, b)."""
    A, B = np.unique(np.round(d[:, a], 6)), np.unique(np.round(d[:, b], 6)); iF = np.searchsorted(F, d[:, 0])
    ia, ib = np.searchsorted(A, np.round(d[:, a], 6)), np.searchsorted(B, np.round(d[:, b], 6))
    H = {}
    for k, c in (("x", 4), ("y", 6), ("z", 8)):
        h = np.zeros((len(F), len(A), len(B)), complex); h[iF, ia, ib] = d[:, c] + 1j * d[:, c + 1]; H[k] = h
    return A, B, H
def edges(X, H):
    """outermost x rows that contain field over the whole width (below and above the electrode, inside the monitor)."""
    full = [k for k in range(len(X)) if np.all(abs(H["x"][-1, k]) + abs(H["y"][-1, k]) + abs(H["z"][-1, k]) > 0)]
    return full[0], full[-1]
def loop_z(fn, yc, dyg, x0, x1):
    F, d = plane(fn); X, Y, H = grid(d, F, 1, 2); y0, y1 = np.argmin(abs(Y - (yc - dyg))), np.argmin(abs(Y - (yc + dyg)))
    i0, i1 = edges(X, H); xs, ys = X[i0:i1 + 1] * 1e-3, Y[y0:y1 + 1] * 1e-3
    I = (np.trapezoid(H["x"][:, i0:i1 + 1, y0], xs, axis=1) + np.trapezoid(H["y"][:, i1, y0:y1 + 1], ys, axis=1)
         - np.trapezoid(H["x"][:, i0:i1 + 1, y1], xs, axis=1) - np.trapezoid(H["y"][:, i0, y0:y1 + 1], ys, axis=1))
    return F, I
def loop_y(fn, zc, dzg, x0, x1):
    F, d = plane(fn); X, Z, H = grid(d, F, 1, 3); z0, z1 = np.argmin(abs(Z - (zc - dzg))), np.argmin(abs(Z - (zc + dzg)))
    i0, i1 = edges(X, H); xs, zs = X[i0:i1 + 1] * 1e-3, Z[z0:z1 + 1] * 1e-3
    I = (np.trapezoid(H["z"][:, i0, z0:z1 + 1], zs, axis=1) + np.trapezoid(H["x"][:, i0:i1 + 1, z1], xs, axis=1)
         - np.trapezoid(H["z"][:, i1, z0:z1 + 1], zs, axis=1) - np.trapezoid(H["x"][:, i0:i1 + 1, z0], xs, axis=1))
    return F, I
dyb, dyr = WS / 2 + 0.00445 / 2, WS / 2 + 0.0048 / 2
# ---------------- lines: current (mean of the 3 planes in one cell) and voltage waves
def load_line(fn):
    d = np.loadtxt(os.path.join(D, fn), skiprows=2); fr = np.unique(d[:, 0]); z = d[d[:, 0] == fr[0], 3]
    o = np.argsort(z); return fr, z[o], (d[:, 6] + 1j * d[:, 7]).reshape(len(fr), len(z))[:, o]
LS = np.load(os.path.join(HERE, "ls_extraction_130.npz"))
def two(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]; return c, M @ c - vv
def no_aperture(v, win=36, drop=6):
    out = np.empty(len(v) - win + 1, complex)
    for j in range(len(out)):
        seg = v[j:j + win]; out[j] = seg[np.argsort(abs(seg))[drop:]].mean()
    return out
RES = {}
for ln, (z0, z1, dr, yc) in LINES.items():
    F, z, Ep = load_line(f"{ln}_gap+.txt"); _, _, Em = load_line(f"{ln}_gap-.txt"); V = G1 / 2 * (Ep - Em); w = 2 * np.pi * F * 1e9
    zs = np.convolve(z, np.ones(36) / 36, "valid"); s = (zs - z0) if dr > 0 else (z1 - zs); m = (zs >= z0 + 0.18) & (zs <= z1 - 0.18); s = s * 1e-3
    Is = [loop_z(f"H_{ln}_xs{k}.txt", yc, dyb, -0.001, 0.003)[1] * dr for k in range(3)]
    zp = np.array([float(open(os.path.join(D, f"H_{ln}_xs{k}.txt")).readline().split("z ")[1].split(" ..")[0]) for k in range(3)])
    sp = ((zp - z0) if dr > 0 else (z1 - zp)).mean() * 1e-3; I = np.mean(Is, 0); spread = np.std(np.abs(Is), 0) / abs(I)
    Zc, Zc_avg, Vp = np.zeros(len(F), complex), np.zeros(len(F), complex), np.zeros(len(F), complex)
    for i in range(len(F)):
        g0 = [np.interp(F[i], LS["F"], LS["aF"]) * 100 / 8.686, np.interp(F[i], LS["F"], LS["nF"]) * w[i] / C0]
        for kind in ("noap", "avg"):
            vv = (no_aperture(V[i]) if kind == "noap" else np.convolve(V[i], np.ones(36) / 36, "valid"))[m]
            r = lambda p: np.r_[(e := two(p[0] + 1j * p[1], s[m], vv)[1]).real, e.imag]
            p = least_squares(r, g0, x_scale=[max(g0[0], 1), g0[1]]).x; g = p[0] + 1j * p[1]; c, _ = two(g, s[m], vv)
            fw, bw = c[0] * np.exp(-g * sp), c[1] * np.exp(g * sp)
            if kind == "noap": Zc[i] = (fw - bw) / I[i]; Vp[i] = fw + bw
            else: Zc_avg[i] = (fw - bw) / I[i]
    RES[ln] = dict(F=F, I=I, spread=spread, Zc=Zc, Zc_avg=Zc_avg, V=Vp, P=0.5 * np.real(Vp * np.conj(I)), s=sp)
with contextlib.redirect_stdout(io.StringIO()):
    lb = runpy.run_path(os.path.join(HERE, "lbs_bend_130.py"))
_, Zts = lb["line"](F)
print("Zc of the lines from the H-field current (cell-mean of 3 planes) vs L+S touchstone Zc (smooth fit)")
print(" f GHz | Re Zc L1 / L2 / L3 (H) | Im Zc L1 / L2 / L3 | touchstone Re / Im | Re Zc with cell-averaged V (L1) | current spread over 3 planes (L1)")
for q in (2, 5, 10, 20, 40, 60, 80, 100, 120, 130):
    i = np.argmin(abs(F - q))
    print(f"{F[i]:5.0f} | " + " / ".join(f"{RES[l]['Zc'][i].real:5.1f}" for l in LINES) + " | " + " / ".join(f"{RES[l]['Zc'][i].imag:+5.1f}" for l in LINES)
          + f" | {Zts[i].real:5.1f} / {Zts[i].imag:+5.1f} | {RES['L1']['Zc_avg'][i].real:5.1f} | {100*RES['L1']['spread'][i]:.1f} %")
for l in LINES:
    mm = F >= 10; print(f"{l}: Re Zc (H) - touchstone, 10-130 GHz: mean {np.mean((RES[l]['Zc']-Zts).real[mm]):+.2f} ohm, rms {np.sqrt(np.mean(((RES[l]['Zc']-Zts).real[mm])**2)):.2f}; Im mean {np.mean((RES[l]['Zc']-Zts).imag[mm]):+.2f}")
# ---------------- raised straights and bend apexes: voltage and current
def raised(name_e, fn_h, yc, zpl, dr):
    _, z, Ep = load_line(f"{name_e}_gap+.txt"); _, _, Em = load_line(f"{name_e}_gap-.txt"); V = G2 / 2 * (Ep - Em)
    Vz = np.array([np.interp(zpl, z, v.real) + 1j * np.interp(zpl, z, v.imag) for v in V])
    _, I = loop_z(fn_h, yc, dyr, CLAD - 0.001, CLAD + MTX + 0.001); return Vz, I * dr
zr1 = L1 + 0.05 + TL / 2; zr2 = L1 - L2 - 0.05 - TL / 2
CACHE = os.path.join(HERE, "cache", "long_bend_apex.npz")
if not os.path.exists(CACHE):
    out = {}
    for nm, yap in (("BEND1", 0.0), ("BEND2", 2 * RB)):
        zf = zipfile.ZipFile(io.BytesIO(b"".join(open(p, "rb").read() for p in sorted(glob.glob(os.path.join(D, nm + ".zip.0*"))))))
        rows = []
        for ch in pd.read_csv(zf.open(nm + ".txt"), sep=r"\s+", skiprows=2, header=None, chunksize=2_000_000):
            a = ch.to_numpy(); rows.append(a[abs(a[:, 2] - yap) < 1e-7])
        out[nm] = np.concatenate(rows)
    os.makedirs(os.path.dirname(CACHE), exist_ok=True); np.savez(CACHE, **out)
AP = np.load(CACHE)
def apex_V(nm, zc, sgn):
    a = AP[nm]; Fa = np.unique(a[:, 0]); Vc = []
    for f in Fa:
        b = a[a[:, 0] == f]; o = np.argsort(b[:, 3]); z, Ez = b[o, 3], b[o, 8] + 1j * b[o, 9]
        r = sgn * (z - zc); Er = sgn * Ez                                   # radial coordinate and component
        vin, vout = [], []
        for rg in (RB - 0.01975, RB + 0.01975):
            k = abs(r - rg) <= 0.0036; o2 = np.argsort(r[k]); val = np.trapezoid(Er[k][o2], r[k][o2] * 1e-3)
            (vin if rg < RB else vout).append(val)
        Vc.append((-vin[0] + vout[0]) / 2)
    return np.array(Vc)
PTS = []
PTS.append(("L1 (mid)", RES["L1"]["V"], RES["L1"]["I"]))
PTS.append(("raised L1", *raised("L1_taper", "H_raised_L1.txt", -RB, zr1, +1)))
_, Ia = loop_y("H_bend1_apex.txt", ZB1 + RB, dyr, CLAD - 0.001, CLAD + MTX + 0.001); PTS.append(("bend 1 apex", apex_V("BEND1", ZB1, +1), Ia))
PTS.append(("raised L2 end", *raised("L2_taper_end", "H_raised_L2end.txt", RB, zr1, -1)))
PTS.append(("L2 (mid)", RES["L2"]["V"], RES["L2"]["I"]))
PTS.append(("raised L2 start", *raised("L2_taper_start", "H_raised_L2start.txt", RB, zr2, -1)))
_, Ib = loop_y("H_bend2_apex.txt", ZB2 - RB, dyr, CLAD - 0.001, CLAD + MTX + 0.001); PTS.append(("bend 2 apex", apex_V("BEND2", ZB2, -1), Ib))
PTS.append(("raised L3", *raised("L3_taper", "H_raised_L3.txt", 3 * RB, zr2, +1)))
PTS.append(("L3 (mid)", RES["L3"]["V"], RES["L3"]["I"]))
P = np.array([0.5 * np.real(v * np.conj(i)) for _, v, i in PTS]); Zloc = np.array([v / i for _, v, i in PTS])
print("\nNet power along the path (dB re L1 mid) and local V/I (ohm)")
print(" f GHz | " + " | ".join(n for n, _, _ in PTS))
for q in (10, 20, 40, 60, 80, 100, 120):
    i = np.argmin(abs(F - q)); print(f"{F[i]:5.0f} | " + " | ".join(f"{10*np.log10(P[k,i]/P[0,i]):+6.2f} ({Zloc[k,i].real:4.1f})" for k in range(len(PTS))))
np.savez(os.path.join(HERE, "h_field_analysis.npz"), F=F, Zts=Zts, names=[n for n, _, _ in PTS], P=P, Zloc=Zloc,
         **{f"{l}_{k}": RES[l][k] for l in RES for k in ("Zc", "Zc_avg", "I", "V", "spread")})
