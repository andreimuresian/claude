"""Istanbul EO crosstalk study: slide deck in the company template (python-pptx).
Template = docs/CST_line_extraction.pptx with its slides removed (same as build_meeting.py).
Figures: istanbul_figs.py -> istanbul_img/. Output: ../Istanbul_EO_crosstalk.pptx"""
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

# ---------------------------------------------------------------- 1 title
s = prs.slides.add_slide(L_TITLE)
text(s, 0, 2.15, 13.33, 1.4, ["Electro-optic crosstalk of the Istanbul module:", "simulation step by step, and comparison with the lab"], size=34, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0, 3.75, 13.33, 0.8, "CST time-domain runs (a)–(d): bare lines, real terminations, launch pads, driver · 8.75 mm lines, 625 µm pitch", size=18, color=MUTED, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------- 2 summary
s = new(); title(s, "Summary", "The full-module simulation falls inside the spread of the lab measurements")
stat(s, 0.5, 1.6, 3.95, 2.25, "−27 dB", "Simulated EO crosstalk, full module (median 5–60 GHz)", col=RGBColor(0x7A, 0x4B, 0xD1))
stat(s, 4.69, 1.6, 3.95, 2.25, "−19 / −30 dB", "Lab, the two directions of one line pair (median, read from a plot)", col=RED)
stat(s, 8.88, 1.6, 3.95, 2.25, "6.4 / 5 GHz", "Ripple period: simulation / lab (worst pair)")
card(s, 0.5, 4.15, 6.05, 2.75, "What we learned", ["Each piece added to the model raises the EO crosstalk: from −38 dB (bare lines) to −27 dB (full module).",
     "The driver side changes the picture most: strong crosstalk already at a few GHz and a regular ripple.",
     "The rule of thumb \"EO = FEXT − 6 dB\" holds only for bare lines; in the module EO ≈ FEXT."])
card(s, 6.78, 4.15, 6.07, 2.75, "Open points", ["Simulation and lab differ by up to 8 dB for the worst direction; the two lab directions differ by 10 dB.",
     "Next: real driver data, numeric lab data, and a few sensitivity runs (wires, glue, chip edge)."], hc=RED)
note(s, "EO crosstalk = modulation of line B's light caused by driving line A, relative to line A's own modulation.")

# ---------------------------------------------------------------- 3 what we compute
s = new(); title(s, "What the EO crosstalk is and how we get it", "Straight from the simulated fields: no circuit or mode model in between")
step(s, 0.5, 1.6, 3.95, 2.6, "1", "Drive line A only", ["CST time-domain run, one excited port: the aggressor. Line B is terminated as in the module."])
arrow(s, 4.55, 2.7, 0.5)
step(s, 5.15, 1.6, 3.95, 2.6, "2", "Read the field in the gaps", ["Field exported along both gaps of both lines, every 5 µm, at 60 frequencies (1–60 GHz)."])
arrow(s, 9.2, 2.7, 0.5)
step(s, 9.8, 1.6, 3.05, 2.6, "3", "Follow the light", ["Add up the field the light meets while it travels along each line."])
card(s, 0.5, 4.5, 6.05, 2.4, "The key idea", ["The light travels together with the electrical wave on its own line.",
     "A wave on line B that travels in the same direction as the light keeps modulating it: it counts.",
     "A wave travelling the opposite way changes sign many times as the light passes: it averages out."])
card(s, 6.78, 4.5, 6.07, 2.4, "Result", ["**EO crosstalk = (modulation of B) / (modulation of A)**, both lines driven in push-pull.",
     "Optical group index 2.27. Same method for every run, so the runs compare one to one."])

# ---------------------------------------------------------------- 4 section: setup
s = new(); title(s, "Simulation set-up: lessons from the Cordoba runs", "Six choices, each one backed by a Cordoba result")
rows = [["Setting", "Before", "Now", "Why (Cordoba evidence)"],
        ["Mesh", "6 cells in the gap", "finer (≥ 4–5 cells, 60 steps/λ)", "line speed changed by 1–2 % on refinement"],
        ["Device width", "21 µm beyond ground", "≈ 400–625 µm", "victim field changed by 20 %, EO by 1–3 dB"],
        ["Bottom of the silicon", "open", "electric (conductive glue)", "adds a slow substrate wave and the ~7 GHz ripple"],
        ["Solver accuracy", "−27 dB", "−40 dB", "at −27 dB the victim field was 40–240 % wrong"],
        ["Field monitors", "every 5 GHz", "every 1 GHz", "5 GHz steps miss a 7 GHz ripple"],
        ["Excited ports", "4", "1 (others terminated)", "4× shorter runs; matches the lab drive"]]
table(s, 0.5, 1.6, 12.35, rows, [2.2, 2.2, 2.9, 5.0], size=13, row_h=0.62)
text(s, 0.5, 6.15, 12.35, 0.8, "Why so strict: line B's field is 30–75 dB below line A's. Small numerical errors on A are large errors on B.", size=14, color=MUTED)

# ---------------------------------------------------------------- 5 width + bottom
s = new(); title(s, "Model the chip as it is mounted: width and bottom", "Cordoba 8 mm, EO crosstalk at 12 frequencies")
fig(s, "cordoba_width.png", 0.5, 1.55, 6.05, 3.25, "Cordoba EO crosstalk, narrow vs wide substrate")
fig(s, "cordoba_bottom.png", 6.78, 1.55, 6.07, 3.25, "Cordoba EO crosstalk, open vs electric bottom")
card(s, 0.5, 5.0, 6.05, 1.9, "Larger device width", ["With the side boundary 21 µm from the outer ground, part of the victim field was cut off: EO 1–3 dB too low.",
     "Istanbul check: widening from ≈ 400 to 625 µm changed EO by only 0.7 dB."], size=14)
card(s, 6.78, 5.0, 6.07, 1.9, "Electric bottom", ["The chip sits on conductive glue. A conductor under the silicon guides a slow wave (index ≈ 3.1) under all the metal.",
     "EO changes by −10 to +5 dB and gets a ripple. Leaving it out is not conservative."], size=14)

# ---------------------------------------------------------------- 6 accuracy + monitors
s = new(); title(s, "Let the solver finish, and sample finely", "Cordoba 8 mm, electric bottom")
fig(s, "cordoba_accuracy.png", 0.5, 1.55, 6.05, 3.25, "EO crosstalk vs solver stopping level")
fig(s, "cordoba_monitors.png", 6.78, 1.55, 6.07, 3.25, "EO crosstalk sampled every 1 GHz vs every 5 GHz")
card(s, 0.5, 5.0, 6.05, 1.9, "Accuracy −40 dB", ["Stopping at −27 dB leaves energy in the structure: fine for line A, wrong for the weak line B (EO up to 18 dB off).",
     "−40 dB agrees with −44.5 dB within 0.6 dB above 20 GHz (1–2 dB below 15 GHz)."], size=14)
card(s, 6.78, 5.0, 6.07, 1.9, "Monitors every 1 GHz", ["The EO crosstalk ripples with a period of about 7 GHz. Every 5 GHz the dips fall between samples.",
     "Monitors do not slow the solver (7.0 ms per step with 60 monitors)."], size=14)

# ---------------------------------------------------------------- 7 mesh + one port
s = new(); title(s, "Finer mesh and one active port", "Accuracy where it matters, computing time where it does not")
table(s, 0.5, 1.6, 6.3, [["Istanbul 3 mm line", "Coarse", "Refined"], ["Line index (30 GHz)", "2.113", "2.138"],
      ["NEXT (30 GHz)", "−45.9 dB", "−45.8 dB"], ["FEXT (30 GHz)", "−50.6 dB", "−50.9 dB"], ["S21 (30 GHz)", "−0.99 dB", "−1.18 dB"]], [2.6, 1.8, 1.8], size=13, row_h=0.5, hl=(1,))
card(s, 0.5, 4.3, 6.3, 2.6, "Why the mesh matters for EO", ["Refining the mesh changed the crosstalk by less than 0.5 dB, but the speed of the wave by 1–2 %.",
     "The EO crosstalk depends on how well the electrical wave keeps pace with the light. Over 8.75 mm, 1 % in speed is a visible error at high frequency.",
     "Rule: at least 4–5 cells across each gap and across the metal."], size=14)
card(s, 7.05, 1.6, 5.8, 2.45, "One excited port, three idle", ["Every excited port is a full run (Cordoba, −40 dB: 12 h on GPU).",
     "Exciting all four ports would take ~4× longer."], size=14)
card(s, 7.05, 4.3, 5.8, 2.6, "Why one is enough", ["In the lab only line A is driven. The other ends are terminated inside the model (resistors, driver port), so one run is exactly the lab situation.",
     "Four ports are needed only to change terminations afterwards."], size=14)

# ---------------------------------------------------------------- 8 eigenmode
s = new(); title(s, "Why the eigenmode route was stopped", "It explained the physics but could not give reliable numbers")
card(s, 0.5, 1.6, 4.0, 3.0, "What it is", ["Solves one short slice of an infinitely long, straight line and returns its modes.",
     "Idea: rebuild line B's field as a sum of six modes."])
card(s, 4.67, 1.6, 4.0, 3.0, "Why it failed", ["Line B is 55–75 dB below line A. The two solvers differ in line index by 0.004–0.01: this mismatch is as large as B itself.",
     "Fits got worse above 30 GHz; prediction tests passed once in six."], hc=RED)
card(s, 8.84, 1.6, 4.01, 3.0, "Why it cannot help the module", ["A periodic slice has no pads, no driver, no bends, no terminations: exactly the parts that drive the module crosstalk."], hc=RED)
card(s, 0.5, 4.85, 12.35, 2.05, "What we keep from it", ["The slow wave between the metal and the conductive glue (index ≈ 3.1), and that the ripple comes from waves making a round trip along the chip.",
     "The time-domain fields give the EO crosstalk directly, for any geometry: that is the route for all module runs."])

# ---------------------------------------------------------------- 9 build-up overview
s = new(); title(s, "Istanbul: building the module piece by piece", "Four runs, one piece added each time, same settings")
fig(s, "module_model.png", 0.5, 1.55, 5.0, 3.0, "CST model of the full module: driver carrier, bond wires, launch pads, lines")
fig(s, "istanbul_eo_abcd.png", 5.7, 1.55, 7.15, 3.9, "EO crosstalk of runs a to d")
table(s, 0.5, 4.75, 5.0, [["Run", "Added", "EO median"], ["(a)", "bare lines", "−38.4 dB"], ["(b)", "real terminations", "−36.7 dB"],
      ["(c)", "launch pads", "−32.8 dB"], ["(d)", "driver + wires", "−27.3 dB"]], [0.8, 2.4, 1.8], size=12.5, row_h=0.42, hl=(4,))
text(s, 5.7, 5.6, 7.15, 1.3, ["Medians over 5–60 GHz. 2 and 15 GHz left out (corrupted export in run c).",
     "Line A (aggressor) at y = 0, line B (victim) 625 µm away."], size=12, color=MUTED)

# ---------------------------------------------------------------- 10 a -> b
s = new(); title(s, "Step (a) → (b): real terminations", "+1.5 dB median; more ripple")
fig(s, "step_ab.png", 0.5, 1.55, 7.3, 4.1, "EO crosstalk, run a vs run b")
card(s, 8.05, 1.55, 4.8, 2.6, "What changes", ["The 50 Ω port at the far end is replaced by the real termination: about 40 Ω on silicon pads.",
     "Part of line A's wave is now reflected back."], size=14)
card(s, 8.05, 4.35, 4.8, 2.55, "Why EO rises", ["The reflected wave runs backward on A. The crosstalk it creates on B runs forward, with the light, so it counts.",
     "Each round trip adds a contribution with a different phase: dips every 6.5–7 GHz."], size=14)
text(s, 0.5, 5.8, 7.3, 1.0, "The ripple period is set by the time a wave needs to go along the line and back.", size=13, color=MUTED)

# ---------------------------------------------------------------- 11 b -> c
s = new(); title(s, "Step (b) → (c): launch pads", "+3.6 dB median vs (b); EO rises more than FEXT")
fig(s, "step_bc.png", 0.5, 1.55, 7.3, 4.1, "EO crosstalk, run b vs run c")
card(s, 8.05, 1.55, 4.8, 2.6, "What changes", ["Wide launch pads at the line input. Their field spreads further sideways than the narrow line's.",
     "Compared with (a): NEXT +6.1 dB, FEXT +3.7 dB, EO +5.4 dB (medians)."], size=14)
card(s, 8.05, 4.35, 4.8, 2.55, "Why EO rises more than FEXT", ["The pads couple a wave onto B right at the entrance. It then travels with the light over the full 8.75 mm.",
     "A head start counts in full; crosstalk built along the line counts only half."], size=14)

# ---------------------------------------------------------------- 12 c -> d
s = new(); title(s, "Step (c) → (d): the driver", "+6.4 dB median vs (c); 10 dB or more below 10 GHz")
fig(s, "step_cd.png", 0.5, 1.55, 7.3, 4.1, "EO crosstalk, run c vs run d")
card(s, 8.05, 1.55, 4.8, 2.05, "What changes", ["Driver carrier (alumina) with its traces, and eight bond wires to the launch pads. The driver itself is an ideal matched source."], size=14)
card(s, 8.05, 3.75, 4.8, 3.15, "Why the low frequencies change most", ["Crosstalk built along the lines grows with frequency: below 10 GHz it is very weak (runs a–c).",
     "The driver side adds coupling that does not need high frequency: return currents shared by the carrier and the wires, and a wave guided by the whole metal over the conductive bottom."], size=14)
text(s, 0.5, 5.8, 7.3, 1.1, ["Most likely explanation, consistent with all runs; not yet proven by a dedicated test."], size=13, color=MUTED)

# ---------------------------------------------------------------- 13 ripple of d
s = new(); title(s, "The ripple of the full module is a round trip", "Peaks every 6.4 GHz, the same in NEXT, FEXT and EO")
fig(s, "run_d_ports.png", 0.5, 1.55, 7.3, 4.1, "Run d: NEXT, FEXT and EO crosstalk")
card(s, 8.05, 1.55, 4.8, 2.55, "One wave, two speeds", ["Out along the line at the line's speed (index 2.23), back under it on the slow substrate wave (index ≈ 3.1)."], size=14)
card(s, 8.05, 4.25, 4.8, 2.65, "The numbers match", ["Round trip over 8.75 mm: 156 ps → one ripple every 6.4 GHz, as simulated.",
     "Cordoba (8 mm): 143 ps → 7.0 GHz, as found there."], size=14)
text(s, 0.5, 5.8, 7.3, 1.1, "NEXT and FEXT at the same level, with the same ripple: the crosstalk no longer comes mainly from the parallel lines.", size=13, color=MUTED)

# ---------------------------------------------------------------- 14 why -6 dB fails
s = new(); title(s, "Why \"EO = FEXT − 6 dB\" no longer holds", "It assumes all the crosstalk is built up along the line")
fig(s, "eo_vs_fext_a_d.png", 0.5, 1.55, 8.3, 2.9, "EO crosstalk vs FEXT, runs a and d")
cd = CategoryChartData(); cd.categories = ["Cordoba", "(a)", "(c)", "(d)"]; cd.add_series("EO − FEXT (dB)", (-6.0, -4.8, -1.7, 0.3))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(9.0), Inches(1.55), Inches(3.85), Inches(2.9), cd); ch = gf.chart
ch.has_legend = False; ch.has_title = True; ch.chart_title.text_frame.text = "EO − FEXT, median (dB)"
tp = ch.chart_title.text_frame.paragraphs[0]; tp.runs[0].font.size = Pt(12); tp.runs[0].font.bold = True; tp.runs[0].font.name = FONT; tp.runs[0].font.color.rgb = INK
pl = ch.plots[0]; pl.has_data_labels = True; dl = pl.data_labels; dl.number_format = '+0.0;−0.0'; dl.number_format_is_linked = False
dl.font.size = Pt(11); dl.font.name = FONT; dl.position = XL_LABEL_POSITION.OUTSIDE_END
ser = pl.series[0]; ser.format.fill.solid(); ser.format.fill.fore_color.rgb = NAVY; ser.invert_if_negative = False
va = ch.value_axis; va.maximum_scale = 2; va.minimum_scale = -8; va.major_unit = 2; va.has_major_gridlines = True
va.major_gridlines.format.line.color.rgb = BOX; va.tick_labels.font.size = Pt(10); va.tick_labels.font.name = FONT
ch.category_axis.tick_labels.font.size = Pt(11); ch.category_axis.tick_labels.font.name = FONT
from pptx.enum.chart import XL_TICK_LABEL_POSITION
ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
card(s, 0.5, 4.7, 6.05, 2.2, "Built along the line → −6 dB", ["On matched bare lines B's wave grows from zero at the input to its full value (FEXT) at the far end.",
     "The light sees the average: half the far-end value, i.e. −6 dB."], size=14)
