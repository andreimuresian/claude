"""Exactness checks for tline.py on synthetic lines (no CST data).  Run: python test_tline.py"""
import numpy as np

from tline import C0, eo_db, eo_response, gamma_L, line_s

f = np.linspace(0.1e9, 80e9, 800)
n = 2.25
gam = (0.5 + 0.08 * np.sqrt(f / 1e9)) * 100 / 8.686 + 1j * 2 * np.pi * f * n / C0
zc = np.full(len(f), 42.0 + 0.5j)

# 1. extraction recovers gamma*L and Zc of a uniform line exactly, through
#    every half-wave resonance (2.5 mm: 26.6, 53.3, 79.9 GHz)
for L in (2.5e-3, 14e-3):
    gl, z = gamma_L(line_s(gam, zc, L, 50.0), 50.0)
    assert np.max(np.abs(gl - gam * L)) < 1e-12 and np.max(np.abs(z - zc)) < 1e-11, L

# 2. lossless, velocity- and impedance-matched line -> flat EO response
m = eo_response(f, 1j * 2 * np.pi * f * n / C0, np.full(len(f), 50.0 + 0j), 14e-3, n, 50, 50)
assert np.max(np.abs(eo_db(m))) < 1e-12

# 3. lossless, impedance-matched, velocity mismatch dn -> |sinc(pi f dn L / c)|
dn = 0.2
m = eo_response(f, 1j * 2 * np.pi * f * (n + dn) / C0, np.full(len(f), 50.0 + 0j), 14e-3, n, 50, 50)
x = np.pi * f * dn * 14e-3 / C0
ref = 20 * np.log10(np.abs(np.sinc(x / np.pi)) / np.abs(np.sinc(x[0] / np.pi)))
assert np.max(np.abs(eo_db(m) - ref)) < 1e-10

print("tline.py: all exactness checks pass")
