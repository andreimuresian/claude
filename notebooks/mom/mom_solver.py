"""Layered-medium MPIE Method of Moments for the coplanar T-slot line.

Unknowns: RWG surface-current coefficients on the metal footprint (Phase-1
same-interface kernels G_A, G_q; lossy metal via a surface impedance Z_s).
All source/observation points are coplanar, so the 1/rho triangle integrals are
the closed-form edge sums _Ipot / _Ivec (verified to ~1e-13 against quadrature).

STATUS (Phase 2, 2026-09-22)
----------------------------
VALIDATED and kept:
  * assemble()  -- the MPIE matrix.  Reciprocal to 1e-16.  A quasi-static
    capacitance solve built on it reproduces the dataset baseline C to 4-10 %.
  * _Ipot / _Ivec analytic coplanar integrals; singularity extraction with the
    smooth remainder that captures the thin-film transition.
  * Two bugs were found and fixed here and in mesh_generator: gmsh triangles
    are re-wound CCW (they were flipping the sign of the analytic integrals on
    ~half the mesh), and _Ipot floors its log argument (NaN when the field
    point lands on a source vertex).

ABANDONED (finite-line extraction is ill-posed for this validation):
  * series_2port / launch_extract and the S->ABCD->RLGC path below.  The
    N/N+1 lines are electrically short (~0.14 lambda_g) and unterminated, so
    the driven field is a nearly-pure reactive standing wave with almost no
    phase progression -- gamma/Z0 extraction is ill-conditioned.  A clean
    traveling wave needs matched wave ports (a 2D eigenvalue sub-project, out
    of scope), and the zero-thickness planar model cannot match the thick metal
    (MTX up to ~14 um) of the 2D-FEM baseline.  These routines are retained for
    reference only; they do NOT meet the Phase-2 tolerances.  See PROGRESS.md.
"""
import warnings
import numpy as np
from scipy import special
from scipy.interpolate import CubicSpline
import stack_params as sp
from layered_greens import Stack, EPS0, MU0, C0
warnings.filterwarnings("ignore")

_G3 = np.array([[1/6, 1/6], [2/3, 1/6], [1/6, 2/3]])   # 3-pt triangle rule (bary)
_W3 = np.array([1/3, 1/3, 1/3])
_GL, _WL = np.polynomial.legendre.leggauss(16)          # edge line integrals


# ---------- coplanar analytic triangle integrals (verified) ----------------
def _Ipot(p, tri):
    """int_T 1/|p-r'| dA'  (p, tri coplanar)."""
    s = 0.0
    for i in range(3):
        a = tri[i]; b = tri[(i+1) % 3]
        u = b-a; L = np.hypot(u[0], u[1]); uh = u/L
        mh = np.array([uh[1], -uh[0]])
        P0 = (a[0]-p[0])*mh[0] + (a[1]-p[1])*mh[1]
        lm = (a[0]-p[0])*uh[0] + (a[1]-p[1])*uh[1]
        lp = (b[0]-p[0])*uh[0] + (b[1]-p[1])*uh[1]
        Ra = np.hypot(a[0]-p[0], a[1]-p[1]); Rb = np.hypot(b[0]-p[0], b[1]-p[1])
        floor = 1e-13*(Ra+Rb) + 1e-300          # guard roundoff at a vertex
        num = max(Rb+lp, floor); den = max(Ra+lm, floor)
        s += P0*np.log(num/den)
    return s


def _Ivec(p, tri):
    """int_T (r'-p)/|p-r'| dA'  via  boundary R n' dl'."""
    out = np.zeros(2)
    for i in range(3):
        a = tri[i]; b = tri[(i+1) % 3]
        u = b-a; L = np.hypot(u[0], u[1]); uh = u/L
        nout = np.array([uh[1], -uh[0]])
        t = 0.5*(_GL+1)
        qx = a[0]+t*u[0]; qy = a[1]+t*u[1]
        R = np.hypot(qx-p[0], qy-p[1])
        out += nout*(np.sum(_WL*R)*(L/2))
    return out


