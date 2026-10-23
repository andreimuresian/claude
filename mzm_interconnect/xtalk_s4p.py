"""
Crosstalk of a coupled pair taken straight from its 4-port Touchstone file,
at the simulated length (no length extrapolation).

Two identical lines A and B (A <-> B mirror symmetry) split exactly into an
even 2-port (V_A = V_B) and an odd 2-port (V_A = -V_B):

    S_e = S_AA + S_AB,   S_o = S_AA - S_AB        (2 x 2 blocks, ends 1, 2)

A reciprocal, end-symmetric 2-port is one uniform line section: from its ABCD
matrix, cosh(gamma L) = (A + D)/2 and Z = sqrt(B/C). So each mode becomes a
table (loss, microwave index, Z) that the coupled-line element of
coupled_line.py turns back into the same 4-port at length L. Everything the
200 um dataset feeds (Python twin, EO crosstalk, INTERCONNECT tables and the
full cascade) then runs unchanged on these tables.

Two equivalent lines, both from the file
  * 'exact terminals': gamma and Z of each mode as extracted. Gives the file
    back exactly (S-parameters, so electrical NEXT and FEXT with any source
    and termination). But a NEXT that is not two-mode physics (the Istanbul
    NEXT is a far-end round trip, see docs/cst/xtalk/istanbul/fields_30GHz)
    is absorbed into an effective impedance split Ze != Zo, and that split
    launches a forward wave on B: on the 5 mm file -32.5 dB along the whole
    line at 30 GHz, against -45..-50 dB in CST's own fields. The EO crosstalk
    rides on that forward wave, so it is overstated (by ~13 dB there).
  * 'Ze = Zo (forward waves)': the same gamma_e, gamma_o, Z set to their mean.
    FEXT stays within ~1.5-3.5 dB of the file (it is set by the gamma split),
    NEXT is not reproduced (~20 dB low), and B's forward wave is the FEXT
    build-up, as in the fields. The default for the EO crosstalk.
  * Either way, the length must be the length that was simulated: the tables
    are per metre of that length.

Port order of the file: 'A1 A2 B1 B2' (1 = A near, 2 = A far, 3 = B near,
4 = B far; the Istanbul files) or 'A1 B1 A2 B2'.
"""
from __future__ import annotations

import os

import numpy as np

from .physics import C0
from .scripted_line import NP_PER_DB_EXACT, rlc_z
from . import coupled_line as CL

PORT_ORDERS = ("1 A near, 2 A far, 3 B near, 4 B far",
               "1 A near, 2 B near, 3 A far, 4 B far")
VARIANTS = ("Ze = Zo (forward waves)", "exact terminals")


def _reorder(s: np.ndarray, order: str) -> np.ndarray:
    """Return S in the block order A1, A2, B1, B2."""
    idx = [0, 1, 2, 3] if order == PORT_ORDERS[0] else [0, 2, 1, 3]
    return s[:, idx][:, :, idx]


def _s2abcd(S, z0):
    s11, s12, s21, s22 = S[:, 0, 0], S[:, 0, 1], S[:, 1, 0], S[:, 1, 1]
    A = ((1 + s11) * (1 - s22) + s12 * s21) / (2 * s21)
    B = z0 * ((1 + s11) * (1 + s22) - s12 * s21) / (2 * s21)
    C = ((1 - s11) * (1 - s22) - s12 * s21) / (2 * s21 * z0)
    D = ((1 - s11) * (1 + s22) + s12 * s21) / (2 * s21)
    return A, B, C, D


def _mode_line(S, f_Hz, L, z0):
    """gamma (1/m) and Z of the uniform line equivalent to a 2-port. The root
    of cosh(gamma L) = x is followed in frequency (the two roots are gamma and
    -gamma; at low loss their magnitudes are nearly equal), starting from
    beta > 0 at the lowest frequency, and the phase is unwrapped on the way."""
    A, B, C, D = _s2abcd(S, z0)
    x = (A + D) / 2
    r = np.sqrt(x * x - 1)
    gl = np.empty(len(f_Hz), complex)
    prev = None
    for i in range(len(f_Hz)):
        cands = [np.log(x[i] + r[i]), np.log(x[i] - r[i])]
        if prev is None:
            c = max(cands, key=lambda c: c.imag)            # beta > 0
            c = complex(abs(c.real), c.imag)
        else:
            best = None
            for c in cands:
                for k in (-1, 0, 1):                       # unwrap the phase
                    cc = complex(c.real, c.imag + 2 * np.pi * (np.round((prev.imag - c.imag)
                                                                       / (2 * np.pi)) + k))
                    if best is None or abs(cc - prev) < abs(best - prev):
                        best = cc
            c = best
        gl[i] = prev = c
    gamma = gl / L
    Z = np.sqrt(B / C)
    # sign of Z: B = Z sinh(gamma L)
    ref = B / np.sinh(gl)
    Z = np.where(np.real(Z * np.conj(ref)) < 0, -Z, Z)
    return gamma, Z, np.abs(A - D)


