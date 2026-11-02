"""30 GHz fit of the electric-bottom TD gap fields (widened CORDOBA) with the electric-bottom eigenmodes
(2 mm cell, Ymax magnetic 616 um beyond the outer ground, Si 525 um on an electric wall; even and odd runs on the same model):
even cpw, slot, strips-vs-bottom; odd cpw, slot, A vs B. Same machinery as
../cordoba_8mm/modefit/fit30.py (exact sectors, fixed n, loss and cell patterns, T-stem positions
excluded). Then: a free extra wave (A-vs-B pattern) added on top, scanned in n and loss.
(Even and odd modes must come from the same model and mesh: B is the small difference of two nearly
equal CPW terms, and pattern noise between meshes, about 1 % of A, would swamp it.)"""
import os, sys, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../cordoba_8mm/modefit"))
os.environ["FIELDS"] = HERE
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import fit30 as F
F.EIG = os.path.join(HERE, "../cordoba_8mm/eigen_w2mm_mag_ebottom")
F.MODES = {
    "e_sb":   ("eig_even_mode1_e.txt", 22.2635700716, 38.28, None),
    "e_slot": ("eig_even_mode2_e.txt", 28.7474073186, 30.33, None),
    "e_cpw":  ("eig_even_mode3_e.txt", 31.0442220176, 26.28, 2.229),
    "o_AvsB": ("eig_odd_mode1_e.txt", 23.8567966499, 13.61, None),
    "o_slot": ("eig_odd_mode2_e.txt", 28.9257077157, 34.17, None),
    "o_cpw":  ("eig_odd_mode3_e.txt", 31.0445460781, 26.28, 2.229),
}
for nm, (fn, f, Q, ng) in F.MODES.items():
    g, n, adb = F.gamma(f, Q, ng); print(f"{nm:7s} f {f:8.4f} GHz  n(30 GHz) {n:.5f}  alpha {adb:5.2f} dB/cm")
E = ["e_cpw", "e_slot", "e_sb"]; O = ["o_cpw", "o_slot", "o_AvsB"]
print("\nmodel                                   | A CPW | B' all | B' CPW | B' slot")
for lab, ne, no in (("CPW pair", ["e_cpw"], ["o_cpw"]),
                    ("CPW + slot pairs", ["e_cpw", "e_slot"], ["o_cpw", "o_slot"]),
                    ("+ A vs B", ["e_cpw", "e_slot"], O),
                    ("+ strips vs bottom (all six)", E, O)):
    o = F.fit(ne, no); print(f"{lab:40s}| {o['rAc']:.3f} | {o['rB']:.3f}  | {o['rBc']:.3f}  | {o['rBs']:.3f}")
o = F.fit(E, O); ref = abs(o["x"]["e_cpw+"])
print("amplitudes / e_cpw+ (six modes):", ", ".join(f"{k} {abs(v)/ref:.2e}" for k, v in o["x"].items()))
# free extra wave (A-vs-B pattern of the open-bottom cell, as in the earlier scans) on top of the six
F.MODES["x_free"] = ("../eigen_w1.2mm_mag/eig_odd_mode1_AvsB.txt", 22.4143168874, 4.604, None)
orig = F.gamma
def run(n_x, a_x):
    def g(f_GHz, Q, ng, n_override=None):
        if abs(f_GHz - 22.4143168874) < 1e-6:
            return a_x * 100 / 8.686 + 1j * n_x * 2 * np.pi * F.F / F.C0, n_x, a_x
        return orig(f_GHz, Q, ng)
    F.gamma = g; o = F.fit(E, O + ["x_free"]); F.gamma = orig; return o
best = sorted((run(n, a)["rBc"], n, a) for n in np.arange(2.30, 3.401, 0.025) for a in (1, 2, 3, 5, 8, 12))
print("\nsix modes + free wave: best", " | ".join(f"n {n:.3f} a {a} -> B' CPW {r:.3f}" for r, n, a in best[:3]))
prof = {}
for r, n, a in best: prof[round(n, 3)] = min(prof.get(round(n, 3), 9), r)
print("  best residual vs n:", " ".join(f"{n:.2f}:{v:.2f}" for n, v in sorted(prof.items())))
o = run(best[0][1], best[0][2]); ref = abs(o["x"]["e_cpw+"])
print(f"  at the best: A CPW {o['rAc']:.3f}, B' all {o['rB']:.3f}, B' slot {o['rBs']:.3f}")
print("  amplitudes / e_cpw+:", ", ".join(f"{k} {abs(v)/ref:.2e}" for k, v in o["x"].items()))
