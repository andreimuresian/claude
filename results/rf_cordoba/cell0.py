# %% [0] Geometry, Mesh & Material Configuration  --  RF cross-section, Cordoba + SiO2 buffer + ALD Al2O3
#
#   Full two-arm GSG (push-pull) Cordoba cross-section at 60 GHz: centred signal, a rib with its
#   SiO2 cap in each gap, both grounds, unetched LN slab across the domain.
#   Optional layers, drawn exactly as in the optical (Vpi*L / IL / group-index) models:
#     BUFFER_H : SiO2 buffer on the whole slab, under the gold and across the gaps (merges with the
#                caps); the gold sits on it, GAP is measured there, CAP_H counts from its top.
#     T_ALD    : conformal ALD Al2O3 on every surface exposed to air after the electrodes
#                (electrode tops / walls, slab or buffer in the gaps and outside, cap sides / top).
import time
import warnings
from collections import OrderedDict

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from shapely.affinity import scale as _scale
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union
from skfem import MeshTri
from femwell.mesh import mesh_from_OrderedDict

warnings.filterwarnings("ignore")

# femwell bug fix (as in the optical notebooks): mesh_from_OrderedDict() never really switches
# off gmsh's "extend mesh size from boundary", so every fine surface size (e.g. the 20 nm ALD)
# propagates deep into the neighbouring regions -- here, into the PEC electrodes.
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
# 1. PARAMETER BLOCK  (Cordoba)
# ============================================================
f0        = 60.0e9      # Hz    mode-analysis frequency
device_l  = 16.5e-3     # m     line length used for the S21 report

auc_w     = 35.0        # um    W_S  central signal electrode width
gap       = 4.15        # um    GAP  signal-to-ground gap (on the buffer when BUFFER_H > 0)
au_h      = 2.0         # um    MTX  electrode thickness
aul_w     = 49.85       # um    lateral ground width
cap_w     = 2.0         # um    SiO2 cap width
cap_h     = 1.40        # um    SiO2 cap height (from the buffer top)

tfln      = 0.540       # um    total thin-film LN thickness
wg_h      = 0.270       # um    rib height (etch depth)
slab_h    = tfln - wg_h # um    un-etched slab
wg_top    = 1.0         # um    rib top width
theta     = 60.0        # deg   rib sidewall angle

box_h     = 4.7         # um    buried SiO2
si_h      = 550.0       # um    silicon substrate (real thickness)
air_h     = 550.0       # um    air above the slab
lat_pad   = 200.0       # um    lateral padding beyond each outer ground edge

BUFFER_H  = 0.0         # um    SiO2 buffer (0 = none; 0.200 = buffered design)
T_ALD     = 0.0         # um    ALD Al2O3 thickness (0 = none; 0.040 = nominal)
EPS_ALD   = 9.8         #       ALD Al2O3 relative permittivity at RF (same value as the Vpi*L studies)
TAN_ALD   = 0.0         #       ALD Al2O3 loss tangent at f0 (0 = lossless; see the loss assessment)

basetta   = wg_h / np.tan(np.deg2rad(theta))
wg_bottom = wg_top + 2.0 * basetta

r9     = lambda v: round(float(v), 9)
y_b    = r9(slab_h + BUFFER_H)  # bottom of the gold (= buffer top)
x_sig  = auc_w / 2.0            # signal spans [-x_sig, +x_sig]
x_gi   = x_sig + gap            # ground inner edge
x_go   = x_gi + aul_w           # ground outer edge
x_dom  = x_go + lat_pad         # domain half width
x_wg   = x_sig + gap / 2.0      # rib centre (mid-gap)
y_el   = r9(y_b + au_h)         # electrode top
y_rib  = slab_h + wg_h          # rib top
y_cap  = r9(y_b + cap_h)        # cap top

# ============================================================
# 2. MATERIALS  (60 GHz)
# ============================================================
C0   = 299792458.0
EPS0 = 8.8541878128e-12
MU0  = 4.0e-7 * np.pi
ETA0 = np.sqrt(MU0 / EPS0)
DB_PER_NEPER = 20.0 * np.log10(np.e)

