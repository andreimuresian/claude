"""Common index shift dn of a family pair (TD mesh vs eigen mesh): scan dn for CPW (and then for all
families together), report A CPW, B' CPW residuals and the hold-out (1st half -> 2nd half) B' CPW residual."""
import numpy as np, copy, sweepfit as S
orig = {k: (D.cn.copy()) for k, D in S.DISP.items()}
def shift(fams, dn):
    for k, D in S.DISP.items():
        D.cn = orig[k].copy()
        if k in fams: D.cn[0] += dn
def holdout(f, td):
    tr = copy.copy(td); m = td.zz < 4e-3
    tr.zz, tr.A, tr.Bp, tr.idx = td.zz[m], td.A[:, m], td.Bp[:, m], td.idx[m]
    x = np.array(list(S.fit(f, tr)["x"].values()))
    te = copy.copy(td); te.zz, te.A, te.Bp, te.idx = td.zz[~m], td.A[:, ~m], td.Bp[:, ~m], td.idx[~m]
    ce, _, _ = S.basis(("e_cpw","e_slot","e_sb"), f, te); co, _, _ = S.basis(("o_cpw","o_slot","o_AvsB"), f, te)
    mB = np.array([S.cpw(0.5*c) for c in ce] + [S.cpw(-0.5*c) for c in co]).T @ x; d = S.cpw(te.Bp)
    return np.linalg.norm(d - mB) / np.linalg.norm(d)
for f in S.FTD:
    td = S.TDData(f); rows = []
    for dn in np.arange(-0.004, 0.0201, 0.002):
        shift(("e_cpw", "o_cpw"), dn); o = S.fit(f, td)
        rows.append((o["res"]["A CPW"], o["res"]["B CPW"], dn))
    a = min(rows); b = min(rows, key=lambda t: t[1])
    shift(("e_cpw", "o_cpw"), a[2]); ho = holdout(f, td); oa = S.fit(f, td)
    shift((), 0); o0 = S.fit(f, td); ho0 = holdout(f, td)
    print(f"{f:2d} GHz  dn=0: A {o0['res']['A CPW']:.4f} B {o0['res']['B CPW']:.3f} hold {ho0:.2f} | best on A: dn {a[2]:+.3f}"
          f" A {a[0]:.4f} B {oa['res']['B CPW']:.3f} hold {ho:.2f} | best on B: dn {b[2]:+.3f} B {b[1]:.3f}", flush=True)
shift((), 0)
