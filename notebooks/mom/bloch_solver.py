"""Periodic (Floquet) MPIE assembly and Bloch-eigenvalue extraction.

One unit cell of the T-slot line, periodic along v with period P.  The unknowns
are the RWG coefficients in the cell (mesh_generator.rwg_basis_cell); edges on
the v = 0 / v = P boundary are single wrapped basis functions whose minus half
lives one period up (shift = 1).

Because the periodic kernel is quasi-periodic,
        G_p(du, dv + kP) = exp(j beta k P) G_p(du, dv),
a half that sits one period up can be kept at its in-cell position provided its
interaction is multiplied by exp(j beta sigma P).  That phase is folded into the
basis weights: the row side carries exp(+j beta sigma P) and the column side
exp(-j beta sigma P), so Z = A^T G Bc.  Z(beta) is not symmetric for beta != 0
(reciprocity is Z(beta)^T = Z(-beta)).

The kernel is Ewald-split (floquet_greens.FloquetKernel):
  * sharp part -- real-space lattice sum over a few images; the m = 0 term
    carries the 1/rho singularity and is integrated with the Phase-2 analytic
    coplanar triangle integrals (reused verbatim from mom_solver).
  * soft part  -- smooth, evaluated at centroids for every pair.

A Bloch mode is a beta with Z(beta) singular; we root-find on
    g(beta) = 1 / (x^H Z(beta)^{-1} y)
which is zero exactly at the eigenvalues, using one LU solve per evaluation.
"""
import numpy as np
from scipy import sparse
from mom_solver import _Ipot, _Ivec, _G3, _W3, _edges_of, _gram

# Degree-5 symmetric 7-point triangle rule, for the OUTER integration of the
# singular 1/rho double integral.  The local-asymptote re-split multiplies
# SPsing by K_loc ~ 4.8 x the old Kq, so whatever error the outer rule makes is
# amplified by the same factor -- and int_Ti int_Tj 1/rho has a log singularity
# in the outer variable, which a 3-point rule resolves poorly.  Measured effect
# of leaving it at 3 points: absolute C degraded from 2.9 % to 12.9 %.
_s15 = np.sqrt(15.0)
_G7 = np.array([[1/3, 1/3],
                [(6+_s15)/21, (6+_s15)/21], [(9-2*_s15)/21, (6+_s15)/21],
                [(6+_s15)/21, (9-2*_s15)/21],
                [(6-_s15)/21, (6-_s15)/21], [(9+2*_s15)/21, (6-_s15)/21],
                [(6-_s15)/21, (9+2*_s15)/21]])
# KNOWN LIMITATION -- READ BEFORE TRUSTING C OR dC FROM THIS SOLVER.
#
# _RFLOOR floors the quadrature distances in the near-field remainder.  It is
# NOT a harmless safeguard: it influences the answer.  Measured on row 118 at
# h = 9 um, varying only this number:
#
#     floor      C_u error     n_m
#     0.300        -7.5 %     2.1195
#     0.150       -11.2 %     2.1020
#     0.050       -12.7 %     2.1329
#     0.015       +60.3 %     3.0677     <- diverges
#
# Cause: the remainder  g = G_sharp(rho) - K_loc/rho  STILL carries a 1/rho
# singularity.  A single constant can only cancel it at one distance (reff);
# everywhere else the 1/rho survives with a different coefficient.  A
# fixed-order Gauss rule cannot integrate 1/rho, so it diverges as sample
# points approach coincidence and is floor-dependent otherwise.
#
# Consequence: beta (hence n_m) is robust to this -- it moves 1.5 % over the
# floor range 0.30-0.05 while C moves 5 points, and its agreement with the
# independent 2D finite-volume solve (0.4-0.7 %) holds throughout.  C and dC
# from this solver are NOT trustworthy at better than 5-10 %.  The hybrid takes
# the baseline C from cpw_2d_static instead, which is why this has not blocked
# the deliverable.
#
# Proper fix, not done: the layered static kernel is an exact image series
# sum_n a_n / sqrt(rho^2 + (2 n t)^2); each term's double integral over
# coplanar triangles has a semi-analytic form, which removes the singularity at
# EVERY rho rather than at one.  That is the prerequisite for a trustworthy dC.
#
# That test has now been done, and it settles the question: the pre-change code
# was LUCKY, and this scheme is roughly an order of magnitude more robust, not
# less.  Sweeping the old single-point distance reff = max(D, _RCO sqrt(Ai+Aj))
# on the same row:
#
#     _RCO       C error       n_m
#     0.15        -23.5 %     1.9684
#     0.25         -8.5 %     2.1508
#     0.35 (ship)  +3.1 %     2.2808
#     0.50        +22.1 %     2.4818
#     0.70         -6.2 %     2.1496
#
# i.e. a 45-point C range and a 26 % n_m range, with the shipped 0.35 sitting on
# the single best C value in the sweep.  Against that, this scheme spans 5 points
# in C and 1.5 % in n_m.  So this change REDUCED a pre-existing parameter
# dependence; it did not introduce one, and reverting is not a sound option.
#
# Two corollaries.  The old code's n_m = 2.2808 was itself a floor artifact --
# the same code gives 2.1508 and 2.1496 at _RCO = 0.25 and 0.70, near this
# scheme's 2.0971 and near the independent 2D value 2.0821.  And the reported
# "dC went 67.7 % -> 73.1 %" was a comparison between two arbitrary parameter
# points, not a regression.
_RFLOOR = 0.15
_W7 = np.array([9/40,
                (155-_s15)/1200, (155-_s15)/1200, (155-_s15)/1200,
                (155+_s15)/1200, (155+_s15)/1200, (155+_s15)/1200])
