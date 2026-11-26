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

# 1b --------------------------------------------------------------- simulated structures
s = new(); title(s, "Simulated structures", "CST time domain, 0–130 GHz, 50 Ω ports; E-field exported along the centre of both gaps (every 5 µm)")
for k, (img, lab, txt) in enumerate((("sch_LS.png", "L+S", "Straight line 3.24 mm: line parameters α, n_{m}, Z_{c}"),
                                     ("sch_LBS.png", "L+B+S", "Line 2.16 mm + bend block + line 1.08 mm: bend block"),
                                     ("sch_full.png", "Full equaliser", "2.70 (+) + bend + 1.44 (+) + bend + 1.44 (−) mm: validation"))):
    y = (1.5, 2.85, 4.75)[k]; h = (1.15, 1.75, 2.15)[k]
    text(s, 0.5, y + 0.05, 2.3, 0.4, lab, size=15, bold=True, color=NAVY)
    text(s, 0.5, y + 0.45, 2.3, h - 0.45, txt, size=11.5, color=MUTED)
    W, H = Image.open(os.path.join(IMG, img)).size; hh = min(h, 9.9 * H / W); s.shapes.add_picture(os.path.join(IMG, img), Inches(2.95), Inches(y), Inches(hh * W / H), Inches(hh))

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

# 3 ---------------------------------------------------------------- field extraction (1/2)
EK = 0.0028   # inches per pixel of the equation images
def eqk(s, name, x, y):
    H_ = Image.open(os.path.join(IMG, name + ".png")).size[1]; eqimg(s, name, x, y, H_ * EK); return y + H_ * EK
s = new(); title(s, "Field extraction (1/2): gap voltage and two-wave fit", "A uniform single-mode line carries one forward and one backward wave: their standing wave fixes γ")
fig(s, "field_fit_30GHz.png", 0.5, 1.45, 6.2, 5.07, "Gap voltage along the straight line at 30 GHz: samples, cell average and two-wave fit")
X = 6.95
text(s, X, 1.42, 5.9, 0.5, "**1. Gap voltage.** E_{y} (field across the gap) read at the centre of the upper and lower gap, electrode mid-height (x = 1 µm), every 5 µm:", size=11.5)
y = eqk(s, "eq4_v", X + 0.2, 1.95)
text(s, X, y + 0.04, 5.9, 0.3, "**2. Model.** One forward and one backward wave:", size=11.5)
y = eqk(s, "eq4_model", X + 0.2, y + 0.36)
text(s, X, y + 0.06, 5.9, 0.55, "**3. Fit.** 649 complex equations, three unknowns: for each trial γ, V^{+} and V^{−} by linear least squares; γ adjusted until the misfit is smallest:", size=11.5)
y = eqk(s, "eq4_fit", X + 0.2, y + 0.62)
text(s, X, y + 0.04, 5.9, 0.3, "One minimum for n_{m} = 1.5–3.5 (checked 10–130 GHz); start from the touchstone γ.", size=10.5, color=MUTED)
text(s, X, y + 0.42, 5.9, 0.95, "**4. Cell average.** The field at the sample point halves over 15 µm of each 0.18 mm cell (tee aperture, zoom). γ is the change from cell to cell, so V is averaged over one cell before the fit: misfit 14 % → 0.5 %.", size=11.5)
note(s, "Files L1_gap+.txt (y = -0.082925 mm) and L1_gap-.txt (y = -0.122075 mm), x = 0.001 mm, z step 5 um, 649 samples; columns EyRe, EyIm. GAP = 4.45 um. The two gap fields point in opposite directions for the line mode, hence the difference. Outer fit: scipy least_squares on (alpha, beta); inner: 649 x 2 linear least squares. Fit range 0.18-3.06 mm (end cut tested: <= 0.0008 in n_m above 4 GHz). 30 GHz: n_m 2.226, alpha 2.22 dB/cm, |V-/V+| 0.07.")

