"""Widened CORDOBA run (substrate 625 um beyond the outer grounds) against the narrow one (21 um):
1) S-parameter column 1 (only port 1 was driven in the widened run): S11, S21, NEXT = S31, FEXT = S41.
2) Gap fields point by point: |wide - narrow| / |narrow| on A and B (CPW and slot patterns).
3) EO crosstalk B/A from the fields (50 ohm source and load, push-pull, n_g 2.27)."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import numpy as np, skrf
from mzm_interconnect import parameters as P, xtalk_fields as XF
HERE = os.path.dirname(os.path.abspath(__file__)); NAR = os.path.join(HERE, "../cordoba_8mm")
d = lambda x: 20 * np.log10(np.abs(x) + 1e-30)
nw = skrf.Network(os.path.join(HERE, "LINEA_8MM_625UM_PITCH_CORDOBA_OAD_1port.s4p"))
nn = skrf.Network(os.path.join(NAR, "LINEA_8MM_625UM_PITCH_CORDOBA.s4p"))
assert np.allclose(nw.f, nn.f)
f = nw.f; w = 2 * np.pi * f
print("columns 2-4 of the widened s4p, max |S|:", f"{np.abs(nw.s[:, :, 1:]).max():.1e}", "(not computed: only port 1 driven)")
gd = lambda x: -np.gradient(np.unwrap(np.angle(x)), w)
print("\n f GHz |  S11 n/w      |  S21 n/w        |  NEXT n/w       |  FEXT n/w       | |S41w-S41n|/|S41n|")
for g in (1, 2, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60):
    i = np.argmin(abs(f - g * 1e9)); a, b = nn.s[i], nw.s[i]
    print(f" {g:5d} | {d(a[0,0]):6.1f} {d(b[0,0]):6.1f} | {d(a[1,0]):7.3f} {d(b[1,0]):7.3f} | {d(a[2,0]):6.1f} {d(b[2,0]):6.1f} | "
          f"{d(a[3,0]):6.1f} {d(b[3,0]):6.1f} | {abs(b[3,0]-a[3,0])/abs(a[3,0]):.3f}")
sel = (f >= 5e9) & (f <= 50e9)
for k, n in (("narrow", nn), ("wide", nw)):
    t = [np.median(gd(n.s[:, a, 0])[sel]) * 1e12 for a in (1, 2, 3)]
    print(f"{k:6s}: delay S21 {t[0]:.2f} ps (n_g {t[0]*1e-12*2.99792458e8/8e-3:.4f}), NEXT {t[1]/t[0]:.2f}x, FEXT {t[2]/t[0]:.2f}x")
fn, fw = XF.load_field_dir(NAR), XF.load_field_dir(HERE)
z = fn["z"]; assert np.allclose(z, fw["z"])
inn = (z >= 0.31e-3) & (z <= 7.69e-3)
print("\nGap fields, interior z 0.31-7.69 mm: rms|wide - narrow| / rms|narrow|")
print(" f GHz | A CPW   A slot | B CPW   B slot")
for g in fn["f_GHz"]:
    row = f" {g:5.0f} |"
    for L in "AB":
        pn, mn = fn["ports"][g][1][L]; pw, mw = fw["ports"][g][1][L]
        for pat in (lambda p, m: p - m, lambda p, m: p + m):   # CPW: V+ + V- = Ey+ - Ey-; slot: Ey+ + Ey-
            a, b = pat(pn, mn)[inn], pat(pw, mw)[inn]
            row += f" {np.linalg.norm(b - a) / np.linalg.norm(a):6.3f}"
        row += " |"
    print(row)
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
rn, rw = XF.eo_crosstalk_fields(p, fn), XF.eo_crosstalk_fields(p, fw)
print("\nEO crosstalk B/A from the fields (dB), 50/50 ohm, push-pull, n_g", p["ng"])
print(" f GHz | narrow | wide  | wide - narrow")
for i, g in enumerate(rn["f_GHz"]):
    print(f" {g:5.0f} | {d(rn['X'][i]):6.1f} | {d(rw['X'][i]):5.1f} | {d(rw['X'][i]) - d(rn['X'][i]):+5.1f}")