from layered_greens import EPS0, MU0, C0


def _static_blocks(cell, fk, near_fac, n_sharp):
    """Everything in the near/self block that does NOT depend on beta.

    The analytic coplanar integrals (_Ipot/_Ivec), the areas, the edge weights
    and the sharp radial remainders are all pure geometry + kernel, so they are
    built once per (cell, kernel) and reused for every Bloch iterate.  Only the
    wrapped-edge phase varies, and it enters as exp(j beta P)^d with
    d = sigma_m - sigma_n in {-1, 0, +1}; hence three sparse matrices.

    This is the whole cost of an assembly -- with near_fac = 3 each triangle has
    ~260 near partners, so the Python pair loop is ~50 s.  Caching it takes a
    repeat assembly to a few seconds, which is what makes a secant search (and
    gate V3.7) affordable."""
    c = cell.get("_asm_cache")
    # _RFLOOR MUST be in the key: it changes the blocks this function builds,
    # and a sweep over it silently reused the first value's cache until the
    # driver popped _asm_cache by hand.  That trap is closed here.
    key = (id(fk), near_fac, n_sharp, _RFLOOR)
    if c is not None and c["key"] == key:
        return c
    nodes = cell["nodes"]; tris = cell["tris"]
    cent = cell["cent"]; area = cell["area"]
    Le = cell["L"]; sh_p = cell["shift_p"]; sh_m = cell["shift_m"]
    Ne = len(Le); Nt = len(tris)
    w = fk.w; jw = 1j*w

    du = cent[:, 0][:, None] - cent[:, 0][None, :]
    dv = cent[:, 1][:, None] - cent[:, 1][None, :]
    D = np.hypot(du, dv)
    hh = np.sqrt(area)
    near = D <= near_fac*(hh[:, None] + hh[None, :])

    tri_pts = nodes[tris]
    ii, jj = np.where(np.triu(near))
    rows = []; cols = []; vals = []; dsh = []
    Gpot_near = sparse.lil_matrix((Nt, Nt), dtype=complex)
    for i, j in zip(ii, jj):
        Ti = tri_pts[i]; Tj = tri_pts[j]
        Ai = area[i]; Aj = area[j]
        ro = (_G7[:, 0][:, None]*(Ti[1]-Ti[0]) + _G7[:, 1][:, None]*(Ti[2]-Ti[0])
              + Ti[0])
        Ip = np.array([_Ipot(r, Tj) for r in ro])
        Iv = np.array([_Ivec(r, Tj) for r in ro])
        SPsing = Ai*np.sum(_W7*Ip)

        # ---- near-field remainder: LOCAL asymptote + double quadrature ----
        # Phase 3 extracted the rho -> 0 constant Kq = 1/(2 pi eps0 (eps_air +
        # eps_LN)) analytically and evaluated the whole remainder at ONE
        # effective distance.  Both halves of that are wrong in a layered
        # stack.  Kq is the correct 1/rho constant only for rho << t_LN, and
        # t_LN is 0.13-0.36 um against a mesh of 9-13 um: over the range where
        # near pairs actually sit, the true local constant rho*G(rho) is 2.4 to
        # 5.0 times Kq, so the analytic integration removes less than a quarter
        # of the singularity and the leftover KEEPS a 1/rho that a one-point
        # evaluation cannot integrate.  Measured on row 118, the remainder
        # g_q varies 76x across a single triangle and changes sign.
        #
        # This is also why the homogeneous-air case converges under refinement
        # and the layered case does not (0.0016 vs 0.0576 for h = 13 -> 9 um):
        # in one medium Kq is exact at EVERY rho, so nothing is left over.
        #
        # Fix: re-split with the local constant K_loc = rho_c G(rho_c) at the
        # pair's own distance -- an exact splitting, since the same K_loc is
        # integrated analytically and subtracted inside the quadrature -- and
        # integrate what remains over BOTH triangles instead of sampling it at
        # a point.  Only the conditioning changes, never the operator.
        # G_A needs none of this (it varies 1.2x over the same range) but gets
        # the same treatment for consistency.
        rj = (_G7[:, 0][:, None]*(Tj[1]-Tj[0]) + _G7[:, 1][:, None]*(Tj[2]-Tj[0])
              + Tj[0])
        Rpq = np.maximum(np.hypot(ro[:, None, 0] - rj[None, :, 0],
                                  ro[:, None, 1] - rj[None, :, 1]),
                         _RFLOOR*np.sqrt(Ai + Aj))
        Wpq = _W7[:, None]*_W7[None, :]
        reff = max(D[i, j], 0.35*np.sqrt(Ai+Aj))
        Kq_l = reff*complex(fk.Gq_sharp(reff))        # local 1/rho constants
        KA_l = reff*complex(fk.GA_sharp(reff))
        gq_pq = fk.Gq_sharp(Rpq) - Kq_l/Rpq
        gA_pq = fk.GA_sharp(Rpq) - KA_l/Rpq
        SP = Kq_l*SPsing + Ai*Aj*np.sum(Wpq*gq_pq)
        Gpot_near[i, j] = SP/(Ai*Aj)
        Gpot_near[j, i] = SP/(Ai*Aj)
        em = _edges_of(cell, i); en = _edges_of(cell, j)
        for (me, mv, ms) in em:
            rmv = ro - nodes[mv]
            sm = sh_p[me] if ms > 0 else sh_m[me]
            for (ne, nv, ns) in en:
                sn = sh_p[ne] if ns > 0 else sh_m[ne]
                inner = Iv + (ro-nodes[nv])*Ip[:, None]
                vs = Ai*np.sum(_W7*np.sum(rmv*inner, axis=1))
                # (r_p - v_m).(r'_q - v_n) weighted by the remainder, over both
                # triangles, in place of the centroid-only product
                dot_pq = np.einsum("pd,qd->pq", rmv, rj - nodes[nv])
                VP = KA_l*vs + Ai*Aj*np.sum(Wpq*dot_pq*gA_pq)
                base = (jw*(ms*Le[me]/(2*Ai))*(ns*Le[ne]/(2*Aj))*VP
                        + (1.0/jw)*(ms*Le[me]/Ai)*(ns*Le[ne]/Aj)*SP)
                rows.append(me); cols.append(ne); vals.append(base); dsh.append(sm-sn)
                if i != j:
                    rows.append(ne); cols.append(me); vals.append(base); dsh.append(sn-sm)
    rows = np.asarray(rows); cols = np.asarray(cols)
    vals = np.asarray(vals, complex); dsh = np.asarray(dsh)
    S = {}
    for d in (-1, 0, 1):
        k = dsh == d
        S[d] = sparse.coo_matrix((vals[k], (rows[k], cols[k])),
                                 shape=(Ne, Ne)).tocsr()
    c = dict(key=key, du=du, dv=dv, near=near, S=S,
             Gpot_near=Gpot_near.tocsr(), gram=_gram(cell))
    cell["_asm_cache"] = c
    return c


