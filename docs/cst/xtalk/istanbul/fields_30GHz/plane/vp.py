import sys; sys.path.insert(0,'.')
from sect import *
from scipy.optimize import minimize_scalar, least_squares
NP=np.log(10)/20
NC={"even":2.106,"odd":2.090}; AC=2.7          # line modes: sector fits / A-gap fit
def basis(z, waves):
    cols=[]
    for n,a,d in waves:                          # d=+1 forward, -1 backward
        g=a*10*NP/1e0*0.1 + 1j*K0*n             # a dB/cm -> Np/mm: a*NP/10
        g=a*NP/10 + 1j*K0*n
        cols.append(np.exp(-d*g*(z-z[0])))
    return np.column_stack(cols)
def resid(name, ch, z, xw):
    """xw: list of extra waves (n, a, d). Line modes fixed."""
    waves=[(NC[name],AC,+1),(NC[name],AC,-1)]+list(xw)
    B=basis(z,waves); R,*_=np.linalg.lstsq(B,ch.T,rcond=None)
    return np.linalg.norm(B@R-ch.T)/np.linalg.norm(ch), R
