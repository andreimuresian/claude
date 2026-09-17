"""Meshing helpers shared by the quasi-static and full-wave solvers."""

import contextlib
import io

from femwell.mesh import mesh_from_OrderedDict
from skfem.io.meshio import from_meshio


def build_mesh(cs, resolution=0.5, default_max=60.0, optical_half=False,
               filename="tfln.msh", quiet=True):
    """Mesh a CrossSection, refining where the fields are concentrated."""
    polys = cs.polygons(optical_half=optical_half)

    resolutions = {
        "signal": {"resolution": 2.0 * resolution, "distance": 5.0},
        "ground_l": {"resolution": 4.0 * resolution, "distance": 5.0},
        "ground_r": {"resolution": 4.0 * resolution, "distance": 5.0},
        "slab": {"resolution": 1.0 * resolution, "distance": 3.0},
        "oxide": {"resolution": 2.0 * resolution, "distance": 5.0},
    }
    for name in polys:
        if name.startswith("rib_"):
            resolutions[name] = {"resolution": 0.05 * resolution, "distance": 1.0}
        elif name.startswith("cap_"):
            resolutions[name] = {"resolution": 0.2 * resolution, "distance": 1.0}

    ctx = contextlib.redirect_stdout(io.StringIO()) if quiet \
        else contextlib.nullcontext()
    with ctx:
        mesh = from_meshio(mesh_from_OrderedDict(
            polys, resolutions, filename=filename,
            default_resolution_max=default_max))
    return mesh


def metal_facets(cs, mesh):
    """Names of the mesh boundaries that bound each electrode."""
    out = {}
    for metal in cs.metal_names():
        out[metal] = [name for name in mesh.boundaries
                      if name.startswith(metal + "___")
                      or name.endswith("___" + metal)]
    return out
