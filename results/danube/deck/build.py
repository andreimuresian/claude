"""Danube deck in the AFR template.  Run: python3 build.py"""
import sys, json, shutil, os, csv
os.makedirs("/tmp/deck5", exist_ok=True)
shutil.copy("/home/user/claude/results/final_deck/VPI_Lisbon_Lifted_final.pptx", "/tmp/deck5/meeting.pptx")
sys.path.insert(0, "/home/user/claude/results/final_deck/src")
from head5 import *
H = "/home/user/claude/results/danube/"; D = H + "deck/"
RED = RGBColor(0xC0, 0x39, 0x2B); LRED = RGBColor(0xF0, 0xA0, 0x8F); LBLUE = RGBColor(0x7F, 0xB3, 0xEA)
rows = list(csv.DictReader(open(H + "danube_slab_w_sweep.csv")))
def ser(case, col): return sorted((float(r["slab_w_top_um"]), float(r[col])) for r in rows if r["case"] == case)
WL = [json.loads(l[7:]) for l in open(H + "wl.txt") if l.startswith("RESULT")]
def wser(lab): return sorted({round(r["wl"] * 1e3): r["IL_dBcm"] for r in WL if r["tee"] == (1 if lab.startswith("inside") else 0)}.items())
first_new = len(prs.slides)
B = lambda t, **k: (t, dict({"size": 13, "space": 6}, **k))

# 1 title ------------------------------------------------------------------
s = prs.slides.add_slide(L_TITLE)
text(s, 1.4, 2.4, 10.5, 2.4, [("Danube (O band)", {"size": 34, "bold": True}),
     ("Standing wave, tee cross-sections and over-etch", {"size": 26, "bold": True}),
     ("Slab-width sweep at 1310 nm, wavelength sweep 1270–1330 nm, comparison with measured trends", {"size": 18, "color": MUT})],
     align=PP_ALIGN.CENTER)

# 2 where the cross-sections come from ----------------------------------------
s = new("Where the four cross-sections come from", "Top view of the push-pull modulator (KLayout): red lines = the two simulated cuts")
image(s, D + "klayout_top.png", 0.6, 1.8, h=4.6)
box(s, 7.0, 1.8, 5.8, 4.6, [("Two cuts along the line", {"size": 15, "bold": True, "color": NAVY, "space": 8}),
    B("Outside of tee: full ground electrode, 28 µm wide, 2 µm thick"),
    B("Inside of tee: the slow-wave tee leaves only a 2.0 × 0.5 µm ground stub next to the gap; the signal is unchanged", space=14),
    ("Two process versions", {"size": 15, "bold": True, "color": NAVY, "space": 8}),
    B("Standard: BOX intact"),
    B("Over-etched (process reality): BOX recessed 700 nm wherever the LN slab is removed; gold fills the recess under the electrodes", space=14),
    ("→ 2 cuts × 2 processes = 4 cross-sections", {"size": 14, "bold": True, "color": RED})])

# 3 the four cross-sections ----------------------------------------------------
s = new("The four simulated cross-sections", "Nominal geometry, one arm: the right edge is the signal centre (mirror plane)")
image(s, D + "xs_2x2.png", 0.6, 1.75, w=12.1)
text(s, 0.6, 5.85, 12.2, 1.2, [("λ = 1310 nm · LN film 450 nm, etch 225 nm · rib top 0.8 µm · gap 4.15 µm · signal 10 µm (5 µm per arm) · "
     "slab top width 10.15 µm · slab ends etched at 60° · SiO₂ cap 2.0 × 1.4 µm", {"size": 13, "color": MUT, "space": 6}),
     ("Mesh converged at 1310 nm: 6 nm gold skin (skin depth ≈ 12 nm); IL within ≈ 3 %, Vπ·L within 0.1 %", {"size": 13, "color": MUT})])

# 4 slab-width sweep: IL -------------------------------------------------------
s = new("Slab-width sweep: the IL ripple survives in all four cases", "1310 nm, slab top width 5.15 → 12.15 µm, 100 nm step")
xy_chart(s, 0.6, 1.75, 8.6, 4.6, [("1 outside, standard", ser("1", "IL_dB_per_cm"), RED, 4, 1.75, False),
    ("2 inside, standard", ser("2", "IL_dB_per_cm"), BLUE, 4, 1.75, False),
    ("3 outside, over-etched", ser("3", "IL_dB_per_cm"), LRED, 4, 1.5, True),
    ("4 inside, over-etched", ser("4", "IL_dB_per_cm"), LBLUE, 4, 1.5, True),
    ("nominal 10.15 µm", [(10.15, 0), (10.15, 0.22)], GREY, 0, 1.25, True)],
    (5, 12.5), (0, 0.22), "Slab top width (µm)", "Insertion loss (dB/cm)", legend=True, xmaj=1, ymaj=0.02)
