"""Istanbul EO crosstalk study: slide deck in the company template (python-pptx).
Template = docs/CST_line_extraction.pptx with its slides removed (same as build_meeting.py).
Figures: istanbul_figs.py -> istanbul_img/. Output: ../Istanbul_EO_crosstalk.pptx (revised 2026-11-10: 12 slides)."""
import os, re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.oxml.ns import qn
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); IMG = os.path.join(HERE, "istanbul_img")
NAVY = RGBColor(0x0E, 0x22, 0x68); RED = RGBColor(0xF2, 0x00, 0x13); INK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x5A, 0x60, 0x6E); CARD = RGBColor(0xF1, 0xF3, 0xF8); WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ROW = RGBColor(0xF6, 0xF7, 0xFA); BOX = RGBColor(0xD9, 0xDC, 0xE3); PINK = RGBColor(0xFD, 0xEC, 0xEE)
FONT = "Arial"
prs = Presentation(os.path.join(HERE, "..", "..", "..", "CST_line_extraction.pptx"))
lst = prs.slides._sldIdLst
for s in list(lst):
    prs.part.drop_rel(s.get(qn("r:id"))); lst.remove(s)
L_TITLE, L_BLANK = prs.slide_layouts[11], prs.slide_layouts[12]

def runs(p, t, size, color, bold=False):
    for tok in re.split(r"(\*\*.+?\*\*|_\{.+?\}|\^\{.+?\})", t):
        if not tok: continue
        b, base, s = bold, 0, tok
        if tok.startswith("**"): b, s = True, tok[2:-2]
        elif tok.startswith("_{"): base, s = -25000, tok[2:-1]
        elif tok.startswith("^{"): base, s = 30000, tok[2:-1]
        r = p.add_run(); r.text = s; f = r.font
        f.name, f.size, f.bold = FONT, Pt(size), b; f.color.rgb = color
        if base: r._r.get_or_add_rPr().set("baseline", str(base))

def text(s, x, y, w, h, paras, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, sa=5, bullet=False):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame
    tf.word_wrap = True; tf.margin_left = tf.margin_right = Inches(0.04); tf.margin_top = tf.margin_bottom = Inches(0.02); tf.vertical_anchor = anchor
    for i, para in enumerate([paras] if isinstance(paras, str) else paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align; p.space_after = Pt(sa)
        sz, col, bd = size, color, bold
        if isinstance(para, tuple):
            para, o = para; sz, col, bd = o.get("size", sz), o.get("color", col), o.get("bold", bd)
        if para.startswith("- "):
            para = para[2:]; pPr = p._p.get_or_add_pPr(); pPr.set("marL", str(int(Inches(0.2)))); pPr.set("indent", str(int(-Inches(0.2))))
            bu = pPr.makeelement(qn("a:buChar"), {"char": "•"}); pPr.append(bu)
        runs(p, para, sz, col, bd)
    return tb

def title(s, t, sub=None):
    text(s, 0.55, 0.42, 10.6, 0.7, t, size=28)
    if sub: text(s, 0.6, 1.02, 11.8, 0.4, sub, size=15, color=NAVY, bold=True)

def rect(s, x, y, w, h, fill=CARD, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: sh.adjustments[0] = 0.06
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None: sh.line.fill.background()
    else: sh.line.color.rgb = line; sh.line.width = Pt(1.25)
    sh.shadow.inherit = False
    return sh

def fig(s, name, x, y, w, h, alt=""):
    rect(s, x, y, w, h, fill=WHITE, line=BOX)
    path = os.path.join(IMG, name); W, H = Image.open(path).size; sc = min((w - .1) / W, (h - .1) / H); ww, hh = W * sc, H * sc
    p = s.shapes.add_picture(path, Inches(x + (w - ww) / 2), Inches(y + (h - hh) / 2), Inches(ww), Inches(hh))
    if alt: p._element.nvPicPr.cNvPr.set("descr", alt)

def card(s, x, y, w, h, head, body, hc=NAVY, size=14, fill=CARD):
    rect(s, x, y, w, h, fill=fill)
    text(s, x + 0.15, y + 0.1, w - 0.3, h - 0.15, [(head, {"bold": True, "color": hc, "size": size + 2})] + [(b, {"size": size}) for b in body], sa=4)

def stat(s, x, y, w, h, big, small, col=NAVY):
    rect(s, x, y, w, h)
    text(s, x, y + 0.12, w, 0.95, big, size=36, bold=True, color=col, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.2, y + 1.1, w - 0.4, h - 1.15, small, size=13, color=INK, align=PP_ALIGN.CENTER)

def table(s, x, y, w, rows, col_w, size=12, row_h=0.4, hl=()):
    gt = s.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows))); tb = gt.table
    pr = tb._tbl.tblPr
    for k in ("bandRow", "firstRow"): pr.set(k, "0")
    st = pr.find(qn("a:tableStyleId"))
    if st is not None: pr.remove(st)
    tot = sum(col_w)
    for j, cw in enumerate(col_w): tb.columns[j].width = Inches(w * cw / tot)
    for i, r in enumerate(rows):
        tb.rows[i].height = Inches(row_h)
        for j, v in enumerate(r):
            c = tb.cell(i, j); c.margin_left = c.margin_right = Inches(0.06); c.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = c.text_frame.paragraphs[0]; c.text_frame.word_wrap = True; p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            runs(p, str(v), size, WHITE if i == 0 else INK, bold=(i == 0 or j == 0))
            c.fill.solid(); c.fill.fore_color.rgb = NAVY if i == 0 else (PINK if i in hl else (ROW if i % 2 else WHITE))

