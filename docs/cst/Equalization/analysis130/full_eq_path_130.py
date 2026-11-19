"""Full equaliser run, 0-130 GHz: coplanar (v_c) and ground-to-ground (v_p) voltages along the whole path
port 1 -> L1 (2.70 mm, +z) -> bend 1 -> L2 (1.44 mm, -z) -> bend 2 -> L3 (1.44 mm, +z) -> port 2.

Left/right are taken with respect to the direction of travel (top view, z to the right, y up), so that the sign of
v_p is the same along the whole path (inner/outer would swap between the two bends, which turn opposite ways):
  v_left, v_right = signal-to-ground voltage across the gap on the left / right of the travelling wave
  v_c = (v_left + v_right)/2 (coplanar mode),  v_p = (v_left - v_right)/2 (ground-to-ground mode).
  Bend 1 turns left (inner gap = left), bend 2 turns right (inner gap = right).
Straight gaps: v = +GAP * Ey for a gap at y above the signal, -GAP * Ey below (point field at the gap centre).
Arcs: line integral of the radial field across each gap from the 2D maps (BEND1, BEND2, read from the split zip and
cached in ./cache), every 2 deg.
Calibration (frequency independent, fixed at 1 GHz, as in bend_path_130.py): buried lines raw; each raised gap
(raised straight before/after a bend) scaled once so that its 1 GHz voltage matches the cell-averaged buried voltage
over the last 0.36 mm before the transition (vertical step + 50 um gap taper); each arc point scaled at 1 GHz to the
voltage interpolated between the two arc ends.
Outputs: full_eq_path_130.npz (path coordinate s, v_c, v_p, segment index for every frequency)."""
import os, io, glob, zipfile, numpy as np, pandas as pd
from scipy.interpolate import RegularGridInterpolator
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "..", "full equalizer", "130 GHz")
G1, G2, RB = 4.45e-6, 4.8e-6, 0.1025; RIN, ROUT = RB - 0.01975, RB + 0.01975
ZB1, ZB2, YC2 = 2.97434, 0.98566, 2 * RB
CACHE = os.path.join(HERE, "cache", "full_bend_maps.npz")
if not os.path.exists(CACHE):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    zf = zipfile.ZipFile(io.BytesIO(b"".join(open(p, "rb").read() for p in sorted(glob.glob(os.path.join(R, "bend_fields_full_eq.zip.0*"))))))
    out = {}
    for nm in ("BEND1", "BEND2"):
        d = pd.read_csv(zf.open(nm + ".txt"), sep=r"\s+", skiprows=2, header=None, engine="c").to_numpy()
        f = np.unique(d[:, 0]); y = np.unique(np.round(d[:, 2], 6)); z = np.unique(np.round(d[:, 3], 6))
        iF, iY, iZ = np.searchsorted(f, d[:, 0]), np.searchsorted(y, np.round(d[:, 2], 6)), np.searchsorted(z, np.round(d[:, 3], 6))
        Ey = np.zeros((len(f), len(y), len(z)), np.complex64); Ez = np.zeros_like(Ey)
        Ey[iF, iY, iZ] = d[:, 6] + 1j * d[:, 7]; Ez[iF, iY, iZ] = d[:, 8] + 1j * d[:, 9]
        out.update({f"{nm}_y": y, f"{nm}_z": z, f"{nm}_Ey": Ey, f"{nm}_Ez": Ez, "f": f}); del d
    np.savez(CACHE, **out)
M = np.load(CACHE); F = M["f"]

def load(fn):
    d = np.loadtxt(os.path.join(R, fn), skiprows=2); fr = np.unique(d[:, 0]); z = d[d[:, 0] == fr[0], 3]
    o = np.argsort(z); return z[o], (d[:, 6] + 1j * d[:, 7]).reshape(len(fr), len(z))[:, o]
def straight(name, gap, direction, zlim=None):
    """gap voltages (left, right) and z for a straight piece travelling along +z (direction=+1) or -z (-1)."""
    z, Ep = load(f"{name}_gap+.txt"); _, Em = load(f"{name}_gap-.txt")
    k = np.ones(len(z), bool) if zlim is None else (z > zlim[0]) & (z <= zlim[1])
    z, vup, vdn = z[k], gap * Ep[:, k], -gap * Em[:, k]               # gap above (+y) / below (-y) the signal
    if direction > 0: return z, vup, vdn                               # travelling +z: left = +y
    o = np.argsort(-z); return z[o], vdn[:, o], vup[:, o]             # travelling -z: left = -y, reverse order
def arc(nm, zc, yc, sgn_z, turn):
    """bend map nm; arc centre (zc, yc); points y = yc - r cos(th), z = zc + sgn_z r sin(th), th 0..180 deg."""
    th = np.radians(np.arange(0, 180.01, 2.0)); y, z = M[f"{nm}_y"], M[f"{nm}_z"]
    DR = np.arange(-G2 * 1e3 / 2 - 0.0012, G2 * 1e3 / 2 + 0.0012 + 1e-9, 0.00025); vin, vout = [], []
    for i in range(len(F)):
        iy, iz = (RegularGridInterpolator((y, z), M[f"{nm}_{c}"][i], bounds_error=False, fill_value=0) for c in ("Ey", "Ez")); vals = []
        for r in (RIN, ROUT):
            rr = r + DR[:, None]; pts = np.stack([(yc - rr * np.cos(th)).ravel(), (zc + sgn_z * rr * np.sin(th)).ravel()], 1)
            er = (iy(pts) * np.tile(-np.cos(th), len(DR)) + iz(pts) * np.tile(sgn_z * np.sin(th), len(DR))).reshape(len(DR), len(th))
            vals.append(np.trapezoid(er, DR * 1e-3, axis=0))
        vin.append(-vals[0]); vout.append(vals[1])                     # signal -> ground: inner ground at smaller r
    vin, vout = np.array(vin), np.array(vout)
    return th, (vin, vout) if turn == "left" else (vout, vin)        # (left, right)
