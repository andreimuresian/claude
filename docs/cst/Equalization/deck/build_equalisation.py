"""Equalisation study: slide deck in the company template (python-pptx). Helpers copied from
docs/cst/xtalk/deck/build_istanbul.py. Figures: eq_figs.py -> img/. Output: ../Equalisation.pptx (built incrementally)."""
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
HERE = os.path.dirname(os.path.abspath(__file__)); IMG = os.path.join(HERE, "img")
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
text(s, 0.5, 2.15, 12.33, 1.4, ["Travelling-wave equaliser:", "line and bend models from CST"], size=34, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.5, 3.75, 12.33, 0.8, "CST time-domain simulations, 0–130 GHz · straight line, line + bend, full equaliser", size=18, color=MUTED, align=PP_ALIGN.CENTER)

# 2 ---------------------------------------------------------------- touchstone extraction
def eqrow(s, tag, label, name, y, h, x=0.5, xe=1.0):
    text(s, x, y, 12.3, 0.35, f"**{tag}** {label}", size=13)
    eqimg(s, name, xe, y + 0.36, h)

s = new(); title(s, "Touchstone extraction of α, n_{m} and Z_{c}", "The structure between the two ports is treated as one uniform line of length L")
eqrow(s, "1.", "Uniform line: forward and backward wave (every reflection is in V^{−})", "eq_waves", 1.5, 0.42)
eqrow(s, "2.", "Writing V^{±} from the values at z = L gives the line transfer (ABCD) matrix", "eq_abcd_line", 2.38, 0.38)
eqrow(s, "3.", "Exact conversion of the 50 Ω S-parameters into A, B, C (valid for any mismatch)", "eq_s2a", 3.22, 0.42)
eqrow(s, "4.", "Matching 2 and 3", "eq_ts_zc", 4.1, 0.34, xe=1.0); eqimg(s, "eq_ts_g", 3.0, 4.46, 0.3)
eqrow(s, "5.", "Attenuation and microwave index", "eq_ts_an", 4.95, 0.46)
card(s, 0.5, 5.95, 12.35, 1.0, "Limit", ["Port transitions are folded into γ and Z_{c}. At βL = mπ, sinh γL ≈ 0: B and C both vanish and Z_{c} = √(B/C) is set by the ports."], hc=RED, size=12.5)

# 3 ---------------------------------------------------------------- field extraction
s = new(); title(s, "Field extraction of α, n_{m} and Z_{c}", "Gap voltage along the line, fitted with a forward and a backward wave")
eqrow(s, "1.", "Gap voltage from E_{y} at the centre of both gaps (x = 1 µm), 5 µm steps", "eq_f_v", 1.5, 0.42)
eqrow(s, "2.", "Least squares on γ; V^{+}, V^{−} solved linearly for each trial γ; 0.18 mm excluded at each end", "eq_f_fit", 2.42, 0.36)
eqrow(s, "3.", "Attenuation and microwave index", "eq_f_an", 3.28, 0.36)
eqrow(s, "4.", "Impedance from the reflection at port 2 (z = L, 50 Ω load)", "eq_f_zc", 4.14, 0.44)
card(s, 0.5, 5.15, 6.05, 1.8, "Strength", ["γ is fitted away from the ends: ports only set V^{+} and V^{−}. Reflections are kept as V^{−} (|Γ_{L}| ≈ 0.08). Fit residual ≤ 2.3 %."], size=12.5)
card(s, 6.8, 5.15, 6.05, 1.8, "Limit", ["Z_{c} needs the load at z = L: the port-2 transition enters Z_{c}. Below ≈ 4 GHz the line is < 0.05 λ long and the two waves are hard to separate."], hc=RED, size=12.5)

