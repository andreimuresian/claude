# Checklist for TD crosstalk runs (Istanbul a-d and later)

Purpose: field-based EO crosstalk B/A from the time-domain solver, compared with lab module measurements (up to
about -20 dB). Each item: what to check, how, and why (with the evidence from the CORDOBA runs).

## Model
- [ ] **Bottom of the Si as mounted.** Conductive glue or metal under the chip: electric bottom; otherwise open.
  Why: a conductor under the Si creates the strips-vs-bottom mode (n about 3.1), which carries the 143 ps round trip
  behind the 7 GHz EO ripple (`cordoba_8mm_wide_ebottom_40dB_dense/README.md`).
- [ ] **Lateral environment as built.** Chip edge, neighbouring lines (four lines per chip) or neighbouring cells within
  the modelled width; if not modelled, record what is left out. Open lateral boundary at least 600 um from the outer
  ground (as in the widened CORDOBA). See the note at the end.
- [ ] **Si thickness, oxide, LN, metal** as in the process (Si 525 um was used; 550 was an earlier error).
- [ ] **Ports and terminations.** Excite only the physical source (line A input). Model every other termination
  (line B input with its driver output impedance, both far ends) inside the 3D model as lumped elements, so one
  excitation reproduces the lab configuration and no post-processing re-termination (which needs all ports excited) is
  needed.

## Mesh
- [ ] **Gap resolved.** At least 4-5 mesh cells across each 4.15 um gap and across the metal thickness; check in the
  mesh view at a gap. Why: the coarse Istanbul mesh gave unreliable fields (even line A could not be fitted).
- [ ] **CPW index check.** From S21 phase (or a pencil on line A's field) the CPW index must agree with an independent
  reference within 0.01 (CORDOBA: TD vs eigen 0.004-0.01). A mesh refinement step that changes B/A by more than 1 dB
  means the mesh is not converged.

## Solver
- [ ] **Accuracy -40 dB**, and the log says "Steady state energy criterion met" (not the time limit).
  Why: -27 dB left B's field 40-240 % wrong and the EO up to 18 dB wrong; -40 vs -44.5 dB agree within about 0.6 dB in
  EO above 20 GHz. Below 15 GHz -40 dB is not converged (1-2 dB in EO); state that limit or run longer if needed.
- [ ] **Once per new structure type:** compare two stopping levels (e.g. -35 and -40 dB, or -40 and -45) at a few
  monitor frequencies; B/A must change by less than about 1 dB.
- [ ] **Maximum solver duration** long enough to reach -40 dB (CORDOBA 8 mm: about 0.5 ns simulated).
- [ ] Project on a local disk (the network drive caused file locks and slowed the result write-out).

## Field monitors
- [ ] **E-field, frequency, every 1 GHz** over the band (1-60 GHz), each with **Use Subvolume** on a thin slab over the
  gaps of both lines (e.g. x 0..0.002, |y| covering both lines, z over the line). Create them with the VBA loop
  (`.UseSubvolume "True"`, `.SetSubvolume ...`); not with the broadband-monitor tool, whose 2D monitors CST 2025 ignores.
  Why 1 GHz: the EO ripple period is about 7 GHz for 8 mm; refine to 0.5 GHz only if the electrical length grows
  beyond about 15 mm (period c / ((n_opt + n_wave) L)).
- [ ] No full-volume monitors except at most one reference frequency.
- [ ] After the run, the log has no "monitor ... not supported" warning.

## Exports
- [ ] Result template "Export 3D Field Result", sweep frequency (all samples), result chosen as a specific monitor
  (e.g. `e-field (f=1) [1]`), ASCII, one template per line with prefixes `A_` / `B_`; box x 0.001, y gap range of the
  line, z full length, one common step 0.005 mm.
- [ ] Every file 1 x 9 x N points with exactly two non-zero gap columns per line.
- [ ] The s4p and the end of the solver log with the run.
- [ ] Remove stray templates from other projects (e.g. ones loading files from someone's desktop).

## Note: lateral boundary
Open (PML) absorbs everything that reaches it: it models an infinitely wide chip with nothing beside the lines. An
electric wall is not more correct: it is a perfect reflector that would trap substrate waves between walls (the
eigenmode cell modes are exactly that), unless there really is metal there. The real edge of a Si chip reflects
substantially (normal-incidence reflection about 0.55 from Si to air, total reflection at grazing angles), and
neighbouring lines both couple and scatter. Best: model the real chip edge (Si ending in air, open boundary beyond)
when its distance is known; otherwise keep open at 600+ um and run one sensitivity check (edge vs open) for the
module case.