# 3b --------------------------------------------------------------- field extraction (2/2)
s = new(); title(s, "Field extraction (2/2): results, assumptions, limits", "Same fit; α and n_{m} from γ, Z_{c} from the reflection at port 2")
text(s, 0.5, 1.45, 6.0, 0.3, "**Attenuation and microwave index**", size=12)
eqk(s, "eq4_an", 0.7, 1.8)
text(s, 6.8, 1.45, 6.0, 0.3, "**Impedance: port 2 taken as a 50 Ω load at z = L**", size=12)
eqk(s, "eq4_zc", 7.0, 1.8)
table(s, 0.5, 2.55, 12.35, [["Assumption", "Strength", "Evidence"],
      ["One propagating mode", "Strong", "Two waves leave 0.5 % misfit after the cell average"],
      ["Uniform line (same γ everywhere)", "Strong", "Cell 0.18 mm ≤ λ/5.6 at 130 GHz; cells reflect coherently only near 360 GHz"],
      ["Point field ∝ gap voltage", "Weak, no effect here", "The scale factor cancels in γ and in Γ_{L}"],
      ["Port 2 is an ideal 50 Ω load", "Weak, Z_{c} only", "The port transition enters Z_{c}: Im Z_{c} differs from the touchstone by up to 2 Ω"],
      ["Line long enough for a standing wave", "Weak below 4 GHz", "Line < 0.05 λ: the processing choices move n_{m} by up to 0.07 at 1 GHz"]], [3.4, 2.3, 6.65], size=11, row_h=0.36)
card(s, 0.5, 4.9, 6.05, 2.05, "Processing checks (≥ 4 GHz)", ["Without the cell average: Δn_{m} ≤ 0.002, Δα ≤ 0.006 dB/cm, ΔZ_{c} ≤ 0.2 Ω. Without the 0.18 mm end cut: Δn_{m} ≤ 0.001, Δα ≤ 0.005 dB/cm. Below 4 GHz the field route is not reliable."], size=11.5)
card(s, 6.8, 4.9, 6.05, 2.05, "Z_{c} from the H field (10 + 5 + 5 run)", ["Current from the H loop: Re Z_{c} = 39–40 Ω on all three lines, 8 % below the touchstone: the voltage is still point field × gap. Power flow (Z_{c} = 2P/|I|^{2}) needs E and H on one plane of a straight line: not done yet."], hc=RED, size=11.5)

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

# 6 ---------------------------------------------------------------- bend block: extraction
s = new(); title(s, "Bend block: two independent extractions", "Block between plane 1 and plane 2 (z = 2.16 mm): vertical step, 50 µm gap taper, raised straight, U-bend, and back")
W, H = Image.open(os.path.join(IMG, "sch_LBS_waves.png")).size; s.shapes.add_picture(os.path.join(IMG, "sch_LBS_waves.png"), Inches(1.9), Inches(1.4), Inches(1.85 * W / H), Inches(1.85))
text(s, 0.5, 3.3, 12.3, 0.35, "**Touchstone route.** The L+B+S matrix is a chain of port 1, line 1, block, line 2, port 2; lines and ports are known from L+S:", size=12.5)
eqimg(s, "eq_chain", 0.8, 3.66, 0.34)
eqimg(s, "eq_a2s", 0.8, 4.08, 0.44); text(s, 6.9, 4.12, 5.95, 0.4, "S-parameters of T_{bend}, referenced to the line Z_{c} on both sides", size=11, color=MUTED)
text(s, 0.5, 4.62, 12.3, 0.35, "**Field route.** Forward/backward wave fit on line 1 (coordinate z) and line 2 (coordinate s), γ of the line; a: towards the block, b: away from it:", size=12.5)
eqimg(s, "eq_w1", 0.8, 4.98, 0.32); eqimg(s, "eq_w2", 0.8, 5.38, 0.3); eqimg(s, "eq_w3", 0.8, 5.76, 0.3)
text(s, 0.5, 6.2, 12.3, 0.7, "One excitation (port 1) gives 2 equations for 4 unknowns. Reciprocity (S_{12} = S_{21}) and mirror symmetry of the block about the bend axis (S_{22} = S_{11}) close the system. Neither the ports nor the line Z_{c} enter.", size=11.5, color=MUTED)

# 7 ---------------------------------------------------------------- bend block: results
s = new(); title(s, "Bend block: the two routes agree", "|S_{21}|, delay and |S_{11}| of the block, referenced to the line impedance")
fig(s, "bend_routes.png", 0.5, 1.5, 12.35, 3.65, "Bend block S21, delay and S11 from touchstone and fields")
eqimg(s, "eq_delay", 0.6, 5.3, 0.46)
card(s, 0.5, 5.9, 4.0, 1.05, "Agreement", ["|S_{21}| within 0.06 dB, |S_{11}| within 0.03, delay within 0.03 ps."], size=11.5)
card(s, 4.67, 5.9, 4.0, 1.05, "Delay of the coplanar wave", ["5.0 ps from plane 1 to plane 2 (same both ways): index 1.72 over 0.87 mm."], size=11.5)
card(s, 8.84, 5.9, 4.01, 1.05, "Below 10 GHz", ["The block is a small difference: at 2 GHz L+B+S 22°, lines 18°, block 3.6°. 1° of error = 1.4 ps."], size=11.5)