card(s, 6.78, 4.7, 6.07, 2.2, "Injected at the input → 0 dB", ["Pads and driver put crosstalk on B before the line starts. That wave travels with the light all the way: the light sees it in full.",
     "The more of the crosstalk comes from the input, the closer EO gets to FEXT."], hc=RED, size=14)

# ---------------------------------------------------------------- 15 lab data
s = new(); title(s, "Lab measurements and how we read them", "Module K00626 (SN 6A077700): six crosstalk curves")
fig(s, "lab_measurement_K00626.png", 0.5, 1.55, 7.6, 3.85, "Lab measurement of the module: signals and EO crosstalk")
card(s, 8.3, 1.55, 4.55, 2.3, "Large spread", ["Three line pairs, both directions: up to ~10 dB between curves at the same frequency.",
     "MZ3toMZ4 is the worst; its reverse MZ4toMZ3 is among the best."], size=14)
card(s, 8.3, 4.0, 4.55, 2.9, "Digitized with WebPlotDigitizer", ["automeris.io: load the picture, click two known values on each axis, click points along a curve, export the numbers.",
     "Done for MZ3toMZ4 (orange, 87 points) and MZ4toMZ3 (blue, 93 points)."], size=14)
text(s, 0.5, 5.55, 7.6, 1.35, ["**Only an estimate:** in the shared picture one pixel is about 0.2 GHz and 0.15 dB; overlapping curves of similar colour; deep dips fall between the clicked points; for the blue curve the axis scaling was reconstructed from the dip positions."], size=12.5, color=INK)