# ---------- Green's-function table for one geometry ------------------------
class Kernel:
    """G_A(rho), G_q(rho) for a given etched LN thickness, plus the rho->0
    coefficients K_A, K_q used for singularity extraction."""
    def __init__(self, t_LN, f=sp.F0, n=130):
        self.st = Stack(sp.EPS_AIR, sp.device_layers(t_LN=t_LN, lossy=True),
                        sp.EPS_AIR, f=f)
        self.f = f; self.w = 2*np.pi*f
        rho = np.logspace(np.log10(3e-7), np.log10(3e-3), n)
        GA, Gq = self.st.table(rho)
        self.rho = rho; self.lr = np.log(rho)
        self._GAr = CubicSpline(self.lr, GA.real); self._GAi = CubicSpline(self.lr, GA.imag)
        self._Gqr = CubicSpline(self.lr, Gq.real); self._Gqi = CubicSpline(self.lr, Gq.imag)
        self.Kq = self.st._asym("TM")/(2*np.pi)      # G_q -> Kq/rho
        self.KA = self.st._asym("TE")/(2*np.pi)      # G_A -> KA/rho

    def GA(self, rho):
        lr = np.log(np.clip(rho, self.rho[0], self.rho[-1]))
        return self._GAr(lr)+1j*self._GAi(lr)

    def Gq(self, rho):
        lr = np.log(np.clip(rho, self.rho[0], self.rho[-1]))
        return self._Gqr(lr)+1j*self._Gqi(lr)


