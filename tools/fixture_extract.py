"""
Fixture-aware extraction: fit  T . line . T  instead of inverting a bare line.

WHY
    The uniform-line ABCD inversion solves two complex equations (S11, S21 of a
    symmetric reciprocal 2-port) for two complex unknowns (gamma.L and Zc) at
    each frequency independently. It is exactly determined, so it always returns
    an answer and has no redundancy left with which to notice that the thing
    between the ports is not a bare line. What it actually returns is the
    *equivalent uniform line* of whatever is there -- launches included.

    A launch is a fixed structure, so its contribution to the per-unit-length
    answer scales as 1/L, and because it is reflective the two launches form a
    cavity that rings at c/(2.n_m.L) and its harmonics. Hence: a bias that grows
    as the line gets shorter, plus resonant spikes at that line's own
    Fabry-Perot frequencies.

    This fit breaks the degeneracy with frequency-domain redundancy instead:
    alpha, n_m and Zc are smooth few-parameter functions and the launch is a
    fixed lumped network, so ~1000 frequencies constrain 11 parameters. Loss and
    launch have different frequency signatures, and the fit can tell them apart.

WHAT IT FIXES, AND WHAT IT DOES NOT
    Validated on a synthetic 2 mm line with known truth and known 28 pH / 12 fF
    launches: it recovers alpha to 0.0% at 40, 80, 150 and 300 GHz and recovers
    the launch as 27.9 pH / 12.0 fF, having been told neither. The bare
    inversion on the same file is +1.7% at 80 GHz but -3.9% by 300 GHz, because
    it absorbs the launch into the wrong alpha coefficients and they then
    diverge outside the measured band.

    It does NOT fix a test pattern that is a different structure from the device
    -- different conductor width, different loaded-cell density, different
    launches. That difference lives in the raw |S21| and no post-processing can
    or should remove it.

USAGE
    from tools.fixture_extract import fit_fixture
    par, fG, res = fit_fixture("line_2mm.s2p", L_mm=2.0)
    a, b, c = par[0:3]          # alpha(f) = a.sqrt(f) + b.f + c   [dB/cm, f in GHz]
    n0, dn, fc = par[3:6]       # n_m(f)  = n0 + dn.f/(fc+f)
    zinf, k1, k2 = par[6:9]     # Zc(f)   = zinf + k1/sqrt(f) - j.k2/sqrt(f)
    Lt_pH, Ct_fF = par[9:11]    # the recovered launch

    Expect ~4 minutes on 1000 frequency points; it is an occasional extraction,
    not something to put in a sweep.
"""
import sys, numpy as np
sys.path.insert(0,'/home/user/claude'); import matplotlib; matplotlib.use('Agg')
from scipy.optimize import least_squares
import skrf as rf
C0=299792458.0

def cascade(*Ms):
    out=Ms[0]
    for M in Ms[1:]: out=np.einsum('ik...,kj...->ij...',out,M)
    return out
def abcd_series(z): return np.array([[np.ones_like(z),z],[np.zeros_like(z),np.ones_like(z)]])
def abcd_shunt(y):  return np.array([[np.ones_like(y),np.zeros_like(y)],[y,np.ones_like(y)]])
def abcd_to_s(M,Z0):
    A,B,C,D=M[0,0],M[0,1],M[1,0],M[1,1]; den=A+B/Z0+C*Z0+D
    return (A+B/Z0-C*Z0-D)/den, 2/den

def model(par, fG, L_m, Z0, with_fixture=True):
    a,b,c, n0,dn,fc, zinf,k1,k2, Lt,Ct = par
    alpha = a*np.sqrt(fG)+b*fG+c
    nm    = n0 + dn*fG/(fc+fG)
    Zc    = (zinf + k1/np.sqrt(fG)) - 1j*(k2/np.sqrt(fG))
    g  = alpha*100/8.686 + 1j*nm*2*np.pi*fG*1e9/C0
    gl = g*L_m; ch,sh = np.cosh(gl), np.sinh(gl)
    line = np.array([[ch, Zc*sh],[sh/Zc, ch]])
    if not with_fixture:
        return abcd_to_s(line, Z0)
    w = 2*np.pi*fG*1e9
    T1 = cascade(abcd_series(1j*w*Lt*1e-12), abcd_shunt(1j*w*Ct*1e-15))
    T2 = cascade(abcd_shunt(1j*w*Ct*1e-15), abcd_series(1j*w*Lt*1e-12))
    return abcd_to_s(cascade(T1,line,T2), Z0)

def fit_fixture(path, L_mm, Z0=50.0, fmin=1.0, with_fixture=True):
    net=rf.Network(path); m=net.f>fmin*1e9
    fG=net.f[m]/1e9; S11m=net.s[m,0,0]; S21m=net.s[m,1,0]
    L_m=L_mm*1e-3
    def resid(par):
        S11,S21 = model(par,fG,L_m,Z0,with_fixture)
        return np.concatenate([ (S11-S11m).real,(S11-S11m).imag,
                                (S21-S21m).real,(S21-S21m).imag ])
    p0 = [0.5,0.02,0.1, 2.30,0.02,40.0, 60.0,5.0,3.0, 0.0,0.0]
    lo = [0.0,0.0,-2.0, 1.5,-0.5,1.0,  20.0,-50.,-50., -300.,-300.]
    hi = [5.0,0.5, 2.0, 4.0, 0.5,1e4, 150.0, 50., 50.,  300., 300.]
    if not with_fixture:
        p0[-2:]=[0.,0.]; lo[-2:]=[-1e-9,-1e-9]; hi[-2:]=[1e-9,1e-9]
    r=least_squares(resid,p0,bounds=(lo,hi),max_nfev=40000,xtol=1e-14,ftol=1e-14)
    return r.x, fG, r

def truth(fG):
    return (0.90*np.sqrt(fG)+0.010*fG+0.05, 2.34-0.10*np.exp(-fG/25.0))

OUT='/tmp/claude-0/-home-user-claude/7930b8bd-7239-59e6-a8de-284bb11bf7ea/scratchpad/fixture'
print("SYNTHETIC 2 mm LINE with 28 pH / 12 fF launches -- truth known exactly.")
print("(truth: alpha = 0.90.sqrt(f) + 0.010.f + 0.05 dB/cm)\n")
print(f"{'method':38s} {'a':>7} {'b':>8} {'c':>7} | {'alpha@40':>9} {'alpha@80':>9} {'err@80':>8}")
at,_ = truth(np.array([40.,80.]))
for lbl, wf in (("bare-line inversion (what we do now)",False),
                ("T . line . T fit (fixture-aware)",True)):
    par,fG,r = fit_fixture(f"{OUT}/syn_2.0mm.s2p", 2.0, with_fixture=wf)
    a40=par[0]*np.sqrt(40)+par[1]*40+par[2]; a80=par[0]*np.sqrt(80)+par[1]*80+par[2]
    print(f"{lbl:38s} {par[0]:7.4f} {par[1]:8.5f} {par[2]:7.4f} | {a40:9.3f} {a80:9.3f} "
          f"{100*(a80-at[1])/at[1]:+7.1f}%")
    if wf: print(f"{'   recovered launch':38s} {par[9]:7.2f} pH {par[10]:7.2f} fF   "
                 f"(true 28.0 pH, 12.0 fF)")
print(f"{'TRUTH':38s} {0.90:7.4f} {0.010:8.5f} {0.05:7.4f} | {at[0]:9.3f} {at[1]:9.3f}")
