"""
Lumerical INTERCONNECT schematic builder and runner.

This is the former MZM_API_launcher, turned into something the GUI can call:
it takes the same normalised parameter dictionary the Python model uses, plus
the exported table files, and builds the schematic. Nothing here is imported
unless the user actually asks for INTERCONNECT, so the rest of the toolkit
runs fine on a machine with no Lumerical installation.

Two topologies are available:

  "single-arm"  one driven arm + a static phase shifter in the other.
                This is the historically validated build.

  "push-pull"   both arms modulated from the same traveling-wave electrode
                with opposite-sign phase coefficients, which is what an X-cut
                LN G-S-G device physically does. The microwave response is
                identical; V_pi halves and the chirp goes to zero.

If the INTERCONNECT build in use will not fan one electrical output out to two
modulation ports, the builder falls back to a single modulator carrying the
summed efficiency. That reproduces the same |S21| and the same effective
V_pi -- only the chirp/spectral asymmetry is lost -- and it says so loudly in
the log rather than silently building something different.
"""

from __future__ import annotations

import os
import sys
from typing import Callable, Optional, Sequence

import numpy as np

from . import parameters as P
from .physics import rlc_impedance


class LumericalUnavailable(RuntimeError):
    pass


def load_lumapi(lumapi_path: str):
    """Import lumapi from an explicit install directory."""
    if lumapi_path and os.path.isdir(lumapi_path) and lumapi_path not in sys.path:
        sys.path.insert(0, lumapi_path)
    try:
        import lumapi                                   # noqa: F401
        return lumapi
    except Exception as exc:                            # pragma: no cover
        raise LumericalUnavailable(
            f"Could not import lumapi from '{lumapi_path}'. Point the "
            f"'lumapi directory' field at e.g. "
            f"C:\\Program Files\\Lumerical\\v242\\api\\python  ({exc})") from exc


KNOWN_ENA_RESULTS = ['input 1/S21', 'input 1/transmission', 'input 1/gain',
                     'S21', 'transmission', 'gain', 'ENA_1', 'model']