def arrow(s, x, y, w, h=0.4):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    a.fill.solid(); a.fill.fore_color.rgb = MUTED; a.line.fill.background(); a.shadow.inherit = False

def step(s, x, y, w, h, tag, head, body, hc=NAVY):
    rect(s, x, y, w, h, fill=CARD)
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.15), Inches(y + 0.15), Inches(0.5), Inches(0.5))
    c.fill.solid(); c.fill.fore_color.rgb = hc; c.line.fill.background(); c.shadow.inherit = False
    tf = c.text_frame; tf.margin_left = tf.margin_right = 0; p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    runs(p, tag, 14, WHITE, True); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    text(s, x + 0.75, y + 0.17, w - 0.85, 0.5, head, size=14.5, bold=True, color=hc)
    text(s, x + 0.15, y + 0.75, w - 0.3, h - 0.8, body, size=12.5, sa=3)

new = lambda: prs.slides.add_slide(L_BLANK)
def note(s, t): s.notes_slide.notes_text_frame.text = t

def eqimg(s, name, x, y, h):
    path = os.path.join(IMG, name + ".png"); W, H = Image.open(path).size
    s.shapes.add_picture(path, Inches(x), Inches(y), Inches(h * W / H), Inches(h))

def caption(s, x, y, w, t, h=0.4): text(s, x, y, w, h, t, size=12, color=MUTED)

PURPLE = RGBColor(0x7A, 0x4B, 0xD1)

# 1 ---------------------------------------------------------------- title
s = prs.slides.add_slide(L_TITLE)
text(s, 0.5, 2.15, 12.33, 1.4, ["Istanbul electro-optical crosstalk:", "simulation and lab measurement comparison"], size=34, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.5, 3.75, 12.33, 0.8, "CST time-domain full-wave simulations · 8.75 mm line pair, 625 µm pitch · module K00626", size=18, color=MUTED, align=PP_ALIGN.CENTER)

# 2 ---------------------------------------------------------------- purpose
s = new(); title(s, "Purpose", "A fast and reliable simulation of the EO crosstalk between adjacent modulators")
fig(s, "model_d_driver.png", 0.5, 1.6, 6.3, 3.8, "CST model of the Istanbul module input: driver carrier, bond wires, launch pads, line pair")
caption(s, 0.5, 5.5, 6.3, "Istanbul full-module model: driver carrier, bond wires, launch pads and the 8.75 mm line pair.", h=0.6)
step(s, 7.05, 1.6, 5.8, 1.6, "1", "Simulate", ["EO crosstalk of an Istanbul line pair and of the full module, from the driver output to the line end."])
step(s, 7.05, 3.4, 5.8, 1.6, "2", "Compare", ["Simulated EO crosstalk against the lab measurement of module K00626."])
step(s, 7.05, 5.2, 5.8, 1.6, "3", "Establish", ["A validated simulation flow for later designs: pitch, terminations, assembly."])

