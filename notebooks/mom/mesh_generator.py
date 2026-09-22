"""Planar triangular mesh + RWG basis for the coplanar (G-S-G) travelling-wave
line with T-slots etched into the grounds.

Geometry (from the CST HF Multilayer history, all metal coplanar at z=0):
  * signal strip : Y in [-WS/2, WS/2]
  * ground L/R   : Y in +/-[WS/2+GAP, WS/2+GAP+WG],  WG = 70 um
  * propagation  : Z in [0, n_periods * PITCH],  PITCH = 200 um
  * T-slot per period per ground, cut from the inner edge:
        stem : width L1 (in Z), depth W1 (in Y from the inner edge)
        cap  : width L2 (in Z), depth W2 (in Y, just beyond the stem)
    surviving ground rim = WG - W1 - W2.

The mesh is a flat triangulation in the (Y, Z) plane.  RWG basis functions live
on interior edges (shared by two triangles); boundary edges carry no RWG but are
returned (flagged by end-face location) so the solver can build the ports.
"""
import numpy as np
import gmsh
import shapely.geometry as sg
from shapely.ops import unary_union
from shapely.affinity import scale as _sscale

PITCH = 200e-6
WG_DEF = 70e-6


def geom_from_row(row):
    """Dataset row (um) -> geometry dict in metres."""
    return dict(WS=row["WS"]*1e-6, GAP=row["GAP"]*1e-6, WG=WG_DEF,
                MTX=row["MTX"]*1e-6, CAP_W=row["CAP_W"]*1e-6,
                L1=row["L1"]*1e-6, L2=row["L2"]*1e-6,
                W1=row["W1"]*1e-6, W2=row["W2"]*1e-6,
                ETCH_DEPTH=row["ETCH_DEPTH"]*1e-6)


def _slot(zc, x_gi, W1, W2, L1, L2, x_go):
    """T-slot polygon centred at Z=zc on a right-hand ground (inner edge x_gi)."""
    b = min(x_gi + W1, x_go)
    c = min(x_gi + W1 + W2, x_go)
    stem = sg.box(x_gi - 1e-12, zc - L1/2, b, zc + L1/2)          # depth W1, width L1
    cap = sg.box(b, zc - L2/2, c, zc + L2/2)                       # depth W2, width L2
    return unary_union([stem, cap])


def footprint(g, n_periods, etched=True):
    """shapely (Multi)Polygon of the metal for a line of n_periods."""
    WS, GAP, WG = g["WS"], g["GAP"], g["WG"]
    Lz = n_periods * PITCH
    x_si, x_gi, x_go = WS/2, WS/2 + GAP, WS/2 + GAP + WG
    signal = sg.box(-x_si, 0.0, x_si, Lz)
    gR = sg.box(x_gi, 0.0, x_go, Lz)
    gL = sg.box(-x_go, 0.0, -x_gi, Lz)
    if etched and g["W1"] + g["W2"] > 0 and g["L1"] > 0 and g["L2"] > 0:
        slots = []
        for k in range(n_periods):
            zc = (k + 0.5) * PITCH
            sR = _slot(zc, x_gi, g["W1"], g["W2"], g["L1"], g["L2"], x_go)
            slots.append(sR)
            slots.append(_sscale(sR, xfact=-1.0, origin=(0, 0)))     # mirror to left
        cut = unary_union(slots)
        gR = gR.difference(cut); gL = gL.difference(cut)
    return unary_union([signal, gR, gL])


def _critical_lines(g, n_periods, etched):
    """Boundaries where the current concentrates: signal edges, ground inner
    edges and slot rims.  Used to grade the mesh (fine here, coarse outward)."""
    WS, GAP, WG = g["WS"], g["GAP"], g["WG"]
    Lz = n_periods*PITCH
    x_si, x_gi, x_go = WS/2, WS/2+GAP, WS/2+GAP+WG
    lines = [sg.LineString([(s*x_si, 0), (s*x_si, Lz)]) for s in (-1, 1)]
    lines += [sg.LineString([(s*x_gi, 0), (s*x_gi, Lz)]) for s in (-1, 1)]
    if etched and g["W1"]+g["W2"] > 0 and g["L1"] > 0 and g["L2"] > 0:
        for k in range(n_periods):
            zc = (k+0.5)*PITCH
            sR = _slot(zc, x_gi, g["W1"], g["W2"], g["L1"], g["L2"], x_go)
            lines.append(sR.boundary)
            lines.append(_sscale(sR.boundary, xfact=-1.0, origin=(0, 0)))
    return unary_union(lines)


