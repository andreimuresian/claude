# Istanbul 5 mm, field monitors at 30 GHz: where NEXT comes from

Data: E and H along z at x = 1 um, y = +-0.305425 mm (centre of the inner signal-ground
gap of A and B), port 1 (A near end) driven. Script: `field_decomposition.py`.

## Checks
* Line A: forward + backward line waves fit E_y and H_x jointly to 0.9 %:
  n = 2.103 (the coarse-family value), alpha = 2.67 dB/cm, |Gamma| = 0.093.
* Field and S-parameters agree: backward wave on B at z = 0.25 mm -37.0 dB vs |S31| -37.1 dB;
  forward wave on B near the far end -48 dB vs |S41| -49.1 dB.

## Findings
1. **NEXT is built up along the whole line, not at the near end.** B's backward wave grows
   steadily from about -47 dB at the far end to -37 dB at the near end (from E_y; -45 to -39.5 dB
   from H_x).
2. **Its phase is locked to a backward-travelling wave.** No 2-beta rotation: contra-directional
   coupling from A's forward wave would turn by 2 beta L = 760 deg over 5 mm and ripple.
3. **The S-parameters say the same: NEXT is a round trip.** Group delay of S31 is 2.2-2.3 x that
   of S21 at 3, 5 and 8.75 mm, flat from 10 to 40 GHz. Slope vs length: 14.9 ps/mm against
   6.97 ps/mm for the through path, i.e. n_go + n_back = 4.48 with the CPW mode at 2.09:
   the return leg travels at n ~ 2.4.
4. **The return leg is not the CPW mode.** E_y and H_x on B do not decompose consistently into
   line waves (34 % residual with A's wave impedance); one extra backward wave with n ~ 2.39
   brings it to 8 %. On the uniform 200 um pitch line the port solver found the "whole line
   against the frame" modes at n = 2.33-2.41 (field in the Si, at the outer ground edges); the
   Istanbul lines with floating 30 um grounds support the same family.

## Interpretation (to be confirmed)
A's forward CPW wave reaches the far end, where part of it is turned into the slower
common-mode-type wave (n ~ 2.4) travelling back. Over the return trip this wave and the CPW modes
slip by (2.4 - 2.1) k0 per mm, which transfers energy steadily onto B's CPW mode (same mechanism as
FEXT, with a split of ~0.3 instead of ~0.01). Both legs travel in the same direction as the waves
they exchange energy with, so there is no 2-beta mismatch and no ripple; the coherence length
pi / dbeta is ~17 mm at 30 GHz, so the growth stays ~linear per leg up to ~8 mm and flattens at
higher f and L (8.75 mm sits 4 dB under L^2).

## Open
* What terminates this wave at the ports (number of modes per waveguide port): an
  undeclared propagating mode is reflected by a CST waveguide port.
* Direct evidence of the n ~ 2.4 wave: E along z at y = 0 (midway between the lines), where the
  CPW modes are weak.
* w = 2 mm run (lateral boundary).
