"""Periodic 3D MoM cell of the tee-loaded line (mom_cell, general geometry).

Same formulation as cell3d.PlainCell (Floquet harmonics of the 2D layered kernel), for a
cross-section that changes along z.  This file: the surface mesh and the basis functions.

Half structure x >= 0 (the CPW mode is even: J_x odd, J_y, J_z, charge even); x = 0 is the
symmetry plane, no faces there.  The metal is voxelised on a global tensor grid (x, y, z);
every face between a metal and a non-metal voxel is a rectangle:
  S face: normal x or y -> a cross-section segment (grid edge) x a z cell,
  E face: normal z      -> a cross-section cell (x-y rectangle) at a z plane (slot end walls).
One rooftop basis per edge shared by two faces (current flows from face 1 across the edge
into face 2, normal flux 1 A/m at the edge, linear in each face).  Each basis is a sum of
pieces  coef * (cross-section piece) * (z function):
  cross-section pieces: segment start ramp (1-u), end ramp (u) [current along the segment],
      segment constant [J_z, or charge]; cell ramps x-up/x-down [J_x], y-up/y-down [J_y],
      cell constant [charge];
  z functions: pulse, ramp up, ramp down on a z cell; delta at a z plane.
The divergence (charge, times -j w) is carried as separate pieces with constant
cross-section weight; the bases are continuous, so there are no edge line charges.
"""
import numpy as np


def grade(L, h0, h1, hmax, growth=1.3):
    """Breakpoints on [0, L]: step h0 at 0, h1 at L, growing by `growth` up to hmax.
    Steps are laid from both ends, always the smaller next step first (so a fine end is graded
    even when the other end is coarse); the remainder becomes whole middle steps and all steps
    are then rescaled together to fill L exactly (no sliver cells)."""
    a, b = [], []
    ha, hb = min(h0, hmax), min(h1, hmax)
    while True:
        if ha <= hb:
            if sum(a) + sum(b) + ha > L*(1 + 1e-9):
                break
            a.append(ha); ha = min(ha*growth, hmax)
        else:
            if sum(a) + sum(b) + hb > L*(1 + 1e-9):
                break
            b.append(hb); hb = min(hb*growth, hmax)
    if not a and not b:
        return np.array([0.0, L])
    steps = a + b[::-1]
    rem = L - sum(steps)
    hm = min(max(steps)*growth, hmax)                   # size of a middle step
    m = int(np.floor(rem/hm + 0.5))
    if m == 0 and rem > 0.5*min(ha, hb):                # most of one more step: add it
        m, hm = 1, rem
    while True:
        steps = np.array(a + [hm]*m + b[::-1])
        if steps.max()*L/steps.sum() <= hmax*(1 + 1e-9):
            break
        m += 1
    pts = np.r_[0, np.cumsum(steps*L/steps.sum())]
    pts[-1] = L
    return pts


def lines(breaks, hmin, hmax, coarse=(), growth=1.3):
    """Grid lines through all breaks, step hmin at every break except those in `coarse`."""
    br = np.unique(np.round(np.asarray(breaks, float), 12))
    out = [br[0]]
    for a, b in zip(br[:-1], br[1:]):
        h0 = hmax if any(abs(a - c) < 1e-12 for c in coarse) else hmin
        h1 = hmax if any(abs(b - c) < 1e-12 for c in coarse) else hmin
        out.extend(a + grade(b - a, min(h0, b - a), min(h1, b - a), hmax, growth)[1:])
    return np.array(out)