# ---------------------------------------------------------------- 16 sim vs lab
s = new(); title(s, "Simulation vs lab", "The simulation lies between the two directions of the same line pair")
fig(s, "sim_vs_lab.png", 0.5, 1.55, 7.7, 4.15, "Simulated EO crosstalk vs the two digitized lab curves")
table(s, 8.4, 1.55, 4.45, [["5–60 GHz", "Median", "Max", "Ripple"], ["Lab MZ3toMZ4", "−19.3", "−14.3", "5.0 GHz"],
      ["Simulation (d)", "−27.3", "−20.1", "6.4–6.9 GHz"], ["Lab MZ4toMZ3", "−29.6", "−22.5", "9.2 GHz*"]], [1.75, 0.85, 0.75, 1.1], size=11.5, row_h=0.5, hl=(2,))
text(s, 8.4, 3.65, 4.45, 0.5, "dB unless noted. *Too few points for a reliable period.", size=11, color=MUTED)
card(s, 8.4, 4.25, 4.45, 2.65, "Reading", ["Below 25 GHz: simulation and lab agree within a few dB.",
     "Above 27 GHz: the worst lab direction is 5–8 dB higher, the other ≈ 2 dB lower.",
     "Both show a regular ripple; the lab one is about 25 % shorter."], size=14)
