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
s = new(); title(s, "Why S-parameters are not sufficient", "The EO crosstalk depends on the voltage profile V(z) along the whole victim line")
fig(s, "fext_ambiguity.png", 0.5, 1.6, 6.4, 3.65, "Two victim profiles with the same FEXT but different EO crosstalk")
caption(s, 0.5, 5.35, 6.4, "Same FEXT, different EO crosstalk: the optical phase integrates V(z), not its end value.", h=0.6)
card(s, 7.15, 1.6, 5.7, 1.65, "Port data", ["S-parameters describe the four line ends only. NEXT and FEXT are the victim signal at its near and far end."])
card(s, 7.15, 3.4, 5.7, 1.85, "Optical response", ["The light collects the field along the full length, in step with its own travel time. Equal FEXT can give EO crosstalk differing by 6 dB."])
card(s, 7.15, 5.4, 5.7, 1.5, "Consequence", ["V(z) of both lines is taken from full-wave field monitors, every 1 GHz from 1 to 60 GHz (victim ripple period ≈ 6.5 GHz)."], hc=RED)

# 4 ---------------------------------------------------------------- eigenmode
s = new(); title(s, "Eigenmode solver: physical insight, no quantitative crosstalk", "Six-mode description of the Cordoba 8 mm pair (same platform, simpler geometry)")
card(s, 0.5, 1.6, 6.0, 2.45, "Strengths", ["- Fast: one periodic cell, about 2 min per solution.",
     "- Lists the modes a line supports: even/odd coplanar pair, slot modes and, with a conductive bottom, a slow wave between all electrodes and the bottom (index ≈ 3.2).",
     "- Identified that slow wave as the backward wave found under line B in the time-domain fields."], size=13)
card(s, 0.5, 4.2, 6.0, 2.7, "Limits", ["- Infinite uniform cell: no line ends, hence no reflections, end conversion or fields localised near the pads.",
     "- No pads, wire bonds, driver or bends.",
     "- Line B: misfit of 5–15 % up to 30 GHz, about 100 % at 60 GHz; one prediction test passed out of six."], hc=RED, size=13)
fig(s, "eigen_error_scale.png", 6.75, 1.6, 6.1, 3.3, "Error scale of the mode description of line A compared with the line B field")
card(s, 6.75, 5.05, 6.1, 1.85, "Why line B fails", ["The imperfections in the description of line A (red) exceed the whole victim field (green). Mode model abandoned: the EO crosstalk is taken directly from the time-domain fields."], size=13)

# 5 ---------------------------------------------------------------- EO computation
s = new(); title(s, "EO crosstalk from full-wave fields", "CST time-domain solver; E_{y} exported in both gaps of both lines, every 5 µm")
text(s, 0.5, 1.55, 6.4, 0.35, "**1.** Light enters at t_{0} and reaches z at", size=13); eqimg(s, "eq_time", 0.9, 1.92, 0.36)
text(s, 0.5, 2.4, 6.4, 0.35, "**2.** Phase of arm k (κ: EO constant, equal for all arms)", size=13); eqimg(s, "eq_phase", 0.9, 2.8, 0.5)
text(s, 0.5, 3.45, 6.4, 0.35, "**3.** Phasor field E(z)·exp(jωt): Δφ_{k} = κL·Re{H_{k}·exp(jωt_{0})}, with", size=13); eqimg(s, "eq_H", 0.9, 3.85, 0.6)
text(s, 0.5, 4.6, 6.4, 0.35, "**4.** Push-pull (difference of the two gaps) and crosstalk", size=13); eqimg(s, "eq_pp", 0.9, 5.0, 0.5)
text(s, 0.5, 5.65, 6.4, 1.2, "The integral is evaluated as a sum over the 5 µm samples. Backward waves meet the light with a phase that rotates along the line: their contributions cancel to a small residual. Forward waves keep their phase and add up.", size=12, color=MUTED)
table(s, 7.1, 1.6, 5.75, [["Assumption", "Assessment"],
      ["Full-wave field: forward, backward, substrate waves, reflections", "Rigorous: no mode model"],
      ["Linear Pockels effect, small signal, E_{y} only", "Standard"],
      ["Optical group index 2.27, constant; no optical loss", "Standard, minor"],
      ["E_{y} at one point per gap (x = 1.275 µm, 5 µm from centre), not an optical-mode overlap", "Weakness: level depends on the point (2.2 dB for 2.5 µm); ratio partly compensates"],
      ["Δz = 5 µm; solver stopped at −40 dB", "≤ 0.6 dB above 20 GHz, 1–2 dB below 15 GHz"]], [3.1, 2.65], size=11.5, row_h=0.88, hl=(4,))

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
s = new(); title(s, "EO crosstalk: effect of each element", "Medians over 5–60 GHz (2 and 15 GHz excluded: corrupted export in run c)")
fig(s, "istanbul_eo_abcd.png", 0.5, 1.55, 7.2, 4.1, "EO crosstalk of the four Istanbul runs")
table(s, 7.9, 1.55, 4.95, [["Step", "EO change", "Cause"],
      ["(a) → (b)", "+1.5 dB", "≈ 50 Ω like the port of (a); different reflection phase at the far-end pads"],
      ["(a) → (c)", "+5.4 dB", "Pads couple a wave onto B at the line input, then carried along with the light"],
      ["(c) → (d)", "+6.4 dB\n(≥ 10 dB below 10 GHz)", "Driver carrier and bond wires inject a strong victim signal before the line"]], [1.05, 1.25, 2.65], size=11.5, row_h=1.0, hl=(3,))
