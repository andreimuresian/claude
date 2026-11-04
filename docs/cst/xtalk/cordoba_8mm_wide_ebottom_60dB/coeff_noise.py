"""How well the data determine the B-side coefficients: add complex Gaussian noise to B's gap data with rms = 10 %
of B (the size of the fit residual and of the estimated remaining truncation error), refit 30 times, report the
scatter of each normalised B-side coefficient relative to its value; also the scatter of the model EO."""
import os, sys, copy
HERE = os.path.dirname(os.path.abspath(__file__)); os.environ["TDDIR"] = HERE
exec(open(os.path.join(HERE, "smoothness.py")).read().split("C = {f: coeffs")[0])
rng = np.random.default_rng(1)
grp = {"CPW fwd B": lambda c: 0.5*(c["e_cpw+"]-c["o_cpw+"]), "CPW bwd B": lambda c: 0.5*(c["e_cpw-"]-c["o_cpw-"]),
       "slot fwd B": lambda c: 0.5*(c["e_slot+"]-c["o_slot+"]), "sb fwd": lambda c: c["e_sb+"], "sb bwd": lambda c: c["e_sb-"],
       "AvsB fwd": lambda c: c["o_AvsB+"], "AvsB bwd": lambda c: c["o_AvsB-"]}
print(" f  | relative scatter (std/|value|) at 10 % noise on B: " + " | ".join(grp) + " | EO dB std")
for f in F:
    td = TD[f]; c0 = coeffs(fits[f]["x"], f); s = {k: [] for k in grp}; eo = []
    rmsB = np.sqrt(np.mean(abs(td.Bp)**2))
    for _ in range(30):
        t = copy.copy(td); t.Bp = td.Bp + 0.1*rmsB*(rng.standard_normal(td.Bp.shape)+1j*rng.standard_normal(td.Bp.shape))/np.sqrt(2)
        o = S.fit(int(f), t); c = coeffs(o["x"], f)
        for k, g in grp.items(): s[k].append(g(c))
        eo.append(20*np.log10(abs(o["eo"]["Hm_B"]/o["eo"]["Hm_A"])))
    print(f"{f:3.0f} | " + " | ".join(f"{np.std(s[k])/abs(grp[k](c0)):6.2f}" for k in grp) + f" | {np.std(eo):.2f}")
