"""
Python twin of the "TL line" scripted element (lumerical/tl_element_setup.lsf).

The scripted element is a uniform transmission line with an exact S-matrix:
two bidirectional RF ports (the two ends of the line), an output carrying the
voltage the light integrates along it (electrodes only), and optionally an
output carrying the far-end voltage. INTERCONNECT solves the network it sits
in -- source, electrodes, bends, termination -- so no Thevenin tables and no
per-neighbour files are needed: each element's table depends only on that
element.

This module does three things:

  * writes the element tables (``electrode_line.txt``, ``bend_line.txt``) in
    the format the LSF reads with ``readdata``;
  * repeats, line for line, what the LSF computes (``tl_sparams``), so the
    S-parameters INTERCONNECT builds can be checked number by number;
  * solves the same network INTERCONNECT will solve (``chain_response``) and
    compares it with the closed-form model, as the prediction for Step 0.

Conventions (identical in the LSF):
  voltage waves in reference R0:  a = (V + R0 I)/2,  b = (V - R0 I)/2
  modulation output = (1/L) int_0^L V(z) exp(+j b_o z) dz * exp(-j b_o L)
  i.e. referenced to the light leaving the line, like eo_transfer.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import numpy as np

from .physics import (C0, bend_line, bend_summary, electrode_layout, eo_transfer,
                      first_crossing)

# The LSF uses log(10)/20; physics.py uses the rounded 1/8.686. The difference
# is 1e-5 relative on the loss, far below anything measurable, but the twin
# must repeat the LSF exactly.
NP_PER_DB_EXACT = np.log(10.0) / 20.0

TABLE_HEADER = "frequency_Hz loss_dB_per_m microwave_index Re_Z0_ohm Im_Z0_ohm"


# ---------------------------------------------------------------------------
# 1. Tables
# ---------------------------------------------------------------------------
def write_tl_table(path: str, f_Hz, loss_dB_m, nm, Z, notes=()) -> str:
    """Write a table the LSF can read. readdata skips lines that start with a
    letter, so every header and note line starts with one."""
    f_Hz = np.asarray(f_Hz, float)
    Z = np.broadcast_to(np.asarray(Z, complex), f_Hz.shape)
    nm = np.broadcast_to(np.asarray(nm, float), f_Hz.shape)
    loss = np.broadcast_to(np.asarray(loss_dB_m, float), f_Hz.shape)
    with open(path, "w", encoding="ascii") as fh:
        for n in notes:
            fh.write("Note " + str(n).replace("\n", " ") + "\n")
        fh.write(TABLE_HEADER + "\n")
        for row in zip(f_Hz, loss, nm, Z.real, Z.imag):
            fh.write(" ".join(f"{v:.12e}" for v in row) + "\n")
    return path


def read_tl_table(path: str):
    """Read a table exactly as the LSF does: skip lines starting with a letter,
    then add a DC row copied from the first point if the table starts above 0."""
    rows = []
    with open(path, encoding="ascii") as fh:
        for line in fh:
            s = line.strip()
            if not s or s[0].isalpha():
                continue
            rows.append([float(x) for x in s.split()])
    M = np.array(rows)
    f, loss, nm, Z = M[:, 0], M[:, 1], M[:, 2], M[:, 3] + 1j * M[:, 4]
    if f[0] > 0:
        f = np.r_[0.0, f]
        loss, nm, Z = np.r_[loss[0], loss], np.r_[nm[0], nm], np.r_[Z[0], Z]
    return f, loss, nm, Z


# ---------------------------------------------------------------------------
# 2. The element itself (mirror of tl_element_setup.lsf)
# ---------------------------------------------------------------------------
def _int_lin(q, L):
    """(exp(q L) - 1) / q, the integral of exp(q z) over 0..L, as the LSF
    computes it: the series L (1 + qL/2 + (qL)^2/6) where |qL| < 1e-6, because
    there exp(qL) - 1 cancels (a lossless, velocity-matched section has q = 0
    and lost 2 % that way)."""
    qL = q * L
    sm = np.abs(qL) < 1e-6
    return np.where(sm, L * (1 + qL / 2 + qL * qL / 6), (np.exp(qL) - 1) / (q + sm))


def tl_sparams(f_Hz, loss_dB_m, nm, Z, L, ng=None, R0=50.0,
               modulating=True, waves="voltage", ng2=None) -> dict:
    """S-matrix entries of one TL line element, as the LSF sets them. With
    *ng2* the element also has the "modulation 2" output (T1_2, T2_2): the same
    line voltage integrated by light at the second arm's group index."""
    f_Hz = np.asarray(f_Hz, float)
    w = 2 * np.pi * f_Hz
    g = np.asarray(loss_dB_m) * NP_PER_DB_EXACT + 1j * w * np.asarray(nm) / C0
    Zl = np.asarray(Z, complex)
    G = (Zl - R0) / (Zl + R0)
    e1 = np.exp(-g * L)
    e2 = e1 * e1
    den = 1 - G * G * e2
    S11 = G * (1 - e2) / den
    S21 = (1 - G * G) * e1 / den
    ws = np.sqrt(R0) if waves == "power" else 1.0
    Rw = R0 / ws
    out = dict(f_Hz=f_Hz, S11=S11, S21=S21, L=L, R0=R0, waves=waves,
               modulating=bool(modulating),
               FE1=ws * S21, FE2=ws * (1 + S11))
    if modulating:
        def vavg(V1, I1, ngk):
            bo = w * float(ngk) / C0
            F1 = _int_lin(-g + 1j * bo, L)
            F2 = _int_lin(g + 1j * bo, L)
            Xo = np.exp(-1j * bo * L) / L
            Vp = (V1 + Zl * I1) / 2
            Vm = (V1 - Zl * I1) / 2
            return (Vp * F1 + Vm * F2) * Xo

        port1 = (ws * (1 + S11), (1 - S11) / Rw)
        port2 = (ws * S21, -S21 / Rw)
        out["T1"] = vavg(*port1, ng)
        out["T2"] = vavg(*port2, ng)
        out["ng"] = float(ng)
        if ng2 is not None:
            out["T1_2"] = vavg(*port1, ng2)
            out["T2_2"] = vavg(*port2, ng2)
            out["ng2"] = float(ng2)
    return out


