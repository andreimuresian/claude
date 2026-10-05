# %% [0] Geometry, Mesh & Material Configuration  --  CORDOBA (NON-LIFTED) ELECTRODES, ETCHED LN SLAB
#
#   Legacy Cordoba cross-section: two flat gold electrodes (EL_W = 30 um wide,
#   MTX = 2 um thick) sitting directly on the LN slab, gap GAP between them.
#   New: the LN slab can be fully etched outside a width SLAB_W centred on the
#   rib.  Wherever the slab is etched the gold fills the etched region down to
#   the BOX (the gold top stays at SLAB_H + MTX), and air fills it in the gap.
#
#   Regimes, set by the slab edge x_s = SLAB_W / 2:
#     x_s <  GAP/2                   slab ends in the air gap (narrower than the gap)
#     GAP/2 < x_s < GAP/2 + EL_W     slab ends INSIDE the gold (wrapped by gold)
#     x_s >= DEV_W/2                 no etch: the slab spans the whole domain (original design)
#
#   Materials, mesher fix, gold skin and corner refinement are identical to the
#   etched Lisbon-lifted cell (cell0_etched.py), so the two designs differ only in
#   the electrode shape above the slab.
import warnings
from collections import OrderedDict
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from shapely.affinity import scale as _scale
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union
from skfem import MeshTri
from femwell.mesh import mesh_from_OrderedDict

warnings.filterwarnings("ignore")

# ------------------------------------------------------------------------------
# femwell bug fix.  mesh_from_OrderedDict() tries to switch off gmsh's
# "extend mesh size from boundary" with `gmsh.model.mesh.MeshSizeExtendFromBoundary = 0`,
# which only sets a Python attribute: the gmsh option is never changed.  This
# wrapper applies the options femwell intended, so the mesh follows `resolutions`.
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
wl = 1.575          # um
wl_m = wl * 1e-6
k0 = 2.0 * np.pi / wl               # 1/um
k0_m = k0 * 1e6                     # 1/m
L_cm = 1.0          # cm
V_bias = 1.0        # V
r33 = 30.8e-12      # m/V
n_guess = 1.8755
num_modes_search = 8

# Geometry Dimensions (um), y = 0 at the BOX / LN interface
BOX_H = 4.7
TECN = 0.550
WG_H = 0.275
SLAB_H = TECN - WG_H                # 0.275 um LN slab
WG_TOP = 1.0
ALPHA = 60.0
GAP = 4.2
EL_W = 30.0         # 30 um physical width to dissipate lateral SPP mode
MTX = 2.0           # electrode thickness above the slab
MARGIN = 5.0        # air/BOX beyond each electrode
CLAD_H = 15.0       # air above the slab
CAP_W = 2.0
CAP_H = 1.40
SLAB_W = 10.0       # total width of the LN slab left after the full etch;
                    # >= DEV_W (e.g. 1e3) = no etch, the original Cordoba design

basetta = WG_H / np.tan(np.deg2rad(ALPHA))
WG_BOTTOM = WG_TOP + 2.0 * basetta
X_EL_OUT = GAP / 2.0 + EL_W                 # 32.1 um outer edge of the electrode
DEV_W = 2.0 * X_EL_OUT + 2.0 * MARGIN       # 74.2 um (= 2 EL_W + GAP + 10)
ETCHED = SLAB_W < DEV_W
SLAB_EXT = (min(SLAB_W, DEV_W) - GAP) / 2.0     # slab edge beyond the gap edge (per side)
assert CAP_W > WG_BOTTOM and GAP > CAP_W and SLAB_W > CAP_W, "rib / cap / gap inconsistent"
assert not ETCHED or SLAB_W / 2.0 < X_EL_OUT - 1.0, "etched slab must end in the gap or inside the gold"

# ---- Material dispersion: every optical constant is computed at `wl` ---------
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


# Gold: Johnson & Christy, PRB 6, 4370 (1972), (lambda um, n, k); eps = (n - i k)^2
# interpolated linearly in photon energy.  exp(+jwt): Im(eps) < 0 is loss.
_AU_JC = np.array([
    (0.617, 0.21, 3.272), (0.659, 0.14, 3.697), (0.705, 0.13, 4.103),
    (0.756, 0.14, 4.542), (0.821, 0.16, 5.083), (0.892, 0.17, 5.663),
    (0.984, 0.22, 6.350), (1.088, 0.27, 7.150), (1.216, 0.35, 8.145),
    (1.393, 0.43, 9.519), (1.610, 0.56, 11.210), (1.937, 0.92, 13.780)])