# 8 ---------------------------------------------------------------- parasitic mode
s = new(); title(s, "The dips are resonances of a ground-to-ground wave", "Generated in the U-bend, trapped between the two ports")
eqimg(s, "eq_vp", 0.6, 1.5, 0.5)
text(s, 4.1, 1.45, 8.75, 0.75, "v_{in}, v_{out}: voltages across the inner and outer gap (signal to ground). v_{c}: quasi-TEM coplanar mode, opposite fields in the two gaps, push-pull modulation. v_{p} = (φ_{outer} − φ_{inner})/2: ground-to-ground mode, same field direction in both gaps, no modulation.", size=11.5)
fig(s, "bend_parasitic.png", 0.5, 2.3, 8.3, 2.85, "Parasitic voltage on the lines versus frequency, and along the path")
text(s, 9.0, 2.35, 3.85, 0.35, "**Resonance comb**", size=12.5); eqimg(s, "eq_comb", 9.0, 2.75, 0.45)
text(s, 9.0, 3.3, 3.85, 1.85, "n_{p} = 2.39: effective index of the ground-to-ground wave (forward/backward fit of v_{p} on line 1); L_{path} = 4.11 mm: 15.3, 30.5, 45.8, 61.1, 76.4, 91.6 GHz. Dips: 15.5, 30.6, 46.3, 62.1, 78.1, 93.2 GHz. A coplanar round trip would give a 17.2 GHz spacing.", size=11.5)
card(s, 0.5, 5.3, 4.0, 1.65, "Ports", ["The PEC bridge of each port joins the two grounds: v_{p} = 0 there, a short for this mode. Γ_{p} ≈ −1: |Γ_{p}| = 1.0 ± 0.1, phase 160–170°. Coplanar wave: |Γ| = 0.08."], size=11.5)
card(s, 4.67, 5.3, 4.0, 1.65, "Birth", ["Inner gap 124 µm shorter than the outer one: the two gap voltages drift out of phase. At 78 GHz v_{p}/v_{c}: 0.06 → 0.45 across the U-bend."], size=11.5)
card(s, 8.84, 5.3, 4.01, 1.65, "Line 2 stronger", ["Conversion is forward: v_{p} leaves the bend towards port 2; line 1 receives it only after reflection at port 2."], size=11.5)
note(s, "Arc voltages: the staircase mesh scales the exported field of oblique gap points by a geometric factor (up to x2). Each point is calibrated by its own 1 GHz value; point sampling and line integral then agree. Line voltages averaged over one 0.18 mm cell of the periodic loading. Physical vs artefact: the line-extraction ripples were in per-unit-length quantities (alpha, Zc) and sat at the extraction condition beta L = m pi; these dips are in the transmitted power of the block, appear in both independent routes, and coincide with a measured second mode.")

# 9 ---------------------------------------------------------------- bend loss
s = new(); title(s, "Bend loss sits in the raised path, not in the transitions", "Left: the block against straight line. Right: loss per section (field route)")
fig(s, "bend_loss.png", 0.5, 1.5, 12.35, 3.85, "Smooth part of the bend loss and split along the path")
card(s, 0.5, 5.5, 4.0, 1.45, "Cubic fit: an average", ["Between the dips the data sit up to 0.09 dB above it: each resonance is a dip plus an overshoot. No unique resonance-free reference from this run."], hc=RED, size=11)
card(s, 4.67, 5.5, 4.0, 1.45, "Where the loss is (≤ 60 GHz)", ["The two transitions (step + 50 µm gap taper) together: < 0.07 dB. Raised straights + U-bend: the rest; 4.7 dB/cm at 60 GHz, against 3.3 dB/cm for the straight buried line."], size=11)
card(s, 8.84, 5.5, 4.01, 1.45, "Forward wave", ["Amplitude of the wave travelling towards port 2, at the section ends; reflected waves excluded. Whole block = |S_{21}| when nothing returns from port 2."], size=11)
note(s, "Forward wave from forward/backward fits on line 1 and line 2 (gamma of the line) and on the raised path s = 2.215-2.975 mm (TAPER_L straights + U-bend; gamma free: n = 1.72). Transition = vertical step at z = 2.16 mm + 50 um gap taper 4.45 -> 4.8 um. Voltage calibration: buried lines as cell averages, raised gaps scaled once so that the 1 GHz voltage is continuous across the transition. Sum of the sections = field-route |S21| within 0.05 dB.")

