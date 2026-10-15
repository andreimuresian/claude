"""Istanbul + conformal 200 nm SiO2 buffer, from VPI_interface_optimized_Istanbul.ipynb."""
import json, copy, sys
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Istanbul.ipynb"))
c0 = "".join(nb["cells"][0]["source"])
a = c0.index("def build_polygons"); b = c0.index("# ============================================================\n# 3. MESH")
c0 = c0[:a] + open("/home/user/claude/results/istanbul_buffer/build_polygons_buf.py").read() + c0[b:]
rep = [
 ("ISTANBUL (C-band tapeout), ETCHED LN SLAB", "ISTANBUL + 200 nm SiO2 BUFFER, ETCHED LN SLAB"),
 ("#   the BOX and its top drops by SLAB_H (275 nm).  Gap 4.45 um, slab 10.15 um (gap + 5.7).\n",
  "#   the BOX and its top drops by SLAB_H (275 nm).  Gap 4.45 um, slab 10.15 um (gap + 5.7).\n"
  "#   BUFFERED: a conformal SiO2 buffer (BUFFER_H) is deposited after the slab etch on the slab top,\n"
  "#   the slab side walls and the BOX; the gold sits on it everywhere (raised by BUFFER_H).\n"
  "#   GAP is the gold-to-gold gap on the buffer; the cap height is measured from the buffer top.\n"),
 ("CAP_H = 1.40\n", "CAP_H = 1.40\nBUFFER_H = 0.200    # conformal SiO2 buffer under all the gold\n"),
 ('("box", "SiO2"),', '("box", "SiO2"), ("buf", "SiO2"),'),
 ("h_skin = 0.012 ", "h_skin = 0.018 "),
 ('    "slab_mid":    (0.110, 0.40),\n    "slab_far":    (0.150, 0.50),\n',
  '    "slab_mid":    (0.110, 0.40),\n    "slab_far":    (0.150, 0.50),\n'
  '    "buf_fine":    (min(BUFFER_H / 4, 0.050), 0.20),\n    "buf_mid":     (0.100, 0.30),\n    "buf_far":     (0.200, 0.50),\n'),
 ("Istanbul electrodes, cross-section as simulated", "Istanbul + SiO2 buffer, cross-section as simulated"),
 ("Istanbul electrodes, etched slab |", "Istanbul + buffer, etched slab |"),
 ("_dim(ax_a, -_xg, _xg, SLAB_H + MTX - 0.35,", "_dim(ax_a, -_xg, _xg, SLAB_H + BUFFER_H + MTX - 0.35,"),
]
for x, y in rep:
    assert x in c0, x
    c0 = c0.replace(x, y)
nb = copy.deepcopy(nb)
lines = c0.rstrip("\n").split("\n"); nb["cells"][0]["source"] = [l + "\n" for l in lines[:-1]] + [lines[-1]]
json.dump(nb, open(sys.argv[1], "w"), indent=1, ensure_ascii=False); print("wrote", sys.argv[1])