# 3 ---------------------------------------------------------------- difficulty
s = new(); title(s, "Why S-parameters are not sufficient", "The EO crosstalk integrates the victim voltage V(z) along the whole line")
fig(s, "slide3_victim.png", 0.5, 1.55, 6.6, 3.85, "Victim V(z) from fields and from S-parameters with a uniform-pair model")
caption(s, 0.5, 5.5, 6.6, "Same NEXT and FEXT at the ends, different V(z) in between: the uniform-line model does not hold.", h=0.6)
card(s, 7.35, 1.55, 5.5, 1.65, "From S-parameters", ["NEXT and FEXT give the victim at both ends. With γ and Z_{c} of a uniform pair they fix V(z) everywhere."], size=13)
card(s, 7.35, 3.35, 5.5, 2.05, "Why it fails", ["The pair is not uniform: pads, bond wires and driver are folded into γ and Z_{c}. The victim is the small difference of two nearly equal modes (Δn ≈ 0.005): small errors in γ give large errors in V(z)."], hc=RED, size=13)
card(s, 7.35, 5.55, 5.5, 1.35, "Consequence", ["V(z) of both lines is taken from full-wave field monitors (slides 11–13: EO from S-parameters 5–8 dB too high)."], size=13)

# 5 ---------------------------------------------------------------- EO computation
s = new(); title(s, "EO crosstalk from full-wave fields", "CST time-domain solver; E_{y} sampled in both gaps of both lines, every 5 µm along the line")
fig(s, "eo_sampling.png", 0.5, 1.5, 5.6, 4.73, "One line: two gaps, the optical arm in each gap and the field sample points")
text(s, 0.5, 6.3, 5.6, 0.65, "V_{±} ∝ E_{y} at the sample points; same points in both lines, so the constant cancels in X_{EO}. Aggressor: V_{c} ≈ 0; victim: V_{c} ≠ 0. Linear Pockels effect, n_{g} = 2.27, no optical loss.", size=11, color=MUTED)
EQK = 0.58 / 200     # inches per pixel of the equation images (same scale for all)
def eq(name, x, y):
    H = Image.open(os.path.join(IMG, name + ".png")).size[1]; eqimg(s, name, x, y, H * EQK); return y + H * EQK
X0 = 6.45
text(s, X0, 1.45, 6.4, 0.55, "**1. Pockels effect.** The voltage across a gap shifts the optical phase of the arm in that gap; the two arms shift in opposite directions.", size=12)
y = eq("eq5_pockels", X0 + 0.3, 1.98)
text(s, X0 + 0.3, y, 6.1, 0.3, "κ: EO constant (phase per volt and unit length); V_{π}: voltage for a π shift over L.", size=10.5, color=MUTED)
text(s, X0, 2.8, 6.4, 0.55, "**2. Light in transit.** The light enters at t_{0} and reaches z at t_{0} + n_{g}z/c: each arm adds up the voltage it meets on its way.", size=12)
y = eq("eq5_arm", X0 + 0.3, 3.33)
text(s, X0, 3.85, 6.4, 0.3, "**3. Phasor form.** H is the voltage the light sees, averaged along its path.", size=12)
y = eq("eq5_phasor", X0 + 0.3, 4.15); y = eq("eq5_H", X0 + 0.3, y + 0.05)
text(s, X0 + 0.3, y, 6.1, 0.3, "A wave travelling with the light adds up; a backward wave averages out.", size=10.5, color=MUTED)
text(s, X0, 5.33, 6.4, 0.55, "**4. Push-pull.** The output follows φ_{+} − φ_{−}: only the differential gap voltage V_{d} modulates; a common part V_{c} shifts both arms alike and cancels.", size=12)
y = eq("eq5_X", X0 + 0.3, 5.88); eq("eq5_X2", X0 + 0.3, y + 0.04)

