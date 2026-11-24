# DEEP RESEARCH BRIEF — Lowering Vπ·L of an X-cut thin-film lithium niobate (TFLN) modulator at fixed gap, with geometry only

## 1. RESEARCH QUESTION
Which **geometric strategies** (placement and shape of materials we already use: LiNbO3, SiO2, Au, optionally Al) can reduce the push-pull half-wave-voltage–length product **Vπ·L of our TFLN Mach-Zehnder modulator from ≈1.85 V·cm to ≈1.6 V·cm at λ = 1625 nm**, while keeping the electrode gap ≥ 3.2 µm and the optical insertion loss comfortably below 0.5 dB/cm?

## 2. DECISION / OUTCOME AND AUDIENCE
- The research supports a **tapeout decision due in about two weeks**. Its output is a short list of 2–4 cross-section modifications that our team will then verify with our own FEM simulations (femwell: 2D optical mode solver plus anisotropic electrostatics).
- Audience: photonic integrated-circuit engineers who are expert in TFLN modulator physics and FEM simulation. Do not explain basic electro-optics. Focus on what has been demonstrated or rigorously simulated, by how much it helped, and under which conditions.
- A strategy is only useful if it can plausibly be fabricated with our **existing materials and process steps** in the short term.

## 3. CURRENT DESIGN (baseline "Madrid B") — full context

**Platform and waveguide**
- X-cut LiNbO3 thin film on SiO2 BOX (4.7 µm). TE mode; the field is along the crystal z-axis, so the modulator uses r33 (30.8 pm/V).
- LN film thickness (TECN): 550 nm. Rib etch depth: 275 nm. Remaining slab: 275 nm, continuous and unetched across the whole device.
- Rib top width 1.4 µm, multimode, chosen deliberately. Sidewall angle 60°, so the rib base is about 1.72 µm.

**Materials and properties**
- LN (Zelmon 1997 Sellmeier) at 1625 nm: ne ≈ 2.13, no ≈ 2.21. DC relative permittivity: ε along the in-plane horizontal axis (crystal z) = 28; ε along the vertical axis = 44.
- SiO2 (Malitson): n ≈ 1.444, DC ε ≈ 3.75.
- Au (Johnson & Christy): n ≈ 0.56 + 11.2i at 1625 nm.
- Al: available in the process only as a 400 nm first metal layer; n ≈ 1.55 + 16i (literature value).

**Electrodes**
- Coplanar gold electrodes, push-pull. Vπ·L is quoted for push-pull: Vπ·L = G·λ / (2·r33·ne³·Γ).
- Au is 2 µm thick and 30 µm wide. It sits on a **120 nm SiO2 buffer** that covers the slab, so the gold never touches the LN.
- Electrode gap G = 3.2 µm, edge to edge.
- An SiO2 cap covers the rib inside the gap: width G − 0.2 µm = 3.0 µm, height 0.5 µm. The cladding above is air.

**Performance at 1625 nm**
- Vπ·L = 1.854 V·cm; optical overlap Γ ≈ 0.47; metal-induced IL = 0.21 dB/cm.

**Reference design "Madrid A"** (gap 3.5 µm, 40 nm ALD Al2O3, same stack otherwise): 1.89 V·cm, 0.19 dB/cm. ALD is now **excluded** because the process is immature.