def assemble_periodic(cell, fk, Zs, beta, near_fac=3.0, n_sharp=None,
                      want_pot=False):
    """Dense complex Floquet MoM matrix Z(beta) for one unit cell.

    The mixed-potential EFIE, with G_A and G_q the TRUE potential kernels that
    layered_greens returns (G_A -> mu0/(4 pi R), G_q -> 1/(4 pi eps R)), is

        Z_mn = j w <f_m, Int G_A f_n> + (1/j w) <div f_m, Int G_q div f_n>

    from E_scat = -j w A - grad Phi with A = Int G_A J and Phi = Int G_q rho,
    rho = -div J/(j w).  Both terms are then in ohms, matching Z_s * Gram.
    """
    nodes = cell["nodes"]; tris = cell["tris"]
    cent = cell["cent"]; area = cell["area"]
    tp = cell["tp"]; tm = cell["tm"]; vp = cell["vp"]; vm = cell["vm"]
    Le = cell["L"]; sh_p = cell["shift_p"]; sh_m = cell["shift_m"]
    P = cell["Lz"]
    Ne = len(Le); Nt = len(tris)
    if n_sharp is None:
        n_sharp = fk.n_sharp
    jw = 1j*fk.w
    fk.set_beta(beta)
    ca = _static_blocks(cell, fk, near_fac, n_sharp)
    du = ca["du"]; dv = ca["dv"]; near = ca["near"]

    # sharp lattice sum at centroids (near/self zeroed: done analytically)
    GqS = np.zeros((Nt, Nt), complex)
    GaS = np.zeros((Nt, Nt), complex)
    for m in range(-n_sharp, n_sharp+1):
        R = np.hypot(du, dv - m*P)
        if m == 0:
            R = np.where(near, 1.0, R)
        ph = np.exp(1j*beta*m*P)
        gq = fk.Gq_sharp(R)*ph
        ga = fk.GA_sharp(R)*ph
        if m == 0:
            gq[near] = 0.0; ga[near] = 0.0
        GqS += gq; GaS += ga
    # soft part: smooth everywhere, centroid is fine
    gqs, gas = fk.soft_p(du.ravel(), dv.ravel())
    GqS += gqs.reshape(Nt, Nt)
    GaS += gas.reshape(Nt, Nt)

    # ---- basis weights with the Bloch phase ------------------------------
    eP = np.exp(1j*beta*P)
    A_b = np.zeros((Nt, Ne), complex); C_b = np.zeros((Nt, Ne), complex)
    A_x = np.zeros((Nt, Ne), complex); C_x = np.zeros((Nt, Ne), complex)
    A_y = np.zeros((Nt, Ne), complex); C_y = np.zeros((Nt, Ne), complex)
    for e in range(Ne):
        for (t, vv, s, sg) in ((tp[e], vp[e], +1.0, sh_p[e]),
                               (tm[e], vm[e], -1.0, sh_m[e])):
            pr = eP**sg
            rc = cent[t] - nodes[vv]
            A_b[t, e] += s*Le[e]*pr;      C_b[t, e] += s*Le[e]/pr
            A_x[t, e] += s*Le[e]/2*rc[0]*pr; C_x[t, e] += s*Le[e]/2*rc[0]/pr
            A_y[t, e] += s*Le[e]/2*rc[1]*pr; C_y[t, e] += s*Le[e]/2*rc[1]/pr

    Phi = A_b.T @ GqS @ C_b
    Av = A_x.T @ GaS @ C_x + A_y.T @ GaS @ C_y
    Z = jw*Av + (1.0/jw)*Phi

    # ---- cached near / self block, with only the wrap phase applied -------
    S = ca["S"]
    Z += (S[0] + eP*S[1] + S[-1]/eP).toarray()
    Z += Zs*ca["gram"]
    if want_pot:
        return Z, C_b, GqS + ca["Gpot_near"].toarray()
    return Z