text(s, 0.5, 5.85, 7.7, 1.0, "The simulation drives one direction only; the lab directions differ by 10 dB, more than the simulation–lab gap.", size=13, color=MUTED)

# ---------------------------------------------------------------- 17 where from / future
s = new(); title(s, "Where the remaining differences may come from", "What is not in the model yet, and how to test it")
rows = [["Possible cause", "Why it matters", "Proposed study"],
        ["Real driver", "Modelled as an ideal matched port; the real chip and package add length and coupling", "Driver S-parameters or package model in the run"],
        ["Assembly as built", "Wire loops, glue and carrier position change the shared return path", "Sensitivity runs: wire height, glue / no glue"],
        ["Chip surroundings", "Four lines per chip and a real chip edge; the model has two lines and open sides", "Four-line run with the real chip edge"],
        ["Lab method", "Victim driver state and the squelch settings change B's termination", "Ask for the measurement procedure"],
        ["Read-out", "Values digitized from a picture; low-frequency simulation less converged", "Numeric lab data; longer run below 15 GHz"]]
table(s, 0.5, 1.6, 12.35, rows, [2.1, 5.6, 4.65], size=12.5, row_h=0.72)
text(s, 0.5, 6.05, 12.35, 0.8, "Longer ripple path in the lab (5 GHz vs 6.4 GHz) points to the driver side or the return path: a good first target.", size=13, color=NAVY, bold=True)

# ---------------------------------------------------------------- 18 conclusions
s = new(); title(s, "Conclusions", "")
card(s, 0.5, 1.4, 6.05, 5.5, "Simulation", ["Cordoba fixed the set-up: finer mesh, wide chip, electric bottom, −40 dB, 1 GHz monitors, one active port.",
     "Each added piece raises the EO crosstalk; the driver side most, especially below 10 GHz.",
     "Crosstalk injected at the input travels with the light and counts in full: EO ≈ FEXT in the module, not FEXT − 6 dB.",
     "The module ripple matches a round trip line + slow substrate wave (6.4 GHz)."], size=16)
card(s, 6.78, 1.4, 6.07, 5.5, "Comparison with the lab", ["The full-module simulation (−27 dB median) falls inside the lab spread (−19 to −30 dB).",
     "It reproduces the level below 25 GHz and the regular ripple; it underestimates the worst direction by up to 8 dB.",
     "Next: real driver data, numeric lab data, sensitivity runs on wires, glue and chip edge."], hc=RED, size=16)

out = os.path.join(HERE, "..", "Istanbul_EO_crosstalk.pptx"); prs.save(out); print("saved", os.path.abspath(out))
