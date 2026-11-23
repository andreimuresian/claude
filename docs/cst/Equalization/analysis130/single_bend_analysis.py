"""Single-bend run (20 um buried stubs, PEC-bridged ports; EL_L = EL_L2 = 0.02 mm), 0-130 GHz: power flow along the bend.

Planes along the path (E and H at the same positions): stub 1 (z 0.01) -> A1 (just after the 50 um gap taper) -> M1 -> B1
(just before the arc) -> apex -> B2 -> M2 -> A2 -> stub 2.
Voltage (coplanar, signal to ground, mean of the two gaps): line integral of the field across each gap, averaged over the
interior rows of the metal height (rows on the metal faces excluded) (buried x 0..MTX, raised x CLAD_H..CLAD_H+MTX): the same definition on every plane.
Current: Ampere loop of H around the signal electrode (as in h_field_analysis.py), counted along the direction of travel
(apex plane: the (x, z) loop is oriented along -y, hence the sign -1 for travel along +y).
Net power P = 1/2 Re(V I*) (standing waves do not change it) -> loss of the coplanar wave between consecutive planes
(dissipation + radiation + conversion into the parasitic mode). Check: P(stub 2)/P(stub 1) against |S21|^2/(1-|S11|^2).
Also local V/I and the dips of the single-bend |S21| (trapped parasitic mode between the PEC-bridged ports).
Outputs: single_bend_analysis.npz, printed tables."""
import os, numpy as np, pandas as pd, skrf as rf
from scipy.signal import find_peaks
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "..", "single bend")
RB, WS, CLAD, MTX = 0.1025, 0.0347, 0.0036, 0.002; L, TL = 0.02, 0.22434; ZB = L + 0.05 + TL
def load(fn):
    d = pd.read_csv(os.path.join(D, fn), sep=r"\s+", skiprows=2, header=None).to_numpy(); return np.unique(d[:, 0]), d
def grid(d, F, a, b):
    A, B = np.unique(np.round(d[:, a], 6)), np.unique(np.round(d[:, b], 6)); iF = np.searchsorted(F, d[:, 0])
    ia, ib = np.searchsorted(A, np.round(d[:, a], 6)), np.searchsorted(B, np.round(d[:, b], 6)); out = {}
    for k, c in (("x", 4), ("y", 6), ("z", 8)):
        h = np.zeros((len(F), len(A), len(B)), complex); h[iF, ia, ib] = d[:, c] + 1j * d[:, c + 1]; out[k] = h
    return A, B, out
def edges(X, H):
    full = [k for k in range(len(X)) if np.all(abs(H["x"][-1, k]) + abs(H["y"][-1, k]) + abs(H["z"][-1, k]) > 0)]
    return full[0], full[-1]
def current(fn, c, dg, coord):
    """loop current; coord 'y': plane z = const (x, y); 'z': plane y = const (x, z)."""
    F, d = load(fn); X, Y, H = grid(d, F, 1, 2 if coord == "y" else 3); j0, j1 = np.argmin(abs(Y - (c - dg))), np.argmin(abs(Y - (c + dg)))
    i0, i1 = edges(X, H); xs, ys = X[i0:i1 + 1] * 1e-3, Y[j0:j1 + 1] * 1e-3; t = coord
    return F, (np.trapezoid(H["x"][:, i0:i1 + 1, j0], xs, axis=1) + np.trapezoid(H[t][:, i1, j0:j1 + 1], ys, axis=1)
               - np.trapezoid(H["x"][:, i0:i1 + 1, j1], xs, axis=1) - np.trapezoid(H[t][:, i0, j0:j1 + 1], ys, axis=1))
def voltage(fn, c, dg, coord, xlo, xhi):
    """coplanar voltage: gap above c (ground at larger coordinate): +int E; gap below: -int E; mean over the rows in the metal height."""
    F, d = load(fn); X, Y, E = grid(d, F, 1, 2 if coord == "y" else 3); rows = np.where((X > xlo + 1e-6) & (X < xhi - 1e-6))[0]          # interior rows only (the rows on the metal faces read low)
    vals = []
    for r in rows:
        v = []
        for sgn in (+1, -1):
            k = abs(Y - (c + sgn * dg)) <= 0.0045; v.append(sgn * np.trapezoid(E[coord][:, r, k], Y[k] * 1e-3, axis=1))
        vals.append((v[0] + v[1]) / 2)
    return F, np.mean(vals, 0)