# 11 --------------------------------------------------------------- full equaliser: building blocks
s = new(); title(s, "Full equaliser: folds and bends match the building blocks", "Fields of the full run (2.70 + 1.44 + 1.44 mm) against L+S (lines) and L+B+S (bend)")
fig(s, "full_blocks.png", 0.5, 1.5, 12.35, 3.65, "Line parameters per fold and the two bends of the full run")
card(s, 0.5, 5.3, 4.0, 1.65, "Lines", ["All three folds: α within 0.06 dB/cm and n_{m} within 0.008 of L+S (0.019 on L2 below 10 GHz). The straight line is the same everywhere."], size=11.5)
card(s, 4.67, 5.3, 4.0, 1.65, "Bends", ["Delays 4.97 ps (bend 1) and 5.06 ps (bend 2), against 5.00 ps in L+B+S."], size=11.5)
card(s, 8.84, 5.3, 4.01, 1.65, "Two bends together", ["= 2 × smoothed L+B+S bend within 0.03 dB rms up to 40 GHz. Above: 0.08 dB (40–80 GHz) and 0.2 dB (80–130 GHz) less loss: part of the power converted at bend 1 returns at bend 2."], size=11.5)

# 12 --------------------------------------------------------------- full equaliser: parasitic cancellation
s = new(); title(s, "Parasitic cancellation: strong up to 40 GHz, partial above", "Bend 1 turns left, bend 2 turns right: their ground-to-ground waves have opposite sign")
fig(s, "full_parasitic.png", 0.5, 1.5, 12.35, 3.65, "Parasitic voltage per fold, along the path, and the ripple of the full S21")
card(s, 0.5, 5.3, 4.0, 1.65, "After both bends (L3)", ["16–31 GHz: −40 to −47 dB, against −13 to −30 dB after one bend. Above 80 GHz: −11 to −16 dB, as after one bend: no cancellation left."], size=11.5)
card(s, 4.67, 5.3, 4.0, 1.65, "Ripple of the full S_{21}", ["Below 60 GHz: coplanar mismatch ripple (on the |S_{11}| peaks, 9.8 GHz). Above 60 GHz: dips on the v_{p} peaks, 8.9 GHz apart: parasitic wave trapped over 7.32 mm; 0.14–0.49 dB."], size=11.5)
card(s, 8.84, 5.3, 4.01, 1.65, "Why it degrades", ["The two modes travel at different speeds (n_{p} 2.39, n_{m} 2.21): the wave of bend 1 reaches bend 2 out of phase, more so at high f and on longer lines."], hc=RED, size=11.5)
note(s, "Voltages: left/right gaps with respect to the direction of travel, so that v_p keeps its sign through both bends. Arcs calibrated at 1 GHz as for L+B+S. Comb check: coplanar round trip over the path, n about 2.11 (lines 2.23, raised 1.72): 9.8 GHz; parasitic, effective n about 2.29: 8.9 GHz.")

# 13 --------------------------------------------------------------- cascade validation
s = new(); title(s, "Two-port cascade: within budget up to 60 GHz, not above", "Line (L+S) + bend (L+B+S) + ports, against the full run; three versions of the bend two-port")
fig(s, "cascade_130.png", 0.5, 1.5, 12.35, 3.7, "Cascade against the full run: EO response, S21 and EO error")
table(s, 0.5, 5.35, 7.6, [["Bend two-port", "EO error 1–60 GHz", "EO error 62–130 GHz", "|S_{21}| error 62–130 GHz"],
      ["Cubic over 1–130 GHz", "0.08 dB rms (0.14 max)", "0.10 dB rms (0.22 max)", "0.21 dB rms"],
      ["Local bridging of the dips", "0.03 dB rms (0.08 max)", "0.18 dB rms (0.34 max)", "0.35 dB rms"],
      ["Raw (dips kept)", "0.04 dB rms (0.10 max)", "0.19 dB rms (0.33 max)", "0.44 dB rms"]], [2.2, 1.8, 1.8, 1.8], size=10.5, row_h=0.38)
