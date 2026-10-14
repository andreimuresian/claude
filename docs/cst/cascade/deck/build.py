from helpers import *
SM = pickle.load(open(os.path.join(HERE, "summary.pkl"), "rb"))
BOX = RGBColor(0xD9, 0xDC, 0xE3)
def card(s, x, y, w, h, head, body, hc=NAVY, size=11.5):
    rect(s, x, y, w, h)
    text(s, x + 0.15, y + 0.08, w - 0.3, h - 0.12, [(head, {"bold": True, "color": hc, "size": size + 1.5})] + [(b, {"size": size}) for b in body], sa=3)
def fig(s, name, x, y, w, h, frame=True):
    if frame: rect(s, x, y, w, h, fill=WHITE, line=BOX)
    pic(s, name, x + 0.05, y + 0.05, w - 0.1, h - 0.1)
P = SM["port"]; Ln = SM["lines"]; L3 = SM["LC3"]
k4, k05, k45 = (0.001, 0.005), (0.0005, 0.001), (0.0005, 0.005)

# 1 title
s = prs.slides.add_slide(L_TITLE)
text(s, 0, 2.3, 13.33, 1.3, "CST straight line: port artefact and line extraction", size=38, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0, 3.65, 13.33, 0.8, "Cascading, de-embedding with three lengths, a model of the port region, and what it means for INTERCONNECT",
     size=18, color=MUTED, align=PP_ALIGN.CENTER)

# 2 context
s = new(); title(s, "Why, and what was simulated", "Goal: line data we can cascade in INTERCONNECT, then EO response, then crosstalk")
fig(s, "runs.png", 0.5, 1.6, 6.6, 2.4)
rows = [["Item", "Value"], ["Line", "uniform CPW, S 35 µm, gap 4.15 µm, ground 49.85 µm, Au 2 µm"], ["Lengths", "0.5, 1 and 5 mm, same ports and settings"],
        ["Export", "2-port Touchstone, 50 Ω reference, 0–60 GHz"], ["Wanted", "α(f), n_m(f), Zc(f): any length follows"]]
table(s, 7.35, 1.6, 5.5, rows, [1.2, 4.3], size=11, row_h=0.47)
steps = [("1  Cascade", "five 1 mm runs vs one 5 mm run"), ("2  De-embed", "pairs of lengths → port-free γ, Zc"),
         ("3  Port model", "what the CST port adds to every run"), ("4  Next", "EO cascade, then coupled lines (crosstalk)")]
for i, (a, b) in enumerate(steps):
    x = 0.5 + i * 3.1; rect(s, x, 4.35, 2.9, 1.25, fill=WHITE, line=NAVY if i < 3 else BOX)
    text(s, x + 0.12, 4.42, 2.7, 1.15, [(a, {"bold": True, "color": NAVY if i < 3 else MUTED, "size": 14}), (b, {"size": 11.5})], sa=2)
text(s, 0.5, 5.85, 12.35, 1.0, [("Key quantities.", {"bold": True, "color": NAVY}),
     ("ABCD (chain) matrix of each run: relates V, I at input to V, I at output, independent of the 50 Ω reference. A uniform line: "
      "A = D = cosh γℓ, B = Zc sinh γℓ, C = sinh γℓ / Zc. Cascading = multiplying ABCD matrices.", {})], size=12, sa=2)

# 3 cascade principle
s = new(); title(s, "Cascading identical lines adds no mismatch", "The 50 Ω reference is bookkeeping: it appears only at the two outer ends")
fig(s, "cascade_illustration.png", 0.5, 1.55, 7.9, 4.65)
card(s, 8.65, 1.55, 4.2, 2.05, "Proof on an ideal line", [f"Analytic line, Zc = 37 − 1j Ω: 1 mm⁵ vs 5 mm in 50 Ω → max |ΔS| = {SM['ideal_err']:.0e}.",
     "ABCD joins V and I continuously: Zc meets Zc, nothing reflects."])
