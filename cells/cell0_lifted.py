# %% [0] Geometry, Mesh & Material Configuration  --  LIFTED-ELECTRODE GEOMETRY
#
#   Each electrode is ONE fused gold body made of three blocks:
#     lower block : sits directly on the LN slab, inner edge at the 4.2 um gap
#     column      : 2.0 um wide riser on the outer end of the lower block
#     lifted pad  : runs outward on top of the 3.6 um SiO2 buffer
#   Bottom gap 4.2 um (lower blocks), top gap 10 um (columns), overhang 2.9 um.
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
EL_H = 2.000                        # electrode thickness (lower block AND lifted pad)
BUFFER_H = 3.600                    # SiO2 buffer under the LIFTED pad (not under the lower block)
CAP_H = 1.400                       # SiO2 cap on the rib, measured from the slab top
CLAD_ABOVE = 2.000                  # air kept above the top of the electrodes

# ---- Horizontal Dimensions (um) ---------------------------------------------
WG_TOP = 1.0
ALPHA = 60.0
GAP_BOT = 4.2                       # gap between the lower blocks (on the slab)
GAP_TOP = 10.0                      # gap between the columns
COL_W = 2.0                         # column (riser) width
CAP_W = 2.0                         # SiO2 cap width
EL_W = 30.0                         # total electrode width, from the gap edge outward
MARGIN = 5.0

basetta = WG_H / np.tan(np.deg2rad(ALPHA))
WG_BOTTOM = WG_TOP + 2.0 * basetta
OVERHANG = (GAP_TOP - GAP_BOT) / 2.0        # 2.9 um: lower block beyond the column
LOW_W = OVERHANG + COL_W                    # 4.9 um: lower-block width on the slab
assert CAP_W > WG_BOTTOM, "cap must be wider than the rib base"
assert GAP_BOT > CAP_W, "cap must fit inside the bottom gap"
assert OVERHANG > 0 and EL_W > LOW_W, "inconsistent electrode dimensions"

# ---- Refractive Indices & Permittivities (at 1.575 um anchor) ----------------
ne, no = 2.136842, 2.210268
n_sio2 = 1.438749
eps_au = -120.7 - 11.9j             # Physical gold loss: Im(eps) < 0 in exp(+jwt)

# ---- Mesh scales (values from the mesh-convergence study) --------------------
h_core = 0.040
h_skin = 0.025

# Gold "skin": a 70 nm shell resolving the ~23 nm optical skin depth.
# Only the lower block touches the mode, so only the lower block is shelled:
#   * its whole bottom face on the LN slab (the loss channel), graded laterally;
#   * its inner wall (faces the rib across the gap), full height;
#   * the bottom of its outer wall, where the channel under the metal ends.
# The column and the lifted pad are >= 2 um from the slab: bulk mesh only.
SKIN_T = 0.070
SKIN_SEGMENTS = [(0.0, 2.5, 1.0), (2.5, LOW_W, 1.6)]   # offsets from the gap edge
SKIN_LEN = SKIN_SEGMENTS[-1][1]
OUTER_WALL_SKIN_H = 0.5