card(s, 8.35, 5.35, 4.5, 1.6, "Meaning", ["Up to 60 GHz the bend is a two-port. Above, the cascade loses too much and its EO is too flat: the returned parasitic power is missing. Next: two-mode bend."], hc=RED, size=11)
note(s, "Light delay in each bend = slope delay of the bend model (5.03 ps). V(z) agreement (one complex scale per frequency): median 0.7-0.9 % up to 60 GHz, 3-7 % above. Error budget of the earlier 0-60 GHz validation: EO within about 0.05 dB rms.")

# 14 --------------------------------------------------------------- two-mode bend
s = new(); title(s, "Two-mode bend from the L+B+S fields", "Coplanar and parasitic waves fitted on both lines; ports included through Γ_{p}")
eqimg(s, "eq_tm1", 0.6, 1.5, 0.33); eqimg(s, "eq_tm2", 0.6, 1.95, 0.3)
text(s, 7.6, 1.95, 5.25, 0.55, "a: waves towards the bend, b: away from it (planes as for the two-port). κ: conversion; ρκ: reconversion (reciprocity between modes of different impedance).", size=10.5, color=MUTED)
fig(s, "two_mode_coeffs.png", 0.5, 2.5, 12.35, 3.0, "Two-mode bend coefficients")
table(s, 0.5, 5.65, 12.35, [["t_{c}", "κ", "t_{p}", "ρ = Z_{c}/Z_{p}", "Ports (Γ_{p})", "Parasitic line"],
      ["smooth, 5.00 ps; no dips", "j · 0.002 f · e^{−jω 5.3 ps}", "5.2 ps; loss 1.3 × t_{c}", "1.56 (Z_{p} ≈ 27 Ω)", "−0.98 e^{−jω 0.56 ps}", "n_{p} 2.38, α_{p} 1.3 α_{c}"]],
      [1.9, 2.3, 2.0, 2.0, 2.1, 2.05], size=10.5, row_h=0.62)
note(s, "Assumptions: reciprocity, mirror symmetry, backward conversion and parasitic reflection at the bend neglected. kap and t_p come from the parasitic equations alone; rho is the only free value and is chosen where t_c is smoothest (the trapped resonance removed from the coplanar transmission). The +90 deg of kap at 0 Hz is the path-difference mechanism (inner gap shorter). alpha_p is weakly determined (k from 0.7 to 2 changes the prediction by < 0.01 dB rms). Gamma_p delay 0.56 ps: effective short about 35 um behind the port plane.")

# 15 --------------------------------------------------------------- two-mode cascade
s = new(); title(s, "The two-mode bend predicts the full equaliser", "No information from the full run; lines from L+S, bends from L+B+S")
fig(s, "two_mode_cascade.png", 0.5, 1.5, 12.35, 3.65, "Full run against the two-mode and two-port cascades")
table(s, 0.5, 5.3, 8.0, [["Bend model", "EO 1–60 GHz", "EO 62–130 GHz", "|S_{21}| 62–130 GHz"],
      ["Two-mode (smooth)", "0.02 dB rms", "0.07 dB rms (0.20 max)", "0.11 dB rms"],
      ["Two-mode, no reconversion (ρ = 0)", "0.04 dB rms", "0.18 dB rms", "0.31 dB rms"],
      ["Two-port, cubic", "0.08 dB rms", "0.10 dB rms (0.22 max)", "0.21 dB rms"],
      ["Two-port, local bridging", "0.03 dB rms", "0.18 dB rms (0.34 max)", "0.35 dB rms"]], [2.6, 1.6, 2.1, 1.7], size=10.5, row_h=0.33)
card(s, 8.75, 5.3, 4.1, 1.65, "Result", ["Best model at all frequencies. Parasitic level on L2 within 1 dB up to 60 GHz, 3 dB above. The returned power (ρκ) is essential above 60 GHz."], size=11)

