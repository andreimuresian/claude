"""Crosstalk from cross-section modes: slide deck in the company template (python-pptx).
Template = the company deck docs/CST_line_extraction.pptx with its slides removed."""
import os, re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); IMG = os.path.join(HERE, "..")
NAVY = RGBColor(0x0E, 0x22, 0x68); RED = RGBColor(0xF2, 0x00, 0x13); INK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x5A, 0x60, 0x6E); CARD = RGBColor(0xF1, 0xF3, 0xF8); WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ROW = RGBColor(0xF6, 0xF7, 0xFA); BOX = RGBColor(0xD9, 0xDC, 0xE3); GREEN = RGBColor(0x2E, 0x8B, 0x57)
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

def text(s, x, y, w, h, paras, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, sa=4):
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

def pic(s, name, x, y, w, h):
    path = os.path.join(IMG, name); W, H = Image.open(path).size; sc = min(w / W, h / H); ww, hh = W * sc, H * sc
    return s.shapes.add_picture(path, Inches(x + (w - ww) / 2), Inches(y + (h - hh) / 2), Inches(ww), Inches(hh))

def fig(s, name, x, y, w, h):
    rect(s, x, y, w, h, fill=WHITE, line=BOX); pic(s, name, x + 0.05, y + 0.05, w - 0.1, h - 0.1)

def card(s, x, y, w, h, head, body, hc=NAVY, size=12):
    rect(s, x, y, w, h)
    text(s, x + 0.15, y + 0.08, w - 0.3, h - 0.12, [(head, {"bold": True, "color": hc, "size": size + 1.5})] + [(b, {"size": size}) for b in body], sa=3)

def stat(s, x, y, w, h, big, small, col=NAVY):
    rect(s, x, y, w, h)
    text(s, x, y + 0.15, w, 1.0, big, size=40, bold=True, color=col, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.2, y + 1.2, w - 0.4, h - 1.3, small, size=13, color=INK, align=PP_ALIGN.CENTER)

def table(s, x, y, w, rows, col_w, size=11, row_h=0.42, hl=()):
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
            c.fill.solid(); c.fill.fore_color.rgb = NAVY if i == 0 else (RGBColor(0xFD, 0xEC, 0xEE) if i in hl else (ROW if i % 2 else WHITE))

def arrow(s, x, y, w, h=0.4):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    a.fill.solid(); a.fill.fore_color.rgb = MUTED; a.line.fill.background(); a.shadow.inherit = False

new = lambda: prs.slides.add_slide(L_BLANK)

# 1 title
s = prs.slides.add_slide(L_TITLE)
text(s, 0, 2.3, 13.33, 1.3, "Electrical crosstalk from a single cross-section", size=38, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0, 3.65, 13.33, 0.8, "2-D port modes vs full 3-D CST · two TFLN GSG lines, pitch 200 µm · 1 mm and 5 mm", size=18, color=MUTED, align=PP_ALIGN.CENTER)

# 2 summary
s = new(); title(s, "Summary", "Two cross-section modes reproduce the crosstalk of the 3-D simulations")
stat(s, 0.5, 1.6, 3.95, 2.4, "2 of 6", "modes carry all the crosstalk of a single-line launch")
stat(s, 4.69, 1.6, 3.95, 2.4, "1–5 dB", "agreement with 3-D CST, 1 mm NEXT and FEXT")
stat(s, 8.88, 1.6, 3.95, 2.4, "minutes", "per frequency in 2-D, for any line length", col=RED)
card(s, 0.5, 4.3, 6.05, 2.6, "Main message", ["Crosstalk = slow phase drift between an **even** and an **odd** wave shared by the two lines.",
     "Their index and impedance come from one 2-D cross-section; any length follows from a formula."])
card(s, 6.78, 4.3, 6.05, 2.6, "Open point", ["5 mm NEXT above 25 GHz: model 6–10 dB below 3-D.",
     "The 3-D values sit on the 5 mm error floor (−56 dB). Test: finer port mesh."], hc=RED)

# 3 structure
s = new(); title(s, "Structure and question", "Two identical GSG lines; the grounds of the two lines are not connected")
fig(s, "waveguide_port_xs.png", 0.5, 1.55, 7.4, 5.35)
card(s, 8.15, 1.55, 4.7, 5.35, "Setup", ["Thin-film LiNbO_{3} on SiO_{2} on 525 µm Si.",
     "Each line: ground–signal–ground, signal 35 µm, gaps 4.15 µm.", "Pitch 200 µm; inner grounds 57 µm apart.",
     "**NEXT** = S_{31}: line A's signal seen at the near end of line B.", "**FEXT** = S_{41}: seen at the far end.",
     "Target length 14–15 mm: too long for direct 3-D runs."])

