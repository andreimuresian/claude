"""Builds VPI_Madrid.ipynb from the Cordoba + ALD notebook (flat, non-lifted electrodes)."""
import json, re
SRC = "/home/user/claude/VPI_interface_optimized_Cordoba_alumina.ipynb"
nb = json.load(open(SRC))
s = "".join(nb["cells"][0]["source"])

def sub(old, new, count=1):
    global s
    assert s.count(old) >= 1, old[:60]
    s = s.replace(old, new, count)

i0 = s.index("import warnings")
s = '''# %% [0] Geometry, Mesh & Material Configuration  --  MADRID (1625 nm, very low Vpi)
#
#   Flat (non-lifted) Cordoba-type GSG electrodes on an unetched 275 nm LN slab
#   (550 nm film, 275 nm rib etch, 60 deg walls, rib top 1.4 um).
#   BUFFER_H : SiO2 buffer deposited after the rib etch over the whole wafer
#              (slab in the gap and under the gold); the gold sits on it.
#   Cap      : SiO2, CAP_W = GAP - 0.2 um wide, CAP_H = 0.5 um above the buffer top.
#   T_ALD    : conformal ALD Al2O3 over every exposed surface (after the gold).
#   MTX      : gold thickness above the buffer.
#   BUFFER_H = 0 and T_ALD = 0 give back flat Cordoba electrodes with a short wide cap.
''' + s[i0:]

sub("wl = 1.575          # um", "wl = 1.625          # um (L band)")
sub("n_guess = 1.90       # wider rib (1.4 um): TE mode near 1.90", "n_guess = 1.885      # TE mode of the 1.4 um rib at 1625 nm")
sub("num_modes_search = 20  # gold surface modes crowd this window", "num_modes_search = 6")
sub("GAP = 4.2\n", "GAP = 3.5\n")
sub("MTX = 2.0           # electrode thickness above the slab", "MTX = 2.0           # electrode (gold) thickness above the buffer")
sub("CAP_W = 2.0\nCAP_H = 1.40\n", "BUFFER_H = 0.100    # SiO2 buffer on the slab, under the gold and across the gap (um)\nCAP_W = round(GAP - 0.2, 6)   # wide, short cap\nCAP_H = 0.50        # cap height above the buffer top\n")
sub("N_ALD = 1.74        # ALD Al2O3 optical index at wl (amorphous film; user value)",
    "N_ALD = float(np.sqrt(1 + 1.5977254 * wl**2 / (wl**2 - 0.01075085)))  # ALD Al2O3 Sellmeier (fit to Zhukovsky 2015)")
sub('("clad", "air"), ("elR", "Au_sig"), ("elL", "Au_gnd"), ("alu", "Al2O3"),',
    '("clad", "air"), ("elR", "Au_sig"), ("elL", "Au_gnd"), ("alu", "Al2O3"), ("buf", "SiO2"),')

