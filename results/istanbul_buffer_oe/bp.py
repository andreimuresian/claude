def build_polygons():
    r9 = lambda v: round(float(v), 9)
    xg = r9(GAP / 2.0)                              # electrode inner edge (on the buffer)
    x_out = r9(X_EL_OUT)                            # electrode outer edge
    X = r9(DEV_W / 2.0)
    a = np.deg2rad(ALPHA_SLAB)
    b = BUFFER_H
    xs = r9(SLAB_W / 2.0)                           # slab edge at the slab TOP
    xsb = r9(xs + SLAB_H / np.tan(a))               # slab edge at the BOX (foot)
    y_slab_top = r9(SLAB_H)
    y_buf_top = r9(SLAB_H + b)                      # buffer top on the slab = bottom of the gold
    y_cap_top = r9(y_buf_top + CAP_H)               # cap height measured from the buffer top
    y_clad_top = r9(SLAB_H + CLAD_H)
    y_fine_top = r9(y_buf_top + 0.6)

    # ---- substrate profile (right half): slab top, 60 deg slope, pedestal wall
    #      down to -OE (over-etch, vertical), recess floor.  The conformal buffer
    #      surface is that profile offset by b (mitred corners), computed exactly:
    nx, ny = np.sin(a), np.cos(a)                   # outward normal of the slope
    # slope offset line: points p with (p - (xs,SH)) . n = b
    def on_slope_y(x):                              # y of the offset slope line at x
        return SLAB_H + (b - (x - xs) * nx) / ny
    def on_slope_x(y):
        return xs + (b - (y - SLAB_H) * ny) / nx
    C1 = (r9(on_slope_x(SLAB_H + b)), y_buf_top)    # top / slope corner
    if OE > 0:
        C2 = (r9(xsb + b), r9(on_slope_y(xsb + b)))  # slope / pedestal-wall corner (convex)
        C3 = (r9(xsb + b), r9(-OE + b))              # wall / recess-floor corner (concave)
        surf_r = [C1, C2, C3, (X, C3[1])]
    else:
        C2 = (r9(on_slope_x(b)), r9(b))              # slope / BOX corner (concave)
        surf_r = [C1, C2, (X, r9(b))]
    x_foot = C2[0]                                   # where the gold leaves the slope
    surf = [(-x, y) for x, y in reversed(surf_r)] + surf_r
    UNDER = Polygon([(-X, -BOX_H)] + surf + [(X, -BOX_H)])     # everything below the buffer top

    # ---- 1. LN ------------------------------------------------------------------
    core_poly = Polygon([
        (-WG_BOTTOM / 2.0, y_slab_top), (-WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_TOP / 2.0, y_slab_top + WG_H), (WG_BOTTOM / 2.0, y_slab_top)])
    slab = Polygon([(-xsb, 0.0), (xsb, 0.0), (xs, y_slab_top), (-xs, y_slab_top)])

    # ---- 2. BOX, over-etched by OE outside the slab footprint (vertical walls)
    box_all = box(-X, -BOX_H, X, 0.0)
    if OE > 0:
        box_all = box_all.difference(unary_union([box(-X, -OE, -xsb, 0.0), box(xsb, -OE, X, 0.0)]))

    # ---- 3. conformal SiO2 buffer (deposited after slab etch + over-etch) ------
    buf_all = _areal(UNDER.difference(box_all).difference(slab).difference(core_poly))

    # ---- 4. SiO2 cap above the buffer, fused with it ------------------------------
    cap_poly = _areal(box(-CAP_W / 2.0, y_slab_top, CAP_W / 2.0, y_fine_top)
                      .difference(core_poly).difference(buf_all))
    cap_up = box(-CAP_W / 2.0, y_fine_top, CAP_W / 2.0, y_cap_top)
    buf_cap = _areal(buf_all.intersection(box(-CAP_W / 2.0, 0.0, CAP_W / 2.0, y_clad_top)))
    cap_poly = _areal(unary_union([cap_poly, buf_cap]))
    buf = _areal(buf_all.difference(box(-CAP_W / 2.0, -BOX_H, CAP_W / 2.0, y_clad_top)))

    # ---- 5. Electrode (right = signal): 2 um gold on the buffer, top at buffer
    #         top + MTX on the slab, b + MTX beyond (step at the slope foot);
    #         below that it fills the buffer-lined recess
    el_r = _areal(unary_union([box(xg, -BOX_H, x_foot, r9(y_buf_top + MTX)),
                               box(x_foot, -BOX_H, x_out, r9(b + MTX))]).difference(UNDER))
    assert el_r.geom_type == "Polygon", "electrode is not a single body"

    # ---- 6. Air -----------------------------------------------------------------
    solids = unary_union([core_poly, slab, buf_all, cap_poly, cap_up, el_r, mirror(el_r), box_all])
    clad_all = box(-X, -BOX_H, X, y_clad_top).difference(solids)
    clad_gap = _areal(clad_all.intersection(box(-xg, 0.0, xg, y_fine_top)))
    clad_gap_up = _areal(clad_all.intersection(box(-xg, y_fine_top, xg, y_cap_top + 0.6)))
    clad_far = _areal(clad_all.difference(box(-xg, 0.0, xg, y_cap_top + 0.6)))

    x_fine = r9(max(X_FINE_MIN, x_foot + 1.0))
    x_near = r9(min(x_fine + 15.0, X - 2.0))
    def _split(g, a0, a1):
        return _areal(g.intersection(box(-a1, -BOX_H - 1, a1, y_clad_top)).difference(box(-a0, -BOX_H - 1, a0, y_clad_top)))
    xb1 = r9(xg + 1.0)
    base = OrderedDict()
    base["core"] = core_poly
    base["cap"] = cap_poly
    base["cap_up"] = cap_up
    base["elR_bulk"] = el_r
    base["elL_bulk"] = mirror(el_r)
    base["slab_fine"] = slab
    base["buf_fine"] = _split(buf, 0.0, x_fine)
    base["buf_mid"] = _split(buf, x_fine, x_near)
    base["buf_far"] = _split(buf, x_near, X + 1)
    base["box_near"] = _areal(box_all.intersection(box(-xb1, -0.5, xb1, 0.0)))
    base["box_mid"] = _areal(box_all.intersection(box(-x_fine, -1.5, x_fine, 0.0)).difference(box(-xb1, -0.5, xb1, 0.0)))
    base["box_far"] = _areal(box_all.difference(box(-x_fine, -1.5, x_fine, 0.0)))
    base["clad_gap"] = clad_gap
    base["clad_gap_up"] = clad_gap_up
    base["clad_far"] = clad_far

    # ---- 7. Refinement: corner patches + gold skin -------------------------------
    pts = [(xg, y_buf_top), C1, C2] + ([C3] if OE > 0 else []) + [(xs, y_slab_top), (xsb, 0.0)]
    pts = list(dict.fromkeys((r9(px), r9(py)) for px, py in pts))
    r_c = CORNER_R
    edges = [xb1, x_fine, CAP_W / 2.0]
    for i, (px, py) in enumerate(pts):
        for qx, qy in pts[i + 1:]:
            r_c = min(r_c, max(abs(px - qx), abs(py - qy)) / 2.5)
        for ex in edges:
            if 1e-9 < abs(px - ex) < r_c + 1e-9:
                r_c = 0.8 * abs(px - ex)
    assert r_c >= 0.005, f"corner patches would be {r_c*1e3:.1f} nm: not meshable"
    patches_r = unary_union([box(px - r_c, py - r_c, px + r_c, py + r_c) for px, py in pts])
    patches = unary_union([patches_r, mirror(patches_r)])

    import shapely
    skin_r = unary_union([
        box(xg, y_buf_top, x_foot, y_buf_top + SKIN_T),                  # gold on the slab buffer
        UNDER.buffer(SKIN_T, join_style=2).intersection(box(C1[0] - SKIN_T, -BOX_H, x_foot + BOT_SKIN_L, y_buf_top + SKIN_T)),
        box(xg, y_buf_top, xg + SKIN_T, y_clad_top),                     # inner wall
        box(x_out - SKIN_T, -BOX_H, x_out, b + OUTER_WALL_SKIN_H),       # outer wall foot
    ])
    skin_zone = shapely.set_precision(unary_union([skin_r, mirror(skin_r)]), 1e-3)   # helper only

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
            if not sk.is_empty:
                polys[name.replace("bulk", "skin")] = sk
            reg = _areal(reg.difference(skin_zone))
        if not reg.is_empty:
            polys[name] = reg
    return polys, y_clad_top

