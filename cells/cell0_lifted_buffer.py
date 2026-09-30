# %% [0] Geometry, Mesh & Material Configuration  --  LIFTED ELECTRODE ON A SiO2 BUFFER
#
#   Each electrode is ONE fused gold body made of three blocks:
#     lower block : sits on the SiO2 buffer, inner edge at the 3.2 um bottom gap
#     column      : 2.0 um wide riser on the outer end of the lower block
#     lifted pad  : runs outward on top of the 3.6 um SiO2 lift
#   The SiO2 buffer (BUFFER_H, 200 nm) covers the LN slab everywhere: under the
#   lower block, under the lift (where the two oxides form one layer) and across
#   the gap, where it fuses with the SiO2 cap.  BUFFER_H = 0 is supported and gives
#   back the plain lifted geometry (gold directly on the slab).
#
#   Vertical references (all measured from the buffer top = bottom of the gold):
#     lower block EL_H, SiO2 lift LIFT_H (pad bottom), pad EL_H, cap CAP_H.
import warnings
from collections import OrderedDict
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from shapely.affinity import scale as _scale
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import set_precision
from skfem import MeshTri
from femwell.mesh import mesh_from_OrderedDict

warnings.filterwarnings("ignore")

# ------------------------------------------------------------------------------
# femwell bug fix.  mesh_from_OrderedDict() tries to switch off gmsh's
# "extend mesh size from boundary" with `gmsh.model.mesh.MeshSizeExtendFromBoundary = 0`,
# which only sets a Python attribute: the gmsh option is never changed.  As a
# result every fine region pushes its size deep into its neighbours, so the
# `resolutions` dict does not describe the real mesh.  This wrapper applies the
# options femwell intended, right when it installs its background field.
import gmsh
if not getattr(gmsh.model.mesh.field, "_size_fix", False):
    _orig_set_bg = gmsh.model.mesh.field.setAsBackgroundMesh

    def _set_bg_fixed(tag):
        _orig_set_bg(tag)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

    gmsh.model.mesh.field.setAsBackgroundMesh = _set_bg_fixed
    gmsh.model.mesh.field._size_fix = True

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
BUFFER_H = 0.200                    # SiO2 buffer on the slab: under the electrodes, under the
                                    # lift and across the gap (0.0 = gold directly on the slab)
EL_H = 2.000                        # electrode thickness (lower block AND lifted pad)
LIFT_H = 3.600                      # SiO2 lift under the pad, from the buffer top to the pad bottom
CAP_H = 1.400                       # SiO2 cap on the rib, from the buffer top
CLAD_ABOVE = 2.000                  # air kept above the top of the electrodes

# ---- Horizontal Dimensions (um) ---------------------------------------------
WG_TOP = 1.0
ALPHA = 60.0
GAP_BOT = 3.2                       # gap between the lower blocks (on the buffer)
GAP_TOP = 10.0                      # gap between the columns (GAP_TOP = 2 * (x_lift - COL_W))
COL_W = 2.0                         # column (riser) width
CAP_W = 2.0                         # SiO2 cap width
EL_W = 30.0                         # total electrode width, from the gap edge outward
MARGIN = 5.0

basetta = WG_H / np.tan(np.deg2rad(ALPHA))
WG_BOTTOM = WG_TOP + 2.0 * basetta
OVERHANG = (GAP_TOP - GAP_BOT) / 2.0        # 3.4 um: lower block beyond the column
LOW_W = OVERHANG + COL_W                    # 5.4 um: lower-block width
X_LIFT = GAP_BOT / 2.0 + LOW_W              # 7.0 um: where the gold leaves the buffer
HAS_BUF = BUFFER_H > 1e-9
assert CAP_W > WG_BOTTOM, "cap must be wider than the rib base"
assert GAP_BOT > CAP_W, "cap must fit inside the bottom gap"
assert OVERHANG > 0 and EL_W > LOW_W, "inconsistent electrode dimensions"
assert LIFT_H > EL_H, "the pad must sit above the lower block"
assert BUFFER_H >= 0.0

# ---- Refractive Indices & Permittivities (at 1.575 um anchor) ----------------
ne, no = 2.136842, 2.210268
n_sio2 = 1.438749
eps_au = -120.7 - 11.9j             # Physical gold loss: Im(eps) < 0 in exp(+jwt)

