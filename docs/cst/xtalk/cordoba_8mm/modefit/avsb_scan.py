"""30 GHz: residual on B's CPW pattern vs the A-against-B index and loss (other modes fixed
at the eigenmode values). Tests whether the end-localised remainder is that mode."""
import numpy as np, fit30 as F
orig = F.gamma
def run(n_avsb, a_dbcm):
    def g(f_GHz, Q, ng, n_override=None):
        if abs(f_GHz - 22.4143168874) < 1e-6:
            beta = n_avsb * 2 * np.pi * F.F / F.C0; alpha = a_dbcm * 100 / 8.686
            return alpha + 1j * beta, n_avsb, a_dbcm
        return orig(f_GHz, Q, ng)
    F.gamma = g
    o = F.fit(["e_cpw", "e_slot"], ["o_cpw", "o_slot", "o_AvsB"])
    F.gamma = orig
    return o
best = None
print(" n_AvsB  a(dB/cm) | B' CPW  B' all  A")
for n in np.arange(2.6, 3.21, 0.05):
    for a in (5, 10, 15, 20, 30):
        o = run(n, a)
        if best is None or o["rBc"] < best[0]:
            best = (o["rBc"], n, a, o["rB"], o["rA"])
        if a in (10, 15):
            print(f" {n:5.2f}   {a:4.0f}     | {o['rBc']:.3f}  {o['rB']:.3f}  {o['rA']:.3f}")
print(f"best: n {best[1]:.2f}, a {best[2]} dB/cm -> B' CPW {best[0]:.3f}, B' all {best[3]:.3f}, A {best[4]:.3f}")
o = run(best[1], best[2])
cpw = lambda v: (v[0] - v[1]) / 2
rB = cpw(F.Bp) - cpw(o["mB"]); dB = cpw(F.Bp); zz = F.zz * 1e3; nrm = np.sqrt(np.mean(abs(dB) ** 2))
print(" z (mm): remainder / rms(data):", " ".join(f"{a:.1f}:{np.sqrt(np.mean(abs(rB[abs(zz-a)<0.25])**2))/nrm:.2f}" for a in np.arange(0.5, 7.6, 1.0)))
