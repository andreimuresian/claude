"""
Python twin of the coupled-electrode scripted element (two identical,
parallel TL lines A and B; LSF to follow).

Two identical coupled uniform lines are two independent uniform lines: the
even mode (V_A = V_B) and the odd mode (V_A = -V_B). Each mode is exactly the
single "TL line" element of scripted_line.py, with its own table (loss,
microwave index, Z). The block reuses ``tl_sparams`` for each mode and
recombines at the ports:

    S_AA = (S_e + S_o)/2          (own line)
    S_BA = (S_e - S_o)/2          (crosstalk: NEXT = S_B1,A1, FEXT = S_B2,A1)

and, because the modulation output is linear in the line voltage,

    V_A(z) = (V_e(z) + V_o(z))/2,  V_B(z) = (V_e(z) - V_o(z))/2

so the voltage the light integrates on each line, and each far-end voltage,
recombine the same way. No segmentation: every integral is the exact closed
form of the single-line element.

Port order: A1, A2, B1, B2 (1 = input end, 2 = far end). Keys:
  S[i][j]     4x4 S-matrix entries, arrays over frequency
  T[k][j]     modulation output of line k (0 = A, 1 = B) per unit incident
              wave at port j (same normalisation as T1/T2 of tl_sparams)
  T2[k][j]    the same at the second arm's group index (if ng2 is given)
  FE[k][j]    far-end voltage of line k per unit incident wave at port j
  NE[k][j]    near-end voltage of line k (at its end 1), same normalisation
"""

from __future__ import annotations

import numpy as np

from .scripted_line import NP_PER_DB_EXACT, read_tl_table, tl_sparams, write_tl_table
from .physics import C0

PORTS = ("A1", "A2", "B1", "B2")


def coupled_sparams(f_Hz, even: tuple, odd: tuple, L, ng=None, R0=50.0,
                    modulating=True, waves="voltage", ng2=None) -> dict:
    """*even*, *odd*: (loss_dB_per_m, microwave_index, Z) of each mode, as in
    the single-line tables. Returns the 4-port block (see module doc)."""
    e = tl_sparams(f_Hz, *even, L, ng, R0, modulating, waves, ng2)
    o = tl_sparams(f_Hz, *odd, L, ng, R0, modulating, waves, ng2)

    def comb(xe, xo, same):
        return 0.5 * (xe + xo) if same else 0.5 * (xe - xo)

    # line index of each port, and end (1 or 2)
    line = (0, 0, 1, 1)
    end = (1, 2, 1, 2)
    # single-line entry X[out_end][in_end]
    Se = {(1, 1): e["S11"], (2, 1): e["S21"], (1, 2): e["S21"], (2, 2): e["S11"]}
    So = {(1, 1): o["S11"], (2, 1): o["S21"], (1, 2): o["S21"], (2, 2): o["S11"]}
    S = [[comb(Se[end[i], end[j]], So[end[i], end[j]], line[i] == line[j])
          for j in range(4)] for i in range(4)]
    out = dict(f_Hz=np.asarray(f_Hz, float), L=L, R0=R0, waves=waves, S=S,
               even=e, odd=o)

    # far-end voltage of line k (voltage at its end 2): FE1 for wave at end 1,
    # FE2 for wave at end 2
    FEe = {1: e["FE1"], 2: e["FE2"]}
    FEo = {1: o["FE1"], 2: o["FE2"]}
    out["FE"] = [[comb(FEe[end[j]], FEo[end[j]], k == line[j]) for j in range(4)]
                 for k in range(2)]
    # near end: by symmetry of each mode line, a wave entering at end 1 gives
    # at end 1 what a wave entering at end 2 gives at end 2
    NEe = {1: e["FE2"], 2: e["FE1"]}
    NEo = {1: o["FE2"], 2: o["FE1"]}
    out["NE"] = [[comb(NEe[end[j]], NEo[end[j]], k == line[j]) for j in range(4)]
                 for k in range(2)]
    if modulating:
        for key, sfx in (("T", ""), ("T2", "_2")):
            if key == "T2" and ng2 is None:
                continue
            Te = {1: e["T1" + sfx], 2: e["T2" + sfx]}
            To = {1: o["T1" + sfx], 2: o["T2" + sfx]}
            out[key] = [[comb(Te[end[j]], To[end[j]], k == line[j]) for j in range(4)]
                        for k in range(2)]
    return out


