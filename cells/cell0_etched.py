# %% [0] Geometry, Mesh & Material Configuration  --  LIFTED ELECTRODES, ETCHED LN SLAB
#
#   Same lifted-electrode cross-section as the "Lisbona lifted" design (bottom gap
#   4.2 um, top gap 10 um, 2.9 um overhang + 2.0 um column = 4.9 um lower block,
#   pad lifted on 3.6 um SiO2), but the LN slab is fully etched outside a width
#   SLAB_W centred on the rib.  The etched region (slab height) is filled by
#   whatever sits above it: air in the gap, gold under the lower blocks, SiO2
#   under the lifted pads.  All top surfaces keep their heights.
#
#   Three regimes, set by the slab edge x_s = SLAB_W / 2:
#     x_s <  GAP_BOT/2               slab ends in the air gap (narrower than the gap)
#     GAP_BOT/2 < x_s < x_lift       slab ends INSIDE the gold lower block
#     x_s >= x_lift                  slab runs past the gold / SiO2 interface
#   x_lift = GAP_TOP/2 + COL_W = 7.0 um is the outer edge of the lower block.
import warnings
from collections import OrderedDict
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from shapely.affinity import scale as _scale
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection, box
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

# ---- Vertical Dimensions (um) ------------------------------------------------
BOX_H = 4.7
TECN = 0.550                        # LN film thickness
WG_H = 0.275                        # rib height (etch depth)
SLAB_H = TECN - WG_H                # 0.275 um (LN slab thickness)
EL_H = 2.000                        # electrode thickness (lower block AND lifted pad)
BUFFER_H = 3.600                    # SiO2 under the lifted pad, measured from the slab top
CAP_H = 1.400                       # SiO2 cap on the rib, measured from the slab top
CLAD_ABOVE = 2.000                  # air kept above the top of the electrodes

# ---- Horizontal Dimensions (um) ---------------------------------------------
WG_TOP = 1.0
ALPHA = 60.0
GAP_BOT = 4.2                       # gap between the lower blocks
GAP_TOP = 10.0                      # gap between the columns (x_lift = GAP_TOP/2 + COL_W)
COL_W = 2.0                         # column (riser) width
CAP_W = 2.0                         # SiO2 cap width
EL_W = 30.0                         # total electrode width, from the gap edge outward
MARGIN = 5.0
SLAB_W = 3.2                        # total width of the LN slab left after the full etch
SLAB_RES = 0.0                      # LN left outside slab_w (partial second etch); 0 = full etch
SPACER_W = 0.0                      # SiO2 spacer between the slab end and the gold (0 = none);
                                    # only for a slab ending inside the gold, same height as the slab

basetta = WG_H / np.tan(np.deg2rad(ALPHA))
WG_BOTTOM = WG_TOP + 2.0 * basetta
OVERHANG = (GAP_TOP - GAP_BOT) / 2.0        # 2.9 um: lower block beyond the column
LOW_W = OVERHANG + COL_W                    # 4.9 um: lower-block width
X_LIFT = GAP_TOP / 2.0 + COL_W              # 7.0 um: gold / SiO2 interface
SLAB_EXT = (SLAB_W - GAP_BOT) / 2.0         # slab edge beyond the gap edge (per side)
assert CAP_W > WG_BOTTOM, "cap must be wider than the rib base"
assert GAP_BOT > CAP_W, "cap must fit inside the bottom gap"
assert SLAB_W > CAP_W, "the cap must sit on the slab"
assert 0.0 <= SLAB_RES < SLAB_H and (SLAB_RES == 0.0 or SPACER_W == 0.0), "residual slab: 0 <= t < SLAB_H, no spacer"
assert SPACER_W == 0.0 or GAP_BOT < SLAB_W < GAP_TOP + 2 * COL_W - 2 * SPACER_W, (
    "the SiO2 spacer needs a slab that ends inside the gold")
assert OVERHANG > 0 and EL_W > LOW_W, "inconsistent electrode dimensions"

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