# 4 ---------------------------------------------------------------- line: touchstone vs fields
s = new(); title(s, "Line parameters: touchstone and fields agree", "Straight line 3.24 mm (L+S run), 50 Ω ports, 0–130 GHz")
fig(s, "line_ts_vs_fields.png", 0.5, 1.55, 6.55, 4.6, "Attenuation, microwave index and impedance from touchstone and fields")
table(s, 7.3, 1.55, 5.55, [["Quantity", "Fields − touchstone", "Origin of the difference"],
      ["α", "rms 0.04 dB/cm (≤ 60 GHz), 0.09 dB/cm (> 60 GHz)", "Touchstone ripple, period c / (2n_{m}L) = 20.8 GHz: set by the line ends; not reproduced by a lumped port"],
      ["n_{m}", "−0.013, constant", "Port transitions: 2.5 pH + 1.7 fF at each end reproduce +0.012"],
      ["Re Z_{c}", "mean < 0.1 Ω", "Touchstone spikes at βL = mπ"],
      ["Im Z_{c}", "within 2 Ω", "Port-2 transition in the field value"]], [0.9, 1.9, 2.75], size=11, row_h=0.78)
card(s, 7.3, 5.55, 5.55, 1.4, "Use", ["γ from the fields; Z_{c} from the touchstone away from βL = mπ. The mismatch ripple of S_{21} and EO is not lost: the cascade rebuilds it from Z_{c} and the port impedances."], size=12)

# 5 ---------------------------------------------------------------- extrapolation
s = new(); title(s, "Extrapolation from 1–60 GHz field data holds up to 130 GHz", "Physical fits of the previous run (fields, 1–60 GHz) compared with the new run (fields, 62–130 GHz)")
eqimg(s, "eq_fits", 0.6, 1.55, 0.42)
text(s, 0.6, 2.02, 12.2, 0.4, "√f: skin-effect conductor loss · f: dielectric loss · n_{m}: bounded dispersion, corner f_{c} inside the fitted band · Z_{c}: internal inductance falling with the skin depth", size=11.5, color=MUTED)
fig(s, "line_extrapolation.png", 0.5, 2.5, 12.35, 3.1, "Fits of the 1-60 GHz field data extrapolated against the 62-130 GHz field data")
def kpi(s, x, y, w, h, big, small):
    rect(s, x, y, w, h)
    text(s, x, y + 0.08, w, 0.6, big, size=28, bold=True, color=NAVY, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.15, y + 0.72, w - 0.3, h - 0.75, small, size=12, align=PP_ALIGN.CENTER)
kpi(s, 0.5, 5.7, 3.0, 1.25, "≤ 1.4 %", "α (0.07 dB/cm)")
kpi(s, 3.62, 5.7, 3.0, 1.25, "≤ 0.003", "n_{m} (0.14 %)")
kpi(s, 6.74, 5.7, 3.0, 1.25, "≤ 1.3 Ω", "Re Z_{c} (3 %)")
kpi(s, 9.86, 5.7, 3.0, 1.25, "≤ 1.6 Ω", "Im Z_{c}: the field value rises with f (port-2 transition), the fit cannot")

# 6 ---------------------------------------------------------------- bend block: two routes
s = new(); title(s, "Bend block: touchstone and fields give the same two-port", "L+B+S run; block = rise, raised straight, U-bend, raised straight, descent")
fig(s, "bend_routes.png", 0.5, 1.55, 12.35, 3.75, "Bend block S21, phase delay and S11 from touchstone and fields")
text(s, 0.5, 5.4, 6.0, 0.35, "**Touchstone:** line and port blocks removed from the L+B+S matrix", size=12.5); eqimg(s, "eq_deemb", 0.7, 5.78, 0.36)
text(s, 0.5, 6.25, 6.0, 0.7, "Line: γ from the fields, Z_{c} from the touchstone (βL = mπ bands excluded); ports: 2.9 pH + 1.6 fF (fitted on L+S).", size=11, color=MUTED)
text(s, 6.75, 5.4, 6.1, 0.35, "**Fields:** waves of lines 1 and 2 at the two planes, symmetric block", size=12.5); eqimg(s, "eq_fieldS", 6.95, 5.78, 0.3)
text(s, 6.75, 6.25, 6.1, 0.7, "Agreement: |S_{21}| within 0.06 dB, delay within 0.05 ps above 60 GHz, |S_{11}| within 0.03. Delay 5.0 ps, i.e. index 1.73 over 0.87 mm.", size=11, color=MUTED)