# 6 ---------------------------------------------------------------- set-up 1/2
s = new(); title(s, "Simulation set-up (1/2): length, mesh, substrate bottom", "Corrections derived from earlier Istanbul and Cordoba runs, applied to all Istanbul runs")
step(s, 0.5, 1.6, 6.3, 1.65, "1", "Full-length line", ["Istanbul 1–8.75 mm: NEXT grows ≈ L²; the two-mode length extrapolation misses it by 10–30 dB. The 8.75 mm line is simulated directly."], hc=NAVY)
step(s, 0.5, 3.4, 6.3, 1.65, "2", "Mesh refinement", ["Istanbul 3 mm: index 2.113 → 2.138 (1.2 %), i.e. 0.27 rad over 8.75 mm at 60 GHz: relevant for velocity matching. ≥ 4–5 cells across gaps and metal."], hc=NAVY)
step(s, 0.5, 5.2, 6.3, 1.7, "3", "Electric bottom", ["Chip on 40 µm conductive epoxy on Al₂O₃: a conductor under the silicon. Open boundary = unbounded substrate, without the wave guided between electrodes and bottom."], hc=NAVY)
fig(s, "cordoba_bottom.png", 7.05, 1.6, 5.8, 3.4, "Cordoba EO crosstalk with open and electric substrate bottom")
caption(s, 7.05, 5.1, 5.8, "Cordoba 8 mm: the electric bottom changes the EO crosstalk by −10 to +5 dB and adds a ripple. Open-bottom results are not conservative.", h=0.9)

# 7 ---------------------------------------------------------------- set-up 2/2
s = new(); title(s, "Simulation set-up (2/2): accuracy, monitors, excitation", "Validated on the Cordoba 8 mm pair, where the victim is 55–75 dB below the aggressor")
fig(s, "cordoba_accuracy.png", 0.5, 1.6, 6.05, 3.15, "Cordoba EO crosstalk for three solver stopping levels")
fig(s, "cordoba_monitors.png", 6.78, 1.6, 6.07, 3.15, "Cordoba EO crosstalk with monitors every 1 GHz and every 5 GHz")
step(s, 0.5, 4.95, 4.0, 1.95, "4", "Accuracy −40 dB", ["At −27 dB the victim field is 40–240 % wrong (EO up to 18 dB). −40 dB: within 0.6 dB of −44.5 dB above 20 GHz."])
step(s, 4.67, 4.95, 4.0, 1.95, "5", "Monitors every 1 GHz", ["5 GHz spacing misses the ≈ 7 GHz ripple; models fitted to sparse monitors failed prediction tests."])
step(s, 8.84, 4.95, 4.01, 1.95, "6", "One active port", ["Line A input excited, all other ends terminated in the model: the lab drive in one run, 4× less time."])

# 8 ---------------------------------------------------------------- models
s = new(); title(s, "Modular build-up: four models", "(b) and (c) each add one element to (a); (d) adds the driver to (c). Each change is isolated.")
cells = [("model_a_bare.png", "(a) Bare line pair", "8.75 mm, pitch 625 µm. 50 Ω discrete ports at both ends of both lines."),
         ("model_b_termination.png", "(b) Real far-end termination", "Pads on Si through an LN/SiO₂ trench; lumped RS 25 Ω + 2 × RG 50 Ω (50 Ω). Ports at the near end only."),
         ("model_c_pads.png", "(c) Input launch pads", "Launch pads on oxide at the line input; 50 Ω discrete ports at the pads and at the far ends."),
         ("model_d_driver.png", "(d) Driver and bond wires", "Al₂O₃ driver carrier with output traces, 8 bond wires (17 µm); waveguide ports on the carrier traces.")]