def tl_electrode_sparams(f_Hz, layout, el_tab, bend_tab=None, ng=2.27, ng2=None,
                        R0=50.0, waves="voltage") -> dict:
    """
    The "TL electrode" element (lumerical/tl_electrode_setup.lsf), line for
    line: a whole bent electrode -- modulating sections and bends -- as ONE
    element. *layout* rows are (L_rf, L_opt, modulating); *el_tab* and
    *bend_tab* are (loss_dB_m, nm, Z) on the grid *f_Hz*.

    S-matrix: product of the sections' ABCD matrices (exact cascade; S22 differs
    from S11 when the electrode is not symmetric). Modulation outputs: per
    modulating section the exact integral of V(z) (V and I at its entry found by
    stepping through the cascade), referenced to the light leaving it, delayed
    by the light's transit through everything after it, weighted L_k / L_mod and
    summed -- one output per arm, referenced to the light leaving the electrode.
    The optical delays between sections are phases here, not Optical Delay
    elements: in INTERCONNECT those emit no light for their first tau, which
    swamped the EO trace (the first bend run).
    """
    f_Hz = np.asarray(f_Hz, float)
    w = 2 * np.pi * f_Hz
    lay = [tuple(map(float, r)) for r in layout]

    def line(tab):
        loss, nm, Z = tab
        return (np.asarray(loss) * NP_PER_DB_EXACT + 1j * w * np.asarray(nm) / C0,
                np.asarray(Z, complex))
    ge, Ze = line(el_tab)
    gb, Zb = line(bend_tab) if bend_tab is not None else (ge, Ze)
    tA, tB, tC, tD = (np.ones_like(w, complex), np.zeros_like(w, complex),
                      np.zeros_like(w, complex), np.ones_like(w, complex))
    for L, _Lo, mod in lay:
        g, Z = (ge, Ze) if mod > 0.5 else (gb, Zb)
        e1, e2 = np.exp(g * L), np.exp(-g * L)
        ch, sh = (e1 + e2) / 2, (e1 - e2) / 2
        tA, tB, tC, tD = (tA * ch + tB * sh / Z, tA * Z * sh + tB * ch,
                          tC * ch + tD * sh / Z, tC * Z * sh + tD * ch)
    den = tA + tB / R0 + tC * R0 + tD
    S11 = (tA + tB / R0 - tC * R0 - tD) / den
    S22 = (-tA + tB / R0 - tC * R0 + tD) / den
    S21 = 2 / den
    ws = np.sqrt(R0) if waves == "power" else 1.0
    Rw = R0 / ws
    Lmod = sum(L for L, _o, m in lay if m > 0.5)
    ngs = [ng] + ([ng2] if ng2 is not None else [])
    T = [[np.zeros_like(w, complex), np.zeros_like(w, complex)] for _ in ngs]
    exc = [[ws * (1 + S11), (1 - S11) / Rw], [ws * S21, -S21 / Rw]]   # V, I at the entry
    tail = sum(Lo for _L, Lo, _m in lay)
    for L, Lo, mod in lay:
        g, Z = (ge, Ze) if mod > 0.5 else (gb, Zb)
        tail -= Lo
        if mod > 0.5:
            for km, ngk in enumerate(ngs):
                bo = w * float(ngk) / C0
                F1 = _int_lin(-g + 1j * bo, L)
                F2 = _int_lin(g + 1j * bo, L)
                Xo = np.exp(-1j * bo * L) / L * np.exp(-1j * bo * tail) * (L / Lmod)
                for j, (V, I) in enumerate(exc):
                    T[km][j] = T[km][j] + ((V + Z * I) / 2 * F1 + (V - Z * I) / 2 * F2) * Xo
        e1, e2 = np.exp(g * L), np.exp(-g * L)
        ch, sh = (e1 + e2) / 2, (e1 - e2) / 2
        exc = [[ch * V - Z * sh * I, -sh / Z * V + ch * I] for V, I in exc]
    out = dict(f_Hz=f_Hz, S11=S11, S22=S22, S21=S21, L=Lmod, R0=R0, waves=waves,
               modulating=True, FE1=ws * S21, FE2=ws * (1 + S22),
               T1=T[0][0], T2=T[0][1], ng=float(ng))
    if ng2 is not None:
        out.update(T1_2=T[1][0], T2_2=T[1][1], ng2=float(ng2))
    return out


