# %% [0] Geometry, Mesh & Material Configuration
#        SINGLE-GAP ASYMMETRIC ELECTRODES: short ground (0.5 um) / tall signal (10 um)
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
num_modes_search = 8

# ---- Vertical Dimensions (um) ------------------------------------------------
BOX_H = 4.7
TECN = 0.550
WG_H = 0.275
SLAB_H = TECN - WG_H                # 0.275 um (LN slab thickness)
BUFFER_H = 0.100                    # SiO2 buffer under the electrodes
EL_GND_H = 0.500                    # ground (left) electrode height
EL_SIG_H = 10.000                   # signal (right) electrode height  <-- TALL
CAP_H = 1.400                       # SiO2 cap height, measured FROM THE BUFFER TOP
CLAD_ABOVE = 2.000                  # air kept above the tallest metal feature

# ---- Horizontal Dimensions (um) ---------------------------------------------
WG_TOP = 1.0
ALPHA = 60.0
GAP_BOT = 4.15                      # THE single electrode gap (name kept: cells 4/5 use it)
CAP_W = 2.0                         # SiO2 cap width (no longer spans the gap)
EL_W = 30.0                         # electrode width (both)
MARGIN = 5.0

basetta = WG_H / np.tan(np.deg2rad(ALPHA))
WG_BOTTOM = WG_TOP + 2.0 * basetta
assert CAP_W > WG_BOTTOM, "cap must be wider than the rib base"
assert GAP_BOT > CAP_W, "cap must fit inside the gap"

# ---- Refractive Indices & Permittivities (at 1.575 um anchor) ----------------
ne, no = 2.136842, 2.210268
n_sio2 = 1.438749
eps_au = -120.7 - 11.9j             # Physical gold loss: Im(eps) < 0 in exp(+jwt)

# ---- Mesh scales -------------------------------------------------------------
h_core = 0.040
h_skin = 0.025

# Gold "skin" strips: a 70 nm shell resolving the ~23 nm optical skin depth,
# graded laterally away from the gap.  (a, b, factor) are offsets from the
# electrode inner edge, in um; the local size is factor * h_skin.
SKIN_T = 0.070
SKIN_SEGMENTS = [(0.0, 5.0, 1.0), (5.0, 10.0, 1.6), (10.0, 20.0, 2.5)]
SKIN_LEN = SKIN_SEGMENTS[-1][1]
# How far up the inner wall of each electrode the fine skin is carried.
# The ground electrode is only 0.5 um tall, so it gets skinned all the way
# (bottom + wall + top).  The signal electrode is 10 um tall: the mode is long
# gone by 2 um, so skinning it to the roof would be pure waste.
WALL_SKIN_H = 2.0
TOP_SKIN_LEN = 5.0                  # length of the ground electrode's top skin

# Buffer mesh scale MUST track BUFFER_H, otherwise a thickness sweep silently
# sweeps mesh quality too.  BUFFER_H = 0 is supported (buffer dropped entirely).
HAS_BUF = BUFFER_H > 1e-9
N_BUF_LAYERS = 2
h_buf = BUFFER_H / N_BUF_LAYERS if HAS_BUF else h_skin

# The buffer is graded far harder than the skin: its size is set by the layer
# THICKNESS, so a long fine strip is ruinously expensive.  Cost ~ N^2 / BUFFER_H.
# (a, b, factor) are offsets from the CAP EDGE, since the buffer now runs the
# full device width rather than starting at the electrode.
BUF_SEGMENTS = [(0.0, 3.0, 1.0), (3.0, 10.0, 3.0), (10.0, 20.0, 9.0)]
BUF_LEN = BUF_SEGMENTS[-1][1]

