# %% [7] Field components in dB: whole section + zoom on the slab under the gold
# Same field as cell [6] (`_comp`: Ex, Ey, Ez phase-referenced to Ex, normalised to max|Ex|).
# Here we plot |E_i|^2 in dB relative to max|Ex|^2 (a log scale of the INTENSITY of each
# component), sampled finely inside every mesh triangle (no averaging onto nodes), so that
# jumps at interfaces stay sharp and the tails are not smeared or tiled.
#   - whole section : rib mode + evanescent tails + standing wave under the gold, 3 components
#   - zoom          : the slab between the electrode inner edge and the slab end
#   - lateral cuts  : |E_i|^2 (dB) along x at three heights in the slab, 3 components
import matplotlib.tri as mtri

# Plot-only refinement: the FEM field varies smoothly INSIDE each triangle (N1 for Ex, Ey,
# P1 for Ez). Instead of one averaged value per triangle, sample it at a lattice of points
# inside every triangle (N_SUB x N_SUB sub-triangles per element). Vertices are NOT shared
# between elements, so jumps at material interfaces stay sharp. The mesh and the solution
# are unchanged.
from skfem import Basis
N_SUB = 5
_ij = [(i, j) for j in range(N_SUB + 1) for i in range(N_SUB + 1 - j)]
_Xref = np.array([[i / N_SUB for i, j in _ij], [j / N_SUB for i, j in _ij]])
_idx = {p: n for n, p in enumerate(_ij)}
_loc = []
for j in range(N_SUB):
    for i in range(N_SUB - j):
        _loc.append((_idx[(i, j)], _idx[(i + 1, j)], _idx[(i, j + 1)]))
        if i + j < N_SUB - 1:
            _loc.append((_idx[(i + 1, j)], _idx[(i + 1, j + 1)], _idx[(i, j + 1)]))
_loc = np.array(_loc)
_bs = Basis(fund_mode.basis.mesh, fund_mode.basis.elem,
            quadrature=(_Xref, np.full(_Xref.shape[1], 1.0 / _Xref.shape[1])))
_Es = _bs.interpolate(fund_mode.E)
_sub = {"Ex": _v(_Es[0])[0], "Ey": _v(_Es[0])[1], "Ez": _v(_Es[1])}          # (n_el, n_pts)
_sub = {k: v * _ph / _A for k, v in _sub.items()}                              # same reference as cell [6]
_xg = _bs.mapping.F(_Xref)                                                      # (2, n_el, n_pts)
_ne, _npt = _sub["Ex"].shape
_PX, _PY = _xg[0].ravel(), _xg[1].ravel()
_T = (np.arange(_ne)[:, None, None] * _npt + _loc[None]).reshape(-1, 3)
_dB_sub = {k: 10.0 * np.log10(np.maximum(np.abs(v).ravel() ** 2, 1e-30)) for k, v in _sub.items()}
_tri_sub = mtri.Triangulation(_PX, _PY, _T)
_finder = mtri.Triangulation(skfem_mesh.p[0], skfem_mesh.p[1], skfem_mesh.t.T).get_trifinder()


def _cut_dB(k, xs, ys):
    """|E_k|^2 (dB) at points: locate the FEM triangle, then interpolate inside its sub-lattice."""
    e = _finder(xs, ys); ok = e >= 0; e0 = np.maximum(e, 0)
    p = skfem_mesh.p[:, skfem_mesh.t[:, e0]]                                  # (2, 3, n)
    J = np.stack([p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]], axis=-1)            # (2, n, 2)
    rhs = np.stack([xs - p[0, 0], ys - p[1, 0]])                              # (2, n)
    det = J[0, :, 0] * J[1, :, 1] - J[0, :, 1] * J[1, :, 0]
    xi = (J[1, :, 1] * rhs[0] - J[0, :, 1] * rhs[1]) / det * N_SUB
    et = (-J[1, :, 0] * rhs[0] + J[0, :, 0] * rhs[1]) / det * N_SUB
    i0 = np.clip(np.floor(xi), 0, N_SUB - 1).astype(int); j0 = np.clip(np.floor(et), 0, N_SUB - 1).astype(int)
    fx, fy = xi - i0, et - j0
    up = (fx + fy > 1.0) & (i0 + j0 < N_SUB - 1)
    i0 = np.minimum(i0, N_SUB - 1 - j0)
    V = _dB_sub[k].reshape(_ne, _npt)
    g = lambda i, j: V[e0, np.array([_idx[(a, b)] for a, b in zip(i, j)])]
    lo = (1 - fx - fy) * g(i0, j0) + fx * g(np.minimum(i0 + 1, N_SUB - j0), j0) + fy * g(i0, np.minimum(j0 + 1, N_SUB - i0))
    i1, j1 = np.minimum(i0 + 1, N_SUB), np.minimum(j0 + 1, N_SUB)
    hi = (fx + fy - 1) * g(np.minimum(i1, N_SUB - j1), j1) + (1 - fy) * g(np.minimum(i1, N_SUB - j0), j0) \
        + (1 - fx) * g(np.minimum(i0, N_SUB - j1), j1)
    return np.where(ok, np.where(up, hi, lo), np.nan)


