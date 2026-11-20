# Injected into VPI_Madrid.ipynb cell 0 just before `polygons, Y_TOP = build_polygons()`.
# Madrid-Ti: continuous LN slab, Ti strips directly on the slab (conductor at DC, lossy optically),
# Au pad on Ti, Au bridge to a tall Au electrode standing on a SiO2 buffer that exists only outside the Ti.
GAP = G_TI                                   # field-defining gap = Ti gap
import os
N_TI = complex(os.environ.get("N_TI", "3.7+4.4j").replace(" ", ""))  # ASSUMED literature value; Al: 1.55+16j
eps_ti = (N_TI.real - 1j * N_TI.imag) ** 2   # exp(+jwt): Im(eps) < 0 is loss
MATERIALS["Ti_sig"] = {"color": "#d62728", "eps_dc": (1.0, 1.0), "eps_opt": (eps_ti,) * 3, "desc": "Ti (signal)"}
MATERIALS["Ti_gnd"] = {"color": "#a01818", "eps_dc": (1.0, 1.0), "eps_opt": (eps_ti,) * 3, "desc": "Ti (ground)"}
PREFIX_TO_MAT[:0] = [("tiR", "Ti_sig"), ("tiL", "Ti_gnd"), ("fill", "SiO2")]
_xi = G_TI / 2.0; _xg = _xi + TI_P; _xpo = _xg + PAD_W; _xto = _xpo + TI_X; _xo = _xto + SP_W
X_EL_OUT = _xo + OUT_W
DEV_W = 2.0 * X_EL_OUT + 2.0 * MARGIN
ETCHED = False


def build_polygons():
    ys = SLAB_H; x_dev = DEV_W / 2.0
    y_ti = round(ys + TI_H, 6); y_pad = round(y_ti + PAD_H, 6); y_br = round(y_pad + BR_H, 6)
    y_buf = round(ys + BUFFER_H, 6); y_tall = y_buf + TALL_H
    y_clad_top = ys + CLAD_H
    x_fine = max(X_FINE_MIN, _xo + 1.0)
    x_near = min(x_fine + 15.0, x_dev - 2.0)
    core = Polygon([(-WG_BOTTOM / 2, ys), (-WG_TOP / 2, ys + WG_H), (WG_TOP / 2, ys + WG_H), (WG_BOTTOM / 2, ys)])
    slab = box(-x_dev, 0.0, x_dev, ys)
    tiR = box(_xi, ys, _xto, y_ti)
    elR = unary_union([box(_xg, y_ti, _xpo, y_pad), box(_xg, y_pad, _xo, y_br),
                       box(_xo, y_buf, X_EL_OUT, y_tall)])
    elR = Polygon(elR.exterior)
    bufR = box(_xto, ys, x_dev, y_buf)
    fillR = _areal(box(_xpo, ys, _xo, y_pad).difference(unary_union([tiR, bufR])))
    capg = _areal(box(-_xg, ys, _xg, y_pad).difference(unary_union([core, tiR, mirror(tiR)])))
    solids = unary_union([core, slab, tiR, mirror(tiR), elR, mirror(elR), bufR, mirror(bufR),
                          fillR, mirror(fillR), capg])
    clad = box(-x_dev, 0.0, x_dev, y_clad_top).difference(solids)
    near = box(-_xg, y_pad, _xg, y_pad + 0.6)
    base = OrderedDict()
    base["core"] = core
    base["cap"] = capg
    base["fillR"] = fillR; base["fillL"] = mirror(fillR)
    bufs = unary_union([bufR, mirror(bufR)]).difference(unary_union([elR, mirror(elR)]))
    base["buf_fine"] = _areal(bufs.intersection(box(-x_fine, 0, x_fine, y_buf)))
    base["buf_far"] = _areal(bufs.difference(box(-x_fine, 0, x_fine, y_buf)))
    base["tiR"] = tiR; base["tiL"] = mirror(tiR)
    base["elR_bulk"] = elR; base["elL_bulk"] = mirror(elR)
    base["slab_fine"] = _areal(slab.intersection(box(-x_fine, 0, x_fine, ys)))
    base["slab_mid"] = _areal(slab.intersection(box(-x_near, 0, x_near, ys)).difference(box(-x_fine, 0, x_fine, ys)))
    base["slab_far"] = _areal(slab.difference(box(-x_near, 0, x_near, ys)))
    base["box_near"] = box(-(_xg + 1.0), -0.5, _xg + 1.0, 0.0)
    base["box_mid"] = box(-(_xg + 1.0), -1.5, _xg + 1.0, -0.5)
    base["box_far"] = box(-x_dev, -BOX_H, x_dev, 0.0).difference(box(-(_xg + 1.0), -1.5, _xg + 1.0, 0.0))
    base["clad_gap_up"] = _areal(clad.intersection(near))
    base["clad_far"] = _areal(clad.difference(near))
    r_c = min(CORNER_R, 0.4 * TI_H)
    pts = [(_xi, ys), (_xi, y_ti), (_xg, y_ti), (_xto, ys), (_xto, y_ti), (_xpo, y_ti)]
    pr = unary_union([box(px - r_c, py - r_c, px + r_c, py + r_c) for px, py in pts])
    patches = unary_union([pr, mirror(pr)])
    skR = unary_union([box(_xg, y_ti, _xpo, y_ti + SKIN_T), box(_xg, y_ti, _xg + SKIN_T, y_br)])
    skin = unary_union([skR, mirror(skR)])
    polys = OrderedDict()
    for name, reg in base.items():
        if reg.is_empty:
            continue
        pc = _areal(reg.intersection(patches))
        if not pc.is_empty:
            polys[name + "_corner"] = pc
        reg = _areal(reg.difference(patches))
        if name.startswith("el"):
            polys[name.replace("bulk", "skin")] = _areal(reg.intersection(skin))
            reg = _areal(reg.difference(skin))
        if not reg.is_empty:
            polys[name] = reg
    import shapely
    out = OrderedDict()
    for k, p in polys.items():
        q = _areal(shapely.set_precision(p, 1e-6))
        if not q.is_empty:
            out[k] = q
    return out, y_clad_top


_h_m = 0.007 if abs(N_TI.imag) > 10 else h_skin   # Al skin depth ~16 nm: finer
_TI_RES = {"tiR": (_h_m, 0.15), "tiL": (_h_m, 0.15), "fillR": (0.050, 0.30), "fillL": (0.050, 0.30)}
