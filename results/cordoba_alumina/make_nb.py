"""Build VPI_interface_optimized_Cordoba_alumina.ipynb from the uploaded Cordoba etched-slab notebook.
Adds a conformal ALD Al2O3 layer (thickness T_ALD) on every exposed surface, no slab etch."""
import json, sys
src_nb, out_nb = sys.argv[1], sys.argv[2]
nb = json.load(open(src_nb))
s = ''.join(nb['cells'][0]['source'])

def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)

rep("# %% [0] Geometry, Mesh & Material Configuration  --  CORDOBA (NON-LIFTED) ELECTRODES, ETCHED LN SLAB\n#\n",
    "# %% [0] Geometry, Mesh & Material Configuration  --  CORDOBA ELECTRODES + CONFORMAL ALD Al2O3\n#\n"
    "#   ALD alumina protection layer of thickness T_ALD deposited AFTER the electrodes: it coats\n"
    "#   uniformly every surface exposed to air (electrode tops and walls, LN slab in the gap\n"
    "#   and outside the electrodes, SiO2 cap sides and top).  Gold still sits directly on LN.\n"
    "#   T_ALD = 0 reproduces the original Cordoba design exactly.\n#\n")
rep("WG_TOP = 1.0\n", "WG_TOP = 1.4\n")
rep("n_guess = 1.8755\nnum_modes_search = 8", "n_guess = 1.90       # wider rib (1.4 um): TE mode near 1.90\nnum_modes_search = 20  # gold surface modes crowd this window")
rep("SLAB_W = 10.0       #", "SLAB_W = 1.0e3      #")
rep("                    # >= DEV_W (e.g. 1e3) = no etch, the original Cordoba design\n",
    "                    # >= DEV_W (e.g. 1e3) = no etch, the original Cordoba design\n"
    "T_ALD = 0.040       # ALD Al2O3 thickness (um), conformal on all exposed surfaces; 0 = none\n"
    "N_ALD = 1.74        # ALD Al2O3 optical index at wl (amorphous film; user value)\n"
    "EPS_ALD_DC = 9.8    # ALD Al2O3 relative permittivity at RF/DC\n"
    "MESH_SCALE = 1.0    # global mesh-size multiplier (mesh-convergence studies)\n"
    "ALD_CELLS = 3.0     # target elements across the alumina thickness near the rib\n")
# materials
rep('    "air":    {"color": "#ffffff"',
    '    "Al2O3":  {"color": "#f472d0", "eps_dc": (EPS_ALD_DC, EPS_ALD_DC), "eps_opt": (N_ALD**2, N_ALD**2, N_ALD**2), "desc": "ALD Al2O3 Protection"},\n'
    '    "air":    {"color": "#ffffff"')
rep('    ("clad", "air"), ("elR", "Au_sig"), ("elL", "Au_gnd"),',
    '    ("clad", "air"), ("elR", "Au_sig"), ("elL", "Au_gnd"), ("alu", "Al2O3"),')
# geometry: alumina shell carved out of the air
rep('''    clad_all = box(-x_dev_max, 0.0, x_dev_max, y_clad_top).difference(solids)
''', '''    clad_all = box(-x_dev_max, 0.0, x_dev_max, y_clad_top).difference(solids)

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
''')
rep('''    base["clad_far"] = clad_far
''', '''    base["clad_far"] = clad_far
    base["alu_near"] = alu_near
    base["alu_far"] = alu_far
''')
# resolutions
rep('''    "clad_far":    (0.800, 1.00),
}''', '''    "clad_far":    (0.800, 1.00),
    "alu_near":    (min(0.012, T_ALD / ALD_CELLS) if T_ALD > 0 else 0.012, 0.10),
    "alu_far":     (max(T_ALD, 0.030), 0.30),
}''')
rep('''        resolutions[_k] = {"resolution": h_corner, "distance": 0.10}
    else:
        _r, _d = _base_res[_k]
        resolutions[_k] = {"resolution": _r, "distance": _d}''',
'''        resolutions[_k] = {"resolution": h_corner * MESH_SCALE, "distance": 0.10}
    else:
        _r, _d = _base_res[_k]
        resolutions[_k] = {"resolution": _r * MESH_SCALE, "distance": _d}''')
rep("    default_resolution_min=0.5 * min(h_skin, h_corner),",
    "    default_resolution_min=0.5 * MESH_SCALE * min(h_skin, h_corner, T_ALD / ALD_CELLS if T_ALD > 0 else 1.0),")
rep('print(f"              gap {GAP:.2f} um | flat electrodes {EL_W:.0f} x {MTX:.1f} um, gold out to x = {X_EL_OUT:.2f} um")',
    'print(f"              gap {GAP:.2f} um | flat electrodes {EL_W:.0f} x {MTX:.1f} um, gold out to x = {X_EL_OUT:.2f} um")\n'
    'print(f"              ALD Al2O3 {T_ALD*1e3:.0f} nm (n = {N_ALD}, eps_dc = {EPS_ALD_DC}) | WG_TOP {WG_TOP} um | MESH_SCALE {MESH_SCALE}")')
nb['cells'][0]['source'] = s.splitlines(keepends=True)
for c in nb['cells']:
    if c['cell_type'] == 'code':
        c['outputs'] = []; c['execution_count'] = None
json.dump(nb, open(out_nb, 'w'), indent=1)
print("ok")
