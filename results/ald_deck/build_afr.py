"""ALD Al2O3 deck in the AFR company template (master of results/final_deck/VPI_Lisbon_Lifted_final.pptx).

Run: python3 build_afr.py -> ALD_alumina_Cordoba_vs_Lisbon_AFR.pptx
head5.py loads /tmp/deck5/meeting.pptx: copy the final deck there first.
"""
import sys, json, shutil, os
os.makedirs("/tmp/deck5", exist_ok=True)
shutil.copy("/home/user/claude/results/final_deck/VPI_Lisbon_Lifted_final.pptx", "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *

HERE = "/home/user/claude/results/ald_deck/"
FG = HERE + "figs/"
PINK = RGBColor(0xBE, 0x18, 0x5D)
C_COR, C_LIS = ORANGE, BLUE

C = json.load(open(HERE + "../cordoba_alumina/summary.json"))["sweep"]
cor = [(r["T_nm"], r["VpiL_Vcm"], r["IL_dBcm"]) for r in C]
R = [json.loads(l) for l in open(HERE + "../lisbon_alumina/results.jsonl") if l.startswith("{")]
K = {(round(r["T_nm"]), r["gap"]): r for r in R if r["mesh_scale"] == 1 and r["ald_cells"] == 3}
lis = [(t, K[(t, 3.4)]["VpiL_Vcm"], K[(t, 3.4)]["IL_dBcm"]) for t in sorted(t for t, g in K if g == 3.4)]
first_new = len(prs.slides)

# 1 title -------------------------------------------------------------------
s = prs.slides.add_slide(L_TITLE)
text(s, 1.4, 2.35, 10.5, 2.4, [("ALD alumina protection layer:", {"size": 32, "bold": True}),
                               ("Cordoba vs buffered Lisbon lifted", {"size": 28, "bold": True}),
                               ("Effect on Vπ·L and insertion loss, gap relaxation and robustness at λ = 1575 nm",
                                {"size": 20, "color": MUT})], align=PP_ALIGN.CENTER)

# 2 what we studied ----------------------------------------------------------
s = new("What we studied", "A thin alumina film covers every exposed surface after the electrodes are made")
cards = [("The layer", ["ALD Al₂O₃, conformal on all surfaces", "Nominal 40 nm, swept 0 → 100 nm",
                        "Optical index 1.74", "RF permittivity 9.8"], PINK),
         ("Cordoba", ["Gold directly on the LN slab", "Electrode gap 4.2 µm",
                      "Reference: 0.43 dB/cm, 2.17 V·cm"], C_COR),
         ("Lisbon lifted, buffered", ["Gold on a 200 nm SiO₂ buffer", "Bottom gap 3.4 µm",
                                      "Reference: 0.03 dB/cm, 2.17 V·cm"], C_LIS)]
for i, (h, items, col) in enumerate(cards):
    x = 0.7 + i * 4.1
    box(s, x, 2.0, 3.8, 2.9, [(h, {"size": 18, "bold": True, "color": col, "space": 12})] +
        [(t, {"size": 14, "space": 8}) for t in items])
text(s, 0.7, 5.35, 12.0, 1.2, [("Common settings: 1575 nm, 550 nm LN film with 275 nm etch, rib top width 1.4 µm, "
                                 "SiO₂ cap 2.0 × 1.4 µm, full LN slab (no slab etch).", {"size": 14, "color": MUT}),
                                ("Questions: how much does the layer lower Vπ·L, how much loss does it add, "
                                 "and can it let us widen the Lisbon gap?", {"size": 15, "bold": True, "color": NAVY})])

# 3 cross sections ------------------------------------------------------------
s = new("The two cross-sections with 40 nm of alumina", "Alumina in pink; the red box marks the zoomed electrode corner")
text(s, 0.6, 1.85, 4, 0.35, [("Cordoba", {"size": 15, "bold": True, "color": C_COR})])
image(s, FG + "xs_cordoba_clean.png", 0.6, 2.2, h=2.35)
text(s, 0.6, 4.6, 4, 0.35, [("Lisbon lifted with 200 nm SiO₂ buffer", {"size": 15, "bold": True, "color": C_LIS})])
image(s, FG + "xs_lisbon_clean.png", 0.6, 4.95, h=2.35)
box(s, 8.3, 2.3, 4.4, 2.9, [("Legend", {"size": 14, "bold": True, "color": NAVY, "space": 8}),
                            ("Gold: electrodes", {"size": 13}), ("Grey: lithium niobate", {"size": 13}),
                            ("Blue: SiO₂ (box, cap, buffer, lift)", {"size": 13}), ("Pink: ALD alumina", {"size": 13, "bold": True, "color": PINK})])

# 4 Cordoba -------------------------------------------------------------------
s = new("Cordoba: lower Vπ·L, but twice the loss at 40 nm", "Gap 4.2 µm")
xy_chart(s, 0.6, 1.85, 6.0, 3.9, [("Vπ·L", [(t, v) for t, v, _ in cor], C_COR, 7, 2.25, False)], (0, 100), (2.0, 2.2),
         "Al₂O₃ thickness (nm)", "Vπ·L (V·cm)", legend=False, xmaj=20, ymaj=0.05)
xy_chart(s, 6.8, 1.85, 6.0, 3.9, [("IL", [(t, i) for t, _, i in cor], C_COR, 7, 2.25, False)], (0, 100), (0, 2.2),
         "Al₂O₃ thickness (nm)", "Insertion loss (dB/cm)", legend=False, xmaj=20, ymaj=0.5)
stat(s, 1.6, 5.95, 4.2, 1.15, "−3 %", "Vπ·L at 40 nm: 2.174 → 2.109 V·cm", C_COR)
stat(s, 7.6, 5.95, 4.2, 1.15, "×2.2", "loss at 40 nm: 0.43 → 0.93 dB/cm", PINK)
notes(s, "Validated against COMSOL: the Vpi*L change matches point by point; the IL increase factor matches within about 3 %. "
         "Absolute IL differs by a nearly constant ~25 % ratio (gold model or metal mesh in COMSOL).")

# 5 Lisbon --------------------------------------------------------------------
s = new("Lisbon buffered: larger Vπ·L gain, very low loss", "Bottom gap 3.4 µm")
xy_chart(s, 0.6, 1.85, 6.0, 3.9, [("Vπ·L", [(t, v) for t, v, _ in lis], C_LIS, 7, 2.25, False)], (0, 100), (1.9, 2.2),
         "Al₂O₃ thickness (nm)", "Vπ·L (V·cm)", legend=False, xmaj=20, ymaj=0.05)
xy_chart(s, 6.8, 1.85, 6.0, 3.9, [("IL", [(t, i) for t, _, i in lis], C_LIS, 7, 2.25, False)], (0, 100), (0, 0.12),
         "Al₂O₃ thickness (nm)", "Insertion loss (dB/cm)", legend=False, xmaj=20, ymaj=0.02)
stat(s, 1.6, 5.95, 4.2, 1.15, "−5.4 %", "Vπ·L at 40 nm: 2.175 → 2.058 V·cm", C_LIS)
stat(s, 7.6, 5.95, 4.2, 1.15, "0.055 dB/cm", "loss at 40 nm: still 8× below bare Cordoba", PINK)

# 6 comparison -----------------------------------------------------------------
s = new("Side by side: same trend, different strength", "Each curve is measured from its own design without alumina")
xy_chart(s, 0.6, 1.85, 6.0, 4.0, [("Cordoba, gap 4.2 µm", [(t, v - cor[0][1]) for t, v, _ in cor], C_COR, 6, 2.25, False),
                                  ("Lisbon buffered, gap 3.4 µm", [(t, v - lis[0][1]) for t, v, _ in lis], C_LIS, 6, 2.25, False)],
         (0, 100), (-0.25, 0), "Al₂O₃ thickness (nm)", "Vπ·L change (V·cm)", xmaj=20, ymaj=0.05)
xy_chart(s, 6.8, 1.85, 6.0, 4.0, [("Cordoba", [(t, i) for t, _, i in cor], C_COR, 6, 2.25, False),
                                  ("Lisbon buffered", [(t, i) for t, _, i in lis], C_LIS, 6, 2.25, False)],
         (0, 100), (0.01, 10), "Al₂O₃ thickness (nm)", "Insertion loss (dB/cm, log)", log=True, xmaj=20)
text(s, 0.8, 6.1, 11.8, 1.0, [("Same starting Vπ·L (2.17 V·cm), but Lisbon gains almost twice as much.", {"bullet": True, "size": 15}),
                              ("Loss grows by a similar factor in both, yet Lisbon stays about 15 times lower.", {"bullet": True, "size": 15})])

# 7 why ---------------------------------------------------------------------
s = new("Why Lisbon gains more: what the alumina sits on", "Simplified drawing, not to scale")
image(s, FG + "mechanism.png", 0.6, 1.85, w=8.0)
image(s, FG + "equal_gap_test.png", 8.9, 1.85, w=3.9)
text(s, 0.8, 5.0, 11.8, 2.1, [
    ("In Cordoba, the electric field already prefers the LN, which is far more polarisable than alumina.", {"bullet": True, "size": 15, "space": 10}),
    ("In Lisbon, alumina is the most polarisable material at the electrode level: it acts like a small extension of the electrode toward the waveguide.", {"bullet": True, "size": 15, "space": 10}),
    ("Test at the same 4.2 µm gap: Lisbon still gains twice as much. The buffer, not the narrower gap, causes the difference.", {"bullet": True, "size": 15, "bold": True, "color": NAVY})])

# 8 mesh -----------------------------------------------------------------------
s = new("Is it the mesh? No", "The 40 nm cases were repeated with a much finer mesh")
table(s, [["Case (40 nm alumina)", "Mesh refinement", "Vπ·L change", "Loss change"],
          ["Lisbon, gap 3.4 µm", "30 % finer everywhere", "+0.01 %", "−0.8 %"],
          ["Lisbon, gap 3.4 µm", "5 elements across the alumina (instead of 3)", "< 0.01 %", "−0.2 %"],
          ["Lisbon, gap 4.2 µm", "30 % finer everywhere", "+0.01 %", "−0.8 %"],
          ["Cordoba, gap 4.2 µm", "30 % finer everywhere", "+0.02 %", "−0.6 %"],
          ["Cordoba, gap 4.2 µm", "5 elements across the alumina (instead of 3)", "0.00 %", "+0.03 %"]],
      0.9, 2.0, 11.5, [3.0, 4.9, 1.8, 1.8], size=14, row_h=0.5)
stat(s, 3.4, 5.5, 6.5, 1.3, "0.05 V·cm", "Lisbon–Cordoba difference at 40 nm: about 100× larger than any mesh effect", C_LIS)

# 9 gap relaxation ------------------------------------------------------------------
s = new("Gap relaxation: from 3.4 µm to 3.6 µm",
        "Target: Vπ·L of Lisbon without alumina at 3.4 µm (2.175 V·cm, the same as Cordoba)")
gaps = lambda t: sorted(g for tt, g in K if tt == t)
ser_v = [("no Al₂O₃", [(g, K[(0, g)]["VpiL_Vcm"]) for g in gaps(0)], GREY, 6, 1.75, False),
         ("40 nm Al₂O₃", [(g, K[(40, g)]["VpiL_Vcm"]) for g in gaps(40)], C_LIS, 7, 2.5, False),
         ("target 2.175 V·cm", [(3.4, 2.1747), (4.8, 2.1747)], INK, 0, 1.25, True)]
xy_chart(s, 0.6, 1.85, 6.0, 4.0, [ser_v[1], ser_v[0], ser_v[2]], (3.4, 4.8), (2.0, 2.9), "Bottom gap (µm)", "Vπ·L (V·cm)", xmaj=0.2, ymaj=0.1)
ser_i = [("no Al₂O₃", [(g, K[(0, g)]["IL_dBcm"]) for g in gaps(0)], GREY, 6, 1.75, False),
         ("40 nm Al₂O₃", [(g, K[(40, g)]["IL_dBcm"]) for g in gaps(40)], C_LIS, 7, 2.5, False),
         ("Cordoba 0.43 dB/cm", [(3.4, 0.427), (4.8, 0.427)], C_COR, 0, 1.25, True)]
xy_chart(s, 6.8, 1.85, 6.0, 4.0, [ser_i[1], ser_i[0], ser_i[2]], (3.4, 4.8), (0.0001, 1), "Bottom gap (µm)", "Insertion loss (dB/cm, log)", log=True, xmaj=0.2)
stat(s, 0.9, 6.05, 3.6, 1.1, "3.60 µm", "relaxed gap with 40 nm alumina", C_LIS)
stat(s, 4.85, 6.05, 3.6, 1.1, "0.029 dB/cm", "loss at 3.60 µm: 15× below Cordoba", PINK)
stat(s, 8.8, 6.05, 3.6, 1.1, "+0.58 V·cm/µm", "Vπ·L cost of widening the gap", NAVY)
notes(s, "The 0.12 V*cm gained from the alumina buys only about 0.2 um of gap, because Vpi*L rises steeply with the gap. "
         "Loss is never the limit: it falls with the gap and is below 0.001 dB/cm at 4.8 um.")

# 10 robustness ----------------------------------------------------------------------
s = new("Robustness: alumina thickness ±10 nm", "Gap fixed at 3.60 µm, designed for 40 nm")
tol = json.load(open(HERE + "../lisbon_alumina/summary.json"))["tolerance_at_G_star"]
table(s, [["Alumina thickness", "Vπ·L (V·cm)", "Change", "Insertion loss (dB/cm)"]] +
      [[f"{r['T']} nm" + (" (nominal)" if r["T"] == 40 else f" ({r['T'] - 40:+d} nm)"), f"{r['VpiL']:.3f}",
        f"{100 * (r['VpiL'] / tol[1]['VpiL'] - 1):+.1f} %", f"{r['IL']:.3f}"] for r in tol],
      1.5, 2.1, 10.3, [3.2, 2.3, 2.0, 2.8], size=15, row_h=0.55, highlight=(2,))
text(s, 1.5, 4.6, 10.5, 2.2, [
    ("A ±10 nm error moves Vπ·L by only about ±1 %.", {"bullet": True, "size": 16, "space": 12}),
    ("This equals a gap error of about 40 nm: gap lithography matters more than alumina control.", {"bullet": True, "size": 16, "space": 12}),
    ("Loss stays between 0.025 and 0.033 dB/cm, far below Cordoba's 0.43 dB/cm.", {"bullet": True, "size": 16})])

# 11 conclusions ---------------------------------------------------------------------
s = new("Conclusions")
for i, (h, t) in enumerate([("Alumina lowers Vπ·L in both designs", "by 3 % in Cordoba and 5.4 % in Lisbon at 40 nm"),
                            ("The difference is physical", "the buffer makes the alumina more effective; the mesh is not the cause"),
                            ("Loss is not a concern for Lisbon", "below 0.06 dB/cm at 3.4 µm, below 0.03 dB/cm at 3.6 µm"),
                            ("The gap gain is modest: 3.4 → 3.6 µm", "a wider gap is possible only by accepting a higher Vπ·L"),
                            ("Process tolerance is comfortable", "±10 nm of alumina changes Vπ·L by about ±1 %")]):
    y = 1.75 + i * 1.05
    box(s, 0.9, y, 11.5, 0.88, [[(h + ":  ", {"bold": True, "color": NAVY, "size": 16}), (t, {"size": 16})]])

sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = HERE + "ALD_alumina_Cordoba_vs_Lisbon_AFR.pptx"
prs.save(out); print("saved", out, len(prs.slides))