def _add_poly(poly, hfun):
    """Register one shapely Polygon (with holes) as a gmsh plane surface;
    per-point mesh size from hfun(x, y)."""
    def loop(coords):
        pts = [gmsh.model.occ.addPoint(x, y, 0, hfun(x, y)) for x, y in coords[:-1]]
        lines = [gmsh.model.occ.addLine(pts[i], pts[(i+1) % len(pts)])
                 for i in range(len(pts))]
        return gmsh.model.occ.addCurveLoop(lines)
    outer = loop(list(poly.exterior.coords))
    holes = [loop(list(r.coords)) for r in poly.interiors]
    return gmsh.model.occ.addPlaneSurface([outer] + holes)


def build_mesh(g, n_periods, h, etched=True, h_coarse=None, grade=0.55):
    """Return a dict with nodes (Npt,2 in metres), tris (Ntri,3), tri_region
    ('sig'/'gL'/'gR'), and the geometry.  Mesh is graded: fine size `h` near
    the gap/slot boundaries, growing to `h_coarse` (default 3.6*h) in the outer
    ground.  V2.4 refinement just halves `h`."""
    if h_coarse is None:
        h_coarse = 3.6*h
    fp = footprint(g, n_periods, etched)
    polys = list(fp.geoms) if fp.geom_type == "MultiPolygon" else [fp]
    # fine band in |Y|: signal + gap + slot reach (W1+W2), coarse in outer ground
    x_gi = g["WS"]/2 + g["GAP"]
    yf = x_gi + max(g["W1"]+g["W2"], g["GAP"]) + 12e-6

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("line")
    for p in polys:
        _add_poly(p, lambda x, y: h_coarse)      # points neutral; field controls
    gmsh.model.occ.synchronize()
    me = gmsh.model.mesh.field.add("MathEval")
    gmsh.model.mesh.field.setString(
        me, "F", f"({h}) + ({grade})*max(0, fabs(y) - ({yf}))")
    cap = gmsh.model.mesh.field.add("MathEval")            # constant ceiling
    gmsh.model.mesh.field.setString(cap, "F", f"{h_coarse}")
    mn = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(mn, "FieldsList", [me, cap])
    gmsh.model.mesh.field.setAsBackgroundMesh(mn)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.model.mesh.generate(2)
    nt, nc, _ = gmsh.model.mesh.getNodes()
    nodes = nc.reshape(-1, 3)[:, :2]
    idmap = {int(t): i for i, t in enumerate(nt)}
    et, etags, enodes = gmsh.model.mesh.getElements(2)
    tris = None
    for typ, conn in zip(et, enodes):
        if typ == 2:                                    # 3-node triangle
            tris = np.array([idmap[int(v)] for v in conn]).reshape(-1, 3)
    gmsh.finalize()

    # orient every triangle counter-clockwise (the analytic coplanar integrals
    # _Ipot/_Ivec assume CCW; gmsh output is not guaranteed consistent)
    v = nodes[tris]
    sa = ((v[:, 1, 0]-v[:, 0, 0])*(v[:, 2, 1]-v[:, 0, 1])
          - (v[:, 2, 0]-v[:, 0, 0])*(v[:, 1, 1]-v[:, 0, 1]))
    cw = sa < 0
    tris[cw] = tris[cw][:, ::-1]

    WS, GAP = g["WS"], g["GAP"]
    x_si, x_gi = WS/2, WS/2 + GAP
    cen = nodes[tris].mean(axis=1)
    reg = np.where(np.abs(cen[:, 0]) <= x_si, "sig",
                   np.where(cen[:, 0] > 0, "gR", "gL"))
    return dict(nodes=nodes, tris=tris, region=reg, geom=g,
                n_periods=n_periods, Lz=n_periods*PITCH, etched=etched)


