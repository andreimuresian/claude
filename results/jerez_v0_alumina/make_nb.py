"""Jerez V0 (O band, non-lifted Cordoba-type electrodes, unetched slab) + conformal ALD Al2O3,
from the Cordoba alumina notebook.  Usage: make_nb.py out.ipynb"""
import json, copy, sys
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Cordoba_alumina.ipynb"))
s = "".join(nb["cells"][0]["source"])
rep = [
 ("CORDOBA ELECTRODES + CONFORMAL ALD Al2O3\n#\n", "JEREZ V0 (O band) + CONFORMAL ALD Al2O3\n#\n"
  "#   Jerez V0: Cordoba-type flat 2 um electrodes on an unetched slab, 400 nm LN film, 170 nm rib etch,\n"
  "#   rib top 1.0 um, gap 4.15 um, 1310 nm.  Same as Jerez lifted without the electrode lift.\n#\n"),
 ("wl = 1.575", "wl = 1.310"),
 ("n_guess = 1.90       # wider rib (1.4 um): TE mode near 1.90", "n_guess = 1.87       # Jerez V0 at 1310 nm: TE mode near 1.87"),
 ("TECN = 0.550", "TECN = 0.400"), ("WG_H = 0.275", "WG_H = 0.170"),
 ("WG_TOP = 1.4\n", "WG_TOP = 1.0\n"), ("GAP = 4.2\n", "GAP = 4.15\n"),
 ("h_skin = 0.012", "h_skin = 0.006"),
]
for a, b in rep:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
nb = copy.deepcopy(nb)
L = s.rstrip("\n").split("\n"); nb["cells"][0]["source"] = [l + "\n" for l in L[:-1]] + [L[-1]]
for c in nb["cells"]: c["outputs"] = []; c["execution_count"] = None
json.dump(nb, open(sys.argv[1], "w"), indent=1, ensure_ascii=False); print("wrote", sys.argv[1])
