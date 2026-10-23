"""
The full MZM cascade in crosstalk mode: two modulators, A (aggressor, driven)
and B (victim, its driver idle), whose straight electrodes run side by side as
the 200 um pitch coupled pair.

    ENA / NRZ -> SRC_A (Zs) -> A1 ===== A2 -> LOAD_A (Rt)        electrode
                 LOAD_B1 (Zs) -> B1 ===== B2 -> LOAD_B (Rt)       Compound
                               "Coupled TL" (CTL_1)
                 modulation A / 2 A  -> OM_A_1 / OM_A_2   (modulator A's arms)
                 modulation B / 2 B  -> OM_B_1 / OM_B_2   (modulator B's arms)

    CWL_A -> SPLT_A1 -> arms of A -> SPLT_A2 -> PIN_A -> ENA input 1 (or EYE_1)
    CWL_B -> SPLT_B1 -> arms of B -> SPLT_B2 -> PIN_B -> ENA input 2 (or EYE_2)

Each modulator is the single-line build's interferometer (same laser, Y
branches, bias, arm-2 loss, modulator coefficients, push-pull or single arm);
B is a copy of A. The electrode is the Coupled TL element of the GUI's
Crosstalk window, at its length xt_L_mm, with the worse impedance split; the
source and terminations are the sidebar's (full R, L, C). The same electrical
network is the Python twin's terminated_response, so:

  * ENA input 1 is A's EO response, input 2 is B's: the ratio is the EO
    crosstalk in the receiver, the quantity the GUI's panel 3 predicts;
  * in eye mode EYE_1 is A's eye (now on the coupled line) and EYE_2 is what
    reaches B's receiver while B's driver is idle: pure crosstalk.

Scope: a straight electrode (the crosstalk dataset is one uniform section).
Bends between coupled sections are not modelled.

Nothing here imports lumapi unless run_xtalk_cascade() is called.
"""

from __future__ import annotations

import os
import traceback
from typing import Callable, Optional

import numpy as np

from . import coupled_line as CL
from . import parameters as P
from . import scripted_line as SL
from .interconnect import (P_BI1, P_BI2, P_IN, P_IN1, P_IN2, P_MOD, P_OUT, P_OUT1, P_OUT2,
                           P_COMB_OUT, P_Y1, P_Y2, P_Y3, InterconnectBuilder, clean_eo_trace)
from .physics import C0

MZMS = ("A", "B")
COMPOUND = "PAIR"
FIR_TAPS = 1024
L_OM = 1e-6


def arm_weights(p: dict):
    """(c1, c2, ng1, ng2, pushpull): the modulator coefficients and group
    indices of the two arms, as in the single-line build."""
    vpi = float(p["Vpi_V"])
    d = float(p["vpi_imbalance_frac"])
    c1 = -np.pi / (vpi * L_OM)
    c2 = +np.pi / (vpi * (1.0 + d) * L_OM)
    ng = float(p["ng"])
    dn = float(p.get("ng_imbalance", 0.0))
    pushpull = str(p["drive_config"]) == "push-pull"
    return c1, c2, ng * (1.0 + dn / 2.0), ng * (1.0 - dn / 2.0), pushpull


def twin(p: dict, out_dir: str, top_GHz: float, points_per_GHz: float = 40.0) -> dict:
    """Tables up to *top_GHz* and the Python twin of the cascade: the line
    voltages each arm's light integrates (H_A, H_B, and H2_A, H2_B at the
    second arm's n_g) with the sidebar's source and termination, and the
    small-signal photocurrent of each modulator, w1 H(ng1) + w2 H(ng2) with
    w1 = c1, w2 = -c2 (push-pull) or w2 = 0 (single arm). Both modulators are
    biased alike, so their ratio is the receiver's EO crosstalk."""
    ds = CL.load_dataset()
    dz = float(ds["dz_hi"])
    tables = CL.export_coupled_tables(p, out_dir, dz, f_top_GHz=top_GHz,
                                      points_per_GHz=points_per_GHz)
    c1, c2, ng1, ng2, pp = arm_weights(p)
    L = float(p["xt_L_mm"]) * 1e-3
    blk = CL.coupled_sparams_from_tables(tables["even"], tables["odd"], L, ng=ng1,
                                         ng2=ng2 if pp else None, R0=InterconnectBuilder.R0)
    f = blk["f_Hz"]
    Zs = SL.rlc_z(f, float(p["Zs_R"]), float(p["Zs_L_pH"]) * 1e-12, float(p["Zs_C_fF"]) * 1e-15)
    Rt = SL.rlc_z(f, float(p["Rt_R"]), float(p["Rt_L_pH"]) * 1e-12, float(p["Rt_C_fF"]) * 1e-15)
    r = CL.terminated_response(blk, Zs, Rt, InterconnectBuilder.R0)
    w2 = -c2 if pp else 0.0
    opt = {k: c1 * r[f"H_{k}"] + (w2 * r[f"H2_{k}"] if pp else 0.0) for k in MZMS}
    return dict(tables=tables, f_GHz=f / 1e9, resp=r, opt=opt, L=L, dz=dz,
                ng1=ng1, ng2=ng2, pushpull=pp)