SIGMA_AU  = 4.56e7
skin_au   = np.sqrt(2.0 / (2 * np.pi * f0 * MU0 * SIGMA_AU))
Rs_au     = 1.0 / (SIGMA_AU * skin_au)
SIGMA_ALD = 2 * np.pi * f0 * EPS0 * EPS_ALD * TAN_ALD      # S/m equivalent of the loss tangent

MATERIALS = {
    "LN":    {"color": "#2ecc71", "eps_rf": (28.0, 44.0, 44.0), "sigma": 1e-3,  "desc": "LiNbO3 slab + ribs"},
    "SiO2":  {"color": "#00ebfc", "eps_rf": (3.9, 3.9, 3.9),    "sigma": 1e-13, "desc": "SiO2 box + caps + buffer"},
    "Al2O3": {"color": "#f472d0", "eps_rf": (EPS_ALD,) * 3,     "sigma": SIGMA_ALD, "desc": "ALD Al2O3"},
    "Si":    {"color": "#7f8c8d", "eps_rf": (11.7, 11.7, 11.7), "sigma": 1e-12, "desc": "Silicon substrate"},
    "air":   {"color": "#ffffff", "eps_rf": (1.0, 1.0, 1.0),    "sigma": 0.0,   "desc": "Air / vacuum"},
    "Au":    {"color": "#f39c12", "eps_rf": (1.0, 1.0, 1.0),    "sigma": 0.0,   "desc": "Gold electrodes (PEC)"},
}
PREFIX_TO_MAT = [("el_", "Au"), ("rib", "LN"), ("slab", "LN"), ("cap", "SiO2"), ("buf", "SiO2"),
                 ("box", "SiO2"), ("alu", "Al2O3"), ("si", "Si"), ("air", "air")]
METAL_REGIONS = ("el_sig", "el_gr", "el_gl")
SIGNAL_REGION = "el_sig"


def mat_of_region(name):
    base = name.split("__")[-1] if "__" in name else name
    for p, m in PREFIX_TO_MAT:
        if base.startswith(p):
            return m
    raise KeyError(name)


def mirror(p):
    return _scale(p, xfact=-1.0, yfact=1.0, origin=(0, 0))


def _areal(g, tol=1e-10):
    if g.is_empty:
        return Polygon()
    parts = [g] if isinstance(g, Polygon) else [q for q in getattr(g, "geoms", []) if isinstance(q, (Polygon, MultiPolygon))]
    parts = [q for p in parts for q in (p.geoms if isinstance(p, MultiPolygon) else [p]) if q.area > tol]
    return Polygon() if not parts else (parts[0] if len(parts) == 1 else MultiPolygon(parts))


# ============================================================
# 3. MESH CONTROL
# ============================================================
MESH_FACTOR = 0.35     # converged setting (see results/rf_cordoba): 1.0 is ~2 % off in Z0
COLLAR_W    = 4.0      # um, lateral reach of the fine air collar past the gap
COLLAR_H    = 4.0      # um, height of the fine air collar above the electrodes
CORNER_BOX  = 0.25     # um, half-size of the refinement box on each electrode corner
CORNER_RES  = 0.050    # um, mesh size inside those boxes
SKIN_T      = 0.10     # um, thickness of the conductor-surface collar
SKIN_REACH  = 5.0      # um, how far that collar runs along the top / bottom faces
SKIN_RES    = 0.100    # um, mesh size inside the collar
NEAR        = 15.0     # um, reach of the "near" zones past the outer ground edge


