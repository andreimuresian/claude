# Madrid 1 (tri-galvanic) single-arm cross-section, injected before `polygons, Y_TOP = build_polygons()`.
import os
# Signal (right): tall Au (MTX_BIG) of width W_S. Ground (left): thin tongue MTX_SMALL x W_T, then tall MTX_BIG x W_G.
# Flat SiO2 buffer BUFFER_H on the continuous slab; SiO2 cap CAP_W x CAP_H (CAP_H from the buffer top); air above.
GAP = M1_GAP; BUFFER_H = M1_BUF; CAP_W = M1_CW; CAP_H = M1_CH
_xg = GAP / 2.0
X_EL_OUT = max(_xg + W_S, _xg + W_T + W_G)
DEV_W = 2.0 * X_EL_OUT + 2.0 * MARGIN
ETCHED = False


def build_polygons():
    ys = SLAB_H; x_dev = DEV_W / 2.0
    yb = round(ys + BUFFER_H, 6); ycap = round(yb + CAP_H, 6); y_clad_top = ys + CLAD_H
    core = Polygon([(-WG_BOTTOM / 2, ys), (-WG_TOP / 2, ys + WG_H), (WG_TOP / 2, ys + WG_H), (WG_BOTTOM / 2, ys)])
    slab = box(-x_dev, 0.0, x_dev, ys)
    # buffer only OUTSIDE the cap; the cap (same SiO2) fills down to the slab: no LN/buffer/cap triple point at the rib
    buf = _areal(box(-x_dev, ys, x_dev, yb).difference(box(-CAP_W / 2, ys, CAP_W / 2, yb))) if BUFFER_H > 0 else Polygon()
    cap = _areal(box(-CAP_W / 2, ys, CAP_W / 2, ycap).difference(core))
    elR = box(_xg, yb, _xg + W_S, yb + MTX_BIG)
    elL = Polygon(unary_union([box(-_xg - W_T, yb, -_xg, yb + MTX_SMALL),
                               box(-_xg - W_T - W_G, yb, -_xg - W_T, yb + MTX_BIG)]).exterior)
    # --- Gemini variants (all default off) ---
    TRW = float(os.environ.get("TRW", "0")); TRF = float(os.environ.get("TRF", "0.2"))      # U-slot trench width, floor above rib top
    STW = float(os.environ.get("STW", "0")); STT = float(os.environ.get("STT", "0"))        # stepped buffer: width under inner edge, total thickness
    SBX = float(os.environ.get("SBX", "0")); SBH = float(os.environ.get("SBH", "0.35"))     # inverted-L: bottom gold setback, height
    extra_ox = []
    if STW > 0:
        for s_ in (1, -1):
            st = box(_xg, ys, _xg + STW, ys + STT) if s_ > 0 else box(-_xg - STW, ys, -_xg, ys + STT)
            extra_ox.append(st)
        elR = Polygon(elR.difference(extra_ox[0]).exterior); elL = Polygon(elL.difference(extra_ox[1]).exterior)
    if SBX > 0:
        for s_ in (1, -1):
            sb = box(_xg, yb, _xg + SBX, yb + SBH) if s_ > 0 else box(-_xg - SBX, yb, -_xg, yb + SBH)
            extra_ox.append(sb)
        elR = Polygon(elR.difference(extra_ox[-2]).exterior); elL = Polygon(elL.difference(extra_ox[-1]).exterior)
    if extra_ox:
        cap = _areal(unary_union([cap] + extra_ox).difference(unary_union([core, elR, elL])))
        buf = _areal(buf.difference(unary_union(extra_ox)))
    TRMODE = os.environ.get("TRMODE", "both")      # both | opt (air optically, SiO2 at DC) | dc (air at DC, SiO2 optically)
    trench = Polygon()
    if TRW > 0:
        trench = _areal(box(-TRW / 2, ys + WG_H + TRF, TRW / 2, ycap).intersection(cap))
        cap = _areal(cap.difference(box(-TRW / 2, ys + WG_H + TRF, TRW / 2, ycap + 1.0)))
        if TRMODE != "both":
            MATERIALS["TRENCH"] = {"color": "#ffd0e0", "desc": "trench (split test)",
                "eps_dc": (3.75, 3.75) if TRMODE == "opt" else (1.0, 1.0),
                "eps_opt": (1.0, 1.0, 1.0) if TRMODE == "opt" else (n_sio2 ** 2,) * 3}
            PREFIX_TO_MAT.insert(0, ("trn", "TRENCH"))
    solids = unary_union([core, slab, buf, cap, elR, elL] + ([trench] if (TRW > 0 and TRMODE != "both") else []))
    clad = box(-x_dev, 0.0, x_dev, y_clad_top).difference(solids)
    near = box(-_xg, ycap, _xg, ycap + 0.6)
    base = OrderedDict()
    base["core"] = core; base["cap"] = cap
    if TRW > 0 and TRMODE != "both": base["trn"] = trench
    if BUFFER_H > 0: base["buf_fine"] = buf
    base["elR_bulk"] = elR; base["elL_bulk"] = elL
    base["slab_fine"] = slab                       # fine slab everywhere: the lateral slab wave must be resolved
    base["box_near"] = box(-(_xg + 1.0), -0.5, _xg + 1.0, 0.0)
    base["box_mid"] = box(-(_xg + 1.0), -1.5, _xg + 1.0, -0.5)
    base["box_far"] = box(-x_dev, -BOX_H, x_dev, 0.0).difference(box(-(_xg + 1.0), -1.5, _xg + 1.0, 0.0))
    base["clad_gap_up"] = _areal(clad.intersection(near))
    base["clad_far"] = _areal(clad.difference(near))
    r_c = min(CORNER_R, 0.4 * BUFFER_H) if BUFFER_H > 0 else CORNER_R
    pts = [(_xg, yb), (_xg + W_S, yb), (-_xg, yb), (-_xg - W_T - W_G, yb)]
    if STW > 0: pts += [(s_ * _xg, ys + STT) for s_ in (1, -1)] + [(s_ * (_xg + STW), ys + STT) for s_ in (1, -1)] + [(s_ * (_xg + STW), yb) for s_ in (1, -1)]
    if SBX > 0: pts += [(s_ * (_xg + SBX), yb) for s_ in (1, -1)] + [(s_ * (_xg + SBX), yb + SBH) for s_ in (1, -1)] + [(s_ * _xg, yb + SBH) for s_ in (1, -1)]
    pts = [p for p in pts if not (p == (-_xg, yb) and (STW > 0 or SBX > 0)) and not (p == (_xg, yb) and (STW > 0 or SBX > 0))]
    patches = unary_union([box(px - r_c, py - r_c, px + r_c, py + r_c) for px, py in pts])
    if BUFFER_H > 0 and os.environ.get("RIBPATCH", "0") == "1":   # rib-base corners: LN / buffer / cap junctions
        xb = WG_BOTTOM / 2.0; xt = xb - BUFFER_H / np.tan(np.deg2rad(ALPHA)); rr = min(0.02, 0.3 * BUFFER_H)
        rp = unary_union([box(x - rr, y - rr, x + rr, y + rr) for x, y in ((xb, ys), (xt, yb))])
        patches = unary_union([patches, rp, mirror(rp)])
    # gold skin: the full bottom face of both electrodes, plus the inner walls
    _sk = []
    for s_ in (1, -1):
        if STW > 0: _sk.append(box(min(s_ * _xg, s_ * (_xg + STW)), ys + STT, max(s_ * _xg, s_ * (_xg + STW)), ys + STT + SKIN_T))
        if SBX > 0:
            _sk.append(box(min(s_ * (_xg + SBX), s_ * (_xg + SBX + SKIN_T)), yb, max(s_ * (_xg + SBX), s_ * (_xg + SBX + SKIN_T)), yb + SBH))
            _sk.append(box(min(s_ * _xg, s_ * (_xg + SBX)), yb + SBH, max(s_ * _xg, s_ * (_xg + SBX)), yb + SBH + SKIN_T))
    skin = unary_union(_sk + [box(-x_dev, yb, x_dev, yb + SKIN_T),
                        box(_xg, yb, _xg + SKIN_T, yb + MTX_BIG), box(-_xg - SKIN_T, yb, -_xg, yb + MTX_SMALL)])
    polys = OrderedDict()
    for name, reg in base.items():
        if reg.is_empty: continue
        pc = _areal(reg.intersection(patches))
        if not pc.is_empty: polys[name + "_corner"] = pc
        reg = _areal(reg.difference(patches))
        if name.startswith("el"):
            s = _areal(reg.intersection(skin))
            if not s.is_empty: polys[name.replace("bulk", "skin")] = s
            reg = _areal(reg.difference(skin))
        if not reg.is_empty: polys[name] = reg
    import shapely
    out = OrderedDict()
    for k, p in polys.items():
        q = _areal(shapely.set_precision(p, 1e-6))
        if not q.is_empty: out[k] = q
    return out, y_clad_top