class InterconnectBuilder:
    """Builds, runs and reads back a traveling-wave MZM schematic."""

    def __init__(self, lumapi_path: str, hide: bool = False,
                 log: Optional[Callable[[str], None]] = None):
        self.log = log or (lambda m: print(m))
        self._lumapi = load_lumapi(lumapi_path)
        self.sim = self._lumapi.INTERCONNECT(hide=bool(hide))
        self.topology = None

    # ---------------- low level helpers (from the original launcher) ----
    def setp(self, el, candidates, value, required=True):
        for c in candidates:
            try:
                self.sim.setnamed(el, c, value)
                return True
            except Exception:
                continue
        if required:
            raise KeyError(f"{el}: none of {candidates} accepted")
        return False

    def add(self, candidates, name, x, y):
        for c in candidates:
            try:
                el = self.sim.addelement(c)
                if el.name != name:          # skip the no-op rename that spams warnings
                    el.name = name
                el.x_position = x
                el.y_position = y
                return el
            except Exception:
                continue
        raise RuntimeError(f"Cannot add {name} from {candidates}")

    def _try_connect(self, *args) -> bool:
        try:
            self.sim.connect(*args)
            return True
        except Exception:
            return False

    # ---------------- build --------------------------------------------
    def build(self, p: dict, files: dict) -> str:
        """
        Build the whole schematic from a normalised parameter dict and the
        loss/z0/nm table paths produced by ``extractor.export_lumerical_tables``.
        Returns the topology actually built.
        """
        p = P.normalise(p)
        sim = self.sim
        sim.new()
        sim.switchtodesign()
        sim.deleteall()
        sim.set("sample rate", float(p["ic_sample_rate_GHz"]) * 1e9)

        f_opt = 299792458.0 / (float(p["lambda_nm"]) * 1e-9)
        want_pp = str(p["drive_config"]) == "push-pull"

        # ---- 1. optical source ----
        self.add(['CW Laser'], 'CWL_1', 115, 195)
        self.setp('CWL_1', ['frequency'], f_opt)
        self.setp('CWL_1', ['power'], 10 ** (float(p["P_laser_dBm"]) / 10) / 1000)
        self.setp('CWL_1', ['linewidth'], 0)
        self.setp('CWL_1', ['enable RIN', 'RIN enable'], False, required=False)
        self.setp('CWL_1', ['linewidth distribution', 'linewidth_distribution'],
                  'Lorentzian', required=False)

        # ---- 2. splitter / combiner ----
        self.add(['Optical Splitter', 'Optical Splitter/Coupler'], 'SPLT_1', 280, 195)
        self.setp('SPLT_1', ['configuration'], 'splitter', required=False)
        self.setp('SPLT_1', ['number of ports', 'number of output ports'], 2, required=False)
        self.setp('SPLT_1', ['split ratio'], 'even')

        self.add(['Optical Combiner', 'Optical Splitter/Coupler', 'Optical Splitter'],
                 'SPLT_2', 780, 210)
        self.setp('SPLT_2', ['configuration'], 'combiner', required=False)
        self.setp('SPLT_2', ['number of ports', 'number of input ports'], 2, required=False)
        self.setp('SPLT_2', ['split ratio'], 'even')

        # ---- 3. bias / static arm-phase error ----
        phase_rad = np.deg2rad(float(p["bias_phase_deg"]) + float(p["arm_phase_imbalance_deg"]))
        self.add(['Optical Phase Shift'], 'PHS_1', 640, 285)
        self.setp('PHS_1', ['input parameter'], 'constant', required=False)
        self.setp('PHS_1', ['phase shift'], float(phase_rad))

        # ---- 4. arm-2 excess loss (asymmetric over-etch) ----
        d_loss = float(p["arm_loss_imbalance_dB"])
        self.has_attenuator = False
        if d_loss > 0:
            try:
                self.add(['Optical Attenuator'], 'ATT_1', 730, 285)
                self.setp('ATT_1', ['attenuation'], d_loss)
                self.has_attenuator = True
            except Exception as exc:
                self.log(f"  arm-2 attenuator not available ({exc}); "
                         f"loss imbalance applied in the Python model only.")

        # ---- 5. modulator(s) ----
        L_OM = 1e-6
        vpi = float(p["Vpi_V"])
        d = float(p["vpi_imbalance_frac"])

        def add_modulator(name, x, y, coeff):
            self.add(['Optical Modulator Measured', 'Optical Modulator (Measured)'], name, x, y)
            self.setp(name, ['configuration'], 'bidirectional')
            self.setp(name, ['length'], L_OM)
            self.setp(name, ['electrode type'], 'lumped')
            self.setp(name, ['input parameter'], 'coefficients')
            self.setp(name, ['phase coefficient c', 'c'], coeff)
            for k in ('a', 'b', 'd'):
                self.setp(name, [f'phase coefficient {k}', k], 0.0, required=False)
            for k in ('a', 'b', 'c', 'd'):
                self.setp(name, [f'absorption coefficient {k}', f'absorption {k}'],
                          0.0, required=False)

        c1 = -np.pi / (vpi * L_OM)
        c2 = +np.pi / (vpi * (1.0 + d) * L_OM)

        # ---- 6. traveling-wave electrode ----
        self.add(['Traveling Wave Electrode'], 'TW_1', 420, -45)
        self.setp('TW_1', ['length'], float(p["L_target_mm"]) * 1e-3)
        self.setp('TW_1', ['optical index'], float(p["ng"]))
        self.setp('TW_1', ['transfer function'], 'modulation voltage')

        nm_ok = (self.setp('TW_1', ['microwave index type'], 'table', required=False) and
                 self.setp('TW_1', ['load microwave index from file',
                                    'microwave index from file'], True, required=False) and
                 self.setp('TW_1', ['microwave index filename', 'microwave index file'],
                           files["nm"], required=False))
        if nm_ok:
            self.log("  TW_1: dispersive n_m(f) table loaded from nm.txt")
        else:
            nm60 = float(np.loadtxt(files["nm"], comments='#')[:, 1].mean())
            self.setp('TW_1', ['microwave index type'], 'constant')
            self.setp('TW_1', ['microwave index'], nm60)
            self.log(f"  TW_1: n_m table unsupported -> constant n_m = {nm60:.4f}")

        self.setp('TW_1', ['loss type'], 'table')
        self.setp('TW_1', ['load loss from file', 'loss from file'], True)
        self.setp('TW_1', ['loss filename', 'loss file'], files["loss"])
        self.setp('TW_1', ['characteristic impedance type'], 'table')
        self.setp('TW_1', ['load characteristic impedance from file',
                           'characteristic impedance from file'], True)
        self.setp('TW_1', ['characteristic impedance filename',
                           'characteristic impedance file'], files["z0"])

        # INTERCONNECT takes a single constant reactance, so any L/C parasitic
        # is collapsed to its value at the probe frequency. The Python model
        # keeps the full frequency dependence -- expect the two to diverge if
        # you push the parasitics hard.
        f_probe = float(p["f_probe_GHz"])
        zs = complex(rlc_impedance(np.array([f_probe]), float(p["Zs_R"]),
                                   float(p["Zs_L_pH"]), float(p["Zs_C_fF"]))[0])
        zt = complex(rlc_impedance(np.array([f_probe]), float(p["Rt_R"]),
                                   float(p["Rt_L_pH"]), float(p["Rt_C_fF"]))[0])
        self.setp('TW_1', ['source resistance'], float(np.real(zs)))
        self.setp('TW_1', ['source reactance'], float(np.imag(zs)))
        self.setp('TW_1', ['terminating resistance'], float(np.real(zt)))
        self.setp('TW_1', ['terminating reactance'], float(np.imag(zt)))
        if abs(np.imag(zs)) > 1e-9 or abs(np.imag(zt)) > 1e-9:
            self.log(f"  NOTE: source/load reactance frozen at {f_probe:.1f} GHz "
                     f"(Xs={np.imag(zs):+.2f}, Xt={np.imag(zt):+.2f} ohm). "
                     f"INTERCONNECT has no frequency-dependent termination.")
        self.setp('TW_1', ['junction capacitance', 'constant junction capacitance'],
                  0, required=False)
        self.setp('TW_1', ['junction resistance', 'constant junction resistance'],
                  0, required=False)

        # ---- 7. detector ----
        self.add(['PIN Photodetector', 'Photodetector'], 'PIN_1', 950, 210)
        self.setp('PIN_1', ['responsivity'], 1)
        self.setp('PIN_1', ['frequency at max power'], False, required=False)
        self.setp('PIN_1', ['frequency'], f_opt, required=False)
        for q in ('thermal noise', 'shot noise', 'power saturation'):
            self.setp('PIN_1', [f'enable {q}', f'{q} enable'], False, required=False)

        # ---- 8. network analyser ----
        self.add(['Network Analyzer'], 'ENA_1', 340, -350)
        self.setp('ENA_1', ['analysis type'], 'impulse response')
        self.setp('ENA_1', ['signal source', 'source'], 'internal', required=False)
        self.setp('ENA_1', ['source kind', 'kind'], 'power', required=False)
        self.setp('ENA_1', ['power', 'source power'], 0.001, required=False)
        self.setp('ENA_1', ['input parameter'], 'start and stop', required=False)
        self.setp('ENA_1', ['start frequency'], 0, required=False)
        self.setp('ENA_1', ['stop frequency'], float(p["f_max_GHz"]) * 1e9, required=False)
        self.setp('ENA_1', ['number of points', 'number of frequency points'],
                  int(p["ic_ena_points"]), required=False)
        self.setp('ENA_1', ['remove dc', 'remove DC'], True, required=False)
        self.setp('ENA_1', ['peak analysis', 'peak_analysis'], 'disable', required=False)

        # ---- 9. optical wiring ----
        sim.connect('CWL_1', 'output', 'SPLT_1', 'input')
        sim.connect('PIN_1', 'output', 'ENA_1', 'input 1')
        sim.connect('ENA_1', 'output', 'TW_1', 'input')
        sim.connect('SPLT_2', 'output', 'PIN_1', 'input')

        if want_pp:
            add_modulator('OM_1', 560, 120, c1)
            add_modulator('OM_2', 560, 300, c2)
            sim.connect('SPLT_1', 'output 1', 'OM_1', 'port 1')
            sim.connect('OM_1', 'port 2', 'SPLT_2', 'input 1')
            sim.connect('SPLT_1', 'output 2', 'OM_2', 'port 1')
            sim.connect('OM_2', 'port 2', 'PHS_1', 'port 1')
            tail = self._wire_arm2_tail()
            sim.connect(*tail, 'SPLT_2', 'input 2')

            ok = (self._try_connect('TW_1', 'output', 'OM_1', 'modulation') and
                  self._try_connect('TW_1', 'output', 'OM_2', 'modulation'))
            if ok:
                self.topology = "push-pull"
                self.log("  Topology: TRUE PUSH-PULL -- one electrode driving both arms "
                         "with opposite-sign phase coefficients.")
            else:
                self.log("  This INTERCONNECT build will not fan one electrical output "
                         "out to two modulation ports.")
                self.topology = self._rebuild_lumped_pushpull(p, c1, c2, L_OM)
        else:
            add_modulator('OM_1', 560, 120, c1)
            sim.connect('SPLT_1', 'output 1', 'OM_1', 'port 1')
            sim.connect('OM_1', 'port 2', 'SPLT_2', 'input 1')
            sim.connect('SPLT_1', 'output 2', 'PHS_1', 'port 1')
            tail = self._wire_arm2_tail()
            sim.connect(*tail, 'SPLT_2', 'input 2')
            sim.connect('TW_1', 'output', 'OM_1', 'modulation')
            self.topology = "single-arm"
            self.log("  Topology: SINGLE-ARM drive (one modulated arm, static phase in "
                     "the other). Chirp parameter = 1, V_pi is the full single-arm V_pi.")

        return self.topology

    def _wire_arm2_tail(self):
        """Insert the arm-2 attenuator if present; return the element/port feeding
        the combiner."""
        if self.has_attenuator:
            self.sim.connect('PHS_1', 'port 2', 'ATT_1', 'input')
            return ('ATT_1', 'output')
        return ('PHS_1', 'port 2')

    def _rebuild_lumped_pushpull(self, p, c1, c2, L_OM) -> str:
        """
        Fallback: collapse push-pull onto the single driven modulator by summing
        the two arms' efficiencies. |S21| and V_pi_eff are preserved exactly;
        the chirp asymmetry is not represented.
        """
        sim = self.sim
        try:
            sim.deleteelement('OM_2')
        except Exception:
            pass
        c_eff = c1 - c2                      # |c1| + |c2| since the signs oppose
        self.setp('OM_1', ['phase coefficient c', 'c'], c_eff)
        sim.connect('SPLT_1', 'output 2', 'PHS_1', 'port 1')
        sim.connect('TW_1', 'output', 'OM_1', 'modulation')
        self.log(f"  Falling back to a LUMPED push-pull equivalent: one modulator with "
                 f"c = {c_eff:.4g} (= |c1|+|c2|). Same EO |S21| and same effective V_pi "
                 f"({1.0 / abs(c_eff) * np.pi / L_OM:.3f} V); chirp is NOT modelled.")
        return "push-pull (lumped equivalent)"

    # ---------------- run & read back -----------------------------------
    def run(self, save_path: Optional[str] = None):
        self.log("  Running impulse-response sweep in INTERCONNECT...")
        self.sim.run()
        if save_path:
            self.sim.save(save_path)
            self.log(f"  Project saved: {save_path}")

    def close(self):
        try:
            self.sim.close()
        except Exception:
            pass

    # -- the original launcher's robust ENA dataset probing, kept verbatim
    #    in behaviour but quieter and returning data instead of printing it.
    @staticmethod
    def _collect_datasets(res, prefix=''):
        out = []
        if not isinstance(res, dict):
            return out
        f = None
        for k, v in res.items():
            if k.lower() in ('f', 'frequency', 'freq'):
                f = np.asarray(v, dtype=float).ravel()
                break
        for k, v in res.items():
            if k.lower() in ('f', 'frequency', 'freq'):
                continue
            if isinstance(v, dict):
                out += InterconnectBuilder._collect_datasets(v, prefix=f"{prefix}{k}/")
                continue
            if f is None:
                continue
            try:
                d = np.asarray(v, dtype=complex).ravel()
            except Exception:
                continue
            if d.size == f.size:
                out.append((f"{prefix}{k}", f, d))
        return out

    def ena_trace(self, p: dict, element: str = 'ENA_1'):
        """
        Returns (f_GHz, S21_normalised_dB, bw_GHz).

        The ENA exposes several similarly-named datasets depending on version;
        this probes all of them and picks the one that actually rolls off,
        exactly as the original launcher did.
        """
        f_norm = float(p["f_norm_GHz"]) * 1e9
        level = float(p["bw_level_dB"])

        cands = []
        try:
            cands += [str(n) for n in self.sim.getresultnames(element)]
        except Exception:
            pass
        for n in KNOWN_ENA_RESULTS:
            if n not in cands:
                cands.append(n)

        rows, seen = [], set()
        for n in cands:
            try:
                res = self.sim.getresult(element, n)
            except Exception:
                continue
            for label, f, d in self._collect_datasets(res):
                if label in seen:
                    continue
                seen.add(label)
                is_real = np.allclose(d.imag, 0.0, atol=1e-12)
                interps = [('dB', d.real)] if is_real else []
                mag = np.abs(d)
                mag[mag == 0] = 1e-300
                interps.append(('lin', 20 * np.log10(mag)))
                for tag, s_dB in interps:
                    i0 = int(np.argmin(np.abs(f - f_norm)))
                    s = s_dB - s_dB[i0]
                    below = np.where(s <= level)[0]
                    bw = None
                    if below.size:
                        i = below[0]
                        if i > 0:
                            f1, f2 = f[i - 1] / 1e9, f[i] / 1e9
                            bw = f1 + (f2 - f1) * (level - s[i - 1]) / (s[i] - s[i - 1])
                        else:
                            bw = f[0] / 1e9
                    rows.append({'label': f"{label} [{tag}]", 'f': f, 's': s,
                                 'bw': bw, 'min': float(s.min())})

        if not rows:
            raise RuntimeError(f"No frequency-domain dataset could be read from {element}.")

        f_max_GHz = rows[0]['f'][-1] / 1e9
        crossing = [r for r in rows if r['bw'] is not None and r['bw'] < f_max_GHz - 1.0]
        best = min(crossing, key=lambda r: r['min']) if crossing else min(rows, key=lambda r: r['min'])
        self.log(f"  ENA dataset selected: {best['label']}")
        return best['f'] / 1e9, best['s'], (best['bw'] if best['bw'] else f_max_GHz)