# Gold has no Sellmeier form (free-electron metal).  Johnson & Christy, PRB 6,
# 4370 (1972), (lambda um, n, k); eps = (n - i k)^2 is interpolated linearly in
# photon energy, where it is smooth (Drude-like).  Sign convention exp(+jwt):
# Im(eps) < 0 is loss.
_AU_JC = np.array([
    (0.617, 0.21, 3.272), (0.659, 0.14, 3.697), (0.705, 0.13, 4.103),
    (0.756, 0.14, 4.542), (0.821, 0.16, 5.083), (0.892, 0.17, 5.663),
    (0.984, 0.22, 6.350), (1.088, 0.27, 7.150), (1.216, 0.35, 8.145),
    (1.393, 0.43, 9.519), (1.610, 0.56, 11.210), (1.937, 0.92, 13.780)])


def eps_Au_JC(lam):
    lam_t, n_t, k_t = _AU_JC.T
    assert lam_t.min() <= lam <= lam_t.max(), "wavelength outside the J&C table"
    E_t = 1.239842 / lam_t                      # eV, decreasing
    eps_t = (n_t - 1j * k_t) ** 2
    E = 1.239842 / lam
    return complex(np.interp(E, E_t[::-1], eps_t.real[::-1]),
                   np.interp(E, E_t[::-1], eps_t.imag[::-1]))


ne, no = n_LN(wl)
n_sio2 = n_SiO2(wl)
eps_au = eps_Au_JC(wl)
print(f"[materials @ {wl*1e3:.0f} nm] LN ne={ne:.6f} no={no:.6f} | "
      f"SiO2 n={n_sio2:.6f} | Au eps={eps_au.real:.2f}{eps_au.imag:+.2f}j")

# ---- Mesh scales (same as the converged lifted design) ------------------------
h_core = 0.040
h_skin = 0.012                      # gold on LN: the SPP decays into Au in ~22 nm
SKIN_T = 0.070                      # gold shell resolving the ~23 nm optical skin depth
BOT_SKIN_L = 0.5                    # shell on gold-on-BOX beyond an etched slab end
OUTER_WALL_SKIN_H = 0.5
# Corners where metal meets the LN slab carry a field singularity: every such
# corner gets a small square patch of very fine mesh, split by material.
CORNER_R = 0.050                    # corner patch half-size (um)
h_corner = 0.006                    # mesh size inside the corner patches (um)