fig(s, "renorm.png", 8.65, 3.75, 4.2, 2.45)
text(s, 0.5, 6.35, 12.35, 0.7, [f"**Renormalising to Zc** changes only the outer references, identically for both: max |S21| gap {SM['renorm_max'][0]:.2f} dB (50 Ω) "
     f"vs {SM['renorm_max'][1]:.2f} dB (Zc). What is counted five times is the **port region** (orange), inside the data."], size=12)

# 4 raw cascade
s = new(); title(s, "Raw cascade: 1 mm × 5 vs 5 mm", "Close, but not exact: the error grows with frequency")
fig(s, "raw_cascade.png", 0.5, 1.55, 12.35, 3.5)
card(s, 0.5, 5.25, 4.0, 1.6, "|S21|", [f"within 0.1 dB to ~35 GHz, up to {SM['casc_max']:.2f} dB at 55 GHz."])
card(s, 4.67, 5.25, 4.0, 1.6, "|S11|", ["same −12 dB envelope (same Zc), minima shifted to lower f by 0.2–1 GHz."])
card(s, 8.85, 5.25, 4.0, 1.6, "∠S21", ["cascade accumulates extra phase: ~6° at 30 GHz, ~15° at 60 GHz."], hc=RED)

# 5 port artefact fixed
s = new(); title(s, "Every run carries the same, length-independent port artefact", "Excess of each single run over the de-embedded line: identical for 0.5, 1 and 5 mm")
fig(s, "excess.png", 0.5, 1.55, 7.6, 2.95)
fig(s, "port_model.png", 0.5, 4.6, 7.6, 2.35)
e = SM["exc"]
rows = [["Excess per run", "0.5 mm", "1 mm", "5 mm"]] + [[f"phase @ {x} GHz", *[f"{e[x][L][1]:.2f}°" for L in (0.0005, 0.001, 0.005)]] for x in (10, 30, 60)] + \
       [[f"loss @ 30 GHz", *[f"{e[30][L][0]:+.3f} dB" for L in (0.0005, 0.001, 0.005)]]]
table(s, 8.35, 1.55, 4.5, rows, [1.7, 0.95, 0.95, 0.95], size=11, row_h=0.42)
card(s, 8.35, 3.8, 4.5, 3.15, "Reading", ["Excess = apparent γℓ of one run − true γℓ (4.5 mm de-embedding).",
     "**Phase:** 1.4° at 30 GHz, ~3° at 60 GHz, the same at 10× different lengths → a fixed block at the ports, not the line.",
     "**Loss:** ±0.03 dB, at the run-to-run noise level.",
     "Model (dotted): two port regions, each a series L_{s} + shunt C_{p}."], size=11)

# 6 what the port does
s = new(); title(s, "What one port region does", f"Series {L3[0]*1e12:.1f} pH + shunt {L3[1]*1e15:.1f} fF, fitted on all three runs: a pure phase delay")
fig(s, "port_char.png", 0.5, 1.55, 12.35, 3.45)
rows = [["f (GHz)", "|S21| (dB)", "∠S21", "|S11| (dB)", "extra line"]] + [[f"{x}", f"{P[x]['mag']:+.4f}", f"{P[x]['ph']:.2f}°", f"{P[x]['s11']:.0f}", f"{P[x]['dl']:.1f} µm"] for x in (10, 30, 60)]
table(s, 0.5, 5.2, 6.3, rows, [0.9, 1.2, 1.0, 1.2, 1.2], size=11.5, row_h=0.42)
card(s, 7.05, 5.2, 5.8, 1.7, "Physical meaning", ["≈ 9.5 µm of extra line per port: the reference plane sits slightly inside the line, where the 2D port mode settles into the 3D field.",
     "Line per unit length: 238 nH/m, 178 pF/m → 2.8 pH ≈ 12 µm, 1.3 fF ≈ 7 µm."], size=11)