def _window(xlim, ylim, pad=0.5):
    cx, cy = _PX[_T].mean(axis=1), _PY[_T].mean(axis=1)
    return ~((cx > xlim[0] - pad) & (cx < xlim[1] + pad) & (cy > ylim[0] - pad) & (cy < ylim[1] + pad))


def plot_components_db(xlim, ylim, dyn_db=80.0, title_extra="", figsize=(13, 9.5)):
    fig, axs = plt.subplots(3, 1, figsize=figsize, sharex=True)
    _mask = _window(xlim, ylim)
    for ax, k in zip(axs, ("Ex", "Ey", "Ez")):
        _t = mtri.Triangulation(_PX, _PY, _T, mask=_mask)
        tp = ax.tripcolor(_t, _dB_sub[k], cmap="turbo", vmin=-abs(dyn_db), vmax=0.0,
                          shading="gouraud", rasterized=True)
        _outline(ax, color="w", alpha=0.8)
        cb = fig.colorbar(tp, ax=ax, pad=0.012, extend="min")
        cb.set_label(rf"$|E_{k[1]}|^2$ / max$|E_x|^2$ (dB)")
        ax.set_xlim(xlim); ax.set_ylim(ylim); ax.set_aspect("equal")
        ax.set_ylabel(r"$y$ ($\mu$m)")
        ax.set_title(rf"$|E_{k[1]}|^2$ (dB, common reference max$|E_x|^2$)")
    for ax in axs:
        for _x in (GAP_BOT / 2.0, -GAP_BOT / 2.0):
            ax.axvline(_x, color="w", ls="--", lw=0.8, alpha=0.9)
        for _x in (SLAB_W / 2.0, -SLAB_W / 2.0):
            ax.axvline(_x, color="m", ls=":", lw=1.2)
    axs[-1].set_xlabel(r"$x$ ($\mu$m)")
    fig.suptitle(rf"Field components, {dyn_db:.0f} dB range | slab_w = {SLAB_W:.1f} um, "
                 rf"IL = {att_opt_dB_cm:.3f} dB/cm {title_extra}", y=0.995)
    plt.tight_layout(); plt.show()


# 1) whole section (white dashed: electrode inner edges, magenta dotted: slab ends)
plot_components_db(xlim=(-SLAB_W / 2.0 - 3.0, SLAB_W / 2.0 + 3.0), ylim=(-1.0, 2.6), dyn_db=100.0)

# 2) zoom on the standing-wave region: slab under the right electrode
_x0, _x1 = GAP_BOT / 2.0 - 1.0, SLAB_W / 2.0 + 1.0
plot_components_db(xlim=(_x0, _x1), ylim=(-0.4, 0.75), dyn_db=80.0,
                   title_extra="| zoom on the slab under the gold", figsize=(13, 8))

# 3) lateral cuts through the slab, read from the sub-sampled FEM field
_xs = np.linspace(0.0, SLAB_W / 2.0 + 1.5, 4000)
fig, axs = plt.subplots(1, 3, figsize=(16, 4.2), sharey=True)
for ax, k in zip(axs, ("Ex", "Ey", "Ez")):
    for _y, _c in ((SLAB_H * 0.1, "#27ae60"), (SLAB_H * 0.5, "#c0392b"), (SLAB_H * 0.9, "#2980b9")):
        _val = _cut_dB(k, _xs, np.full_like(_xs, _y))
        ax.plot(_xs, _val, lw=1.0, color=_c, label=f"y = {_y:.3f} um")
    ax.axvline(GAP_BOT / 2.0, color="k", ls="--", lw=0.8)
    ax.axvline(SLAB_W / 2.0, color="m", ls=":", lw=1.2)
    ax.set_title(rf"$|E_{k[1]}|^2$ in the slab (dB)"); ax.set_xlabel(r"$x$ ($\mu$m)")
    ax.grid(alpha=0.3); ax.set_ylim(-120, 3)
axs[0].set_ylabel(r"dB rel. max$|E_x|^2$"); axs[0].legend(fontsize=8, loc="lower left")
fig.suptitle("Lateral cuts in the LN slab (dashed: electrode inner edge, dotted: slab end)")
plt.tight_layout(); plt.show()
