"""Group-index notebooks (Cordoba 1575 nm, Jerez V0 1310 nm) with conformal ALD Al2O3 and an ALD Sellmeier.
usage: make_nb.py cordoba|jerez out.ipynb"""
import json, copy, sys
design, out = sys.argv[1], sys.argv[2]
BUF = design == "cordoba_buf"
if BUF: design = "cordoba"
src = {"cordoba": "/home/user/claude/VPI_interface_optimized_Cordoba_alumina.ipynb",
       "jerez": "/home/user/claude/VPI_interface_optimized_JerezV0_alumina.ipynb"}[design]
nb = json.load(open(src)); s = "".join(nb["cells"][0]["source"])
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
rep("N_ALD = 1.74        # ALD Al2O3 optical index at wl (amorphous film; user value)\n",
    "ALD_MODEL = \"sellmeier\"   # 'sellmeier': ALD Sellmeier as fitted | 'scaled': same dispersion, scaled to N_ALD_REF at wl\n"
    "N_ALD_REF = 1.74    # index at wl used by the 'scaled' model (earlier ALD runs)\n")
rep("eps_au = eps_Au_JC(wl)\n",
    "eps_au = eps_Au_JC(wl)\n\n\n"
    "def n_ALD_sellmeier(lam):\n"
    "    \"\"\"ALD Al2O3: one-term Sellmeier fitted (0.35-1.69 um, max error 4e-4) to the ellipsometry data of\n"
    "    20 nm ALD films grown at 120 C, Zhukovsky et al., PRL 115, 177402 (2015) (refractiveindex.info).\"\"\"\n"
    "    l2 = lam ** 2\n"
    "    return np.sqrt(1 + 1.5977254 * l2 / (l2 - 0.01075085))\n\n\n"
    "def n_ALD(lam):\n"
    "    if ALD_MODEL == \"scaled\":\n"
    "        return n_ALD_sellmeier(lam) * N_ALD_REF / n_ALD_sellmeier(wl)\n"
    "    return n_ALD_sellmeier(lam)\n\n\n"
    "N_ALD = n_ALD(wl)\n")
if design == "cordoba":
    rep("TECN = 0.550\nWG_H = 0.275\nSLAB_H = TECN - WG_H                # 0.275 um LN slab\n",
        "TECN = 0.540\nWG_H = 0.270\nSLAB_H = TECN - WG_H                # 0.270 um LN slab\n")
    rep("GAP = 4.2\n", "GAP = 4.15\n")
    # graded gold skin, as in Jerez V0: full resolution within SKIN_NEAR of the gap edge, 2x beyond
    rep("            sk = _areal(reg.intersection(skin_zone))\n            polys[name.replace(\"bulk\", \"skin\")] = sk\n",
        "            sk = _areal(reg.intersection(skin_zone))\n"
        "            _nr = box(-GAP / 2.0 - SKIN_NEAR, -BOX_H, GAP / 2.0 + SKIN_NEAR, 1e3)\n"
        "            polys[name.replace(\"bulk\", \"skin\")] = _areal(sk.intersection(_nr))\n"
        "            _sf = _areal(sk.difference(_nr))\n"
        "            if not _sf.is_empty:\n"
        "                polys[name.replace(\"bulk\", \"skinfar\")] = _sf\n")
    rep('    "elL_skin":    (h_skin, 0.20),\n', '    "elL_skin":    (h_skin, 0.20),\n    "elR_skinfar": (2.0 * h_skin, 0.20),\n    "elL_skinfar": (2.0 * h_skin, 0.20),\n')
    rep("MESH_SCALE = 1.0    #", "SKIN_NEAR = 6.0     # um from the gap edge with the full-resolution gold skin\nMESH_SCALE = 1.0    #")
if BUF:
    rep("CAP_H = 1.40\n", "CAP_H = 1.40\nBUFFER_H = 0.200    # SiO2 buffer on the whole slab: under the gold and across the gap (fused with the cap)\n")
    rep("    y_el_top = y_slab_top + MTX                     # 2.275\n    y_cap_top = y_slab_top + CAP_H                  # 1.675\n",
        "    y_buf = round(y_slab_top + BUFFER_H, 9)         # buffer top = bottom of the gold (rounded: exact vertices)\n"
        "    y_el_top = y_buf + MTX\n    y_cap_top = y_buf + CAP_H                       # cap height from the buffer top\n")
    rep("    y_fine_top = y_slab_top + 0.6 ", "    y_fine_top = y_buf + 0.6 ")
    rep("    el_r = box(xg, 0.0, x_out, y_el_top).difference(slab)\n",
        "    el_r = box(xg, y_buf, x_out, y_el_top).difference(slab)\n"
        "    buf = _areal(box(-x_dev_max, y_slab_top, x_dev_max, y_buf).difference(core_poly)\n"
        "                 .difference(box(-CAP_W / 2.0, 0.0, CAP_W / 2.0, y_cap_top)))   # under the cap: part of the cap\n")
    rep("    solids = unary_union([core_poly, slab, cap_poly, cap_up, el_r, mirror(el_r)])",
        "    solids = unary_union([core_poly, slab, cap_poly, cap_up, el_r, mirror(el_r), buf])")
    rep('    base["alu_far"] = alu_far\n',
        '    base["alu_far"] = alu_far\n'
        '    base["buf_near"] = _areal(buf.intersection(box(-x_fine, 0.0, x_fine, y_buf)))\n'
        '    base["buf_far"] = _areal(buf.difference(box(-x_fine, 0.0, x_fine, y_buf)))\n')
    rep("        pts.append((xg, y_slab_top))                 # inner corner: gold / LN / air",
        "        pts.append((xg, y_buf))                      # inner corner: gold / buffer / air")
    rep("        pts.append((x_out, y_slab_top))              # outer corner: gold / LN / air (no etch)",
        "        pts.append((x_out, y_buf))                   # outer corner")
    rep("        slab.buffer(SKIN_T, join_style=2),\n", "        slab.buffer(SKIN_T, join_style=2),\n        box(xg, y_buf, x_out, y_buf + SKIN_T),     # gold bottom on the buffer\n")
    rep('("alu", "Al2O3"),', '("alu", "Al2O3"), ("buf", "SiO2"),')
    rep('    "slab_fine":   (0.025, 0.30),\n', '    "slab_fine":   (0.025, 0.30),\n    "buf_near":    (min(BUFFER_H / 4, 0.05), 0.20),\n    "buf_far":     (0.100, 0.30),\n')
s = s.replace("# %% [0] Geometry, Mesh & Material Configuration  --", "# %% [0] Geometry, Mesh & Material Configuration  --  GROUP INDEX STUDY --", 1)
nb = copy.deepcopy(nb)
def setsrc(c, t):
    L = t.rstrip("\n").split("\n"); c["source"] = [l + "\n" for l in L[:-1]] + [L[-1]]
setsrc(nb["cells"][0], s)
cell = copy.deepcopy(nb["cells"][4]); setsrc(cell, open("/home/user/claude/results/ald_group_index/cell_ng.py").read())
nb["cells"].append(cell)
for c in nb["cells"]: c["outputs"] = []; c["execution_count"] = None
json.dump(nb, open(out, "w"), indent=1, ensure_ascii=False); print("wrote", out)
