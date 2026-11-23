# Injected into VPI_Madrid.ipynb cell 0 before `polygons, Y_TOP = build_polygons()`.
# Madrid tri-galvanic: flat SiO2 buffer (rib through it), SiO2 cap over the rib (width = Al gap),
# 400 nm Al on the buffer from the cap edge to the electrode outer edge, conformal top SiO2 over cap and
# the Al protrusions (only between the Au1 inner edges), Au1 2 um on Al, Au2 10 um x 10 um at the outer edge.
import os
GAP = G_AL
N_AL = complex(os.environ.get("N_AL", "1.55+16j").replace(" ", ""))   # ASSUMED literature value
eps_al = (N_AL.real - 1j * N_AL.imag) ** 2
MATERIALS["Al_sig"] = {"color": "#a99bbf", "eps_dc": (1.0, 1.0), "eps_opt": (eps_al,) * 3, "desc": "Al (signal)"}
MATERIALS["Al_gnd"] = {"color": "#8a7aa6", "eps_dc": (1.0, 1.0), "eps_opt": (eps_al,) * 3, "desc": "Al (ground)"}
PREFIX_TO_MAT[:0] = [("alR", "Al_sig"), ("alL", "Al_gnd"), ("tox", "SiO2")]
_xa = G_AL / 2.0; _xg = _xa + TG_P
X_EL_OUT = _xa + EL_W
DEV_W = 2.0 * X_EL_OUT + 2.0 * MARGIN
ETCHED = False
BUFFER_H = TG_B


def build_polygons():
    ys = SLAB_H; x_dev = DEV_W / 2.0; xo = X_EL_OUT
    yb = round(ys + TG_B, 6); yal = round(yb + AL_H, 6); ycap = round(yb + CAPH_TG, 6)
    y1 = round(yal + AU1_H, 6); y2 = y1 + AU2_H; y_clad_top = ys + CLAD_H
    x_fine = max(X_FINE_MIN, _xg + 2.0); x_near = min(x_fine + 15.0, x_dev - 2.0)
    core = Polygon([(-WG_BOTTOM / 2, ys), (-WG_TOP / 2, ys + WG_H), (WG_TOP / 2, ys + WG_H), (WG_BOTTOM / 2, ys)])
    slab = box(-x_dev, 0.0, x_dev, ys)
    buf = _areal(box(-x_dev, ys, x_dev, yb).difference(core)) if TG_B > 0 else Polygon()
    cap = _areal(box(-_xa, ys, _xa, ycap).difference(unary_union([core, buf])))
    alR = box(_xa, yb, xo, yal)
    elR = Polygon(unary_union([box(_xg, yal, xo, y1), box(xo - AU2_W, y1, xo, y2)]).exterior)
    metals = unary_union([alR, mirror(alR), elR, mirror(elR)])
    solids0 = unary_union([core, slab, buf, cap, metals])
    tox = Polygon()
    if TOX_H > 0:
        seed = unary_union([cap, alR.intersection(box(_xa, yb, _xg, yal)), mirror(alR).intersection(box(-_xg, yb, -_xa, yal))])
        tox = _areal(seed.buffer(TOX_H, join_style=2, mitre_limit=10.0).intersection(box(-_xg, yb, _xg, y_clad_top)).difference(solids0))
    solids = unary_union([solids0, tox])
    clad = box(-x_dev, 0.0, x_dev, y_clad_top).difference(solids)
    near = box(-_xg, yb, _xg, ycap + TOX_H + 0.8)
    base = OrderedDict()
    base["core"] = core; base["cap"] = cap
    if TOX_H > 0: base["tox"] = tox
    if TG_B > 0:
        base["buf_fine"] = _areal(buf.intersection(box(-x_fine, 0, x_fine, yb)))
        base["buf_far"] = _areal(buf.difference(box(-x_fine, 0, x_fine, yb)))
    base["alR_bulk"] = alR; base["alL_bulk"] = mirror(alR)
    base["elR_bulk"] = elR; base["elL_bulk"] = mirror(elR)
    base["slab_fine"] = _areal(slab.intersection(box(-x_fine, 0, x_fine, ys)))
    base["slab_mid"] = _areal(slab.intersection(box(-x_near, 0, x_near, ys)).difference(box(-x_fine, 0, x_fine, ys)))
    base["slab_far"] = _areal(slab.difference(box(-x_near, 0, x_near, ys)))
    base["box_near"] = box(-(_xg + 1.0), -0.5, _xg + 1.0, 0.0)
    base["box_mid"] = box(-(_xg + 1.0), -1.5, _xg + 1.0, -0.5)
    base["box_far"] = box(-x_dev, -BOX_H, x_dev, 0.0).difference(box(-(_xg + 1.0), -1.5, _xg + 1.0, 0.0))
    base["clad_gap_up"] = _areal(clad.intersection(near))
    base["clad_far"] = _areal(clad.difference(near))
    r_c = min(CORNER_R, 0.4 * TG_B) if TG_B > 0 else 0.02
    pts = [(_xa, yb), (_xa, yal), (_xg, yal)]
    pr = unary_union([box(px - r_c, py - r_c, px + r_c, py + r_c) for px, py in pts])
    patches = unary_union([pr, mirror(pr)])
    xs_al = _xg + 1.5                                   # fine Al skin out to 1.5 um under Au1
    skA = box(_xa, yb, xs_al, yal).difference(box(_xa + SKIN_A, yb + SKIN_A, xs_al, yal - SKIN_A))
    skA = unary_union([skA, mirror(skA)])
    skE = unary_union([box(_xg, yal, _xg + SKIN_T, y1)]); skE = unary_union([skE, mirror(skE)])
    polys = OrderedDict()
    for name, reg in base.items():
        if reg.is_empty: continue
        pc = _areal(reg.intersection(patches))
        if not pc.is_empty: polys[name + "_corner"] = pc
        reg = _areal(reg.difference(patches))
        if name.startswith("al") or name.startswith("el"):
            sk = skA if name.startswith("al") else skE
            s = _areal(reg.intersection(sk))
            if not s.is_empty: polys[name.replace("bulk", "skin")] = s
            reg = _areal(reg.difference(sk))
        if not reg.is_empty: polys[name] = reg
    import shapely
    out = OrderedDict()
    for k, p in polys.items():
        q = _areal(shapely.set_precision(p, 1e-6))
        if not q.is_empty: out[k] = q
    return out, y_clad_top


_TG_RES = {"tox": (0.025, 0.20), "alR_skin": (0.007, 0.15), "alL_skin": (0.007, 0.15),
           "alR_bulk": (0.300, 0.40), "alL_bulk": (0.300, 0.40)}
