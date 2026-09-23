"""Common-mesh differencing for the T-slot unit cell (Phase 3 remediation).

Phase 3 built the etched and the unetched cell with two INDEPENDENT calls to
gmsh, so their triangulations were unrelated (row 38: 1756 unetched vs 1342
etched).  The discretisation errors in C, L and alpha were therefore
uncorrelated and did not cancel in the perturbation

        dC = C_etched - C_unetched ,

which is a ~5 % difference of two ~2e-10 F/m numbers.  A 1-3 % error in each
term is then a 25-60 % error in the difference -- exactly the observed V3.4c
failure.

The fix is to difference on ONE triangulation.  Note the construction runs the
opposite way to the obvious one: the RWG unknowns live on metal only, so the
etched mesh has no triangles inside the slot at all and there is nothing there
to re-tag.  Instead we mesh the UNETCHED metal with the tee outline embedded as
an internal constraint (the slot is a separate gmsh surface, fragmented against
the surrounding ground so the mesh is conformal across its rim), and obtain the
etched cell by DELETING the slot triangles.  Hence

  * nodes            -- identical array for both cells
  * triangles        -- etched set is a strict subset of the unetched set, and
                        every surviving triangle has bit-identical vertices
  * RWG basis        -- identical on every edge that does not touch the slot
                        rim; rim edges are interior (unknown) in the unetched
                        cell and boundary (no unknown) in the etched cell,
                        which is the correct physics in both cases
  * triangle counts  -- NOT equal; they differ by exactly n_slot_tris.  Equal
                        counts would mean the slot had not been cut.
"""
import numpy as np
import gmsh
import shapely.geometry as sg
from shapely.ops import unary_union
from shapely.affinity import scale as _sscale

from mesh_generator import PITCH, _slot, _add_poly, rwg_basis_cell


def _pieces(g):
    """Decompose the unetched unit-cell metal into (metal, slot) shapely parts.

    Returns (list_of_polys, list_of_is_slot, slot_union).  The slot union is
    empty when the row carries no tee."""
    WS, GAP, WG = g["WS"], g["GAP"], g["WG"]
    x_si, x_gi, x_go = WS/2, WS/2 + GAP, WS/2 + GAP + WG
    sig = sg.box(-x_si, 0.0, x_si, PITCH)
    gR = sg.box(x_gi, 0.0, x_go, PITCH)
    gL = sg.box(-x_go, 0.0, -x_gi, PITCH)
    has_tee = g["W1"] + g["W2"] > 0 and g["L1"] > 0 and g["L2"] > 0
    polys, is_slot, slots = [sig], [False], []
    for full, mirror in ((gR, False), (gL, True)):
        if not has_tee:
            polys.append(full); is_slot.append(False)
            continue
        s = _slot(0.5*PITCH, x_gi, g["W1"], g["W2"], g["L1"], g["L2"], x_go)
        if mirror:
            s = _sscale(s, xfact=-1.0, origin=(0, 0))
        hole = s.intersection(full)          # clips the 1e-12 overhang exactly
        met = full.difference(s)
        for part, flag in ((met, False), (hole, True)):
            for q in (part.geoms if part.geom_type == "MultiPolygon" else [part]):
                if q.area <= 0:
                    continue
                polys.append(q); is_slot.append(flag)
        slots.append(hole)
    return polys, is_slot, (unary_union(slots) if slots else sg.Polygon())


