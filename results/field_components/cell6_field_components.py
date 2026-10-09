# %% [6] Field components Ex, Ey, Ez of the optical mode (signed, phase-referenced)
# The mode solver works on the 2D cross-section but solves for the FULL vector field of a
# mode E(x, y, z) = [Ex(x,y), Ey(x,y), Ez(x,y)] * exp(-j*beta*z): the z dependence is known
# analytically (exp(-j*beta*z)), so only the (x, y) profiles are unknowns. femwell discretises
# (Ex, Ey) with Nedelec (N1) edge elements and Ez with Lagrange (P1) nodal elements.
# femwell stores Ez already rescaled to its physical amplitude (it divides by j*beta/k0), so
# Ez is in quadrature (90 deg) with Et: after referencing the phase to Ex we plot Re(Ex),
# Re(Ey) and Im(Ez), all normalised to max|Ex|.
import matplotlib.tri as mtri
from matplotlib.colors import TwoSlopeNorm


def _v(f):
    return np.asarray(f.value if hasattr(f, "value") else f)


_Ei = fund_mode.basis.interpolate(fund_mode.E)
_Ex_q, _Ey_q, _Ez_q = _v(_Ei[0])[0], _v(_Ei[0])[1], _v(_Ei[1])      # (n_el, n_quad)

# global phase reference: make Ex real and positive at its maximum
_k = np.unravel_index(np.argmax(np.abs(_Ex_q)), _Ex_q.shape)
_ph = np.exp(-1j * np.angle(_Ex_q[_k]))
_A = np.abs(_Ex_q[_k])
_comp = {"Ex": _Ex_q * _ph / _A, "Ey": _Ey_q * _ph / _A, "Ez": _Ez_q * _ph / _A}


def _to_nodes(q):
    el = q.mean(axis=-1)
    out = np.zeros(skfem_mesh.p.shape[1], dtype=complex); cnt = np.zeros(skfem_mesh.p.shape[1])
    for i in range(skfem_mesh.t.shape[0]):
        np.add.at(out, skfem_mesh.t[i], el); np.add.at(cnt, skfem_mesh.t[i], 1.0)
    return out / np.maximum(cnt, 1.0)


_nod = {k: _to_nodes(v) for k, v in _comp.items()}
_trc = mtri.Triangulation(skfem_mesh.p[0], skfem_mesh.p[1], skfem_mesh.t.T)
_show = {"Ex": ("Re", _nod["Ex"].real), "Ey": ("Re", _nod["Ey"].real), "Ez": ("Im", _nod["Ez"].imag)}

# fraction of each component in the total |E|^2 (element-weighted, inside the window shown)
_area = 0.5 * np.abs((skfem_mesh.p[0, skfem_mesh.t[1]] - skfem_mesh.p[0, skfem_mesh.t[0]])
                     * (skfem_mesh.p[1, skfem_mesh.t[2]] - skfem_mesh.p[1, skfem_mesh.t[0]])
                     - (skfem_mesh.p[0, skfem_mesh.t[2]] - skfem_mesh.p[0, skfem_mesh.t[0]])
                     * (skfem_mesh.p[1, skfem_mesh.t[1]] - skfem_mesh.p[1, skfem_mesh.t[0]]))
_P = {k: float(np.sum(np.mean(np.abs(v) ** 2, axis=-1) * _area)) for k, v in _comp.items()}
_Ptot = sum(_P.values())
for k in _comp:
    _i = np.max(np.abs(_comp[k]))
    print(f"{k}: max|{k}|/max|Ex| = {_i:.3f}   share of integral |E|^2 = {_P[k] / _Ptot * 100:6.2f} %"
          + (f"   phase vs Ex: {np.angle(np.sum(_comp[k] * np.conj(_comp['Ex'])), deg=True):+.0f} deg" if k == "Ex" else ""))
_w = np.abs(_comp["Ez"]) ** 2
print(f"Ez in quadrature with Ex: |E|^2-weighted share of Ez in Im(Ez) = "
      f"{np.sum(_comp['Ez'].imag ** 2) / np.sum(_w) * 100:.1f} %  (100 % = exactly 90 deg)")


def plot_components(xlim=(-4.0, 4.0), ylim=(-0.8, 1.6), per_component_scale=True):
    fig, axs = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    for ax, (k, (part, f)) in zip(axs, _show.items()):
        m = np.max(np.abs(f)) if per_component_scale else 1.0
        cf = ax.tripcolor(_trc, f, shading="gouraud", cmap="RdBu_r",
                          norm=TwoSlopeNorm(0.0, -m, m))
        _outline(ax, color="k", alpha=0.6)
        cb = fig.colorbar(cf, ax=ax, pad=0.012)
        cb.set_label(rf"{part}$(E_{k[1]})$ / max$|E_x|$")
        ax.set_xlim(xlim); ax.set_ylim(ylim); ax.set_aspect("equal")
        ax.set_ylabel(r"$y$ ($\mu$m)")
        ax.set_title(rf"{part}($E_{k[1]}$)   peak = {np.max(np.abs(f)):.3f} $\times$ max$|E_x|$"
                     + ("   (own colour scale)" if per_component_scale and k != "Ex" else ""))
    axs[-1].set_xlabel(r"$x$ ($\mu$m)")
    fig.suptitle(rf"Fundamental mode field components | $n_{{eff}}$ = {np.real(n_eff):.4f}", y=0.995)
    plt.tight_layout(); plt.show()


plot_components()                              # each component on its own colour scale
plot_components(per_component_scale=False)     # common scale: true relative magnitudes

# ---- 1D cuts through the rib centre (y) and at mid-rib height (x) ---------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 3.8))
_xs = np.linspace(-4, 4, 1601); _ys = np.linspace(-0.8, 1.6, 1201)
_yc = SLAB_H + WG_H / 2.0
for k, (part, f) in _show.items():
    it = mtri.LinearTriInterpolator(_trc, f)
    a1.plot(_xs, it(_xs, np.full_like(_xs, _yc)), label=rf"{part}($E_{k[1]}$)")
    a2.plot(_ys, it(np.zeros_like(_ys), _ys), label=rf"{part}($E_{k[1]}$)")
a1.set_xlabel(r"$x$ ($\mu$m)"); a1.set_title(rf"horizontal cut, y = {_yc:.3f} um (mid rib)")
a2.set_xlabel(r"$y$ ($\mu$m)"); a2.set_title("vertical cut, x = 0")
for a in (a1, a2):
    a.axhline(0, color="k", lw=0.5); a.grid(alpha=0.3); a.legend(fontsize=8); a.set_ylabel("/ max|Ex|")
plt.tight_layout(); plt.show()
