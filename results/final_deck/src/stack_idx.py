import numpy as np, strip1d as S
S.ns = 1.443723; S.eau = -120.37 - 11.93j
ne, no = S.ne, S.no
def bound(B, ein, sig=2.0):
    nk, V, y = S.modes(B, ein, sigma_n=sig)
    g = [x for x in nk if S.ns < x.real < 3.5]
    return g[0] if g else np.nan
for lab, B in (("Au / LN / BOX", 0.0), ("SiO2 / LN / BOX (gold far)", 2.5)):
    v = [bound(B, e) for e in (ne**2, no**2)]
    print(lab, [f"{x.real:.4f}" for x in v], "mean", f"{np.mean([x.real for x in v]):.4f}")
em, ed = S.eau, S.ns**2
print("Au / SiO2 SPP", np.sqrt(em*ed/(em+ed)))
