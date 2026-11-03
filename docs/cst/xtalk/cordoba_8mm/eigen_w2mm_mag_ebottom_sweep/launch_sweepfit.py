"""Launch-born field: six modes + one forward wave (born at z = 0) with free n (0-4) and large loss
(0-12 dB/mm), pattern CPW or strips-vs-bottom; best B' CPW residual, hold-out and EO weight of the extra
wave on B (|H_extra| / |H_data| on the fitted samples)."""
import numpy as np, copy, sweepfit as S
exec(open("dn_sweepfit.py").read().split("for f in S.FTD")[0])
pats = {"CPW": S.pattern_raw("p20_even/eig_even_mode3_e.txt"), "sb": S.pattern_raw("p20_even/eig_even_mode1_e.txt"),
        "AvsB": S.pattern_raw("p20_odd/eig_odd_mode1_e.txt")}
def ho_extra(f, td, kw):
    tr = copy.copy(td); m = td.zz < 4e-3
    tr.zz, tr.A, tr.Bp, tr.idx = td.zz[m], td.A[:, m], td.Bp[:, m], td.idx[m]
    x = np.array(list(S.fit(f, tr, **kw)["x"].values()))
    te = copy.copy(td); te.zz, te.A, te.Bp, te.idx = td.zz[~m], td.A[:, ~m], td.Bp[:, ~m], td.idx[~m]
    ce, _, _ = S.basis(("e_cpw","e_slot","e_sb"), f, te, extra=kw.get("extra_e")); co, _, _ = S.basis(("o_cpw","o_slot","o_AvsB"), f, te, extra=kw.get("extra_o"))
    mB = np.array([S.cpw(0.5*c) for c in ce] + [S.cpw(-0.5*c) for c in co]).T @ x; d = S.cpw(te.Bp)
    return np.linalg.norm(d - mB) / np.linalg.norm(d)
for f in S.FTD:
    td = S.TDData(f); base = S.fit(f, td)["res"]["B CPW"]; best = (9,)
    for pn, u in pats.items():
        for n in np.arange(0.0, 4.01, 0.1):
            for adb in (0.5, 1, 2, 3, 4, 6, 8, 12):
                for side in ("e", "o"):
                    kw = {("extra_" + side): {"x": (u, n, adb / 8.686e-3)}}
                    o = S.fit(f, td, **kw)
                    if o["res"]["B CPW"] < best[0]: best = (o["res"]["B CPW"], pn, n, adb, side, kw, o)
    r, pn, n, adb, side, kw, o = best
    e = o["eo"]; hx = sum(v for k, v in e["HB_comp"].items() if k.startswith("x"))
    print(f"{f:2d} GHz six {base:.3f} -> {r:.3f}  extra: {pn} pattern ({side}), n {n:.1f}, {adb} dB/mm;"
          f" A CPW {o['res']['A CPW']:.4f}; hold-out {ho_extra(f, td, kw):.2f}; |H_extra|/|H_data| B {abs(hx)/abs(e['Hd_B']):.2f}", flush=True)
