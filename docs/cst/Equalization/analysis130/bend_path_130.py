"""L+B+S run, 0-130 GHz: coplanar (CPW) and ground-to-ground (parasitic) voltages along the whole path
port 1 -> line 1 -> rise + raised straight -> U-bend -> raised straight + descent -> line 2 -> port 2.

Potentials: signal phi_s, inner ground phi_i (bend-centre side), outer ground phi_o.
  v_in = phi_s - phi_i,  v_out = phi_s - phi_o  (gap voltages, field at the gap centre x gap width)
  CPW voltage        v_c = (v_in + v_out) / 2
  parasitic voltage  v_p = (v_in - v_out) / 2 = (phi_o - phi_i) / 2   (potential difference between the two grounds)
Gap widths: 4.45 um buried (x = 1 um), 4.8 um raised (x = 4.6 um). In the arc the field across a gap is radial:
  v_in = -E_r(inner gap) * gap, v_out = +E_r(outer gap) * gap, E_r from the 2D map (bilinear interpolation).
Path coordinate s along the line centre (arc radius 0.1025 mm).
The bend map (BEND.txt, 477 MB) is read from the split zip in the repository and cached in ./cache (git-ignored).
Calibration (frequency-independent factors fixed at 1 GHz, local so that the 1 GHz standing wave is not imprinted):
on the staircase mesh the exported field of an oblique gap is scaled by a geometric factor (up to x2 at 1 GHz);
raised and buried gaps differ in width and height. Buried lines are kept raw (their point field swings x2 within each 0.18 mm cell of the
periodic loading: use cell averages); each raised gap gets one factor that makes the 1 GHz voltage continuous across
the 50 um rise (cell-averaged buried voltage of the last 0.36 mm vs the first raised point after the rise); each arc point is scaled at 1 GHz to the voltage
interpolated between the two arc ends (0.32 mm apart, 1/900 of a wavelength at 1 GHz).
Checked: point sampling and line integral across the gap give the same calibrated arc profile.
Outputs: bend_path_130.npz (v_c, v_p along s for every frequency), printed checks."""
import os, io, glob, zipfile, numpy as np, pandas as pd
from scipy.interpolate import RegularGridInterpolator
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "..", "L+B+S", "130 GHz")
G1, G2, ZB, RB, RIN, ROUT = 4.45e-6, 4.8e-6, 2.43434, 0.1025, 0.08275, 0.12225
CACHE = os.path.join(HERE, "cache", "lbs_bend_map.npz")
if not os.path.exists(CACHE):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    zf = zipfile.ZipFile(io.BytesIO(b"".join(open(p, "rb").read() for p in sorted(glob.glob(os.path.join(R, "bend_fields_L+B+S.zip.0*"))))))
    d = pd.read_csv(zf.open("BEND.txt"), sep=r"\s+", skiprows=2, header=None, engine="c").to_numpy()
    f = np.unique(d[:, 0]); y = np.unique(np.round(d[:, 2], 6)); z = np.unique(np.round(d[:, 3], 6))
    iF, iY, iZ = np.searchsorted(f, d[:, 0]), np.searchsorted(y, np.round(d[:, 2], 6)), np.searchsorted(z, np.round(d[:, 3], 6))
    Ey = np.zeros((len(f), len(y), len(z)), np.complex64); Ez = np.zeros_like(Ey)
    Ey[iF, iY, iZ] = d[:, 6] + 1j * d[:, 7]; Ez[iF, iY, iZ] = d[:, 8] + 1j * d[:, 9]
    np.savez(CACHE, f=f, y=y, z=z, Ey=Ey, Ez=Ez); del d
M = np.load(CACHE); F, ym, zm = M["f"], M["y"], M["z"]

def load(fn):
    d = np.loadtxt(os.path.join(R, fn), skiprows=2); fr = np.unique(d[:, 0]); z = d[d[:, 0] == fr[0], 3]
    o = np.argsort(z); return z[o], (d[:, 6] + 1j * d[:, 7]).reshape(len(fr), len(z))[:, o]
