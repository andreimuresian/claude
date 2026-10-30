"""30 GHz, widened run: how much of B's EO integral comes from each fitted wave?
Fit: five eigenmodes (1.2 mm magnetic cell, fixed n, loss, cell patterns) plus the A-vs-B pattern with
free n 2.475, 3 dB/cm (the extra wave), on the kept (non-stem) samples of the interior 0.31-7.69 mm.
EO weight of a field component c(z) on B (push-pull pattern): H[c] = mean_z c(z) exp(j beta_o (z - L)),
beta_o = 2 pi f 2.27 / c, over the same samples. Contributions are complex and add up to H[model];
H[data] - H[model] = H[residual]."""
import os, sys, io, contextlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../cordoba_8mm/modefit"))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../..")))
os.environ["FIELDS"] = os.environ.get("FIELDS") or os.path.dirname(os.path.abspath(__file__))
import numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    import avsb_scan as S
F = S.F
o = S.run(2.475, 3.0)
# rebuild the per-component model on B' (same construction as fit30.fit)
def gfree(f_GHz, Q, ng, n_override=None):
    if abs(f_GHz - 22.4143168874) < 1e-6:
        return 3.0 * 100 / 8.686 + 1j * 2.475 * 2 * np.pi * F.F / F.C0, 2.475, 3.0
    return S.orig(f_GHz, Q, ng)
F.gamma = gfree
ce, le = F.basis(["e_cpw", "e_slot"]); co, lo = F.basis(["o_cpw", "o_slot", "o_AvsB"])
F.gamma = S.orig
comps = {}
for c, l in zip(ce, le): comps[l] = 0.5 * c * o["x"][l]            # B' = (Se - So)/2
for c, l in zip(co, lo): comps[l] = -0.5 * c * o["x"][l]
cpw = lambda v: (v[0] - v[1]) / 2
bo = 2 * np.pi * F.F * 2.27 / F.C0
H = lambda c: np.mean(c * np.exp(1j * bo * (F.zz - F.L)))
Hd = H(cpw(F.Bp)); Hm = H(cpw(o["mB"]))
print(f"B CPW pattern, 30 GHz, wide run. |H| relative to |H[data]| (phase vs data):")
print(f"  data           1.000")
print(f"  model (sum)    {abs(Hm)/abs(Hd):.3f}  ({np.angle(Hm/Hd, deg=True):+6.1f} deg)")
print(f"  residual       {abs(Hd-Hm)/abs(Hd):.3f}")
groups = {"CPW pair forward (e+o)": ["e_cpw+", "o_cpw+"], "CPW pair backward": ["e_cpw-", "o_cpw-"],
          "slot pair forward": ["e_slot+", "o_slot+"], "slot pair backward": ["e_slot-", "o_slot-"],
          "extra wave forward (n 2.475)": ["o_AvsB+"], "extra wave backward (n 2.475)": ["o_AvsB-"]}
for g, ls in groups.items():
    h = sum(H(cpw(comps[l])) for l in ls)
    rms = np.sqrt(np.mean(abs(sum(cpw(comps[l]) for l in ls)) ** 2)) / np.sqrt(np.mean(abs(cpw(F.Bp)) ** 2))
    print(f"  {g:30s} |H| {abs(h)/abs(Hd):.3f} ({np.angle(h/Hd, deg=True):+6.1f} deg) | share of B's CPW-pattern rms {rms:.2f}")
# the same weight on the full 0-8 mm with all samples, data only, to see the share of the ends
from mzm_interconnect.xtalk_fields import load_field_dir
fd = load_field_dir(os.environ["FIELDS"]); z = fd["z"]; p, m = fd["ports"][30.0][1]["B"]; v = (p - m) / 2
Hall = np.trapezoid(v * np.exp(1j * bo * (z - z[-1])), z) / (z[-1] - z[0])
inn = (z >= 0.31e-3) & (z <= 7.69e-3)
Hin = np.trapezoid((v * np.exp(1j * bo * (z - z[-1])))[inn], z[inn]) / (z[-1] - z[0])
print(f"\nends: |H| over 0-8 mm / over the interior 0.31-7.69 mm (same normalisation): {abs(Hall)/abs(Hin):.3f}")