# 4 pitch
s = new(); title(s, "3-D baseline: pitch study at 1 mm", "Crosstalk falls fast with pitch, until it reaches the simulation's own error floor")
fig(s, "pitch_compare.png", 0.5, 1.55, 8.3, 3.25)
card(s, 9.05, 1.55, 3.8, 1.55, "200 µm", ["NEXT ≈ −60 dB, FEXT ≈ −70 dB at 30 GHz."])
card(s, 9.05, 3.25, 3.8, 1.55, "400 / 625 µm", ["below their own error floor (dotted) under ~30 GHz."])
card(s, 0.5, 5.0, 12.35, 1.9, "Error floor = |S_{21} − S_{43}|", ["Lines A and B are identical, so S_{21} = S_{43} in an exact solution: their difference is the run's numerical error.",
     "Crosstalk below it is not trustworthy. Above ~30 GHz the 400 and 625 µm curves rise together: substrate leakage is a hypothesis, not proven."], hc=RED)

# 5 cascade
s = new(); title(s, "Chaining five 1 mm blocks fails for crosstalk", "The through path is reproduced; NEXT and FEXT are not")
fig(s, "cascade_naive.png", 0.5, 1.55, 12.35, 3.45)
for i, (h, b) in enumerate([("Port phase", "removed: no change"), ("37 vs 50 Ω", "renormalised: dips remain"), ("A/B asymmetry", "symmetrised: 0.0 dB change"), ("Conclusion", "need a method that does not rely on 3-D crosstalk values")]):
    card(s, 0.5 + i * 3.1, 5.2, 2.95, 1.7, h, [b], hc=RED if i == 3 else NAVY)

# 6 idea
s = new(); title(s, "Idea: one line driven = half even + half odd", "Each wave keeps its shape on a uniform line; only their speeds and impedances differ")
fig(s, "decomposition.png", 0.5, 1.55, 7.6, 5.35)
card(s, 8.35, 1.55, 4.5, 5.35, "Physics in four numbers", ["**Even:** same voltage on A and B. **Odd:** opposite voltages.",
     "Different speeds → their sum drifts from line A to line B: **FEXT**, set by Δn.",
     "Different impedances → port reflections no longer cancel on B: **NEXT**, set by Z_{even}/Z_{odd}.",
     "Needed: n_{even}, n_{odd}, Z_{even}, Z_{odd}."])

# 7 modes
s = new(); title(s, "The 2-D port solve finds six quasi-TEM modes", "6 metal strips + metal port frame = 7 conductors → 6 modes")
fig(s, "modes_montage.png", 0.5, 1.55, 8.6, 4.0)
card(s, 9.35, 1.55, 3.5, 4.0, "Reading", ["Modes 5, 6: field in the signal gaps, identical on both lines → the even/odd pair.",
     "Modes 1–4: ground vs ground, or whole line vs frame."])
text(s, 0.5, 5.75, 12.3, 0.9, "CST time-domain port solver, port modes only, electric shielding, port 650 × 900 µm. Run at 6, 18, 30, 42, 60 GHz.", size=12, color=MUTED)

# 8 why two
s = new(); title(s, "A GSG launch excites only the even/odd pair", "Counting what the port allows")
steps = [("6", "modes available", "any voltage pattern on the 6 strips"), ("− 2", "grounds tied, symmetric feed", "removes the slot modes 3, 4"),
         ("− 2", "current returns on own grounds", "removes the line-vs-frame modes 1, 2"), ("= 2", "remaining", "A in CPW mode, B in CPW mode = even + odd")]