MATERIALS = {
    "LN":     {"color": "#8b95a1", "eps_dc": (28.0, 44.0), "eps_opt": (ne**2, no**2, no**2), "desc": "LN Core / Slab"},
    "SiO2":   {"color": "#5aa9f0", "eps_dc": (3.75, 3.75), "eps_opt": (n_sio2**2, n_sio2**2, n_sio2**2), "desc": "SiO2 Cap / Buffer / Box"},
    "air":    {"color": "#ffffff", "eps_dc": (1.00, 1.00), "eps_opt": (1.00, 1.00, 1.00), "desc": "Air Cladding"},
    "Au_sig": {"color": "#f6c453", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Signal Electrode (+1V), 10 um tall"},
    "Au_gnd": {"color": "#e5a92e", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Ground Electrode (0V), 0.5 um tall"},
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
    xg = GAP_BOT / 2.0                              # 2.075 um, electrode inner edge
    x_cap = CAP_W / 2.0                             # 1.000 um, cap edge
    x_el_outer = xg + EL_W                          # 32.075 um
    DEV_W = 2.0 * x_el_outer + 2.0 * MARGIN         # 74.150 um
    x_dev_max = DEV_W / 2.0                         # 37.075 um
    x_near = xg + SKIN_LEN                          # 22.075 um (active zone boundary)
    x_buf_near = x_cap + BUF_LEN                    # 21.000 um (end of graded buffer)

    y_slab_bot = 0.0
    y_slab_top = SLAB_H                             # 0.275
    y_buf_top = SLAB_H + BUFFER_H                   # 0.375 -- electrodes rest here
    y_gnd_top = y_buf_top + EL_GND_H                # 0.875
    y_sig_top = y_buf_top + EL_SIG_H                # 10.375
    y_cap_top = y_buf_top + CAP_H                   # 1.775 (cap measured from buffer top)
    y_clad_top = max(y_sig_top, y_gnd_top, y_cap_top) + CLAD_ABOVE     # 12.375
    CLAD_H = y_clad_top - SLAB_H                    # 12.100
    y_box_bot = -BOX_H

    # ---- 1. LN Rib Core ------------------------------------------------------
    core_poly = Polygon([
        (-WG_BOTTOM / 2.0, y_slab_top),
        (-WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_BOTTOM / 2.0, y_slab_top),
    ])

    # ---- 2. Central SiO2 Cap -------------------------------------------------
    # 2.0 um wide, from the slab surface up to y_cap_top.  The 0.1 um slice
    # between the slab and the buffer top is the same SiO2, so it is simply
    # absorbed into the cap here rather than meshed as a separate sliver.
    cap_poly = box(-x_cap, y_slab_top, x_cap, y_cap_top).difference(core_poly)

    # ---- 3. SiO2 Buffer, full device width outside the cap -------------------
    if HAS_BUF:
        buf_segs_r = [box(x_cap + a, y_slab_top, x_cap + b, y_buf_top)
                      for (a, b, _f) in BUF_SEGMENTS]
        buf_far_r = box(x_buf_near, y_slab_top, x_dev_max, y_buf_top)
        buf_far_l = mirror(buf_far_r)
        buf_all = [*buf_segs_r, *[mirror(s) for s in buf_segs_r], buf_far_r, buf_far_l]
    else:
        buf_segs_r, buf_far_r, buf_far_l, buf_all = [], None, None, []

    # ---- 4/5. Electrodes -----------------------------------------------------
    # Common builder: bottom skin strip graded by SKIN_SEGMENTS, plus an inner
    # wall skin of height `wall_h`, plus (optionally) a top skin strip.
    def build_electrode(height, wall_h, top_skin):
        body = box(xg, y_buf_top, x_el_outer, y_buf_top + height)
        wall_h = min(wall_h, height)
        skins = [box(xg + min(a, EL_W), y_buf_top,
                     xg + min(b, EL_W), y_buf_top + SKIN_T)
                 for (a, b, _f) in SKIN_SEGMENTS if min(b, EL_W) > min(a, EL_W)]
        skins[0] = unary_union([skins[0],
                                box(xg, y_buf_top, xg + SKIN_T, y_buf_top + wall_h)])
        if top_skin:
            y_t = y_buf_top + height
            skins[0] = unary_union([skins[0],
                                    box(xg, y_t - SKIN_T,
                                        xg + min(TOP_SKIN_LEN, EL_W), y_t)])
        bulk = body.difference(unary_union(skins))
        return body, skins, bulk

    # Right = SIGNAL, 10 um tall.  Wall skinned to 2 um only; no top skin (the
    # roof is 10 um above the mode).
    el_r, skins_r, bulk_r = build_electrode(EL_SIG_H, WALL_SKIN_H, top_skin=False)
    # Left = GROUND, 0.5 um tall.  Fully shelled: bottom + wall + top, because
    # its top face sits only ~0.6 um above the slab and does see the mode.
    el_l_r, skins_l_r, bulk_l_r = build_electrode(EL_GND_H, EL_GND_H, top_skin=True)
    el_l = mirror(el_l_r)
    skins_l = [mirror(s) for s in skins_l_r]
    bulk_l = mirror(bulk_l_r)

    # ---- 7. LN Slab ----------------------------------------------------------
    slab_fine = box(-(xg + 5.0), y_slab_bot, xg + 5.0, y_slab_top)
    slab_mid = box(-x_near, y_slab_bot, x_near, y_slab_top).difference(slab_fine)
    slab_far = box(-x_dev_max, y_slab_bot, x_dev_max, y_slab_top).difference(
        unary_union([slab_fine, slab_mid]))

    # ---- 8. SiO2 Underclad (BOX) --------------------------------------------
    # The BOX carries almost no field: keep the refined part tight around the
    # gap.  Letting it follow x_near costs ~20k triangles for nothing.
    box_near = box(-(xg + 1.0), -1.5, xg + 1.0, y_slab_bot)
    box_far = box(-x_dev_max, y_box_bot, x_dev_max, y_slab_bot).difference(box_near)

    # ---- 9. Air Cladding -----------------------------------------------------
    all_solid = unary_union([core_poly, cap_poly, *buf_all, el_r, el_l])
    clad_all = box(-x_dev_max, y_slab_top, x_dev_max, y_clad_top).difference(all_solid)
    # Fine air only in the gap, up to a little above the cap.
    clad_gap = clad_all.intersection(box(-xg, y_slab_top, xg, y_cap_top + 1.0))
    clad_far = clad_all.difference(clad_gap)

    polys = OrderedDict()
    polys["core"] = core_poly
    polys["cap"] = cap_poly
    for i, sg in enumerate(buf_segs_r):
        polys[f"bufR_{i}"] = sg
        polys[f"bufL_{i}"] = mirror(sg)
    if HAS_BUF:
        polys["buf_far_r"] = buf_far_r
        polys["buf_far_l"] = buf_far_l

    for i, sk in enumerate(skins_r):
        polys[f"elR_skin{i}"] = sk
    polys["elR_bulk"] = bulk_r
    for i, sk in enumerate(skins_l):
        polys[f"elL_skin{i}"] = sk
    polys["elL_bulk"] = bulk_l

    polys["slab_fine"] = slab_fine
    polys["slab_mid"] = slab_mid
    polys["slab_far"] = slab_far
    polys["box_near"] = box_near
    polys["box_far"] = box_far
    polys["clad_gap"] = clad_gap
    polys["clad_far"] = clad_far

    return polys, DEV_W, CLAD_H

# ============================================================
# 3. MESH GENERATION & RESOLUTION SETUP
# ============================================================
polygons, DEV_W, CLAD_H = build_polygons()

resolutions = {
    "core":       {"resolution": h_core,       "distance": 0.30},
    "cap":        {"resolution": 1.5 * h_core, "distance": 0.30},
    "clad_gap":   {"resolution": 2.0 * h_core, "distance": 0.40},
    "slab_fine":  {"resolution": 0.050,        "distance": 0.30},
    "slab_mid":   {"resolution": 0.110,        "distance": 0.40},
    "box_near":   {"resolution": 0.080,        "distance": 0.50},
    "elR_bulk":   {"resolution": 0.800,        "distance": 0.50},
    "elL_bulk":   {"resolution": 0.800,        "distance": 0.50},
    "slab_far":   {"resolution": 0.150,        "distance": 0.50},
    "box_far":    {"resolution": 0.800,        "distance": 1.00},
    "clad_far":   {"resolution": 0.800,        "distance": 1.00},
}

for _i, (_a, _b, _f) in enumerate(SKIN_SEGMENTS):
    for _s in ("R", "L"):
        _k = f"el{_s}_skin{_i}"
        if _k in polygons:
            resolutions[_k] = {"resolution": _f * h_skin, "distance": 0.20}

if HAS_BUF:
    for _i, (_a, _b, _f) in enumerate(BUF_SEGMENTS):
        for _s in ("R", "L"):
            resolutions[f"buf{_s}_{_i}"] = {"resolution": _f * h_buf, "distance": 0.20}
    # Far from the gap the buffer carries no field: floor its size so a very
    # thin BUFFER_H cannot explode the element count.
    for _s in ("_r", "_l"):
        resolutions[f"buf_far{_s}"] = {"resolution": max(9.0 * h_buf, 0.10), "distance": 0.50}

# ---- Validity / consistency assertions ---------------------------------------
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
assert abs(_tot - DEV_W * (BOX_H + SLAB_H + CLAD_H)) < 1e-8, (
    f"tiling gap: {_tot:.6f} vs {DEV_W * (BOX_H + SLAB_H + CLAD_H):.6f}")

print(f"[geometry OK] {len(polygons)} regions tile exactly")
print(f"              gap = {GAP_BOT:.3f} um | ground {EL_GND_H:.2f} um tall | "
      f"signal {EL_SIG_H:.2f} um tall")
print(f"              cap {CAP_W:.2f} x {CAP_H:.2f} um from buffer top "
      f"(y = {SLAB_H + BUFFER_H:.3f} -> {SLAB_H + BUFFER_H + CAP_H:.3f})")
if HAS_BUF:
    print(f"              buffer {BUFFER_H*1e3:.0f} nm, full width | "
          f"h_buf = {h_buf*1e3:.1f} nm ({N_BUF_LAYERS} layers across)")
else:
    print("              NO BUFFER (electrodes rest directly on the LN slab)")
print(f"              DEV_W = {DEV_W:.2f} um, CLAD_H = {CLAD_H:.2f} um "
      f"(air to y = {SLAB_H + CLAD_H:.2f})")

_est = sum(2 * polygons[k].area / resolutions[k]["resolution"] ** 2 for k in polygons)
print(f"              estimated total mesh ~{_est:,.0f} triangles")

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

# ---- Cross-section visualization ---------------------------------------------
fig, ax = plt.subplots(figsize=(12, 5.0))
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
    sub_mesh.plot(np.zeros(sub_mesh.nelements), ax=ax, shading="flat",
                  cmap=plt.matplotlib.colors.ListedColormap([col]))
    sub_mesh.draw(ax=ax, color="black", lw=0.15)
    if mat_key not in seen:
        legend_patches.append(mpatches.Patch(color=col, label=f"{mat_key}: {MATERIALS[mat_key]['desc']}"))
        seen.add(mat_key)

ax.legend(handles=legend_patches, loc="upper right", framealpha=0.9, fontsize=8)
ax.set_title(rf"Single gap {GAP_BOT:.2f} $\mu$m | ground {EL_GND_H:.1f} $\mu$m / "
             rf"signal {EL_SIG_H:.0f} $\mu$m | {BUFFER_H*1e3:.0f} nm $\mathrm{{SiO}}_2$ buffer")
ax.set_xlim([-8.0, 8.0])
ax.set_ylim([-1.0, 4.0])
ax.set_xlabel(r"$x$ ($\mu$m)")
ax.set_ylabel(r"$y$ ($\mu$m)")
ax.set_aspect("equal")
plt.tight_layout()
plt.show()