# 7 de-embedding
s = new(); title(s, "Two-length de-embedding: γ exact, Zc almost", "Matrices do not commute: one port box survives, but it cannot change γ")
fig(s, "deemb.png", 0.5, 1.55, 7.7, 2.6)
card(s, 8.45, 1.55, 4.4, 2.6, "Why γ is clean", ["γ sits in the eigenvalues e^{±γΔℓ} (trace); Zc in the eigenvectors (V/I of each wave).",
     "P̃⁻¹(…)P̃ changes eigenvectors, never eigenvalues. tr(P̃⁻¹ L P̃) = tr(L)."], size=11)
card(s, 0.5, 4.35, 6.05, 2.55, "Extraction", ["cosh γΔℓ = (A + D)/2 → e^{−γΔℓ} = A − √(A² − 1)  (root with |·| < 1, passive line)",
     "α = −ln|e^{−γΔℓ}| / Δℓ,   β = −unwrap∠e^{−γΔℓ} / Δℓ,   n_m = βc/ω",
     "Phase unwrapped from DC: needs only a fine frequency grid, no resonance."], size=11)
card(s, 6.8, 4.35, 6.05, 2.55, "Size of the Zc residue", ["Series r alone: Zc'² = Zc² − r². With the fitted port: (|Z_{s}|/Zc)², (ωC_{p}Zc)² ≈ 10^{−4} → ~0.01 %.",
     "Scatter seen in √(B/C) (±1 %, spikes at βΔℓ = mπ where B, C → 0) is numerical, not residue."], size=11)

# 8 three cleansed lines
s = new(); title(s, "Three de-embedded lines", "4 mm and 4.5 mm agree; the 0.5 mm difference is too short to beat the run noise")
fig(s, "three_lines.png", 0.5, 1.55, 12.35, 3.45)
rows = [["f", "α 4 / 0.5 / 4.5 mm (dB/cm)", "n_m 4 / 0.5 / 4.5 mm"]] + [[f"{x} GHz", " / ".join(f"{Ln[x][k][0]:.2f}" for k in (k4, k05, k45)),
        " / ".join(f"{Ln[x][k][1]:.3f}" for k in (k4, k05, k45))] for x in (1, 10, 30, 60)]
table(s, 0.5, 5.15, 6.2, rows, [0.8, 2.8, 2.6], size=11, row_h=0.36, hl_rows=())
fig(s, "noise_amp.png", 6.9, 5.1, 2.7, 1.9, frame=False)
card(s, 9.75, 5.15, 3.1, 1.8, "Why 0.5 mm fails", ["Each run: ~0.02 dB, ~0.2° noise. Divided by Δℓ: 8× worse at 0.5 mm than at 4 mm.",
     "Rule: largest Δℓ for γ."], size=10.5)

# 9 predict 0.5 mm
s = new(); title(s, "Predicting the 0.5 mm run from the 1 and 5 mm runs", "The 0.5 mm data were not used: a blind test of the port model")
fig(s, "pred05.png", 0.5, 1.55, 12.35, 3.45)
steps = [("1", "γ from 5 − 1 mm (trace)"), ("2", "fit L_{s}, C_{p}, Zc to the 1 and 5 mm S11, S21"), ("3", "T = P · L(0.5 mm) · P̃ → S at 50 Ω"), ("4", "compare with CST 0.5 mm")]
for i, (n, t) in enumerate(steps):
    x = 0.5 + i * 2.05; rect(s, x, 5.2, 1.9, 1.05, fill=WHITE, line=NAVY)
    text(s, x + 0.1, 5.25, 1.7, 1.0, [(n, {"bold": True, "color": RED, "size": 16}), (t, {"size": 10.5})], sa=1)
pr = SM["pred05"]
rows = [["f (GHz)", "Δ|S21|", "Δ∠S21 model", "Δ∠S21 no ports"]] + [[f"{x}", f"{pr[x][0]:+.3f} dB", f"{pr[x][1]:+.2f}°", f"{pr[x][2]:+.2f}°"] for x in (10, 30, 60)]
table(s, 8.85, 5.2, 4.0, rows, [0.8, 1.0, 1.1, 1.2], size=10.5, row_h=0.36)
text(s, 0.5, 6.45, 8.2, 0.5, "Model: ≤ 0.02 dB, ≤ 0.2°. Without the port model the phase is off by 1.2° at 30 GHz, 2.5° at 60 GHz.", size=11.5, color=NAVY, bold=True)