def rwg_basis(mesh):
    """Interior edges -> full RWG (charge-neutral); all boundary edges carry no
    unknown (natural zero normal current).  Ports are added later as a
    charge-neutral series delta-gap on a signal-strip cut (see mom_solver)."""
    nodes, tris = mesh["nodes"], mesh["tris"]
    region = mesh["region"]; Lz = mesh["Lz"]
    v = nodes[tris]
    area = 0.5*np.abs((v[:, 1, 0]-v[:, 0, 0])*(v[:, 2, 1]-v[:, 0, 1])
                      - (v[:, 2, 0]-v[:, 0, 0])*(v[:, 1, 1]-v[:, 0, 1]))
    cent = v.mean(axis=1)
    edge_map = {}
    for ti, tri in enumerate(tris):
        for a, b, opp in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
            key = tuple(sorted((int(tri[a]), int(tri[b]))))
            edge_map.setdefault(key, []).append((ti, int(tri[opp])))
    edges, tp, tm, vp, vm, L = [], [], [], [], [], []
    for key, lst in edge_map.items():
        if len(lst) != 2:
            continue                                         # boundary -> natural
        n0, n1 = key
        edges.append((n0, n1))
        tp.append(lst[0][0]); vp.append(lst[0][1])
        tm.append(lst[1][0]); vm.append(lst[1][1])
        L.append(np.hypot(*(nodes[n0]-nodes[n1])))
    return dict(edges=np.array(edges), tp=np.array(tp), tm=np.array(tm),
                vp=np.array(vp), vm=np.array(vm), L=np.array(L),
                area=area, cent=cent, nodes=nodes, tris=tris,
                region=region, Lz=Lz, geom=mesh["geom"])


# ==========================================================================
# Phase 3: Floquet periodic unit cell (one period, Bloch-wrapping RWG edges)
# ==========================================================================
def build_unit_cell(g, h, etched=True, h_coarse=None, grade=0.55):
    """One period (v in [0,P]) with the T-slot centred at v=P/2, meshed so the
    v=0 and v=P boundaries are node-for-node periodic (gmsh setPeriodic).  The
    returned dict matches build_mesh() plus 'periodic'=True."""
    if h_coarse is None:
        h_coarse = 3.6*h
    if max(g["L1"], g["L2"]) >= PITCH:
        raise ValueError("tee longer than the period; unit cell would wrap")
    fp = footprint(g, 1, etched)          # tee already centred at 0.5*PITCH
    polys = list(fp.geoms) if fp.geom_type == "MultiPolygon" else [fp]
    x_gi = g["WS"]/2 + g["GAP"]
    yf = x_gi + max(g["W1"]+g["W2"], g["GAP"]) + 12e-6

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("cell")
    for p in polys:
        _add_poly(p, lambda x, y: h_coarse)
    gmsh.model.occ.synchronize()
    # pair the v=0 and v=P boundary curves of each conductor
    bot, top = [], []
    for d, t in gmsh.model.getEntities(1):
        com = gmsh.model.occ.getCenterOfMass(d, t)
        if abs(com[1]) < 1e-12:
            bot.append((com[0], t))
        elif abs(com[1]-PITCH) < 1e-12:
            top.append((com[0], t))
    bot.sort(); top.sort()
    if len(bot) != len(top):
        gmsh.finalize()
        raise RuntimeError("unit-cell boundary curves do not pair up")
    aff = [1, 0, 0, 0,  0, 1, 0, PITCH,  0, 0, 1, 0,  0, 0, 0, 1]
    gmsh.model.mesh.setPeriodic(1, [t for _, t in top], [t for _, t in bot], aff)

    me = gmsh.model.mesh.field.add("MathEval")
    gmsh.model.mesh.field.setString(
        me, "F", f"({h}) + ({grade})*max(0, fabs(y) - ({yf}))")
    cap = gmsh.model.mesh.field.add("MathEval")
    gmsh.model.mesh.field.setString(cap, "F", f"{h_coarse}")
    mn = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(mn, "FieldsList", [me, cap])
    gmsh.model.mesh.field.setAsBackgroundMesh(mn)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.model.mesh.generate(2)
    nt, nc, _ = gmsh.model.mesh.getNodes()
    nodes = nc.reshape(-1, 3)[:, :2]
    idmap = {int(t): i for i, t in enumerate(nt)}
    et, _, enodes = gmsh.model.mesh.getElements(2)
    tris = None
    for typ, conn in zip(et, enodes):
        if typ == 2:
            tris = np.array([idmap[int(v)] for v in conn]).reshape(-1, 3)
    gmsh.finalize()

    v = nodes[tris]
    sa = ((v[:, 1, 0]-v[:, 0, 0])*(v[:, 2, 1]-v[:, 0, 1])
          - (v[:, 2, 0]-v[:, 0, 0])*(v[:, 1, 1]-v[:, 0, 1]))
    tris[sa < 0] = tris[sa < 0][:, ::-1]
    x_si = g["WS"]/2
    cen = nodes[tris].mean(axis=1)
    reg = np.where(np.abs(cen[:, 0]) <= x_si, "sig",
                   np.where(cen[:, 0] > 0, "gR", "gL"))
    return dict(nodes=nodes, tris=tris, region=reg, geom=g,
                n_periods=1, Lz=PITCH, etched=etched, periodic=True)