card(s, 7.9, 5.75, 4.95, 1.15, "Ripple", ["Period 6.2–6.8 GHz in all four runs: a property of the line (round trip ≈ 150 ps)."], size=12.5)
text(s, 0.5, 5.8, 7.2, 1.0, "Bare line: −38.4 dB · real termination: −36.7 dB · launch pads: −32.8 dB · full module: −27.3 dB", size=13, color=MUTED)

# 10 --------------------------------------------------------------- EO vs FEXT
s = new(); title(s, "Full module: EO crosstalk ≈ FEXT", "The driver-side coupling places the victim signal at the line input")
fig(s, "victim_profile_9GHz.png", 0.5, 1.55, 6.4, 3.5, "Victim field along the line at 9 GHz for runs a, c, d")
cd = CategoryChartData(); cd.categories = ["(a) bare line", "(c) launch pads", "(d) full module"]; cd.add_series("EO − FEXT (dB)", (-4.8, -1.7, 0.3))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(7.15), Inches(1.55), Inches(5.7), Inches(3.5), cd); ch = gf.chart
ch.has_legend = False; ch.has_title = True; ch.chart_title.text_frame.text = "EO − FEXT, median 5–60 GHz (dB)"
r0 = ch.chart_title.text_frame.paragraphs[0].runs[0]; r0.font.size = Pt(13); r0.font.bold = True; r0.font.name = FONT; r0.font.color.rgb = INK
pl = ch.plots[0]; pl.has_data_labels = True; dl = pl.data_labels; dl.number_format = '+0.0;−0.0'; dl.number_format_is_linked = False
dl.font.size = Pt(12); dl.font.name = FONT; dl.position = XL_LABEL_POSITION.OUTSIDE_END
ser = pl.series[0]; ser.format.fill.solid(); ser.format.fill.fore_color.rgb = NAVY; ser.invert_if_negative = False
va = ch.value_axis; va.maximum_scale = 2; va.minimum_scale = -8; va.major_unit = 2; va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = BOX; va.tick_labels.font.size = Pt(11); va.tick_labels.font.name = FONT
from pptx.enum.chart import XL_TICK_LABEL_POSITION
ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW; ch.category_axis.tick_labels.font.size = Pt(11); ch.category_axis.tick_labels.font.name = FONT
card(s, 0.5, 5.2, 6.4, 1.7, "Observation", ["In (d) the victim field is already −20 dB at the line input and stays constant along the line (3 and 9 GHz); in (a) and (c) it is −50 to −70 dB. The added coupling lies between the driver port and the line input (carrier traces or bond wires, not separated)."], size=12.5)
card(s, 7.15, 5.2, 5.7, 1.7, "Consequence", ["A victim wave present from the input travels with the light over the full length: EO ≈ FEXT. Coupling built along the line gives EO ≈ FEXT − 6 dB (bare line: −4.8 dB)."], hc=RED, size=12.5)

# 11 --------------------------------------------------------------- lab
s = new(); title(s, "Comparison with the lab measurement", "Module K00626: simulated EO crosstalk within the spread of the measured curves")
fig(s, "sim_vs_lab.png", 0.5, 1.55, 7.7, 4.2, "Simulated EO crosstalk and two digitized lab curves")
card(s, 8.4, 1.55, 4.45, 1.85, "Lab data", ["Six curves (three pairs, both directions), spread ≈ 10 dB. Two curves digitized from the report image: estimates only."], size=12.5)
card(s, 8.4, 3.55, 4.45, 1.75, "Agreement", ["Simulated median −27 dB, inside the lab range (−19 to −30 dB). Ripple 6.2–6.8 GHz simulated, ≈ 5 GHz measured."], size=12.5)
card(s, 8.4, 5.45, 4.45, 1.45, "Limits", ["A sharper comparison needs numerical lab data. Real driver, assembly and lab settings are not modelled."], hc=RED, size=12.5)
caption(s, 0.5, 5.85, 7.7, "Digitized with WebPlotDigitizer (automeris.io): pixel resolution ≈ 0.2 GHz and 0.15 dB, overlapping curves, notches under-sampled.", h=0.7)

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