# ---- Mesh scales -------------------------------------------------------------
# Convergence (BUFFER_H = 200 nm, gaps 3.2 / 10, x_lift = 7.0 um):
#   reference, everything near the mode refined 1.5-2x (220k triangles):
#       IL = 0.0473 dB/cm, Vpi*L = 2.1493 V*cm
#   these settings (67k triangles, ~75 s for 8 modes):
#       IL = 0.0481 dB/cm, Vpi*L = 2.1484 V*cm        (IL +1.7 %, Vpi*L -0.04 %)
#   one-at-a-time refinements (buffer 25/12.5 nm, skin 12/8 nm, slab 15 nm,
#   corners, lift step, far slab, gap/cap/core/BOX) all move IL by < 1 %.
# BUFFER_H = 0 falls back to the settings converged for the plain lifted model
# (12 nm skin: with gold directly on the slab the loss is 5x higher and the skin
# is the one parameter that matters).
h_core = 0.040
h_skin = 0.018 if HAS_BUF else 0.012        # the field decays into Au in ~22 nm

# Buffer: its size follows the layer THICKNESS (N_BUF_LAYERS elements across),
# capped at H_BUF_MAX.  A very thin buffer (< 50 nm) therefore gets a very fine,
# expensive mesh: cost ~ N_BUF_LAYERS^2 / BUFFER_H.
N_BUF_LAYERS = 4
H_BUF_MAX = 0.050
h_buf = min(BUFFER_H / N_BUF_LAYERS, H_BUF_MAX) if HAS_BUF else H_BUF_MAX

# Gold "skin": a 70 nm shell resolving the ~23 nm optical skin depth, only on the
# lower block (the column and the pad are >= 1.6 um from the mode):
#   * its whole bottom face (the loss channel), NOT graded;
#   * its inner wall (faces the rib across the gap), full height;
#   * the bottom of its outer wall, where the channel under the metal ends.
SKIN_T = 0.070
_SPLIT = min(2.5, 0.5 * LOW_W)
SKIN_SEGMENTS = [(0.0, _SPLIT, 1.0), (_SPLIT, LOW_W, 1.0)]  # offsets from the gap edge; kept
                                                            # as two regions for the loss map
OUTER_WALL_SKIN_H = 0.5
# Both bottom corners of each lower block carry a field singularity (metal wedge).
# A square patch of very fine mesh is carved around each of them, from every region
# it touches (metal / buffer or slab / air / lift SiO2), whatever BUFFER_H is.
CORNER_R = 0.050                    # corner patch half-size (um)
h_corner = 0.006                    # mesh size inside the corner patches (um)
# Where the gold leaves the buffer, the field guided in the buffer under the metal
# spills into the lift oxide: a short refined zone right outside the outer wall.
STEP_L = 1.0                        # length of that zone (um)
STEP_H = 0.300                      # its height above the buffer top (um)

