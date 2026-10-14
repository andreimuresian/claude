"""Equivalent circuit of a length dz of two coupled lines."""
import matplotlib; matplotlib.use("Agg")
import schemdraw, schemdraw.elements as elm
schemdraw.config(fontsize=12)
d = schemdraw.Drawing(show=False)
yT, yA, yB, yG = 9, 6, 3, 0
def line(y, n, lab_loc):
    d.add(elm.Dot(open=True).at((0, y)).label(f"V{n}(z)\nI{n} →", loc="left"))
    d.add(elm.Resistor().right().label(f"R_s·dz", loc=lab_loc))
    d.add(elm.Inductor2().right().label(f"L_s·dz", loc=lab_loc))
    d.add(elm.Line().right().length(4.5))
    d.add(elm.Dot(open=True).label(f"V{n}(z+dz)", loc="right"))
line(yA, "₁", "top"); line(yB, "₂", "bottom")
for y in (yT, yG):
    d.add(elm.Line().at((0, y)).right().length(10.5))
d.add(elm.Label().at((5.2, yT + 0.45)).label("return (grounds)"))
d.add(elm.Label().at((5.2, yG - 0.5)).label("return (grounds)"))
d.add(elm.Capacitor().at((7.2, yA)).to((7.2, yB)).label("C_m·dz", loc="bottom").color("#c62828"))
d.add(elm.Capacitor().at((8.8, yA)).to((8.8, yT)).label("C_g·dz", loc="bottom"))
d.add(elm.Capacitor().at((8.8, yB)).to((8.8, yG)).label("C_g·dz", loc="top"))
d.add(elm.Line().at((4.5, yA - 0.7)).to((4.5, yB + 0.7)).color("#1565c0").linestyle("--"))
d.add(elm.Label().at((2.9, 4.5)).label("L_m·dz, R_m·dz\n(shared flux,\nshared return)", fontsize=11, color="#1565c0"))
d.save("cell.png", dpi=140)