# ---------- MPIE matrix -----------------------------------------------------
def assemble(rwg, kern, Zs, near_fac=3.0):
    """Dense complex MoM matrix Z (Ne x Ne).

    The mixed-potential EFIE, with G_A and G_q the TRUE potential kernels that
    layered_greens returns (G_A -> mu0/(4 pi R), G_q -> 1/(4 pi eps R)), is

        Z_mn = j w <f_m, Int G_A f_n> + (1/j w) <div f_m, Int G_q div f_n>

    from E_scat = -j w A - grad Phi with A = Int G_A J and Phi = Int G_q rho,
    rho = -div J/(j w).  Both terms are then in ohms, matching Z_s * Gram.
    """
    nodes = rwg["nodes"]; tris = rwg["tris"]
    cent = rwg["cent"]; area = rwg["area"]
    edges = rwg["edges"]; tp = rwg["tp"]; tm = rwg["tm"]
    vp = rwg["vp"]; vm = rwg["vm"]; Le = rwg["L"]
    Ne = len(edges); Nt = len(tris)
    w = kern.w
    jw = 1j*w

    # --- centroid interaction matrices (far), self/near zeroed -------------
    dx = cent[:, 0][:, None]-cent[:, 0][None, :]
    dy = cent[:, 1][:, None]-cent[:, 1][None, :]
    D = np.hypot(dx, dy)
    hh = np.sqrt(area)
    thr = near_fac*(hh[:, None]+hh[None, :])
    near_mask = D <= thr
    Dsafe = np.where(near_mask, 1.0, D)
    GA_cc = kern.GA(Dsafe); Gq_cc = kern.Gq(Dsafe)
    GA_cc[near_mask] = 0.0; Gq_cc[near_mask] = 0.0

    # sparse edge->triangle weight maps
    # charge weight B[t,e] = s * Le ; vector weight Wc[t,e,:] = s*Le/2*(cent_t - v)
    Bp = np.zeros((Nt, Ne)); Wx = np.zeros((Nt, Ne)); Wy = np.zeros((Nt, Ne))
    for e in range(Ne):
        terms = [(tp[e], vp[e], +1.0)]
        if tm[e] >= 0:
            terms.append((tm[e], vm[e], -1.0))
        for (t, vv, s) in terms:
            Bp[t, e] += s*Le[e]
            rc = cent[t]-nodes[vv]
            Wx[t, e] += s*Le[e]/2*rc[0]; Wy[t, e] += s*Le[e]/2*rc[1]

    # far matrix
    Phi = Bp.T @ Gq_cc @ Bp                      # scalar-potential (charge)
    Av = Wx.T @ GA_cc @ Wx + Wy.T @ GA_cc @ Wy   # vector-potential
    Z = jw*Av + (1.0/jw)*Phi

    # --- near / self full accurate value (these pairs were zeroed above) ---
    # SP_full  = Kq * int_Ti int_Tj 1/rho  +  Ai Aj * g_q(rho_eff)   (g = G-K/rho)
    # VP_full  = KA * outer[(r-mv).(Ivec+(r-nv)Ipot)] + Ai Aj (ci-mv).(cj-nv) g_A
    tri_pts = nodes[tris]
    ii, jj = np.where(np.triu(near_mask))
    for i, j in zip(ii, jj):
        Ti = tri_pts[i]; Tj = tri_pts[j]
        Ai = area[i]; Aj = area[j]
        ro = (_G3[:, 0][:, None]*(Ti[1]-Ti[0]) + _G3[:, 1][:, None]*(Ti[2]-Ti[0])
              + Ti[0])                                       # 3 outer pts on Ti
        Ip = np.array([_Ipot(r, Tj) for r in ro])           # inner over Tj
        Iv = np.array([_Ivec(r, Tj) for r in ro])
        SPsing = Ai*np.sum(_W3*Ip)                           # int_Ti int_Tj 1/rho
        reff = max(D[i, j], 0.35*np.sqrt(Ai+Aj))
        gq = kern.Gq(reff) - kern.Kq/reff                    # smooth remainders
        gA = kern.GA(reff) - kern.KA/reff
        SP_full = kern.Kq*SPsing + Ai*Aj*gq                  # scalar (charge) double int
        em = _edges_of(rwg, i); en = _edges_of(rwg, j)
        for (me, mv, ms) in em:
            rmv = ro-nodes[mv]
            cmv = cent[i]-nodes[mv]
            for (ne, nv, ns) in en:
                inner = Iv + (ro-nodes[nv])*Ip[:, None]
                vsing = Ai*np.sum(_W3*np.sum(rmv*inner, axis=1))
                VP_full = kern.KA*vsing + Ai*Aj*np.dot(cmv, cent[j]-nodes[nv])*gA
                addZ = (jw*(ms*Le[me]/(2*Ai))*(ns*Le[ne]/(2*Aj))*VP_full
                        + (1.0/jw)*(ms*Le[me]/Ai)*(ns*Le[ne]/Aj)*SP_full)
                Z[me, ne] += addZ
                if i != j:
                    Z[ne, me] += addZ
    # --- surface impedance (RWG Gram, metal) ------------------------------
    Z += Zs*_gram(rwg)
    return Z


def _edges_of(rwg, t):
    """(edge index, opposite-vertex node, sign) for the (up to 3) RWG edges of
    triangle t."""
    if "_e_of_t" not in rwg:
        eot = {i: [] for i in range(len(rwg["tris"]))}
        for e in range(len(rwg["edges"])):
            eot[rwg["tp"][e]].append((e, rwg["vp"][e], +1.0))
            if rwg["tm"][e] >= 0:
                eot[rwg["tm"][e]].append((e, rwg["vm"][e], -1.0))
        rwg["_e_of_t"] = eot
    return rwg["_e_of_t"][t]


