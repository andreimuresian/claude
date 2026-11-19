"""Bend block, 0-130 GHz: agreement of the touchstone and field routes, and loss budget.
Inputs: lbs_bend_130.npz (lbs_bend_130.py), ls_extraction_130.npz (line alpha, field route).
Loss fraction of the block: 1 - |S11|^2 - |S21|^2 (power not transmitted or reflected in the coplanar mode:
dissipated in metal and dielectric, radiated, or converted into the parasitic mode).
Smooth part: cubic fit of |S21| dB outside +/-2.5 GHz of the dips; compared with the loss of the same path length
(0.871 mm: 2 x 0.274 mm raised straight + 0.322 mm arc) of buried line.
Outputs: printed table, bend_compare_130.npz."""
import os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
b = np.load(os.path.join(HERE, "lbs_bend_130.npz")); P = np.load(os.path.join(HERE, "parasitic_mode_130.npz")); LS = np.load(os.path.join(HERE, "ls_extraction_130.npz"))
f, SA, F, SB, tpA, tpB = b["f"], b["SA"], b["F"], b["SB"], b["tpA"], b["tpB"]
ia = np.array([np.argmin(abs(f - x)) for x in F]); dB = lambda s: 20 * np.log10(abs(s))
d21 = dB(SB[:, 1, 0]) - dB(SA[ia, 1, 0]); dt = tpB - tpA[ia]; d11 = abs(SB[:, 0, 0]) - abs(SA[ia, 0, 0])
for lo, hi in ((1, 10), (10, 60), (62, 130)):
    m = (F >= lo) & (F <= hi)
    print(f"{lo:3d}-{hi:3d} GHz: |S21| fields - ts mean {d21[m].mean():+.3f} dB, max {abs(d21[m]).max():.3f} dB | phase delay mean {dt[m].mean():+.3f} ps, max {abs(dt[m]).max():.3f} ps | |S11| max diff {abs(d11[m]).max():.3f}")
s21 = dB(SA[:, 1, 0]); far = np.min([abs(f - x) for x in P["dips"]], 0) > 2.5
trend = np.polyval(np.polyfit(f[far & (f >= 1)], s21[far & (f >= 1)], 3), f)
lossf = 1 - abs(SA[:, 0, 0]) ** 2 - abs(SA[:, 1, 0]) ** 2
aline = np.interp(f, LS["F"], LS["aF"]); line_eq = -aline * 0.0871                      # dB over 0.871 mm of buried line
print(" f GHz | bend |S21| dB smooth | same length of buried line (dB) | ratio | loss fraction 1-|S11|^2-|S21|^2 (smooth trend / at dip)")
for q in (10, 20, 40, 60, 80, 100, 120):
    i = np.argmin(abs(f - q)); print(f"{q:5d}  | {trend[i]:+.3f} | {line_eq[i]:+.3f} | {trend[i]/line_eq[i]:.2f} | {1-10**(trend[i]/10):.3f}")
for x in P["dips"]:
    i = np.argmin(abs(f - x)); print(f"   dip {x:6.1f} GHz: |S21| {s21[i]:+.3f} dB vs smooth {trend[i]:+.3f} dB (extra {s21[i]-trend[i]:+.3f} dB), loss fraction {lossf[i]:.3f}")
tauA = np.median(tpA[(f > 10)]); tauB = np.median(tpB[F > 10]); print(f"phase delay median >10 GHz: ts {tauA:.3f} ps, fields {tauB:.3f} ps -> index over 0.871 mm: {tauB*1e-12*299792458/0.871e-3:.3f}")
np.savez(os.path.join(HERE, "bend_compare_130.npz"), trend=trend, lossf=lossf, line_eq=line_eq)