def load_pair(path: str, L_mm: float, order: str = PORT_ORDERS[0]) -> dict:
    """Read the s4p and build the even/odd mode tables at length *L_mm*.
    Returns f_Hz (DC dropped), the reordered S, the per-mode (gamma, Z), the
    tables in the single-line format, and the quality figures."""
    import skrf as rf
    net = rf.Network(path)
    if net.nports != 4:
        raise ValueError(f"{os.path.basename(path)} has {net.nports} ports, not 4")
    keep = net.f > 0
    f = net.f[keep]
    s = _reorder(net.s[keep], order)
    z0 = float(np.real(net.z0[0, 0]))
    L = float(L_mm) * 1e-3
    # A <-> B mirror symmetry and end symmetry: the decomposition assumes both
    sym_ab = float(np.max(np.abs(s[:, :2, :2] - s[:, 2:, 2:])))
    sym_end = float(np.max(np.abs(s[:, 0, 0] - s[:, 1, 1])))
    Saa = 0.5 * (s[:, :2, :2] + s[:, 2:, 2:])               # averaged A and B
    Sab = 0.5 * (s[:, :2, 2:] + s[:, 2:, :2])
    modes = {}
    for name, sgn in (("even", 1), ("odd", -1)):
        Sm = Saa + sgn * Sab
        # end-symmetric average (the uniform line has S11 = S22)
        Sm = Sm.copy()
        refl = 0.5 * (Sm[:, 0, 0] + Sm[:, 1, 1])
        thru = 0.5 * (Sm[:, 1, 0] + Sm[:, 0, 1])
        Sm[:, 0, 0] = Sm[:, 1, 1] = refl
        Sm[:, 1, 0] = Sm[:, 0, 1] = thru
        gamma, Z, _ = _mode_line(Sm, f, L, z0)
        w = 2 * np.pi * f
        modes[name] = dict(gamma=gamma, Z=Z,
                           table=(np.real(gamma) / NP_PER_DB_EXACT, np.imag(gamma) * C0 / w, Z))
    Zm = 0.5 * (modes["even"]["Z"] + modes["odd"]["Z"])
    for name in ("even", "odd"):
        t = modes[name]["table"]
        modes[name]["table_eq"] = (t[0], t[1], Zm)
    # the equivalent line must give the file back
    blk = CL.coupled_sparams(f, modes["even"]["table"], modes["odd"]["table"], L, R0=z0,
                             modulating=False)
    rec = np.array([[blk["S"][i][j] for j in range(4)] for i in range(4)]).transpose(2, 0, 1)
    err = np.abs(rec - s)
    return dict(path=os.path.abspath(path), name=os.path.basename(path), f_Hz=f, s=s, z0=z0,
                L=L, order=order, even=modes["even"], odd=modes["odd"],
                sym_ab=sym_ab, sym_end=sym_end, rec_err=float(np.max(err)),
                rec_err_xt=float(np.max(err[:, 2:, :2])),
                data_top_GHz=float(f[-1] / 1e9), data_min_GHz=float(f[0] / 1e9))


def tables_on_grid(pair: dict, f_Hz, variant: str = VARIANTS[0]):
    """Even/odd tables on *f_Hz* for *variant*: interpolated inside the file's
    band, held at the end values outside it (loss, index and Z frozen;
    INTERCONNECT needs the tables up to its Nyquist frequency, the analysis
    band stops at the data)."""
    f = np.asarray(f_Hz, float)
    key = "table" if variant == VARIANTS[1] else "table_eq"
    out = []
    for m in ("even", "odd"):
        loss, nm, Z = pair[m][key]
        fi = pair["f_Hz"]
        g = lambda y: np.interp(f, fi, y)
        out.append((g(loss), g(nm), g(np.real(Z)) + 1j * g(np.imag(Z))))
    return tuple(out)