def _gram(rwg):
    """RWG mass matrix  int f_m.f_n dA  (nonzero only for edges sharing a tri)."""
    Ne = len(rwg["edges"]); G = np.zeros((Ne, Ne))
    nodes = rwg["nodes"]; area = rwg["area"]; Le = rwg["L"]
    for t in range(len(rwg["tris"])):
        loc = _edges_of(rwg, t)
        A = area[t]
        v = rwg["tris"][t]
        # 3-pt rule for f_m.f_n on this triangle
        ro = (_G3[:, 0][:, None]*(nodes[v[1]]-nodes[v[0]])
              + _G3[:, 1][:, None]*(nodes[v[2]]-nodes[v[0]]) + nodes[v[0]])
        for (me, mv, ms) in loc:
            fm = ms*Le[me]/(2*A)*(ro-nodes[mv])
            for (ne, nv, ns) in loc:
                fn = ns*Le[ne]/(2*A)*(ro-nodes[nv])
                G[me, ne] += A*np.sum(_W3*np.sum(fm*fn, axis=1))
    return G


# ---------- ports and S-parameter extraction --------------------------------
def cut_edges(rwg, z_plane):
    """Signal-strip RWG edges whose two triangles straddle Z=z_plane, with the
    sign that orients the RWG current to +Z.  A charge-neutral series delta-gap
    on this set is the port (current source in the signal line; grounds return)."""
    reg = rwg["region"]; cent = rwg["cent"]; tp = rwg["tp"]; tm = rwg["tm"]
    out = []
    for e in range(len(rwg["edges"])):
        i, j = tp[e], tm[e]
        if reg[i] != "sig" or reg[j] != "sig":
            continue
        zi, zj = cent[i, 1], cent[j, 1]
        if (zi-z_plane)*(zj-z_plane) < 0:
            out.append((e, 1.0 if zj > zi else -1.0))
    return out


def series_2port(Z, rwg, z0, z1, Z0=50.0):
    """Two series delta-gap ports at signal cuts z0, z1.  Drive each with unit
    EMF (+Z), read the net +Z line current at both cuts -> network G (I=G V);
    S from G referenced to Z0.  Returns (S, Lline=z1-z0, ports)."""
    p0 = cut_edges(rwg, z0); p1 = cut_edges(rwg, z1)
    Ne = Z.shape[0]

    def rhs(pl):
        b = np.zeros(Ne, complex)
        for e, s in pl:
            b[e] = s
        return b

    R = np.column_stack([rhs(p0), rhs(p1)])
    X = np.linalg.solve(Z, R)

    def cur(pl, x):
        return sum(s*x[e] for e, s in pl)

    G = np.array([[cur(p0, X[:, 0]), cur(p0, X[:, 1])],
                  [cur(p1, X[:, 0]), cur(p1, X[:, 1])]])
    Y0 = 1.0/Z0; I2 = np.eye(2)
    S = np.linalg.solve(Y0*I2 + G, Y0*I2 - G)
    return S, (z1-z0), (p0, p1)


def rlcg_from_S(S, Lline, w, Z0=50.0):
    """ABCD from the 2-port S; per-metre L, C and attenuation of the line."""
    S11, S12, S21, S22 = S[0, 0], S[0, 1], S[1, 0], S[1, 1]
    den = 2*S21
    A = ((1+S11)*(1-S22)+S12*S21)/den
    B = Z0*((1+S11)*(1+S22)-S12*S21)/den
    Cc = (1.0/Z0)*((1-S11)*(1-S22)-S12*S21)/den
    gamma = np.arccosh(A)/Lline
    if gamma.real < 0:
        gamma = -gamma
    Z0l = np.sqrt(B/Cc)
    if Z0l.real < 0:
        Z0l = -Z0l
    return dict(gamma=gamma, Z0=Z0l,
                L=(gamma*Z0l).imag/w, C=(gamma/Z0l).imag/w,
                alpha_Np=abs(gamma.real), alpha_dBcm=abs(gamma.real)*8.686/100.0,
                nm=gamma.imag*C0/w)


# ---------- modal extraction (port-independent) -----------------------------
def _sig_current(rwg, x, z):
    """Net +Z signal current crossing plane Z=z."""
    return sum(s*x[e] for e, s in cut_edges(rwg, z))