def tl_electrode_from_paths(paths: dict, R0=50.0, waves="voltage", second=False) -> dict:
    """The TL electrode element exactly as the build configures it from the
    exported tables and electrode_layout.txt."""
    meta = paths["meta"]
    d = os.path.dirname(paths["json"])
    f, le, ne, Ze = read_tl_table(os.path.join(d, "electrode_line.txt"))
    bend = None
    if os.path.exists(os.path.join(d, "bend_line.txt")):
        fb, lb, nb, Zb = read_tl_table(os.path.join(d, "bend_line.txt"))
        bend = (lb, nb, Zb)
    lay = read_layout(os.path.join(d, "electrode_layout.txt"))
    e0 = next(e for e in meta["elements"] if e["modulating"])
    return tl_electrode_sparams(f, lay, (le, ne, Ze), bend, e0["ng"],
                                e0.get("ng2") if second else None, R0, waves)


def write_layout(path: str, layout) -> str:
    with open(path, "w", encoding="ascii") as fh:
        fh.write("Note one row per piece, from the RF input to the termination\n")
        fh.write("L_rf_m L_opt_m modulating\n")
        for L, Lo, m in layout:
            fh.write(f"{L:.12e} {Lo:.12e} {int(m)}\n")
    return path


def read_layout(path: str):
    rows = []
    with open(path, encoding="ascii") as fh:
        for line in fh:
            t = line.strip()
            if t and not t[0].isalpha():
                rows.append(tuple(float(x) for x in t.split()))
    return rows


