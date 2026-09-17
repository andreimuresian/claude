"""3D unit cell, layered extrusion, with explicit face tracking.

Each base face is extruded individually so that the mapping
base face -> (volume, top face) is exact at every layer.  No geometric
guessing, so notches and gaps can never be mistaken for metal.
"""
import numpy as np
import gmsh


def build(ws=35., gap=6., t_au=1., L1=20., L2=60., W1=15., W2=25.,
          pitch=200., w_gnd=70., pad=100., si_h=100., box_h=4.7, ln_h=0.46,
          air_h=60., etched=True, lc_gap=1.2, lc_far=25.,
          n_ln=4, n_ox=5, n_si=5, n_au=2, n_air=6,
          out="l3.msh", verbose=False):
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
    occ = gmsh.model.occ
    gmsh.model.add("l3")
    hw = ws / 2 + gap + w_gnd + pad
    g0 = ws / 2 + gap

    base = occ.addRectangle(-hw, 0, 0, 2 * hw, pitch)
    sig = occ.addRectangle(-ws / 2, 0, 0, ws, pitch)
    gr = occ.addRectangle(g0, 0, 0, w_gnd, pitch)
    gl = occ.addRectangle(-g0 - w_gnd, 0, 0, w_gnd, pitch)

    grounds = [(2, gr), (2, gl)]
    if etched:
        zc, cuts = pitch / 2, []
        for sgn in (+1, -1):
            inner, off = (g0 if sgn > 0 else -g0), 0.0
            for (L, W) in ((L1, W1), (L2, W2)):
                x_lo = inner + off if sgn > 0 else inner - off - W
                cuts.append((2, occ.addRectangle(x_lo, zc - L / 2, 0, W, L)))
                off += W
        grounds, _ = occ.cut(grounds, cuts, removeObject=True, removeTool=True)

    tools = [(2, sig)] + grounds
    _, omap = occ.fragment([(2, base)], tools)
    occ.synchronize()

    sig_faces = {t for d, t in omap[1]}
    gnd_faces = {t for grp in omap[2:] for d, t in grp}

    faces, labels = [], []
    for d, t in gmsh.model.getEntities(2):
        bb = gmsh.model.getBoundingBox(d, t)
        if abs(bb[2]) < 1e-4 and abs(bb[5]) < 1e-4:
            faces.append(t)
            labels.append("signal" if t in sig_faces
                          else "ground" if t in gnd_faces else "air")

    # size field: fine near every metal edge, growing outward
    curves = set()
    for t in faces:
        for d, c in gmsh.model.getBoundary([(2, t)], oriented=False):
            curves.add(abs(c))
    fd = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(fd, "CurvesList", sorted(curves))
    gmsh.model.mesh.field.setNumber(fd, "Sampling", 600)
    ft = gmsh.model.mesh.field.add("Threshold")
    gmsh.model.mesh.field.setNumber(ft, "InField", fd)
    gmsh.model.mesh.field.setNumber(ft, "SizeMin", lc_gap)
    gmsh.model.mesh.field.setNumber(ft, "SizeMax", lc_far)
    gmsh.model.mesh.field.setNumber(ft, "DistMin", 2 * gap)
    gmsh.model.mesh.field.setNumber(ft, "DistMax", 25 * gap)
    gmsh.model.mesh.field.setAsBackgroundMesh(ft)
    for opt in ("MeshSizeExtendFromBoundary", "MeshSizeFromPoints",
                "MeshSizeFromCurvature"):
        gmsh.option.setNumber("Mesh." + opt, 0)

    regions = {}

    def push(cur, dz, n, name, keep_labels=False):
        """Extrude each face individually; return the new top faces in order."""
        tops = []
        for t, lab in zip(cur, labels):
            res = occ.extrude([(2, t)], 0, 0, dz, numElements=[n],
                              recombine=False)
            top = [tt for dd, tt in res if dd == 2][0]
            vol = [tt for dd, tt in res if dd == 3][0]
            tag = lab if keep_labels else name
            regions.setdefault(tag, []).append(vol)
            tops.append(top)
        return tops

    cur = faces
    for name, dz, n in (("ox", -box_h, n_ox), ("si", -si_h, n_si)):
        cur = push(cur, dz, n, name)
    cur = faces
    for name, dz, n, keep in (("ln", ln_h, n_ln, False),
                              ("metal", t_au, n_au, True),
                              ("air", air_h, n_air, False)):
        cur = push(cur, dz, n, name, keep_labels=keep)

    occ.synchronize()
    for name, tl in regions.items():
        if tl:
            gmsh.model.addPhysicalGroup(3, tl, name=name)
    gmsh.model.mesh.generate(3)
    nn = len(gmsh.model.mesh.getNodes()[0])
    _, ets, _ = gmsh.model.mesh.getElements(3)
    nt = sum(len(e) for e in ets)
    gmsh.write(out)
    gmsh.finalize()
    return out, nn, nt


if __name__ == "__main__":
    import time
    for etched in (False, True):
        t = time.time()
        f, nn, nt = build(etched=etched, out=f"l3_{etched}.msh")
        print(f"{'etched' if etched else 'plain':8s} nodes={nn:8d} "
              f"tets={nt:9d} ({time.time()-t:5.1f}s)")
