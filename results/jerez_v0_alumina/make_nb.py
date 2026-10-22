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
 ("            sk = _areal(reg.intersection(skin_zone))\n            polys[name.replace(\"bulk\", \"skin\")] = sk\n",
  "            sk = _areal(reg.intersection(skin_zone))\n"
  "            # 1310 nm needs a 6 nm skin, but the slab runs under 30 um of gold per side: keep\n"
  "            # h_skin within SKIN_NEAR of the gap edge and 2 x h_skin beyond (memory)\n"
  "            _nr = box(-GAP / 2.0 - SKIN_NEAR, -BOX_H, GAP / 2.0 + SKIN_NEAR, 1e3)\n"
  "            polys[name.replace(\"bulk\", \"skin\")] = _areal(sk.intersection(_nr))\n"
  "            _sf = _areal(sk.difference(_nr))\n"
  "            if not _sf.is_empty:\n"
  "                polys[name.replace(\"bulk\", \"skinfar\")] = _sf\n"),
 ('    "elL_skin":    (h_skin, 0.20),\n', '    "elL_skin":    (h_skin, 0.20),\n    "elR_skinfar": (2.0 * h_skin, 0.20),\n    "elL_skinfar": (2.0 * h_skin, 0.20),\n'),
 ("MESH_SCALE = 1.0    #", "SKIN_NEAR = 6.0     # um from the gap edge with the full-resolution gold skin\nMESH_SCALE = 1.0    #"),
]
for a, b in rep:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
nb = copy.deepcopy(nb)
L = s.rstrip("\n").split("\n"); nb["cells"][0]["source"] = [l + "\n" for l in L[:-1]] + [L[-1]]
for c in nb["cells"]: c["outputs"] = []; c["execution_count"] = None
json.dump(nb, open(sys.argv[1], "w"), indent=1, ensure_ascii=False); print("wrote", sys.argv[1])