# 7 ---------------------------------------------------------------- parasitic mode
s = new(); title(s, "The dips are resonances of a ground-to-ground mode", "Born in the U-bend, reflected at both ports: a standing wave over the 4.11 mm path")
fig(s, "bend_parasitic.png", 0.5, 1.55, 8.3, 3.6, "Parasitic voltage on the lines and in the arc")
eqimg(s, "eq_vp", 9.0, 1.6, 0.5)
text(s, 9.0, 2.2, 3.85, 0.9, "v_{in}, v_{out}: voltage across the inner and outer gap. v_{p} = (φ_{outer} − φ_{inner})/2: potential difference between the two grounds.", size=11.5, color=MUTED)
eqimg(s, "eq_comb", 9.0, 3.2, 0.5)
text(s, 9.0, 3.8, 3.85, 1.3, "n_{p} = 2.39 from the fields (line 1), slower than the coplanar mode (2.21). Predicted 15.3, 30.5, 45.8, 61.1, 76.3, 91.6 GHz; dips at 15.5, 30.6, 46.3, 62.1, 78.1, 93.2 GHz.", size=11.5)
card(s, 0.5, 5.3, 6.05, 1.6, "Birth", ["In the arc the inner gap is 124 µm shorter than the outer one: the two gap voltages fall out of phase. At 78 GHz |v_{p}/v_{c}| grows from 0.06 at the entry to 0.44 at the exit."], size=12)
card(s, 6.8, 5.3, 6.05, 1.6, "Resonance", ["The ports match only the coplanar mode: the parasitic wave is trapped between them. At each round trip of 2π the trapped wave builds up and draws power from the coplanar mode."], size=12)
note(s, "Arc stations only at 0, 90 and 180 deg: at oblique angles the exported field of the staircase mesh gives path-dependent gap voltages, even at 1 GHz. Comb drift at high order: the 0.87 mm raised part has a lower parasitic index than the lines (about 2.05 if the dip spacing, 15.6 GHz, is attributed to the whole path).")

# 8 ---------------------------------------------------------------- bend loss
s = new(); title(s, "Bend loss: line-like up to 50 GHz, growing faster above", "Smooth part of the bend block compared with the same length of straight buried line")
fig(s, "bend_loss.png", 0.5, 1.55, 7.2, 4.0, "Bend block S21 compared with an equal length of line")
table(s, 7.95, 1.55, 4.9, [["f (GHz)", "Bend, smooth (dB)", "Line, 0.87 mm (dB)"],
      ["20", "−0.14", "−0.15"], ["60", "−0.31", "−0.28"], ["100", "−0.54", "−0.37"], ["120", "−0.72", "−0.41"]], [1.1, 1.9, 1.9], size=12, row_h=0.42)
card(s, 7.95, 3.85, 4.9, 1.7, "Dips", ["Extra loss at the resonances: 0.07 dB at 15.5 GHz, 0.34 dB at 62 GHz, 0.50 dB at 109 GHz. Power converted into the trapped parasitic wave."], size=12)
card(s, 0.5, 5.75, 12.35, 1.15, "Location within the bend: not resolved", ["E-field data give voltages only; a voltage change across the rise or in the arc can be impedance as well as loss. Power flow ½Re(V I*) needs H: H monitors at the line end, after the rise and at the arc stations in the next run."], hc=RED, size=12)

out = os.path.join(HERE, "..", "Equalisation.pptx"); prs.save(out); print("saved", os.path.abspath(out))