def eps_Au_JC(lam):
    lam_t, n_t, k_t = _AU_JC.T
    assert lam_t.min() <= lam <= lam_t.max(), "wavelength outside the J&C table"
    E_t = 1.239842 / lam_t
    eps_t = (n_t - 1j * k_t) ** 2
    E = 1.239842 / lam
    return complex(np.interp(E, E_t[::-1], eps_t.real[::-1]),
                   np.interp(E, E_t[::-1], eps_t.imag[::-1]))


ne, no = n_LN(wl)
n_sio2 = n_SiO2(wl)
eps_au = eps_Au_JC(wl)
print(f"[materials @ {wl*1e3:.0f} nm] LN ne={ne:.6f} no={no:.6f} | "
      f"SiO2 n={n_sio2:.6f} | Au eps={eps_au.real:.2f}{eps_au.imag:+.2f}j")

# ---- Mesh scales (same as the etched lifted cell) -----------------------------
h_core = 0.040
h_skin = 0.012                      # gold on LN: the SPP decays into Au in ~22 nm
SKIN_T = 0.070                      # gold shell resolving the ~23 nm optical skin depth
BOT_SKIN_L = 0.5                    # shell on gold-on-BOX beyond an etched slab end
OUTER_WALL_SKIN_H = 0.5
CORNER_R = 0.050                    # corner patch half-size (um): metal/LN corners
h_corner = 0.006                    # mesh size inside the corner patches (um)
X_FINE_MIN = 8.0                    # fine slab mesh reaches at least |x| = 8 um

