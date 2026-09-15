"""
Traveling-wave Mach-Zehnder modulator modelling toolkit.

Pipeline:

    CST / VNA .s2p
         |  extractor.extract_line_fit      ABCD de-embedding + physical fits
         v
      LineFit                               intrinsic per-unit-length alpha, Zc, n_m
         |  physics.eo_response             closed-form TW transfer function (~1 ms)
         v
      EOResult  -->  sweep.run_sweep        any parameter, any metric
         |
         |  extractor.export_lumerical_tables
         v
    loss.txt / z0.txt / nm.txt / sim_params.json
         |  interconnect.InterconnectBuilder
         v
    Lumerical INTERCONNECT schematic + solver cross-check

Launch the GUI with ``python run_mzm_studio.py`` or
``python -m mzm_interconnect.cli gui``.
"""

__version__ = "1.0.0"

from . import parameters, physics  # noqa: F401