# ---------------------------------------------------------------- eigenvalue
def tl_test_vector(cell):
    """A transmission-line-shaped test vector: v-directed current on the signal
    conductor, returning on the grounds.

    A RANDOM vector does not work.  The EFIE has a large loop (divergence-free)
    near-null space whose singular values are O(w) and almost independent of
    beta -- with sigma_Si = 2.5e-4 it pins sigma_min at ~4.7e-11 flat from
    n = 0.5 to n = 232, so both sigma_min and a random-vector 1/(x^H Z^-1 y)
    are blind to the transmission-line mode.  Projecting onto a charge-carrying,
    v-directed current exposes it."""
    cent = cell["cent"]; tp = cell["tp"]; tm = cell["tm"]
    dv = cent[tp][:, 1] - cent[tm][:, 1]
    du = cent[tp][:, 0] - cent[tm][:, 0]
    dirv = dv/np.maximum(np.hypot(du, dv), 1e-30)
    sgn = np.where(cell["region"][tp] == "sig", 1.0, -1.0)
    return dirv*sgn*cell["L"]


def bloch_mode(cell, fk, Zs, beta0, tol=1e-7, maxit=25, y=None, **kw):
    """Complex Bloch wavenumber near beta0 with Z(beta) singular.

    g(beta) = 1/(y^T Z^-1 y) is analytic with zeros at the eigenvalues; a
    secant drives it to zero, one LU per step.  beta0 should be complex: the
    CPW mode here sits BELOW the TM0 (n = 3.31) and TE0 (n = 2.54) surface-wave
    indices, so low Floquet harmonics are open radiation channels and the mode
    is leaky -- its wavenumber has a real negative imaginary part and there is
    no root on the real axis to find."""
    if y is None:
        y = tl_test_vector(cell)

    def g(b):
        Z = assemble_periodic(cell, fk, Zs, b, **kw)
        return 1.0/(y @ np.linalg.solve(Z, y))

    b0 = complex(beta0)
    b1 = b0*(1 + 3e-3)
    g0, g1 = g(b0), g(b1)
    hist = [(b0, g0), (b1, g1)]
    best = (abs(g1), b1)
    for _ in range(maxit):
        if abs(g1 - g0) < 1e-300:
            break
        b2 = b1 - g1*(b1 - b0)/(g1 - g0)
        if not np.isfinite(b2):
            break
        # keep the search inside the physical window: a leaky CPW mode has
        # 1 < Re(n) < n_sw and modest loss, so reject wild secant excursions
        n2 = b2/fk.k0
        if not (0.5 < n2.real < 6.0 and -1.0 < n2.imag <= 1e-6):
            b2 = b1 + 0.3*(b2 - b1)/abs(b2 - b1)*abs(b1)*0.05
        g2 = g(b2)
        hist.append((b2, g2))
        if abs(g2) < best[0]:
            best = (abs(g2), b2)
        if abs(b2 - b1) < tol*abs(b2):
            b1, g1 = b2, g2
            break
        b0, g0, b1, g1 = b1, g1, b2, g2
    return best[1], hist


