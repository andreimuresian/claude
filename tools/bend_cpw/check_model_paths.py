"""Regression check for mzm_interconnect.bend_cpw.model: the single-frequency
path (at_ref, used by the inverse design and the GUI's 60 GHz figures) must
equal the frequency-sweep path (evaluate on a grid) for any geometry.
(An uninitialised-array bug once made at_ref return garbage intermittently.)"""
import sys
import numpy as np
sys.path.insert(0, __file__.rsplit("/tools/", 1)[0])
from mzm_interconnect.bend_cpw import BendGeometry, line_model

rng = np.random.default_rng(7)
worst = 0.0
for _ in range(40):
    g = BendGeometry(rng.uniform(10, 70), rng.uniform(2, 15), rng.uniform(20, 100), rng.uniform(0.5, 4),
                     buf_um=rng.uniform(1, 6), sigma=rng.uniform(2e7, 5e7))
    f = rng.uniform(1, 200)
    a = line_model(g).at_ref(f)
    b = line_model(g).evaluate(np.array([f, f * 1.37, f * 0.61, f * 1.9, f * 0.3]) * 1e9)   # > 3 depths: table path
    for k, kb in (("Z0", "Z0"), ("n_m", "n_m"), ("alpha_dB_cm", "alpha_dB_cm")):
        worst = max(worst, abs(a[k] / b[kb][0] - 1))
print(f"at_ref vs evaluate, 40 random geometries/frequencies: max relative difference {worst:.2e}")
sys.exit(0 if worst < 2e-3 else 1)
