"""Istanbul notebook = attached etched-Cordoba notebook with the Istanbul electrode:
gap 4.45 um, 2.0 um gold that follows the slab (drops by SLAB_H beyond the slab end)."""
import json, copy, sys
src = json.load(open("/root/.claude/uploads/fd41e088-2b12-5532-ab62-ef0605547492/8633fc62-VPI_interface_optimized_Cordoba_etched_slab.ipynb"))
nb = copy.deepcopy(src)
c0 = [
 ("# %% [0] Geometry, Mesh & Material Configuration  --  CORDOBA (NON-LIFTED) ELECTRODES, ETCHED LN SLAB",
  "# %% [0] Geometry, Mesh & Material Configuration  --  ISTANBUL (C-band tapeout), ETCHED LN SLAB\n"
  "#\n#   Istanbul: same stack as the etched Cordoba cell, but the 2.0 um gold is deposited\n"
  "#   conformally: on the slab its top is at SLAB_H + MTX, beyond the slab end it sits on\n"
  "#   the BOX and its top drops by SLAB_H (275 nm).  Gap 4.45 um, slab 10.15 um (gap + 5.7).\n#"),
 ("GAP = 4.2\n", "GAP = 4.45\n"),
 ("MTX = 2.0           # electrode thickness above the slab", "MTX = 2.0           # gold thickness (conformal: on the slab and on the BOX)"),
 ("SLAB_W = 10.0       #", "SLAB_W = 10.15      #"),
 ("ETCHED = SLAB_W < DEV_W\n", "ETCHED = SLAB_W < DEV_W\nassert ETCHED and SLAB_W > GAP, \"Istanbul: the slab must end inside the gold\"\n"),
 ("    # ---- 3. Electrode (right = signal): flat gold block, filling the etched\n    #         slab region down to the BOX\n    el_r = box(xg, 0.0, x_out, y_el_top).difference(slab)",
  "    # ---- 3. Electrode (right = signal): conformal 2 um gold. On the slab (xg..xs)\n"
  "    #         the top is at SLAB_H + MTX; beyond the slab end it sits on the BOX\n"
  "    #         and its top drops to MTX (a 275 nm step at x = xs)\n"
  "    el_r = unary_union([box(xg, y_slab_top, xs, y_el_top), box(xs, 0.0, x_out, MTX)])"),
 ("Cordoba electrodes, cross-section as simulated", "Istanbul electrodes, cross-section as simulated"),
 ("Cordoba electrodes, etched slab |", "Istanbul electrodes, etched slab |"),
 ('flat electrodes {EL_W:.0f} x {MTX:.1f} um', 'conformal electrodes {EL_W:.0f} x {MTX:.1f} um (step -{SLAB_H*1e3:.0f} nm at the slab end)'),
]
def setsrc(c, text):
    lines = text.rstrip("\n").split("\n")
    c["source"] = [l + "\n" for l in lines[:-1]] + [lines[-1]]
for i, c in enumerate(nb["cells"]):
    text = "".join(c["source"])
    if i == 0:
        for a, b in c0:
            assert a in text, a
            text = text.replace(a, b)
    setsrc(c, text); c["outputs"] = []; c["execution_count"] = None
json.dump(nb, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
print("wrote", sys.argv[1])
