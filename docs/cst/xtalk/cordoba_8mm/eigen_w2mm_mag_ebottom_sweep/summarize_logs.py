"""
Phase sweep, 2 mm cell, electric bottom: tables from the solver logs (p*/log_excerpt.txt) plus the 15 deg run.
n = c*phi/(2*pi*f*p), p = 0.18 mm. n_g from the slope of f vs phase per family (central differences).
Spatial attenuation from Q: alpha = omega/(2 Q v_g) (complex-frequency eigenvalue at real beta).
Substrate cell modes: compared with the TM0 wave of 525 um Si (11.9) on a perfect conductor, with a lateral
standing wave between Ymin (y = 0, symmetry plane) and the magnetic wall at y = 1.0 mm.
"""
import os, re, glob
import numpy as np
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
C, P = 299.792458, 0.18          # mm*GHz, mm
runs = {}
for d in sorted(glob.glob(os.path.join(HERE, "p*_*"))):
    m = re.match(r"p(\d+)_(even|odd)", os.path.basename(d))
    rows = re.findall(r"^\s+(\d+)\s+([\d.]+) GHz\s+([\d.]+)", open(os.path.join(d, "log_excerpt.txt")).read(), re.M)
    runs[(int(m.group(1)), m.group(2))] = [(float(f), float(q)) for _, f, q in rows]
runs[(15, "even")] = [(22.2635700716, 38.28), (28.7474073186, 30.33), (31.0442220176, 26.28), (57.6845, 6.1)]
runs[(15, "odd")] = [(23.8567966499, 13.61), (28.9257077157, 34.17), (31.0445460781, 26.28), (49.4865, 5.2), (58.6331, 5.3)]
n_of = lambda ph, f: C * ph / 360.0 / (f * P)

def tm0(f, d=0.525, er=11.9):
    k0 = 2 * np.pi * f / C
    g = lambda u: u * np.tan(u) - er * np.sqrt(max((er - 1) * (k0 * d) ** 2 - u * u, 0))
    umax = min(np.sqrt(er - 1) * k0 * d, np.pi / 2 - 1e-9)
    u = brentq(g, 1e-9, umax - 1e-12)
    return np.sqrt(er - (u / (k0 * d)) ** 2)

fams = {"even": ["strips vs bottom", "slot", "CPW"], "odd": ["A vs B", "slot", "CPW"]}
out = []
for sym in ("even", "odd"):
    print(f"\n=== {sym}: guided families (first three modes of every run) ===")
    for k, name in enumerate(fams[sym]):
        ph = np.array([p for p in (5, 10, 15, 20, 25, 30) if len(runs[(p, sym)]) > k])
        f = np.array([runs[(p, sym)][k][0] for p in ph]); q = np.array([runs[(p, sym)][k][1] for p in ph])
        n = n_of(ph, f)
        ng = (C / P / 360.0) / np.gradient(f, ph)          # n_g = c dbeta/domega
        a = 2 * np.pi * f / (2 * q) * ng / C * 8.686        # dB/mm
        print(f"{name}:")
        for i in range(len(ph)):
            print(f"  {ph[i]:2d} deg  f {f[i]:8.4f}  n {n[i]:.4f}  n_g {ng[i]:.3f}  Q {q[i]:6.2f}  alpha {a[i]:.3f} dB/mm")
            out.append((sym, name, ph[i], f[i], n[i], ng[i], q[i], a[i]))
    print("  split even-odd: ")
print("\nEven/odd splits (odd - even) / even, frequency at equal phase:")
for p in (5, 10, 15, 20, 25, 30):
    e, o = runs[(p, "even")], runs[(p, "odd")]
    s = f"  {p:2d} deg  slot {(o[1][0]-e[1][0])/e[1][0]:+.2e}"
    if len(e) > 2 and len(o) > 2: s += f"  CPW {(o[2][0]-e[2][0])/e[2][0]:+.2e}"
    print(s)

print("\n=== extra modes (beyond the three guided families) vs the TM0 cell-mode model ===")
print("TM0 index of 525 um Si on PEC:", ", ".join(f"{f} GHz {tm0(f):.3f}" for f in (30, 45, 50, 55, 60)))
W = 1.0
for (p, sym), modes in sorted(runs.items()):
    for f, q in modes[3:]:
        nz = n_of(p, f); k0 = 2 * np.pi * f / C
        ny = np.sqrt(max(tm0(f) ** 2 - nz ** 2, 0))
        ky = ny * k0                                        # 1/mm
        order = ky * W / (np.pi / 2)                        # in quarter waves across 1 mm
        print(f"  {p:2d} deg {sym:4s}  f {f:7.3f}  n_z {nz:.3f}  Q {q:5.2f}  TM0 {tm0(f):.3f}  k_y W/(pi/2) = {order:.2f}")
np.savetxt(os.path.join(HERE, "guided_families.csv"),
           np.array([(s[2], s[3], s[4], s[5], s[6], s[7]) for s in out]), delimiter=",", fmt="%.6g",
           header="rows in order: " + "; ".join(sorted({f'{s[0]} {s[1]}' for s in out})) +
           "\nphase_deg,f_GHz,n,n_g,Q,alpha_dB_per_mm  (see summarize_logs.log for labels)")