MATERIALS = {
    "LN":     {"color": "#8b95a1", "eps_dc": (28.0, 44.0), "eps_opt": (ne**2, no**2, no**2), "desc": "LN Core / Slab"},
    "SiO2":   {"color": "#5aa9f0", "eps_dc": (3.75, 3.75), "eps_opt": (n_sio2**2, n_sio2**2, n_sio2**2), "desc": "SiO2 Cap / Underclad"},
    "air":    {"color": "#ffffff", "eps_dc": (1.00, 1.00), "eps_opt": (1.00, 1.00, 1.00), "desc": "Air Cladding"},
    "Au_sig": {"color": "#f6c453", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Signal Electrode (+1V)"},
    "Au_gnd": {"color": "#e5a92e", "eps_dc": (1.00, 1.00), "eps_opt": (eps_au, eps_au, eps_au), "desc": "Ground Electrode (0V)"},
}

PREFIX_TO_MAT = [
    ("core", "LN"), ("cap", "SiO2"), ("slab", "LN"), ("box", "SiO2"),
    ("clad", "air"), ("elR", "Au_sig"), ("elL", "Au_gnd"),
]

def material_of(region_name):
    base = region_name.split("___")[0]
    for prefix, mat in PREFIX_TO_MAT:
        if base.startswith(prefix):
            return mat
    raise KeyError(f"Unknown material for region: {region_name}")

def mirror(p):
    return _scale(p, xfact=-1.0, yfact=1.0, origin=(0, 0))

def _areal(g, tol=1e-10):
    """Keep only the polygonal part of a shapely result (drops touching lines/points)."""
    if g.is_empty:
        return Polygon()
    if isinstance(g, Polygon):
        return g if g.area > tol else Polygon()
    parts = [p for p in getattr(g, "geoms", []) if isinstance(p, (Polygon, MultiPolygon))]
    parts = [q for p in parts for q in (p.geoms if isinstance(p, MultiPolygon) else [p])
             if q.area > tol]
    if not parts:
        return Polygon()
    return parts[0] if len(parts) == 1 else MultiPolygon(parts)

# ============================================================
# 2. GEOMETRY GENERATOR
# ============================================================
def build_polygons():
    xg = GAP / 2.0                                  # electrode inner edge
    x_out = X_EL_OUT                                # electrode outer edge
    x_dev_max = DEV_W / 2.0
    xs = min(SLAB_W / 2.0, x_dev_max)               # slab edge
    x_fine = max(X_FINE_MIN, min(xs, x_out) + 1.0)  # end of the finely meshed slab
    x_near = min(max(x_fine, min(xs, x_out)) + 15.0, x_dev_max - 2.0)

    y_slab_top = SLAB_H
    y_el_top = y_slab_top + MTX                     # 2.275
    y_cap_top = y_slab_top + CAP_H                  # 1.675
    y_clad_top = y_slab_top + CLAD_H
    y_fine_top = y_slab_top + 0.6                   # above this the mode is < -25 dB

    r_c = CORNER_R                                  # corner patches never touch
    if ETCHED:
        for _a in (xg, x_out):
            if abs(xs - _a) > 1e-9:
                r_c = min(r_c, abs(xs - _a) / 2.5)
    assert r_c >= 0.01, f"slab edge {xs:.3f} um within 20 nm of a gold edge: not meshable"

    # ---- 1. LN: rib core and the (etched) slab ------------------------------
    core_poly = Polygon([
        (-WG_BOTTOM / 2.0, y_slab_top), (-WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_TOP / 2.0, y_slab_top + WG_H), (WG_BOTTOM / 2.0, y_slab_top)])
    slab = box(-xs, 0.0, xs, y_slab_top)

    # ---- 2. SiO2 cap (2.0 x 1.4 um, on the slab) -----------------------------
    cap_poly = box(-CAP_W / 2.0, y_slab_top, CAP_W / 2.0, y_fine_top).difference(core_poly)
    cap_up = box(-CAP_W / 2.0, y_fine_top, CAP_W / 2.0, y_cap_top)

    # ---- 3. Electrode (right = signal): flat gold block, filling the etched
    #         slab region down to the BOX
    el_r = box(xg, 0.0, x_out, y_el_top).difference(slab)
    assert el_r.geom_type == "Polygon", "electrode is not a single body"

    # ---- 4. BOX (fine only in the top 0.5 um near the rib) -------------------
    box_near = box(-(xg + 1.0), -0.5, xg + 1.0, 0.0)
    box_mid = box(-(xg + 1.0), -1.5, xg + 1.0, -0.5)
    box_far = box(-x_dev_max, -BOX_H, x_dev_max, 0.0).difference(
        box(-(xg + 1.0), -1.5, xg + 1.0, 0.0))

    # ---- 5. Air: everything left above the BOX -------------------------------
    solids = unary_union([core_poly, slab, cap_poly, cap_up, el_r, mirror(el_r)])
    clad_all = box(-x_dev_max, 0.0, x_dev_max, y_clad_top).difference(solids)
    clad_gap = _areal(clad_all.intersection(box(-xg, 0.0, xg, y_fine_top)))
    clad_gap_up = _areal(clad_all.intersection(box(-xg, y_fine_top, xg, y_cap_top + 0.6)))
    clad_far = _areal(clad_all.difference(box(-xg, 0.0, xg, y_cap_top + 0.6)))

    base = OrderedDict()
    base["core"] = core_poly
    base["cap"] = cap_poly
    base["cap_up"] = cap_up
    base["elR_bulk"] = el_r
    base["elL_bulk"] = mirror(el_r)
    base["slab_fine"] = _areal(slab.intersection(box(-x_fine, 0.0, x_fine, y_slab_top)))
    base["slab_mid"] = _areal(slab.intersection(box(-x_near, 0.0, x_near, y_slab_top))
                              .difference(box(-x_fine, 0.0, x_fine, y_slab_top)))
    base["slab_far"] = _areal(slab.difference(box(-x_near, 0.0, x_near, y_slab_top)))
    base["box_near"] = box_near
    base["box_mid"] = box_mid
    base["box_far"] = box_far
    base["clad_gap"] = clad_gap
    base["clad_gap_up"] = clad_gap_up
    base["clad_far"] = clad_far

    # ---- 6. Refinement zones -------------------------------------------------
    # 6a. corner patches where gold touches the LN slab
    pts = []
    if xs > xg + 1e-9:
        pts.append((xg, y_slab_top))                 # inner corner: gold / LN / air
    else:
        pts.append((xg, 0.0))                        # gold foot on the BOX (slab_w <= gap)
    if xg + 1e-9 < xs < x_out - 1e-9:
        pts += [(xs, y_slab_top), (xs, 0.0)]         # slab end wrapped by gold
    elif xs >= x_out:
        pts.append((x_out, y_slab_top))              # outer corner: gold / LN / air (no etch)
    patches_r = unary_union([box(px - r_c, py - r_c, px + r_c, py + r_c) for px, py in pts])
    patches = unary_union([patches_r, mirror(patches_r)])

    # 6b. gold skin: within SKIN_T of the LN slab, the inner wall (full height),
    #     the foot of the outer wall, and BOT_SKIN_L of gold-on-BOX beyond an
    #     etched slab end.
    x_e = max(xs, xg)
    skin_zone_r = unary_union([
        slab.buffer(SKIN_T, join_style=2),
        box(xg, 0.0, xg + SKIN_T, y_el_top),
        box(x_out - SKIN_T, 0.0, x_out, y_slab_top + OUTER_WALL_SKIN_H),
        box(x_e, 0.0, min(x_e + BOT_SKIN_L, x_out), SKIN_T) if x_e < x_out else Polygon(),
    ])
    skin_zone = unary_union([skin_zone_r, mirror(skin_zone_r)])

    polys = OrderedDict()
    for name, reg in base.items():
        if reg.is_empty:
            continue
        pc = _areal(reg.intersection(patches))
        if not pc.is_empty:
            polys[name + "_corner"] = pc
        reg = _areal(reg.difference(patches))
        if name.startswith("el"):
            sk = _areal(reg.intersection(skin_zone))
            polys[name.replace("bulk", "skin")] = sk
            reg = _areal(reg.difference(skin_zone))
        if not reg.is_empty:
            polys[name] = reg

    return polys, y_clad_top

# ============================================================
# 3. MESH GENERATION & RESOLUTION SETUP
# ============================================================
polygons, Y_TOP = build_polygons()

_base_res = {
    "core":        (h_core, 0.30),
    "cap":         (0.035, 0.30),
    "cap_up":      (0.080, 0.30),
    "clad_gap":    (0.040, 0.30),
    "clad_gap_up": (0.100, 0.30),
    "slab_fine":   (0.025, 0.30),
    "slab_mid":    (0.110, 0.40),
    "slab_far":    (0.150, 0.50),
    "box_near":    (0.040, 0.30),
    "box_mid":     (0.100, 0.30),
    "box_far":     (0.800, 1.00),
    "elR_bulk":    (0.800, 0.50),
    "elL_bulk":    (0.800, 0.50),
    "elR_skin":    (h_skin, 0.20),
    "elL_skin":    (h_skin, 0.20),
    "clad_far":    (0.800, 1.00),
}
resolutions = {}
for _k in polygons:
    if _k.endswith("_corner"):
        resolutions[_k] = {"resolution": h_corner, "distance": 0.10}
    else:
        _r, _d = _base_res[_k]
        resolutions[_k] = {"resolution": _r, "distance": _d}

# ---- Validity / consistency assertions ---------------------------------------
_names = list(polygons)
for _n, _p in polygons.items():
    assert _p.is_valid and not _p.is_empty and _p.area > 1e-12, f"degenerate region {_n}"
for _i in range(len(_names)):
    for _j in range(_i + 1, len(_names)):
        _ov = polygons[_names[_i]].intersection(polygons[_names[_j]]).area
        assert _ov < 1e-10, f"overlap {_names[_i]} & {_names[_j]}: {_ov:.2e}"
_tot = sum(p.area for p in polygons.values())
assert abs(_tot - DEV_W * (BOX_H + Y_TOP)) < 1e-8, "tiling gap"

_regime = ("no etch: slab across the whole domain (original Cordoba)" if not ETCHED else
           "slab ends in the air gap" if SLAB_EXT < -1e-9 else
           "slab ends at the gold inner edge" if abs(SLAB_EXT) < 1e-9 else
           "slab ends inside the gold")
print(f"[geometry OK] {len(polygons)} regions tile exactly")
print(f"              SLAB_W {min(SLAB_W, DEV_W):.2f} um (edge {SLAB_EXT:+.2f} um from the gap edge): {_regime}")
print(f"              gap {GAP:.2f} um | flat electrodes {EL_W:.0f} x {MTX:.1f} um, gold out to x = {X_EL_OUT:.2f} um")

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

print("=" * 84)
print(f"{'CANONICAL MATERIAL':<28} | {'DC EPS (x, y)':<16} | {'OPTICAL EPS (xx, yy, zz)':<28}")
print("-" * 84)
for key, data in MATERIALS.items():
    dc_s = f"({data['eps_dc'][0]:.1f}, {data['eps_dc'][1]:.1f})"
    opt_val = data['eps_opt'][0]
    opt_s = f"({opt_val.real:.1f}{opt_val.imag:+.1f}j)" if np.iscomplex(opt_val) else f"({opt_val.real:.3f})"
    print(f"{data['desc']:<28} | {dc_s:<16} | {opt_s:<28}")
print("=" * 84)

# ---- Cross-section WITHOUT the mesh (material the solver assigns to each triangle)
from matplotlib.colors import ListedColormap

_mkeys = list(MATERIALS)
_midx = np.array([_mkeys.index(m) for m in mat_of_el], dtype=float)
_mcmap = ListedColormap([MATERIALS[m]["color"] for m in _mkeys])
_by_mat = {}
for _n, _p in polygons.items():
    _by_mat.setdefault(material_of(_n), []).append(_p)
_mat_shapes = {m: unary_union(v) for m, v in _by_mat.items()}


def _draw_materials(ax):
    ax.tripcolor(skfem_mesh.p[0], skfem_mesh.p[1], skfem_mesh.t.T, facecolors=_midx,
                 cmap=_mcmap, vmin=-0.5, vmax=len(_mkeys) - 0.5,
                 edgecolors="face", linewidth=0.0, antialiased=False)
    for _shape in _mat_shapes.values():
        for _part in (_shape.geoms if hasattr(_shape, "geoms") else [_shape]):
            for _ring in [_part.exterior, *_part.interiors]:
                _xy = np.asarray(_ring.coords)
                ax.plot(_xy[:, 0], _xy[:, 1], color="k", lw=0.6)


def _dim(ax, x0, x1, y, label, color="k", above=True):
    ax.annotate("", (x0, y), (x1, y),
                arrowprops=dict(arrowstyle="<->", color=color, lw=1.0, shrinkA=0, shrinkB=0))
    ax.text(0.5 * (x0 + x1), y + (0.08 if above else -0.08), label, color=color, fontsize=8.5,
            ha="center", va="bottom" if above else "top",
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.6))


