import json, sys
from bend_fem import run
cases = {
 "base":            dict(),
 "reach17.5":       dict(mesh_opts=dict(SKIN_REACH=17.5)),
 "reach17.5_corner.025": dict(mesh_opts=dict(SKIN_REACH=17.5, CORNER_RES=0.025)),
 "reach17.5_corner.0125": dict(mesh_opts=dict(SKIN_REACH=17.5, CORNER_RES=0.0125)),
 "reach17.5_skin.05": dict(mesh_opts=dict(SKIN_REACH=17.5, SKIN_RES=0.05)),
 "reach17.5_skin.025_corner.0125": dict(mesh_opts=dict(SKIN_REACH=17.5, SKIN_RES=0.025, CORNER_RES=0.0125)),
 "reach17.5_mf0.7": dict(mesh_opts=dict(SKIN_REACH=17.5, MESH_FACTOR=0.7)),
 "reach17.5_mf0.5": dict(mesh_opts=dict(SKIN_REACH=17.5, MESH_FACTOR=0.5)),
 "reach17.5_pad400_air1000": dict(mesh_opts=dict(SKIN_REACH=17.5), geom=dict(lat_pad=400.0, air_h=1000.0)),
}
which = sys.argv[1:] or list(cases)
for k in which:
    r = run(60e9, **cases[k])
    r = {a: float(b) for a, b in r.items()}
    print(json.dumps(dict(case=k, **r)), flush=True)
