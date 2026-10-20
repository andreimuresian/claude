"""Danube notebook: Istanbul (60 deg slab) notebook with a new cell 0 (one arm of the GSG,
TEE / OE selectors).  Usage: make_nb.py out.ipynb"""
import json, copy, sys
H = "/home/user/claude/results/danube/"
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Istanbul_slanted_slab.ipynb"))
s = "".join(nb["cells"][0]["source"])
head = s[:s.index("# ============================================================\n# 1. FIXED")]
head = head[head.index("import warnings"):]
mat = s[s.index("# ---- Material dispersion"):s.index("# ---- Mesh scales")]
mesh_sc = s[s.index("# ---- Mesh scales"):s.index("MATERIALS = {")]
mats = s[s.index("MATERIALS = {"):s.index("# ============================================================\n# 2. GEOMETRY")]
res = s[s.index("# ============================================================\n# 3. MESH"):s.index("# ---- Validity")]
val = s[s.index("# ---- Validity"):s.index("# ---- Cross-section WITHOUT")]
res = res.replace('    "slab_fine":   (0.025, 0.30),\n    "slab_mid":    (0.110, 0.40),\n    "slab_far":    (0.150, 0.50),\n',
                  '    "slab_fine":   (0.025, 0.30),\n    "clad_near":   (0.050, 0.30),\n')
val = val.replace("assert abs(_tot - DEV_W * (BOX_H + Y_TOP)) < 1e-8", "assert abs(_tot - DEV_W * (BOX_H + Y_TOP)) < 1e-7")
a = val.index("_regime = ("); b = val.index("raw_mesh = ")
val = val[:a] + ('print(f"[geometry OK] {len(polygons)} regions tile exactly")\n'
 'print(f"              Danube {\'INSIDE\' if TEE else \'OUTSIDE\'} of tee | over-etch {OE*1e3:.0f} nm | slab top {SLAB_W:.2f} um "\n'
 '      f"(edge {SLAB_EXT:+.2f} um past each gap edge) | gap {GAP:.2f} um")\n'
 'print(f"              ground: {\'stub %.1f x %.1f um\' % (STUB_W, STUB_H) if TEE else \'%.0f x %.1f um\' % (GND_W, MTX)} | "\n'
 '      f"signal {SIG_W/2:.1f} um per arm (domain edge at the symmetry plane x = {X_R:.3f})")\n\n') + val[b:]
hdr = ("# %% [0] Geometry, Mesh & Material Configuration  --  DANUBE (O-band push-pull, one arm)\n#\n"
 "#   One arm of the GSG push-pull modulator, from the Istanbul notebook with 60 deg slab ends.\n"
 "#   The right domain edge is the signal centre (mirror plane, inside the gold): exact for one arm.\n"
 "#   Four cross-sections, chosen with TEE and OE:\n"
 "#     TEE = False: outside of tee, 28 um x 2 um ground   | TEE = True: inside of tee, 2.0 x 0.5 um ground stub\n"
 "#     OE  = 0.0  : standard BOX                         | OE  = 0.7 : BOX over-etched 700 nm outside the slab\n"
 "#   SLAB_W is the slab TOP width; the ground stub (inside of tee) does not move with SLAB_W.\n")
c0 = (hdr + head + open(H + "params.py").read() + mat + mesh_sc + mats
      + "# ============================================================\n# 2. GEOMETRY GENERATOR\n# ============================================================\n"
      + open(H + "bp.py").read() + res + val + open(H + "plot0.py").read())
c0 = c0.replace("X_FINE_MIN = 8.0                    # fine slab mesh reaches at least |x| = 8 um\n", "")
nb = copy.deepcopy(nb)
def setsrc(c, t):
    L = t.rstrip("\n").split("\n"); c["source"] = [l + "\n" for l in L[:-1]] + [L[-1]]
setsrc(nb["cells"][0], c0)
c1 = "".join(nb["cells"][1]["source"]).replace('ax0.text(-GAP / 2 - 5.5, SLAB_H + 0.8, "GROUND (0V)"', 'ax0.text(-GAP / 2 - 2.0, SLAB_H + 0.8, "GND"')
setsrc(nb["cells"][1], c1)
for c in nb["cells"]: c["outputs"] = []; c["execution_count"] = None
json.dump(nb, open(sys.argv[1], "w"), indent=1, ensure_ascii=False); print("wrote", sys.argv[1])