dgb, dgr = WS / 2 + 0.00445 / 2, WS / 2 + 0.0048 / 2
PL = [("stub 1", "stub1", -RB, dgb, "y", 0.0, MTX, +1), ("A1", "A1", -RB, dgr, "y", CLAD, CLAD + MTX, +1), ("M1", "M1", -RB, dgr, "y", CLAD, CLAD + MTX, +1),
      ("B1", "B1", -RB, dgr, "y", CLAD, CLAD + MTX, +1), ("apex", "apex", ZB + RB, dgr, "z", CLAD, CLAD + MTX, -1),
      ("B2", "B2", RB, dgr, "y", CLAD, CLAD + MTX, -1), ("M2", "M2", RB, dgr, "y", CLAD, CLAD + MTX, -1), ("A2", "A2", RB, dgr, "y", CLAD, CLAD + MTX, -1),
      ("stub 2", "stub2", RB, dgb, "y", 0.0, MTX, -1)]
V, I = [], []
for lab, tag, c, dg, co, xlo, xhi, dr in PL:
    F, v = voltage(f"E_{tag}.txt", c, dg, co, xlo, xhi); _, i = current(f"H_{tag}.txt", c, dg, co); V.append(v); I.append(dr * i)
V, I = np.array(V), np.array(I); P = 0.5 * np.real(V * np.conj(I)); Z = V / I
net = rf.Network(os.path.join(D, "BASELINE - BEND.s2p")); fS = net.f / 1e9
s21, s11 = np.interp(F, fS, abs(net.s[:, 1, 0])), np.interp(F, fS, abs(net.s[:, 0, 0]))
chk = 10 * np.log10(P[-1] / P[0]) - 10 * np.log10(s21 ** 2 / (1 - s11 ** 2))
print(f"check P(stub 2)/P(stub 1) against |S21|^2/(1-|S11|^2): mean {chk[F>=5].mean():+.3f} dB, rms {np.sqrt(np.mean(chk[F>=5]**2)):.3f} dB (5-130 GHz)")
SEG = [("step + gap taper (side 1)", 0, 1), ("raised straight A1 -> B1", 1, 3), ("arc B1 -> apex", 3, 4), ("arc apex -> B2", 4, 5),
       ("raised straight B2 -> A2", 5, 7), ("gap taper + step (side 2)", 7, 8), ("whole bend (stub 1 -> stub 2)", 0, 8)]
print(" f GHz | " + " | ".join(s for s, _, _ in SEG) + "   [dB, net power]")
for q in (10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130):
    i = np.argmin(abs(F - q)); print(f"{F[i]:5.0f} | " + " | ".join(f"{10*np.log10(P[b,i]/P[a,i]):+.3f}" for _, a, b in SEG))
print(" f GHz | local V/I (ohm): " + " / ".join(l for l, *_ in PL))
for q in (10, 40, 80, 120):
    i = np.argmin(abs(F - q)); print(f"{F[i]:5.0f} | " + " / ".join(f"{Z[k,i].real:.1f}" for k in range(len(PL))))
dB = 20 * np.log10(abs(net.s[:, 1, 0])); k = fS >= 1; tr = np.polyval(np.polyfit(fS[k], dB[k], 3), fS)
dips, pr = find_peaks(-(dB - tr), prominence=0.03, distance=30)
print("single-bend |S21| dips (GHz, depth dB):", [(round(fS[j], 1), round(pr["prominences"][n], 2)) for n, j in enumerate(dips)])
print("touchstone |S21| dB at 20/60/100/130 GHz:", [round(dB[np.argmin(abs(fS-q))], 3) for q in (20, 60, 100, 130)])
np.savez(os.path.join(HERE, "single_bend_analysis.npz"), F=F, P=P, V=V, I=I, Z=Z, names=[p[0] for p in PL], fS=fS, s21=net.s[:, 1, 0], s11=net.s[:, 0, 0], chk=chk)
