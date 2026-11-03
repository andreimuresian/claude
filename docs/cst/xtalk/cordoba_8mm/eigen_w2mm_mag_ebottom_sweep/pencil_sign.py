"""Sign test of the pencil waves: a passive guided wave decays in its direction of travel, so sign(n) = sign(alpha)
(alpha > 0: decays toward +z). Energy share of waves with sign(n) != sign(alpha) ('inconsistent'), per data set,
M = 6, window 0.31-7.69 mm, with the level of each data set relative to A's CPW pattern (rms)."""
import numpy as np, pencil_gap as P, sweepfit as S
rms = lambda v: np.sqrt(np.mean(abs(v) ** 2))
print(" f  | level dB re A CPW: A slot, B CPW, B slot | inconsistent share (M 6): A CPW, A slot, B CPW, B slot, B gap+, B gap- | pencil resid B CPW")
for f in S.FTD:
    td = S.TDData(f); z = td.z_full
    sets = {"A CPW": S.cpw(td.A_full), "A slot": S.slot(td.A_full), "B CPW": S.cpw(td.Bp_full),
            "B slot": S.slot(td.Bp_full), "B+": td.Bp_full[0], "B-": td.Bp_full[1]}
    lev = {k: 20 * np.log10(rms(v) / rms(sets["A CPW"])) for k, v in sets.items()}
    inc = {}; rr = {}
    for k, v in sets.items():
        sn = P.snapshots(v, z, 0.31e-3, 7.69e-3); p, _, _ = P.pencil(sn, 6); sh, res = P.amplitudes(sn, p)
        n, a = P.describe(p, f); bad = (np.sign(n) != np.sign(a)) & (abs(a) > 0.05)
        inc[k] = sh[bad].sum(); rr[k] = res
    print(f"{f:3d} | {lev['A slot']:6.1f} {lev['B CPW']:6.1f} {lev['B slot']:6.1f} | " +
          " ".join(f"{inc[k]*100:5.1f}%" for k in sets) + f" | {rr['B CPW']:.3f}")