segs = []                                                              # (name, s-length increments handled below)
z, l, r = straight("L1", G1, +1); segs.append(["L1", z - z[0], l, r])
z, l, r = straight("L1_taper", G2, +1, (2.70, ZB1)); segs.append(["raised 1a", z - 2.70, l, r])
th, (l, r) = arc("BEND1", ZB1, 0.0, +1, "left"); segs.append(["arc 1", RB * th, l, r])
z, l, r = straight("L2_taper_end", G2, -1, (2.70, ZB1)); segs.append(["raised 1b", ZB1 - z, l, r])
z, l, r = straight("L2", G1, -1); segs.append(["L2", 2.70 - z, l, r])
z, l, r = straight("L2_taper_start", G2, -1, (ZB2, 1.26)); segs.append(["raised 2a", 1.26 - z, l, r])
th, (l, r) = arc("BEND2", ZB2, YC2, -1, "right"); segs.append(["arc 2", RB * th, l, r])
z, l, r = straight("L3_taper", G2, +1, (ZB2, 1.26)); segs.append(["raised 2b", z - ZB2, l, r])
z, l, r = straight("L3", G1, +1); segs.append(["L3", z - 1.26, l, r])
# path coordinate
s0, S = 0.0, []
off = {"L1": 0, "raised 1a": 2.70, "arc 1": 2.70 + (ZB1 - 2.70), "raised 1b": None}
lens = {"L1": 2.70, "raised 1a": ZB1 - 2.70, "arc 1": np.pi * RB, "raised 1b": ZB1 - 2.70, "L2": 1.44, "raised 2a": 1.26 - ZB2,
        "arc 2": np.pi * RB, "raised 2b": 1.26 - ZB2, "L3": 1.44}
start = 0.0
for sg in segs:
    sg[1] = sg[1] + start; start += lens[sg[0]]
# calibration
def cal(prev_buried, raised, side_first):
    """scale raised gap voltages so that at 1 GHz the raised point next to the transition equals the buried cell average."""
    for k in (2, 3):
        vb = abs(prev_buried[k][0].mean()); vr = abs(raised[k][0, 0 if side_first else -1]); raised[k] *= vb / vr
def last_cells(sg, end):           # buried voltages over the 0.36 mm next to the transition
    s = sg[1]; m = (s >= s.max() - 0.36) if end else (s <= s.min() + 0.36); return [None, None, sg[2][:, m], sg[3][:, m]]
idx = {sg[0]: n for n, sg in enumerate(segs)}
def calib(raised_name, buried_name, buried_end, raised_first):
    rs = segs[idx[raised_name]]; rs[1] = rs[1]; tmp = [None, None, rs[2], rs[3]]
    s = rs[1]; j = np.argmin(abs(s - (s.min() + 0.055))) if raised_first else np.argmin(abs(s - (s.max() - 0.055)))   # first point after the 50 um taper
    bs = last_cells(segs[idx[buried_name]], buried_end)
    for k in (2, 3): rs[k] *= abs(bs[k][0].mean()) / abs(rs[k][0, j])
calib("raised 1a", "L1", True, True); calib("raised 1b", "L2", False, False)
calib("raised 2a", "L2", True, True); calib("raised 2b", "L3", False, False)
for a, p_, n_ in (("arc 1", "raised 1a", "raised 1b"), ("arc 2", "raised 2a", "raised 2b")):
    sa, sp, sn = segs[idx[a]], segs[idx[p_]], segs[idx[n_]]; t = np.linspace(0, 1, len(sa[1]))
    for k in (2, 3):
        a0, a1 = abs(sp[k][0, -1]), abs(sn[k][0, 0]); target = a0 + (a1 - a0) * t; sa[k] = sa[k] * (target / abs(sa[k][0]))[None, :]
S = np.concatenate([sg[1] for sg in segs]); VL = np.concatenate([sg[2] for sg in segs], 1); VR = np.concatenate([sg[3] for sg in segs], 1)
SEG = np.concatenate([[n] * len(sg[1]) for n, sg in enumerate(segs)])
VC, VP = (VL + VR) / 2, (VL - VR) / 2
print("path length", round(S[-1], 4), "mm;", [(sg[0], round(sg[1][0], 3), round(sg[1][-1], 3)) for sg in segs])
for q in (1, 40, 80):
    i = np.argmin(abs(F - q)); print(f"{q} GHz |v_c| segment ends:", [f"{sg[0]}: {abs(VC[i][SEG==n][0]):.2f}->{abs(VC[i][SEG==n][-1]):.2f}" for n, sg in enumerate(segs)])
np.savez(os.path.join(HERE, "full_eq_path_130.npz"), F=F, S=S, VC=VC, VP=VP, SEG=SEG, names=[sg[0] for sg in segs])