class XtalkCascadeBuilder(InterconnectBuilder):
    """The single-line builder's helpers, with two modulators on one coupled
    electrode."""

    COMPOUND = COMPOUND

    # ---------------------------------------------------------------- optics
    def _splitters(self, tag: str, x: int, y: int, p: dict) -> dict:
        """Input splitter and output combiner of modulator *tag* (Y branches,
        else the Optical Splitter), with the port names each answers to."""
        rho = min(max(0.5 + float(p["split_err"]), 1e-6), 1 - 1e-6)
        s_in, s_out = f"SPLT_{tag}1", f"SPLT_{tag}2"
        try:
            for name, xx, t in ((s_in, x, 1.0 - rho), (s_out, x + 500, 0.5)):
                self.add(['Waveguide Y Branch'], name, xx, y)
                self.setp(name, ['configuration'], 'bidirectional', required=False)
                self.setp(name, ['input parameter'], 'coupling coefficient')
                self.setp(name, ['insertion loss'], float(p["y_branch_loss_dB"]), required=False)
                self.setp(name, ['coupling coefficient 1'], t)
                self.setp(name, ['coupling coefficient 2'], t, required=False)
                self.setp(name, ['phase shift'], 0.0, required=False)
            return dict(s_in=s_in, s_out=s_out, y=True, split_in=P_Y1, split_a=P_Y2,
                        split_b=P_Y3, comb_out=P_Y1, comb_a=P_Y2, comb_b=P_Y3)
        except Exception as exc:
            self.log(f"  {tag}: Waveguide Y Branch not available ({exc}); Optical Splitter.")
        for name in (s_in, s_out):
            try:
                self.sim.delete(name)
            except Exception:
                pass
        self.add(['Optical Splitter', 'Optical Splitter/Coupler'], s_in, x, y)
        self.setp(s_in, ['configuration'], 'splitter', required=False)
        self.setp(s_in, ['split ratio'], 'even')
        self.add(['Optical Combiner', 'Optical Splitter/Coupler', 'Optical Splitter'],
                 s_out, x + 500, y)
        self.setp(s_out, ['configuration'], 'combiner', required=False)
        self.setp(s_out, ['split ratio'], 'even')
        return dict(s_in=s_in, s_out=s_out, y=False, split_in=P_IN, split_a=P_OUT1,
                    split_b=P_OUT2, comb_out=P_COMB_OUT, comb_a=P_IN1, comb_b=P_IN2)

    def _modulator(self, name, x, y, coeff):
        self.add(['Optical Modulator Measured', 'Optical Modulator (Measured)'], name, x, y)
        self.setp(name, ['configuration'], 'bidirectional')
        self.setp(name, ['length'], L_OM)
        self.setp(name, ['electrode type'], 'lumped')
        self.setp(name, ['input parameter'], 'coefficients')
        self.setp(name, ['phase coefficient c', 'c'], coeff)
        for k in ('a', 'b', 'd'):
            self.setp(name, [f'phase coefficient {k}', k], 0.0, required=False)
        for k in ('a', 'b', 'c', 'd'):
            self.setp(name, [f'absorption coefficient {k}', f'absorption {k}'], 0.0,
                      required=False)

    def _mzm(self, tag: str, y0: int, p: dict) -> list:
        """One interferometer, laser to photodiode. Returns [(arm output,
        modulator)] for the electrode outputs: 'modulation <tag>' -> arm 1 and,
        push-pull, 'modulation 2 <tag>' -> arm 2."""
        c1, c2, ng1, ng2, pp = arm_weights(p)
        f_opt = C0 / (float(p["lambda_nm"]) * 1e-9)
        cwl, phs, pin = f"CWL_{tag}", f"PHS_{tag}", f"PIN_{tag}"
        self.add(['CW Laser'], cwl, 115, y0 + 75)
        self.setp(cwl, ['frequency'], f_opt)
        self.setp(cwl, ['power'], 10 ** (float(p["P_laser_dBm"]) / 10) / 1000)
        self.setp(cwl, ['linewidth'], 0)
        self.setp(cwl, ['enable RIN', 'RIN enable'], False, required=False)
        sp = self._splitters(tag, 280, y0 + 75, p)
        rho = min(max(0.5 + float(p["split_err"]), 1e-6), 1 - 1e-6)
        d_split = 0.0 if sp["y"] else -10.0 * np.log10((1.0 - rho) / rho)
        d_loss = float(p["arm_loss_imbalance_dB"]) + d_split
        self.add(['Optical Phase Shift'], phs, 640, y0 + 165)
        self.setp(phs, ['input parameter'], 'constant', required=False)
        self.setp(phs, ['phase shift'],
                  float(np.deg2rad(float(p["bias_phase_deg"]) + float(p["arm_phase_imbalance_deg"]))))
        att = None
        if d_loss > 1e-9:
            att = f"ATT_{tag}"
            self.add(['Optical Attenuator'], att, 730, y0 + 165)
            self.setp(att, ['attenuation'], d_loss)
        self.add(['PIN Photodetector', 'Photodetector'], pin, 950, y0 + 90)
        self.setp(pin, ['responsivity'], 1)
        self.setp(pin, ['frequency at max power'], False, required=False)
        self.setp(pin, ['frequency'], f_opt, required=False)
        for q in ('thermal noise', 'shot noise', 'power saturation'):
            self.setp(pin, [f'enable {q}', f'{q} enable'], False, required=False)

        om1 = f"OM_{tag}_1"
        self._modulator(om1, 560, y0, c1)
        self.connect(cwl, P_OUT, sp["s_in"], sp["split_in"])
        self.connect(sp["s_in"], sp["split_a"], om1, P_BI1)
        self.connect(om1, P_BI2, sp["s_out"], sp["comb_a"])
        outs = [(f"modulation {tag}", om1)]
        arm2_from, arm2_port = sp["s_in"], sp["split_b"]
        if pp:
            om2 = f"OM_{tag}_2"
            self._modulator(om2, 560, y0 + 165, c2)
            self.connect(sp["s_in"], sp["split_b"], om2, P_BI1)
            arm2_from, arm2_port = om2, P_BI2
            outs.append((f"modulation 2 {tag}", om2))
        self.connect(arm2_from, arm2_port, phs, P_BI1)
        tail, tail_port = phs, P_BI2
        if att:
            self.connect(phs, P_BI2, att, P_IN)
            tail, tail_port = att, P_OUT
        self.connect(tail, tail_port, sp["s_out"], sp["comb_b"])
        self.connect(sp["s_out"], sp["comb_out"], pin, P_IN)
        return outs

    # ------------------------------------------------------------ electrode
    def _electrode(self, p: dict, tw: dict, drive: str, outs: list):
        """SRC_A, LOAD_B1, CTL_1, LOAD_A, LOAD_B as one Compound with
        scattering data analysis on; each modulation output becomes a Compound
        output wired to its modulator."""
        top_Hz = float(tw["tables"]["table_top_GHz"]) * 1e9
        n_freq = max(201, int(float(tw["tables"]["table_top_GHz"]) * 4) + 1)
        zs = (float(p["Zs_R"]), float(p["Zs_L_pH"]) * 1e-12, float(p["Zs_C_fF"]) * 1e-15)
        rt = (float(p["Rt_R"]), float(p["Rt_L_pH"]) * 1e-12, float(p["Rt_C_fF"]) * 1e-15)
        self.make_source("SRC_A", 260, -200, *zs, top_Hz, n_freq)
        self.make_load("LOAD_B1", 260, -80, *zs, top_Hz, n_freq)
        self.make_coupled("CTL_1", 440, -150, tw["tables"]["even"], tw["tables"]["odd"],
                          tw["L"], tw["ng1"], ng2=tw["ng2"] if tw["pushpull"] else None,
                          modulating=True, fir_taps=FIR_TAPS)
        self.make_load("LOAD_A", 640, -200, *rt, top_Hz, n_freq)
        self.make_load("LOAD_B", 640, -80, *rt, top_Hz, n_freq)
        self.connect(drive, P_OUT, "SRC_A", ['port 1'])
        self.connect("SRC_A", ['port 2'], "CTL_1", ['A1'])
        self.connect("LOAD_B1", ['port 1'], "CTL_1", ['B1'])
        self.connect("CTL_1", ['A2'], "LOAD_A", ['port 1'])
        self.connect("CTL_1", ['B2'], "LOAD_B", ['port 1'])
        members = ["SRC_A", "LOAD_B1", "CTL_1", "LOAD_A", "LOAD_B"]
        outputs = [("CTL_1", port, f"to {om}", om, P_MOD) for port, om in outs]
        if not self.make_compound(COMPOUND, members, outputs):
            raise RuntimeError("the electrode Compound could not be made or its "
                               "'scattering data analysis' could not be switched on")
        if self.setp(COMPOUND, ['number of fir taps'], FIR_TAPS, required=False):
            self._fix_filter(COMPOUND)
        self.log(f"  {COMPOUND}: SRC_A -> CTL_1 (A) -> LOAD_A, LOAD_B1 -> CTL_1 (B) -> LOAD_B; "
                 f"{len(outputs)} modulation outputs, scattering data analysis on.")

    # ---------------------------------------------------------------- build
    def build_pair(self, p: dict, tw: dict, mode: str = "ena") -> str:
        p = P.normalise(p)
        sim = self.sim
        sim.new()
        sim.switchtodesign()
        sim.deleteall()
        self._wiring, self.pending_manual, self._pos = [], [], {}
        self.mode = mode
        fs_GHz = float(p["ic_sample_rate_GHz"])
        if mode == "eye":
            levels = 4 if str(p["mod_format"]).upper() == "PAM4" else 2
            need = 16 * float(p["bitrate_Gbps"]) / (1 if levels == 2 else 2)
            fs_GHz = max(fs_GHz, need)
        sim.set("sample rate", fs_GHz * 1e9)
        self.fs_GHz = fs_GHz

        outs = self._mzm("A", 100, p) + self._mzm("B", 520, p)
        if mode == "eye":
            self._add_eye_chain(p)
            self.connect('PIN_A', P_OUT, 'EYE_1', P_IN)
            self._electrode(p, tw, 'NRZ_1', outs)
            self._wire_eye_reference(p)
            self._add_far_end_eye(p)                 # EYE_2: same symbol settings
            self.connect('PIN_B', P_OUT, 'EYE_2', P_IN)
            self._wire_far_end_eye_reference()
            self._check_eye_wiring()
        else:
            q = dict(p, ic_electrode_model="TL line")
            self.read_far_end, self.diagnose = True, False
            self._add_ena(q)                          # two inputs, set before any wire
            if self.ena_inputs < 2:
                self.log("  ENA_1 would not take 2 inputs: only modulator A is read.")
            self.connect('PIN_A', P_OUT, 'ENA_1', P_IN1)
            if self.ena_inputs >= 2:
                self.connect('PIN_B', P_OUT, 'ENA_1', P_IN2)
            self._electrode(p, tw, 'ENA_1', outs)
            # the links the Compound step can drop; a duplicate is refused harmlessly
            self._try_connect('PIN_A', P_OUT[0], 'ENA_1', 'input 1')
            if self.ena_inputs >= 2:
                self._try_connect('PIN_B', P_OUT[0], 'ENA_1', 'input 2')
        kind = "push-pull" if tw["pushpull"] else "single-arm"
        self.log(f"  Crosstalk cascade: two {kind} modulators on the coupled 200 um pitch "
                 f"electrode, L = {tw['L']*1e3:.2f} mm; {len(self._wiring)} links.")
        for m in self.pending_manual:
            self.log(f"  MANUAL WIRE NEEDED: {m}")
        return f"crosstalk pair, {kind}"


