# %% [0] Geometry, Mesh & Material Configuration (New Stepped Electrode & Buffer Geometry)
import warnings
from collections import OrderedDict
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from shapely.affinity import scale as _scale
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from skfem import MeshTri
from femwell.mesh import mesh_from_OrderedDict

warnings.filterwarnings("ignore")

# ============================================================
# 1. FIXED PHYSICAL & GEOMETRIC PARAMETERS
# ============================================================
wl = 1.575          # um (base reference)
wl_m = wl * 1e-6
k0 = 2.0 * np.pi / wl               # 1/um
k0_m = k0 * 1e6                     # 1/m
L_cm = 1.0          # cm
V_bias = 1.0        # V
r33 = 30.8e-12      # m/V
n_guess = 1.8755
num_modes_search = 10             # tighter gap -> more hybrid SPP modes near the shift

# Vertical Dimensions (um)
BOX_H = 4.7
TECN = 0.550
WG_H = 0.275
SLAB_H = TECN - WG_H                # 0.275 um (LN slab thickness)
BUFFER_H = 0.100                    # SiO2 buffer under the electrodes (SWEEP THIS)
EL_BOT_H = 0.500                    # 0.500 um (Bottom electrode thickness)
EL_TOP_H = 0.500                    # 0.500 um (Top electrode thickness)
CLAD_H = 15.0

# Horizontal Dimensions (um)
WG_TOP = 1.0
ALPHA = 60.0
GAP_BOT = 3.0                       # 3.0 um bottom electrode gap
GAP_TOP = 2.5                       # 2.5 um top electrode gap (protrudes inward by 0.25 um)
EL_W = 30.0                         # 30.0 um electrode width
MARGIN = 5.0

basetta = WG_H / np.tan(np.deg2rad(ALPHA))
WG_BOTTOM = WG_TOP + 2.0 * basetta

# Refractive Indices & Permittivities (at 1.575 um anchor)
ne, no = 2.136842, 2.210268
n_sio2 = 1.438749
eps_au = -120.7 - 11.9j             # Physical gold loss: Im(eps) < 0 in exp(+jwt)

# Skin layer configuration (70 nm strip resolves the 23 nm optical skin depth)
SKIN_T = 0.070
SKIN_SEGMENTS = [(0.0, 5.0, 1.0), (5.0, 10.0, 1.6), (10.0, 20.0, 2.5)]
SKIN_LEN = SKIN_SEGMENTS[-1][1]

# Buffer mesh scale MUST track BUFFER_H, otherwise a thickness sweep silently
# sweeps mesh quality too (1 element across at 20 nm, 8 at 100 nm).
N_BUF_LAYERS = 4
h_buf = BUFFER_H / N_BUF_LAYERS