def rlc_z(f_Hz, R, L_H=0.0, C_F=0.0):
    """Source / load impedance exactly as source_setup.lsf and
    termination_setup.lsf compute it: (R + jwL) in parallel with C."""
    f_Hz = np.asarray(f_Hz, float)
    if L_H == 0 and C_F == 0:
        return np.full(f_Hz.shape, complex(R))
    w = 2 * np.pi * f_Hz
    Zrl = R + 1j * w * L_H
    return Zrl / (1 + 1j * w * C_F * Zrl)


def tl_sparams_from_table(path: str, L, ng=None, R0=50.0, modulating=True,
                          waves="voltage", ng2=None) -> dict:
    f, loss, nm, Z = read_tl_table(path)
    return tl_sparams(f, loss, nm, Z, L, ng, R0, modulating, waves, ng2)


# ---------------------------------------------------------------------------
# 3. The network INTERCONNECT will solve
# ---------------------------------------------------------------------------
@dataclass
class ChainResult:
    f_Hz: np.ndarray
    vavg: list            # per element: modulation voltage (None for a bend)
    far_end: list         # per element: voltage at its port 2
    s11_in: np.ndarray    # reflection seen by the source, reference Zs
    H: np.ndarray         # EO response: length-weighted sum at the device exit
    vavg2: list = None    # per element: "modulation 2" (None if absent)
    H2: np.ndarray = None  # the same sum for the second arm (its own n_g)


def chain_response(elements: list, Zs, Rt, R0=50.0, ng=None,
                   opt_lengths=None) -> ChainResult:
    """
    Source (EMF 1 V behind Zs) -> element 1 -> element 2 -> ... -> Rt.

    *elements* are tl_sparams dicts on a common grid, all with reference R0 and
    voltage waves. *Zs* and *Rt* are scalars or arrays on that grid (an R+L+C
    network, see rlc_z). Unknowns are the incident waves at every element port;
    b = S a inside each element, a = b of the neighbour across each joint,
    a = G_s b + src at the source and a = G_t b at the termination.

    *opt_lengths* are the optical path lengths of the elements (default: their
    RF lengths); they set the light's delay between modulating elements.
    """
    f = elements[0]["f_Hz"]
    nf, n = len(f), len(elements)
    Zs = np.broadcast_to(np.asarray(Zs, complex), f.shape)
    Rt = np.broadcast_to(np.asarray(Rt, complex), f.shape)
    Gs = (Zs - R0) / (Zs + R0)
    Gt = (Rt - R0) / (Rt + R0)
    src = R0 / (Zs + R0)                         # voltage waves, EMF 1 V
    a = np.zeros((nf, 2 * n), complex)
    for i in range(nf):
        S = np.zeros((2 * n, 2 * n), complex)
        for k, el in enumerate(elements):
            s11, s21 = el["S11"][i], el["S21"][i]
            s22 = el["S22"][i] if "S22" in el else s11
            S[2 * k:2 * k + 2, 2 * k:2 * k + 2] = [[s11, s21], [s21, s22]]
        C = np.zeros((2 * n, 2 * n), complex)
        C[0, 0] = Gs[i]
        for k in range(n - 1):
            C[2 * k + 2, 2 * k + 1] = 1
            C[2 * k + 1, 2 * k + 2] = 1
        C[2 * n - 1, 2 * n - 1] = Gt[i]
        rhs = np.zeros(2 * n, complex)
        rhs[0] = src[i]
        a[i] = np.linalg.solve(np.eye(2 * n) - C @ S, rhs)

    vavg, vavg2, far = [], [], []
    for k, el in enumerate(elements):
        a1, a2 = a[:, 2 * k], a[:, 2 * k + 1]
        far.append(el["FE1"] * a1 + el["FE2"] * a2)
        vavg.append(el["T1"] * a1 + el["T2"] * a2 if el["modulating"] else None)
        vavg2.append(el["T1_2"] * a1 + el["T2_2"] * a2 if "T1_2" in el else None)
    b1 = elements[0]["S11"] * a[:, 0] + elements[0]["S21"] * a[:, 1]
    V_in = a[:, 0] + b1
    I_in = (a[:, 0] - b1) / R0
    Zin = V_in / I_in
    s11_in = (Zin - Zs) / (Zin + Zs)

    # Light: each modulation output is referenced to the light leaving its
    # element, so everything downstream delays it by n_g * (optical length)/c.
    opt = opt_lengths or [el["L"] for el in elements]
    w = 2 * np.pi * f
    Lmod = sum(el["L"] for el in elements if el["modulating"])

    def light_sum(vs, key):
        H = np.zeros(nf, complex)
        tail = 0.0
        for k in range(n - 1, -1, -1):
            el = elements[k]
            if el["modulating"]:
                ngk = float(ng if ng is not None else el[key])
                H += el["L"] / Lmod * vs[k] * np.exp(-1j * w * ngk * tail / C0)
            tail += opt[k]
        return H

    H = light_sum(vavg, "ng")
    two = all(v is not None for v, el in zip(vavg2, elements) if el["modulating"])
    H2 = light_sum(vavg2, "ng2") if two and ng is None else None
    return ChainResult(f, vavg, far, s11_in, H, vavg2, H2)