for i, (img, head, body) in enumerate(cells):
    x = 0.5 + (i % 2) * 6.28; y = 1.55 + (i // 2) * 2.75
    fig(s, img, x, y, 3.5, 2.55, head)
    text(s, x + 3.65, y + 0.1, 2.45, 2.4, [(head, {"bold": True, "color": NAVY, "size": 14})] + [(body, {"size": 12.5})], sa=4)

# 9 ---------------------------------------------------------------- results
s = new(); title(s, "EO crosstalk: effect of each element", "One EO crosstalk value per frequency (whole 8.75 mm line); levels summarised over 5–60 GHz")
fig(s, "istanbul_eo_abcd.png", 0.5, 1.55, 7.2, 3.98, "EO crosstalk of the four Istanbul runs")
table(s, 0.5, 5.65, 7.2, [["Run", "Median 5–60 GHz", "Maximum 5–60 GHz"],
      ["(a) bare lines", "−38.4 dB", "−33.1 dB at 46 GHz"], ["(b) + real terminations", "−36.7 dB", "−31.9 dB at 37 GHz"],
      ["(c) + launch pads", "−32.8 dB", "−26.1 dB at 48 GHz"], ["(d) + driver (full module)", "−27.3 dB", "−20.1 dB at 29 GHz"]], [2.6, 2.0, 2.6], size=11, row_h=0.26)
table(s, 7.9, 1.55, 4.95, [["Step", "Median change", "Cause"],
      ["(a) → (b)", "+1.5 dB", "≈ 50 Ω like the port of (a); different reflection phase at the far-end pads"],
      ["(a) → (c)", "+5.4 dB", "Pads couple a wave onto B at the line input, then carried along with the light"],
      ["(c) → (d)", "+6.4 dB\n(≥ 10 dB below 10 GHz)", "Driver carrier and bond wires inject a strong victim signal before the line"]], [1.05, 1.25, 2.65], size=11.5, row_h=0.95, hl=(3,))
card(s, 7.9, 5.5, 4.95, 1.45, "Ripple", ["Period 6.2–6.9 GHz in all runs, i.e. two victim contributions 1/Δf ≈ 150 ps apart: one trip along the line (65 ps, S_{21}) plus a slower return (≈ 85 ps, n ≈ 3)."], size=11.5)
note(s, "Median over the 54 monitor frequencies 5-60 GHz of the EO crosstalk in dB (2 and 15 GHz excluded: corrupted export in run c). The curve ripples by 10-20 dB with deep notches: a mean of dB values is pulled down by the notches, a mean of power is dominated by the peaks; the median is the level the curve exceeds at half of the frequencies. Power means: -37.6, -36.0, -31.0, -25.3 dB. Ripple: periodogram of the detrended dB curve, 6.94 / 6.60 / 6.24 / 6.67 GHz for a / b / c / d. One-way group delay of S21 (run a) 64-68 ps (n_g 2.2-2.3); the return at n about 3 is consistent with the wave guided between the electrodes and the conductive bottom.")

# 10 --------------------------------------------------------------- EO vs FEXT
s = new(); title(s, "Full module: EO crosstalk ≈ FEXT", "Where the victim signal is created sets how much of it the light collects")
fig(s, "coupling_paths.png", 0.5, 1.5, 6.2, 4.17, "Coupling along the line and before the line, with the resulting victim profiles")
fig(s, "victim_profile_9GHz.png", 6.95, 1.5, 5.9, 3.13, "Simulated victim field along the line at 9 GHz, runs a, c, d")
table(s, 6.95, 4.75, 5.9, [["EO − FEXT, 5–60 GHz", "(a) bare lines", "(c) + pads", "(d) full module"],
      ["Median", "−4.8 dB", "−1.7 dB", "+0.3 dB"], ["5–95 % range", "−8.9 … −0.7 dB", "−8.9 … +6.0 dB", "−3.2 … +5.0 dB"]], [1.85, 1.35, 1.35, 1.35], size=10.5, row_h=0.3)
card(s, 0.5, 5.85, 6.2, 1.1, "Run (d)", ["The victim is already −20 dB at the line input and stays flat along the line: the extra coupling is in the driver traces or bond wires (not separated in this run)."], size=11)
card(s, 6.95, 5.85, 5.9, 1.1, "Why EO can exceed FEXT", ["FEXT is read at the far end, after 3–4 dB of line loss. EO compares victim and aggressor modulation along the whole line, where both lose alike."], hc=RED, size=11)
note(s, "Idealised profiles: a victim built up uniformly along the line grows linearly from zero; its average over the line is half its end value (-6 dB). A victim injected before the line travels with the light at constant ratio to the aggressor. EO - FEXT percentiles from xtalk_run_a.csv and xtalk_run_d.csv; run (d) EO above FEXT at 56 % of the frequencies. Median |S21|: -2.9 dB (a), -4.3 dB (d).")

# 11 --------------------------------------------------------------- lab
s = new(); title(s, "Comparison with the lab measurement", "Module K00626: simulated EO crosstalk within the spread of the measured curves")
fig(s, "sim_vs_lab.png", 0.5, 1.55, 7.7, 4.2, "Simulated EO crosstalk and two digitized lab curves")
card(s, 8.4, 1.55, 4.45, 1.85, "Lab data", ["Six curves (three pairs, both directions), spread ≈ 10 dB. Two curves digitized from the report image: estimates only."], size=12.5)
card(s, 8.4, 3.55, 4.45, 1.75, "Agreement", ["Simulated median −27 dB, inside the lab range (−19 to −30 dB). Ripple 6.2–6.8 GHz simulated, ≈ 5 GHz measured."], size=12.5)
card(s, 8.4, 5.45, 4.45, 1.45, "Limits", ["A sharper comparison needs numerical lab data. Real driver, assembly and lab settings are not modelled."], hc=RED, size=12.5)
caption(s, 0.5, 5.85, 7.7, "Digitized with WebPlotDigitizer (automeris.io): pixel resolution ≈ 0.2 GHz and 0.15 dB, overlapping curves, notches under-sampled.", h=0.7)

# R1 --------------------------------------------------------------- review: V(z) from S vs fields
s = new(); title(s, "V(z) from S-parameters: aggressor reproduced, victim not", "Same runs, V(z) from the touchstone (uniform coupled pair) and from the gap fields")
fig(s, "review_vz.png", 0.5, 1.45, 12.35, 3.7, "V(z) of both lines from S-parameters and from fields, runs a and c")
text(s, 0.5, 5.25, 6.2, 0.35, "**From S-parameters:** even and odd mode m of a uniform pair", size=12)
for k_, (nm, yy) in enumerate((("eq12_mode", 5.62), ("eq12_V", 6.22), ("eq12_AB", 6.58))):
    H_ = Image.open(os.path.join(IMG, nm + ".png")).size[1]; eqimg(s, nm, 0.75, yy, H_ * 0.0034)
card(s, 6.95, 5.25, 5.9, 1.7, "Why the victim fails", ["(a) V_{B} is the small difference of two nearly equal modes (n_{e} − n_{o} ≈ 0.005): S-parameter errors of −40 dB shift it by 1–6 dB.",
     "(c) The pads are folded into the line: Z_{o} − Z_{e} jumps from 1 to 11 Ω (40 GHz), i.e. the pad coupling is spread along z: victim ≈ +7 dB."], hc=RED, size=11)
note(s, "S route: only port 1 is excited in the runs; the uniform-pair symmetries (mirror A-B, end reversal, reciprocity) fill the 4-port. Field route: line voltage = mean of the two gap voltages; the 2 of 40 samples per 0.2 mm cell that fall on the cell loading are interpolated. Both normalised to line A at the far-end port. Sensitivity: complex noise of -40 / -50 / -60 dB added to S11, S21, S31, S41 (run a) changes the S-route victim by 6 / 3.8 / 1.3 dB at 10 GHz and 1 / 0.5 / 0.1 dB at 40 GHz (median over z); the aggressor by < 0.1 dB.")

# R2 --------------------------------------------------------------- review: EE crosstalk
s = new(); title(s, "EE crosstalk: S-parameters and fields agree", "NEXT and FEXT of runs a, c, d from the touchstone and from the field at the line ends")
fig(s, "review_ee.png", 0.5, 1.5, 12.35, 3.55, "NEXT and FEXT from S-parameters and from fields")
card(s, 0.5, 5.2, 4.0, 1.75, "Definition", ["Aggressor driven at port 1, all ports matched: NEXT = S_{31}, FEXT = S_{41} (victim wave at its near and far end per incident wave)."], size=10.5)
card(s, 4.67, 5.2, 4.0, 1.75, "From fields", ["A matched port without incident wave has V_{j} = b_{j}√Z_{0}: S_{31} = S_{21}·V_{B}(0)/V_{A}(L), S_{41} = S_{21}·V_{B}(L)/V_{A}(L), with the voltage ratios from the fields."], size=10.5)
table(s, 8.84, 5.2, 4.01, [["Field − S, median", "NEXT", "FEXT"], ["(a) bare line", "−2.0 dB", "−1.7 dB"], ["(c) + pads", "−0.1 dB", "−2.6 dB"], ["(d) + driver", "+0.7 dB", "−1.1 dB"]], [1.81, 1.1, 1.1], size=10.5, row_h=0.4)
note(s, "Point-by-point scatter 2-6 dB: ripple shifts and the accuracy of a victim 30-60 dB below the aggressor (solver -40 dB, one sample per gap). In (c) and (d) the S-parameter NEXT is at the pad or driver port, the field value at the line input: the levels still agree. EE crosstalk is a port quantity: the S-parameters give it directly.")

# R3 --------------------------------------------------------------- review: EO crosstalk
s = new(); title(s, "EO crosstalk: the S-parameter route fails on the victim", "X = H[V_{B}] / H[V_{A}], H[V] = (1/L) ∫ V(z) exp(jβ_{o}(z − L)) dz, with V(z) from S or from the fields")
fig(s, "review_eo.png", 0.5, 1.5, 12.35, 3.55, "EO crosstalk from the S-parameter V(z) and from the fields")
table(s, 0.5, 5.2, 6.4, [["5–60 GHz, median", "EO from fields", "EO from S", "S − fields"], ["(a) bare line", "−38.4 dB", "−32.3 dB", "+5.2 dB"], ["(c) + pads", "−32.8 dB", "−24.8 dB", "+7.5 dB"], ["(d) + driver", "−27.3 dB", "not possible", "–"]], [1.6, 1.6, 1.6, 1.6], size=10.5, row_h=0.4)
card(s, 7.15, 5.2, 5.7, 1.75, "Meaning", ["The light integrates the victim V(z), which the S-parameters do not fix: the S route overestimates by 5–8 dB, more with pads. FEXT ≈ EO only in (d), where the victim is injected before the line (slide 9)."], hc=RED, size=10.5)
note(s, "Push-pull with symmetric gaps, n_g 2.27, 50 ohm source and loads. Run d: the touchstone export failed, the ASCII S-parameters are magnitudes only (no phase), so no V(z) can be built from them.")

# R4 --------------------------------------------------------------- review: INTERCONNECT
s = new(); title(s, "Lumped-block crosstalk model in INTERCONNECT", "Proposal: cascade of lumped coupled-line cells, each driving a lumped EO phase cell")
card(s, 0.5, 1.6, 4.0, 2.5, "Feasibility", ["- Possible: it is the discrete form of the same integral H[V].",
     "- Cells ≤ λ_{RF}/20 ≈ 0.1 mm at 60 GHz: ≈ 90 cells per line, 180 voltage taps and optical delays."], size=13.5)
card(s, 4.67, 1.6, 4.0, 2.5, "Physics", ["- Same equations as the Python cascade: no new information.",
     "- Result at best as good as the cell parameters it is given."], size=13.5)
card(s, 8.84, 1.6, 4.01, 2.5, "Inputs", ["- Each cell needs γ, Z_{c} and the coupling of the victim: the quantities the S-parameters do not give accurately (slides 11–13).",
     "- Pads, wires, driver as S-blocks give only port quantities."], hc=RED, size=13.5)
card(s, 0.5, 4.35, 6.1, 1.9, "Status", ["A scripted coupled-electrode element (two-mode line, exact 4-port and V(z) integrals) already exists in INTERCONNECT. It reproduces the Python model and inherits its limits on the victim."], size=14)
card(s, 6.75, 4.35, 6.1, 1.9, "Recommendation", ["EO crosstalk from the CST fields (Python), as in this study. INTERCONNECT only at link level: the simulated crosstalk transfer function as a black box for eye and BER studies."], hc=NAVY, size=14)
note(s, "lambda_RF at 60 GHz with n about 2.3: 2.2 mm. The coupling built up in the cells is the two-mode description, which misses the bottom-guided slow wave and the pad/driver injection; both dominate the module crosstalk (slides 8, 9).")

# 12 --------------------------------------------------------------- conclusions
s = new(); title(s, "Conclusions", "")
stat(s, 0.5, 1.45, 3.95, 2.0, "−27 dB", "Simulated EO crosstalk, full module (median)", col=PURPLE)
stat(s, 4.69, 1.45, 3.95, 2.0, "−19 to −30 dB", "Lab range, module K00626 (medians)", col=RED)
stat(s, 8.88, 1.45, 3.97, 2.0, "≈ 6.5 / 5 GHz", "Ripple period, simulation / lab")
card(s, 0.5, 3.75, 3.95, 2.6, "Method", ["- EO crosstalk from full-wave fields: no mode model.",
     "- Full length, fine mesh, electric bottom, −40 dB, 1 GHz monitors, one active port."], size=14)
card(s, 4.69, 3.75, 3.95, 2.6, "Physics", ["- Each module element raises the EO crosstalk; the driver side most.",
     "- Coupling at the input travels with the light: EO ≈ FEXT, not FEXT − 6 dB."], size=14)
card(s, 8.88, 3.75, 3.97, 2.6, "Next", ["- Numerical lab data.",
     "- Optical-mode overlap instead of point sampling.",
     "- Real driver and assembly variations."], hc=RED, size=14)

out = os.path.join(HERE, "..", "Istanbul_EO_crosstalk.pptx"); prs.save(out); print("saved", os.path.abspath(out))
