"""Render the meshed unit cell with every dimension annotated, so the geometry
can be validated by eye against the CST model instead of taken on trust."""
import sys
sys.path.insert(0, "/home/user/claude/notebooks/mom")
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
import mesh_generator as mg
from common_mesh import build_common_cells

D = "/root/.claude/uploads/f069cebc-0d61-5069-a4b8-cc5b76a72567/51442c2b-FULL_DATASET.xlsx"
P = mg.PITCH


def draw(rows=(118, 121, 38), h=9e-6, out="geometry_check.png"):
    d = pd.read_excel(D)
    fig, ax = plt.subplots(1, len(rows), figsize=(5.2*len(rows), 7.0))
    for a, i in zip(np.atleast_1d(ax), rows):
        o = d.loc[i]; g = mg.geom_from_row(o)
        cu, ce, info = build_common_cells(g, h)
        n = ce["nodes"]*1e6; t = ce["tris"]
        a.triplot(Triangulation(n[:, 0], n[:, 1], t), lw=0.35, color="0.55")
        x_si, x_gi, x_go = o.WS/2, o.WS/2+o.GAP, o.WS/2+o.GAP+70.0
        for xv, lab, c in ((x_si, "WS/2", "tab:blue"), (x_gi, "WS/2+GAP", "tab:red"),
                           (x_go, "+WG", "tab:green")):
            for s in (-1, 1):
                a.axvline(s*xv, color=c, lw=0.9, ls="--", alpha=0.8)
        zc = 0.5*P*1e6
        b = x_gi + o.W1; cc = x_gi + o.W1 + o.W2
        a.plot([x_gi, b], [zc, zc], "k-", lw=2)
        a.annotate("W1=%.2f" % o.W1, ((x_gi+b)/2, zc+3), ha="center", fontsize=8)
        a.plot([b, cc], [zc, zc], "m-", lw=2)
        a.annotate("W2=%.2f" % o.W2, ((b+cc)/2, zc-7), ha="center", fontsize=8, color="m")
        a.plot([x_gi+1, x_gi+1], [zc-o.L1/2, zc+o.L1/2], "k-", lw=2)
        a.annotate("L1=%.2f" % o.L1, (x_gi+3, zc+o.L1/2+3), fontsize=8)
        a.plot([cc-1, cc-1], [zc-o.L2/2, zc+o.L2/2], "m-", lw=2)
        a.annotate("L2=%.2f" % o.L2, (cc-1, zc-o.L2/2-8), fontsize=8, color="m", ha="right")
        a.set_title("row %d   WS=%.2f GAP=%.2f MTX=%.2f\nW1=%.2f W2=%.2f L1=%.2f L2=%.2f\n"
                    "Nt %d etched / %d unetched  (all um)"
                    % (i, o.WS, o.GAP, o.MTX, o.W1, o.W2, o.L1, o.L2,
                       info["Nt_etched"], info["Nt_unetched"]), fontsize=9)
        a.set_xlabel("x transverse [um]"); a.set_ylabel("v propagation [um]")
        a.set_aspect("equal"); a.set_ylim(0, P*1e6)
    fig.suptitle("Meshed ETCHED unit cell, one period. Dashed: signal edge (blue), "
                 "ground inner edge (red), ground outer edge (green).\n"
                 "Note MTX is NOT drawn: the mesh is a zero-thickness sheet, which is "
                 "the known modelling gap.", fontsize=10)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    print("wrote", out)


if __name__ == "__main__":
    draw()
