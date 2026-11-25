import json as _j
GM = "/home/user/claude/results/madrid/m1/"
# U1 literature
s = new("Literature search (Gemini Deep Research): what we tested", "Constraints: gap ≥ 3.2 µm, buffer ≥ 100 nm, no new materials, 550/275 nm film · Gemini's numbers are model estimates; all values below are our FEM (Madrid 1, gap 3.5 µm, 1625 nm)")
table(s, [["Gemini proposal", "Gemini claim", "Our FEM", "Verdict"],
          ["Flush SiO₂ gap fill to gold top (no trench)", "−7 %", "−0.3 % (fill 1.1 → 5 µm)", "No effect"],
          ["U-slot: SiO₂ pillars on gold walls + central air trench", "−12 to −13 %", "−6.7 % (−5.3 % at equal IL)", "Adopted"],
          ["Stepped buffer under the inner electrode edge", "IL relief", "on the buffer trade-off curve", "No gain"],
          ["Inverted-L gold foot (bottom setback)", "IL relief", "on the buffer trade-off curve", "No gain"],
          ["Local BOX air undercut", "−6.7 %", "not simulated", "Next-generation process"],
          ["Rib widening 1.4 → 1.6 µm", "−2.4 %", "not simulated", "Dropped"]],
      0.6, 1.8, 8.4, [3.3, 1.4, 2.3, 1.4], size=11, highlight=(2,))
image(s, GM + "gemini/gemini_variants_tradeoff.png", 9.15, 1.75, w=3.85)
box(s, 0.6, 5.0, 8.4, 1.5, [("Gemini found the right mechanism and geometry; its magnitudes came from a simplified isotropic model and were ≈ 2× optimistic. Its literature audit agrees with ours: no compliant device reaches 1.6 V·cm.", B)])
# U2 design
s = new("Madrid 1 with U-slot: optimised cross-section", "Gap 3.5 µm · oxide fill 2.0 µm flush on both gold walls · 1.0 µm air trench, floor 100 nm above the rib · buffer 130 nm")
image(s, GM + "gemini/madrid1_uslot_xs.png", 0.5, 1.5, h=5.3)
table(s, [["", "Vπ·L", "IL"], ["U-slot (130 nm)", "1.782", "0.189"], ["buffer −40 nm", "1.729", "0.323"], ["no-slot robust (115 nm)", "1.880", "0.192"]],
      8.3, 1.7, 4.5, [2.1, 1.2, 1.2], size=11, highlight=(1,))
box(s, 8.3, 3.3, 4.5, 3.0, [H("Result"), ("−5.2 % Vπ·L at equal IL; same gain at every buffer 100–130 nm", B),
    ("Worst case (−40 nm) stays < 0.4 dB/cm", B), ("Symmetric tall ground: further −1.4 % (RF check needed)", B)])
# U3 physics
s = new("Why it works: the trench concentrates the DC field", "Same design with and without the trench · E_x·G/V map, equipotentials every 0.05 V, optical mode contours")
image(s, GM + "gemini/field/trench_field_comparison.png", 0.4, 1.5, h=5.35)
box(s, 7.25, 1.55, 5.6, 4.8, [H("Split test (trench air only for one solver)"),
    ("Air for DC only: 1.801 V·cm, IL unchanged → ≈ 90 % of the gain is electrostatic", B),
    ("Air for optics only: 1.890 V·cm, IL +15 % → the IL penalty is optical", B),
    ("Oxide pillars carry the electrode potential inward; the voltage drops across the 1 µm air trench", B),
    ("Field in the rib +6 % (mode-weighted 0.597 → 0.632), Γ 0.496 → 0.532", B),
    ("Pillars need ≥ 1.5 µm height; effect saturates above", B)])
# U4 sensitivity
s = new("U-slot sensitivity", "Gap 3.5 µm, buffer 130 nm, fill 2.0 µm · FEM, 1625 nm · dotted: no trench (1.910 / 0.162)")
image(s, GM + "uslot/uslot_1d_sweeps.png", 0.35, 1.5, w=12.6)
box(s, 0.6, 5.45, 3.9, 1.35, [("Trench width: flat optimum 0.8–1.4 µm (≤ 0.6 %): litho-tolerant", {"size": 11})])
box(s, 4.7, 5.45, 3.9, 1.35, [("Floor: +0.011 V·cm per 50 nm, no cliff; 200 nm keeps −5.6 % at IL 0.171", {"size": 11})])
box(s, 8.8, 5.45, 4.0, 1.35, [("Pillars must touch the gold: a 200 nm air gap makes it worse than no trench", {"size": 11, "bold": True, "color": RED})])
# U5 process variant
s = new("Process-realistic variant: gold tongues over the oxide", "Oxide 3.5 × 1.0 µm · gold gap 3.3 µm (0.1 µm overlap/side) · 1 µm first gold layer + 200 nm belly · trench 1.0 µm, floor 100 nm, buffer 130 nm")
image(s, GM + "tongue/tongue_as_simulated.png", 0.4, 1.55, w=8.4)
table(s, [["Case", "Vπ·L", "IL", "−40 nm"], ["no tongue", "1.803", "0.189", "—"], ["aligned 0.1 / 0.1", "1.790", "0.189", "—"],
          ["signal tongue 0.2", "1.796", "0.189", "1.743 / 0.324"], ["ground tongue 0.2", "1.787", "0.189", "1.734 / 0.324"]],
      9.0, 1.7, 3.9, [1.4, 0.75, 0.75, 1.0], size=10, highlight=(2,))
box(s, 9.0, 3.65, 3.9, 2.7, [("Overlap guarantees gold–oxide contact; tongues even help (−0.4 to −0.9 %)", B),
    ("Misalignment ±0.1 µm: < 0.5 % Vπ·L, IL unchanged", B), ("1 µm fill costs +0.4 % vs 2 µm pillars", B)])
