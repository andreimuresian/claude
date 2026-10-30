"""30 GHz: victim CPW-pattern residual of the five-mode fit when the A-vs-B wave takes a free
index n and loss a (other four modes fixed at the eigenmode values), over a wider grid than
../cordoba_8mm/modefit/avsb_scan.py. Run with FIELDS=<run folder>."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../cordoba_8mm/modefit"))
import numpy as np, avsb_scan as S
best = []
for n in np.arange(2.30, 3.201, 0.025):
    for a in (0.5, 1, 2, 3, 5, 8, 12, 16):
        o = S.run(n, a); best.append((o["rBc"], n, a, o["rB"], o["rA"]))
best.sort()
print(f"fields: {os.environ.get('FIELDS')}")
for r in best[:5]:
    print(f"  n {r[1]:.3f}  a {r[2]:4.1f} dB/cm -> B' CPW {r[0]:.3f}, B' all {r[3]:.3f}, A {r[4]:.3f}")
prof = {}
for r in best:
    prof[r[1]] = min(prof.get(r[1], 9), r[0])
print("  best residual vs n:", " ".join(f"{n:.2f}:{v:.2f}" for n, v in sorted(prof.items()) if abs((n * 40) % 2) < 1e-6 or True)[:2000])
