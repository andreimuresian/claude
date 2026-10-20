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


_case = f"{'inside' if TEE else 'outside'} of tee, {'over-etched ' + format(OE * 1e3, '.0f') + ' nm' if OE > 0 else 'standard'}"
fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(13, 7.4), gridspec_kw=dict(height_ratios=[1, 1.2]))
_draw_materials(ax_a)
ax_a.legend(handles=[mpatches.Patch(color=MATERIALS[m]["color"], label=f"{m}: {MATERIALS[m]['desc']}")
                     for m in _mkeys if m in _mat_shapes], loc="upper left", framealpha=0.95, fontsize=8)
ax_a.set_xlim(X_L, X_R); ax_a.set_ylim(-2.0, 4.0); ax_a.set_aspect("equal")
ax_a.set_title(f"Danube ({_case}), one arm, full domain width | right edge = signal centre (symmetry plane)")
_draw_materials(ax_b)
ax_b.set_xlim(-SLAB_W / 2.0 - 1.5, X_R); ax_b.set_ylim(-1.2, 2.6); ax_b.set_aspect("equal")
ax_b.set_xlabel(r"$x$ ($\mu$m)"); ax_b.set_ylabel(r"$y$ ($\mu$m)")
ax_b.set_title(rf"Zoom | slab top width {SLAB_W:.2f} $\mu$m, gap {GAP:.2f} $\mu$m, $\lambda$ = {wl*1e3:.0f} nm")
plt.tight_layout()
plt.show()

# ---- Cross-section with the mesh ----------------------------------------------
fig, ax = plt.subplots(figsize=(13, 4.5))
_draw_materials(ax)
skfem_mesh.draw(ax=ax, color="black", lw=0.15)
ax.set_xlim(-SLAB_W / 2.0 - 1.5, X_R); ax.set_ylim(-1.2, 2.6); ax.set_aspect("equal")
ax.set_title(f"Danube ({_case}) mesh | {skfem_mesh.nelements} triangles")
plt.tight_layout()
plt.show()
