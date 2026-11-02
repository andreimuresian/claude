"""30 GHz fit of the electric-bottom TD gap fields with the electric-bottom EVEN eigenmodes (cpw, slot,
strips-vs-bottom) and, until the odd run is in, the open-bottom ODD modes (cpw, slot, A vs B).
Same machinery as ../cordoba_8mm/modefit/fit30.py (exact sectors, fixed n, loss, cell patterns,
T-stem positions excluded). Then: residual vs a free extra wave (A-vs-B pattern, free n and loss).

NOT VALID until the odd electric-bottom run replaces the open-bottom odd modes: line B is the small
difference (Se - So)/2 of two nearly equal CPW contributions, and even and odd patterns from different
meshes differ by about 1 % point to point (new vs old even CPW pattern: identical shape, 0.3-1.2 % noise).
That 1 % of line A is about -40 dB, above B (-53 dB), so the mixed fit fails even on A (0.45 vs 0.014).
The earlier fits used even and odd runs on the same mesh, where this noise cancels."""
import os, sys, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../cordoba_8mm/modefit"))
os.environ["FIELDS"] = HERE
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import fit30 as F
F.EIG = os.path.join(HERE, "../cordoba_8mm/eigen_w1.2mm_mag_ebottom")
OPEN = "../eigen_w1.2mm_mag/"
F.MODES = {
    "e_sb":   ("eig_even_mode1_stripsvsbottom.txt", 21.7364055801, 172.8, None),
    "e_slot": ("eig_even_mode2_slot.txt", 28.6810118013, 29.86, None),
    "e_cpw":  ("eig_even_mode3_cpw.txt", 31.0361181988, 26.27, 2.229),
    "o_AvsB": (OPEN + "eig_odd_mode1_AvsB.txt", 22.4143168874, 4.604, None),
    "o_slot": (OPEN + "eig_odd_mode2_slot.txt", 28.8667173152, 33.498, None),
    "o_cpw":  (OPEN + "eig_odd_mode3_cpw.txt", 31.0302771383, 26.260, 2.227),
}
for nm, (fn, f, Q, ng) in F.MODES.items():
    g, n, adb = F.gamma(f, Q, ng); print(f"{nm:7s} f {f:8.4f} GHz  n(30 GHz) {n:.4f}  alpha {adb:5.2f} dB/cm")
print("\nmodel                                   | A CPW | B' all | B' CPW | B' slot")
for lab, ne, no in (("CPW pair", ["e_cpw"], ["o_cpw"]),
                    ("CPW + slot pairs", ["e_cpw", "e_slot"], ["o_cpw", "o_slot"]),
                    ("+ A vs B (open-bottom odd)", ["e_cpw", "e_slot"], ["o_cpw", "o_slot", "o_AvsB"]),
                    ("+ strips vs bottom (new even mode)", ["e_cpw", "e_slot", "e_sb"], ["o_cpw", "o_slot", "o_AvsB"])):
    o = F.fit(ne, no); print(f"{lab:40s}| {o['rAc']:.3f} | {o['rB']:.3f}  | {o['rBc']:.3f}  | {o['rBs']:.3f}")
# free extra wave on top of all six
orig = F.gamma
def run(n_x, a_x):
    def g(f_GHz, Q, ng, n_override=None):
        if abs(f_GHz - 22.4143168874) < 1e-6:
            return a_x * 100 / 8.686 + 1j * n_x * 2 * np.pi * F.F / F.C0, n_x, a_x
        return orig(f_GHz, Q, ng)
    F.gamma = g; o = F.fit(["e_cpw", "e_slot", "e_sb"], ["o_cpw", "o_slot", "o_AvsB"]); F.gamma = orig; return o
