"""Currents on line A's three conductors (Ampere loops around each strip) for
eigenmode 3, even and odd. A pure signal-vs-own-grounds (GSG) mode has
I_signal = -(I_g1 + I_g2); a net line current returns through the enclosure
(even) or the neighbouring line (odd).  usage: python eig_conductor_currents.py [zip]"""
import sys, numpy as np
src = open("eig_impedance.py").read().split("Pe, Ve")[0]
exec(src)
from eig_z_definitions import loop_current
strips = {"ground 1": (28.5e-6, 78.35e-6), "signal": (82.5e-6, 117.5e-6), "ground 2": (121.65e-6, 171.5e-6)}
for tag in ("even", "odd"):
    _, _, H = load(f"Mode_3_h_{tag}.txt"); x, y, E = load(f"Mode_3_e_{tag}.txt")
    I = {k: loop_current(x, y, H, -1e-6, 3e-6, a - 1e-6, b + 1e-6) for k, (a, b) in strips.items()}
    s = I["signal"]
    net = sum(I.values())
    print(f"{tag}: I_g1/I_s = {I['ground 1']/s:+.4f}  I_g2/I_s = {I['ground 2']/s:+.4f}  "
          f"net line current / I_s = {net/s:+.4f}")