# ---------------------------------------------------------------------------
# Parameters that can also be swept on the INTERCONNECT side (spot checks)
# ---------------------------------------------------------------------------
LUMERICAL_SWEEPABLE = {
    "Rt_R": ('TW_1', ['terminating resistance'], lambda v: float(v)),
    "Zs_R": ('TW_1', ['source resistance'], lambda v: float(v)),
    "L_target_mm": ('TW_1', ['length'], lambda v: float(v) * 1e-3),
    "ng": ('TW_1', ['optical index'], lambda v: float(v)),
    "Vpi_V": (None, None, None),     # handled by rebuilding the coefficient
}


def verify_points(builder: InterconnectBuilder, p: dict, key: str,
                  values: Sequence[float],
                  progress: Optional[Callable[[int, int, str], None]] = None) -> dict:
    """
    Re-run INTERCONNECT at a handful of points of an already-built schematic so
    the fast Python sweep can be spot-checked against the solver.

    Only properties that map onto an existing element property are supported;
    anything else would need a full rebuild and is better done in Python.
    """
    if key not in LUMERICAL_SWEEPABLE or LUMERICAL_SWEEPABLE[key][0] is None:
        raise ValueError(f"'{key}' cannot be re-swept in place; it needs a rebuild.")
    element, props, conv = LUMERICAL_SWEEPABLE[key]
    out = {"values": list(values), "bw_GHz": []}
    for i, v in enumerate(values):
        builder.sim.switchtodesign()
        builder.setp(element, props, conv(v))
        builder.run()
        _, _, bw = builder.ena_trace(p)
        out["bw_GHz"].append(float(bw))
        if progress:
            progress(i + 1, len(values), f"{key} = {v:g} -> {bw:.2f} GHz")
    return out