# 10 5 mm vs clean
s5, m = SM["s5"], SM["s5max"]
s = new(); title(s, "5 mm CST run vs the clean 4.5 mm-derived line", "Clean line alone misses only the port phase; adding the two port regions closes the gap")
fig(s, "s5_vs_clean.png", 0.5, 1.55, 12.35, 3.45)
rows = [["", "max Δ|S21|", "Δ∠S21 @ 30 GHz", "Δ∠S21 @ 60 GHz"],
        ["clean line (γ 4.5 mm, Zc fit)", f"{m['clean_db']:.2f} dB", f"{s5[30][1]:+.2f}°", f"{s5[60][1]:+.2f}°"],
        ["clean line + 2 port regions", f"{m['port_db']:.2f} dB", f"{s5[30][3]:+.2f}°", f"{s5[60][3]:+.2f}°"]]
table(s, 0.5, 5.25, 7.4, rows, [2.9, 1.4, 1.55, 1.55], size=11.5, row_h=0.45)
card(s, 8.15, 5.2, 4.7, 1.7, "Consistency", ["|S11|, |S21| differences ≤ 0.08 dB, at noise level, both ways.",
     "Phase difference = 2 port regions (1.4° at 30 GHz), as predicted."], size=11)

# 11 really cleansed lines
c_ = SM["corr"]
s = new(); title(s, "Port-free lines from a single run", "Remove both port regions: L(ℓ) = P⁻¹ · T_run · P̃⁻¹  (P from the 1 + 5 mm fit)")
fig(s, "corrected_runs.png", 0.5, 1.55, 8.3, 3.25)
rows = [["n_m from one run", "raw", "port-corrected", "4.5 mm de-emb."]] + [[f"0.5 mm @ {x} GHz", f"{c_[x][0.0005][3]:.3f}", f"{c_[x][0.0005][1]:.3f}", f"{Ln[x][k45][1] if x in Ln else 0:.3f}"] for x in (10, 30, 60)]
table(s, 9.0, 1.55, 3.85, rows, [1.45, 0.7, 1.0, 0.95], size=10, row_h=0.42)
card(s, 9.0, 3.4, 3.85, 1.4, "Independent test", ["The 0.5 mm run was not used to build P: its n_m error drops from 3–4 % to < 1 %."], size=10.5)
card(s, 0.5, 5.0, 6.05, 1.9, "What it fixes", ["**Phase / n_m** from one run, any length (the artefact is phase).",
     "**Port-free Touchstones** of each run: docs/cst/cascade/cleaned/.",
     "Future runs with the same ports and mesh: one length enough for n_m."], size=11)
card(s, 6.8, 5.0, 6.05, 1.9, "What it cannot fix", ["**α from one short run**: run noise (~0.02 dB) ÷ length. Loss still needs a length difference.",
     "P must be re-characterised for a new cross-section or port setup."], hc=RED, size=11)

# 12 FSR
fs = SM["fsr"]
s = new(); title(s, "n_m: resonance (FSR) method vs ABCD extraction", "Why 2 mm was thought to be the minimum, and why it is not")
fig(s, "fsr.png", 0.5, 1.55, 8.3, 2.9)
card(s, 9.0, 1.55, 3.85, 2.9, "FSR method", ["Mismatched line: S11 = Γ(1 − e^{−2γL})/(1 − Γ²e^{−2γL}) → minima at βL = mπ:",
     "n_m = m·c / (2 L f_m)",
     "One minimum in band needs L ≥ c/(2 n_m f_max) ≈ 1.3 mm at 60 GHz → '2 mm'."], size=10.5)
