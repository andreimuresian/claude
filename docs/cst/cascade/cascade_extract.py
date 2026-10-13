import numpy as np
c=299792458;R0=50
def load(fn):
    d=np.loadtxt(fn,comments=['!','#'])
    f=d[:,0]*1e9;S=np.zeros((len(f),2,2),complex)
    for k,(i,j) in enumerate([(0,0),(1,0),(0,1),(1,1)]):
        S[:,i,j]=d[:,1+2*k]*np.exp(1j*np.deg2rad(d[:,2+2*k]))
    return f,S
def s2abcd(S):
    s11,s12,s21,s22=S[:,0,0],S[:,0,1],S[:,1,0],S[:,1,1]
    A=((1+s11)*(1-s22)+s12*s21)/(2*s21);B=R0*((1+s11)*(1+s22)-s12*s21)/(2*s21)
    C=((1-s11)*(1-s22)-s12*s21)/(2*s21)/R0;D=((1-s11)*(1+s22)+s12*s21)/(2*s21)
    return np.stack([np.stack([A,B],-1),np.stack([C,D],-1)],-2)
def abcd2s(T):
    A,B,C,D=T[:,0,0],T[:,0,1],T[:,1,0],T[:,1,1];den=A+B/R0+C*R0+D
    S=np.empty_like(T);S[:,0,0]=(A+B/R0-C*R0-D)/den;S[:,0,1]=2*(A*D-B*C)/den
    S[:,1,0]=2/den;S[:,1,1]=(-A+B/R0-C*R0+D)/den;return S
def gz(T,L,f):
    A=(T[:,0,0]+T[:,1,1])/2;g=np.arccosh(A)
    # unwrap beta continuously
    b=np.unwrap(np.imag(g)*1)  # imag in [0,pi]
    g=np.real(g)+1j*np.imag(g)
    Z=np.sqrt(T[:,0,1]/T[:,1,0]); Z=np.where(Z.real<0,-Z,Z)
    return g,Z
f,S1=load('LINEA0_1MM.s2p');f5,S5=load('LINEA0_5MM.s2p');assert np.allclose(f,f5)
T1=s2abcd(S1);T5=s2abcd(S5)
T15=np.linalg.matrix_power(T1,5);S15=abcd2s(T15)
db=lambda x:20*np.log10(abs(x))
ang=lambda x:np.rad2deg(np.unwrap(np.angle(x)))
idx=[np.argmin(abs(f-x*1e9)) for x in [0,1,5,10,20,30,40,50,60]]
print('f  |S21|5mm dB  cascade  d  | S11 5mm dB cascade | phase21 5mm casc')
for i in idx:
    print(f"{f[i]/1e9:4.0f} {db(S5[i,1,0]):8.3f} {db(S15[i,1,0]):8.3f} {db(S15[i,1,0])-db(S5[i,1,0]):7.3f} | {db(S5[i,0,0]):7.2f} {db(S15[i,0,0]):7.2f} | {ang(S5[:,1,0])[i]:9.2f} {ang(S15[:,1,0])[i]:9.2f}")
# extraction per length: alpha and nm via cosh, with phase unwrap by continuity: beta*L = unwrapped -angle of e^{-gamma L} from eigen
def ext(T,L):
    A=(T[:,0,0]+T[:,1,1])/2
    # eigenvalue e^{-gL}: lam = A - sqrt(A^2-1), choose |lam|<1
    r=np.sqrt(A*A-1+0j);lam=A-r;lam=np.where(abs(lam)>1,A+r,lam)
    ph=np.unwrap(np.angle(lam));al=-np.log(abs(lam))/L;be=-ph/L
    Z=np.sqrt(T[:,0,1]/T[:,1,0]);Z=np.where(Z.real<0,-Z,Z)
    return al,be,Z
w=2*np.pi*f
for nm,T,L in [('1mm',T1,1e-3),('5mm',T5,5e-3),('2len',np.linalg.solve(T1,T5),4e-3)]:
    al,be,Z=ext(T,L)
    print(nm,'f a(dB/cm) nm Zc')
    for i in idx[1:]:
        print(f"  {f[i]/1e9:4.0f} {al[i]*8.686/100:6.3f} {be[i]*c/w[i]:7.4f} {Z[i].real:6.2f}{Z[i].imag:+6.2f}j")
from scipy.signal import argrelmin
for nm,S,L in [('1mm',S1,1e-3),('5mm',S5,5e-3)]:
    m=argrelmin(db(S[:,0,0]),order=20)[0]
    print(nm,'S11 minima GHz',np.round(f[m]/1e9,2),'dB',np.round(db(S[m,0,0]),1))
    fm=f[m]; print('  n from f_m = m c/(2 n L):',[round(k*c/(2*L*x),4) for k,x in enumerate(fm,1)])
    if len(fm)>1: print('  n from spacing:',np.round(c/(2*L*np.diff(fm)),4))
