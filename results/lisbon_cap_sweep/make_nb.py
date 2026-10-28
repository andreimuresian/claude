"""Lisbon lifted + 200 nm buffer, cap sweep notebook: the user's notebook with GAP_BOT 3.4 and the
low-cap fix (a cap lower than the 0.6 um fine-mesh band used to be stretched to 0.6 um)."""
import json, copy, sys
nb = json.load(open(sys.argv[1])); s = "".join(nb["cells"][0]["source"])
rep = [("GAP_BOT = 3.6 ", "GAP_BOT = 3.4 "),
       ("    cap_poly = box(-CAP_W / 2.0, y_slab_top, CAP_W / 2.0, y_fine_top).difference(core_poly)\n    cap_up = box(-CAP_W / 2.0, y_fine_top, CAP_W / 2.0, y_cap_top)\n",
        "    y_cap_low = min(y_fine_top, y_cap_top)          # a cap lower than the fine band ends at CAP_H\n"
        "    cap_poly = box(-CAP_W / 2.0, y_slab_top, CAP_W / 2.0, y_cap_low).difference(core_poly)\n"
        "    cap_up = (box(-CAP_W / 2.0, y_fine_top, CAP_W / 2.0, y_cap_top) if y_cap_top > y_fine_top + 1e-9\n"
        "              else Polygon())\n")]
for a, b in rep:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
nb = copy.deepcopy(nb)
L = s.rstrip("\n").split("\n"); nb["cells"][0]["source"] = [l + "\n" for l in L[:-1]] + [L[-1]]
for c in nb["cells"]: c["outputs"] = []; c["execution_count"] = None
json.dump(nb, open(sys.argv[2], "w"), indent=1, ensure_ascii=False); print("wrote", sys.argv[2])
