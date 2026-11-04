"""Reliability of the pencil sign test: apply it to the six-mode model of B (physical waves only, by construction)
evaluated on the full line, with and without the fit residual added back (model + (data - model) = data, so the
residual part is shuffled in z to keep its level but break its structure). TDDIR selects the TD run."""
import numpy as np, copy, sweepfit as S, pencil_gap as P
rng = np.random.default_rng(0)
print(" f | inconsistent share, M 6: model only | model + shuffled residual | data")
for f in S.FTD:
    td = S.TDData(f); o = S.fit(f, td); x = np.array(list(o["x"].values()))
    full = copy.copy(td); full.zz = td.z_full; full.idx = np.round(((td.z_full*1e3-0.04) % 0.18)/0.005).astype(int) % 36
    ce, _, _ = S.basis(("e_cpw","e_slot","e_sb"), f, full); co, _, _ = S.basis(("o_cpw","o_slot","o_AvsB"), f, full)
    mB = np.array([S.cpw(0.5*c) for c in ce] + [S.cpw(-0.5*c) for c in co]).T @ x
    dB = S.cpw(td.Bp_full); r = dB - mB
    out = []
    for v in (mB, mB + rng.permutation(r), dB):
        sn = P.snapshots(v, td.z_full, 0.31e-3, 7.69e-3); p, _, _ = P.pencil(sn, 6); sh, _ = P.amplitudes(sn, p)
        n, a = P.describe(p, f); out.append(sh[(np.sign(n) != np.sign(a)) & (abs(a) > 0.05)].sum())
    print(f"{f:2d} | {out[0]*100:5.1f}% | {out[1]*100:5.1f}% | {out[2]*100:5.1f}%")