stat(s, 9.5, 1.85, 3.3, 1.2, "≈ 1.3 µm", "ripple period in slab width", NAVY)
stat(s, 9.5, 3.25, 3.3, 1.2, "0.003 → 0.21", "IL range over the sweep (dB/cm)", RED)
stat(s, 9.5, 4.65, 3.3, 1.2, "0.027–0.029", "nominal IL, all four (dB/cm),\non the falling edge of a peak", NAVY)
text(s, 0.6, 6.5, 12.2, 0.6, [("Same peak positions in all four cases; the tee and the over-etch only change peak heights.", {"size": 14, "bold": True, "color": NAVY})])

# 5 why the ripple is the same ---------------------------------------------------
s = new("Why the ripple is the same in all four", "The cavity is the LN slab covered by gold, between the gap edge and the slab end")
cards = [("Cavity unchanged", ["The slab wave guided under the gold is reflected at the slab end",
          "That stretch is identical in all four cases: same gap, slab, 60° end"]),
         ("Electrode size irrelevant", ["Light enters gold only ≈ 12 nm (skin depth)",
          "2 µm or 0.5 µm thick, 28 µm or 2 µm wide: same to the light"]),
         ("Over-etch is out of the way", ["The recess is below the slab plane and beyond the slab end",
          "Only the evanescent tail reaches it: small change in peak heights"])]
for i, (h, items) in enumerate(cards):
    box(s, 0.6 + i * 4.15, 1.9, 3.95, 2.7, [(h, {"size": 16, "bold": True, "color": NAVY, "space": 10})] + [B(t, size=14, space=10) for t in items])
text(s, 0.6, 5.0, 12.2, 1.2, [("Optical loss depends only on the gold geometry seen by the light, not on which electrode is signal or ground: "
     "with a symmetric cross-section each side gives half of the loss.", {"size": 14, "color": INK})])

# 6 inside of tee: double ripple at 8 um ------------------------------------------
s = new("Inside of tee: a second ripple from 8.15 µm", "The stub is fixed (2 µm); the slab end moves with the slab width")
image(s, D + "tee_transition.png", 0.6, 1.7, h=1.75)
xy_chart(s, 0.6, 3.6, 7.4, 3.0, [("1 outside of tee", [p for p in ser("1", "IL_dB_per_cm") if 7.0 <= p[0] <= 12.2], RED, 4, 1.75, False),
    ("2 inside of tee", [p for p in ser("2", "IL_dB_per_cm") if 7.0 <= p[0] <= 12.2], BLUE, 4, 1.75, False)],
    (7, 12.2), (0, 0.15), "Slab top width (µm)", "IL (dB/cm)", legend=True, xmaj=1, ymaj=0.05)
box(s, 8.3, 3.6, 4.5, 3.0, [("Below 8.15 µm", {"size": 14, "bold": True, "color": NAVY, "space": 4}),
    B("Stub wraps the slab end: both sides alike, curves 1 and 2 coincide", space=10),
    ("From 8.15 µm", {"size": 14, "bold": True, "color": NAVY, "space": 4}),
    B("Ground cavity frozen at the stub width: constant ≈ 0.01–0.015 dB/cm", space=4),
    B("Only the signal side still ripples: peaks ≈ halved, troughs raised")])

# 7 Vpi*L ------------------------------------------------------------------------
s = new("Vπ·L: flat with slab width, two small offsets", "Per arm, 1310 nm")
xy_chart(s, 0.6, 1.75, 7.6, 4.6, [("1 outside, standard", ser("1", "VpiL_Vcm"), RED, 4, 1.75, False),
    ("2 inside, standard", ser("2", "VpiL_Vcm"), BLUE, 4, 1.75, False),
    ("3 outside, over-etched", ser("3", "VpiL_Vcm"), LRED, 4, 1.5, True),
    ("4 inside, over-etched", ser("4", "VpiL_Vcm"), LBLUE, 4, 1.5, True)],
    (5, 12.5), (1.80, 2.00), "Slab top width (µm)", "Vπ·L (V·cm)", legend=True, xmaj=1, ymaj=0.05)
box(s, 8.5, 1.75, 4.3, 2.2, [("Inside vs outside of tee: +1.8 %", {"size": 14, "bold": True, "color": NAVY, "space": 6}),
    B("1.937 vs 1.903 V·cm. The small 0.5 µm stub collects fewer field lines than the full 2 µm ground, so less field crosses the LN")])
box(s, 8.5, 4.15, 4.3, 2.2, [("Over-etch: lower Vπ·L at narrow slabs", {"size": 14, "bold": True, "color": NAVY, "space": 6}),
    B("Gold filling the recess sits beside the slab end; with a narrow slab it is close to the gap and pulls more field into the LN"),
    B("−1.9 % at 5.15 µm, −0.1 % at nominal")])

