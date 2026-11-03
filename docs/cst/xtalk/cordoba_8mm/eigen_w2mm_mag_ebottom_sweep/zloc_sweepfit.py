"""Where B' CPW misfit sits along z (global six-mode fit, 1 mm bins), and local fits in 2 mm windows
(same six modes, amplitudes free per window): small local residuals with a large global one mean the
wave amplitudes drift along the line (B keeps receiving or losing field), not a wrong pattern."""
import numpy as np, copy, sweepfit as S
edges = np.arange(0.3, 7.71, 1.0) * 1e-3
print(" f  | global B' CPW resid in 1 mm bins (0.3..7.7 mm)                 | |B'CPW| rms per bin rel. to mean     | local 2 mm windows resid")
for f in S.FTD:
    td = S.TDData(f); o = S.fit(f, td); d = o["data"]["B CPW"]; m = o["model"]["B CPW"]
    g = []; a = []
    for z0, z1 in zip(edges[:-1], edges[1:]):
        s = (td.zz >= z0) & (td.zz < z1); g.append(np.linalg.norm((d-m)[s])/np.linalg.norm(d[s])); a.append(np.sqrt(np.mean(abs(d[s])**2)))
    a = np.array(a)/np.sqrt(np.mean(abs(d)**2))
    loc = []
    for z0 in (0.31e-3, 2.31e-3, 4.31e-3, 5.69e-3):
        w = copy.copy(td); s = (td.zz >= z0) & (td.zz < z0 + 2e-3)
        w.zz, w.A, w.Bp, w.idx = td.zz[s], td.A[:, s], td.Bp[:, s], td.idx[s]
        loc.append(S.fit(f, w)["res"]["B CPW"])
    print(f"{f:3d} | " + " ".join(f"{v:.2f}" for v in g) + " | " + " ".join(f"{v:.2f}" for v in a) + " | " + " ".join(f"{v:.3f}" for v in loc))