def rwg_basis_cell(mesh, tol=1e-9):
    """RWG basis on a periodic unit cell.  Interior edges are ordinary RWG.  An
    edge on v=0 is matched to its partner on v=P and becomes ONE wrapped basis
    function whose minus half lives in the next cell: shift[j]=+1 marks a half
    that sits at v+P, so its interactions pick up exp(j*beta*P) (handled in the
    assembly).  Edges on the outer metal rim carry no unknown."""
    nodes, tris = mesh["nodes"], mesh["tris"]
    region = mesh["region"]; P = mesh["Lz"]
    v = nodes[tris]
    area = 0.5*np.abs((v[:, 1, 0]-v[:, 0, 0])*(v[:, 2, 1]-v[:, 0, 1])
                      - (v[:, 2, 0]-v[:, 0, 0])*(v[:, 1, 1]-v[:, 0, 1]))
    cent = v.mean(axis=1)
    emap = {}
    for ti, tri in enumerate(tris):
        for a, b, opp in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
            key = tuple(sorted((int(tri[a]), int(tri[b]))))
            emap.setdefault(key, []).append((ti, int(tri[opp])))
    edges, tp, tm, vp, vm, L, sp_, sm_ = [], [], [], [], [], [], [], []
    bot, top = {}, {}
    for key, lst in emap.items():
        n0, n1 = key
        ln = float(np.hypot(*(nodes[n0]-nodes[n1])))
        if len(lst) == 2:
            edges.append((n0, n1))
            tp.append(lst[0][0]); vp.append(lst[0][1]); sp_.append(0)
            tm.append(lst[1][0]); vm.append(lst[1][1]); sm_.append(0)
            L.append(ln)
        else:
            y0, y1 = nodes[n0, 1], nodes[n1, 1]
            k = (round(min(nodes[n0, 0], nodes[n1, 0]), 12),
                 round(max(nodes[n0, 0], nodes[n1, 0]), 12))
            if abs(y0) < tol and abs(y1) < tol:
                bot[k] = (lst[0][0], lst[0][1], ln)
            elif abs(y0-P) < tol and abs(y1-P) < tol:
                top[k] = (lst[0][0], lst[0][1], ln)
    nwrap = 0
    for k, (tb, vb, ln) in bot.items():
        if k not in top:
            continue
        tt, vt, _ = top[k]
        # plus half: the v=P-side triangle (in this cell); minus half: the
        # v=0-side triangle, which for this basis sits one period up (shift +1)
        edges.append((-1, -1))
        tp.append(tt); vp.append(vt); sp_.append(0)
        tm.append(tb); vm.append(vb); sm_.append(1)
        L.append(ln); nwrap += 1
    return dict(edges=np.array(edges), tp=np.array(tp), tm=np.array(tm),
                vp=np.array(vp), vm=np.array(vm), L=np.array(L),
                shift_p=np.array(sp_), shift_m=np.array(sm_),
                area=area, cent=cent, nodes=nodes, tris=tris,
                region=region, Lz=P, geom=mesh["geom"], n_wrapped=nwrap)