segs = []                                  # (s array mm, v_in, v_out) per segment
# line 1 (centre y = -RB): inner gap = gap+ (y > centre); field +y in inner gap means signal -> inner ground... v_in = Ey(gap+) * gap
z, Ep = load("L1_gap+.txt"); _, Em = load("L1_gap-.txt"); segs.append(("line 1", z, G1 * Ep, -G1 * Em))
z, Ep = load("L1_taper_gap+.txt"); _, Em = load("L1_taper_gap-.txt"); k = (z > 2.16 + 1e-6) & (z <= ZB)
segs.append(("raised 1", z[k], G2 * Ep[:, k], -G2 * Em[:, k]))
th = np.radians(np.arange(0.0, 180.01, 2.0)); s_arc = ZB + RB * th   # s continues from z = ZB, 2 deg steps
# arc: true line integral of E_r across each gap (radial span gap +/- 1.2 um, 0.25 um steps; E = 0 inside the metal),
# so the 1 um staircase of the curved metal edges does not bias the result
DR = np.arange(-G2 * 1e3 / 2 - 0.0012, G2 * 1e3 / 2 + 0.0012 + 1e-9, 0.00025)
Ein, Eout = [], []
for i in range(len(F)):
    iy, iz = (RegularGridInterpolator((ym, zm), M[c][i], bounds_error=False, fill_value=0) for c in ("Ey", "Ez")); vals = []
    for r in (RIN, ROUT):
        rr = r + DR[:, None]; yy, zz = -rr * np.cos(th), ZB + rr * np.sin(th); pts = np.stack([yy.ravel(), zz.ravel()], 1)
        er = (iy(pts) * np.tile(-np.cos(th), len(DR)) + iz(pts) * np.tile(np.sin(th), len(DR))).reshape(len(DR), len(th))
        vals.append(np.trapezoid(er, DR * 1e-3, axis=0))        # integral of E_r dr (V)
    Ein.append(vals[0]); Eout.append(vals[1])
segs.append(("arc", s_arc, -np.array(Ein), np.array(Eout)))
s_end = s_arc[-1]
# raised 2 and line 2 (centre y = +RB): inner gap = gap- (y < centre); r_hat = +y there: v_in = -Ey(gap-) gap, v_out = Ey(gap+) gap
z, Ep = load("L2_taper_gap+.txt"); _, Em = load("L2_taper_gap-.txt"); k = (z > 2.16 + 1e-6) & (z <= ZB); o = np.argsort(-z[k])
segs.append(("raised 2", s_end + (ZB - z[k][o]), -G2 * Em[:, k][:, o], G2 * Ep[:, k][:, o]))
z, Ep = load("L2_gap+.txt"); _, Em = load("L2_gap-.txt"); o = np.argsort(-z); s_r2 = s_end + (ZB - 2.16)
segs.append(("line 2", s_r2 + (2.16 - z[o]), -G1 * Em[:, o], G1 * Ep[:, o]))
S = np.concatenate([sg[1] for sg in segs]); VIN = np.concatenate([sg[2] for sg in segs], 1); VOUT = np.concatenate([sg[3] for sg in segs], 1)
# local calibration (frequency independent factors, fixed at 1 GHz):
#  - buried lines: raw (point field x gap);
#  - raised sections and arc: one factor per gap (inner, outer) per side, so that at 1 GHz the voltage is continuous
#    across the 50 um rise (the voltage cannot change over 50 um at 1 GHz);
#  - arc points: each point scaled, at 1 GHz, to the voltage interpolated between the two arc ends (0.32 mm apart).
nseg = [len(sg[1]) for sg in segs]; idx = np.cumsum([0] + nseg); sl = [slice(idx[k], idx[k + 1]) for k in range(5)]
for V in (VIN, VOUT):
    # buried side: mean over the last two cells (0.36 mm = 2 pitches) before the rise, i.e. the cell-averaged voltage;
    # raised side: first point after the rise (z >= 2.215 mm)
    s0, s4 = segs[0][1], segs[4][1]; r1, r3 = segs[1][1], segs[3][1]
    vb1 = abs(V[0, sl[0]][(s0 >= 1.80) & (s0 < 2.16)].mean()); vb2 = abs(V[0, sl[4]][(s4 > s4[0]) & (s4 <= s4[0] + 0.36)].mean())
    vr1 = abs(V[0, sl[1]][np.argmin(abs(r1 - 2.215))]); vr3 = abs(V[0, sl[3]][np.argmin(abs(r3 - (r3[-1] - 0.055)))])
    k1, k2 = vb1 / vr1, vb2 / vr3
    V[:, sl[1]] *= k1; V[:, sl[3]] *= k2
    a = V[:, sl[2]]; a0, a1 = abs(V[0, sl[1]][-1]), abs(V[0, sl[3]][0])          # 1 GHz voltage at both arc ends
    target = a0 + (a1 - a0) * th / np.pi; V[:, sl[2]] = a * (target / abs(a[0]))[None, :]
VC, VP = (VIN + VOUT) / 2, (VIN - VOUT) / 2; SEG = np.concatenate([[n] * len(sg[1]) for n, sg in enumerate(segs)])
print("path length", round(S[-1], 4), "mm; segments", [(sg[0], round(sg[1][0], 3), round(sg[1][-1], 3)) for sg in segs])
for q in (10, 31, 40, 79):
    i = np.argmin(abs(F - q)); print(f"{q} GHz: |v_c| (V) at segment ends:", [f"{sg[0]}: {abs(VC[i][SEG==n][0]):.3f}->{abs(VC[i][SEG==n][-1]):.3f}" for n, sg in enumerate(segs)])
np.savez(os.path.join(HERE, "bend_path_130.npz"), F=F, S=S, VC=VC, VP=VP, SEG=SEG, names=[sg[0] for sg in segs])
