# %% [0] Geometry, Mesh & Material Configuration  --  BUFFERED / SPLIT-ELECTRODE VARIANT
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
wl = 1.575          # um
wl_m = wl * 1e-6
k0 = 2.0 * np.pi / wl               # 1/um
k0_m = k0 * 1e6                     # 1/m
L_cm = 1.0          # cm
V_bias = 1.0        # V
r33 = 30.8e-12      # m/V
n_guess = 1.8755
num_modes_search = 10               # +2 vs. previous: tighter gap => more hybrid SPP modes near the shift

# --- Vertical stack (um), y = 0 at the BOX / LN interface --------------------
BOX_H = 4.7
TECN = 0.550
WG_H = 0.275
SLAB_H = TECN - WG_H                # 0.275  -> top of the LN slab
WG_TOP = 1.0
ALPHA = 60.0
CLAD_H = 15.0

BUF_H = 0.100                       # NEW: SiO2 buffer decoupling slab from electrodes
EL_BOT_H = 0.500                    # NEW: bottom electrode thickness
EL_TOP_H = 0.500                    # NEW: top electrode thickness

# --- Lateral (um) ------------------------------------------------------------
GAP_BOT = 3.00                      # NEW: bottom-electrode gap
GAP_TOP = 2.50                      # NEW: top-electrode gap (protrudes 0.25 um/side toward the rib)
EL_W = 30.0                         # bottom-electrode width; dissipates the lateral SPP
CAP_W = GAP_BOT                     # NEW: cap widened to exactly fill the bottom gap
CAP_H = 1.40                        # cap height above the slab (see NOTE below)

# NOTE on CAP_H -- the one parameter the spec left open.
#   CAP_H = 1.40 (kept, "all other parameters equal"): the cap is TALLER than the
#     electrode stack, so the top-electrode overhang is embedded in the oxide and a
#     0.25 x 0.30 um block of SiO2 sits above it. Physical (trench-filled metal).
#   CAP_H = BUF_H + EL_BOT_H = 0.60: cap top flush with the bottom electrode, so the
#     overhang sits ON the cap -- this is what the reference sketch literally shows,
#     but it leaves only 0.325 um of oxide over the rib and will change neff/loss.
#   Change this single line to switch; the booleans below handle either case.

basetta = WG_H / np.tan(np.deg2rad(ALPHA))
WG_BOTTOM = WG_TOP + 2.0 * basetta

# --- Derived interface levels & x-stations ----------------------------------
Y_SLAB = SLAB_H                     # top of LN slab            0.275
Y_BUF = Y_SLAB + BUF_H              # top of buffer = el. floor 0.375
Y_EB = Y_BUF + EL_BOT_H             # bottom/top electrode seam 0.875
Y_ET = Y_EB + EL_TOP_H              # top of electrode stack    1.375

XB = GAP_BOT / 2.0                  # 1.50  inner edge of bottom electrode = cap edge
XT = GAP_TOP / 2.0                  # 1.25  inner edge of top electrode
X_OUT = XB + EL_W                   # 31.50 outer edge, shared by both electrode halves
DEV_W = 2.0 * X_OUT + 10.0          # 73.0

# --- Refractive Indices & Permittivities ------------------------------------
ne, no = 2.136842, 2.210268
n_sio2 = 1.438749
eps_au = -120.7 - 11.9j             # Physical gold loss: Im(eps) < 0 in exp(+jwt)

# Skin layer configuration (70 nm strip resolves the 23 nm optical skin depth)
SKIN_T = 0.070
SKIN_SEGMENTS = [(0.0, 5.0, 1.0), (5.0, 10.0, 1.6), (10.0, 20.0, 2.5)]

# Mesh scales (from the convergence study)
h_core = 0.040
h_skin = 0.025
h_buf = 0.030                       # NEW: buffer is only 100 nm thick -> ~3 layers across