## 4. HARD CONSTRAINTS (exclude any strategy that violates one; mention it only in an "excluded" appendix)
1. **Electrode gap ≥ 3.2 µm.** This is the minimum metal-to-metal distance at any height. Strategies whose benefit comes from simply narrowing the gap do not count.
2. **Wavelength 1625 nm.** When quoting literature values taken at 1550 nm or 1310 nm, rescale Vπ·L by λ (multiply 1550 nm values by about 1.05). State whether each value is push-pull or single-arm, and normalise to push-pull.
3. **No new materials.** Only LiNbO3, SiO2 (buffer, cap, cladding), Au, and Al as the 400 nm first metal. Excluded: high-k claddings (Ta2O5, HfO2, TiO2, SiN, BTO, glycerol, liquid crystals), ALD alumina, polymers or BCB, doped or transparent conductors, silicon or other hybrid layers.
4. **LN film 550 nm and etch 275 nm are fixed.** Changes to rib width are acceptable only with a strong quantitative justification; 1.4 µm is preferred.
5. **Metal must not touch the LN directly** (minimum SiO2 buffer about 100 nm). Our simulations show that Au, Al or Ti directly on LN couples the mode to surface plasmons at the metal–LN interface, producing 1–60 dB/cm loss.
6. **Gold cannot be buried under SiO2** according to our process engineers. Oxide inside the gap is acceptable; oxide covering the gold top is not.
7. **IL target ≤ 0.3 dB/cm** (hard limit 0.5 dB/cm), metal absorption only, at 1625 nm.
8. Fabrication must be compatible with standard UV lithography and gold electroplating. Our process has up to three metal levels: Al 400 nm, Au 2 µm, Au 10 µm.

## 5. WHAT WE HAVE ALREADY TESTED IN SIMULATION (do not re-propose without new evidence; use it to interpret the literature)
- **Gap 3.5→5.0 µm and buffer 100–200 nm sweeps:** Vπ·L rises by about 0.053 V·cm per 0.1 µm of gap. IL falls by about ÷1.35 per 0.1 µm of gap. A thicker buffer costs Vπ and lowers IL.
- **Buffer below the ~33 nm slab cutoff:** huge IL from a resonance with the metal.
- **Cap width (gap − 0.2 vs gap − 1.0 µm) and cap height:** air pockets between cap and metal raise Vπ·L.
- **Tall signal (10 µm) / thin ground (0.3–2 µm):** Vπ·L changes by about 2 %.
- **Overhang ground** (a gold step reaching closer above the cap): helps only by effectively reducing the gap.
- **Etched (lifted) slab ending near the electrodes ("Lisboa"):** lateral standing waves at **vertical material interfaces** (oxide–gold, oxide–LN, LN–gold) cause strong IL ripples versus geometry. We therefore avoid vertical interfaces within reach of the slab mode.
- **Ti or Al strips directly on the slab under the gold:** plasmonic loss and strip resonances. Rejected.
- **Full SiO2 top cladding burying the gold:** −7 % Vπ·L but IL ×2. At equal IL the gain is about 1 %. Also not manufacturable (constraint 6).
- **Tri-galvanic buffered stack** (400 nm Al electrode edge defining the gap, cap the same width as the Al gap, Al protrusions buried in oxide): no standing wave, but about 5 % worse than Madrid B at equal IL.

## 6. SCOPE
- **Include:** electrode cross-section geometry (shape, height profile, steps, L/T/inverted-L shapes, electrodes partly raised or recessed relative to the rib, multi-level electrodes); placement and shape of SiO2 (cap shape and height, filling the gap up to the electrode top, partial fills, trenches in the buffer); optimal vertical and horizontal position of the optical mode relative to the field maximum; electrode configurations that increase the horizontal field in the rib at fixed gap; geometric means to reduce metal loss so that a thinner buffer can be used; rib-width effects on Γ at fixed gap; any analytical or scaling result for Γ versus geometry in X-cut TFLN.
- **Include as a secondary topic:** RF consequences of each geometry (impedance, microwave index, velocity matching, RF loss), but only to flag show-stoppers.
- **Exclude:** new materials, gap reduction below 3.2 µm, z-cut or y-cut platforms, different film thickness, slow-light or resonant schemes that lower Vπ without lowering Vπ·L, and folded or longer layouts (we know Vπ = Vπ·L / L; we want Vπ·L).
- **Timeframe:** prefer 2018–present (the modern TFLN era). Older bulk-LN or Ti-diffused work only where the geometric principle transfers.

