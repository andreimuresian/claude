"""Sweep the signal-electrode width and compare against the two characteristic
impedance anchor points quoted in the thesis (WS=20 um -> ~41 ohm,
WS=100 um -> ~29 ohm, both from the CST 3D time-domain ABCD extraction)."""

import sys
sys.path.insert(0, ".")

from tfln2d import CrossSection, extract

ANCHORS = {20.0: 41.0, 100.0: 29.0}

print(f"{'WS (um)':>8} {'n_m':>8} {'Z0 (ohm)':>10} {'alpha_c':>9} {'CST Z0':>8} {'err':>7}")
for ws in (20.0, 35.0, 60.0, 80.0, 100.0):
    r = extract(CrossSection(ws=ws), resolution=0.25)
    ref = ANCHORS.get(ws)
    ref_s = f"{ref:.1f}" if ref else "-"
    err_s = f"{r.Z0-ref:+.2f}" if ref else "-"
    print(f"{ws:>8.0f} {r.n_m:>8.4f} {r.Z0:>10.3f} {r.alpha_c:>9.3f} {ref_s:>8} {err_s:>7}")