# ---------------------------------------------------------------------------
# Mode tables: 3-D average line + 2-D even/odd split
# ---------------------------------------------------------------------------
def hybrid_mode_tables(f_Hz, gamma_3d, Z_3d, dbeta, dz):
    """Even/odd tables (loss_dB_per_m, microwave_index, Z) from the 3-D line
    (gamma_3d, Z_3d) and the 2-D split: dbeta = beta_even - beta_odd (1/m),
    dz = Z_even/Z_odd - 1. gamma_e,o = gamma_3d +- j dbeta/2,
    Z_e,o = Z_3d (1 +- dz/2). Loss is shared by both modes."""
    f = np.asarray(f_Hz, float)
    w = 2 * np.pi * f
    loss = np.real(gamma_3d) / NP_PER_DB_EXACT
    with np.errstate(divide="ignore", invalid="ignore"):
        n_e = (np.imag(gamma_3d) + dbeta / 2) * C0 / w
        n_o = (np.imag(gamma_3d) - dbeta / 2) * C0 / w
    if f[0] == 0:                      # index at DC: copy the next point
        n_e[0], n_o[0] = n_e[1], n_o[1]
    return ((loss, n_e, Z_3d * (1 + dz / 2)),
            (loss, n_o, Z_3d * (1 - dz / 2)))


def write_mode_tables(prefix: str, f_Hz, even, odd, notes=()):
    """Write <prefix>_even.txt and <prefix>_odd.txt in the single-line format."""
    pe = write_tl_table(prefix + "_even.txt", f_Hz, *even, notes=list(notes) + ["even mode"])
    po = write_tl_table(prefix + "_odd.txt", f_Hz, *odd, notes=list(notes) + ["odd mode"])
    return pe, po


def coupled_sparams_from_tables(path_even, path_odd, L, **kw) -> dict:
    fe, *even = read_tl_table(path_even)
    fo, *odd = read_tl_table(path_odd)
    if not np.array_equal(fe, fo):
        raise ValueError("even and odd tables must share the frequency grid")
    return coupled_sparams(fe, tuple(even), tuple(odd), L, **kw)


# ---------------------------------------------------------------------------
# Independent check: coupled telegrapher equations, brute force
# ---------------------------------------------------------------------------
def brute_force(f_Hz, even, odd, L, ng, R0=50.0, nz=4001, drive=0):
    """Solve the 2-line telegrapher equations directly (4x4 ODE, matrix
    exponential), all ports terminated in R0, unit voltage wave into port
    *drive*. Returns S column, modulation outputs of A and B (trapezoidal
    integration of V(z) on nz points) and the far-end voltages. Shares no
    code with coupled_sparams; it is only for checking."""
    from scipy.linalg import expm
    Tm = np.array([[1, 1], [1, -1]], float)
    Ti = np.linalg.inv(Tm)
    z = np.linspace(0, L, nz)
    res = dict(S=np.zeros((len(f_Hz), 4), complex), T=np.zeros((len(f_Hz), 2), complex),
               FE=np.zeros((len(f_Hz), 2), complex))
    for n, f in enumerate(f_Hz):
        w = 2 * np.pi * f
        g = [m[0][n] * NP_PER_DB_EXACT + 1j * w * m[1][n] / C0 for m in (even, odd)]
        Zm = [m[2][n] for m in (even, odd)]
        Zp = Tm @ np.diag([g[0] * Zm[0], g[1] * Zm[1]]) @ Ti
        Yp = Tm @ np.diag([g[0] / Zm[0], g[1] / Zm[1]]) @ Ti
        M = np.block([[np.zeros((2, 2)), -Zp], [-Yp, np.zeros((2, 2))]])
        PhL = expm(M * L)
        # unknown state x0 = [VA, VB, IA, IB] at z = 0 (I flowing +z)
        a = np.zeros(4); a[drive] = 1.0
        A = np.zeros((4, 4), complex); b = np.zeros(4, complex)
        # z = 0 ports A1 (k=0), B1 (k=1): V + R0 I = 2 a
        for r, (k, p) in enumerate(((0, 0), (1, 2))):
            A[r, k] = 1; A[r, 2 + k] = R0; b[r] = 2 * a[p]
        # z = L ports A2, B2: V - R0 I = 2 a  (current into the port is -I)
        for r, (k, p) in enumerate(((0, 1), (1, 3))):
            A[2 + r] = PhL[k] - R0 * PhL[2 + k]; b[2 + r] = 2 * a[p]
        x0 = np.linalg.solve(A, b)
        X = np.array([expm(M * zz) @ x0 for zz in z]) if nz <= 400 else None
        if X is None:      # step with a fixed propagator: fast and exact
            P = expm(M * (z[1] - z[0]))
            X = np.empty((nz, 4), complex); X[0] = x0
            for i in range(1, nz):
                X[i] = P @ X[i - 1]
        xL = X[-1]
        V0, VL = x0[:2], xL[:2]
        I0, IL = x0[2:], xL[2:]
        b0 = (V0 - R0 * I0) / 2          # waves leaving at z = 0
        bL = (VL + R0 * IL) / 2          # waves leaving at z = L
        res["S"][n] = [b0[0], bL[0], b0[1], bL[1]]
        bo = w * ng / C0
        ph = np.exp(1j * bo * (z - L)) / L
        res["T"][n] = [np.trapezoid(X[:, k] * ph, z) for k in (0, 1)]
        res["FE"][n] = VL
    return res


