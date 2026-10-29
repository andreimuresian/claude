"""Hypothesis-1 check at 30 GHz: replace the A-vs-B pattern by the one of the narrow cell with the
electric side wall (pair-odd mode 1, 27.3534 GHz, n 2.537, Q 33.7), index and loss fixed at that
mode's values and then scanned; compare with the 1.2 mm magnetic A-vs-B pattern."""
import numpy as np, fit30 as F
F.MODES["o_AvsBn"] = ("eig_odd_mode1_AvsB_narrow_electric.txt", 27.3533895641, 33.699, None)
ub, uf, ph = F.pattern("eig_odd_mode1_AvsB_narrow_electric.txt")
c = (ub[0] - ub[1]) / 2; s = (ub[0] + ub[1]) / 2
r = lambda x: np.sqrt(np.mean(abs(x) ** 2))
print(f"narrow electric A vs B: phase/cell {ph:+.2f} deg, CPW/slot in the gaps {r(c)/r(s):.3f}")
ub2, _, _ = F.pattern("eig_odd_mode1_AvsB.txt")
print(f"1.2 mm magnetic A vs B: CPW/slot {r((ub2[0]-ub2[1])/2)/r((ub2[0]+ub2[1])/2):.3f}")
g, n, adb = F.gamma(*F.MODES["o_AvsBn"][1:])
print(f"own values at 30 GHz: n {n:.4f}, alpha {adb:.2f} dB/cm")
base = ["e_cpw", "e_slot"], ["o_cpw", "o_slot"]
for lab, extra in (("no A vs B", []), ("A vs B 1.2 mm magnetic (own n, alpha)", ["o_AvsB"]),
                   ("A vs B narrow electric (own n, alpha)", ["o_AvsBn"])):
    o = F.fit(base[0], base[1] + extra)
    print(f"{lab:40s} A {o['rA']:.3f}  A CPW {o['rAc']:.3f}  B' {o['rB']:.3f}  B' CPW {o['rBc']:.3f}  B' slot {o['rBs']:.3f}")
orig = F.gamma
def run(key, fkey, n_, a_):
    def gg(f_GHz, Q, ng, n_override=None):
        if abs(f_GHz - fkey) < 1e-6:
            return a_ * 100 / 8.686 + 1j * n_ * 2 * np.pi * F.F / F.C0, n_, a_
        return orig(f_GHz, Q, ng)
    F.gamma = gg
    o = F.fit(base[0], base[1] + [key]); F.gamma = orig
    return o
for key, fkey, lab in (("o_AvsBn", 27.3533895641, "narrow electric pattern"), ("o_AvsB", 22.4143168874, "1.2 mm magnetic pattern")):
    res = sorted((run(key, fkey, n_, a_)["rBc"], n_, a_) for n_ in np.arange(2.30, 2.76, 0.025) for a_ in (0, 1, 2, 3, 5, 8))
    b = res[0]; o = run(key, fkey, b[1], b[2])
    print(f"free n, alpha with {lab}: best n {b[1]:.3f}, {b[2]} dB/cm -> A {o['rA']:.3f}, B' {o['rB']:.3f}, B' CPW {o['rBc']:.3f}, B' slot {o['rBs']:.3f}")
    print("   B' CPW resid vs n (alpha = best):", " ".join(f"{n_:.2f}:{run(key, fkey, n_, b[2])['rBc']:.3f}" for n_ in np.arange(2.35, 2.71, 0.05)))
