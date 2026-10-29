"""
EO crosstalk of a coupled pair straight from CST's field monitors: no line
model, only the Step 1 formula evaluated on the simulated gap voltages.

    X_EO(f) = I_B / I_A,   I_k = c1 H[V_k+](n_g1) - c2 H[V_k-](n_g2)   (push-pull)
    H[V](n_g) = (1/L) int_0^L V(z) exp(j beta_o (z - L)) dz,  beta_o = 2 pi f n_g / c

V_k+ and V_k- are the voltages (signal -> lateral) of line k's two gaps, from
E_y at a point inside each gap: V_k+ ~ E_y(+y side gap), V_k- ~ -E_y(-y side
gap). The proportionality is quasi-static, the same for every gap and every
wave, so it cancels in B/A (checked to 0.1-0.2 dB at 80 GHz, docs/cst/xtalk/
istanbul/fields_30GHz/plane/gap_check_80GHz.py).

Terminations. A field monitor holds the field with one port driven and the
others matched (CST's port impedance). With the device's source and
terminations the ports see incident waves a_j, and by linearity

    V(z) = sum_j a_j F_j(z),

with a_j from the pair's S-matrix (the .s4p of the same run) and the
termination reflections: exact, the s4p is used only at the ports. With source
and load equal to the port impedance of the run (50 ohm) a = (a_src, 0, 0, 0):
the s4p is not needed (pair=None).
F_j for every port comes from the port-1 monitor by symmetry (A <-> B mirror,
end-to-end reversal), unless a monitor of that port is present (it is then
used as is). On the Istanbul 5 mm run the reversal reproduces the port-2
monitor to 1e-4.

Files: e-field_f<f>_<p>_<A|B>.txt (CST 3D export, one subvolume per line,
x fixed, z over the line; see docs/cst/xtalk/istanbul/fields_5mm/README.md).
"""
from __future__ import annotations

import glob
import os
import re

import numpy as np

from .physics import C0
from .scripted_line import rlc_z

NAME = re.compile(r"e-field_f(\d+(?:\.\d+)?)_(\d)_([AB])\.txt$")


def _gap_columns(path: str):
    """z (m) and E_y in the two gaps of one line: (+y side, -y side). The gap
    points are the y columns with a non-zero field (the others are in metal)."""
    a = np.loadtxt(path, skiprows=2)
    ys = np.unique(np.round(a[:, 1], 6)); zs = np.unique(np.round(a[:, 2], 6))
    iy = np.searchsorted(ys, np.round(a[:, 1], 6)); iz = np.searchsorted(zs, np.round(a[:, 2], 6))
    Ey = np.zeros((len(ys), len(zs)), complex)
    Ey[iy, iz] = a[:, 5] + 1j * a[:, 6]
    live = [j for j in range(len(ys)) if np.max(np.abs(Ey[j])) > 0]
    if len(live) != 2:
        raise ValueError(f"{os.path.basename(path)}: expected 2 gap columns, found {len(live)}")
    return zs * 1e-3, Ey[live[1]], Ey[live[0]]


def load_field_dir(path: str) -> dict:
    """{f_GHz: {port: {'A': (Ey+, Ey-), 'B': (Ey+, Ey-)}}, 'z': z (m)}."""
    out, z_ref = {}, None
    for fn in sorted(glob.glob(os.path.join(path, "e-field_f*_*_*.txt"))):
        m = NAME.search(os.path.basename(fn))
        if not m:
            continue
        f, port, line = float(m.group(1)), int(m.group(2)), m.group(3)
        z, ep, em = _gap_columns(fn)
        if z_ref is None:
            z_ref = z
        elif len(z) != len(z_ref) or not np.allclose(z, z_ref):
            raise ValueError(f"{os.path.basename(fn)}: z grid differs from the other files")
        out.setdefault(f, {}).setdefault(port, {})[line] = (ep, em)
    full = {f: d for f, d in out.items() if 1 in d and set(d[1]) == {"A", "B"}}
    if not full:
        raise ValueError(f"no complete port-1 pair (A and B files) in {path}")
    return dict(f_GHz=np.array(sorted(full)), ports={f: full[f] for f in sorted(full)}, z=z_ref,
                path=os.path.abspath(path))