MATERIALS = {
    "LN":     {"color": "#8b95a1", "eps_dc": (28.0, 44.0), "eps_opt": (ne**2, no**2, no**2), "desc": "LN Core / Slab"},
    "SiO2":   {"color": "#5aa9f0", "eps_dc": (3.75, 3.75), "eps_opt": (n_sio2**2, n_sio2**2, n_sio2**2), "desc": "SiO2 Cap / Buffer / Lift / Box"},
    "air":    {"color": "#ffffff", "eps_dc": (1.00, 1.00), "eps_opt": (1.00, 1.00, 1.00), "desc": "Air Cladding"},
    "Au_sig": {"color": "#f6c453", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Signal Electrode (+1V)"},
    "Au_gnd": {"color": "#e5a92e", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Ground Electrode (0V)"},
}

PREFIX_TO_MAT = [
    ("core", "LN"), ("cap", "SiO2"), ("buf", "SiO2"), ("lift", "SiO2"),
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

def _mirror_name(name):
    """elR_* <-> elL_*, *_r <-> *_l (names of mirrored right-half regions)."""
    if name.startswith("elR"):
        return "elL" + name[3:]
    assert name.endswith("_r"), name
    return name[:-2] + "_l"

# ============================================================
# 2. GEOMETRY GENERATOR
# ============================================================
def build_polygons():
    xg = GAP_BOT / 2.0                              # 1.60 um  lower-block inner edge
    x_col_in = GAP_TOP / 2.0                        # 5.00 um  column inner edge
    x_col_out = x_col_in + COL_W                    # 7.00 um  column outer edge = lower-block outer edge
    x_el_outer = xg + EL_W                          # 31.60 um end of the lifted pad
    DEV_W = 2.0 * x_el_outer + 2.0 * MARGIN         # 73.20 um
    x_dev_max = DEV_W / 2.0                         # 36.60 um
    x_near = min(x_col_out + 15.0, x_dev_max - 2.0) # 22.00 um refined-slab boundary (capped
                                                    # so the lift can be pushed far out)

    y_slab_bot = 0.0
    y_slab_top = SLAB_H                             # 0.275
    y_el_bot = y_slab_top + BUFFER_H                # 0.475  buffer top = bottom of the gold
    y_low_top = y_el_bot + EL_H                     # 2.475  top of the lower block
    y_pad_bot = y_el_bot + LIFT_H                   # 4.075  pad bottom = lift top
    y_el_top = y_pad_bot + EL_H                     # 6.075  pad / column top
    y_cap_top = y_el_bot + CAP_H                    # 1.875
    y_clad_top = y_el_top + CLAD_ABOVE              # 8.075
    CLAD_H = y_clad_top - SLAB_H
    y_box_bot = -BOX_H
    y_fine_top = y_el_bot + 0.6                     # above this the mode is < -25 dB

    # ---- 1. LN Rib Core ------------------------------------------------------
    core_poly = Polygon([
        (-WG_BOTTOM / 2.0, y_slab_top),
        (-WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_BOTTOM / 2.0, y_slab_top),
    ])

    # ---- 2. SiO2 Cap (2.0 um wide, 1.4 um above the buffer; fused with the buffer)
    cap_poly = box(-CAP_W / 2.0, y_slab_top, CAP_W / 2.0, y_fine_top).difference(core_poly)
    cap_up = box(-CAP_W / 2.0, y_fine_top, CAP_W / 2.0, y_cap_top)

    # ---- 3. Electrode (right = signal), three blocks Boolean-fused ----------
    low_r = box(xg, y_el_bot, x_col_out, y_low_top)
    col_r = box(x_col_in, y_low_top, x_col_out, y_el_top)
    pad_r = box(x_col_out, y_pad_bot, x_el_outer, y_el_top)
    el_r = unary_union([low_r, col_r, pad_r])
    assert el_r.geom_type == "Polygon", "electrode blocks do not fuse into one body"

    # segment ends snapped to x_col_out: xg + LOW_W and GAP_TOP/2 + COL_W can differ by
    # ~1e-15 (float round-off), which leaves a zero-width sliver that gmsh rejects
    _xe = lambda b: x_col_out if b >= LOW_W - 1e-9 else xg + b
    skins_r = [box(xg + a, y_el_bot, _xe(b), y_el_bot + SKIN_T) for (a, b, _f) in SKIN_SEGMENTS]
    skins_r[0] = unary_union([skins_r[0],                                       # inner wall
                              box(xg, y_el_bot, xg + SKIN_T, y_low_top)])
    skins_r[-1] = unary_union([skins_r[-1],                                     # outer wall foot
                               box(x_col_out - SKIN_T, y_el_bot,
                                   x_col_out, y_el_bot + OUTER_WALL_SKIN_H)])
    bulk_r = el_r.difference(unary_union(skins_r))

    # ---- 4. SiO2 buffer (only if BUFFER_H > 0) ------------------------------
    #      in the gap (between the cap and the lower block) and under the lower block
    bufgap_r = box(CAP_W / 2.0, y_slab_top, xg, y_el_bot) if HAS_BUF else None
    bufel_r = box(xg, y_slab_top, x_col_out, y_el_bot) if HAS_BUF else None

    # ---- 5. SiO2 lift under the pad (+ the buffer under it: one oxide), to the edge
    #      step zone : right outside the outer wall, where the buffer field spills out
    #      near       : the bottom 1 um, where the slab field lives
    lift_step_full = box(x_col_out, y_slab_top, x_col_out + STEP_L, y_el_bot + STEP_H)
    lift_near_full = box(x_col_out, y_slab_top, x_near, y_el_bot + 1.0)
    lift_step_r = lift_step_full
    lift_near_r = lift_near_full.difference(lift_step_full)
    lift_far_r = box(x_col_out, y_slab_top, x_dev_max, y_pad_bot).difference(lift_near_full)

    # ---- 6. LN Slab ----------------------------------------------------------
    slab_fine_full = box(-(x_col_out + 1.0), y_slab_bot, x_col_out + 1.0, y_slab_top)
    slab_fine = slab_fine_full
    slab_mid = box(-x_near, y_slab_bot, x_near, y_slab_top).difference(slab_fine_full)
    slab_far = box(-x_dev_max, y_slab_bot, x_dev_max, y_slab_top).difference(
        box(-x_near, y_slab_bot, x_near, y_slab_top))

    # ---- 7. SiO2 Underclad (BOX) --------------------------------------------
    # Fine only in the top 0.5 um (the mode's BOX tail decays as exp(-4.85 y/um)).
    box_near = box(-(xg + 1.0), -0.5, xg + 1.0, y_slab_bot)
    box_mid = box(-(xg + 1.0), -1.5, xg + 1.0, -0.5)
    box_far = box(-x_dev_max, y_box_bot, x_dev_max, y_slab_bot).difference(
        box(-(xg + 1.0), -1.5, xg + 1.0, y_slab_bot))

    # ---- 8. Air Cladding -----------------------------------------------------
    right = [el_r, lift_step_r, lift_near_r, lift_far_r] + ([bufgap_r, bufel_r] if HAS_BUF else [])
    solids = [core_poly, cap_poly, cap_up] + right + [mirror(p) for p in right]
    clad_all = box(-x_dev_max, y_slab_top, x_dev_max, y_clad_top).difference(unary_union(solids))
    clad_gap = clad_all.intersection(box(-xg, y_slab_top, xg, y_fine_top))
    clad_gap_up = clad_all.intersection(box(-xg, y_fine_top, xg, y_cap_top + 0.6))
    clad_far = clad_all.difference(box(-xg, y_slab_top, xg, y_cap_top + 0.6))

    # ---- 9. Assemble: centre regions + right-half regions and their mirrors ---
    centre = OrderedDict([
        ("core", core_poly), ("cap", cap_poly), ("cap_up", cap_up),
        ("slab_fine", slab_fine), ("slab_mid", slab_mid), ("slab_far", slab_far),
        ("box_near", box_near), ("box_mid", box_mid), ("box_far", box_far),
        ("clad_gap", clad_gap), ("clad_gap_up", clad_gap_up), ("clad_far", clad_far),
    ])
    halves = OrderedDict()
    for i, sk in enumerate(skins_r):
        halves[f"elR_skin{i}"] = sk
    halves["elR_bulk"] = bulk_r
    if HAS_BUF:
        halves["bufgap_r"] = bufgap_r
        halves["bufel_r"] = bufel_r
    halves["lift_step_r"] = lift_step_r
    halves["lift_near_r"] = lift_near_r
    halves["lift_far_r"] = lift_far_r
    for _n in list(halves):
        halves[_mirror_name(_n)] = mirror(halves[_n])

    # ---- 10. Corner patches: carve a (2r x 2r) square around each bottom corner
    #      of each lower block out of EVERY region it touches; each piece keeps the
    #      material of its parent (name prefix) and gets the h_corner mesh.
    r = CORNER_R
    corner_pts = {"cRI": (xg, y_el_bot), "cRO": (x_col_out, y_el_bot),
                  "cLI": (-xg, y_el_bot), "cLO": (-x_col_out, y_el_bot)}
    polys = OrderedDict(list(centre.items()) + list(halves.items()))
    pieces = OrderedDict()
    for tag, (cx, cy) in corner_pts.items():
        patch = box(cx - r, cy - r, cx + r, cy + r)
        for name in list(polys):
            piece = polys[name].intersection(patch)
            if piece.area > 1e-12:
                pieces[f"{name}_{tag}"] = piece
                polys[name] = polys[name].difference(patch)
    polys.update(pieces)
    # Snap every region to a 1 pm grid: coordinates that should coincide but differ by
    # float round-off (e.g. BUFFER_H == CORNER_R) would otherwise leave zero-width slivers
    # that gmsh rejects.  Regions that collapse entirely are dropped.
    polys = OrderedDict((k, set_precision(v, 1e-6)) for k, v in polys.items())
    polys = OrderedDict((k, v) for k, v in polys.items() if v.area > 1e-12)
    return polys, DEV_W, CLAD_H

# ============================================================
# 3. MESH GENERATION & RESOLUTION SETUP
# ============================================================
polygons, DEV_W, CLAD_H = build_polygons()

_base_res = {
    "core":        {"resolution": h_core,       "distance": 0.30},
    "cap":         {"resolution": 0.035,        "distance": 0.30},
    "cap_up":      {"resolution": 0.080,        "distance": 0.30},
    "clad_gap":    {"resolution": 0.040,        "distance": 0.30},
    "clad_gap_up": {"resolution": 0.100,        "distance": 0.30},
    "slab_fine":   {"resolution": 0.025,        "distance": 0.30},
    "slab_mid":    {"resolution": 0.110,        "distance": 0.40},
    "slab_far":    {"resolution": 0.150,        "distance": 0.50},
    "box_near":    {"resolution": 0.040,        "distance": 0.30},
    "box_mid":     {"resolution": 0.100,        "distance": 0.30},
    "box_far":     {"resolution": 0.800,        "distance": 1.00},
    "bufgap":      {"resolution": h_buf,        "distance": 0.20},
    "bufel":       {"resolution": h_buf,        "distance": 0.20},
    "lift_step":   {"resolution": 0.040,        "distance": 0.30},
    "lift_near":   {"resolution": 0.150,        "distance": 0.40},
    "lift_far":    {"resolution": 0.800,        "distance": 1.00},
    "elR_bulk":    {"resolution": 0.800,        "distance": 0.50},
    "elL_bulk":    {"resolution": 0.800,        "distance": 0.50},
    "clad_far":    {"resolution": 0.800,        "distance": 1.00},
}
for _i, (_a, _b, _f) in enumerate(SKIN_SEGMENTS):
    for _s in ("R", "L"):
        _base_res[f"el{_s}_skin{_i}"] = {"resolution": _f * h_skin, "distance": 0.20}

def _res_key(name):
    for suffix in ("_r", "_l"):
        if name.endswith(suffix) and name[:-2] in _base_res:
            return name[:-2]
    return name

resolutions = {}
for _k in polygons:
    if _k[-4:] in ("_cRI", "_cRO", "_cLI", "_cLO"):
        resolutions[_k] = {"resolution": h_corner, "distance": 0.10}
    else:
        resolutions[_k] = _base_res[_res_key(_k)]

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
      f"overhang {OVERHANG:.2f} um | lower block {LOW_W:.2f} um wide | lift at x = {X_LIFT:.2f} um")
if HAS_BUF:
    print(f"              SiO2 buffer {BUFFER_H*1e3:.0f} nm (h_buf = {h_buf*1e3:.1f} nm) | "
          f"electrodes {EL_H:.1f} um | pad on {LIFT_H:.1f} um lift | cap {CAP_W:.1f} x {CAP_H:.1f} um")
else:
    print(f"              NO buffer: gold on the LN slab | "
          f"electrodes {EL_H:.1f} um | pad on {LIFT_H:.1f} um lift | cap {CAP_W:.1f} x {CAP_H:.1f} um")

raw_mesh = mesh_from_OrderedDict(
    polygons,
    resolutions=resolutions,
    default_resolution_min=0.5 * min(h_skin, h_corner),
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
_buf_txt = rf"{BUFFER_H*1e3:.0f} nm $\mathrm{{SiO}}_2$ buffer" if HAS_BUF else "no buffer"
ax.set_title(rf"Lifted electrodes | gaps {GAP_BOT:.1f} / {GAP_TOP:.0f} $\mu$m | {_buf_txt} | "
             rf"{LIFT_H:.1f} $\mu$m lift | {skfem_mesh.nelements} triangles")
ax.set_xlim([-12.0, 12.0])
ax.set_ylim([-1.0, 6.8])
ax.set_xlabel(r"$x$ ($\mu$m)")
ax.set_ylabel(r"$y$ ($\mu$m)")
ax.set_aspect("equal")
plt.tight_layout()
plt.show()
