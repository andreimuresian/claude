"""30 GHz, electric bottom: contribution of each fitted wave (six electric-bottom eigenmodes) to B's EO
integral H (push-pull pattern, n_g 2.27), on the kept samples of the interior, relative to H[data]."""
import os, sys, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    sys.argv = ["x"]; exec(open(os.path.join(HERE, "fit30_ebottom_modes.py")).read().split("# free extra wave")[0])
import numpy as np
o = F.fit(E, O)
ce, le = F.basis(E); co, lo = F.basis(O)
comps = {l: 0.5 * c * o["x"][l] for c, l in zip(ce, le)}
comps.update({l: -0.5 * c * o["x"][l] for c, l in zip(co, lo)})
cpw = lambda v: (v[0] - v[1]) / 2
bo = 2 * np.pi * F.F * 2.27 / F.C0
H = lambda c: np.mean(c * np.exp(1j * bo * (F.zz - F.L)))
Hd = H(cpw(F.Bp)); Hm = H(cpw(o["mB"]))
print(f"|H| / |H[data]|: model {abs(Hm)/abs(Hd):.3f} ({np.angle(Hm/Hd, deg=True):+.1f} deg), residual {abs(Hd-Hm)/abs(Hd):.3f}")
groups = {"CPW pair forward": ["e_cpw+", "o_cpw+"], "CPW pair backward": ["e_cpw-", "o_cpw-"],
          "slot pairs": ["e_slot+", "e_slot-", "o_slot+", "o_slot-"],
          "strips vs bottom forward": ["e_sb+"], "strips vs bottom backward": ["e_sb-"], "A vs B": ["o_AvsB+", "o_AvsB-"]}
for g, ls in groups.items():
    h = sum(H(cpw(comps[l])) for l in ls)
    print(f"  {g:26s} |H| {abs(h)/abs(Hd):.3f} ({np.angle(h/Hd, deg=True):+6.1f} deg)")
