"""2D: modes of the signal strip alone (no grounds), and of the normal CPW, PEC vs PMC outer walls."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "../mom")
import stack_params as sp, fw2d
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, t_LN=sp.TFLN - d.ETCH_DEPTH*1e-6)
x_si = g["WS"]/2
for lab, mx in (("signal only", [(0, x_si)]), ("CPW", None)):
    for wall in ("pec", "pmc"):
        m = fw2d.Mode2D(g, 20e9, metal_x=mx, wall=wall)
        k0 = m.w/fw2d.C0
        from scipy.sparse.linalg import eigs
        vals, vecs = eigs(m.M, k=6, sigma=(2.0*k0)**2, which="LM")
        b = np.sqrt(vals.astype(complex))
        out = []
        for bb, v in zip(b, vecs.T):
            r = m.line_params(bb, v)
            out.append(f"n {bb.real/k0:.3f} a {-bb.imag*8.686/100:.3f} dB/cm |V|/|v| {abs(r['V'])/np.linalg.norm(v):.1e}")
        print(lab, wall, "|", " ; ".join(out), flush=True)