# 16 --------------------------------------------------------------- longer equalisers
s = new(); title(s, "Longer equalisers: the parasitic mode costs at most 0.3 dB", "Two-mode prediction (lines from L+S, bends from L+B+S), against ideal cancellation and the two-port bend")
fig(s, "long_lines_130.png", 0.5, 1.5, 12.35, 3.7, "Predicted 10 + 5 + 5 mm equaliser and effect of the parasitic mode for several lengths")
table(s, 0.5, 5.35, 7.9, [["L1 + L2 + L3 (mm)", "EO at 60 / 100 / 130 GHz", "Parasitic effect (max)", "v_{p}/v_{c} on L3, 60 GHz"],
      ["2.70 + 1.44 + 1.44 (simulated)", "−0.83 / −0.86 / −0.90 dB", "0.20 dB", "−29 dB"],
      ["5.40 + 2.88 + 2.88", "−1.00 / −1.03 / −1.03 dB", "0.16 dB", "−19 dB"],
      ["8 + 4 + 4", "−1.15 / −1.28 / −1.60 dB", "0.11 dB", "−20 dB"],
      ["10 + 5 + 5 (run in progress)", "−1.15 / −1.57 / −2.18 dB", "0.08 dB", "−18 dB"]], [2.5, 2.2, 1.6, 1.6], size=10.5, row_h=0.32)
card(s, 8.6, 5.35, 4.25, 1.6, "Meaning", ["Cancellation worsens with length (v_{p} on L3 up 10 dB), but the parasitic wave is also damped: its EO cost falls. The two-port bend overestimates the loss by up to 0.2–0.36 dB."], size=11)
note(s, "Parasitic effect = EO with the two-mode bend minus EO with kap = 0 (parasitic mode never excited). L1 = 2.70 mm with L2 = L3 = 3, 5, 8 mm: max effect 0.32, 0.24, 0.14 dB (these designs over-equalise: EO rises above 0 dB). EO normalised to 1 GHz; n_g 2.27; light matched to the RF in the bends. All -3 dB EO bandwidths above 130 GHz.")

# 17 --------------------------------------------------------------- optimiser L1 = 10 mm
s = new(); title(s, "L1 = 10 mm: best sections are 8–9 mm, nearly equal", "Two-mode model, L2 (+) and L3 (−) swept 0.5–10 mm; EO relative to the 10 mm line alone at 1 GHz")
fig(s, "optimiser_L1_10mm.png", 0.5, 1.5, 12.35, 4.0, "Optimiser map and EO curves of selected designs")
table(s, 0.5, 5.65, 8.1, [["Design (mm)", "EO at 1 GHz", "Worst 10–130 GHz", "Peaking"],
      ["10 alone", "0 dB", "−3.9 dB (f_{−3 dB} 90 GHz)", "–"],
      ["10 + 5 + 5", "−0.2 dB", "−2.4 dB", "0 dB"],
      ["10 + 8.5 + 8", "0.0 dB", "−1.4 dB", "+0.2 dB"],
      ["10 + 9 + 9", "−0.5 dB", "−1.2 dB", "+0.8 dB"]], [1.7, 1.3, 2.4, 1.0], size=10.5, row_h=0.27)
card(s, 8.85, 5.65, 4.0, 1.3, "Trade-off", ["Longer L2, L3: flatter and stronger at high f, until over-equalisation (peaking) and the cost of 28 mm of electrode."], size=10.5)
note(s, "Validity: 1-130 GHz (no extrapolation of the bend); bend model validated so far on the 1.44 mm sections (10+5+5 run to test it). Not in the model: optical loss and footprint of the longer electrodes, drive power. Light assumed matched to the RF in the bends. L3 > L2 flattens the normalised response further (10+5.5+7) but costs 1.7 dB of low-frequency efficiency.")

# 18 --------------------------------------------------------------- long run validation
s = new(); title(s, "10 + 5 + 5 mm run confirms the prediction", "Run: L1 10.08, L2 = L3 5.04 mm; prediction from L+S and L+B+S only, made before the run")
fig(s, "long_run_validation.png", 0.5, 1.5, 12.35, 3.75, "Long equaliser run against the predictions")
table(s, 0.5, 5.4, 8.0, [["Prediction", "EO offset", "EO shape 5–60 GHz", "EO shape 62–130 GHz", "|S_{21}| 1–60 GHz"],
      ["Two-mode bend", "+0.06 dB", "0.01 dB rms", "0.06 dB rms (0.13 max)", "0.05 dB rms"],
      ["No conversion", "+0.09 dB", "0.01 dB rms", "0.06 dB rms (0.17 max)", "0.07 dB rms"],
      ["Two-port bend", "−0.10 dB", "0.02 dB rms", "0.07 dB rms (0.19 max)", "0.03 dB rms"]], [1.7, 1.2, 1.6, 2.0, 1.5], size=10.5, row_h=0.36)
