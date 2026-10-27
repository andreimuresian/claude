"""
LOW_Z (GAP 4.15 um) vs HIGH_Z (GAP 15 um), 8 mm, 625 um pitch, uniform lines.
Ports 1 A near, 2 A far, 3 B near, 4 B far.
Model-free: NEXT = S31, FEXT = S41. Error floor of the crosstalk: terms that the
pair's symmetries make equal (NEXT: S31, S42 by end symmetry; S13 = S31 by reciprocity
is not a test; FEXT: S41, S32, S23, S14) -- their spread is the numerical noise of the
crosstalk itself. Group delay of NEXT vs through (S21): ~1x = coupling spread along the
line (two-mode picture), ~2x = round trip from the far end.
"""
import skrf, numpy as np
d = lambda x: 20 * np.log10(np.abs(x) + 1e-30)
nets = {k: skrf.Network(f"LINEA_8MM_625UM_PITCH_STD_{k}.s4p") for k in ("LOW_Z", "HIGH_Z")}
f = nets["LOW_Z"].f
w = 2 * np.pi * f
gd = lambda x: -np.gradient(np.unwrap(np.angle(x)), w) * 1e12
print(" f GHz |      LOW_Z (gap 4.15 um)            |      HIGH_Z (gap 15 um)")
print("       | S11   S21   NEXT  FEXT  floorN floorF | S11   S21   NEXT  FEXT  floorN floorF")
for g in (2, 5, 10, 20, 30, 40, 50, 60):
    i = np.argmin(abs(f - g * 1e9)); row = f"{g:5d}  |"
    for k in ("LOW_Z", "HIGH_Z"):
        s = nets[k].s[i]
        fN = abs(s[2, 0] - s[3, 1]); fF = max(abs(s[3, 0] - s[2, 1]), abs(s[3, 0] - s[1, 2]))
        row += f" {d(s[0,0]):5.1f} {d(s[1,0]):5.2f} {d(s[2,0]):5.1f} {d(s[3,0]):5.1f} {d(fN):6.1f} {d(fF):6.1f} |"
    print(row)
for k, n in nets.items():
    s = n.s; sel = (f >= 5e9) & (f <= 50e9)
    t21, tN, tF = (np.median(gd(s[:, a, 0])[sel]) for a in (1, 2, 3))
    print(f"{k}: group delay 5-50 GHz: through {t21:.1f} ps, NEXT {tN:.1f} ps ({tN/t21:.2f}x), FEXT {tF:.1f} ps ({tF/t21:.2f}x)")
    for band in ((2, 20), (20, 40), (40, 60)):
        m = (f >= band[0] * 1e9) & (f <= band[1] * 1e9)
        print(f"   {band[0]:2d}-{band[1]:2d} GHz mean |NEXT| {d(np.sqrt(np.mean(abs(s[m,2,0])**2))):6.1f} dB, |FEXT| {d(np.sqrt(np.mean(abs(s[m,3,0])**2))):6.1f} dB, "
              f"floor NEXT {d(np.sqrt(np.mean(abs(s[m,2,0]-s[m,3,1])**2))):6.1f}, FEXT {d(np.sqrt(np.mean(abs(s[m,3,0]-s[m,2,1])**2))):6.1f}")
