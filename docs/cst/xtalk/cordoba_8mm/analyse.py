"""
CORDOBA 8 mm slow-wave pair (LN 200 nm, SiO2 4.7 um, Si 525 um open bottom, T pitch 180 um,
~15 cells across the gaps). Ports 1 A near, 2 A far, 3 B near, 4 B far.
Through-line index, even/odd split, NEXT/FEXT, symmetry floors; side by side with the
Istanbul 5 mm (coarse TD mesh) and the std 8 mm LOW_Z (same gap, uniform).
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import numpy as np, skrf
from mzm_interconnect import xtalk_s4p as X
here = os.path.dirname(os.path.abspath(__file__))
d = lambda x: 20 * np.log10(np.abs(x) + 1e-30)
runs = {"CORDOBA 8mm": (os.path.join(here, "LINEA_8MM_625UM_PITCH_CORDOBA.s4p"), 8.0),
        "Istanbul 5mm": (os.path.join(here, "../istanbul/TEST0_XTALK_SW_5mm - wider.s4p"), 5.0),
        "std LOW_Z 8mm": (os.path.join(here, "../std_8mm/LINEA_8MM_625UM_PITCH_STD_LOW_Z.s4p"), 8.0)}
for k, (p, L) in runs.items():
    if not os.path.exists(p):
        print(k, "missing", p); continue
    pr = X.load_pair(p, L)
    f = pr["f_Hz"]; s = pr["s"]; w = 2 * np.pi * f
    gd = lambda x: -np.gradient(np.unwrap(np.angle(x)), w) * 1e12
    print(f"\n== {k}: data to {f[-1]/1e9:.1f} GHz, A/B asym {pr['sym_ab']:.1e}, end asym {pr['sym_end']:.1e}")
    print(" GHz   n_e     n_o     dn       a_e dB/cm  Z_e        Z_o        S11   S21    NEXT   FEXT  floorN floorF")
    for g in (5, 10, 20, 30, 40, 50, 60, 70, 80):
        if g * 1e9 > f[-1] + 1: continue
        i = np.argmin(abs(f - g * 1e9)); e, o = pr["even"], pr["odd"]; si = s[i]
        fN = abs(si[2, 0] - si[3, 1]); fF = abs(si[3, 0] - si[2, 1])
        print(f"{g:4d} {e['table'][1][i]:7.4f} {o['table'][1][i]:7.4f} {e['table'][1][i]-o['table'][1][i]:+8.5f} "
              f"{e['table'][0][i]/100:7.3f}   {e['Z'][i].real:5.1f}{e['Z'][i].imag:+5.1f}j {o['Z'][i].real:5.1f}{o['Z'][i].imag:+5.1f}j "
              f"{d(si[0,0]):6.1f} {d(si[1,0]):6.2f} {d(si[2,0]):6.1f} {d(si[3,0]):6.1f} {d(fN):6.1f} {d(fF):6.1f}")
    sel = (f >= 5e9) & (f <= 50e9)
    t21, tN, tF = (np.median(gd(s[:, a, 0])[sel]) for a in (1, 2, 3))
    print(f"group delay 5-50 GHz: through {t21:.1f} ps (n_g {t21*1e-12*X.C0/(L*1e-3):.3f}), NEXT {tN:.1f} ps ({tN/t21:.2f}x), FEXT {tF:.1f} ps ({tF/t21:.2f}x)")
    for band in ((2, 20), (20, 40), (40, 60)):
        m = (f >= band[0] * 1e9) & (f <= band[1] * 1e9)
        rms = lambda x: d(np.sqrt(np.mean(abs(x) ** 2)))
        print(f"   {band[0]:2d}-{band[1]:2d} GHz rms NEXT {rms(s[m,2,0]):6.1f} FEXT {rms(s[m,3,0]):6.1f} dB")
