# %% [5] Optical mode: dB contour map + lateral tail cut
# Place this as a NEW cell AFTER cell [4] (it needs `fund_mode`, `polygons`, `DEV_W`).
import matplotlib.tri as mtri


def _val(f):
    """DiscreteField -> ndarray, tolerant of skfem version differences."""
    return np.asarray(f.value if hasattr(f, "value") else f)


# ---- total intensity |E|^2 per element, then averaged onto nodes -----------
_Ei = fund_mode.basis.interpolate(fund_mode.E)
_Et, _Ez = _val(_Ei[0]), _val(_Ei[1])
I_el = (np.mean(np.abs(_Et[0]) ** 2, axis=-1)
        + np.mean(np.abs(_Et[1]) ** 2, axis=-1)
        + np.mean(np.abs(_Ez) ** 2, axis=-1))

I_nodal = np.zeros(skfem_mesh.p.shape[1])
_cnt = np.zeros(skfem_mesh.p.shape[1])
for _i in range(skfem_mesh.t.shape[0]):
    np.add.at(I_nodal, skfem_mesh.t[_i], I_el)
    np.add.at(_cnt, skfem_mesh.t[_i], 1.0)
I_nodal /= np.maximum(_cnt, 1.0)

I_dB = 10.0 * np.log10(np.maximum(I_nodal / I_nodal.max(), 1e-16))
_tri = mtri.Triangulation(skfem_mesh.p[0], skfem_mesh.p[1], skfem_mesh.t.T)
_interp = mtri.LinearTriInterpolator(_tri, I_dB)


def _outline(ax, lw=0.7, color="white", alpha=0.85):
    """Draw material boundaries so the contours can be read against geometry."""
    for _nm, _pg in polygons.items():
        if _nm.startswith(("clad", "box_far", "slab_far", "buf_far")):
            continue
        for _part in (_pg.geoms if _pg.geom_type == "MultiPolygon" else [_pg]):
            _xy = np.asarray(_part.exterior.coords)
            ax.plot(_xy[:, 0], _xy[:, 1], lw=lw, color=color, alpha=alpha, zorder=5)


def plot_mode_db(dyn_db=60.0, xlim=(-6.0, 6.0), ylim=(-1.0, 2.0),
                 n_levels=24, cmap="turbo"):
    """Contour the mode in dB below peak. Raise dyn_db to see deeper into the tails."""
    fig, ax = plt.subplots(figsize=(12, 4.2))
    lv = np.linspace(-abs(dyn_db), 0.0, n_levels + 1)
    cf = ax.tricontourf(_tri, I_dB, levels=lv, cmap=cmap, extend="min")
    ax.tricontour(_tri, I_dB, levels=lv[::4], colors="k", linewidths=0.3, alpha=0.35)
    _outline(ax)
    cb = fig.colorbar(cf, ax=ax, pad=0.012)
    cb.set_label(r"$|E|^2$ relative to peak (dB)")
    ax.set_xlim(xlim); ax.set_ylim(ylim); ax.set_aspect("equal")
    ax.set_xlabel(r"$x$ ($\mu$m)"); ax.set_ylabel(r"$y$ ($\mu$m)")
    ax.set_title(rf"Fundamental mode, {dyn_db:.0f} dB dynamic range | "
                 rf"BUFFER_H = {BUFFER_H*1e3:.0f} nm, IL = {att_opt_dB_cm:.2f} dB/cm")
    plt.tight_layout(); plt.show()


# Interactive slider if ipywidgets is available; otherwise three fixed ranges.
try:
    from ipywidgets import interact, FloatSlider, fixed
    interact(plot_mode_db,
             dyn_db=FloatSlider(value=60, min=20, max=160, step=5,
                                description="dyn range (dB)", continuous_update=False),
             xlim=fixed((-6.0, 6.0)), ylim=fixed((-1.0, 2.0)),
             n_levels=fixed(24), cmap=fixed("turbo"))
except ImportError:
    # no ipywidgets: show three fixed ranges instead. Call plot_mode_db(dyn_db=...)
    # yourself, or widen xlim to (-25, 25) to see the full electrode span.
    for _d in (40, 80, 140):
        plot_mode_db(dyn_db=_d)


# ---- THE DIAGNOSTIC: lateral cut through the slab -------------------------
# A BOUND mode decays as a straight line in dB.
# A LEAKY mode decays, then flattens into a plateau / standing-wave ripple that
# runs all the way out under the electrodes.
fig, ax = plt.subplots(figsize=(11, 4.0))
x_max = GAP_BOT / 2.0 + EL_W          # out to the far edge of the electrode
for _y, _lab, _c in [(SLAB_H * 0.5, "slab mid-height", "#c0392b"),
                     (SLAB_H + BUFFER_H * 0.5 if BUFFER_H > 0 else SLAB_H * 0.9,
                      "buffer mid-height" if BUFFER_H > 0 else "slab top", "#2980b9")]:
    _xs = np.linspace(0.0, x_max, 2000)
    _v = _interp(_xs, np.full_like(_xs, _y))
    ax.plot(_xs, _v, lw=1.3, color=_c, label=f"y = {_y:.3f} um ({_lab})")

ax.axvline(GAP_BOT / 2.0, color="k", ls="--", lw=0.9)
ax.text(GAP_BOT / 2.0 + 0.2, -8, "electrode inner edge", fontsize=8, rotation=90, va="top")
for _a, _b, _ in SKIN_SEGMENTS:
    ax.axvline(GAP_BOT / 2.0 + _b, color="gray", ls=":", lw=0.7)
ax.set_xlabel(r"$x$ ($\mu$m)"); ax.set_ylabel(r"$|E|^2$ below peak (dB)")
ax.set_ylim(-160, 2); ax.set_xlim(0, x_max)
ax.grid(alpha=0.25)
ax.legend(fontsize=8, loc="upper right")
ax.set_title(rf"Lateral decay of the mode | BUFFER_H = {BUFFER_H*1e3:.0f} nm "
             rf"(straight line = bound, plateau/ripple = leaky)")
plt.tight_layout(); plt.show()

# Quantify it: fit the decay slope over the first 3 um, then report the residual
# level far out. A bound tail extrapolates to << the measured far-field level.
_xs = np.linspace(GAP_BOT / 2.0, GAP_BOT / 2.0 + 3.0, 200)
_v = np.asarray(_interp(_xs, np.full_like(_xs, SLAB_H * 0.5)))
_ok = np.isfinite(_v)
_slope = np.polyfit(_xs[_ok], _v[_ok], 1)[0]
_x_far = GAP_BOT / 2.0 + 15.0
_far = float(_interp(_x_far, SLAB_H * 0.5))
_pred = float(np.polyval(np.polyfit(_xs[_ok], _v[_ok], 1), _x_far))
print(f"near-field decay slope      : {_slope:.2f} dB/um")
print(f"level at x = {_x_far:.1f} um  measured : {_far:.1f} dB")
print(f"                  extrapolated bound : {_pred:.1f} dB")
print(f"excess over a bound tail    : {_far - _pred:+.1f} dB"
      f"   <-- large positive => radiating, not evanescent")