# ---------------------------------------------------------------------------
# 4. Export for a device (electrodes + bends)
# ---------------------------------------------------------------------------
def default_table_top_GHz(p: dict) -> float:
    """The table has to reach the Nyquist frequency of the simulation: INTERCONNECT
    designs the filter over the whole band, and a table that stops at the ENA
    ceiling leaves the rest to extrapolation."""
    fs = float(p["ic_sample_rate_GHz"])
    sym = float(p["bitrate_Gbps"]) / (2 if str(p.get("mod_format", "NRZ")).upper() == "PAM4" else 1)
    fs = max(fs, 16 * sym)                      # the eye build raises it to this
    return max(float(p["f_max_GHz"]), 0.5 * fs)


def export_tl_tables(fit, p: dict, out_dir: str, f_top_GHz=None,
                     points_per_GHz: float = 20.0) -> dict:
    """
    Write electrode_line.txt, bend_line.txt (if the device has bends) and
    tl_elements.json (the element list, in order, with lengths and n_g).
    """
    from .extractor import line_tables
    os.makedirs(out_dir, exist_ok=True)
    top = float(f_top_GHz or default_table_top_GHz(p))
    f_lo = max(fit.f_min_sim_GHz, 1e-3)
    f_GHz = np.linspace(f_lo, top, max(int((top - f_lo) * points_per_GHz), 32))
    alpha, Zc, nm = line_tables(fit, p, f_GHz)
    notes = [f"electrode line from {os.path.basename(fit.source_file)}",
             f"measured range {fit.f_min_sim_GHz:.2f}-{fit.f_max_sim_GHz:.2f} GHz, "
             f"beyond that the fitted model",
             "columns frequency Hz, loss dB per m, microwave index, Re Z0, Im Z0"]
    paths = {"electrode": write_tl_table(os.path.join(out_dir, "electrode_line.txt"),
                                         f_GHz * 1e9, alpha * 100.0, nm, Zc, notes)}
    lay = electrode_layout(p)
    if any(x["kind"] == "bend" for x in lay):
        b = bend_line(p, f_GHz)
        paths["bend"] = write_tl_table(
            os.path.join(out_dir, "bend_line.txt"), f_GHz * 1e9,
            b["bend_alpha_dB_cm"] * 100.0, b["bend_nm"], b["bend_Z"],
            ["bend line: its own loss, index and impedance, not the electrode's",
             bend_summary(p),
             "columns frequency Hz, loss dB per m, microwave index, Re Z0, Im Z0"])
    # Arm 1 on "modulation" (ng1), arm 2 on "modulation 2" (ng2): the same
    # split of ng_imbalance as physics.arm_models.
    ng = float(p["ng"])
    dn = float(p.get("ng_imbalance", 0.0))
    ng1, ng2 = ng * (1.0 + dn / 2.0), ng * (1.0 - dn / 2.0)
    els, k_el, k_b = [], 0, 0
    for x in lay:
        if x["kind"] == "mod":
            k_el += 1
            els.append(dict(name=f"EL_{k_el}", kind="electrode", table="electrode_line.txt",
                            line_length=x["L_rf"], optical_length=x["L_opt"], ng=ng1,
                            ng2=ng2, modulating=1))
        else:
            k_b += 1
            els.append(dict(name=f"BEND_{k_b}", kind="bend", table="bend_line.txt",
                            line_length=x["L_rf"], optical_length=x["L_opt"], ng=ng1,
                            ng2=ng2, modulating=0))
    paths["layout"] = write_layout(os.path.join(out_dir, "electrode_layout.txt"),
                                   [(x["L_rf"], x["L_opt"], 1 if x["kind"] == "mod" else 0)
                                    for x in lay])
    meta = dict(R0=50.0, Zs=float(p["Zs_R"]), Rt=float(p["Rt_R"]),
                Zs_L_pH=float(p.get("Zs_L_pH", 0.0)), Zs_C_fF=float(p.get("Zs_C_fF", 0.0)),
                Rt_L_pH=float(p.get("Rt_L_pH", 0.0)), Rt_C_fF=float(p.get("Rt_C_fF", 0.0)),
                wave_convention="voltage", elements=els,
                table_top_GHz=top, points=len(f_GHz))
    paths["json"] = os.path.join(out_dir, "tl_elements.json")
    with open(paths["json"], "w") as fh:
        json.dump(meta, fh, indent=2)
    paths["meta"] = meta
    return paths


