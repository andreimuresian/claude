"""
Reference Z0, n_m, alpha over the inverse-design space of the bend:
S 30-40 um, W 4-5 um, Wg 50-60 um, t = 2 um, bend stack (3.6 um SiO2 /
0.275 um LN / 4.7 um SiO2 / Si). 3-level full factorial (27 geometries) plus
6 interior points, each at 9 frequencies from 1 to 200 GHz.

Reference = C from the FEM quasi-static solve (bend_fem.py, the user's notebook
formulation) + R, L from the current inside the gold (eddy_tensor.py).
Usage: python doe_design.py [i0 i1]  (slice of the point list, for parallel runs)
"""
import itertools
import json
import sys

import numpy as np

import eddy_tensor as E
from bend_fem import run

F_GHZ = [1, 5, 10, 20, 40, 60, 100, 150, 200]
PTS = [(S, W, Wg) for S, W, Wg in itertools.product((30.0, 35.0, 40.0), (4.0, 4.5, 5.0), (50.0, 55.0, 60.0))]
PTS += [(32.5, 4.25, 52.5), (37.5, 4.75, 57.5), (32.5, 4.75, 57.5), (37.5, 4.25, 52.5), (33.0, 4.6, 51.0),
        (38.0, 4.3, 58.0)]

if __name__ == "__main__":
    i0, i1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, len(PTS))
    for S, W, Wg in PTS[i0:i1]:
        qs = run(60e9, geom=dict(sig_w=S, gap=W, gnd_w=Wg, au_h=2.0, buf_h=3.6),
                 mesh_opts=dict(SKIN_REACH=min(S / 2, 17.5)), qs_only=True)
        res, info = E.solve_Z([f * 1e9 for f in F_GHZ], hfine=0.04, sig_w=S, gap=W, gnd_w=Wg, t=2.0)
        print(json.dumps(dict(S=S, W=W, Wg=Wg, t=2.0, h=3.6, C_eps=float(qs["C_eps"]), C_air=float(qs["C_air"]),
                              f=F_GHZ, R=[x["R"] for x in res], L=[x["L"] for x in res],
                              t_qs=float(qs["t_s"]), t_eddy=info["t_s"])), flush=True)