# 8 over-etch summary ------------------------------------------------------------
s = new("Effect of the 700 nm over-etch", "Outside of tee, standard vs over-etched (inside of tee behaves the same)")
image(s, D + "oe_narrow_vs_nominal.png", 0.6, 1.7, h=1.75)
table(s, [["Quantity", "Standard", "Over-etched", "Change"],
          ["Vπ·L at 5.15 µm (V·cm)", "1.902", "1.866", "−1.9 %"],
          ["Vπ·L at 10.15 µm (V·cm)", "1.903", "1.900", "−0.1 %"],
          ["IL at 10.15 µm (dB/cm)", "0.0274", "0.0290", "+6 %"],
          ["1st IL peak, ≈ 5.9 µm (dB/cm)", "0.206", "0.160", "lower, broader"],
          ["Peaks above 8.3 µm", "–", "–", "within 5 %"],
          ["Ripple period / peak positions", "–", "–", "unchanged"]],
      1.6, 3.65, 10.1, [4.2, 1.8, 1.8, 2.3], size=12, row_h=0.38)
text(s, 0.6, 6.55, 12.2, 0.5, [("The over-etch matters only where the slab is narrow and the recessed gold comes close to the gap.", {"size": 14, "bold": True, "color": NAVY})])

# 9 wavelength sweep ---------------------------------------------------------------
s = new("Wavelength sweep 1270–1330 nm", "Over-etched cross-sections (the process reality), slab 10.15 µm, 5 nm step")
xy_chart(s, 0.6, 1.75, 7.8, 4.6, [("3 outside of tee, over-etched", wser("outside of tee, over-etched"), RED, 6, 2.0, False),
    ("4 inside of tee, over-etched", wser("inside of tee, over-etched"), BLUE, 6, 2.0, False)],
    (1270, 1330), (0, 0.09), "Wavelength (nm)", "Insertion loss (dB/cm)", legend=True, xmaj=10, ymaj=0.01)
table(s, [["λ (nm)", "Outside", "Inside"], ["1270", "0.009", "0.008"], ["1290", "0.014", "0.014"], ["1310", "0.029", "0.029"],
          ["1330", "0.083", "0.077"]], 8.8, 1.85, 4.0, [1.2, 1.4, 1.4], size=12, row_h=0.36)
box(s, 8.8, 3.85, 4.0, 2.5, [("Reading", {"size": 14, "bold": True, "color": NAVY, "space": 6}),
    B("Monotonic rise, no ripple peak inside the band"),
    B("Lower flank of the peak just above 1330 nm"),
    B("Inside and outside of tee coincide: the tee fill factor does not matter")])
text(s, 0.6, 6.5, 12.2, 0.5, [("IL in dB/cm; Vπ·L rises linearly, ≈ +2 % per 20 nm, in both cases.", {"size": 13, "color": MUT})])

# 10 comparison with measurements -----------------------------------------------------
s = new("Comparison with measured data: trends", "Three Danube wafers (ASML, over-etched), modulation-section absorption loss")
image(s, D + "measured.png", 0.6, 1.75, w=8.3)
xy_chart(s, 9.1, 1.7, 3.7, 2.75, [("simulated, over-etched", wser("outside of tee, over-etched"), RED, 4, 2.0, False)],
    (1270, 1330), (0, 3.0), "Wavelength (nm)", "dB/cm", legend=False, xmaj=20, ymaj=0.5)
text(s, 9.1, 4.45, 3.7, 0.4, [("Simulation, same 0–3 dB/cm scale", {"size": 11, "color": MUT})], align=PP_ALIGN.CENTER)
box(s, 0.6, 4.95, 12.2, 1.75, [("Trends agree", {"size": 15, "bold": True, "color": NAVY, "space": 6}),
    B("Smooth, slowly rising loss across 1270–1330 nm, no visible ripple peak, as in every measured chip", space=4),
    B("Absolute values are not compared: wafer-to-wafer spread (up to ×10) is set by process variations", space=0)])

# 11 conclusions -------------------------------------------------------------------------
s = new("Conclusions")
items = [("1", "The standing wave is present in all four Danube cross-sections: period ≈ 1.3 µm of slab width at 1310 nm"),
         ("2", "Tee and over-etch do not move the ripple; they only change peak heights"),
         ("3", "Inside of tee, from 8.15 µm the slab passes the stub: fixed ground cavity + signal ripple"),
         ("4", "Vπ·L ≈ 1.90 V·cm (outside) and 1.94 V·cm (inside of tee); the over-etch lowers it only at narrow slabs"),
         ("5", "Nominal slab: 0.03 dB/cm at 1310 nm, rising smoothly to 0.08 dB/cm at 1330 nm"),
         ("6", "The wavelength trend agrees with the measured wafers")]
for i, (n, t) in enumerate(items):
    y = 1.75 + i * 0.82
    shp = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.8), Inches(y), Inches(0.5), Inches(0.5))
    shp.fill.solid(); shp.fill.fore_color.rgb = NAVY; shp.line.fill.background()
    text(s, 0.8, y, 0.5, 0.5, [(n, {"size": 15, "bold": True, "color": RGBColor(255, 255, 255)})], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 1.55, y - 0.02, 11.2, 0.6, [(t, {"size": 16})], anchor=MSO_ANCHOR.MIDDLE)

sldIdLst = prs.slides._sldIdLst
for sid in list(sldIdLst)[:first_new]:
    prs.part.drop_rel(sid.rId); sldIdLst.remove(sid)
out = H + "Danube_results_AFR.pptx"; prs.save(out); print("saved", out, len(prs.slides))