card(s, 8.75, 5.4, 4.1, 1.55, "Result", ["EO shape within 0.01 dB rms up to 60 GHz; parasitic levels on L2, L3 within a few dB. As predicted, the parasitic mode matters little on long lines (0.03 dB between two-mode and no conversion)."], size=10.5)
note(s, "EO offset: constant difference from 5 GHz upwards, set by the 1 GHz normalisation point; 'shape' = rms after removing it. |S21| above 105 GHz: CST shows a fine ripple (+-0.4-0.7 dB) not reproduced point by point. Folds of the run vs L+S: alpha within 0.05 dB/cm, n_m within 0.003; bend delays 4.99 / 5.10 ps.")

# 19 --------------------------------------------------------------- H-field impedance
s = new(); title(s, "H fields: line impedance from the current", "10 + 5 + 5 mm run; current = loop integral of H around the signal electrode, 3 planes in one cell per line")
fig(s, "h_field_zc.png", 0.5, 1.5, 8.2, 2.75, "Line impedance from the H-field current against the touchstone")
card(s, 8.95, 1.5, 3.9, 2.75, "Result", ["All three lines: Re Z_{c} 39–40 Ω, the same within 0.5 Ω; Im Z_{c} follows the touchstone.", "Re Z_{c} 3.3 Ω (8 %) below the touchstone value."], size=11)
card(s, 0.5, 4.45, 6.05, 2.5, "Why the 8 % gap", ["Z_{c} = V/I needs a voltage. Here V is the field at the gap centre × 4.45 µm outside the apertures; inside a loaded cell V changes (×2 in the aperture) while I stays constant (0.2 % over the cell).",
     "The impedance seen by the ports is the cell-averaged one (touchstone, with port blocks): it reproduces S_{11} of all runs."], size=10.5)
card(s, 6.8, 4.45, 6.05, 2.5, "Next run", ["Export E on the same planes as H: power flow P = ½∫(E × H*)·dA through the cross-section gives Z_{c} = 2P/|I|^{2} without any voltage definition, and the loss between planes (step, taper, U-bend)."], hc=RED, size=10.5)
note(s, "Power along the path from 1/2 Re(V I*) is not reliable with these exports: buried, raised and apex voltages use different definitions (point field x nominal gap vs line integral), which differ by up to 10 %. Local V/I on the raised sections and apexes: 33-49 ohm (standing waves).")

# 20 --------------------------------------------------------------- single bend
s = new(); title(s, "Single bend: 0.3 dB at 60 GHz, raised straights dominate", "Single U-bend run with 20 µm buried stubs; loss from net power ½Re(VI*), mirror sides paired")
fig(s, "single_bend_130.png", 0.5, 1.5, 12.35, 4.0, "Loss split of the single bend and its |S21|")
table(s, 0.5, 5.65, 7.6, [["Net power loss", "10 GHz", "40 GHz", "60 GHz", "100 GHz"],
      ["Single-bend run", "−0.09 dB", "−0.23 dB", "−0.32 dB", "−0.38 dB"],
      ["L+B+S bend block", "−0.10 dB", "−0.22 dB", "−0.35 dB", "−0.53 dB"]], [2.0, 1.4, 1.4, 1.4, 1.4], size=10.5, row_h=0.36)
card(s, 8.35, 5.65, 4.5, 1.3, "Meaning", ["Same bend loss as extracted from L+B+S. The 79.3 GHz dip is the ground-to-ground mode trapped between the two ports (not present on the long lines, where it leaks away)."], size=10.5)
note(s, "Check: P(stub 2)/P(stub 1) = |S21|^2/(1-|S11|^2) within 0.02 dB. Individual plane-to-plane splits carry +-0.2-0.5 dB calibration differences between plane types (buried, raised, apex voltages); only sums over the mirror sides are shown. Local V/I: about 50 ohm at the stubs, 41-53 ohm on the raised sections (standing waves). Group delay of the single bend 5.3-5.5 ps (includes 2 x 20 um stubs), L+B+S block 5.0-5.4 ps.")

out = os.path.join(HERE, "..", "Equalisation.pptx"); prs.save(out); print("saved", os.path.abspath(out))
