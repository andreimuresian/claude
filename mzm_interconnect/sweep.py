"""
Parametric sweep engine.

Because ``physics.eo_response`` is a closed-form evaluation on a numpy grid,
one sweep point costs about a millisecond. A 200-point sweep of the
termination resistance -- or a 40 x 40 map of termination against length --
therefore finishes faster than INTERCONNECT can open a project, which is the
whole point of having a validated Python twin of the schematic.

Any parameter in the registry marked ``sweepable`` can be the swept axis, and
any of the metrics below can be plotted against it. A second (series) axis is
optional and simply produces a family of curves.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

import numpy as np

from . import parameters as P
from .extractor import extract_line_fit
from .physics import LineFit, eo_response, link_metrics, link_response


# =====================================================================
# Metrics that can be plotted against the swept parameter
# =====================================================================
@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    unit: str
    help: str = ""

    @property
    def display(self) -> str:
        return f"{self.label} [{self.unit}]" if self.unit else self.label


METRICS: list[MetricSpec] = [
    MetricSpec("bw_GHz", "EO bandwidth", "GHz",
               "The -3 dB (or -6 dB) point of the normalised EO S21."),
    MetricSpec("s21_at_probe_dB", "EO S21 at probe frequency", "dB",
               "Response at the probe frequency -- stays meaningful when the "
               "-3 dB point runs off the top of the sweep."),
    MetricSpec("s11_worst_dB", "Worst electrical S11", "dB",
               "Input match of the loaded electrode over the band."),
    MetricSpec("walkoff_at_bw", "Velocity walk-off |n_m - n_g|", "-",
               "Evaluated at the bandwidth frequency."),
    MetricSpec("alpha_at_bw_dB_cm", "Microwave loss at BW", "dB/cm", ""),
    MetricSpec("vpi_eff_V", "Effective V_pi", "V",
               "Device half-wave voltage including the drive configuration."),
    MetricSpec("vpi_L_Vcm", "V_pi x L", "V.cm", ""),
    MetricSpec("er_dB", "Static extinction ratio", "dB",
               "Ceiling set by arm loss and splitter imbalance."),
    MetricSpec("chirp_alpha", "Chirp parameter", "-",
               "0 for ideal push-pull, 1 for single-arm drive."),
    MetricSpec("link_bw_GHz", "Link EO bandwidth", "GHz",
               "The -3 dB point of the whole interferometer rather than of the "
               "bare electrode. The two differ only through a group-index "
               "mismatch between the arms; every other imbalance is "
               "frequency-flat and cannot move the bandwidth."),
    MetricSpec("eye_er_dB", "Eye extinction ratio", "dB",
               "Measured on the eye, so unlike the static ER it includes "
               "intersymbol interference. Needs 'Sweep the eye too'."),
    MetricSpec("eye_q", "Eye Q factor", "-",
               "Worst sub-eye. Needs 'Sweep the eye too'."),
    MetricSpec("eye_height_mA", "Eye height", "mA",
               "Worst sub-eye, 3-sigma. Needs 'Sweep the eye too'."),
    MetricSpec("eye_oma_mA", "Optical modulation amplitude", "mA",
               "Needs 'Sweep the eye too'."),
    MetricSpec("eye_jitter_ps", "Eye jitter (rms)", "ps",
               "Needs 'Sweep the eye too'."),
]

METRIC_BY_KEY = {m.key: m for m in METRICS}


# =====================================================================
# Fit cache -- so an 'extract' sweep (e.g. over several .s2p files) does not
# refit the same file over and over.
# =====================================================================
_FIT_CACHE: dict[tuple, LineFit] = {}


def get_fit(p: dict, force: bool = False) -> LineFit:
    """Fitted line physics for *p*, memoised on the extraction inputs."""
    key = (os.path.abspath(str(p["s2p_path"])), float(p["L_meas_mm"]),
           float(p["z0_sys_ohm"]), float(p["f_fit_min_GHz"]), str(p["nm_model"]))
    if force or key not in _FIT_CACHE:
        _FIT_CACHE[key] = extract_line_fit(key[0], key[1], key[2], key[3],
                                           nm_model=key[4])
    return _FIT_CACHE[key]


def clear_fit_cache() -> None:
    _FIT_CACHE.clear()


# =====================================================================
# Evaluating one point
# =====================================================================
def evaluate_point(p: dict, fit: Optional[LineFit] = None,
                   with_eye: bool = False) -> dict:
    """
    All metrics for a single parameter set.

    The eye is optional and off by default because it costs a few hundred
    milliseconds against the circuit evaluation's ~1 ms, and a 40 x 5 sweep
    with the eye on is a minute rather than a second. Turn it on when the
    question is about the eye.
    """
    if fit is None:
        fit = get_fit(p)
    res = eo_response(fit, p)
    lm = link_metrics(p)
    i_bw = int(np.argmin(np.abs(res.f_GHz - res.bw_GHz)))
    extra = {k: float("nan") for k in
             ("eye_er_dB", "eye_q", "eye_height_mA", "eye_oma_mA", "eye_jitter_ps")}
    lk = link_response(fit, p, res)
    if with_eye:
        from .eye import simulate_eye
        ey = simulate_eye(fit, p)
        extra = {"eye_er_dB": ey.er_dB, "eye_q": ey.q_factor,
                 "eye_height_mA": ey.eye_height_A * 1e3,
                 "eye_oma_mA": ey.oma_A * 1e3, "eye_jitter_ps": ey.jitter_rms_ps}
    return {
        "link_bw_GHz": lk.bw_GHz,
        **extra,
        "bw_GHz": res.bw_GHz,
        "bw_clipped": res.bw_clipped,
        "s21_at_probe_dB": res.s21_at_probe_dB,
        "s11_worst_dB": res.s11_worst_dB,
        "walkoff_at_bw": res.walkoff_at_bw,
        "alpha_at_bw_dB_cm": float(res.alpha_dB_cm[i_bw]),
        "vpi_eff_V": lm.vpi_eff_V,
        "vpi_L_Vcm": lm.vpi_L_Vcm,
        "er_dB": lm.er_dB,
        "chirp_alpha": lm.chirp_alpha,
    }


# =====================================================================
# Sweep axes
# =====================================================================
def make_values(start: float, stop: float, n: int, log: bool = False) -> np.ndarray:
    n = max(int(n), 2)
    if log:
        if start <= 0 or stop <= 0:
            raise ValueError("A logarithmic sweep needs strictly positive limits.")
        return np.logspace(np.log10(start), np.log10(stop), n)
    return np.linspace(float(start), float(stop), n)


@dataclass
class SweepResult:
    x_key: str
    x_values: np.ndarray
    series_key: Optional[str]
    series_values: Optional[np.ndarray]
    metrics: dict                      # key -> array (n_series, n_x)
    clipped: np.ndarray                # bool array (n_series, n_x)
    base: dict = field(default_factory=dict)

    @property
    def x_label(self) -> str:
        return P.BY_KEY[self.x_key].display if self.x_key in P.BY_KEY else self.x_key

    @property
    def series_label(self) -> str:
        if not self.series_key:
            return ""
        return P.BY_KEY[self.series_key].display if self.series_key in P.BY_KEY else self.series_key

    def to_csv(self, path: str, metric_keys: Sequence[str] | None = None) -> str:
        keys = list(metric_keys or self.metrics.keys())
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            head = [self.x_label]
            if self.series_key:
                head.insert(0, self.series_label)
            head += [METRIC_BY_KEY[k].display if k in METRIC_BY_KEY else k for k in keys]
            head.append("bandwidth_clipped")
            w.writerow(head)
            n_s = self.metrics[keys[0]].shape[0]
            for si in range(n_s):
                for xi, xv in enumerate(self.x_values):
                    row = [xv]
                    if self.series_key:
                        row.insert(0, self.series_values[si])
                    row += [self.metrics[k][si, xi] for k in keys]
                    row.append(int(self.clipped[si, xi]))
                    w.writerow(row)
        return path


def run_sweep(base: dict,
              x_key: str,
              x_values: Sequence[float],
              series_key: Optional[str] = None,
              series_values: Optional[Sequence[float]] = None,
              progress: Optional[Callable[[int, int, str], None]] = None,
              cancel: Optional[Callable[[], bool]] = None) -> SweepResult:
    """
    Sweep *x_key* (and optionally *series_key*) around the *base* parameter set.

    ``progress(done, total, message)`` is called after every point so a GUI can
    drive a progress bar; ``cancel()`` is polled and, if it returns True, the
    sweep stops early and returns what it has (the remaining points are NaN).
    """
    base = P.normalise(base)
    x_values = np.asarray(x_values, dtype=float if x_key != "s2p_path" else object)
    if series_key:
        series_values = np.asarray(series_values,
                                   dtype=float if series_key != "s2p_path" else object)
    else:
        series_values = np.array([None], dtype=object)

    n_s, n_x = len(series_values), len(x_values)
    total = n_s * n_x
    metrics = {m.key: np.full((n_s, n_x), np.nan) for m in METRICS}
    clipped = np.zeros((n_s, n_x), dtype=bool)
    with_eye = bool(base.get("sweep_eye", False))

    needs_refit = (P.BY_KEY.get(x_key, None) and P.BY_KEY[x_key].affects == "extract") or \
                  (series_key and P.BY_KEY.get(series_key, None)
                   and P.BY_KEY[series_key].affects == "extract")

    fit = None if needs_refit else get_fit(base)

    done = 0
    for si, sv in enumerate(series_values):
        for xi, xv in enumerate(x_values):
            if cancel is not None and cancel():
                if progress:
                    progress(done, total, "cancelled")
                return SweepResult(x_key, x_values, series_key,
                                   None if not series_key else series_values,
                                   metrics, clipped, base)
            p = dict(base)
            p[x_key] = xv
            if series_key:
                p[series_key] = sv
            p = P.normalise(p)
            try:
                vals = evaluate_point(p, fit if not needs_refit else None,
                                      with_eye=with_eye)
                for k, arr in metrics.items():
                    arr[si, xi] = vals[k]
                clipped[si, xi] = bool(vals["bw_clipped"])
            except Exception as exc:                      # keep the sweep alive
                if progress:
                    progress(done, total, f"point {xv} failed: {exc}")
            done += 1
            if progress and (done % max(1, total // 100) == 0 or done == total):
                progress(done, total, f"{done}/{total}")

    return SweepResult(x_key, x_values, series_key,
                       None if not series_key else series_values,
                       metrics, clipped, base)


# =====================================================================
# Plot
# =====================================================================
def sweep_figure(result: SweepResult, metric_key: str, theme, figsize=(10.5, 5.2)):
    """Metric vs swept parameter, one curve per series value."""
    from matplotlib.figure import Figure

    spec = METRIC_BY_KEY.get(metric_key)
    fig = Figure(figsize=figsize, dpi=100)
    fig.patch.set_facecolor(theme["bg"])
    ax = fig.add_subplot(1, 1, 1)
    ax.set_facecolor(theme["axes"])

    y = result.metrics[metric_key]
    n_s = y.shape[0]
    cmap_colors = ["#3f7fd0", "#e2504a", "#4fae7c", "#d99b2e", "#b06bd0",
                   "#2fa8b8", "#e07b39", "#7f8fa6"]
    x = np.asarray(result.x_values, dtype=float)

    for si in range(n_s):
        color = cmap_colors[si % len(cmap_colors)]
        lbl = None
        if result.series_key:
            sv = result.series_values[si]
            lbl = f"{float(sv):g}"
        ax.plot(x, y[si], "-o", ms=3.2, lw=1.8, color=color, label=lbl)

        # mark points where the response never crossed the -3 dB level:
        # the plotted value there is a floor, not a real bandwidth.
        if metric_key == "bw_GHz" and result.clipped[si].any():
            m = result.clipped[si]
            ax.plot(x[m], y[si][m], "^", ms=7, mfc="none", mec=color, mew=1.6)

    ax.set_xlabel(result.x_label, color=theme["fg"])
    ax.set_ylabel(spec.display if spec else metric_key, color=theme["fg"])
    title = f"{spec.label if spec else metric_key} vs {P.BY_KEY[result.x_key].label}"
    ax.set_title(title, color=theme["fg"])
    ax.grid(True, alpha=0.25, color=theme["grid"])
    ax.tick_params(colors=theme["fg"], labelsize=8)
    for s in ax.spines.values():
        s.set_color(theme["grid"])

    handles, labels = ax.get_legend_handles_labels()
    if labels:
        leg = ax.legend(fontsize=8, framealpha=0.25, title=result.series_label)
        for t in leg.get_texts():
            t.set_color(theme["fg"])
        if leg.get_title():
            leg.get_title().set_color(theme["fg"])
    if metric_key == "bw_GHz" and result.clipped.any():
        ax.text(0.985, 0.03,
                "△ response never reached the criterion inside the sweep ceiling\n"
                "   (plotted value is a lower bound -- raise 'Sweep ceiling')",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=7.5, color="#e2504a")
    fig.tight_layout()
    return fig