MATERIALS = {
    "LN":     {"color": "#8b95a1", "eps_dc": (28.0, 44.0), "eps_opt": (ne**2, no**2, no**2), "desc": "LN Core / Slab"},
    "SiO2":   {"color": "#5aa9f0", "eps_dc": (3.75, 3.75), "eps_opt": (n_sio2**2, n_sio2**2, n_sio2**2), "desc": "SiO2 Cap / Buffer / Box"},
    "air":    {"color": "#ffffff", "eps_dc": (1.00, 1.00), "eps_opt": (1.00, 1.00, 1.00), "desc": "Air Cladding"},
    "Au_sig": {"color": "#f6c453", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Signal Electrode (+1V)"},
    "Au_gnd": {"color": "#e5a92e", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Ground Electrode (0V)"},
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
    xg = GAP_BOT / 2.0                              # 2.10 um  lower-block inner edge
    x_col_in = GAP_TOP / 2.0                        # 5.00 um  column inner edge
    x_col_out = x_col_in + COL_W                    # 7.00 um  column outer edge = lower-block outer edge
    x_el_outer = xg + EL_W                          # 32.10 um end of the lifted pad
    DEV_W = 2.0 * x_el_outer + 2.0 * MARGIN         # 74.20 um
    x_dev_max = DEV_W / 2.0                         # 37.10 um
    x_near = x_col_out + 15.0                       # 22.00 um refined-slab boundary

    y_slab_bot = 0.0
    y_slab_top = SLAB_H                             # 0.275
    y_low_top = y_slab_top + EL_H                   # 2.275  top of the lower block
    y_buf_top = y_slab_top + BUFFER_H               # 3.875  pad bottom
    y_el_top = y_buf_top + EL_H                     # 5.875  pad / column top
    y_cap_top = y_slab_top + CAP_H                  # 1.675
    y_clad_top = y_el_top + CLAD_ABOVE              # 7.875
    CLAD_H = y_clad_top - SLAB_H                    # 7.600
    y_box_bot = -BOX_H

    # ---- 1. LN Rib Core ------------------------------------------------------
    core_poly = Polygon([
        (-WG_BOTTOM / 2.0, y_slab_top),
        (-WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_BOTTOM / 2.0, y_slab_top),
    ])

    # ---- 2. SiO2 Cap (2.0 x 1.4 um, on the slab) ----------------------------
    cap_poly = box(-CAP_W / 2.0, y_slab_top, CAP_W / 2.0, y_cap_top).difference(core_poly)

    # ---- 3. Electrode (right = signal), three blocks Boolean-fused ----------
    low_r = box(xg, y_slab_top, x_col_out, y_low_top)
    col_r = box(x_col_in, y_low_top, x_col_out, y_el_top)
    pad_r = box(x_col_out, y_buf_top, x_el_outer, y_el_top)
    el_r = unary_union([low_r, col_r, pad_r])
    assert el_r.geom_type == "Polygon", "electrode blocks do not fuse into one body"

    skins_r = [box(xg + a, y_slab_top, xg + b, y_slab_top + SKIN_T)
               for (a, b, _f) in SKIN_SEGMENTS]
    skins_r[0] = unary_union([skins_r[0],                                       # inner wall
                              box(xg, y_slab_top, xg + SKIN_T, y_low_top)])
    skins_r[-1] = unary_union([skins_r[-1],                                     # outer wall foot
                               box(x_col_out - SKIN_T, y_slab_top,
                                   x_col_out, y_slab_top + OUTER_WALL_SKIN_H)])
    bulk_r = el_r.difference(unary_union(skins_r))

    # ---- 4. SiO2 buffer under the lifted pad, full height, to the domain edge
    #      "near" part: the bottom of the buffer, where the slab field lives.
    buf_near_r = box(x_col_out, y_slab_top, x_near, y_slab_top + 1.0)
    buf_far_r = box(x_col_out, y_slab_top, x_dev_max, y_buf_top).difference(buf_near_r)

    # ---- 5. LN Slab ----------------------------------------------------------
    slab_fine = box(-(x_col_out + 1.0), y_slab_bot, x_col_out + 1.0, y_slab_top)
    slab_mid = box(-x_near, y_slab_bot, x_near, y_slab_top).difference(slab_fine)
    slab_far = box(-x_dev_max, y_slab_bot, x_dev_max, y_slab_top).difference(
        unary_union([slab_fine, slab_mid]))

    # ---- 6. SiO2 Underclad (BOX) --------------------------------------------
    box_near = box(-(xg + 1.0), -1.5, xg + 1.0, y_slab_bot)
    box_far = box(-x_dev_max, y_box_bot, x_dev_max, y_slab_bot).difference(box_near)

    # ---- 7. Air Cladding -----------------------------------------------------
    solids = [core_poly, cap_poly, el_r, mirror(el_r),
              buf_near_r, buf_far_r, mirror(buf_near_r), mirror(buf_far_r)]
    clad_all = box(-x_dev_max, y_slab_top, x_dev_max, y_clad_top).difference(unary_union(solids))
    clad_gap = clad_all.intersection(box(-xg, y_slab_top, xg, y_cap_top + 0.6))
    clad_far = clad_all.difference(clad_gap)

    polys = OrderedDict()
    polys["core"] = core_poly
    polys["cap"] = cap_poly
    for i, sk in enumerate(skins_r):
        polys[f"elR_skin{i}"] = sk
        polys[f"elL_skin{i}"] = mirror(sk)
    polys["elR_bulk"] = bulk_r
    polys["elL_bulk"] = mirror(bulk_r)
    polys["buf_near_r"] = buf_near_r
    polys["buf_near_l"] = mirror(buf_near_r)
    polys["buf_far_r"] = buf_far_r
    polys["buf_far_l"] = mirror(buf_far_r)
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
    "core":        {"resolution": h_core,       "distance": 0.30},
    "cap":         {"resolution": 1.5 * h_core, "distance": 0.30},
    "clad_gap":    {"resolution": 2.0 * h_core, "distance": 0.40},
    "slab_fine":   {"resolution": 0.050,        "distance": 0.30},
    "slab_mid":    {"resolution": 0.110,        "distance": 0.40},
    "slab_far":    {"resolution": 0.150,        "distance": 0.50},
    "box_near":    {"resolution": 0.080,        "distance": 0.50},
    "box_far":     {"resolution": 0.800,        "distance": 1.00},
    "buf_near_r":  {"resolution": 0.150,        "distance": 0.40},
    "buf_near_l":  {"resolution": 0.150,        "distance": 0.40},
    "buf_far_r":   {"resolution": 0.800,        "distance": 1.00},
    "buf_far_l":   {"resolution": 0.800,        "distance": 1.00},
    "elR_bulk":    {"resolution": 0.800,        "distance": 0.50},
    "elL_bulk":    {"resolution": 0.800,        "distance": 0.50},
    "clad_far":    {"resolution": 0.800,        "distance": 1.00},
}
for _i, (_a, _b, _f) in enumerate(SKIN_SEGMENTS):
    for _s in ("R", "L"):
        resolutions[f"el{_s}_skin{_i}"] = {"resolution": _f * h_skin, "distance": 0.20}

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
assert abs(_tot - DEV_W * (BOX_H + SLAB_H + CLAD_H)) < 1e-8, "tiling gap"

print(f"[geometry OK] {len(polygons)} regions tile exactly")
print(f"              gaps: bottom {GAP_BOT:.2f} um / top {GAP_TOP:.2f} um | "
      f"overhang {OVERHANG:.2f} um | lower block {LOW_W:.2f} um wide on the slab")
print(f"              electrodes {EL_H:.1f} um thick | pad lifted on {BUFFER_H:.1f} um SiO2 | "
      f"cap {CAP_W:.1f} x {CAP_H:.1f} um")

raw_mesh = mesh_from_OrderedDict(
    polygons,
    resolutions=resolutions,
    default_resolution_min=0.5 * h_skin,
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
fig, ax = plt.subplots(figsize=(13, 4.8))
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
ax.set_title(rf"Lifted electrodes | gaps {GAP_BOT:.1f} / {GAP_TOP:.0f} $\mu$m | "
             rf"{BUFFER_H:.1f} $\mu$m $\mathrm{{SiO}}_2$ lift | {skfem_mesh.nelements} triangles")
ax.set_xlim([-12.0, 12.0])
ax.set_ylim([-1.0, 6.5])
ax.set_xlabel(r"$x$ ($\mu$m)")
ax.set_ylabel(r"$y$ ($\mu$m)")
ax.set_aspect("equal")
plt.tight_layout()
plt.show()