def build_polygons():
    def rib(xc):
        return Polygon([(xc - wg_bottom / 2, slab_h), (xc - wg_top / 2, y_rib),
                        (xc + wg_top / 2, y_rib), (xc + wg_bottom / 2, slab_h)])

    rib_r = rib(x_wg); rib_l = mirror(rib_r)
    cap_r = box(x_wg - cap_w / 2, slab_h, x_wg + cap_w / 2, y_cap).difference(rib_r); cap_l = mirror(cap_r)
    el_sig = box(-x_sig, y_b, x_sig, y_el)
    el_gr = box(x_gi, y_b, x_go, y_el); el_gl = mirror(el_gr)
    metals = unary_union([el_sig, el_gr, el_gl])
    buf = Polygon()
    if BUFFER_H > 0:
        buf = _areal(box(-x_dom, slab_h, x_dom, y_b).difference(unary_union([rib_r, rib_l, cap_r, cap_l])))
    solids = unary_union([metals, cap_r, cap_l, rib_r, rib_l, buf])
    slab = box(-x_dom, 0.0, x_dom, slab_h)
    alu = Polygon()
    if T_ALD > 0:
        shell = unary_union([solids, slab]).buffer(T_ALD, join_style=2, mitre_limit=10.0)
        alu = _areal(shell.intersection(box(-x_dom, slab_h, x_dom, slab_h + air_h)).difference(solids))
    air = _areal(box(-x_dom, slab_h, x_dom, slab_h + air_h).difference(unary_union([solids, alu])))

    # material zones (near / far)
    near = box(-x_go - NEAR, -box_h, x_go + NEAR, y_el + NEAR)
    gapz = box(-x_gi - COLLAR_W, slab_h, x_gi + COLLAR_W, y_el + COLLAR_H)
    zones = OrderedDict()
    zones["cap_r"], zones["cap_l"], zones["rib_r"], zones["rib_l"] = cap_r, cap_l, rib_r, rib_l
    zones["el_sig"], zones["el_gr"], zones["el_gl"] = el_sig, el_gr, el_gl
    zones["alu_near"] = _areal(alu.intersection(near)); zones["alu_far"] = _areal(alu.difference(near))
    zones["buf_near"] = _areal(buf.intersection(near)); zones["buf_far"] = _areal(buf.difference(near))
    zones["air_gap"] = _areal(air.intersection(gapz))
    zones["air_near"] = _areal(air.intersection(near).difference(gapz))
    zones["air_far"] = _areal(air.difference(near))
    zones["slab_near"] = _areal(slab.intersection(near)); zones["slab_far"] = _areal(slab.difference(near))
    zones["box_near"] = box(-x_go - NEAR, -box_h, x_go + NEAR, 0.0)
    zones["box_far"] = _areal(box(-x_dom, -box_h, x_dom, 0.0).difference(zones["box_near"]))
    zones["si"] = box(-x_dom, -box_h - si_h, x_dom, -box_h)

    # conductor-surface refinement collars (a meshing device): cut into every
    # non-metal zone they cross, so each piece keeps the material of its zone
    corners = [box(xc - CORNER_BOX, yc - CORNER_BOX, xc + CORNER_BOX, yc + CORNER_BOX)
               for xc in (-x_sig, x_sig, -x_gi, x_gi, -x_go, x_go) for yc in (y_b, y_el)]
    corner_ring = unary_union(corners).difference(metals)
    walls = []
    for xa, xb in ((x_sig, x_sig + SKIN_T), (-x_sig - SKIN_T, -x_sig), (x_gi - SKIN_T, x_gi), (-x_gi, -x_gi + SKIN_T)):
        walls.append(box(xa, y_b, xb, y_el))
    for xc in (-x_sig, x_sig, -x_gi, x_gi):
        lo, hi = (xc, xc + SKIN_REACH) if xc > 0 else (xc - SKIN_REACH, xc)
        walls.append(box(lo, y_el, hi, y_el + SKIN_T))
        walls.append(box(lo, y_b - SKIN_T, hi, y_b))
    skin_ring = unary_union(walls).difference(unary_union([metals, corner_ring]))

    polys = OrderedDict()
    for ring_name, ring in (("corner_ring", corner_ring), ("skin_ring", skin_ring)):
        for zn, z in zones.items():
            if zn.startswith("el_") or z.is_empty:
                continue
            piece = _areal(ring.intersection(z))
            if not piece.is_empty:
                polys[f"{ring_name}__{zn}"] = piece
    rings = unary_union([corner_ring, skin_ring])
    for zn, z in zones.items():
        z = z if zn.startswith("el_") else _areal(z.difference(rings))
        if not z.is_empty:
            polys[zn] = z
    import shapely
    polys = OrderedDict((k, v) for k, v in polys.items())
    return polys