def device_chain(paths: dict, R0=50.0, waves="voltage", second=False):
    """Build the element list from exported tables, exactly as INTERCONNECT
    will see it, and return (elements, optical lengths). With *second* the
    electrodes also carry "modulation 2" at the second arm's n_g."""
    meta = paths["meta"]
    d = os.path.dirname(paths["json"])
    els = []
    for e in meta["elements"]:
        els.append(tl_sparams_from_table(os.path.join(d, e["table"]), e["line_length"],
                                         e["ng"], R0, bool(e["modulating"]), waves,
                                         e.get("ng2") if second else None))
    return els, [e["optical_length"] for e in meta["elements"]]


def device_terminations(paths: dict, f_Hz):
    """(Zs, Zt) on *f_Hz* from the exported metadata, as the scripted source
    and load compute them."""
    m = paths["meta"]
    return (rlc_z(f_Hz, m["Zs"], m.get("Zs_L_pH", 0.0) * 1e-12, m.get("Zs_C_fF", 0.0) * 1e-15),
            rlc_z(f_Hz, m["Rt"], m.get("Rt_L_pH", 0.0) * 1e-12, m.get("Rt_C_fF", 0.0) * 1e-15))


def far_end_model(paths: dict, f_max_GHz=None):
    """(f_GHz, V_termination / EMF): the voltage across the termination, from
    the same tables, source and load the TL line build uses. The prediction
    for ENA_1 input 2 (after its factor 1/2, see InterconnectBuilder)."""
    els, opt = device_chain(paths)
    if f_max_GHz is not None:
        m = els[0]["f_Hz"] <= float(f_max_GHz) * 1e9 * 1.0001
        els = [{k: (v[m] if isinstance(v, np.ndarray) and v.shape == m.shape else v)
                for k, v in el.items()} for el in els]
    Zs, Zt = device_terminations(paths, els[0]["f_Hz"])
    r = chain_response(els, Zs, Zt, opt_lengths=opt)
    return r.f_Hz / 1e9, r.far_end[-1]


# ---------------------------------------------------------------------------
# 5. Comparison helpers (numbers, not pictures)
# ---------------------------------------------------------------------------
def bw_GHz(f_GHz, H, f_norm_GHz=1.0, level_dB=-3.0) -> float:
    f_GHz = np.asarray(f_GHz, float)
    ref = np.abs(np.interp(f_norm_GHz, f_GHz, np.abs(H)))
    dB = 20 * np.log10(np.maximum(np.abs(H), 1e-300) / ref)
    fc = first_crossing(f_GHz, dB, level_dB, f_start=f_norm_GHz)
    return float(fc) if fc is not None else float("nan")     # never crosses in range