MATERIALS = {
    "LN":     {"color": "#8b95a1", "eps_dc": (28.0, 44.0), "eps_opt": (ne**2, no**2, no**2), "desc": "LN Core / Slab"},
    "SiO2":   {"color": "#5aa9f0", "eps_dc": (3.75, 3.75), "eps_opt": (n_sio2**2, n_sio2**2, n_sio2**2), "desc": "SiO2 Cap / Lift / Box"},
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
    xg = GAP_BOT / 2.0                              # 2.10 um  lower-block inner edge
    x_col_in = GAP_TOP / 2.0                        # 5.00 um  column inner edge
    x_col_out = X_LIFT                              # 7.00 um  lower-block outer edge
    xs = SLAB_W / 2.0                               # slab edge
    x_el_outer = xg + EL_W                          # 32.10 um end of the lifted pad
    DEV_W = 2.0 * x_el_outer + 2.0 * MARGIN         # 74.20 um
    x_dev_max = DEV_W / 2.0
    x_near = min(max(x_col_out, xs) + 15.0, x_dev_max - 2.0)
    x_fine = max(x_col_out, xs) + 1.0               # end of the finely meshed slab

    y_slab_top = SLAB_H                             # 0.275 (BOX top at y = 0)
    y_low_top = y_slab_top + EL_H                   # 2.275  top of the lower block
    y_buf_top = y_slab_top + BUFFER_H               # 3.875  pad bottom
    y_el_top = y_buf_top + EL_H                     # 5.875
    y_cap_top = y_slab_top + CAP_H                  # 1.675
    y_clad_top = y_el_top + CLAD_ABOVE              # 7.875
    y_fine_top = y_slab_top + 0.6                   # above this the mode is < -25 dB

    # corners: two patches must not overlap (they may coincide), so the patch
    # shrinks when the slab edge is within 2.5*CORNER_R of a gold edge
    w_sp = SPACER_W
    x_m = xs + w_sp                                 # where the gold starts beyond the slab
    r_c = CORNER_R
    for _p, _a in [(xs, xg), (x_m, x_col_out)] + ([(xs, x_m)] if w_sp > 0 else []):
        if abs(_p - _a) > 1e-9:
            r_c = min(r_c, abs(_p - _a) / 2.5)    # patches never touch
    assert r_c >= 0.01, f"slab edge {xs:.3f} um within 20 nm of a gold edge: not meshable"

    # ---- 1. LN: rib core and the (etched) slab ------------------------------
    core_poly = Polygon([
        (-WG_BOTTOM / 2.0, y_slab_top), (-WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_TOP / 2.0, y_slab_top + WG_H), (WG_BOTTOM / 2.0, y_slab_top)])
    t_r = SLAB_RES                                  # residual LN outside slab_w
    slab = box(-xs, 0.0, xs, y_slab_top)
    if t_r > 0:
        slab = unary_union([slab, box(-x_dev_max, 0.0, x_dev_max, t_r)])

    # ---- 2. SiO2 cap (2.0 x 1.4 um, on the slab) -----------------------------
    cap_poly = box(-CAP_W / 2.0, y_slab_top, CAP_W / 2.0, y_fine_top).difference(core_poly)
    cap_up = box(-CAP_W / 2.0, y_fine_top, CAP_W / 2.0, y_cap_top)

    # ---- 3. Electrode (right = signal): the lower block reaches down to the
    #         BOX wherever the slab has been etched away.
    spacer_r = box(xs, 0.0, x_m, y_slab_top) if w_sp > 0 else Polygon()
    low_r = box(xg, 0.0, x_col_out, y_low_top).difference(slab).difference(spacer_r)
    col_r = box(x_col_in, y_low_top, x_col_out, y_el_top)
    pad_r = box(x_col_out, y_buf_top, x_el_outer, y_el_top)
    el_r = unary_union([low_r, col_r, pad_r])
    assert el_r.geom_type == "Polygon", "electrode blocks do not fuse into one body"

    # ---- 4. SiO2 under the lifted pad, down to the BOX where the slab is gone
    buf_r = box(x_col_out, 0.0, x_dev_max, y_buf_top).difference(slab)
    buf_near_r = _areal(buf_r.intersection(box(x_col_out, 0.0, x_near, y_slab_top + 1.0)))
    buf_far_r = _areal(buf_r.difference(box(x_col_out, 0.0, x_near, y_slab_top + 1.0)))

    # ---- 5. BOX (fine only in the top 0.5 um near the rib) -------------------
    box_near = box(-(xg + 1.0), -0.5, xg + 1.0, 0.0)
    box_mid = box(-(xg + 1.0), -1.5, xg + 1.0, -0.5)
    box_far = box(-x_dev_max, -BOX_H, x_dev_max, 0.0).difference(
        box(-(xg + 1.0), -1.5, xg + 1.0, 0.0))

    # ---- 6. Air: everything left above the BOX -------------------------------
    solids = unary_union([core_poly, slab, cap_poly, cap_up, el_r, mirror(el_r),
                          buf_r, mirror(buf_r), spacer_r, mirror(spacer_r)])
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
    base["buf_near_r"] = buf_near_r
    base["buf_near_l"] = mirror(buf_near_r)
    base["buf_far_r"] = buf_far_r
    base["buf_far_l"] = mirror(buf_far_r)
    if w_sp > 0:
        base["buf_spacer_r"] = spacer_r
        base["buf_spacer_l"] = mirror(spacer_r)
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

    # ---- 7. Refinement zones -------------------------------------------------
    # 7a. corner patches: every corner where gold touches the LN slab, plus the
    #     gold foot in the gap if the slab stops short of the gold.
    pts = []
    if t_r > 0:                                      # partial etch: gold always sits on LN
        if xs < xg - 1e-9:
            pts.append((xg, t_r))                    # gold foot on the residual slab
        else:
            pts.append((xg, y_slab_top))
            if xs < x_col_out - 1e-9:
                pts.append((xs, t_r))                # thickness step under the gold
        if xs < x_col_out - 1e-9:
            pts.append((x_col_out, t_r))             # outer corner on the residual slab
        else:
            pts.append((x_col_out, y_slab_top))
    elif xs > xg - 1e-9:
        pts.append((xg, y_slab_top))                 # inner corner: gold / LN / air
    if t_r == 0 and xs < xg + 1e-9:
        pts.append((xg, 0.0))                        # gold foot on the BOX (slab_w <= gap)
    if t_r > 0:
        pass
    elif xg + 1e-9 < xs < x_col_out - 1e-9 and w_sp > 0:
        pts += [(xs, y_slab_top),                    # slab end under the gold, on the spacer
                (x_m, y_slab_top), (x_m, 0.0)]       # spacer wrapped by gold
    elif xg + 1e-9 < xs < x_col_out - 1e-9:
        pts += [(xs, y_slab_top), (xs, 0.0)]         # slab end wrapped by gold
    elif t_r == 0 and xs >= x_col_out - 1e-9:
        pts.append((x_col_out, y_slab_top))          # outer corner: gold / LN / SiO2
    patches_r = unary_union([box(px - r_c, py - r_c, px + r_c, py + r_c)
                             for px, py in pts])
    patches = unary_union([patches_r, mirror(patches_r)])

    # 7b. gold skin: within SKIN_T of the LN slab, the inner wall (full height),
    #     the foot of the outer wall, and BOT_SKIN_L of gold-on-BOX beyond an
    #     etched slab end.
    x_e = max(x_m, xg)
    skin_zone_r = unary_union([
        unary_union([slab, spacer_r]).buffer(SKIN_T, join_style=2),
        box(xg, 0.0, xg + SKIN_T, y_low_top),
        box(x_col_out - SKIN_T, 0.0, x_col_out, y_slab_top + OUTER_WALL_SKIN_H),
        box(x_e, 0.0, min(x_e + BOT_SKIN_L, x_col_out), SKIN_T) if x_e < x_col_out else Polygon(),
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

    return polys, DEV_W, y_clad_top

# ============================================================
# 3. MESH GENERATION & RESOLUTION SETUP
# ============================================================
polygons, DEV_W, Y_TOP = build_polygons()

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
    "buf_near_r":  (0.150, 0.40),
    "buf_near_l":  (0.150, 0.40),
    "buf_far_r":   (0.800, 1.00),
    "buf_far_l":   (0.800, 1.00),
    "buf_spacer_r": (0.020, 0.20),
    "buf_spacer_l": (0.020, 0.20),
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

_regime = ("slab ends in the air gap" if SLAB_EXT < -1e-9 else
           "slab ends at the gold inner edge" if abs(SLAB_EXT) < 1e-9 else
           "slab ends inside the gold" if SLAB_W / 2 < X_LIFT - 1e-9 else
           "slab ends at the gold/SiO2 interface" if abs(SLAB_W / 2 - X_LIFT) < 1e-9 else
           "slab runs past the gold/SiO2 interface")
print(f"[geometry OK] {len(polygons)} regions tile exactly")
print(f"              SLAB_W {SLAB_W:.2f} um (edge {SLAB_EXT:+.2f} um from the gap edge): {_regime}"
      + (f" | SiO2 spacer {SPACER_W*1e3:.0f} nm before the gold" if SPACER_W > 0 else "")
      + (f" | {SLAB_RES*1e3:.0f} nm LN left outside slab_w" if SLAB_RES > 0 else ""))
print(f"              gaps: bottom {GAP_BOT:.2f} um / top {GAP_TOP:.2f} um | "
      f"lower block {LOW_W:.2f} um | gold/SiO2 interface at x = {X_LIFT:.2f} um")

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

# ---- Cross-section WITHOUT the mesh ------------------------------------------
# Every triangle is filled with the colour of the material the SOLVER assigns to
# it (mat_of_el), so this is what is simulated, not just what was drawn.  Thin
# black lines are the material boundaries.
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


_xs, _xg, _yst = SLAB_W / 2.0, GAP_BOT / 2.0, SLAB_H
fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(13, 8.6), gridspec_kw=dict(height_ratios=[1.45, 1]))
_draw_materials(ax_a)
_xl = max(12.0, _xs + 2.0)
_dim(ax_a, -_xs, _xs, -0.45, rf"slab_w = {SLAB_W:.2f} $\mu$m", color="#34495e", above=False)
_dim(ax_a, -_xg, _xg, _yst + EL_H - 0.35, rf"gap = {GAP_BOT:.2f} $\mu$m")
_dim(ax_a, -GAP_TOP / 2.0, GAP_TOP / 2.0, _yst + BUFFER_H + 0.6, rf"top gap = {GAP_TOP:.1f} $\mu$m")
_dim(ax_a, _xg, X_LIFT, _yst + EL_H + 0.35, rf"lower block {LOW_W:.1f} $\mu$m")
ax_a.annotate(rf"gold / SiO$_2$ interface, x_lift = {X_LIFT:.1f} $\mu$m", (X_LIFT, _yst / 2),
              (X_LIFT + 0.6, -0.85), fontsize=8.5, arrowprops=dict(arrowstyle="->", lw=0.8))
ax_a.legend(handles=[mpatches.Patch(color=MATERIALS[m]["color"], label=f"{m}: {MATERIALS[m]['desc']}")
                     for m in _mkeys if m in _mat_shapes],
            loc="upper right", framealpha=0.95, fontsize=8)
ax_a.set_xlim(-_xl, _xl); ax_a.set_ylim(-1.1, 6.3); ax_a.set_aspect("equal")
ax_a.set_xlabel(r"$x$ ($\mu$m)"); ax_a.set_ylabel(r"$y$ ($\mu$m)")
ax_a.set_title(rf"Cross-section as simulated (no mesh) | slab_w = {SLAB_W:.2f} $\mu$m: {_regime}")

# zoom on the right-hand slab end: what surrounds the end of the LN slab
_draw_materials(ax_b)
_zx0, _zx1 = _xs - 1.2, _xs + 1.2
for _xv, _lab, _c in [(_xg, "gold inner edge", "#b9770e"), (X_LIFT, "gold / SiO$_2$ interface", "#1f618d"),
                      (_xs, "slab end", "#c0392b")]:
    if _zx0 < _xv < _zx1:
        ax_b.axvline(_xv, color=_c, ls="--", lw=1.0)
        ax_b.text(_xv + 0.02, 0.86, _lab, color=_c, fontsize=8.5, rotation=90, va="top")
ax_b.axhline(0.0, color="#555", lw=0.6, ls=":")
ax_b.text(_zx0 + 0.03, -0.05, "BOX top (y = 0)", fontsize=8, va="top", color="#555")
ax_b.set_xlim(_zx0, _zx1); ax_b.set_ylim(-0.45, 0.9); ax_b.set_aspect("equal")
ax_b.set_xlabel(r"$x$ ($\mu$m)"); ax_b.set_ylabel(r"$y$ ($\mu$m)")
ax_b.set_title(rf"Zoom on the slab end (x = {_xs:.2f} $\mu$m): LN slab {SLAB_H*1e3:.0f} nm on the BOX")
plt.tight_layout()
plt.show()

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
ax.set_title(rf"Lifted electrodes, etched slab | slab_w = {SLAB_W:.2f} $\mu$m | "
             rf"gaps {GAP_BOT:.1f} / {GAP_TOP:.0f} $\mu$m | {skfem_mesh.nelements} triangles")
ax.set_xlim([-max(12.0, SLAB_W / 2 + 2), max(12.0, SLAB_W / 2 + 2)])
ax.set_ylim([-1.0, 6.5])
ax.set_xlabel(r"$x$ ($\mu$m)")
ax.set_ylabel(r"$y$ ($\mu$m)")
ax.set_aspect("equal")
plt.tight_layout()
plt.show()