MATERIALS = {
    "LN":     {"color": "#2ecc71", "eps_dc": (28.0, 44.0), "eps_opt": (ne**2, no**2, no**2), "desc": "LN Core / Slab"},
    "SiO2":   {"color": "#00ebfc", "eps_dc": (3.75, 3.75), "eps_opt": (n_sio2**2, n_sio2**2, n_sio2**2), "desc": "SiO2 Cap / Buffer / Underclad"},
    "air":    {"color": "#ffffff", "eps_dc": (1.00, 1.00), "eps_opt": (1.00, 1.00, 1.00), "desc": "Air Cladding"},
    "Au_sig": {"color": "#f39c12", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Signal Electrode (+1V)"},
    "Au_gnd": {"color": "#e67e22", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Ground Electrode (0V)"},
}

# "buf" added; note "buf" never shadows "box" under startswith().
PREFIX_TO_MAT = [
    ("core", "LN"), ("cap", "SiO2"), ("slab", "LN"), ("box", "SiO2"),
    ("buf", "SiO2"), ("clad", "air"), ("elR", "Au_sig"), ("elL", "Au_gnd"),
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
# 2. DOMAIN DISCRETIZATION
#    Returns (polygons, resolutions) together so the two can never drift apart.
#    Every region is built strictly non-overlapping; the asserts below prove it.
# ============================================================
def build_polygons():
    polys, res = OrderedDict(), {}

    # ---- LN rib ------------------------------------------------------------
    core = Polygon([
        (-WG_BOTTOM / 2.0, Y_SLAB),
        (-WG_TOP / 2.0, Y_SLAB + WG_H),
        (WG_TOP / 2.0, Y_SLAB + WG_H),
        (WG_BOTTOM / 2.0, Y_SLAB),
    ])

    # ---- Electrodes: drawn as two blocks, unioned into ONE conductor body --
    # Outer edges are flush at X_OUT; only the inner edge differs (XB vs XT).
    el_bot_r = box(XB, Y_BUF, X_OUT, Y_EB)
    el_top_r = box(XT, Y_EB, X_OUT, Y_ET)
    el_r = unary_union([el_bot_r, el_top_r])          # fused -> single Polygon

    # ---- Gold skin strips on the optically-exposed metal faces -------------
    # (a) underside of the bottom electrode, graded in x  (the dominant Au/SiO2 SPP face)
    skins_r = []
    for (a, b, _f) in SKIN_SEGMENTS:
        a_c, b_c = min(a, EL_W), min(b, EL_W)
        if b_c <= a_c:
            continue
        skins_r.append(box(XB + a_c, Y_BUF, XB + b_c, Y_BUF + SKIN_T))
    # (b) inner sidewall of the bottom electrode, merged into segment 0
    skins_r[0] = unary_union([skins_r[0], box(XB, Y_BUF, XB + SKIN_T, Y_EB)])
    # (c) inner sidewall of the TOP electrode + underside of its 0.25 um overhang.
    #     This wraps the re-entrant metal corner nearest the rib - the new loss hot spot.
    skin_top_r = unary_union([
        box(XT, Y_EB, XT + SKIN_T, Y_ET),
        box(XT, Y_EB, XB, Y_EB + SKIN_T),
    ]).difference(unary_union(skins_r))
    bulk_r = el_r.difference(unary_union(skins_r + [skin_top_r]))
    skin_len = min(SKIN_SEGMENTS[-1][1], EL_W)

    # ---- Oxide: cap (over the gap) + 100 nm buffer (everywhere else) -------
    # Booleans are metal-wins, so this stays valid for any CAP_H.
    cap = box(-XB, Y_SLAB, XB, Y_SLAB + CAP_H).difference(
        unary_union([core, el_r, mirror(el_r)])
    )
    buf_full = box(-DEV_W / 2.0, Y_SLAB, DEV_W / 2.0, Y_BUF)
    buf_segs = [box(XB + a, Y_SLAB, XB + b, Y_BUF) for (a, b, _f) in SKIN_SEGMENTS]
    buf_far = buf_full.difference(unary_union(
        buf_segs + [mirror(s) for s in buf_segs] + [box(-XB, Y_SLAB, XB, Y_BUF)]
    ))

    # ---- Slab / BOX / cladding --------------------------------------------
    slab_near = box(-XB - skin_len, 0.0, XB + skin_len, Y_SLAB)
    slab_far = box(-DEV_W / 2.0, 0.0, DEV_W / 2.0, Y_SLAB).difference(slab_near)

    box_near = box(-XB - 1.0, -1.5, XB + 1.0, 0.0)
    box_far = box(-DEV_W / 2.0, -BOX_H, DEV_W / 2.0, 0.0).difference(box_near)

    solids = unary_union([core, cap, el_r, mirror(el_r), buf_full])
    clad = box(-DEV_W / 2.0, Y_SLAB, DEV_W / 2.0, Y_SLAB + CLAD_H).difference(solids)
    clad_gap = clad.intersection(box(-XB - 0.5, Y_SLAB, XB + 0.5, Y_SLAB + 2.5))
    clad_far = clad.difference(clad_gap)

    # ---- Register regions + their mesh sizes -------------------------------
    def add(name, poly, resolution, distance):
        polys[name] = poly
        res[name] = {"resolution": resolution, "distance": distance}

    add("core", core, h_core, 0.30)
    add("cap", cap, 1.5 * h_core, 0.30)

    for i, (s, (_a, _b, f)) in enumerate(zip(skins_r, SKIN_SEGMENTS)):
        add(f"elR_bskin{i}", s, f * h_skin, 0.20)
        add(f"elL_bskin{i}", mirror(s), f * h_skin, 0.20)
    add("elR_tskin", skin_top_r, h_skin, 0.20)
    add("elL_tskin", mirror(skin_top_r), h_skin, 0.20)
    add("elR_bulk", bulk_r, 0.300, 0.50)
    add("elL_bulk", mirror(bulk_r), 0.300, 0.50)

    for i, (s, (_a, _b, f)) in enumerate(zip(buf_segs, SKIN_SEGMENTS)):
        add(f"bufR_{i}", s, f * h_buf, 0.20)
        add(f"bufL_{i}", mirror(s), f * h_buf, 0.20)
    add("buf_far", buf_far, 0.120, 0.50)

    add("slab_near", slab_near, 0.050, 0.30)
    add("slab_far", slab_far, 0.150, 0.50)
    add("box_near", box_near, 0.080, 0.50)
    add("box_far", box_far, 0.800, 1.00)
    add("clad_gap", clad_gap, 2.0 * h_core, 0.50)
    add("clad_far", clad_far, 0.800, 1.00)

    return polys, res


polygons, resolutions = build_polygons()

# ============================================================
# 3. GEOMETRY SANITY CHECKS (cheap; protects you when editing parameters)
# ============================================================
_names = list(polygons)
for _n, _p in polygons.items():
    assert _p.is_valid and not _p.is_empty and _p.area > 1e-9, f"degenerate region: {_n}"
for _i in range(len(_names)):
    for _j in range(_i + 1, len(_names)):
        _ov = polygons[_names[_i]].intersection(polygons[_names[_j]]).area
        assert _ov < 1e-10, f"regions overlap: {_names[_i]} & {_names[_j]} ({_ov:.2e})"
_tot = sum(p.area for p in polygons.values())
_full = DEV_W * (BOX_H + Y_SLAB + CLAD_H)
assert abs(_tot - _full) < 1e-8, f"tiling gap/overlap: {_tot:.9f} vs {_full:.9f}"
assert set(resolutions) == set(polygons)
assert WG_BOTTOM / 2.0 < XB, "rib base is wider than the cap / bottom gap"
_sig_body = unary_union([p for n, p in polygons.items() if n.startswith("elR")])
assert _sig_body.geom_type == "Polygon", "signal electrode is not a single fused body"
print(f"[geometry OK] {len(polygons)} regions tile {_full:.4f} um^2 exactly; "
      f"electrode stack fused, area = {_sig_body.area:.4f} um^2")

# ============================================================
# 4. MESH
# ============================================================
raw_mesh = mesh_from_OrderedDict(
    polygons,
    resolutions=resolutions,
    default_resolution_min=0.5 * h_skin,   # must stay BELOW the finest requested size
    default_resolution_max=0.6,            # matches the converged diagnostic
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
    f"{int(np.sum(mat_of_el == None))} elements unassigned - a region name escaped PREFIX_TO_MAT"  # noqa: E711
)
print(f"[mesh OK] {skfem_mesh.nelements} triangles, {skfem_mesh.nvertices} vertices")
for _m in MATERIALS:
    print(f"    {_m:<8} {int(np.sum(mat_of_el == _m)):>7d} elements")

print("=" * 84)
print(f"{'CANONICAL MATERIAL':<32} | {'DC EPS (x, y)':<16} | {'OPTICAL EPS (xx, yy, zz)':<28}")
print("-" * 84)
for key, data in MATERIALS.items():
    dc_s = f"({data['eps_dc'][0]:.1f}, {data['eps_dc'][1]:.1f})"
    opt_val = data["eps_opt"][0]
    opt_s = f"({opt_val.real:.1f}{opt_val.imag:+.1f}j)" if np.iscomplex(opt_val) else f"({opt_val.real:.3f})"
    print(f"{data['desc']:<32} | {dc_s:<16} | {opt_s:<28}")
print("=" * 84)

# ============================================================
# 5. CROSS-SECTION VISUALIZATION
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(15, 4.6))
for ax, (xlim, ylim, ttl) in zip(axes, [
    ((-8.0, 8.0), (-1.5, 2.5), "Full cross-section"),
    ((-2.2, 2.2), (0.1, 1.8), "Gap detail: buffer, cap & split electrodes"),
]):
    legend_patches, seen = [], set()
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
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_title(ttl, fontsize=10)
    ax.set_xlabel(r"$x$ ($\mu$m)")
    ax.set_ylabel(r"$y$ ($\mu$m)")
    ax.set_aspect("equal")
axes[0].legend(handles=legend_patches, loc="upper right", fontsize=7, framealpha=0.9)
fig.suptitle(
    rf"TFLN rib + {BUF_H*1e3:.0f} nm SiO$_2$ buffer, split electrodes "
    rf"(gap$_{{bot}}$={GAP_BOT}, gap$_{{top}}$={GAP_TOP} $\mu$m) | "
    rf"$h_{{core}}$={h_core}, $h_{{skin}}$={h_skin}, $h_{{buf}}$={h_buf} $\mu$m"
)
plt.tight_layout()
plt.show()