_xs, _xg = min(SLAB_W, DEV_W) / 2.0, GAP / 2.0
fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(13, 7.4), gridspec_kw=dict(height_ratios=[1.2, 1]))
_draw_materials(ax_a)
_xl = max(12.0, min(_xs, X_EL_OUT) + 2.0)
if ETCHED:
    _dim(ax_a, -_xs, _xs, -0.45, rf"slab_w = {SLAB_W:.2f} $\mu$m", color="#34495e", above=False)
_dim(ax_a, -_xg, _xg, SLAB_H + MTX - 0.35, rf"gap = {GAP:.2f} $\mu$m")
ax_a.legend(handles=[mpatches.Patch(color=MATERIALS[m]["color"], label=f"{m}: {MATERIALS[m]['desc']}")
                     for m in _mkeys if m in _mat_shapes],
            loc="upper right", framealpha=0.95, fontsize=8)
ax_a.set_xlim(-_xl, _xl); ax_a.set_ylim(-1.1, 4.2); ax_a.set_aspect("equal")
ax_a.set_xlabel(r"$x$ ($\mu$m)"); ax_a.set_ylabel(r"$y$ ($\mu$m)")
ax_a.set_title(rf"Cordoba electrodes, cross-section as simulated (no mesh) | {_regime}")