# ---------------------------------------------------------------------------
def format_report(tw, meas, status, band) -> str:
    from .xtalk_test import _victim_compare
    out = []
    A = out.append
    A("Full MZM cascade, crosstalk mode: INTERCONNECT vs Python twin")
    A(f"L = {tw['L']*1e3:.3f} mm, Ze/Zo - 1 = {tw['dz']:.4g}, "
      f"{'push-pull' if tw['pushpull'] else 'single arm'}, n_g {tw['ng1']:.4f}"
      + (f" / {tw['ng2']:.4f}" if tw["pushpull"] else ""))
    A(f"band {band[0]:.1f}-{band[1]:.1f} GHz")
    for s in status:
        A(f"  {s}")
    if 1 not in meas:
        return "\n".join(out)
    f1, H1 = meas[1]
    if 2 not in meas:
        c = SL.compare_traces(tw["f_GHz"], tw["opt"]["A"], f1, H1, band)
        A(f"modulator A: max {c['max_dB']:.4f} dB, {c['max_deg']:.3f} deg; B not measured")
        return "\n".join(out)
    f2, H2 = meas[2]
    if not np.allclose(f1, f2):
        H2 = np.interp(f1, f2, H2.real) + 1j * np.interp(f1, f2, H2.imag)
    cA, v = _victim_compare(tw["f_GHz"], tw["opt"]["A"], tw["opt"]["B"], f1, H1, H2, band)
    A("")
    A(f"modulator A (aggressor): scale {cA['scale_abs']:.4f}, latency {cA['latency_ps']:.2f} ps, "
      f"max {cA['max_dB']:.4f} dB, {cA['max_deg']:.3f} deg")
    A(f"modulator B (victim), same corrections: max {v['max_dB']:.4f} dB, {v['max_deg']:.3f} deg "
      f"over {v['n']} points within 40 dB of its maximum")
    A(f"EO crosstalk B/A: ratio error max {v['ratio_dB']:.4f} dB; absolute error floor "
      f"{v['floor_dB']:.1f} dB (median {v['floor_med_dB']:.0f}) re the aggressor")
    A("")
    fq = tw["f_GHz"]
    R = tw["opt"]["B"] / tw["opt"]["A"]
    Rm = H2 / H1
    A(f"{'GHz':>5s} {'twin B/A dB':>12s} {'INTERCONNECT B/A dB':>20s}")
    for g in (10.0, 30.0, band[1]):
        i, j = int(np.argmin(abs(fq - g))), int(np.argmin(abs(f1 - g)))
        A(f"{fq[i]:5.0f} {20*np.log10(abs(R[i])):12.2f} {20*np.log10(abs(Rm[j])):20.2f}")
    A("")
    A("A pass: modulator A within a few hundredths of a dB and a few tenths of a degree,")
    A("B/A within a few tenths of a dB, and an error floor well below the crosstalk (> 30 dB).")
    return "\n".join(out)


