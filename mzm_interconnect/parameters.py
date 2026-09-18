"""
Parameter registry for the TW-MZM modelling toolkit.

Every knob the model understands is declared here, exactly once. The GUI
builds its input panel from this registry, the sweep engine builds its
"what can I sweep?" menu from it, and the CLI builds its argument list from
it. Adding a new physical parameter therefore means adding one ``ParamSpec``
here plus the few lines of physics that consume it -- nothing in the GUI has
to be touched.

``affects`` tells the engine how expensive a change is:

  "extract"   -> the S-parameter de-embedding/fit must be redone (slow, ~1 s)
  "circuit"   -> only the closed-form EO transfer function is re-evaluated
                 (fast, ~1 ms) -- this is what makes sweeps interactive
  "link"      -> affects only static link metrics (Vpi, ER, chirp), not the
                 microwave bandwidth
  "lumerical" -> only used when building/running the INTERCONNECT schematic
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class ParamSpec:
    key: str
    label: str
    default: Any
    group: str
    unit: str = ""
    kind: str = "float"           # float | int | bool | choice | path | dirpath
    choices: Sequence[str] = ()
    sweepable: bool = False
    sweep_default: Optional[tuple] = None   # (start, stop, n_points)
    log_sweep: bool = False
    affects: str = "circuit"
    help: str = ""

    @property
    def display(self) -> str:
        return f"{self.label} [{self.unit}]" if self.unit else self.label


# ---------------------------------------------------------------------------
# The registry.  Order inside a group is the order shown in the GUI.
# ---------------------------------------------------------------------------
PARAMS: list[ParamSpec] = [

    # ---------------- Source data / de-embedding -------------------------
    ParamSpec("s2p_path", "Touchstone file", "", "Line under test", kind="path",
              affects="extract",
              help="CST (or lab VNA) .s2p of the bare traveling-wave electrode."),
    ParamSpec("L_meas_mm", "Length in the .s2p", 8.0, "Line under test", "mm",
              affects="extract",
              help="Physical length of the line that produced the S-parameters. "
                   "Used only to turn alpha and beta into per-unit-length quantities."),
    ParamSpec("z0_sys_ohm", "S-param reference Z0", 50.0, "Line under test", "ohm",
              affects="extract",
              help="Reference impedance of the .s2p file (almost always 50 ohm)."),
    ParamSpec("nm_model", "Microwave index model", "saturating", "Line under test",
              kind="choice", choices=("saturating", "cubic-beta"), affects="extract",
              help="How n_m(f) is extrapolated past the measured band. 'saturating' "
                   "is bounded and pins its corner inside the data. 'cubic-beta' is "
                   "the older polynomial fit, which keeps climbing outside the data "
                   "and can invent a large fake velocity mismatch -- kept only to "
                   "reproduce earlier numbers."),
    ParamSpec("f_fit_min_GHz", "Fit lower cut-off", 0.5, "Line under test", "GHz",
              affects="extract",
              help="Points below this are discarded before de-embedding; the "
                   "ABCD inversion is numerically poor near DC."),

    # ---------------- Device geometry ------------------------------------
    ParamSpec("L_target_mm", "Electrode length L", 8.0, "Device geometry", "mm",
              sweepable=True, sweep_default=(2.0, 20.0, 37), affects="circuit",
              help="Length the response is extrapolated to. Per-unit-length "
                   "physics is assumed length-invariant (true for a uniform line, "
                   "NOT true once bends or tapers are included)."),

    # ---------------- Microwave line 'what-if' knobs ---------------------
    ParamSpec("alpha_scale", "Total loss scale", 1.0, "Microwave line", "x",
              sweepable=True, sweep_default=(0.5, 2.0, 31), affects="circuit",
              help="Multiplies the whole fitted alpha(f). 1.0 = exactly what CST gave."),
    ParamSpec("alpha_skin_scale", "Conductor-loss scale", 1.0, "Microwave line", "x",
              sweepable=True, sweep_default=(0.5, 2.0, 31), affects="circuit",
              help="Scales only the sqrt(f) term: metal conductivity, plating, "
                   "thickness, surface roughness."),
    ParamSpec("alpha_diel_scale", "Dielectric-loss scale", 1.0, "Microwave line", "x",
              sweepable=True, sweep_default=(0.5, 2.0, 31), affects="circuit",
              help="Scales only the linear-f term: substrate/buffer tan(delta)."),
    ParamSpec("alpha_offset_dB_cm", "Loss offset", 0.0, "Microwave line", "dB/cm",
              sweepable=True, sweep_default=(0.0, 2.0, 21), affects="circuit",
              help="Flat excess loss added on top of the fit (bends, transitions, probes)."),
    ParamSpec("nm_offset", "Microwave index offset", 0.0, "Microwave line", "-",
              sweepable=True, sweep_default=(-0.40, 0.40, 41), affects="circuit",
              help="Adds to the fitted n_m(f). This is the velocity-matching knob: "
                   "sweep it to see how much walk-off your bandwidth can tolerate."),
    ParamSpec("zc_offset_ohm", "Impedance offset", 0.0, "Microwave line", "ohm",
              sweepable=True, sweep_default=(-15.0, 15.0, 31), affects="circuit",
              help="Adds to Re(Zc). Lets you explore impedance matching without "
                   "re-running CST."),

    # ---------------- Source / termination -------------------------------
    ParamSpec("Zs_R", "Source resistance", 50.0, "Source & termination", "ohm",
              sweepable=True, sweep_default=(10.0, 100.0, 46), affects="circuit"),
    ParamSpec("Zs_L_pH", "Source series L", 0.0, "Source & termination", "pH",
              sweepable=True, sweep_default=(0.0, 300.0, 31), affects="circuit",
              help="Bond-wire / probe-transition inductance on the drive side."),
    ParamSpec("Zs_C_fF", "Source shunt C", 0.0, "Source & termination", "fF",
              sweepable=True, sweep_default=(0.0, 200.0, 21), affects="circuit",
              help="Pad capacitance on the drive side."),
    ParamSpec("Rt_R", "Termination resistance", 40.0, "Source & termination", "ohm",
              sweepable=True, sweep_default=(10.0, 100.0, 46), affects="circuit",
              help="On-chip or off-chip load. The classic first sweep."),
    ParamSpec("Rt_L_pH", "Termination series L", 0.0, "Source & termination", "pH",
              sweepable=True, sweep_default=(0.0, 300.0, 31), affects="circuit",
              help="Parasitic inductance of the terminating resistor / its bond wire. "
                   "This is usually what kills a nominally perfect 50 ohm load above 50 GHz."),
    ParamSpec("Rt_C_fF", "Termination shunt C", 0.0, "Source & termination", "fF",
              sweepable=True, sweep_default=(0.0, 200.0, 21), affects="circuit",
              help="Pad / parasitic capacitance across the load."),

    # ---------------- Optical --------------------------------------------
    ParamSpec("ng", "Optical group index n_g", 2.27, "Optical", "-",
              sweepable=True, sweep_default=(2.00, 2.60, 31), affects="circuit",
              help="Group index of the optical mode. Together with n_m it sets walk-off."),
    ParamSpec("lambda_nm", "Wavelength", 1550.0, "Optical", "nm",
              sweepable=True, sweep_default=(1500.0, 1600.0, 21), affects="link"),
    ParamSpec("P_laser_dBm", "Laser power", 13.0, "Optical", "dBm",
              sweepable=True, sweep_default=(0.0, 20.0, 21), affects="link"),
    ParamSpec("Vpi_V", "V_pi (single arm)", 4.0, "Optical", "V",
              sweepable=True, sweep_default=(1.0, 10.0, 37), affects="link",
              help="Half-wave voltage of ONE arm at this length. The effective "
                   "device V_pi is derived from this and the drive configuration."),
    ParamSpec("drive_config", "Drive configuration", "push-pull", "Optical",
              kind="choice", choices=("push-pull", "single-arm"), affects="link",
              help="X-cut LN with G-S-G normally gives true single-drive push-pull: "
                   "the two waveguides sit in the two gaps and see opposite E-field."),
    ParamSpec("bias_phase_deg", "Bias point", 90.0, "Optical", "deg",
              sweepable=True, sweep_default=(0.0, 180.0, 37), affects="link",
              help="90 deg = quadrature."),

    # ---------------- Arm imbalance / fabrication defects -----------------
    ParamSpec("arm_loss_imbalance_dB", "Arm loss imbalance", 0.0, "Arm imbalance", "dB",
              sweepable=True, sweep_default=(0.0, 1.0, 21), affects="link",
              help="Excess propagation loss of arm 2 vs arm 1 -- e.g. asymmetric "
                   "rib over-etch. Sets the static extinction ratio."),
    ParamSpec("arm_phase_imbalance_deg", "Arm phase imbalance", 0.0, "Arm imbalance", "deg",
              sweepable=True, sweep_default=(0.0, 180.0, 37), affects="link",
              help="Static optical path-length mismatch between the arms; shifts "
                   "the bias point and makes it wavelength dependent."),
    ParamSpec("vpi_imbalance_frac", "V_pi imbalance", 0.0, "Arm imbalance", "-",
              sweepable=True, sweep_default=(0.0, 0.20, 21), affects="link",
              help="Fractional V_pi mismatch between the two arms (different overlap "
                   "integral after over-etch). Residual chirp in push-pull comes from this."),
    ParamSpec("split_err", "Splitter imbalance", 0.0, "Arm imbalance", "-",
              sweepable=True, sweep_default=(0.0, 0.10, 21), affects="link",
              help="Power split deviation from 0.5 (0.02 = 52:48). Caps the ER."),
    ParamSpec("ng_imbalance", "Group-index imbalance", 0.0, "Arm imbalance", "-",
              sweepable=True, sweep_default=(0.0, 0.02, 21), affects="link",
              help="Fractional n_g mismatch between the arms (arm 1 gets "
                   "+dn/2, arm 2 -dn/2). This is the ONLY imbalance that can "
                   "change the -3 dB bandwidth, because it is the only one "
                   "that makes the two arms see different walk-off. The other "
                   "four are frequency-flat and move the eye without moving "
                   "the bandwidth."),

    # ---------------- Eye diagram / time domain ---------------------------
    ParamSpec("bitrate_Gbps", "Bit rate", 100.0, "Eye diagram", "Gb/s",
              sweepable=True, sweep_default=(25.0, 250.0, 19), affects="link",
              help="Symbol rate is this divided by the bits per symbol "
                   "(1 for NRZ, 2 for PAM4)."),
    ParamSpec("mod_format", "Modulation format", "NRZ", "Eye diagram",
              kind="choice", choices=("NRZ", "PAM4"), affects="link"),
    ParamSpec("prbs_order", "PRBS order", 9, "Eye diagram", "-", kind="int",
              affects="link",
              help="Maximal-length LFSR of this order, so the pattern is a "
                   "genuine PRBS-N and the run lengths stress the low-frequency "
                   "response the way a real BERT does."),
    ParamSpec("drive_Vpp_V", "Drive amplitude", 2.0, "Eye diagram", "Vpp",
              sweepable=True, sweep_default=(0.5, 6.0, 23), affects="link",
              help="Peak-to-peak drive swing at the electrode input."),
    ParamSpec("drive_bw_GHz", "Driver bandwidth", 0.0, "Eye diagram", "GHz",
              sweepable=True, sweep_default=(20.0, 150.0, 27), affects="link",
              help="4th-order Bessel low-pass standing in for the driver's own "
                   "response and finite rise time. 0 means auto (0.7 x symbol "
                   "rate), which is the usual design point."),
    ParamSpec("rx_bw_GHz", "Receiver bandwidth", 0.0, "Eye diagram", "GHz",
              sweepable=True, sweep_default=(20.0, 150.0, 27), affects="link",
              help="4th-order Bessel low-pass after the photodiode. 0 means "
                   "auto (0.75 x symbol rate), the usual eye-mask convention."),
    ParamSpec("samples_per_symbol", "Samples per symbol", 32, "Eye diagram", "-",
              kind="int", affects="link"),
    ParamSpec("fibre_km", "Fibre length", 0.0, "Eye diagram", "km",
              sweepable=True, sweep_default=(0.0, 80.0, 17), affects="link",
              help="Standard single-mode fibre after the modulator. Chirp is "
                   "invisible in a back-to-back eye -- it only turns into "
                   "distortion once dispersion converts phase into amplitude, "
                   "so leave this at 0 to see the modulator alone and raise it "
                   "to make V_pi imbalance visible."),
    ParamSpec("fibre_D_ps_nm_km", "Fibre dispersion", 17.0, "Eye diagram",
              "ps/nm/km", affects="link"),
    ParamSpec("eye_noise", "Include receiver noise", True, "Eye diagram",
              kind="bool", affects="link",
              help="Shot noise on the photocurrent plus a thermal term. Turn "
                   "off for a clean look at the modulator's own distortion."),
    ParamSpec("rx_thermal_pA_rtHz", "Receiver noise density", 10.0, "Eye diagram",
              "pA/rtHz", affects="link"),
    ParamSpec("sweep_eye", "Sweep the eye too", False, "Eye diagram", kind="bool",
              affects="link",
              help="Adds the eye metrics to the Sweep tab. Off by default "
                   "because one eye costs a few hundred milliseconds against "
                   "the circuit evaluation's millisecond, so a large sweep goes "
                   "from a second to a minute."),

    # ---------------- Analysis --------------------------------------------
    ParamSpec("norm_mode", "Normalisation", "plateau", "Analysis",
              kind="choice", choices=("plateau", "point"), affects="circuit",
              help="'plateau' averages the low-frequency response over a whole "
                   "number of standing-wave periods, so the 0 dB reference does "
                   "not land on a random phase of the mismatch ripple. 'point' "
                   "anchors on a single frequency (the older behaviour, and the "
                   "usual textbook convention) -- on a mismatched line that makes "
                   "the bandwidth swing by 15 GHz depending on the frequency you "
                   "happen to pick."),
    ParamSpec("f_norm_GHz", "Anchor frequency (point mode)", 1.0, "Analysis", "GHz",
              affects="circuit",
              help="Only used when Normalisation = 'point'. 0 means DC."),
    ParamSpec("f_max_GHz", "Sweep ceiling", 150.0, "Analysis", "GHz",
              affects="circuit"),
    ParamSpec("n_points", "Frequency points", 1000, "Analysis", "-", kind="int",
              affects="circuit"),
    ParamSpec("bw_level_dB", "Bandwidth criterion", -3.0, "Analysis", "dB",
              kind="choice", choices=("-3.0", "-6.0"), affects="circuit",
              help="-3 dB = electrical (EO,e) bandwidth, the usual quote. "
                   "-6 dB on the same electrical trace = optical (EO,o) bandwidth."),
    ParamSpec("f_probe_GHz", "Probe frequency", 67.0, "Analysis", "GHz",
              sweepable=True, sweep_default=(10.0, 150.0, 29), affects="circuit",
              help="The 'EO S21 at f_probe' metric is evaluated here -- useful when "
                   "the -3 dB point runs off the top of the sweep."),

    # ---------------- Touchstone export -----------------------------------
    ParamSpec("ts_format", "Touchstone data format", "DB", "Export",
              kind="choice", choices=("DB", "MA", "RI"), affects="circuit",
              help="DB = dB magnitude + angle in degrees (matches the two plots). "
                   "MA = linear magnitude + angle. RI = real + imaginary."),
    ParamSpec("ts_ports", "Touchstone columns", "4-column", "Export",
              kind="choice", choices=("4-column", "full 2-port"), affects="circuit",
              help="'4-column' writes exactly frequency + S11 pair + EO S21 pair. "
                   "It is not a valid 2-port .s2p, so a strict Touchstone reader "
                   "(scikit-rf, ADS, CST) will reject it -- use it for numpy, "
                   "Excel or MATLAB. 'full 2-port' pads S12 and S22 with zeros so "
                   "the file parses everywhere; the EO path really is "
                   "unidirectional, so S12 = 0 is honest."),
    ParamSpec("ts_normalised", "Export normalised EO S21", True, "Export",
              kind="bool", affects="circuit",
              help="On: the EO magnitude matches the plot (0 dB at the low-frequency "
                   "reference). Off: the raw transfer function. The header records "
                   "the reference either way, so the two are interconvertible."),

    # ---------------- Lumerical -------------------------------------------
    ParamSpec("lumapi_path", "lumapi directory", r"C:\Program Files\Lumerical\v242\api\python",
              "Lumerical", kind="dirpath", affects="lumerical"),
    ParamSpec("out_dir", "Working / export folder", "", "Lumerical", kind="dirpath",
              affects="lumerical",
              help="Where loss.txt / z0.txt / nm.txt / sim_params.json / the .icp go. "
                   "Defaults to the folder holding the .s2p."),
    ParamSpec("ic_sample_rate_GHz", "Sample rate", 320.0, "Lumerical", "GHz",
              affects="lumerical"),
    ParamSpec("ic_ena_points", "ENA points", 16384, "Lumerical", "-", kind="int",
              affects="lumerical"),
    ParamSpec("ic_hide", "Run INTERCONNECT hidden", False, "Lumerical", kind="bool",
              affects="lumerical"),
]

BY_KEY: dict[str, ParamSpec] = {p.key: p for p in PARAMS}

GROUPS: list[str] = []
for _p in PARAMS:
    if _p.group not in GROUPS:
        GROUPS.append(_p.group)

SWEEPABLE: list[ParamSpec] = [p for p in PARAMS if p.sweepable]


def defaults() -> dict:
    """A fresh parameter dictionary with every registry default applied."""
    return {p.key: p.default for p in PARAMS}


def coerce(key: str, raw: Any) -> Any:
    """Turn a GUI/CLI string into the type the physics layer expects."""
    spec = BY_KEY[key]
    if spec.kind == "float":
        return float(raw)
    if spec.kind == "int":
        return int(float(raw))
    if spec.kind == "bool":
        if isinstance(raw, str):
            return raw.strip().lower() in ("1", "true", "yes", "on")
        return bool(raw)
    if spec.kind == "choice" and spec.key == "bw_level_dB":
        return float(raw)
    return raw


def normalise(params: dict) -> dict:
    """Coerce every known key of *params*, filling in missing ones."""
    out = defaults()
    for k, v in params.items():
        if k in BY_KEY:
            try:
                out[k] = coerce(k, v)
            except (TypeError, ValueError):
                pass
        else:
            out[k] = v
    return out