best = sorted((run(n, a)["rBc"], n, a) for n in np.arange(2.30, 3.401, 0.025) for a in (1, 2, 3, 5, 8, 12))
print("\nwith the new mode, A-vs-B slot replaced by a free wave: best", " | ".join(f"n {n:.3f} a {a} -> B' CPW {r:.3f}" for r, n, a in best[:3]))
prof = {}
for r, n, a in best: prof[round(n, 3)] = min(prof.get(round(n, 3), 9), r)
print("  best residual vs n:", " ".join(f"{n:.2f}:{v:.2f}" for n, v in sorted(prof.items())))
o = F.fit(["e_cpw", "e_slot", "e_sb"], ["o_cpw", "o_slot", "o_AvsB"]); ref = abs(o["x"]["e_cpw+"])
print("\namplitudes / e_cpw+ (six modes):", ", ".join(f"{k} {abs(v)/ref:.2e}" for k, v in o["x"].items()))

# INTERIM: the odd modes above are open-bottom. Mixing them with electric-bottom even modes makes the CPW
# split e - o = -5e-4 (artefact: open-bottom split 3.4e-5), which ruins line A. Until the odd run is in,
# impose the open-bottom CPW split on the pair (dbeta_cpw) and repeat.
k0 = 2 * np.pi * F.F / F.C0
ne = F.gamma(*F.MODES["e_cpw"][1:])[1]; no = F.gamma(*F.MODES["o_cpw"][1:])[1]
d = k0 * (3.36e-5 - (ne - no))
print(f"\nINTERIM, CPW split forced to 3.36e-5 (was {ne-no:.2e} from mixed runs):")
print("model                                   | A CPW | B' all | B' CPW | B' slot")
for lab, ne_, no_ in (("CPW + slot pairs", ["e_cpw", "e_slot"], ["o_cpw", "o_slot"]),
                      ("+ A vs B", ["e_cpw", "e_slot"], ["o_cpw", "o_slot", "o_AvsB"]),
                      ("+ strips vs bottom", ["e_cpw", "e_slot", "e_sb"], ["o_cpw", "o_slot", "o_AvsB"])):
    o = F.fit(ne_, no_, dbeta_cpw=d); print(f"{lab:40s}| {o['rAc']:.3f} | {o['rB']:.3f}  | {o['rBc']:.3f}  | {o['rBs']:.3f}")
def run2(n_x, a_x):
    def g(f_GHz, Q, ng, n_override=None):
        if abs(f_GHz - 22.4143168874) < 1e-6:
            return a_x * 100 / 8.686 + 1j * n_x * 2 * np.pi * F.F / F.C0, n_x, a_x
        return orig(f_GHz, Q, ng)
    F.gamma = g; o = F.fit(["e_cpw", "e_slot", "e_sb"], ["o_cpw", "o_slot", "o_AvsB"], dbeta_cpw=d); F.gamma = orig; return o
best = sorted((run2(n, a)["rBc"], n, a) for n in np.arange(2.30, 3.401, 0.025) for a in (1, 2, 3, 5, 8, 12))
print("free extra wave (A-vs-B pattern) on top: best", " | ".join(f"n {n:.3f} a {a} -> B' CPW {r:.3f}" for r, n, a in best[:3]))
prof = {}
for r, n, a in best: prof[round(n, 3)] = min(prof.get(round(n, 3), 9), r)
print("  best residual vs n:", " ".join(f"{n:.2f}:{v:.2f}" for n, v in sorted(prof.items())))
o = run2(best[0][1], best[0][2]); ref = abs(o["x"]["e_cpw+"])
print("amplitudes / e_cpw+ (with the free wave):", ", ".join(f"{k} {abs(v)/ref:.2e}" for k, v in o["x"].items()))
o = F.fit(["e_cpw", "e_slot", "e_sb"], ["o_cpw", "o_slot", "o_AvsB"], dbeta_cpw=d); ref = abs(o["x"]["e_cpw+"])
print("amplitudes / e_cpw+ (six modes):", ", ".join(f"{k} {abs(v)/ref:.2e}" for k, v in o["x"].items()))
