def build_polygons():
    xg = GAP / 2.0                                  # electrode inner edge (on the buffer)
    x_out = X_EL_OUT                                # electrode outer edge
    x_dev_max = DEV_W / 2.0
    xs = SLAB_W / 2.0                               # LN slab edge
    xb = round(xs + BUFFER_H, 9)                    # buffer edge on the slab side wall
    x_fine = max(X_FINE_MIN, xb + 1.0)              # end of the finely meshed slab / buffer
    x_near = min(x_fine + 15.0, x_dev_max - 2.0)

    y_slab_top = SLAB_H
    y_buf_top = round(SLAB_H + BUFFER_H, 9)         # rounded: must equal the buffer() vertex exactly; bottom of the gold on the slab
    y_el_top = round(y_buf_top + MTX, 9)            # gold top on the slab
    y_el_top_out = round(BUFFER_H + MTX, 9)         # gold top beyond the slab (drops by SLAB_H)
    y_cap_top = y_buf_top + CAP_H                   # cap height measured from the buffer top
    y_clad_top = y_slab_top + CLAD_H
    y_fine_top = y_buf_top + 0.6

    # ---- 1. LN: rib core and the etched slab ----------------------------------
    core_poly = Polygon([
        (-WG_BOTTOM / 2.0, y_slab_top), (-WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_TOP / 2.0, y_slab_top + WG_H), (WG_BOTTOM / 2.0, y_slab_top)])
    slab = box(-xs, 0.0, xs, y_slab_top)

    # ---- 2. Conformal SiO2 buffer: BUFFER_H on the slab top, on the slab side
    #         walls and on the BOX beyond the slab (deposited after the slab etch)
    # built from rectangles (not shapely buffer()) so every vertex is exact
    buf_all = _areal(unary_union([box(-x_dev_max, 0.0, x_dev_max, BUFFER_H), box(-xb, 0.0, xb, y_buf_top)])
                     .difference(slab).difference(core_poly))

    # ---- 3. SiO2 cap (2.0 x 1.4 um above the buffer), fused with the buffer
    cap_poly = _areal(box(-CAP_W / 2.0, y_slab_top, CAP_W / 2.0, y_fine_top)
                      .difference(core_poly).difference(buf_all))
    cap_up = box(-CAP_W / 2.0, y_fine_top, CAP_W / 2.0, y_cap_top)
    buf_cap = _areal(buf_all.intersection(box(-CAP_W / 2.0, 0.0, CAP_W / 2.0, y_clad_top)))
    cap_poly = _areal(unary_union([cap_poly, buf_cap]))
    buf = _areal(buf_all.difference(box(-CAP_W / 2.0, 0.0, CAP_W / 2.0, y_clad_top)))

    # ---- 4. Electrode (right = signal): conformal 2 um gold on the buffer
    el_r = _areal(unary_union([box(xg, y_buf_top, xb, y_el_top), box(xb, BUFFER_H, x_out, y_el_top_out)]))
    assert el_r.geom_type == "Polygon", "electrode is not a single body"

    # ---- 5. BOX ----------------------------------------------------------------
    box_near = box(-(xg + 1.0), -0.5, xg + 1.0, 0.0)
    box_mid = box(-(xg + 1.0), -1.5, xg + 1.0, -0.5)
    box_far = box(-x_dev_max, -BOX_H, x_dev_max, 0.0).difference(box(-(xg + 1.0), -1.5, xg + 1.0, 0.0))

    # ---- 6. Air -----------------------------------------------------------------
    solids = unary_union([core_poly, slab, buf_all, cap_poly, cap_up, el_r, mirror(el_r)])
    clad_all = box(-x_dev_max, 0.0, x_dev_max, y_clad_top).difference(solids)
    clad_gap = _areal(clad_all.intersection(box(-xg, 0.0, xg, y_fine_top)))
    clad_gap_up = _areal(clad_all.intersection(box(-xg, y_fine_top, xg, y_cap_top + 0.6)))
    clad_far = _areal(clad_all.difference(box(-xg, 0.0, xg, y_cap_top + 0.6)))

    def _split(g, a, b):
        return _areal(g.intersection(box(-b, -BOX_H, b, y_clad_top)).difference(box(-a, -BOX_H, a, y_clad_top)))

    base = OrderedDict()
    base["core"] = core_poly
    base["cap"] = cap_poly
    base["cap_up"] = cap_up
    base["elR_bulk"] = el_r
    base["elL_bulk"] = mirror(el_r)
    base["slab_fine"] = _split(slab, 0.0, x_fine)
    base["buf_fine"] = _split(buf, 0.0, x_fine)
    base["buf_mid"] = _split(buf, x_fine, x_near)
    base["buf_far"] = _split(buf, x_near, x_dev_max + 1)
    base["box_near"] = box_near
    base["box_mid"] = box_mid
    base["box_far"] = box_far
    base["clad_gap"] = clad_gap
    base["clad_gap_up"] = clad_gap_up
    base["clad_far"] = clad_far

    # ---- 7. Refinement: corner patches at the gold and slab corners -----------
    pts = [(xg, y_buf_top),                         # gold inner corner on the buffer (gold / SiO2 / air)
           (xs, y_slab_top), (xs, 0.0),             # slab end (LN / SiO2)
           (xb, y_buf_top), (xb, BUFFER_H)]         # gold wrapping the buffered slab end
    edges_x = [xg + 1.0, x_fine, CAP_W / 2.0]
    r_c = CORNER_R
    for i, (px, py) in enumerate(pts):
        for qx, qy in pts[i + 1:]:
            r_c = min(r_c, max(abs(px - qx), abs(py - qy)) / 2.5)
        for ex in edges_x:
            if 1e-9 < abs(px - ex) < r_c + 1e-9:
                r_c = 0.8 * abs(px - ex)
    assert r_c >= 0.01, "corner patches too small: not meshable"
    patches_r = unary_union([box(px - r_c, py - r_c, px + r_c, py + r_c) for px, py in pts])
    patches = unary_union([patches_r, mirror(patches_r)])

    # gold skin: along the gold / buffer interface out to BOT_SKIN_L past the slab
    # end, the inner wall (full height) and the foot of the outer wall
    skin_zone_r = unary_union([
        box(xg, y_buf_top, xb, y_buf_top + SKIN_T),
        box(xb, BUFFER_H, min(xb + BOT_SKIN_L, x_out), BUFFER_H + SKIN_T),
        box(xb, BUFFER_H, xb + SKIN_T, y_el_top),
        box(xg, y_buf_top, xg + SKIN_T, y_el_top),
        box(x_out - SKIN_T, BUFFER_H, x_out, BUFFER_H + OUTER_WALL_SKIN_H),
    ])
    skin_zone = unary_union([skin_zone_r, mirror(skin_zone_r)])

    polys = OrderedDict()
    for name, reg in base.items():
        if reg.is_empty:
            continue
        pc = _areal(reg.intersection(patches))
        if not pc.is_empty:
            polys[name + "_corner"] = pc
        reg = _areal(reg.difference(patches))
        if name.startswith("el"):
            sk = _areal(reg.intersection(skin_zone))
            polys[name.replace("bulk", "skin")] = sk
            reg = _areal(reg.difference(skin_zone))
        if not reg.is_empty:
            polys[name] = reg

    return polys, y_clad_top