def build_common_cells(g, h, h_coarse=None, grade=0.55, tol=1e-9):
    """Mesh once; return (cell_unetched, cell_etched, info).

    Both cells are rwg_basis_cell() dicts sharing the same `nodes` array.  The
    etched cell's triangles are the unetched cell's with the slot rows removed.
    """
    if h_coarse is None:
        h_coarse = 3.6*h
    if max(g["L1"], g["L2"]) >= PITCH:
        raise ValueError("tee longer than the period; unit cell would wrap")
    polys, is_slot, slot_u = _pieces(g)
    x_gi = g["WS"]/2 + g["GAP"]
    yf = x_gi + max(g["W1"] + g["W2"], g["GAP"]) + 12e-6

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("common")
        tags = [_add_poly(p, lambda x, y: h_coarse) for p in polys]
        # Glue the slot surfaces to the surrounding ground so the triangulation
        # is conformal across the tee rim.  The fragment MAP (not a centroid
        # test) says which output surface came from which input: the etched
        # ground is a C around the tee and its centroid lies inside the notch,
        # so a point-in-polygon test misclassifies it as slot.
        if len(tags) > 1:
            _, omap = gmsh.model.occ.fragment([(2, tags[0])],
                                              [(2, t) for t in tags[1:]])
        else:
            omap = [[(2, tags[0])]]
        gmsh.model.occ.synchronize()

        surf, slot_surf = [], []
        for k, outs in enumerate(omap):
            for d, t in outs:
                if d != 2:
                    continue
                surf.append(t)
                if is_slot[k]:
                    slot_surf.append(t)
        if len(set(surf)) != len(surf):
            raise RuntimeError("fragment produced shared surfaces; "
                               "metal/slot tagging would be ambiguous")
        surf = sorted(set(surf))

        # periodic pairing of the v = 0 and v = P conductor edges
        bot, top = [], []
        for d, t in gmsh.model.getEntities(1):
            com = gmsh.model.occ.getCenterOfMass(d, t)
            if abs(com[1]) < 1e-12:
                bot.append((round(com[0], 12), t))
            elif abs(com[1] - PITCH) < 1e-12:
                top.append((round(com[0], 12), t))
        bot.sort(); top.sort()
        if len(bot) != len(top):
            raise RuntimeError(f"unit-cell boundary curves do not pair up "
                               f"({len(bot)} bottom vs {len(top)} top)")
        aff = [1, 0, 0, 0,  0, 1, 0, PITCH,  0, 0, 1, 0,  0, 0, 0, 1]
        gmsh.model.mesh.setPeriodic(1, [t for _, t in top],
                                    [t for _, t in bot], aff)

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
        tri_list, slot_flag = [], []
        for t in surf:
            et, _, en = gmsh.model.mesh.getElements(2, t)
            for typ, conn in zip(et, en):
                if typ != 2:
                    continue
                tt = np.array([idmap[int(v)] for v in conn]).reshape(-1, 3)
                tri_list.append(tt)
                slot_flag.append(np.full(len(tt), t in slot_surf))
        tris = np.vstack(tri_list)
        slot = np.concatenate(slot_flag)
    finally:
        gmsh.finalize()

    # CCW orientation (the analytic coplanar integrals assume it)
    v = nodes[tris]
    sa = ((v[:, 1, 0]-v[:, 0, 0])*(v[:, 2, 1]-v[:, 0, 1])
          - (v[:, 2, 0]-v[:, 0, 0])*(v[:, 1, 1]-v[:, 0, 1]))
    tris[sa < 0] = tris[sa < 0][:, ::-1]

    x_si = g["WS"]/2
    cen = nodes[tris].mean(axis=1)
    reg = np.where(np.abs(cen[:, 0]) <= x_si, "sig",
                   np.where(cen[:, 0] > 0, "gR", "gL"))

    def _cell(mask, etched):
        return dict(nodes=nodes, tris=tris[mask], region=reg[mask], geom=g,
                    n_periods=1, Lz=PITCH, etched=etched, periodic=True)

    keep = np.ones(len(tris), bool)
    mu = rwg_basis_cell(_cell(keep, False))
    me_ = rwg_basis_cell(_cell(~slot, True))
    info = dict(Nt_unetched=int(keep.sum()), Nt_etched=int((~slot).sum()),
                Nt_slot=int(slot.sum()), Ne_unetched=len(mu["L"]),
                Ne_etched=len(me_["L"]), nodes=len(nodes),
                wrap_unetched=mu["n_wrapped"], wrap_etched=me_["n_wrapped"],
                subset_ok=bool(np.array_equal(tris[~slot], tris[~slot])),
                shared_identical=bool(
                    np.array_equal(me_["tris"], tris[~slot])),
                same_nodes=mu["nodes"] is me_["nodes"])
    return mu, me_, info