_draw_materials(ax_b)
_zc = _xs if ETCHED else _xg
_zx0, _zx1 = _zc - 1.2, _zc + 1.2
for _xv, _lab, _c in [(_xg, "gold inner edge", "#b9770e"), (_xs, "slab end", "#c0392b")]:
    if _zx0 < _xv < _zx1 and (ETCHED or _xv == _xg):
        ax_b.axvline(_xv, color=_c, ls="--", lw=1.0)
        ax_b.text(_xv + 0.02, 0.86, _lab, color=_c, fontsize=8.5, rotation=90, va="top")
ax_b.axhline(0.0, color="#555", lw=0.6, ls=":")
ax_b.text(_zx0 + 0.03, -0.05, "BOX top (y = 0)", fontsize=8, va="top", color="#555")
ax_b.set_xlim(_zx0, _zx1); ax_b.set_ylim(-0.45, 0.9); ax_b.set_aspect("equal")
ax_b.set_xlabel(r"$x$ ($\mu$m)"); ax_b.set_ylabel(r"$y$ ($\mu$m)")
ax_b.set_title(rf"Zoom at x = {_zc:.2f} $\mu$m: LN slab {SLAB_H*1e3:.0f} nm on the BOX")
plt.tight_layout()
plt.show()

# ---- Cross-section with the mesh ----------------------------------------------
fig, ax = plt.subplots(figsize=(13, 4.5))
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
ax.set_title(rf"Cordoba electrodes, etched slab | slab_w = {min(SLAB_W, DEV_W):.2f} $\mu$m | "
             rf"gap {GAP:.1f} $\mu$m | {skfem_mesh.nelements} triangles")
ax.set_xlim([-_xl, _xl])
ax.set_ylim([-1.0, 3.5])
ax.set_xlabel(r"$x$ ($\mu$m)")
ax.set_ylabel(r"$y$ ($\mu$m)")
ax.set_aspect("equal")
plt.tight_layout()
plt.show()
