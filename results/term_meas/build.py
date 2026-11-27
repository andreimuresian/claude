import sys, os, shutil, json
os.makedirs("/tmp/deck5", exist_ok=True)
shutil.copy("/home/user/claude/results/final_deck/VPI_Lisbon_Lifted_final.pptx", "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
C = "/home/user/claude/results/term_meas/"; S = json.load(open(C + "rsq_box.json"))
first_new = len(prs.slides); B = {"size": 12, "space": 4}; H = lambda t: (t, {"size": 15, "bold": True, "color": NAVY, "space": 8})
# 1 structure + model
s = new("TiN terminations: structure and model", "3-point DC probe (GSG) · wafers 6LS0004, 6LS0005 (Lisbona tape-out) · 7 fields each · 15 variants")
image(s, C + "layout.png", 0.6, 1.8, w=4.6)
box(s, 5.6, 1.8, 7.2, 3.0, [H("Model"), ("Grounds tied by the probe: Rtot = Rs + Rg / 2", B),
    ("Each arm R = R_sh · L / w, R_sh = ρ / t; gold over TiN shorts it", B),
    ("Rtot = R_sh · L · [1/(ws − δ) + 1/(2(wg − δ))] + R₀ ; δ = width loss vs drawn", B),
    H("Design matrix"), ("Variants 2–15: in-line, L = 56 µm, ws / wg = 2.63 in all → Rs and Rg not separable; split assumed", B),
    ("Variant 1: crossed layout, L = 28 µm → excluded from fit, used as check", B)])
# 2 boxplots variants
s = new("Measured resistance per variant", "Boxes: median, Q1–Q3, whiskers 1.5 × IQR · filled: fields 0, 10, 14 · hollow: fields 2, 5, 7, 8")
image(s, C + "box_variants.png", 0.4, 1.7, w=12.5)
text(s, 0.6, 6.4, 12.2, 0.6, [("Fields 2, 5, 7, 8 scatter only upward (up to +41 Ω): probe-contact problems → excluded from the fit. Fields 0, 10, 14: smooth, 0.2–1.8 Ω about their own line", {"size": 11.5})])
for w in ["6LS0004", "6LS0005"]:
    s = new(f"Measured resistance per variant: {w}", "Median values labelled · filled: fields 0, 10, 14 · hollow: fields 2, 5, 7, 8")
    image(s, C + f"box_{w}.png", 0.4, 1.7, w=12.5)
# 3 fit
s = new("Fit: sheet resistance and width loss", "Fields 0, 10, 14 · straight line gives R₀ ≈ −8 Ω (unphysical) → width loss δ needed")
image(s, C + "term_fit.png", 0.3, 1.7, w=12.7)
text(s, 0.6, 6.7, 12.2, 0.5, [("Best fields 10, 14: R_sh = 27.2 ± 0.6 Ω/sq, δ = 0.9 ± 0.4 µm (R₀ = 0) · with R₀ = 2 Ω: 25.8 Ω/sq, δ = 1.5 µm · field-to-field ±7 %", {"size": 11.5})])
# 4 Rsq boxplot + resistivity
s = new("Sheet resistance and TiN resistivity", "Every measurement converted to R_sh = R / x_eff (width-corrected) · variants 2–15")
image(s, C + "box_rsq.png", 0.5, 1.7, w=6.0)
table(s, [["Wafer", "R_sh (Ω/sq), fields 0,10,14", "ρ at t = 100 nm"], ["6LS0004", f"{S['6LS0004/clean']['med']:.1f}", f"{S['6LS0004/clean']['med']*10:.0f} µΩ·cm"],
          ["6LS0005", f"{S['6LS0005/clean']['med']:.1f}", f"{S['6LS0005/clean']['med']*10:.0f} µΩ·cm"]], 6.9, 1.8, 6.0, [1.4, 2.6, 2.0], size=12)
box(s, 6.9, 3.2, 6.0, 2.1, [("Planar R gives only ρ / t: ρ needs the nominal t (≈ 100 nm)", B),
    ("ρ ≈ 270 µΩ·cm: high for sputtered TiN (typ. 100–150; bulk 15–25)", B),
    ("Sputtered (confirmed): either resistive film (N-rich, low T, porous, oxidised) or exposed strips thinner (etch / TiO₂): ρ = 135 µΩ·cm ⇔ 50 nm conducting", B),
    ("Check: 4-point probe on monitor wafer, step height of exposed strips", B)])
# predictor
P = json.load(open(C + "predictor.json"))
s = new("Predictor: Rtot from wg, ws at fixed ratio", "Assuming Rtot = Rs + Rg / 2 · ws / wg = 2.63 as in all measured variants · L = 56 µm")
rows = [["Rtot target (Ω)", "wg (µm)", "ws (µm)", "Field spread ±7 % (Ω)"]]
for r in P["rows"]: rows.append([f"{r['R']:.1f}", f"{r['wg']:.1f}", f"{r['ws']:.1f}", f"{r['lo']:.1f} – {r['hi']:.1f}"])
table(s, rows, 0.6, 1.8, 6.6, [1.7, 1.4, 1.4, 2.1], size=12, row_h=0.36, highlight=(5,))
box(s, 7.6, 1.8, 5.2, 3.2, [H("Model"), ("Rtot = R_sh · L · [1/(ws − δ) + 1/(2(wg − δ))]", B), ("R_sh = 27.2 Ω/sq, δ = 0.9 µm (fields 10, 14)", B),
    H("Validity"), ("Measured range: wg 12.6–27.3 µm (Rtot ≈ 50–120 Ω)", B), ("Rtot < 50 Ω: wider strips, mild extrapolation (δ matters less)", B),
    ("Alternative fit (R₀ = 2 Ω): wg within 0.4 µm of the table", B), ("Other ws / wg ratios: needs the Rs + Rg/2 split, untested → add one off-ratio variant", B)])
text(s, 0.6, 5.6, 6.6, 0.6, [("50 Ω ≈ variant 2 (71.8 / 27.3 µm), measured 50–52 Ω on fields 0, 10, 14", {"size": 11.5})])
# 5 variant 1 + conclusions
s = new("Variant 1 check and conclusions", "Crossed layout, L = 28 µm, not used in the fit")
table(s, [["Variant 1", "R (Ω)"], ["Predicted (R_sh 27.2, δ 0.9)", "48.1"], ["Measured, median fields 10, 14", "50.2"], ["Difference", "+2.1 (+4 %)"]],
      0.6, 1.8, 5.6, [3.8, 1.8], size=12)
text(s, 0.6, 3.4, 5.6, 1.4, [("+2 Ω: extra pad overlaps and end effects of the short crossed arms; independent confirmation of R_sh", B)])
box(s, 6.7, 1.8, 6.1, 2.4, [H("Conclusions"), ("R_sh ≈ 27 Ω/sq (26.8 / 28.0 per wafer), δ ≈ 1 µm narrower than drawn", B),
    ("ρ ≈ 270 µΩ·cm if t = 100 nm: verify film or exposed thickness", B),
    ("Fields 2, 5, 7, 8: re-measure (contact)", B),
    ("Next layout: vary ws / wg independently to measure Rs and Rg separately", B)])
sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = C + "TiN_terminations_AFR.pptx"; prs.save(out); print("saved", out, len(prs.slides))