# ---------------------------------------------------------------------------
# The network INTERCONNECT will solve
# ---------------------------------------------------------------------------
def terminated_response(block: dict, Zs, Rt, R0=50.0) -> dict:
    """
    Aggressor A driven by an EMF of 1 V behind Zs at A1; the victim's input B1
    sees its own (idle) driver Zs; both far ends A2, B2 end in Rt. *Zs* and
    *Rt* are scalars or arrays on the block's grid (see scripted_line.rlc_z).
    Same normalisation as scripted_line.chain_response, so the aggressor's H
    equals the single-line H when the coupling is removed.

    Returns H_A, H_B (voltage the light integrates on each line, referenced to
    the light leaving the line), H2_A, H2_B (second arm, if present), the
    far-end voltages FE_A, FE_B, the port voltages V (4 x nf, order A1 A2 B1
    B2) and s11_in at A1 (reference Zs).
    """
    f = block["f_Hz"]
    nf = len(f)
    Zs = np.broadcast_to(np.asarray(Zs, complex), f.shape)
    Rt = np.broadcast_to(np.asarray(Rt, complex), f.shape)
    Gs = (Zs - R0) / (Zs + R0)
    Gt = (Rt - R0) / (Rt + R0)
    src = R0 / (Zs + R0)
    S = np.array([[np.broadcast_to(block["S"][i][j], f.shape) for j in range(4)]
                  for i in range(4)])                       # 4 x 4 x nf
    a = np.zeros((nf, 4), complex)
    for n in range(nf):
        G = np.diag([Gs[n], Gt[n], Gs[n], Gt[n]])
        rhs = np.array([src[n], 0, 0, 0], complex)
        a[n] = np.linalg.solve(np.eye(4) - G @ S[:, :, n], rhs)
    b = np.einsum("ijn,nj->ni", S, a)
    out = dict(f_Hz=f, a=a, V=(a + b).T)

    def lin(rows):
        return [sum(rows[k][j] * a[:, j] for j in range(4)) for k in range(2)]
    out["FE_A"], out["FE_B"] = lin(block["FE"])
    out["NE_A"], out["NE_B"] = lin(block["NE"])
    if "T" in block:
        out["H_A"], out["H_B"] = lin(block["T"])
    if "T2" in block:
        out["H2_A"], out["H2_B"] = lin(block["T2"])
    Zin = (a[:, 0] + b[:, 0]) / ((a[:, 0] - b[:, 0]) / R0)
    out["s11_in"] = (Zin - Zs) / (Zin + Zs)
    return out


