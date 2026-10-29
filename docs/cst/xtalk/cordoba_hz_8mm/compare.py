"""
CORDOBA (signal 35 um, grounds 49.85 um) vs CORDOBA high impedance (signal 10 um, grounds 25 um), 8 mm.
1) Model-free S-parameters: S11, S21, NEXT = S31, FEXT = S41, symmetry floors (NEXT: |S31 - S42|,
   FEXT: |S41 - S32|), group delays (S21, S31, S41) and n_g = c tau / L from the S21 delay.
2) EO crosstalk B/A from the CST gap fields at the 12 monitor frequencies (exact for the TD model):
   50 ohm source and load (= the port impedance: no re-termination), push-pull, optical n_g 2.27.
"""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import numpy as np, skrf
from mzm_interconnect import parameters as P, xtalk_s4p as X, xtalk_fields as XF
HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = {"CORDOBA": os.path.join(HERE, "../cordoba_8mm"), "CORDOBA HZ": HERE}
S4P = {"CORDOBA": "LINEA_8MM_625UM_PITCH_CORDOBA.s4p", "CORDOBA HZ": "LINEA_8MM_625UM_PITCH_CORDOBA_NARROW.s4p"}
d = lambda x: 20 * np.log10(np.abs(x) + 1e-30)
C0 = 2.99792458e8; L = 8e-3
nets = {k: skrf.Network(os.path.join(RUNS[k], S4P[k])) for k in RUNS}
f = nets["CORDOBA"].f; assert np.allclose(f, nets["CORDOBA HZ"].f)
w = 2 * np.pi * f
gd = lambda x: -np.gradient(np.unwrap(np.angle(x)), w)
print("S-parameters (dB)      |        CORDOBA (35 / 49.85 um)            |      CORDOBA HZ (10 / 25 um)")
print(" f GHz | S11   S21    NEXT   FEXT  floorN floorF | S11   S21    NEXT   FEXT  floorN floorF")
for g in (1, 2, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60):
    i = np.argmin(abs(f - g * 1e9)); row = f"{g:5d}  |"
    for k in RUNS:
        s = nets[k].s[i]
        row += f" {d(s[0,0]):5.1f} {d(s[1,0]):6.2f} {d(s[2,0]):6.1f} {d(s[3,0]):6.1f} {d(s[2,0]-s[3,1]):6.1f} {d(s[3,0]-s[2,1]):6.1f} |"
    print(row)
for k, n in nets.items():
    s = n.s; sel = (f >= 5e9) & (f <= 50e9)
    t21, tN, tF = (np.median(gd(s[:, a, 0])[sel]) * 1e12 for a in (1, 2, 3))
    print(f"{k:11s}: delay 5-50 GHz S21 {t21:.1f} ps (n_g {t21*1e-12*C0/L:.3f}), NEXT {tN:.1f} ps ({tN/t21:.2f}x), "
          f"FEXT {tF:.1f} ps ({tF/t21:.2f}x); A/B asym {np.max(abs(s[:,:2,:2]-s[:,2:,2:])):.1e}, end asym {np.max(abs(s[:,0,0]-s[:,1,1])):.1e}")
    for b in ((2, 20), (20, 40), (40, 60)):
        m = (f >= b[0] * 1e9) & (f <= b[1] * 1e9)
        rms = lambda x: d(np.sqrt(np.mean(abs(x) ** 2)))
        print(f"   {b[0]:2d}-{b[1]:2d} GHz rms: S11 {rms(s[m,0,0]):6.1f}  NEXT {rms(s[m,2,0]):6.1f}  FEXT {rms(s[m,3,0]):6.1f}")
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
print(f"\nEO crosstalk B/A from the gap fields (dB): Zs {p['Zs_R']} ohm, Zt {p['Rt_R']} ohm, {p['drive_config']}, n_g {p['ng']}")
res = {}
for k in RUNS:
    pair = X.load_pair(os.path.join(RUNS[k], S4P[k]), 8.0)
    fd = XF.load_field_dir(RUNS[k])
    res[k] = XF.eo_crosstalk_fields(p, fd, pair)
print(" f GHz | CORDOBA | CORDOBA HZ | HZ - CORDOBA")
for i, g in enumerate(res["CORDOBA"]["f_GHz"]):
    a, b = d(res["CORDOBA"]["X"][i]), d(res["CORDOBA HZ"]["X"][i])
    print(f" {g:5.0f} | {a:7.1f} | {b:10.1f} | {b-a:+6.1f}")