rows = [["m", "f_m (GHz)", "n_m (FSR)", "n_m (ABCD)"]] + [[f"{i+1}", f"{f_:.2f}", f"{n:.3f}", ""] for i, (f_, n) in enumerate(fs)]
rows[1][3], rows[2][3], rows[3][3] = "1.98", "1.947", "1.94"
table(s, 0.5, 4.65, 5.2, rows, [0.6, 1.4, 1.5, 1.5], size=11, row_h=0.4)
card(s, 5.95, 4.65, 6.9, 2.25, "Take-aways", ["Both agree where minima exist; ABCD gives n_m at every frequency, any length.",
     "Minima spacing gives the RF **group** index c/(2LΔf) = 1.92, 1.89, not the phase index n_m that sets walk-off (2–3 % error).",
     "Short runs are fine for n_m with ABCD; their limit is the port share (now modelled) and noise for α."], size=11)

# 13 INTERCONNECT implications
s = new(); title(s, "What this means for INTERCONNECT", "Segments from γ and Zc, not from raw Touchstones")
cards = [("Electrical cascade", ["Exact for any number of segments (ABCD identity).", "More, shorter CST segments do not help: port share grows."], NAVY),
         ("Electro-optic sampling", ["N lumped OMs sample V(z) at points: error ∝ (βΔz)² → Δz ≪ RF wavelength (~0.1 mm at 100 GHz).",
          "TL scripted element: exact closed-form integral, one element per line."], NAVY),
         ("Frequency → time", ["Each S-matrix becomes an FIR filter; outside a Compound every pass adds latency → wrong ripple (0.45–2.8 dB).",
          "Fix: Compound with scattering data analysis (0.04 dB, 0.4°)."], NAVY),
         ("Crosstalk: not yet covered", ["Needs coupled lines: 2 modes, 4×4 S-matrix, modulation per line from both modes, victim terminations.",
          "Same de-embedding: eigenvalues of T_s⁻¹T_l give γ_{e}, γ_{o} exactly."], RED)]
for i, (h, b, cl) in enumerate(cards):
    x = 0.5 + (i % 2) * 6.25; y = 1.6 + (i // 2) * 2.65
    card(s, x, y, 6.1, 2.45, h, b, hc=cl, size=14)

# 14 summary
s = new(); title(s, "Summary and next steps")
rows = [["Finding", "Evidence"],
        ["Cascading identical lines adds no mismatch; reference choice is bookkeeping", "ideal line 2·10^{−15}; renormalised gap unchanged"],
        ["Every CST run has a fixed port artefact: ~9.5 µm of extra line per port, phase only", "excess phase identical at 0.5 / 1 / 5 mm"],
        ["Port region = 2.8 pH series + 1.3 fF shunt", "blind prediction of 0.5 mm: ≤ 0.02 dB, ≤ 0.2°"],
        ["γ from two lengths is exact; take the largest Δℓ", "4 mm and 4.5 mm agree (n_m ± 0.003)"],
        ["Zc residue ~0.01 %; Zc ≈ 37.3 / 36.6 / 36.4 Ω at 10 / 30 / 60 GHz", "port-model fit"],
        ["Port-free lines from one run (phase); α still needs a length difference", "0.5 mm n_m error 3–4 % → < 1 %"]]
table(s, 0.5, 1.4, 12.35, rows, [7.0, 5.35], size=13, row_h=0.52, left=(0, 1))
card(s, 0.5, 5.15, 12.35, 1.75, "Next", ["1  Line tables for INTERCONNECT: γ (4.5 mm pair) + Zc (fit); check a 5 mm line in INTERCONNECT against CST.",
     "2  Optional CST check: port de-embedding of ~10 µm or a longer lead-in should remove the phase artefact.",
     "3  Crosstalk: derivation of coupled lines first, then CST coupled pair at two lengths, then a 4-port scripted element."], size=13.5)

out = os.path.join(HERE, "CST_line_extraction.pptx"); prs.save(out); print("saved", len(prs.slides))
