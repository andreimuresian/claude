"""FW1: no-tee line of row 49, PEC, 20/60/100 GHz vs the CST no-tee lines."""
import sys, time
import pandas as pd
sys.path.insert(0, "../mom")
import stack_params as sp
import fw2d

d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, t_LN=sp.TFLN - d.ETCH_DEPTH*1e-6)
CST = {20e9: (1.969, 0.000, 36.40), 60e9: (1.972, 0.109, 36.33), 100e9: (1.972, 0.144, 36.12)}
args = [a for a in sys.argv[1:] if "=" in a]; FREQS = [float(a)*1e9 for a in sys.argv[1:] if "=" not in a] or [20e9, 60e9, 100e9]
kw = dict(arg.split("=") for arg in args)
kw = {k: float(v) for k, v in kw.items()}
for f in FREQS:
    t = time.time()
    m = fw2d.Mode2D(g, f, **kw)
    b, V = m.solve(2.0, k=3)
    r = m.line_params(b[0], V[:, 0])
    c = CST[f]
    print(f"{f/1e9:4.0f} GHz N={m.N:7d} | n {r['n']:.4f} (CST {c[0]})  alpha {r['alpha']:.4f} (CST {c[1]})"
          f" | Z VI {abs(r['Z_VI']):.2f} PV {r['Z_PV']:.2f} PI {r['Z_PI']:.2f} (CST {c[2]})"
          f" | other n {[round(x.real/(m.w/fw2d.C0), 3) for x in b[1:]]}  {time.time()-t:.0f} s", flush=True)
