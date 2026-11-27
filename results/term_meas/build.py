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
    ("Each arm R = R□ · L / w, R□ = ρ / t; gold over TiN shorts it", B),
    ("Rtot = R□ · L · [1/(ws − δ) + 1/(2(wg − δ))] + R₀ ; δ = width loss vs drawn", B),
    H("Design matrix"), ("Variants 2–15: in-line, L = 56 µm, ws / wg = 2.63 in all → Rs and Rg not separable; split assumed", B),
    ("Variant 1: crossed layout, L = 28 µm → excluded from fit, used as check", B)])
# 2 boxplots variants
s = new("Measured resistance per variant", "Boxes: median, Q1–Q3, whiskers 1.5 × IQR · filled: fields 0, 10, 14 · hollow: fields 2, 5, 7, 8")
image(s, C + "box_variants.png", 0.4, 1.7, w=12.5)
text(s, 0.6, 6.4, 12.2, 0.6, [("Fields 2, 5, 7, 8 scatter only upward (up to +41 Ω): probe-contact problems → excluded from the fit. Fields 0, 10, 14: smooth, 0.2–1.8 Ω about their own line", {"size": 11.5})])
# 3 fit
s = new("Fit: sheet resistance and width loss", "Fields 0, 10, 14 · straight line gives R₀ ≈ −8 Ω (unphysical) → width loss δ needed")
image(s, C + "term_fit.png", 0.3, 1.7, w=12.7)
text(s, 0.6, 6.7, 12.2, 0.5, [("Best fields 10, 14: R□ = 27.2 ± 0.6 Ω/□, δ = 0.9 ± 0.4 µm (R₀ = 0) · with R₀ = 2 Ω: 25.8 Ω/□, δ = 1.5 µm · field-to-field ±7 %", {"size": 11.5})])
# 4 Rsq boxplot + resistivity
s = new("Sheet resistance and TiN resistivity", "Every measurement converted to R□ = R / x_eff (width-corrected) · variants 2–15")
image(s, C + "box_rsq.png", 0.5, 1.7, w=6.0)
table(s, [["Wafer", "R□ (Ω/□), fields 0,10,14", "ρ at t = 100 nm"], ["6LS0004", f"{S['6LS0004/clean']['med']:.1f}", f"{S['6LS0004/clean']['med']*10:.0f} µΩ·cm"],
          ["6LS0005", f"{S['6LS0005/clean']['med']:.1f}", f"{S['6LS0005/clean']['med']*10:.0f} µΩ·cm"]], 6.9, 1.8, 6.0, [1.4, 2.6, 2.0], size=12)
box(s, 6.9, 3.2, 6.0, 2.1, [("Planar R gives only ρ / t: ρ needs the nominal t (≈ 100 nm)", B),
    ("ρ ≈ 270 µΩ·cm: high for TiN (bulk 15–25, sputtered 100–150)", B),
    ("Either resistive film (N-rich, porous, oxidised) or exposed strips thinner (etch / TiO₂): ρ = 135 µΩ·cm ⇔ 50 nm conducting", B),
    ("Check: 4-point probe on monitor wafer, step height of exposed strips", B)])
# 5 variant 1 + conclusions
s = new("Variant 1 check and conclusions", "Crossed layout, L = 28 µm, not used in the fit")
table(s, [["Variant 1", "R (Ω)"], ["Predicted (R□ 27.2, δ 0.9)", "48.1"], ["Measured, median fields 10, 14", "50.2"], ["Difference", "+2.1 (+4 %)"]],
      0.6, 1.8, 5.6, [3.8, 1.8], size=12)
text(s, 0.6, 3.4, 5.6, 1.4, [("+2 Ω: extra pad overlaps and end effects of the short crossed arms; independent confirmation of R□", B)])
box(s, 6.7, 1.8, 6.1, 2.4, [H("Conclusions"), ("R□ ≈ 27 Ω/□ (26.8 / 28.0 per wafer), δ ≈ 1 µm narrower than drawn", B),
    ("ρ ≈ 270 µΩ·cm if t = 100 nm: verify film or exposed thickness", B),
    ("Fields 2, 5, 7, 8: re-measure (contact)", B),
    ("Next layout: vary ws / wg independently to measure Rs and Rg separately", B)])
sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = C + "TiN_terminations_AFR.pptx"; prs.save(out); print("saved", out, len(prs.slides))