def mode_quantities(beta, P, f):
    """n_m and alpha[dB/cm] from the complex Bloch wavenumber."""
    w = 2*np.pi*f
    nm = beta.real*C0/w
    alpha_dBcm = abs(beta.imag)*8.686/100.0
    return nm, alpha_dBcm


# ------------------------------------------------------------------ RLGC
def line_rlgc(cell, fk, Zs, beta, **kw):
    """Quasi-TEM (L, C, Z0) of the Bloch mode from its own eigenvector.

    The charge per triangle is  q_t = A_t div J_t = (C_b x)_t  (up to the
    common -1/(j w) that cancels in Q/V), the potential is Phi = G_q,per q with
    the near/self block replaced by the analytic double integral, and
        C = Q'/V,   Q' = sum_signal q_t / P,   V = <Phi>_sig - <Phi>_gnd.
    Continuity (-j beta I = -j w Q') then fixes Z0 = beta/(w C) and
    L = Z0 beta/w, so only one extraction is needed, not two."""
    Z, C_b, Gpot = assemble_periodic(cell, fk, Zs, beta, want_pot=True, **kw)
    # eigenvector: smallest singular vector of Z(beta)
    _, _, Vh = np.linalg.svd(Z)
    x = Vh[-1].conj()
    q = C_b @ x
    phi = Gpot @ q
    reg = cell["region"]; A = cell["area"]
    sig = reg == "sig"; gnd = ~sig
    V = (phi[sig] @ A[sig])/A[sig].sum() - (phi[gnd] @ A[gnd])/A[gnd].sum()
    Qp = q[sig].sum()/cell["Lz"]
    C = Qp/V
    w = fk.w
    Z0 = beta/(w*C)
    L = Z0*beta/w
    return dict(C=C, L=L, Z0=Z0, x=x)
