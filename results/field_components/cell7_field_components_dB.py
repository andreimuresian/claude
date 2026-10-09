# %% [7] Field components in dB: whole section + zoom on the slab under the gold
# Same field as cell [6] (`_comp`: Ex, Ey, Ez phase-referenced to Ex, normalised to max|Ex|).
# Here we plot |E_i|^2 in dB relative to max|Ex|^2 (a log scale of the INTENSITY of each
# component), one value per mesh triangle (no averaging onto nodes), so that jumps at
# interfaces stay sharp and the tails are not smeared.
#   - whole section : rib mode + evanescent tails + standing wave under the gold, 3 components
#   - zoom          : the slab between the electrode inner edge and the slab end
#   - lateral cuts  : |E_i|^2 (dB) along x at three heights in the slab, 3 components
import matplotlib.tri as mtri

_I_el = {k: np.mean(np.abs(v) ** 2, axis=-1) for k, v in _comp.items()}       # per triangle
_dB_el = {k: 10.0 * np.log10(np.maximum(v, 1e-30)) for k, v in _I_el.items()}
_tri_el = mtri.Triangulation(skfem_mesh.p[0], skfem_mesh.p[1], skfem_mesh.t.T)
_finder = _tri_el.get_trifinder()


def plot_components_db(xlim, ylim, dyn_db=80.0, title_extra="", figsize=(13, 9.5)):
    fig, axs = plt.subplots(3, 1, figsize=figsize, sharex=True)
    for ax, k in zip(axs, ("Ex", "Ey", "Ez")):
        tp = ax.tripcolor(_tri_el, facecolors=_dB_el[k], cmap="turbo",
                          vmin=-abs(dyn_db), vmax=0.0, shading="flat", rasterized=True)
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

# 3) lateral cuts through the slab, exact per-triangle values (no interpolation)
_xs = np.linspace(0.0, SLAB_W / 2.0 + 1.5, 4000)
fig, axs = plt.subplots(1, 3, figsize=(16, 4.2), sharey=True)
for ax, k in zip(axs, ("Ex", "Ey", "Ez")):
    for _y, _c in ((SLAB_H * 0.1, "#27ae60"), (SLAB_H * 0.5, "#c0392b"), (SLAB_H * 0.9, "#2980b9")):
        _ti = _finder(_xs, np.full_like(_xs, _y))
        _val = np.where(_ti >= 0, _dB_el[k][np.maximum(_ti, 0)], np.nan)
        ax.plot(_xs, _val, lw=1.0, color=_c, label=f"y = {_y:.3f} um")
    ax.axvline(GAP_BOT / 2.0, color="k", ls="--", lw=0.8)
    ax.axvline(SLAB_W / 2.0, color="m", ls=":", lw=1.2)
    ax.set_title(rf"$|E_{k[1]}|^2$ in the slab (dB)"); ax.set_xlabel(r"$x$ ($\mu$m)")
    ax.grid(alpha=0.3); ax.set_ylim(-120, 3)
axs[0].set_ylabel(r"dB rel. max$|E_x|^2$"); axs[0].legend(fontsize=8, loc="lower left")
fig.suptitle("Lateral cuts in the LN slab (dashed: electrode inner edge, dotted: slab end)")
plt.tight_layout(); plt.show()
