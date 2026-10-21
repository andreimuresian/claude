"""Istanbul + 200 nm conformal SiO2 buffer + 60 deg slab ends + 700 nm BOX over-etch,
from the buffered Istanbul notebook.  Usage: make_nb.py out.ipynb"""
import json, copy, sys
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Istanbul_buffer.ipynb"))
c0 = "".join(nb["cells"][0]["source"])
a = c0.index("def build_polygons"); b = c0.index("# ============================================================\n# 3. MESH")
c0 = c0[:a] + open("/home/user/claude/results/istanbul_buffer_oe/bp.py").read() + c0[b:]
rep = [
 ("ISTANBUL + 200 nm SiO2 BUFFER, ETCHED LN SLAB", "ISTANBUL + 200 nm SiO2 BUFFER, 60 deg SLAB ENDS, 700 nm BOX OVER-ETCH"),
 ("#   GAP is the gold-to-gold gap on the buffer; the cap height is measured from the buffer top.\n",
  "#   GAP is the gold-to-gold gap on the buffer; the cap height is measured from the buffer top.\n"
  "#   Slab ends etched at ALPHA_SLAB (60 deg, process); SLAB_W is the slab TOP width.\n"
  "#   OVER-ETCH: the BOX is recessed by OE (vertical walls at the slab foot) wherever the slab\n"
  "#   is removed, BEFORE the buffer: the buffer lines the recess and the gold fills it.\n"),
 ("BUFFER_H = 0.200    # conformal SiO2 buffer under all the gold\n",
  "BUFFER_H = 0.200    # conformal SiO2 buffer under all the gold\nBUFFER_L = 0.200    # SiO2 buffer on the side walls (60 deg slope, pedestal wall), normal thickness\nALPHA_SLAB = 60.0   # slab-end sidewall angle (deg)\nOE = 0.7            # BOX over-etch depth outside the slab footprint (um); 0 = none\n"),
 ("GAP = 4.45\n", "GAP = 3.65          # buffered design point: same Vpi*L as unbuffered Istanbul at 4.45 um\n"),
 ("Istanbul + SiO2 buffer, cross-section as simulated", "Istanbul + buffer + over-etch, cross-section as simulated"),
 ("Istanbul + buffer, etched slab |", "Istanbul + buffer + over-etch |"),
 ("assert abs(_tot - DEV_W * (BOX_H + Y_TOP)) < 1e-8", "assert abs(_tot - DEV_W * (BOX_H + Y_TOP)) < 1e-7"),
 ("ax_b.set_ylim(-0.45, 0.9)", "ax_b.set_ylim(-1.0, 0.9)"),
]
for x, y in rep:
    assert c0.count(x) == 1, x
    c0 = c0.replace(x, y)
nb = copy.deepcopy(nb)
L = c0.rstrip("\n").split("\n"); nb["cells"][0]["source"] = [l + "\n" for l in L[:-1]] + [L[-1]]
for c in nb["cells"]: c["outputs"] = []; c["execution_count"] = None
json.dump(nb, open(sys.argv[1], "w"), indent=1, ensure_ascii=False); print("wrote", sys.argv[1])