## 7. SOURCE STRATEGY
1. Peer-reviewed journals and conferences: Optica, Nature/Nature Photonics/Nature Communications, Optics Express, Optics Letters, JLT, PTL, Photonics Research, Laser Photonics Reviews, APL Photonics, CLEO, OFC, ECOC.
2. arXiv preprints, labelled as not peer-reviewed.
3. Patents (USPTO, EPO, WIPO) for electrode and cladding geometries, especially from HyperLight, Lightium, CSEM, NTT, Fujitsu, Sumitomo and Liobate. Label these as patent claims, not demonstrated results.
4. PhD theses and review articles, e.g. the Lončar group and Zhu et al. "Integrated photonics on thin-film lithium niobate".
5. Vendor and foundry pages only for process-capability context, never for performance claims.

## 8. EVIDENCE RULES
- For every quantitative claim, give: the source, Vπ·L, whether push-pull or single-arm, wavelength, gap, film thickness, etch depth, buffer, cladding, cut, and whether it is **measured or simulated**.
- Separate measured results, simulation-only results, patent claims and your own inference.
- If a paper's improvement comes mostly from a smaller gap, a higher-k material or a thinner film, say so explicitly. It then does not satisfy our constraints.
- When sources disagree, show both values and explain the differences in geometry or normalisation. Do not average them.
- If a quantity is not reported, write "not reported". Do not estimate it silently.
- Flag any strategy that introduces vertical dielectric/metal interfaces near the slab (standing-wave risk) or metal close to the LN (plasmonic loss risk).

## 9. RESEARCH TASKS
1. **Discover** all geometric strategies reported for raising Γ or the field in the LN core of X-cut TFLN at a fixed gap, using only LN, SiO2 and metal.
2. **Verify** the magnitude of each, normalised to push-pull Vπ·L at 1625 nm and to a gap of about 3.2 µm, using the paper's own data or a stated scaling.
3. **Analyse the mechanism:** for each, explain why it raises Γ (field redistribution between the low-ε regions and the LN, mode repositioning, edge-field use, and so on). Check it against our findings: air pockets hurt; oxide in front of tall electrode sidewalls helps; a thicker buffer costs Vπ.
4. **Assess the IL cost** of each and whether it plausibly stays ≤ 0.3 dB/cm with a buffer ≥ 100 nm.
5. **Assess manufacturability** with UV lithography, SiO2 deposition and etch, Au plating and up to three metal levels.
6. **Challenge:** look specifically for evidence that ~1.6 V·cm push-pull at 1625 nm, with a gap ≥ 3.2 µm, a 550/275 nm rib, no high-k materials and IL ≤ 0.3 dB/cm, is **not achievable**. If the reported state of the art cannot reach it, say so and give the realistic floor.

## 10. ANALYSIS FRAMEWORK — rank strategies on
- expected ΔVπ·L (%) at fixed gap, normalised as above;
- IL penalty and whether the buffer can stay ≥ 100 nm;
- evidence level (measured / simulated / patent / inference);
- fabrication complexity and number of extra mask steps;
- risk of lateral standing waves or plasmonic coupling;
- RF impact (impedance, microwave index, RF loss), as show-stopper flags only;
- compatibility with our existing stack (Madrid B) and how many parameters change.

## 11. OUTPUT
1. Executive summary of about 10 lines: is 1.6 V·cm reachable under these constraints, and with which 2–4 strategies?
2. A ranked strategy table with the columns in §10 and a citation per row.
3. For each top strategy: a schematic description precise enough to draw a 2D cross-section (dimensions or ranges), the mechanism, the expected numbers, and the key parameters for us to sweep in FEM.
4. A literature evidence table of each relevant paper's normalised Vπ·L, conditions and measured/simulated status.
5. Combined strategies: which ones stack, and which compete.
6. Excluded strategies (violating a hard constraint) with the constraint they violate, in one line each.
7. Risks, unknowns, and what could not be established.
8. Recommended simulation plan: the top 3 cross-sections, with parameter ranges.
9. Full source list with links.

## 12. QUALITY CHECK BEFORE FINALISING
- Every recommended strategy satisfies all hard constraints in §4.
- Every number is normalised (push-pull, 1625 nm) or explicitly flagged as not normalised.
- No improvement attributed to geometry is actually due to gap, material or film-thickness changes.
- Uncertainty is labelled, and the report answers the decision in §2.
