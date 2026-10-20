def build_polygons():
    r9 = lambda v: round(float(v), 9)
    xg = r9(GAP / 2.0)                              # gap edges at -xg (ground) and +xg (signal)
    xs = r9(SLAB_W / 2.0)                           # slab edge at the slab TOP
    xsb = r9(xs + SLAB_DX)                          # slab edge at the BOX
    x_gout = r9(-(xg + (STUB_W if TEE else GND_W))) # ground outer edge
    t_gnd = STUB_H if TEE else MTX
    x_fine = r9(xsb + 1.0)                          # fine slab / recess mesh out to |x| = xsb + 1

    y_slab_top = r9(SLAB_H)
    y_cap_top = r9(SLAB_H + CAP_H)
    y_clad_top = r9(SLAB_H + CLAD_H)
    y_fine_top = r9(SLAB_H + 0.6)
    y_rec = r9(-OE)

    # ---- 1. LN: rib + slab with 60 deg ends ----------------------------------
    core_poly = Polygon([
        (-WG_BOTTOM / 2.0, y_slab_top), (-WG_TOP / 2.0, y_slab_top + WG_H),
        (WG_TOP / 2.0, y_slab_top + WG_H), (WG_BOTTOM / 2.0, y_slab_top)])
    slab = Polygon([(-xsb, 0.0), (xsb, 0.0), (xs, y_slab_top), (-xs, y_slab_top)])

    # ---- 2. SiO2 cap ---------------------------------------------------------
    cap_poly = box(-CAP_W / 2.0, y_slab_top, CAP_W / 2.0, y_fine_top).difference(core_poly)
    cap_up = box(-CAP_W / 2.0, y_fine_top, CAP_W / 2.0, y_cap_top)

    # ---- 3. BOX, over-etched by OE outside the slab footprint (vertical walls)
    box_all = box(X_L, -BOX_H, X_R, 0.0)
    if OE > 0:
        box_all = box_all.difference(unary_union([box(X_L, y_rec, -xsb, 0.0), box(xsb, y_rec, X_R, 0.0)]))

    # ---- 4. Conformal gold of thickness t over [x1, x2]: on the slab top
    #         (y up to SLAB_H + t inside the slab footprint), on the BOX (up to t)
    #         outside it, and filling the over-etch recess below it.
    def gold(x1, x2, t):
        parts = [box(x1, 0.0, x2, t).difference(box(-xsb, 0.0, xsb, 1e3))]
        lo, hi = max(x1, -xsb), min(x2, xsb)
        if hi > lo:
            parts.append(box(lo, 0.0, hi, r9(y_slab_top + t)))
        if OE > 0:
            parts.append(box(x1, y_rec, x2, 0.0).difference(box(-xsb, y_rec, xsb, 0.0)))
        return _areal(unary_union(parts).difference(slab))

    el_sig = gold(xg, X_R, MTX)                     # signal, out to the symmetry plane
    el_gnd = gold(x_gout, -xg, t_gnd)               # ground (28 um) or stub (2 um x 0.5 um)
    for _e in (el_sig, el_gnd):
        assert _e.geom_type == "Polygon", "electrode is not a single body"

    # ---- 5. Air: everything else (above the BOX and in un-metallised recesses)
    solids = unary_union([core_poly, slab, cap_poly, cap_up, el_sig, el_gnd, box_all])
    clad_all = box(X_L, -BOX_H, X_R, y_clad_top).difference(solids)
    clad_gap = _areal(clad_all.intersection(box(-xg, 0.0, xg, y_fine_top)))
    clad_gap_up = _areal(clad_all.intersection(box(-xg, y_fine_top, xg, y_cap_top + 0.6)))
    clad_near = _areal(clad_all.intersection(box(-x_fine, y_rec - 1e-9 if OE > 0 else 0.0, -xg, y_fine_top)))
    clad_far = _areal(clad_all.difference(box(-xg, 0.0, xg, y_cap_top + 0.6))
                      .difference(box(-x_fine, y_rec - 1e-9 if OE > 0 else 0.0, -xg, y_fine_top)))

    xb1 = xg + 1.0
    base = OrderedDict()
    base["core"] = core_poly
    base["cap"] = cap_poly
    base["cap_up"] = cap_up
    base["elR_bulk"] = el_sig
    base["elL_bulk"] = el_gnd
    base["slab_fine"] = slab
    base["box_near"] = _areal(box_all.intersection(box(-xb1, -0.5, xb1, 0.0)))
    base["box_mid"] = _areal(box_all.intersection(box(-x_fine, -1.5, x_fine, 0.0)).difference(box(-xb1, -0.5, xb1, 0.0)))
    base["box_far"] = _areal(box_all.difference(box(-x_fine, -1.5, x_fine, 0.0)))
    base["clad_gap"] = clad_gap
    base["clad_gap_up"] = clad_gap_up
    base["clad_near"] = clad_near
    base["clad_far"] = clad_far

    # ---- 6. Refinement ----------------------------------------------------------
    # 6a. corner patches: gold / LN corners, slab ends, stub end, recess corners
    pts = [(-xg, y_slab_top), (xg, y_slab_top),                 # gold inner corners on the slab
           (xs, y_slab_top), (xsb, 0.0)]                        # signal-side slab end (in gold)
    pts += [(-xs, y_slab_top), (-xsb, 0.0)]                     # ground-side slab end (gold or air)
    if TEE:
        pts.append((x_gout, y_slab_top) if -x_gout < xs else (x_gout, 0.0))   # stub end
    if OE > 0:
        pts += [(xsb, y_rec), (-xsb, y_rec)]                    # pedestal feet
    pts = list(dict.fromkeys((r9(px), r9(py)) for px, py in pts))
    r_c = CORNER_R
    edges = [xb1, -xb1, x_fine, -x_fine, CAP_W / 2.0, -CAP_W / 2.0]
    for i, (px, py) in enumerate(pts):
        for qx, qy in pts[i + 1:]:
            r_c = min(r_c, max(abs(px - qx), abs(py - qy)) / 2.5)
        for ex in edges:
            if 1e-9 < abs(px - ex) < r_c + 1e-9:
                r_c = 0.8 * abs(px - ex)
    assert r_c >= 0.005, f"corner patches would be {r_c*1e3:.1f} nm: not meshable"
    patches = unary_union([box(px - r_c, py - r_c, px + r_c, py + r_c) for px, py in pts])

    # 6b. gold skin: gold within SKIN_T of the slab, of the BOX / pedestal surface
    #     out to BOT_SKIN_L past each slab end, and the inner walls (full height)
    support = unary_union([slab, box_all])
    skin_zone = unary_union([
        slab.buffer(SKIN_T, join_style=2),
        support.buffer(SKIN_T, join_style=2).intersection(
            box(-xsb - BOT_SKIN_L, -BOX_H, xsb + BOT_SKIN_L, y_slab_top)),
        box(xg, 0.0, xg + SKIN_T, y_clad_top), box(-xg - SKIN_T, 0.0, -xg, y_clad_top),
        box(x_gout, 0.0, x_gout + SKIN_T, y_slab_top + OUTER_WALL_SKIN_H),
    ])
    # refinement helper only: snap it to a 1 nm grid so its offset corners cannot land
    # ~1e-16 um from an electrode vertex (gmsh rejects the resulting zero-length line)
    import shapely
    skin_zone = shapely.set_precision(skin_zone, 1e-3)

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

