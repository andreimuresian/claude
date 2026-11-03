"""Index shifts of strips vs bottom (dn_sb) and A vs B (dn_AB) scanned jointly (TD lateral boundary differs
from the cell's magnetic wall). Reports the best B' CPW residual and its hold-out (1st half -> 2nd half)."""
import numpy as np, copy, sweepfit as S
exec(open("dn_sweepfit.py").read().split("for f in S.FTD")[0])
def shift2(dsb, dab):
    for k, D in S.DISP.items():
        D.cn = orig[k].copy()
    S.DISP["e_sb"].cn[0] += dsb; S.DISP["o_AvsB"].cn[0] += dab
grid = np.arange(-0.20, 0.201, 0.025)
for f in S.FTD:
    td = S.TDData(f); best = (9,)
    for dsb in grid:
        for dab in grid:
            shift2(dsb, dab); r = S.fit(f, td)["res"]
            if r["B CPW"] < best[0]: best = (r["B CPW"], dsb, dab, r["A CPW"], r["B slot"])
    shift2(best[1], best[2]); ho = holdout(f, td); shift2(0, 0)
    print(f"{f:2d} GHz  best B' CPW {best[0]:.3f} at dn_sb {best[1]:+.3f} dn_AB {best[2]:+.3f}  (A CPW {best[3]:.4f},"
          f" B' slot {best[4]:.3f})  hold-out {ho:.2f}", flush=True)