def compare_traces(f_ref_GHz, H_ref, f_test_GHz, H_test, band=(1.0, 150.0),
                   scale_band=(0.5, 3.0), f_norm_GHz=1.0, convention=None) -> dict:
    """
    Compare two complex responses (*ref* in the engineering convention).

    Three things are separated out before anything is called a difference:
      * the phase convention of *test*: INTERCONNECT works in exp(-i w t), so
        its phases are the conjugate of ours. Pass *convention* to impose it;
        otherwise both readings are tried and the one that leaves the smaller
        non-linear phase residual is used. The guess is only reliable when the
        two responses agree, so a report should fix it from its cleanest row
        ('physics' means the test data were conjugated);
      * a pure latency (the digital filters' processing delay), fitted as a
        straight line in phase over *band* and reported as 'latency_ps';
      * an overall scale (|test/ref| median over *scale_band*), which carries
        the drive and wave conventions.
    What is left is reported as max |dB| and max phase difference over *band*,
    plus the -3 dB bandwidth of each.
    """
    f_ref = np.asarray(f_ref_GHz, float)
    Ht0 = np.interp(f_ref, f_test_GHz, np.real(H_test)) + \
        1j * np.interp(f_ref, f_test_GHz, np.imag(H_test))
    Hr = np.asarray(H_ref, complex)
    b = (f_ref >= band[0]) & (f_ref <= band[1])
    m = (f_ref >= scale_band[0]) & (f_ref <= scale_band[1])
    # Angular frequency in rad/ns, so the latency is fitted in ns: with w in
    # rad/s the two columns differ by ~1e12 and lstsq drops the constant one,
    # forcing the phase offset to zero and biasing the latency.
    w = 2 * np.pi * f_ref[b]
    A = np.column_stack([np.ones_like(w), -w])

    cands = (("engineering", Ht0), ("physics", np.conj(Ht0)))
    if convention is not None:          # fixed by the caller (e.g. from the cleanest row)
        cands = tuple(c for c in cands if c[0] == convention)
    best = None
    for conv, Ht in cands:
        ph = np.unwrap(np.angle(Ht[b] / Hr[b]))
        (ph0, tau), *_ = np.linalg.lstsq(A, ph, rcond=None)
        resid = ph - (ph0 - w * tau)
        rms = float(np.sqrt(np.mean(resid ** 2)))
        if best is None or rms < best[0]:
            best = (rms, conv, Ht, ph0, tau, resid)
    _, conv, Ht, ph0, tau, resid = best

    scale_abs = float(np.median(np.abs(Ht[m] / Hr[m])))
    wf = 2 * np.pi * f_ref
    Ht_n = Ht * np.exp(1j * wf * tau) / scale_abs          # latency and scale removed
    ddB = 20 * np.log10(np.abs(Ht_n[b]) / np.abs(Hr[b]))
    ph0w = float(np.angle(np.exp(1j * ph0)))
    return dict(scale_abs=scale_abs, scale_deg=float(np.degrees(ph0w)), convention=conv,
                latency_ps=float(tau * 1e3),
                max_dB=float(np.max(np.abs(ddB))),
                max_deg=float(np.degrees(np.max(np.abs(resid)))),
                bw_ref_GHz=bw_GHz(f_ref, Hr, f_norm_GHz),
                bw_test_GHz=bw_GHz(f_ref, np.abs(Ht_n), f_norm_GHz))


def interpret_scale(scale_abs: float, R0: float = 50.0) -> str:
    """Name the conversion factor an overall scale corresponds to, if any. Only
    the ratio between two INTERCONNECT rows (TL line / TW block) says anything
    about the element; a factor shared by both rows belongs to the analyser."""
    cands = {1.0: "x1", 0.5: "x1/2", 2.0: "x2", np.sqrt(R0): "x sqrt(R0)",
             1 / np.sqrt(R0): "x 1/sqrt(R0)", np.sqrt(R0) / 2: "x sqrt(R0)/2",
             2 / np.sqrt(R0): "x 2/sqrt(R0)"}
    best = min(cands, key=lambda c: abs(np.log(scale_abs / c)))
    if abs(np.log(scale_abs / best)) < 0.02:
        return f"{scale_abs:.4f} (= {cands[best]})"
    return f"{scale_abs:.4f} (not a clean factor)"
