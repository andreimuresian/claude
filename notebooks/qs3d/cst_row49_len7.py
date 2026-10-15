"""Row 49 PEC tee lines, 2/3/5/7 cells at 20 and 60 GHz: per-cell alpha and n from every pair
(line-line and subtraction, as in cst_row49.py).  Run: python cst_row49_len7.py  (-> cst_row49_len7.txt)"""
import os, math, cmath, numpy as np, sys
sys.path.insert(0, "/home/user/claude/notebooks/qs3d")
import cst_row49 as C
D = C.DIR
r = lambda n: C.read(os.path.join(D, n))[0]
S = {20e9: {2: r("400 TEE PEC.s2p")[20e9], 3: r("600 TEE PEC.s2p")[20e9],
            5: r("1000 TEE PEC 20 60GHZ.s2p")[20e9], 7: r("1400 TEE PEC 20 60GHZ.s2p")[20e9]},
     60e9: {2: r("400 TEE PEC.s2p")[60e9], 3: r("600 TEE PEC MESH CORRECTED.s2p")[60e9],
            5: r("1000 TEE PEC 20 60GHZ.s2p")[60e9], 7: r("1400 TEE PEC 20 60GHZ.s2p")[60e9]}}
for f, d in S.items():
    print(f"--- {f/1e9:.0f} GHz")
    for N, s in d.items():
        print(f"  {N} cells: |S11| {abs(s[0]):.4f}  |S21| {abs(s[1]):.5f} ph {math.degrees(cmath.phase(s[1])):8.2f}  lost {100*(1-abs(s[0])**2-abs(s[1])**2):.3f} %  S21-S12 {abs(s[1]-s[2]):.1e}")
    for a, b in ((2,3),(3,5),(5,7),(3,7),(2,7)):
        p = C.pair(d[a], d[b], a, b, f, n_ref=2.6)
        print(f"  {a}->{b}: line-line alpha {p['alpha']:7.3f} dB/cm  n {p['n']:.4f}  subtraction {p['sub']:7.3f}  ends sigma {p['sv']:.4f} lost {p['lostK']:+.3f} %")