def _matrix_pencil(y, dz, M=2):
    """Matrix-pencil poles of a sum of M complex exponentials sampled uniformly.
    Returns gamma_i with z_i = exp(-gamma_i dz)."""
    y = np.asarray(y, complex)
    N = len(y); L = N//2
    H = np.array([y[i:i+L+1] for i in range(N-L)])      # Hankel (N-L, L+1)
    Y0, Y1 = H[:, :-1], H[:, 1:]
    U, s, Vh = np.linalg.svd(Y0, full_matrices=False)
    M = min(M, np.sum(s > s[0]*1e-10))
    Us, ss, Vs = U[:, :M], s[:M], Vh[:M, :]
    Amat = np.diag(1/ss) @ Us.conj().T @ Y1 @ Vs.conj().T
    z = np.linalg.eigvals(Amat)
    return -np.log(z)/dz, z


def launch_extract(Z, rwg, kern, nsamp=40, guard=0.22, zl_frac=0.05):
    """Port-independent modal extraction.  Launch a wave with a series delta-gap
    near the input end, sample the signal current I(z) and the signal-to-ground
    voltage V(z) across the guarded interior, get gamma by 2-mode Prony and
    Z0 = V+/I+ from the forward-wave decomposition."""
    Lz = rwg["Lz"]; w = kern.w
    b = np.zeros(Z.shape[0], complex)
    for e, s in cut_edges(rwg, zl_frac*Lz):
        b[e] = s
    x = np.linalg.solve(Z, b)

    zk = np.linspace(guard*Lz, (1-guard)*Lz, nsamp)
    dz = zk[1]-zk[0]
    Iz = np.array([_sig_current(rwg, x, z) for z in zk])

    # triangle charges Q_t = (1/jw) sum_n s_{n,t} L_n I_n
    Le = rwg["L"]; tp = rwg["tp"]; tm = rwg["tm"]
    q = np.zeros(len(rwg["tris"]), complex)
    for e in range(len(rwg["edges"])):
        q[tp[e]] += Le[e]*x[e]
        if tm[e] >= 0:
            q[tm[e]] -= Le[e]*x[e]
    Qt = q/(1j*w)
    cent = rwg["cent"]; yg = _ground_mid(rwg)

    def phi(y, z):
        d = np.maximum(np.hypot(cent[:, 0]-y, cent[:, 1]-z), 1e-7)
        return np.sum(Qt*kern.Gq(d))
    Vz = np.array([phi(0.0, z)-phi(yg, z) for z in zk])

    # matrix-pencil (robust for the forward+reflected standing wave)
    K = len(Iz)
    gam, roots = _matrix_pencil(Iz, dz, M=2)
    # physical forward mode: Re(gamma)>0 with the smaller |gamma| (propagating,
    # not evanescent); ensure Im(gamma)=beta>0
    order = np.argsort(np.abs(gam.real))            # propagating first
    gamma = gam[order[0]]
    if gamma.real < 0:
        gamma = -gamma
    if gamma.imag < 0:
        gamma = gamma.real - 1j*gamma.imag

    kk = np.arange(K)
    Bmat = np.column_stack([np.exp(-gamma*dz)**kk, np.exp(+gamma*dz)**kk])
    Ipm = np.linalg.lstsq(Bmat, Iz, rcond=None)[0]
    Vpm = np.linalg.lstsq(Bmat, Vz, rcond=None)[0]
    Z0 = Vpm[0]/Ipm[0]
    if Z0.real < 0:
        Z0 = -Z0
    return dict(gamma=gamma, Z0=Z0, nm=gamma.imag*C0/w,
                L=(gamma*Z0).imag/w, C=(gamma/Z0).imag/w,
                alpha_dBcm=abs(gamma.real)*8.686/100.0,
                Iz=Iz, Vz=Vz, zk=zk, roots=roots)


def _ground_mid(rwg):
    g = rwg.get("geom")
    if g is not None:
        return g["WS"]/2 + g["GAP"] + g["WG"]/2
    c = rwg["cent"]; m = rwg["region"] == "gR"
    return float(np.mean(c[m, 0])) if m.any() else 0.0