# ---------------------------------------------------------------------------
# Tables for a device: the GUI's own line + the 2-D even/odd split
# ---------------------------------------------------------------------------
def read_betas(path: str):
    """2-D port-mode table: columns frequency (GHz), beta_even, beta_odd (1/m).
    Lines starting with a letter or '#' are skipped. Returns (f_Hz, dbeta)."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s or s[0].isalpha() or s[0] == "#":
                continue
            rows.append([float(x) for x in s.replace(",", " ").split()[:3]])
    M = np.array(rows)
    return M[:, 0] * 1e9, M[:, 1] - M[:, 2]


def dbeta_on_grid(f_Hz, betas_path=None, dn=None):
    """beta_even - beta_odd on *f_Hz*: from a 2-D port-mode table (dbeta/f
    interpolated, held constant outside the table, i.e. dn held constant), or
    from a constant index split *dn* = n_even - n_odd."""
    f = np.asarray(f_Hz, float)
    if betas_path:
        fb, db = read_betas(betas_path)
        return np.interp(f, fb, db / fb) * f
    return 2 * np.pi * f * float(dn) / C0


def device_mode_tables(fit, p: dict, f_GHz, dz: float, betas_path=None, dn=None):
    """Even/odd tables on *f_GHz*: the GUI's fitted electrode line (the same
    line as the single-line model, from line_tables, with the GUI's what-if
    knobs) split by the 2-D even/odd results. Returns (even, odd, dn(f))."""
    from .extractor import line_tables
    f = np.asarray(f_GHz, float) * 1e9
    alpha, Zc, nm = line_tables(fit, p, np.asarray(f_GHz, float))
    w = 2 * np.pi * f
    gamma = np.asarray(alpha) * 100.0 * NP_PER_DB_EXACT + 1j * w * np.asarray(nm) / C0
    db = dbeta_on_grid(f, betas_path, dn)
    even, odd = hybrid_mode_tables(f, gamma, np.asarray(Zc, complex), db, float(dz))
    return even, odd, db * C0 / w


def device_crosstalk(fit, p: dict, dz: float, betas_path=None, dn=None, f_GHz=None) -> dict:
    """The twin for the GUI's device: the 4-port at R0 (NEXT/FEXT as a VNA
    would measure them) and the circuit with the GUI's source and termination
    (resistance, series L and shunt C, as the TL source/load elements)."""
    from .scripted_line import rlc_z
    if f_GHz is None:
        f_GHz = np.linspace(max(fit.f_min_sim_GHz, 0.05), float(p["f_max_GHz"]), 600)
    f = np.asarray(f_GHz, float) * 1e9
    even, odd, dn_f = device_mode_tables(fit, p, f_GHz, dz, betas_path, dn)
    L = float(p["L_target_mm"]) * 1e-3
    blk = coupled_sparams(f, even, odd, L, ng=float(p["ng"]))
    Zs = rlc_z(f, float(p["Zs_R"]), float(p["Zs_L_pH"]) * 1e-12, float(p["Zs_C_fF"]) * 1e-15)
    Rt = rlc_z(f, float(p["Rt_R"]), float(p["Rt_L_pH"]) * 1e-12, float(p["Rt_C_fF"]) * 1e-15)
    return dict(f_GHz=np.asarray(f_GHz, float), block=blk, resp=terminated_response(blk, Zs, Rt),
                dn=dn_f, dz=float(dz), L=L)


def export_coupled_tables(fit, p: dict, out_dir: str, dz: float, betas_path=None,
                          dn=None, f_top_GHz=None, points_per_GHz: float = 20.0) -> dict:
    """
    Write coupled_even.txt and coupled_odd.txt (device_mode_tables) on the grid
    and density of export_tl_tables.
    """
    import os
    from .scripted_line import default_table_top_GHz
    os.makedirs(out_dir, exist_ok=True)
    top = float(f_top_GHz or default_table_top_GHz(p))
    f_lo = max(fit.f_min_sim_GHz, 1e-3)
    f_GHz = np.linspace(f_lo, top, max(int((top - f_lo) * points_per_GHz), 32))
    even, odd, dn_f = device_mode_tables(fit, p, f_GHz, dz, betas_path, dn)
    src = (f"2-D split from {os.path.basename(betas_path)}" if betas_path
           else f"constant index split dn = {float(dn):.6g}")
    notes = [f"coupled electrodes: line from {os.path.basename(fit.source_file)}",
             src, f"Ze/Zo - 1 = {float(dz):.6g}",
             "columns frequency Hz, loss dB per m, microwave index, Re Z0, Im Z0"]
    pe, po = write_mode_tables(os.path.join(out_dir, "coupled"), f_GHz * 1e9, even, odd, notes)
    return dict(even=pe, odd=po, f_Hz=f_GHz * 1e9, dn=dn_f, dz=float(dz), table_top_GHz=top)