def summary(pair: dict, f_GHz=(10.0, 30.0, 60.0)) -> list:
    rows = [f"{pair['name']}   L = {pair['L']*1e3:.3f} mm   data {pair['data_min_GHz']:.2f}-"
            f"{pair['data_top_GHz']:.1f} GHz   ref {pair['z0']:g} ohm",
            f"A/B asymmetry max {pair['sym_ab']:.1e}, end asymmetry max {pair['sym_end']:.1e}",
            f"equivalent line gives the file back to {pair['rec_err']:.1e} (crosstalk "
            f"terms {pair['rec_err_xt']:.1e})"
            + ("  -- ENDS NOT SYMMETRIC: the file is only approximated" if pair["sym_end"] > 1e-2
               else ""),
            f"{'GHz':>4s} {'n_e':>7s} {'n_o':>7s} {'a_e dB/cm':>9s} {'a_o':>5s} "
            f"{'Z_e ohm':>13s} {'Z_o ohm':>13s}"]
    for g in f_GHz:
        if g > pair["data_top_GHz"] + 1e-9:
            continue
        i = int(np.argmin(np.abs(pair["f_Hz"] / 1e9 - g)))
        e, o = pair["even"], pair["odd"]
        rows.append(f"{g:4.0f} {e['table'][1][i]:7.4f} {o['table'][1][i]:7.4f} "
                    f"{e['table'][0][i]/100:9.2f} {o['table'][0][i]/100:5.2f} "
                    f"{e['Z'][i].real:6.1f}{e['Z'][i].imag:+6.1f}j "
                    f"{o['Z'][i].real:6.1f}{o['Z'][i].imag:+6.1f}j")
    return rows


def pair_from_params(p: dict) -> dict:
    path = str(p["xs_s4p_path"]).strip()
    if not path:
        raise ValueError("choose the pair's .s4p file first")
    return load_pair(path, float(p["xs_L_mm"]), str(p["xs_port_order"]))


def device_crosstalk_s4p(p: dict, pair: dict = None) -> dict:
    """The twin on the file's own frequency points (up to the sidebar's sweep
    ceiling), for both variants: the 4-port at the file's reference and the
    circuit with the GUI's source, termination and n_g."""
    pair = pair or pair_from_params(p)
    f = pair["f_Hz"]
    sel = f <= float(p["f_max_GHz"]) * 1e9 + 1
    f = f[sel]
    from .xtalk_cascade import arm_weights
    _, _, ng1, ng2, pp = arm_weights(p)
    Zs = rlc_z(f, float(p["Zs_R"]), float(p["Zs_L_pH"]) * 1e-12, float(p["Zs_C_fF"]) * 1e-15)
    Rt = rlc_z(f, float(p["Rt_R"]), float(p["Rt_L_pH"]) * 1e-12, float(p["Rt_C_fF"]) * 1e-15)
    out = dict(f_GHz=f / 1e9, s_file=pair["s"][sel], L=pair["L"], pair=pair, pushpull=pp)
    for v, tag in zip(VARIANTS, ("eq", "full")):
        even, odd = tables_on_grid(pair, f, v)
        blk = CL.coupled_sparams(f, even, odd, pair["L"], ng=ng1, ng2=ng2 if pp else None,
                                 R0=pair["z0"])
        out[tag] = dict(block=blk, resp=CL.terminated_response(blk, Zs, Rt, pair["z0"]))
    return out


def export_tables(p: dict, out_dir: str, f_top_GHz=None, points_per_GHz: float = 20.0,
                  pair: dict = None) -> dict:
    """coupled_even.txt / coupled_odd.txt from the s4p (variant p['xs_variant']),
    up to the simulation's Nyquist frequency (same keys as
    coupled_line.export_coupled_tables)."""
    from .scripted_line import default_table_top_GHz
    pair = pair or pair_from_params(p)
    os.makedirs(out_dir, exist_ok=True)
    top = float(f_top_GHz or default_table_top_GHz(p))
    f_lo = 0.05
    f_GHz = np.linspace(f_lo, top, max(int((top - f_lo) * points_per_GHz), 32))
    variant = str(p.get("xs_variant", VARIANTS[0]))
    even, odd = tables_on_grid(pair, f_GHz * 1e9, variant)
    i30 = int(np.argmin(np.abs(pair["f_Hz"] - 30e9)))
    dz30 = (float(np.real(pair["even"]["Z"][i30] / pair["odd"]["Z"][i30]) - 1)
            if variant == VARIANTS[1] else 0.0)
    notes = [f"pair from {pair['name']}, L = {pair['L']*1e3:.4f} mm (equivalent even/odd lines, "
             f"{variant})",
             f"data {pair['data_min_GHz']:.2f}-{pair['data_top_GHz']:.1f} GHz; held constant outside",
             "columns frequency Hz, loss dB per m, microwave index, Re Z0, Im Z0"]
    pe, po = CL.write_mode_tables(os.path.join(out_dir, "coupled"), f_GHz * 1e9, even, odd, notes)
    dn = even[1] - odd[1]
    return dict(even=pe, odd=po, f_Hz=f_GHz * 1e9, dn=dn, dz=dz30, table_top_GHz=top,
                data_top_GHz=pair["data_top_GHz"], name=pair["name"], variant=variant,
                L=pair["L"])
