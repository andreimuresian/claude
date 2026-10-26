# Field planes at 30 and 60 GHz (5 mm, w = 1 mm): EO crosstalk reference and wave content

Export: E at x = 1 um, y -0.40..0.40, z -0.04..5.04, step 5 um, port 1 (A near end) driven.
(Raw export 24 MB, not stored; gap fields in gapV.npz.)

## EO crosstalk from the fields (push-pull, ports 50 ohm as simulated)
| n_g | CST fields | s4p, Ze = Zo | s4p, exact terminals |
|---|---|---|---|
| 2.00 | -57.8 dB | -52.1 dB | -32.6 dB |
| 2.27 | -56.3 dB | -52.3 dB | -33.2 dB |
| 2.40 | -55.0 dB | -52.3 dB | -33.4 dB |

60 GHz (gapV60.npz):

| n_g | CST fields | s4p, Ze = Zo | s4p, exact terminals |
|---|---|---|---|
| 2.00 | -38.1 dB | -42.4 dB | -36.9 dB |
| 2.27 | -38.0 dB | -42.5 dB | -35.9 dB |
| 2.40 | -37.5 dB | -42.2 dB | -35.4 dB |

* 30 GHz: 'exact terminals' overstates by ~23 dB, 'Ze = Zo' by ~4-5 dB.
* 60 GHz: 'Ze = Zo' understates by ~4.5 dB, 'exact terminals' overstates by ~2 dB.
* Neither equivalent line is accurate or conservative across frequency: from the s4p alone the
  EO crosstalk is known to about +-5 dB (Ze = Zo).
* B's common gap field (cancels in push-pull) is 21 % of the differential one at 30 GHz, 46 % at
  60 GHz; a single inner-gap arm sees -51 dB (30 GHz) and -39..-40 dB (60 GHz).
* On B, the common gap field (same in both gaps) is 21 % of the differential one (A: 0.3 %). It
  comes from the extra waves and cancels in push-pull: a single inner-gap arm would see -51 dB.

## Wave content (not final)
Matrix pencil and constrained fits over the plane (mmp.py, sect.py, vp.py): besides the line
modes (n = 2.08-2.10 in the gaps), waves with n ~ 2.4-2.7 travel in both directions, in both the
mirror-even and the mirror-odd parts of the field, dominant outside the gaps and at 10-14 % in
the gaps. Their amplitudes vary along z (fitted 'losses' of -30..+15 dB/cm), so they are not
single clean modes over the plane; an exact count needs more work (end fields and radiation in
the weak region between the lines).