MATERIALS = {
    "LN":     {"color": "#2ecc71", "eps_dc": (28.0, 44.0), "eps_opt": (ne**2, no**2, no**2), "desc": "LN Core / Slab"},
    "SiO2":   {"color": "#00ebfc", "eps_dc": (3.75, 3.75), "eps_opt": (n_sio2**2, n_sio2**2, n_sio2**2), "desc": "SiO2 Cap / Buffer / Box"},
    "air":    {"color": "#ffffff", "eps_dc": (1.00, 1.00), "eps_opt": (1.00, 1.00, 1.00), "desc": "Air Cladding"},
    "Au_sig": {"color": "#f39c12", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Signal Electrode (+1V)"},
    "Au_gnd": {"color": "#e67e22", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Ground Electrode (0V)"},
}

PREFIX_TO_MAT = [
    ("core", "LN"), ("cap", "SiO2"), ("buf", "SiO2"),
    ("slab", "LN"), ("box", "SiO2"), ("clad", "air"),
    ("elR", "Au_sig"), ("elL", "Au_gnd"),
]

def material_of(region_name):
    base = region_name.split("___")[0]
    for prefix, mat in PREFIX_TO_MAT:
        if base.startswith(prefix):
            return mat
    raise KeyError(f"Unknown material for region: {region_name}")

def mirror(p):
    return _scale(p, xfact=-1.0, yfact=1.0, origin=(0, 0))

# ============================================================
# 2. GEOMETRY GENERATOR
# ============================================================
def build_polygons():
    xg_bot = GAP_BOT / 2.0                          # 1.50 um
    xg_top = GAP_TOP / 2.0                          # 1.25 um
    x_el_outer = xg_bot + EL_W                      # 31.50 um
    DEV_W = 2.0 * x_el_outer + 2.0 * MARGIN         # 73.00 um total device width
    x_dev_max = DEV_W / 2.0                         # 36.50 um
    x_near = xg_bot + SKIN_LEN                      # 21.50 um (active zone boundary)

    y_slab_bot = 0.0
    y_slab_top = SLAB_H                             # 0.275 um
    y_buf_top  = SLAB_H + BUFFER_H                  # 0.375 um (bottom face of bottom electrode)
    y_bot_el_top = y_buf_top + EL_BOT_H             # 0.875 um (top face of bottom electrode & cap)
    y_top_el_top = y_bot_el_top + EL_TOP_H         # 1.375 um (top face of top electrode)
    y_clad_top = SLAB_H + CLAD_H                    # 15.275 um
    y_box_bot  = -BOX_H                             # -4.700 um

    # 1. LN Rib Core
    core_poly = Polygon([
        (-WG_BOTTOM / 2.0, y_slab_top),
        (-WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_BOTTOM / 2.0, y_slab_top),
    ])

    # 2. Central SiO2 Cap (enlarged to GAP_BOT, flush with top of bottom electrode)
    cap_poly = box(-xg_bot, y_slab_top, xg_bot, y_bot_el_top).difference(core_poly)

    # 3. SiO2 Buffer Layer under electrodes, graded like the skin
    buf_segs_r = [box(xg_bot + a, y_slab_top, xg_bot + b, y_buf_top)
                  for (a, b, _f) in SKIN_SEGMENTS]
    buf_far_r  = box(x_near, y_slab_top, x_dev_max, y_buf_top)
    buf_far_l  = mirror(buf_far_r)

    # 4. Right Bottom Electrode (0.5 um thick, gap = 3.0 um)
    el_r_bot = box(xg_bot, y_buf_top, x_el_outer, y_bot_el_top)
    skins_r_bot = [box(xg_bot + min(a, EL_W), y_buf_top,
                       xg_bot + min(b, EL_W), y_buf_top + SKIN_T)
                   for (a, b, _f) in SKIN_SEGMENTS if min(b, EL_W) > min(a, EL_W)]
    skins_r_bot[0] = unary_union([skins_r_bot[0],
                                  box(xg_bot, y_buf_top, xg_bot + SKIN_T, y_bot_el_top)])
    bulk_r_bot = el_r_bot.difference(unary_union(skins_r_bot))

    # 5. Right Top Electrode (0.5 um thick, gap = 2.5 um, overhangs by 0.25 um)
    el_r_top = box(xg_top, y_bot_el_top, x_el_outer, y_top_el_top)
    skin_top_wall = box(xg_top, y_bot_el_top, xg_top + SKIN_T, y_top_el_top)
    skin_top_overhang = box(xg_top, y_bot_el_top, xg_bot, y_bot_el_top + SKIN_T)
    skin_r_top = unary_union([skin_top_wall, skin_top_overhang])
    bulk_r_top = el_r_top.difference(skin_r_top)

    # 6. Left Electrodes (Mirrored)
    bulk_l_bot = mirror(bulk_r_bot)
    skin_l_top = mirror(skin_r_top)
    bulk_l_top = mirror(bulk_r_top)

    # 7. LN Slab
    slab_near = box(-x_near, y_slab_bot, x_near, y_slab_top)
    slab_far  = box(-x_dev_max, y_slab_bot, x_dev_max, y_slab_top).difference(slab_near)

    # 8. SiO2 Underclad (BOX)
    box_near = box(-x_near, -1.5, x_near, y_slab_bot)
    box_far  = box(-x_dev_max, y_box_bot, x_dev_max, y_slab_bot).difference(box_near)

    # 9. Air Cladding
    all_solid = unary_union([
        core_poly, cap_poly,
        *buf_segs_r, *[mirror(s) for s in buf_segs_r], buf_far_r, buf_far_l,
        el_r_bot, el_r_top, mirror(el_r_bot), mirror(el_r_top)
    ])
    clad_all = box(-x_dev_max, y_slab_top, x_dev_max, y_clad_top).difference(all_solid)
    clad_gap = clad_all.intersection(box(-xg_top, y_bot_el_top, xg_top, y_top_el_top + 2.5))
    clad_far = clad_all.difference(clad_gap)

    polys = OrderedDict()
    polys["core"] = core_poly
    polys["cap"] = cap_poly
    for i, sg in enumerate(buf_segs_r):
        polys[f"bufR_{i}"] = sg
        polys[f"bufL_{i}"] = mirror(sg)
    polys["buf_far_r"] = buf_far_r
    polys["buf_far_l"] = buf_far_l

    for i, sk in enumerate(skins_r_bot):
        polys[f"elR_bot_skin{i}"] = sk
        polys[f"elL_bot_skin{i}"] = mirror(sk)
    polys["elR_bot_bulk"] = bulk_r_bot
    polys["elR_top_skin"] = skin_r_top
    polys["elR_top_bulk"] = bulk_r_top

    polys["elL_bot_bulk"] = bulk_l_bot
    polys["elL_top_skin"] = skin_l_top
    polys["elL_top_bulk"] = bulk_l_top

    polys["slab_near"] = slab_near
    polys["slab_far"] = slab_far
    polys["box_near"] = box_near
    polys["box_far"] = box_far
    polys["clad_gap"] = clad_gap
    polys["clad_far"] = clad_far

    return polys, DEV_W

# ============================================================
# 3. MESH GENERATION & RESOLUTION SETUP
# ============================================================
h_core = 0.040
h_skin = 0.025

polygons, DEV_W = build_polygons()

resolutions = {
    "core":           {"resolution": h_core,        "distance": 0.30},
    "cap":            {"resolution": 1.5 * h_core,  "distance": 0.30},
    # >21.5 um from the gap the buffer carries no field: floor the size so a very
    # thin BUFFER_H does not explode the element count out here.
    "buf_far_r":      {"resolution": max(4.0 * h_buf, 0.10), "distance": 0.50},
    "buf_far_l":      {"resolution": max(4.0 * h_buf, 0.10), "distance": 0.50},
    "clad_gap":       {"resolution": 2.0 * h_core,  "distance": 0.40},
    "slab_near":      {"resolution": 0.050,         "distance": 0.30},
    "box_near":       {"resolution": 0.080,         "distance": 0.50},
    "elR_bot_bulk":   {"resolution": 0.300,         "distance": 0.50},
    "elR_top_skin":   {"resolution": h_skin,        "distance": 0.20},
    "elR_top_bulk":   {"resolution": 0.300,         "distance": 0.50},
    "elL_bot_bulk":   {"resolution": 0.300,         "distance": 0.50},
    "elL_top_skin":   {"resolution": h_skin,        "distance": 0.20},
    "elL_top_bulk":   {"resolution": 0.300,         "distance": 0.50},
    "slab_far":       {"resolution": 0.150,         "distance": 0.50},
    "box_far":        {"resolution": 0.800,         "distance": 1.00},
    "clad_far":       {"resolution": 0.800,         "distance": 1.00},
}

for _i, (_a, _b, _f) in enumerate(SKIN_SEGMENTS):
    for _s in ("R", "L"):
        resolutions[f"buf{_s}_{_i}"]        = {"resolution": _f * h_buf,  "distance": 0.20}
        resolutions[f"el{_s}_bot_skin{_i}"] = {"resolution": _f * h_skin, "distance": 0.20}

assert set(resolutions) == set(polygons), (
    f"resolution/polygon mismatch: {set(resolutions) ^ set(polygons)}")
_names = list(polygons)
for _n, _p in polygons.items():
    assert _p.is_valid and not _p.is_empty and _p.area > 1e-12, f"degenerate region {_n}"
for _i in range(len(_names)):
    for _j in range(_i + 1, len(_names)):
        _ov = polygons[_names[_i]].intersection(polygons[_names[_j]]).area
        assert _ov < 1e-10, f"overlap {_names[_i]} & {_names[_j]}: {_ov:.2e}"
_tot = sum(p.area for p in polygons.values())
assert abs(_tot - DEV_W * (BOX_H + SLAB_H + CLAD_H)) < 1e-8, "tiling gap"
print(f"[geometry OK] {len(polygons)} regions tile exactly | BUFFER_H={BUFFER_H*1e3:.0f} nm, "
      f"h_buf={h_buf*1e3:.1f} nm ({N_BUF_LAYERS} layers across)")

raw_mesh = mesh_from_OrderedDict(
    polygons,
    resolutions=resolutions,
    default_resolution_min=0.5 * min(h_skin, h_buf),
    default_resolution_max=0.6,
)
skfem_mesh = MeshTri(raw_mesh.points[:, :2].T, raw_mesh.cells_dict["triangle"].T)
tri_subdomains = raw_mesh.cell_data_dict["gmsh:physical"]["triangle"]
name_to_id = {
    name: data[0] if hasattr(data, "__getitem__") else data
    for name, data in raw_mesh.field_data.items()
}

mat_of_el = np.empty(skfem_mesh.nelements, dtype=object)
for raw_name, s_id in name_to_id.items():
    if raw_name.split("___")[0] in polygons:
        mat_of_el[tri_subdomains == s_id] = material_of(raw_name)

assert not np.any(mat_of_el == None), (  # noqa: E711
    f"{int(np.sum(mat_of_el == None))} unassigned elements")  # noqa: E711
print(f"[mesh OK] {skfem_mesh.nelements} triangles, {skfem_mesh.nvertices} vertices")

# Cross-section visualization
fig, ax = plt.subplots(figsize=(12, 4.5))
legend_patches = []
seen = set()

for raw_name, s_id in name_to_id.items():
    if raw_name.split("___")[0] not in polygons:
        continue
    mat_key = material_of(raw_name)
    col = MATERIALS[mat_key]["color"]
    elem_idx = np.where(tri_subdomains == s_id)[0]
    if elem_idx.size == 0:
        continue
    sub_mesh = MeshTri(skfem_mesh.p, skfem_mesh.t[:, elem_idx])
    sub_mesh.plot(
        np.zeros(sub_mesh.nelements),
        ax=ax,
        shading="flat",
        cmap=plt.matplotlib.colors.ListedColormap([col]),
    )
    sub_mesh.draw(ax=ax, color="black", lw=0.15)
    if mat_key not in seen:
        legend_patches.append(mpatches.Patch(color=col, label=f"{mat_key}: {MATERIALS[mat_key]['desc']}"))
        seen.add(mat_key)

ax.legend(handles=legend_patches, loc="upper right", framealpha=0.9)
ax.set_title(rf"Stepped Electrodes & {BUFFER_H*1e3:.0f} nm $\mathrm{{SiO}}_2$ Buffer "
             rf"($h_{{buf}}$={h_buf*1e3:.1f} nm, {N_BUF_LAYERS} layers across)")
ax.set_xlim([-5.0, 5.0])
ax.set_ylim([-0.5, 2.0])
ax.set_xlabel(r"$x$ ($\mu$m)")
ax.set_ylabel(r"$y$ ($\mu$m)")
ax.set_aspect("equal")
plt.tight_layout()
plt.show()