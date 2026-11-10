"""One S11 slide for the JEREZ and HELSINKI ALD decks (to be inserted by the user).
Usage: python3 build_s11_slide.py  -> ../../jerez/S11_slide_JEREZ.pptx, ../../helsinki/S11_slide_HELSINKI.pptx"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deck_helpers as H
from pptx import Presentation
from PIL import Image
from pptx.util import Inches
from pptx.oxml.ns import qn
M = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
CASES = [("jerez", "6JZ0011", "JEREZ", 15, "−21.1 → −20.5 dB", "−16.6 → −16.3 dB"),
         ("helsinki", "5HK0005", "HELSINKI", 8, "−20.5 → −20.5 dB", "−13.6 → −16.5 dB")]
for folder, w, name, n, med, mx in CASES:
    prs = Presentation(os.path.join(M, "..", "CST_line_extraction.pptx")); lst = prs.slides._sldIdLst
    for sl in list(lst): prs.part.drop_rel(sl.get(qn("r:id"))); lst.remove(sl)
    H.prs = prs; s = prs.slides.add_slide(prs.slide_layouts[12])
    H.title(s, f"Wafer {w}: return loss |S_{{11}}|", f"{n} chips · measured, before and after ALD")
    out = os.path.join(M, folder, f"out_{w}")
    for path, x, wd in ((os.path.join(out, "v2_S11.png"), 0.4, 6.4), (os.path.join(out, "S11_all_lines.png"), 6.95, 6.0)):
        H.rect(s, x, 1.5, wd, 3.9, fill=H.WHITE, line=H.BOX)
        W_, H_ = Image.open(path).size; sc = min((wd - .1) / W_, 3.8 / H_); ww, hh = W_ * sc, H_ * sc
        s.shapes.add_picture(path, Inches(x + (wd - ww) / 2), Inches(1.5 + (3.9 - hh) / 2), Inches(ww), Inches(hh))
    H.card(s, 0.4, 5.6, 6.4, 1.3, "Chip mean (left)", ["Measured mean and fitted-line mean, no ALD vs ALD; 50 Ω ends."], size=13)
    H.card(s, 6.95, 5.6, 6.0, 1.3, "No ALD → ALD, 1–60 GHz", [f"Median |S_{{11}}|: {med} · maximum: {mx} (medians over chips)."], size=13)
    p = os.path.join(M, folder, f"S11_slide_{name}.pptx"); prs.save(p); print("saved", p)