BASE_RES = {   # um
    "cap_r": 0.20, "cap_l": 0.20, "rib_r": 0.12, "rib_l": 0.12,
    "air_gap": 0.30, "slab_near": 0.25, "box_near": 2.0,
    "el_sig": 0.80, "el_gr": 0.80, "el_gl": 0.80,
    "air_near": 2.0, "slab_far": 6.0, "box_far": 6.0, "si": 30.0, "air_far": 30.0,
    "buf_near": min(BUFFER_H / 3, 0.10) if BUFFER_H > 0 else 0.1, "buf_far": 1.0,
    "alu_near": min(T_ALD / 2, 0.05) if T_ALD > 0 else 0.05, "alu_far": 1.0,
}
BASE_DIST = {
    "cap_r": 1.0, "cap_l": 1.0, "rib_r": 1.0, "rib_l": 1.0, "air_gap": 3.0, "slab_near": 3.0,
    "box_near": 5.0, "el_sig": 3.0, "el_gr": 3.0, "el_gl": 3.0, "air_near": 10.0, "slab_far": 10.0,
    "box_far": 10.0, "si": 30.0, "air_far": 30.0, "buf_near": 0.5, "buf_far": 2.0, "alu_near": 0.3, "alu_far": 2.0,
}
FIXED = ("corner_ring", "skin_ring", "alu_near", "buf_near")   # not scaled by MESH_FACTOR (geometry-set)


def _res(k):
    if k.startswith("corner_ring"):
        zn = k.split("__")[1]; return min(CORNER_RES, BASE_RES[zn]), 0.6
    if k.startswith("skin_ring"):
        zn = k.split("__")[1]; return min(SKIN_RES, BASE_RES[zn]), 1.0
    f = 1.0 if k.startswith(FIXED) else MESH_FACTOR
    return BASE_RES[k] * f, BASE_DIST[k]


polygons = build_polygons()
resolutions = {k: {"resolution": _res(k)[0], "distance": _res(k)[1]} for k in polygons}

# validity: the regions must tile the domain exactly, without overlaps
_tot = sum(p.area for p in polygons.values())
assert abs(_tot - 2 * x_dom * (box_h + si_h + slab_h + air_h)) < 1e-4 * _tot, "tiling gap"

t_mesh = time.time()
raw_mesh = mesh_from_OrderedDict(polygons, resolutions=resolutions,
                                 default_resolution_min=0.4 * min(CORNER_RES, SKIN_RES, BASE_RES["alu_near"]),
                                 default_resolution_max=35.0)
mesh = MeshTri(raw_mesh.points[:, :2].T, raw_mesh.cells_dict["triangle"].T)
t_mesh = time.time() - t_mesh

tri_subdomains = raw_mesh.cell_data_dict["gmsh:physical"]["triangle"]
name_to_id = {n: (d[0] if hasattr(d, "__getitem__") else d) for n, d in raw_mesh.field_data.items()}
region_of = np.empty(mesh.nelements, dtype=object)
for raw_name, s_id in name_to_id.items():
    base_name = raw_name.split("___")[0]
    if base_name in polygons:
        region_of[tri_subdomains == s_id] = base_name
assert not any(r is None for r in region_of), "untagged elements in the mesh"
mat_of_el = np.array([mat_of_region(r) for r in region_of], dtype=object)

is_metal  = np.isin(region_of.astype(str), METAL_REGIONS)
is_signal = region_of.astype(str) == SIGNAL_REGION

f2t          = mesh.f2t
has_two      = f2t[1] >= 0
on_contour   = has_two & (is_metal[f2t[0]] ^ is_metal[f2t[1]])
metal_side   = np.where(is_metal[f2t[0]], f2t[0], f2t[1])
contour_sig  = on_contour & is_signal[metal_side]
contour_gnd  = on_contour & ~is_signal[metal_side]
contour_all  = on_contour

