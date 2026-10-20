"""Istanbul with a 60 deg slab-end etch (same angle as the rib). SLAB_W is the slab TOP width."""
import json, copy, sys
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Istanbul.ipynb"))
c0 = "".join(nb["cells"][0]["source"])
rep = [
 ("ISTANBUL (C-band tapeout), ETCHED LN SLAB", "ISTANBUL (C-band tapeout), ETCHED LN SLAB WITH 60 deg SLAB-END SIDEWALLS"),
 ("#   the BOX and its top drops by SLAB_H (275 nm).  Gap 4.45 um, slab 10.15 um (gap + 5.7).\n",
  "#   the BOX and its top drops by SLAB_H (275 nm).  Gap 4.45 um, slab 10.15 um (gap + 5.7).\n"
  "#   SLANTED SLAB END: the slab etch leaves ALPHA_SLAB (60 deg) sidewalls, like the rib.\n"
  "#   SLAB_W is the slab TOP width (rib convention); the bottom is wider by 2 SLAB_H / tan(ALPHA_SLAB).\n"
  "#   The conformal gold fills the wedge between the sidewall and the BOX.\n"),
 ("SLAB_W = 10.15      #", "ALPHA_SLAB = 60.0   # slab-end sidewall angle (deg); 90 = vertical (previous model)\nSLAB_W = 10.15      #"),
 ("    xs = min(SLAB_W / 2.0, x_dev_max)               # slab edge\n",
  "    xs = min(SLAB_W / 2.0, x_dev_max)               # slab edge at the TOP of the slab\n"
  "    xsb = xs + SLAB_H / np.tan(np.deg2rad(ALPHA_SLAB))   # slab edge at the BOX (bottom)\n"),
 ("    x_fine = max(X_FINE_MIN, min(xs, x_out) + 1.0)", "    x_fine = max(X_FINE_MIN, min(xsb, x_out) + 1.0)"),
 ("        for _a in (xg, x_out):\n            if abs(xs - _a) > 1e-9:\n                r_c = min(r_c, abs(xs - _a) / 2.5)\n        _d = abs(xs - (xg + 1.0))                   # fine-BOX block edge: a patch edge landing\n        if 1e-9 < _d < r_c + 1e-9:                  # exactly on it makes a zero-length gmsh line\n            r_c = 0.8 * _d\n",
  "        for _x in (xs, xsb):\n            for _a in (xg, x_out):\n                if abs(_x - _a) > 1e-9:\n                    r_c = min(r_c, abs(_x - _a) / 2.5)\n            _d = abs(_x - (xg + 1.0))               # fine-BOX block edge: a patch edge landing\n            if 1e-9 < _d < r_c + 1e-9:              # exactly on it makes a zero-length gmsh line\n                r_c = 0.8 * _d\n"),
 ("    slab = box(-xs, 0.0, xs, y_slab_top)", "    slab = Polygon([(-xsb, 0.0), (xsb, 0.0), (xs, y_slab_top), (-xs, y_slab_top)])   # 60 deg ends"),
 ("    el_r = unary_union([box(xg, y_slab_top, xs, y_el_top), box(xs, 0.0, x_out, MTX)])",
  "    el_r = unary_union([box(xg, 0.0, xsb, y_el_top), box(xsb, 0.0, x_out, MTX)]).difference(slab)"),
 ("        pts += [(xs, y_slab_top), (xs, 0.0)]         # slab end wrapped by gold",
  "        pts += [(xs, y_slab_top), (xsb, 0.0)]        # slanted slab end wrapped by gold"),
 ("    x_e = max(xs, xg)", "    x_e = max(xsb, xg)"),
 ("Istanbul electrodes, cross-section as simulated", "Istanbul, 60 deg slab etch, cross-section as simulated"),
 ("Istanbul electrodes, etched slab |", "Istanbul, 60 deg slab etch |"),
]
for a, b in rep:
    assert c0.count(a) == 1, a
    c0 = c0.replace(a, b)
nb = copy.deepcopy(nb)
lines = c0.rstrip("\n").split("\n"); nb["cells"][0]["source"] = [l + "\n" for l in lines[:-1]] + [lines[-1]]
json.dump(nb, open(sys.argv[1], "w"), indent=1, ensure_ascii=False); print("wrote", sys.argv[1])