# ---- geometry: replace build_polygons() up to the base dict ------------------------
a = s.index("    y_slab_top = SLAB_H\n"); b = s.index("    base = OrderedDict()")
s = s[:a] + '''    y_slab_top = SLAB_H
    y_buf_top = round(SLAB_H + BUFFER_H, 6)
    y_el_top = y_buf_top + MTX
    y_cap_top = y_buf_top + CAP_H
    y_clad_top = y_slab_top + CLAD_H
    y_fine_top = y_slab_top + 0.6                   # above this the mode is < -25 dB
    y_cf = min(y_fine_top, y_cap_top)

    r_c = CORNER_R if BUFFER_H <= 0 else min(CORNER_R, 0.4 * BUFFER_H)
    assert r_c >= 0.004, "buffer too thin to mesh (use 0 or >= 10 nm)"

    # ---- 1. LN rib and slab (unetched) ----------------------------------------
    core_poly = Polygon([
        (-WG_BOTTOM / 2.0, y_slab_top), (-WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_TOP / 2.0, y_slab_top + WG_H), (WG_BOTTOM / 2.0, y_slab_top)])
    slab = box(-xs, 0.0, xs, y_slab_top)

    # ---- 2. SiO2 buffer (whole width) and cap (on the buffer) -----------------
    buf_all = box(-x_dev_max, y_slab_top, x_dev_max, y_buf_top) if BUFFER_H > 0 else Polygon()
    cap_poly = box(-CAP_W / 2.0, y_slab_top, CAP_W / 2.0, y_cf).difference(core_poly)
    if BUFFER_H > 0:
        cap_poly = _areal(cap_poly.difference(buf_all))
    cap_up = box(-CAP_W / 2.0, y_fine_top, CAP_W / 2.0, y_cap_top) if y_cap_top > y_fine_top + 1e-9 else Polygon()
    buf_all = _areal(buf_all.difference(core_poly)) if BUFFER_H > 0 else Polygon()

    # ---- 3. Electrode (right = signal): flat gold block on the buffer --------
    el_r = box(xg, y_buf_top, x_out, y_el_top)

    # ---- 4. BOX (fine only in the top 0.5 um near the rib) -------------------
    box_near = box(-(xg + 1.0), -0.5, xg + 1.0, 0.0)
    box_mid = box(-(xg + 1.0), -1.5, xg + 1.0, -0.5)
    box_far = box(-x_dev_max, -BOX_H, x_dev_max, 0.0).difference(
        box(-(xg + 1.0), -1.5, xg + 1.0, 0.0))

    # ---- 5. Air: everything left above the BOX -------------------------------
    solids = unary_union([core_poly, slab, buf_all, cap_poly, cap_up, el_r, mirror(el_r)])
    clad_all = box(-x_dev_max, 0.0, x_dev_max, y_clad_top).difference(solids)

    # ---- 5b. Conformal ALD Al2O3: the air within T_ALD of any solid (mitred corners)
    alu_near = alu_far = Polygon()
    if T_ALD > 0:
        shell = unary_union([solids, box(-x_dev_max, -BOX_H, x_dev_max, 0.0)]).buffer(
            T_ALD, join_style=2, mitre_limit=10.0)
        alu = _areal(clad_all.intersection(shell))
        clad_all = _areal(clad_all.difference(shell))
        near_box = box(-(xg + 1.0), 0.0, xg + 1.0, y_el_top + 0.5)
        alu_near = _areal(alu.intersection(near_box))
        alu_far = _areal(alu.difference(near_box))
    clad_gap = _areal(clad_all.intersection(box(-xg, 0.0, xg, y_fine_top)))
    clad_gap_up = _areal(clad_all.intersection(box(-xg, y_fine_top, xg, y_cap_top + 0.6)))
    clad_far = _areal(clad_all.difference(box(-xg, 0.0, xg, y_cap_top + 0.6)))

''' + s[b:]
sub('    base["cap_up"] = cap_up\n', '    base["cap_up"] = cap_up\n    base["buf_fine"] = _areal(buf_all.intersection(box(-x_fine, 0.0, x_fine, y_buf_top)))\n    base["buf_far"] = _areal(buf_all.difference(box(-x_fine, 0.0, x_fine, y_buf_top)))\n')
# corner patches / skin: gold now starts at y_buf_top
a = s.index("    pts = []\n"); b = s.index("    patches_r = unary_union")
s = s[:a] + "    pts = [(xg, y_buf_top), (x_out, y_buf_top)]     # gold / (buffer|LN) / air corners\n" + s[b:]
sub("        slab.buffer(SKIN_T, join_style=2),\n", "        box(xg, 0.0, x_out, y_buf_top + SKIN_T),\n")
sub('    "cap_up":      (0.080, 0.30),\n', '    "cap_up":      (0.080, 0.30),\n    "buf_fine":    (min(0.025, max(BUFFER_H, 0.01) / 2.0), 0.20),\n    "buf_far":     (max(min(0.15, BUFFER_H), 0.02), 0.30),\n')
sub("assert CAP_W > WG_BOTTOM and GAP > CAP_W and SLAB_W > CAP_W", "assert CAP_W > WG_BOTTOM and GAP > CAP_W and SLAB_W > CAP_W and GAP - CAP_W > 2 * T_ALD")
sub('print(f"              ALD Al2O3', 'print(f"              buffer {BUFFER_H*1e3:.0f} nm | cap {CAP_W:.2f} x {CAP_H:.2f} um")\nprint(f"              ALD Al2O3')
s = s.replace("Cordoba electrodes, cross-section", "Madrid, cross-section").replace("Cordoba electrodes, etched slab", "Madrid")
sub("    return polys, y_clad_top", """    import shapely
    out = OrderedDict()
    for k, p in polys.items():                      # snap to 1 pm: kills gmsh duplicate points
        q = _areal(shapely.set_precision(p, 1e-6))
        if not q.is_empty:
            out[k] = q
    return out, y_clad_top""")
sub("Y_TOP)) < 1e-8", "Y_TOP)) < 1e-5")
nb["cells"][0]["source"] = s.splitlines(True)
for c in nb["cells"]:
    c["outputs"] = []; c["execution_count"] = None
json.dump(nb, open("/home/user/claude/VPI_Madrid.ipynb", "w"), indent=1)
print("ok")
