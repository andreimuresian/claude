"""Thevenin's theorem on a simple divider (figure for the scripted TL note)."""
import matplotlib; matplotlib.use("Agg")
import schemdraw, schemdraw.elements as elm
from PIL import Image
schemdraw.config(fontsize=12)

def divider(d, x0, load):
    src = d.add(elm.SourceV().at((x0, 0)).up().label("10 V"))
    d.add(elm.Resistor().right().label("R1 = 100 Ω"))
    n = d.add(elm.Dot()).center
    d.add(elm.Resistor().down().label("R2 = 100 Ω", loc="top"))
    d.add(elm.Line().left().tox(x0))
    d.add(elm.Line().right().at((n[0], 0)).tox(x0 + 6.5))
    terminals_from(d, n, x0 + 6.5, load)

def terminals_from(d, n, x_end, load):
    d.add(elm.Line().at(n).right().tox(x_end))
    d.add(elm.Dot(open=not load).label("A", loc="right"))
    if load:
        d.add(elm.Resistor().down().label("R_L = 50 Ω\nV = 2.5 V", loc="bottom"))
    else:
        d.add(elm.Gap().down().label(("+", "V = 5 V", "–"), loc="bottom"))
    d.add(elm.Dot(open=not load).label("B", loc="right"))

def thev(d, x0, load):
    d.add(elm.SourceV().at((x0, 0)).up().label("V_th = 5 V"))
    d.add(elm.Resistor().right().label("R_th = 50 Ω"))
    n = d.here
    d.add(elm.Line().right().at((x0, 0)).tox(x0 + 6.5))
    terminals_from(d, n, x0 + 6.5, load)

def panel(fname, load, ta, tb, sym, foot):
    d = schemdraw.Drawing(show=False)
    divider(d, 0, load)
    thev(d, 13.5, load)
    d.add(elm.Label().at((3.2, 4.3)).label(ta, fontsize=13))
    d.add(elm.Label().at((16.7, 4.3)).label(tb, fontsize=13))
    d.add(elm.Label().at((9.0, 1.5)).label(sym, fontsize=34))
    d.add(elm.Label().at((10, -1.9)).label(foot, fontsize=12))
    d.save(fname, dpi=140)

panel("thevenin_top.png", False, "(a) a real circuit, terminals A–B", "(b) its Thevenin equivalent", "≡",
      "How (b) is found:  V_th = open-circuit voltage at A–B = 10·R2/(R1+R2) = 5 V\n"
      "R_th = resistance seen from A–B with the 10 V source set to zero (shorted) = R1 ∥ R2 = 50 Ω")
panel("thevenin_bottom.png", True, "(c) real circuit + a load", "(d) equivalent + the same load", "=",
      "(c): R2 ∥ R_L = 33.3 Ω, so V = 10·33.3/(100+33.3) = 2.5 V.     (d): V = 5·50/(50+50) = 2.5 V.\n"
      "Any load gives the same V and I in (c) and (d): seen from A–B the two circuits cannot be told apart.\n"
      "Both obey V = V_th − R_th·I.   For a driver, V_th is called the EMF and R_th is Zs.")
a, b = Image.open("thevenin_top.png"), Image.open("thevenin_bottom.png")
im = Image.new("RGB", (max(a.width, b.width), a.height + b.height + 30), "white")
im.paste(a, (0, 0)); im.paste(b, (0, a.height + 30)); im.save("thevenin.png")