print("=" * 88)
print(f"{'MATERIAL':<34} | {'eps_rf (xx, yy, zz)':<24} | {'sigma [S/m]':<12}")
print("-" * 88)
for key, d in MATERIALS.items():
    e = d["eps_rf"]
    print(f"{d['desc']:<34} | {f'({e[0]:.1f}, {e[1]:.1f}, {e[2]:.1f})':<24} | {d['sigma']:<12.3g}")
print("=" * 88)
print(f"f0 = {f0/1e9:.1f} GHz | buffer {BUFFER_H*1e3:.0f} nm | ALD {T_ALD*1e3:.0f} nm (eps {EPS_ALD}, tan d {TAN_ALD})")
print(f"domain  {2*x_dom:.1f} x {si_h+box_h+slab_h+air_h:.1f} um   (lateral padding {lat_pad:.0f} um, air {air_h:.0f} um, Si {si_h:.0f} um)")
print(f"mesh    {mesh.nelements} triangles, {mesh.nvertices} nodes, built in {t_mesh:.1f} s")


def contour_groups(mask):
    out = []
    for side in (0, 1):
        other = 1 - side
        fac = np.where(mask & is_metal[f2t[other]] & ~is_metal[f2t[side]])[0]
        if fac.size == 0:
            continue
        p = mesh.p[:, mesh.facets[:, fac]]
        tan = p[:, 1, :] - p[:, 0, :]
        nrm = np.vstack([tan[1], -tan[0]])
        nrm /= np.linalg.norm(nrm, axis=0)
        midpoint = p.mean(axis=1)
        centroid = mesh.p[:, mesh.t[:, f2t[other][fac]]].mean(axis=1)
        nrm *= np.sign(((midpoint - centroid) * nrm).sum(axis=0))
        out.append((fac, side, nrm))
    return out


CONTOUR = {"sig": contour_groups(contour_sig), "gnd": contour_groups(contour_gnd), "all": contour_groups(contour_all)}

# ---- cross-section (materials, from the mesh) ------------------------------
SHOW_MESH = True
from matplotlib.colors import ListedColormap
_mk = list(MATERIALS)
_mi = np.array([_mk.index(m) for m in mat_of_el], dtype=float)
_cm = ListedColormap([MATERIALS[m]["color"] for m in _mk])
fig, axes = plt.subplots(1, 3, figsize=(17, 3.8))
for ax, (xl, yl, ttl) in zip(axes, [((x_sig - 1.5, x_gi + 1.5), (-0.6, y_el + 1.5), "Right gap"),
                                    ((x_gi - 0.5, x_gi + 0.5), (y_b - 0.35, y_b + 0.45), "Ground inner corner (zoom)"),
                                    ((-x_dom, x_dom), (-box_h - 40, 60), "Full domain")]):
    ax.tripcolor(mesh.p[0], mesh.p[1], mesh.t.T, facecolors=_mi, cmap=_cm, vmin=-0.5, vmax=len(_mk) - 0.5)
    if SHOW_MESH and not ttl.startswith("Full"):
        mesh.draw(ax=ax, color="black", lw=0.1)
    ax.set_xlim(xl); ax.set_ylim(yl); ax.set_aspect("equal" if not ttl.startswith("Full") else "auto")
    ax.set_title(ttl); ax.set_xlabel(r"$x$ ($\mu$m)")
axes[0].legend(handles=[mpatches.Patch(color=MATERIALS[m]["color"], label=m) for m in _mk if m in set(mat_of_el)],
               fontsize=7, loc="upper right")
fig.suptitle(f"Cordoba RF cross-section: signal {auc_w}, gap {gap}, grounds {aul_w}, Au {au_h}, LN {tfln} (rib {wg_h}), "
             f"cap {cap_w} x {cap_h}, buffer {BUFFER_H*1e3:.0f} nm, ALD {T_ALD*1e3:.0f} nm", fontsize=10)
plt.tight_layout(); plt.show()
