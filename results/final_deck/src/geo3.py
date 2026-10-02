import sys; sys.path.insert(0, "/home/user/claude/results/etched_slab/deck_src")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from geoms4 import polys, draw, C
for nm, reps in (("lift", {"SLAB_W = 3.2 ": "SLAB_W = 20.0 "}),
                 ("goldout", {"SLAB_W = 3.2 ": "SLAB_W = 20.0 ", "GOLD_OUT = False": "GOLD_OUT = True"})):
    f, a = plt.subplots(figsize=(6.2, 1.9)); P, m = polys(C + "cell0_etched.py", reps); draw(a, P, m, "", xl=13.5)
    a.set_ylim(-0.6, 6.0)
    f.savefig(f"fig/geo3_{nm}.png", dpi=170, bbox_inches="tight", pad_inches=0.02); plt.close(f)
print("ok")