class Cell:
    """g: dict WS, GAP, MTX, W1, W2, L1, L2 (m).  Tee centred at z = P/2."""

    def __init__(self, g, hmin=0.4e-6, hmax=8e-6, hz_min=1e-6, hz_max=20e-6, P=200e-6, WG=70e-6,
                 growth=1.3, shift=False):
        """shift: tee centred at z = 0 instead of P/2 (the same periodic line seen from another
        cell origin: n and alpha must not change; a check of the cell-boundary handling)."""
        self.P = P
        WS, GAP, t = g["WS"], g["GAP"], g["MTX"]
        x_si, x_gi = WS/2, WS/2 + GAP
        x_go = x_gi + WG
        xb1, xb2 = min(x_gi + g["W1"], x_go), min(x_gi + g["W1"] + g["W2"], x_go)
        self.xs = dict(x_si=x_si, x_gi=x_gi, x_go=x_go, xb1=xb1, xb2=xb2)
        xbr = [0.0, x_si, x_gi, x_go] + [v for v in (xb1, xb2) if x_gi < v < x_go]
        self.X = lines(xbr, hmin, hmax, coarse=(0.0,), growth=growth)
        self.Y = lines([0.0, t], hmin, hmax, growth=growth)
        zc = 0.0 if shift else P/2
        far = P/2 if shift else 0.0                                       # midway between tees
        has = any(0 < v < P for v in (g["L1"], g["L2"]))
        ends = [v/2 if shift else zc - v/2 for v in (g["L1"], g["L2"]) if 0 < v < P]
        zh = lines([0.0, P/2] + ends, hz_min, hz_max, coarse=(far,) + (() if has else (zc,)), growth=growth)
        self.Zg = np.r_[zh, P - zh[-2::-1]]                                 # symmetric about z = P/2
        xm = 0.5*(self.X[1:] + self.X[:-1])
        zm = 0.5*(self.Zg[1:] + self.Zg[:-1]) - zc
        zm = (zm + P/2) % P - P/2                                           # distance to the tee centre
        sig = xm < x_si
        gnd = (xm > x_gi) & (xm < x_go)
        slot = (((xm[:, None] > x_gi) & (xm[:, None] < xb1) & (np.abs(zm)[None, :] < g["L1"]/2))
                | ((xm[:, None] > xb1) & (xm[:, None] < xb2) & (np.abs(zm)[None, :] < g["L2"]/2)))
        mx = (sig | gnd)[:, None] & ~slot                                  # (nx, nz)
        self.metal = np.repeat(mx[:, None, :], len(self.Y) - 1, axis=1)   # (nx, ny, nz), full thickness
        self.owner_x = np.where(sig, 0, 1)                                # 0 signal, 1 ground (per x cell)
        self._faces()
        self._bases()

    # ---------------------------------------------------------------- faces
    def _faces(self):
        m = self.metal
        nx, ny, nz = m.shape
        F = []          # (kind, i, j, k, ...)  kind 'x': x-normal at plane i, y cell j, z cell k
        # x-normal planes 1..nx (plane 0 = symmetry plane, no face)
        for i in range(1, nx + 1):
            a = m[i - 1]; b = m[i] if i < nx else np.zeros_like(a)
            for j, k in zip(*np.nonzero(a != b)):
                F.append(("x", i, j, k))
        for j in range(0, ny + 1):
            a = m[:, j - 1] if j > 0 else np.zeros((nx, nz), bool)
            b = m[:, j] if j < ny else np.zeros((nx, nz), bool)
            for i, k in zip(*np.nonzero(a != b)):
                F.append(("y", i, j, k))
        for k in range(nz):
            a = m[:, :, k - 1]; b = m[:, :, k]                             # k-1 = -1 wraps (periodic)
            for i, j in zip(*np.nonzero(a != b)):
                F.append(("z", i, j, k))
        self.faces = F

    # ---------------------------------------------------------------- bases
    def _bases(self):
        X, Y, Zg, P = self.X, self.Y, self.Zg, self.P
        nz = len(Zg) - 1
        # cross-section elements: segments (grid edges) and cells
        self.seg_id, self.segs = {}, []        # key ('x', i, j): x-directed edge from (X[i],Y[j]) to (X[i+1],Y[j])
        self.cell_id, self.cells = {}, []      # key (i, j)

        def seg(key):
            if key not in self.seg_id:
                d, i, j = key
                p0 = (X[i], Y[j]); p1 = (X[i + 1], Y[j]) if d == "x" else (X[i], Y[j + 1])
                self.seg_id[key] = len(self.segs); self.segs.append((d, p0, p1, i, j))
            return self.seg_id[key]

        def cell(key):
            if key not in self.cell_id:
                i, j = key
                self.cell_id[key] = len(self.cells); self.cells.append((X[i], X[i + 1], Y[j], Y[j + 1], i, j))
            return self.cell_id[key]

        # pieces: (kind 's'|'c', elem, wtype, comp) ; z functions: (type, a, b)
        self.piece_id, self.pieces = {}, []
        self.zf_id, self.zfs = {}, []

        def piece(kind, elem, w, comp):
            key = (kind, elem, w, comp)
            if key not in self.piece_id:
                self.piece_id[key] = len(self.pieces); self.pieces.append(key)
            return self.piece_id[key]

        def zf(typ, a, b):
            key = (typ, round(a, 15), round(b, 15))
            if key not in self.zf_id:
                self.zf_id[key] = len(self.zfs); self.zfs.append((typ, a, b))
            return self.zf_id[key]

        edges = {}

        def add(key, item):
            edges.setdefault(key, []).append(item)

        self.face_elem = []
        for fi, (kind, i, j, k) in enumerate(self.faces):
            za, zb = Zg[k], Zg[k + 1]
            if kind in ("x", "y"):
                s = seg(("y", i, j) if kind == "x" else ("x", i, j))
                self.face_elem.append(("s", s))
                d = "y" if kind == "x" else "x"                          # segment direction = current comp for J_t
                # z-directed edges at the segment end points: J_t pieces x pulse on [za, zb]
                n0 = (i, j); n1 = (i, j + 1) if kind == "x" else (i + 1, j)
                add(("zl", n0, k), (fi, "t", s, "s", d, za, zb))
                add(("zl", n1, k), (fi, "t", s, "e", d, za, zb))
                # transverse edges at planes k (z = za) and k+1 (z = zb)
                add(("tp", ("y", i, j) if kind == "x" else ("x", i, j), k), (fi, "zlo", s, za, zb))
                kk = (k + 1) % nz
                add(("tp", ("y", i, j) if kind == "x" else ("x", i, j), kk), (fi, "zhi", s, za, zb))
            else:
                c = cell((i, j)); z0 = Zg[k]
                self.face_elem.append(("c", c))
                add(("tp", ("x", i, j), k), (fi, "E", c, "y", "lo", z0))       # edge at y = Y[j]
                add(("tp", ("x", i, j + 1), k), (fi, "E", c, "y", "hi", z0))
                add(("tp", ("y", i, j), k), (fi, "E", c, "x", "lo", z0))
                add(("tp", ("y", i + 1, j), k), (fi, "E", c, "x", "hi", z0))
        bad = {k: v for k, v in edges.items() if len(v) not in (1, 2)}
        if bad:
            raise ValueError(f"{len(bad)} non-manifold edges, e.g. {next(iter(bad.items()))}")
        self.open_edges = [k for k, v in edges.items() if len(v) == 1]

        self.bkey = []
        B = []            # basis: list of (piece, zf, coef) for currents
        Q = []            # basis: list of (piece, zf, coef) for the divergence
        self.btype = []
        for key, items in edges.items():
            if len(items) != 2:
                continue
            cur, div = [], []
            for side, it in zip((+1, -1), items):        # side +1: current flows toward the edge
                if it[1] == "t":
                    _, _, s, end, d, za, zb = it
                    L = abs((self.segs[s][2][0] - self.segs[s][1][0]) + (self.segs[s][2][1] - self.segs[s][1][1]))
                    # toward the edge at p0 means -t (t = +d); weight (1-u) at p0, u at p1
                    sgn = (-side if end == "s" else side)
                    cur.append((piece("s", s, end, d), zf("p", za, zb), sgn))
                    # div of w*sgn*t along s: d/ds (1-u) = -1/L, d/ds u = +1/L
                    div.append((piece("s", s, "c", "q"), zf("p", za, zb), sgn*(-1 if end == "s" else 1)/L))
                elif it[1] in ("zlo", "zhi"):
                    _, which, s, za, zb = it
                    h = zb - za
                    if which == "zlo":   # edge at za: weight (zb-z)/h; toward edge = -z
                        sgn = -side
                        cur.append((piece("s", s, "c", "z"), zf("d", za, zb), sgn))
                        div.append((piece("s", s, "c", "q"), zf("p", za, zb), -sgn/h))
                    else:                # edge at zb: weight (z-za)/h; toward edge = +z
                        sgn = side
                        cur.append((piece("s", s, "c", "z"), zf("u", za, zb), sgn))
                        div.append((piece("s", s, "c", "q"), zf("p", za, zb), sgn/h))
                else:
                    _, _, c, comp, lohi, z0 = it
                    xa, xb, ya, yb = self.cells[c][:4]
                    w = (xb - xa) if comp == "x" else (yb - ya)
                    if lohi == "lo":     # edge at the low side: weight (hi - v)/w, toward edge = -comp
                        sgn = -side
                        cur.append((piece("c", c, comp + "d", comp), zf("D", z0, z0), sgn))
                        div.append((piece("c", c, "c", "q"), zf("D", z0, z0), -sgn/w))
                    else:
                        sgn = side
                        cur.append((piece("c", c, comp + "u", comp), zf("D", z0, z0), sgn))
                        div.append((piece("c", c, "c", "q"), zf("D", z0, z0), sgn/w))
            # periodic wrap: an edge at plane 0 shared with a face in the last z cell -> the
            # pieces on the first cells are shifted by +P (Bloch extension, see cell3d)
            if key[0] == "tp" and key[2] == 0:
                cur, div = self._unwrap(cur), self._unwrap(div)
            B.append(cur); Q.append(div); self.bkey.append(key)
            self.btype.append(key[0] if key[0] == "zl" else ("tE" if any(self.pieces[p][0] == "c" for p, _, _ in cur) else "tz"))
        self.B, self.Q = B, Q
        self.N = len(B)

    def _unwrap(self, lst):
        """Shift pieces lying at the start of the period by +P when the basis also has a piece
        at the end of the period (edge at z = 0 = P)."""
        P = self.P
        has_end = any(self.zfs[f][2] > P - 1e-15 and self.zfs[f][0] != "D" for _, f, _ in lst)
        if not has_end:
            return lst
        out = []
        for p, f, c in lst:
            typ, a, b = self.zfs[f]
            if typ == "D" and abs(a) < 1e-15:
                a = b = P
            elif typ != "D" and a < 1e-15:
                a, b = a + P, b + P
            key = (typ, round(a, 15), round(b, 15))
            if key not in self.zf_id:
                self.zf_id[key] = len(self.zfs); self.zfs.append((typ, a, b))
            out.append((p, self.zf_id[key], c))
        return out

    # ---------------------------------------------------------------- checks
    def check(self):
        """Every basis carries zero net charge; returns max |sum div * area * z-extent|."""
        worst = 0.0
        for div in self.Q:
            tot = 0.0
            for p, f, c in div:
                kind, e = self.pieces[p][:2]
                typ, a, b = self.zfs[f]
                if kind == "s":
                    d, p0, p1 = self.segs[e][:3]
                    meas = abs(p1[0] - p0[0]) + abs(p1[1] - p0[1])
                else:
                    xa, xb, ya, yb = self.cells[e][:4]
                    meas = (xb - xa)*(yb - ya)
                zl = 1.0 if typ == "D" else (b - a)
                tot += c*meas*zl
            worst = max(worst, abs(tot))
        return worst