def port_fields(fd: dict, f: float, order: str) -> list:
    """F_j for the four ports in block order A1, A2, B1, B2, each
    {'A': (Ey+, Ey-), 'B': (Ey+, Ey-)}. Mirror y -> -y swaps A <-> B and the
    two sides, and flips E_y; reversal z -> L - z keeps E_y."""
    from .xtalk_s4p import PORT_ORDERS
    d = fd["ports"][f]
    cst = [1, 2, 3, 4] if order == PORT_ORDERS[0] else [1, 3, 2, 4]   # CST port of A1, A2, B1, B2
    F1 = d[1]
    rev = lambda F: {k: (v[0][::-1], v[1][::-1]) for k, v in F.items()}
    mir = lambda F: {"A": (-F["B"][1], -F["B"][0]), "B": (-F["A"][1], -F["A"][0])}
    built = [F1, rev(F1), mir(F1), mir(rev(F1))]
    return [d[cst[j]] if cst[j] in d and set(d[cst[j]]) == {"A", "B"} else built[j] for j in range(4)]


def eo_crosstalk_fields(p: dict, fd: dict, pair: dict = None, port_z0: float = 50.0) -> dict:
    """Field-based EO crosstalk at the monitor frequencies, with the sidebar's
    source, termination, optics and drive. *pair*: xtalk_s4p.load_pair of the
    same run (only its S-matrix at the ports is used). Without *pair* the source
    and load must equal the port impedance of the run (*port_z0*): the exported
    port-1 field is then already the device case and the S-matrix drops out."""
    from .xtalk_cascade import arm_weights
    z = fd["z"]; L = z[-1] - z[0]
    if pair is not None and abs(L - pair["L"]) > 1e-6:
        raise ValueError(f"field data span {L*1e3:.3f} mm, the pair is {pair['L']*1e3:.3f} mm")
    c1, c2, ng1, ng2, pp = arm_weights(p)
    fs = fd["f_GHz"]
    fH = fs * 1e9
    R0 = pair["z0"] if pair is not None else float(port_z0)
    Zs = rlc_z(fH, float(p["Zs_R"]), float(p["Zs_L_pH"]) * 1e-12, float(p["Zs_C_fF"]) * 1e-15)
    Zt = rlc_z(fH, float(p["Rt_R"]), float(p["Rt_L_pH"]) * 1e-12, float(p["Rt_C_fF"]) * 1e-15)
    Gs, Gt = (Zs - R0) / (Zs + R0), (Zt - R0) / (Zt + R0)
    S = np.zeros((len(fs), 4, 4), complex)
    if pair is None:
        if max(np.max(abs(Gs)), np.max(abs(Gt))) > 1e-9:
            raise ValueError(f"without the run's s4p the source and load must be {R0:g} ohm "
                             "(the port impedance of the field run)")
    else:
        for i in range(4):
            for j in range(4):
                sij = pair["s"][:, i, j]
                S[:, i, j] = np.interp(fH, pair["f_Hz"], sij.real) + 1j * np.interp(fH, pair["f_Hz"], sij.imag)
    out = dict(f_GHz=fs, I_A=np.zeros(len(fs), complex), I_B=np.zeros(len(fs), complex),
               V={}, z=z, pushpull=pp)
    for n, f in enumerate(fs):
        G = np.diag([Gs[n], Gt[n], Gs[n], Gt[n]])
        src = np.array([R0 / (Zs[n] + R0), 0, 0, 0], complex)
        a = np.linalg.solve(np.eye(4) - G @ S[n], src)        # incident waves at A1, A2, B1, B2
        F = port_fields(fd, f, str(p.get("xs_port_order", "")) or "1 A near, 2 A far, 3 B near, 4 B far")
        V = {k: (sum(a[j] * F[j][k][0] for j in range(4)),            # V_k+ ~ Ey(+ side)
                 -sum(a[j] * F[j][k][1] for j in range(4)))           # V_k- ~ -Ey(- side)
             for k in ("A", "B")}
        out["V"][f] = V
        bo = lambda ng: 2 * np.pi * f * 1e9 * ng / C0
        H = lambda v, ng: np.trapezoid(v * np.exp(1j * bo(ng) * (z - z[-1])), z) / L
        for k in ("A", "B"):
            I = c1 * H(V[k][0], ng1) + ((-c2) * H(V[k][1], ng2) if pp else 0.0)
            out["I_" + k][n] = I
    out["X"] = out["I_B"] / out["I_A"]
    return out
