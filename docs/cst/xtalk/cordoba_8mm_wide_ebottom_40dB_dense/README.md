# Widened CORDOBA, electric Si bottom, accuracy -40 dB, dense field monitors
Same model as `../cordoba_8mm_wide_ebottom` (-27 dB) and `../cordoba_8mm_wide_ebottom_60dB` (stopped at -44.5 dB),
one port excited. Solver: steady-state criterion met at -40 dB (6,015,354 of 14,746,216 time steps, 8.16 pulse widths,
about 0.48 ns), OpenCL GPU solver (Quadro RTX 6000), total 11 h 56 min, finished 2026-11-05 05:58.
Field monitors: 60 E-field monitors f = 1..60 GHz (1 GHz steps), subvolume x 0..0.002, y -0.34..0.34, z 0..8 mm.

Files to place here:
* zip of the line A exports (template prefix `A_`): x 0.001, y 0.2925..0.3325, z 0..8, step 0.005, 60 frequencies;
* zip of the line B exports (prefix `B_`): x 0.001, y -0.3325..-0.2925, z 0..8, step 0.005, 60 frequencies;
* the s4p of this run;
* the end of the solver log (txt).
The zips are kept in git; they are unpacked locally for the scripts (unpacked folders not committed).