def run_xtalk_cascade(p: dict, out_dir: Optional[str] = None, mode: str = "ena",
                      log: Optional[Callable[[str], None]] = None, keep_open: bool = False):
    """Build (and in ENA mode run and check) the two-modulator cascade.
    Returns (report, builder); builder is None unless *keep_open*."""
    log = log or print
    p = P.normalise(p)
    if int(p.get("n_bends", 0)) > 0:
        log("  NOTE: the crosstalk cascade is a straight coupled electrode of length "
            f"xt_L_mm = {float(p['xt_L_mm']):.2f} mm; the device's bends are not used.")
    out_dir = out_dir or os.path.join(str(p["out_dir"]) or ".", "xtalk_cascade")
    os.makedirs(out_dir, exist_ok=True)
    top = 0.5 * float(p["ic_sample_rate_GHz"])
    tw = twin(p, out_dir, top)
    log(f"  Tables in {out_dir}: coupled_even.txt, coupled_odd.txt, up to {top:.1f} GHz.")
    meas, status, b = {}, [], None
    try:
        b = XtalkCascadeBuilder(str(p["lumapi_path"]), hide=bool(p["ic_hide"]), log=log)
        b.build_pair(p, tw, mode=mode)
        icp = os.path.join(out_dir, f"xtalk_cascade_{mode}.icp")
        b.sim.save(icp)
        if b.pending_manual:
            status.append("saved, not run -- draw by hand: " + "; ".join(b.pending_manual))
        elif mode == "eye":
            log(f"  saved {icp}; running...")
            b.sim.run()
            status.append(f"ran; EYE_1 = modulator A, EYE_2 = modulator B (crosstalk only); "
                          f"project {icp}")
        else:
            log(f"  saved {icp}; running...")
            b.sim.run()
            for k in (1, 2):
                try:
                    f, H, *_ = b.complex_trace('ENA_1', input_port=k)
                    f, H, _ = clean_eo_trace(f, H, b.fs_GHz)
                    meas[k] = (f, H)
                except Exception as exc:
                    log(f"  ENA_1 input {k}: {exc}")
            status.append(f"ran; {len(meas)}/2 traces read; project {icp}")
    except Exception as exc:
        status.append(f"FAILED -- {type(exc).__name__}: {str(exc).strip()}")
        log("  " + traceback.format_exc().strip().splitlines()[-1])
    finally:
        if b is not None and not keep_open:
            try:
                b.close()
            except Exception:
                pass
            b = None
    band = (1.0, min(0.95 * float(p["f_max_GHz"]), float(CL.load_dataset()["data_top_GHz"])))
    rep = format_report(tw, meas, status, band)
    with open(os.path.join(out_dir, f"xtalk_cascade_{mode}_report.txt"), "w") as fh:
        fh.write(rep + "\n")
    log(rep)
    return rep, b
