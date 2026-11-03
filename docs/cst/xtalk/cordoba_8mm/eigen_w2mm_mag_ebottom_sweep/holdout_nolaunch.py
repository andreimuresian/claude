"""Hold-out away from the launch: fit on 1.5-4.5 mm, predict B' CPW on 4.5-7.2 mm (and the reverse)."""
import numpy as np, copy, sweepfit as S
def sub(td, m):
    t = copy.copy(td); t.zz, t.A, t.Bp, t.idx = td.zz[m], td.A[:, m], td.Bp[:, m], td.idx[m]; return t
def pred(f, tr, te):
    x = np.array(list(S.fit(f, tr)["x"].values()))
    ce, _, _ = S.basis(("e_cpw","e_slot","e_sb"), f, te); co, _, _ = S.basis(("o_cpw","o_slot","o_AvsB"), f, te)
    mB = np.array([S.cpw(0.5*c) for c in ce] + [S.cpw(-0.5*c) for c in co]).T @ x; d = S.cpw(te.Bp)
    return np.linalg.norm(d - mB) / np.linalg.norm(d)
print(" f | fit 1.5-4.5 -> 4.5-7.2 | fit 4.5-7.2 -> 1.5-4.5 | fit on 1.5-7.2 itself")
for f in S.FTD:
    td = S.TDData(f); z = td.zz
    a = (z >= 1.5e-3) & (z < 4.5e-3); b = (z >= 4.5e-3) & (z < 7.2e-3)
    print(f"{f:2d} | {pred(f, sub(td, a), sub(td, b)):.3f} | {pred(f, sub(td, b), sub(td, a)):.3f} | {S.fit(f, sub(td, a | b))['res']['B CPW']:.3f}")