for i, (n, h, b) in enumerate(steps):
    x = 0.5 + i * 3.1; o = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.9), Inches(1.6), Inches(1.15), Inches(1.15))
    o.fill.solid(); o.fill.fore_color.rgb = RED if i == 3 else NAVY; o.line.fill.background(); o.shadow.inherit = False
    text(s, x + 0.9, 1.6, 1.15, 1.15, n, size=26, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x, 2.9, 2.95, 0.7, h, size=14, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    text(s, x, 3.6, 2.95, 0.8, b, size=12, color=MUTED, align=PP_ALIGN.CENTER)
card(s, 0.5, 4.4, 6.05, 2.5, "In the 3-D model", ["Lumped ports + PEC bars tie each line's grounds and drive symmetrically: both conditions hold at both ends.",
     "Approximate: the neighbour breaks each line's own mirror symmetry slightly."])
card(s, 6.78, 4.4, 6.05, 2.5, "Where modes 1–4 can appear", ["Asymmetric launches, bends without ground bridges, pads tying grounds differently.",
     "To check: the lab probes and pads."], hc=RED)

# 9 inputs
s = new(); title(s, "Model inputs from the 2-D runs", "Both even/odd differences are almost flat over 6–60 GHz")
fig(s, "inputs_vs_f.png", 0.5, 1.55, 12.35, 4.0)
card(s, 0.5, 5.75, 6.05, 1.15, "Δn", ["from the β of modes 5 and 6 (CST info box): n = βc/(2πf)."], size=11.5)
card(s, 6.78, 5.75, 6.05, 1.15, "Z_{even}/Z_{odd}", ["integrate E_{y} across each gap → line voltages; equal power → Z ∝ V^{2}."], size=11.5)

# 10 hybrid
s = new(); title(s, "Hybrid model", "Average line from 3-D, even/odd split from 2-D")
rect(s, 0.5, 1.7, 3.7, 1.3, fill=NAVY); text(s, 0.6, 1.75, 3.5, 1.2, ["3-D single line (coworker)", "speed, loss, Z vs f", "includes gold losses"], size=13, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, sa=1)
rect(s, 0.5, 3.3, 3.7, 1.3, fill=NAVY); text(s, 0.6, 3.35, 3.5, 1.2, ["2-D port modes (this work)", "Δn(f), Z_{even}/Z_{odd}"], size=13, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, sa=1)
arrow(s, 4.35, 2.95, 0.9); rect(s, 5.4, 2.5, 3.0, 1.3, fill=MUTED)
text(s, 5.5, 2.55, 2.8, 1.2, ["γ_{even}, γ_{odd}", "Z_{even}, Z_{odd}"], size=13, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, sa=1)
arrow(s, 8.55, 2.95, 0.9); rect(s, 9.6, 2.5, 3.25, 1.3, fill=RED)
text(s, 9.7, 2.55, 3.05, 1.2, ["NEXT = ½(Γ_{e} − Γ_{o})", "FEXT = ½(T_{e} − T_{o})", "50 Ω ports, any length"], size=13, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, sa=1)
card(s, 0.5, 4.9, 6.05, 2.0, "Why hybrid", ["The hexahedral port solver treats gold as a perfect conductor: n = 1.888, flat, no loss.",
     "The 3-D line has n = 2.02 → 1.93 and loss. The split comes from geometry and is kept."])
card(s, 6.78, 4.9, 6.05, 2.0, "Why a band, not a line", ["Z_{even}/Z_{odd} − 1 known only to 0.30–0.45 %: the model is drawn at both ends, shaded between.",
     "NEXT ∝ this value (band ≈ 3.5 dB); FEXT barely depends on it."], hc=RED)

# 11 comparison
s = new(); title(s, "Model vs 3-D CST", "Black: coworker's 3-D runs · red band: cross-section model")
fig(s, "modal_vs_s4p_v3.png", 1.4, 1.5, 10.5, 5.45)

# 12 scorecard
s = new(); title(s, "Scorecard", "1 mm agrees; 5 mm NEXT above 25 GHz is the open point (values in dB, CST / model)")
rows = [["", "6 GHz", "18 GHz", "30 GHz", "42 GHz", "60 GHz", "Verdict"],
        ["1 mm NEXT", "−71 / −69…−65", "−62 / −61…−57", "−60 / −58…−55", "−61 / −58…−54", "−61 / −59…−56", "1–5 dB high"],
        ["1 mm FEXT", "−81 / −97…−84", "−72 / −76…−72", "−71 / −67…−65", "−70 / −63…−61", "−59 / −59…−58", "good at 18, 60 GHz"],
        ["5 mm FEXT", "−67 / −68…−66", "−80 / −59", "−57 / −54", "−50 / −51", "−44 / −48", "envelope OK, dips not"],
        ["5 mm NEXT", "−60 / −58…−55", "−65 / −68…−62", "−53 / −62…−61", "−48 / −57…−54", "−46 / −56…−55", "6–10 dB low > 25 GHz"]]
table(s, 0.5, 1.6, 12.35, rows, [1.5, 1.6, 1.6, 1.6, 1.6, 1.6, 2.0], size=12, row_h=0.5, hl=(4,))
card(s, 0.5, 4.4, 6.05, 2.5, "Why 5 mm NEXT may be off", ["A uniform line must show NEXT nulls every ~15 GHz. The 3-D 5 mm NEXT has none above 25 GHz.",
     "Extra near-end coupling (ports, ground modes) or numerical error."], hc=RED)
card(s, 6.78, 4.4, 6.05, 2.5, "Why we cannot tell yet", ["5 mm error floor |S_{21} − S_{43}| ≈ −56 dB at 30 GHz: the disputed values sit on it.",
     "Test: 5 mm 3-D run with finer mesh around the ports."])

# 13 cost
s = new(); title(s, "Cost", "One cross-section replaces a family of long 3-D runs")
stat(s, 0.5, 1.6, 3.95, 2.8, "hours", "per 3-D run and per length; the 5 mm run already sits at its error floor", col=MUTED)
stat(s, 4.69, 1.6, 3.95, 2.8, "minutes", "per 2-D frequency point (2 adaptive passes); 5 points cover 6–60 GHz")
stat(s, 8.88, 1.6, 3.95, 2.8, "free", "any length afterwards: 1, 5 or 14 mm is a formula, no cascade", col=RED)
text(s, 0.5, 4.8, 12.3, 0.6, "First 2-D run: ~47 min with 3 adaptive passes; pass 3 changed the line impedance by only 0.36 %.", size=12, color=MUTED)

# 14 prediction
s = new(); title(s, "Prediction for the 14 mm line", "Hybrid model, pitch 200 µm, straight uniform line, 50 Ω terminations")
fig(s, "predict_14mm.png", 0.5, 1.55, 8.6, 3.2)
for i, (b, t) in enumerate([("−48 dB", "FEXT at 30 GHz"), ("−43 dB", "FEXT at 60 GHz"), ("≈ −54 dB", "NEXT at 60 GHz (line only)")]):
    text(s, 9.4, 1.55 + i * 1.08, 3.4, 0.6, b, size=28, bold=True, color=RED if i < 2 else NAVY)
    text(s, 9.4, 2.12 + i * 1.08, 3.4, 0.4, t, size=12, color=MUTED)
card(s, 0.5, 5.0, 12.35, 1.9, "Reading", ["FEXT grows with length (about +20 dB from 1 to 14 mm) and dominates long lines.",
     "NEXT saturates with length; any near-end contribution of pads or ports must be added separately."])

# 15 slow wave
s = new(); title(s, "Slow-wave (T-loaded) lines", "Same physics; the cross-section becomes one unit cell")
card(s, 0.5, 1.6, 3.95, 2.5, "Still uniform", ["Tees repeat every few tens of µm ≪ RF wavelength: one effective n, Z, α per line up to 60 GHz."])
card(s, 4.69, 1.6, 3.95, 2.5, "Still even + odd", ["Identical, aligned lines keep the A↔B symmetry: the pair modes stay even and odd (Bloch modes)."])
card(s, 8.88, 1.6, 3.95, 2.5, "No 2-D port", ["One cross-section cannot see the tees: extract from one period instead."], hc=RED)
card(s, 0.5, 4.4, 6.05, 2.5, "Option 1", ["3-D eigenmode solve of one period of both lines, periodic boundaries → β_{even}, β_{odd}.",
     "Check: does the eigenmode solver accept anisotropic LiNbO_{3}?"])
card(s, 6.78, 4.4, 6.05, 2.5, "Option 2", ["Short 3-D runs of N and 2N periods → 4 × 4 transfer matrices → eigenvalues give γ_{even}, γ_{odd}; ports cancel.",
     "Reuses the extraction already written."])

# 16 next
s = new(); title(s, "Next steps")
for i, (h, b) in enumerate([("1  5 mm port mesh", "settles whether the 5 mm NEXT excess is real"), ("2  INTERCONNECT block", "4 RF ports + EO outputs, from this model"),
                            ("3  Lab launch", "check probes/pads tie each line's grounds"), ("4  Slow-wave lines", "unit-cell extraction, same model")]):
    x = 0.5 + i * 3.1; rect(s, x, 1.8, 2.95, 2.0, fill=WHITE, line=NAVY)
    text(s, x + 0.12, 1.9, 2.7, 1.8, [(h, {"bold": True, "color": NAVY, "size": 15}), (b, {"size": 12.5})], sa=4)

prs.save(os.path.join(HERE, "..", "crosstalk_cross_section.pptx")); print("saved", len(prs.slides._sldIdLst), "slides")
