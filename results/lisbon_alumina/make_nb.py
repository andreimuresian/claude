"""Lisbon lifted + 200 nm SiO2 buffer + conformal ALD Al2O3.  usage: make_nb.py src.ipynb out.ipynb"""
import json, sys
nb = json.load(open(sys.argv[1]))
s = ''.join(nb['cells'][0]['source'])
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:60], s.count(a)); s = s.replace(a, b)

rep("# %% [0] Geometry, Mesh & Material Configuration  --  LIFTED ELECTRODE ON A SiO2 BUFFER\n#\n",
    "# %% [0] Geometry, Mesh & Material Configuration  --  LIFTED ELECTRODE ON A SiO2 BUFFER + ALD Al2O3\n#\n"
    "#   ALD alumina protection layer (T_ALD) deposited last: it coats uniformly every surface\n"
    "#   exposed to air (electrode blocks, columns and pads, buffer in the gap, SiO2 cap,\n"
    "#   lift oxide).  T_ALD = 0 reproduces the buffered Lisbon design.\n#\n")
rep("n_guess = 1.8755\nnum_modes_search = 8", "n_guess = 1.90        # WG_TOP 1.4 um: TE mode near 1.90\nnum_modes_search = 20")
rep("GAP_BOT = 3.6  ", "GAP_BOT = 3.4  ")
rep("MARGIN = 5.0\n", "MARGIN = 5.0\nT_ALD = 0.040       # ALD Al2O3 thickness (um), conformal on all exposed surfaces; 0 = none\n"
    "N_ALD = 1.74        # ALD Al2O3 optical index at wl\nEPS_ALD_DC = 9.8    # ALD Al2O3 RF/DC permittivity\n"
    "ALD_CELLS = 3.0     # elements across the alumina near the rib\n")
# materials: same dispersion models as the Cordoba notebooks (Zelmon / Malitson / J&C)
rep('''ne, no = 2.136842, 2.210268
n_sio2 = 1.438749
eps_au = -120.7 - 11.9j             # Physical gold loss: Im(eps) < 0 in exp(+jwt)
''', '''# Same material models as the Cordoba notebooks: computed at wl.
def n_LN(lam):
    """Congruent LiNbO3, Zelmon et al., JOSA B 14, 3319 (1997).  Returns (ne, no)."""
    l2 = lam ** 2
    ne_ = np.sqrt(1 + 2.9804 * l2 / (l2 - 0.02047) + 0.5981 * l2 / (l2 - 0.0666)
                  + 8.9543 * l2 / (l2 - 416.08))
    no_ = np.sqrt(1 + 2.6734 * l2 / (l2 - 0.01764) + 1.2290 * l2 / (l2 - 0.05914)
                  + 12.614 * l2 / (l2 - 474.6))
    return ne_, no_


def n_SiO2(lam):
    """Fused silica, Malitson, JOSA 55, 1205 (1965)."""
    l2 = lam ** 2
    return np.sqrt(1 + 0.6961663 * l2 / (l2 - 0.0684043 ** 2)
                   + 0.4079426 * l2 / (l2 - 0.1162414 ** 2)
                   + 0.8974794 * l2 / (l2 - 9.896161 ** 2))


_AU_JC = np.array([
    (0.617, 0.21, 3.272), (0.659, 0.14, 3.697), (0.705, 0.13, 4.103),
    (0.756, 0.14, 4.542), (0.821, 0.16, 5.083), (0.892, 0.17, 5.663),
    (0.984, 0.22, 6.350), (1.088, 0.27, 7.150), (1.216, 0.35, 8.145),
    (1.393, 0.43, 9.519), (1.610, 0.56, 11.210), (1.937, 0.92, 13.780)])


def eps_Au_JC(lam):
    """Gold, Johnson & Christy, PRB 6, 4370 (1972); eps interpolated in photon energy."""
    lam_t, n_t, k_t = _AU_JC.T
    E_t = 1.239842 / lam_t
    eps_t = (n_t - 1j * k_t) ** 2
    E = 1.239842 / lam
    return complex(np.interp(E, E_t[::-1], eps_t.real[::-1]),
                   np.interp(E, E_t[::-1], eps_t.imag[::-1]))


ne, no = n_LN(wl)
n_sio2 = n_SiO2(wl)
eps_au = eps_Au_JC(wl)                 # Im(eps) < 0 is loss in exp(+jwt)
''')
rep('    "air":    {"color": "#ffffff"',
    '    "Al2O3":  {"color": "#f472d0", "eps_dc": (EPS_ALD_DC, EPS_ALD_DC), "eps_opt": (N_ALD**2, N_ALD**2, N_ALD**2), "desc": "ALD Al2O3 Protection"},\n'
    '    "air":    {"color": "#ffffff"')
rep('    ("elR", "Au_sig"), ("elL", "Au_gnd"),\n]', '    ("elR", "Au_sig"), ("elL", "Au_gnd"), ("alu", "Al2O3"),\n]')
rep('''    clad_all = box(-x_dev_max, y_slab_top, x_dev_max, y_clad_top).difference(unary_union(solids))
''', '''    clad_all = box(-x_dev_max, y_slab_top, x_dev_max, y_clad_top).difference(unary_union(solids))

    # ---- 8b. Conformal ALD Al2O3: the air within T_ALD of any solid (mitred corners)
    alu_near = alu_far = None
    if T_ALD > 0:
        shell = unary_union(solids + [box(-x_dev_max, y_box_bot, x_dev_max, y_slab_top)]).buffer(
            T_ALD, join_style=2, mitre_limit=10.0)
        alu = clad_all.intersection(shell)
        clad_all = clad_all.difference(shell)
        near_box = box(-(xg + 1.0), y_slab_top, xg + 1.0, y_low_top + 0.5)
        alu_near = alu.intersection(near_box)
        alu_far = alu.difference(near_box)
''')
rep('''        ("clad_gap", clad_gap), ("clad_gap_up", clad_gap_up), ("clad_far", clad_far),
    ])''', '''        ("clad_gap", clad_gap), ("clad_gap_up", clad_gap_up), ("clad_far", clad_far),
    ])
    if T_ALD > 0:
        centre["alu_near"] = alu_near
        centre["alu_far"] = alu_far''')
rep('''    "clad_far":    {"resolution": 0.800,        "distance": 1.00},
}''', '''    "clad_far":    {"resolution": 0.800,        "distance": 1.00},
    "alu_near":    {"resolution": min(0.012, T_ALD / ALD_CELLS) if T_ALD > 0 else 0.012, "distance": 0.10},
    "alu_far":     {"resolution": max(T_ALD, 0.030), "distance": 0.30},
}''')
rep("    default_resolution_min=0.5 * min(h_skin, h_corner),",
    "    default_resolution_min=0.5 * min(h_skin, h_corner, T_ALD / ALD_CELLS if T_ALD > 0 else 1.0),")
nb['cells'][0]['source'] = s.splitlines(keepends=True)
for c in nb['cells']:
    if c['cell_type'] == 'code': c['outputs'] = []; c['execution_count'] = None
json.dump(nb, open(sys.argv[2], 'w'), indent=1); print("ok")
