# Istanbul 5 mm (w = 1 mm) -- E field in the signal-ground gaps, for the field-based EO crosstalk

Source run: `TEST0_XTALK_SW_5mm.s4p` (same model). One pair of files per monitor frequency f (GHz)
and excited port p:

    e-field_f<f>_<p>_A.txt    line A: x = 0.001, y = 0.305 ... 0.320, z = 0 ... 5, step 0.005
    e-field_f<f>_<p>_B.txt    line B: x = 0.001, y = -0.320 ... -0.305, z = 0 ... 5, step 0.005

CST "3D Export in Volume", Use Subvolume, ASCII, E field, monitor `e-field (f=<f>) [<p>]`.
y = +-0.305 and +-0.320 are inside the signal-ground gaps; y = +-0.310, +-0.315 are inside the
signal metal (zero field). The f = 10, 20, 30, 45, 60, 80 GHz, port 1 files were cut from the
full-plane exports (y -0.40..0.40) and have the same grid and format.

Present: port 1 at 10-80 GHz in 5 GHz steps (15 frequencies); port 2 at 30 GHz, which matches
port 1 reversed in z to 1e-4 (ratio 1.0000, 0.00 deg), so every port follows from port 1 by
symmetry. Used by mzm_interconnect/xtalk_fields.py (GUI: Crosstalk from s4p, 'Field monitor
folder').
