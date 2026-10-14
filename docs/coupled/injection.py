"""A shunt current source vs a series voltage source in the middle of a line."""
import matplotlib; matplotlib.use("Agg")
import schemdraw, schemdraw.elements as elm
from PIL import Image
schemdraw.config(fontsize=12)
W, H = 9, 3
def frame(d):
    d.add(elm.Resistor().at((0, H)).to((0, 0)).label("Z_c\nline to\nnear end", loc="bottom"))
    d.add(elm.Resistor().at((W, H)).to((W, 0)).label("Z_c\nline to\nfar end", loc="top"))
    d.add(elm.Line().at((0, 0)).to((W, 0)))
d = schemdraw.Drawing(show=False); frame(d)
d.add(elm.Line().at((0, H)).to((W, H)))
d.add(elm.SourceI().at((W/2, 0)).to((W/2, H)).label("I from C_m", loc="bottom"))
d.add(elm.Dot().at((W/2, H)))
d.add(elm.Label().at((W/2, H + 0.8)).label("one node, one voltage V = I·Z_c/2\n→ the same V (same sign) at both ends", fontsize=11))
d.add(elm.Label().at((W/2, -1.0)).label("(a) shunt current source: capacitive coupling", fontsize=12))
d.save("inj_shunt.png", dpi=140)
d = schemdraw.Drawing(show=False); frame(d)
d.add(elm.Line().at((0, H)).to((W/2 - 1.5, H)))
d.add(elm.SourceV().endpoints((W/2 + 1.5, H), (W/2 - 1.5, H)).label("E from L_m", loc="bottom"))
d.add(elm.Line().at((W/2 + 1.5, H)).to((W, H)))
d.add(elm.Label().at((W/2, H + 0.8)).label("one loop, one current through both Z_c\n→ +E/2 at the near end, −E/2 at the far end", fontsize=11))
d.add(elm.Label().at((W/2, -1.0)).label("(b) series voltage source: inductive coupling", fontsize=12))
d.save("inj_series.png", dpi=140)
a, b = Image.open("inj_shunt.png"), Image.open("inj_series.png")
im = Image.new("RGB", (a.width + b.width + 60, max(a.height, b.height)), "white")
im.paste(a, (0, 0)); im.paste(b, (a.width + 60, 0)); im.save("injection.png")
