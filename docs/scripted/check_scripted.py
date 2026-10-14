"""Numerical checks for docs/scripted_tl_block_derivation.md (numpy only).
Every block: SRC (Zs) -> TL line -> LOAD (Zt), voltage waves on R0.
Convention e^{+jwt} (the note's maths; the LSF conjugates when writing)."""
import numpy as np
c0 = 299792458.0
f = np.linspace(1e8, 100e9, 400); w = 2*np.pi*f
L, nm, ng, adb = 14e-3, 2.25, 2.20, 0.5*np.sqrt(f/1e9)   # dB/cm ~ sqrt(f)
Zc = 45.0 - 1.0j; import sys; Zs, Zt = 30.0, 80.0; R0 = float(sys.argv[1]) if len(sys.argv) > 1 else 50.0
g = adb*100*np.log(10)/20 + 1j*w*nm/c0; bo = w*ng/c0

# --- line S-matrix in R0 (section 3) ---
G = (Zc-R0)/(Zc+R0); e1 = np.exp(-g*L); e2 = e1*e1; den = 1-G*G*e2
S11 = G*(1-e2)/den; S21 = (1-G*G)*e1/den
# same from ABCD, as a cross-check
A = np.cosh(g*L); B = Zc*np.sinh(g*L); C = np.sinh(g*L)/Zc
d = A + B/R0 + C*R0 + A
print("S11 bounce vs ABCD:", np.max(abs(S11-(A+B/R0-C*R0-A)/d)),
      " S21:", np.max(abs(S21-2/d)))

# --- modulation transfer per unit incident wave (sections 4-5) ---
def Fint(q):  # (e^{qL}-1)/q
    return (np.exp(q*L)-1)/q
Xo = np.exp(-1j*bo*L)/L
V1, I1 = 1+S11, (1-S11)/R0                 # a1=1
T1 = ((V1+Zc*I1)/2*Fint(-g+1j*bo) + (V1-Zc*I1)/2*Fint(g+1j*bo))*Xo
V1, I1 = S21, -S21/R0                      # a2=1
T2 = ((V1+Zc*I1)/2*Fint(-g+1j*bo) + (V1-Zc*I1)/2*Fint(g+1j*bo))*Xo

# --- network: SRC, line, LOAD (section 6) ---
Gs = (Zs-R0)/(Zs+R0); Tf = 2*R0/(Zs+R0); GL = (Zt-R0)/(Zt+R0)
Vemf = 1.0; adrv = Vemf/2                  # EMF = 2 x incident wave
# unknowns a1, a2 (waves entering the line):
#   a1 = Tf*adrv + Gs*b1,  a2 = GL*b2,  b1 = S11 a1 + S21 a2,  b2 = S21 a1 + S11 a2
M = np.zeros((len(f), 2, 2), complex)
M[:, 0, 0] = 1-Gs*S11; M[:, 0, 1] = -Gs*S21
M[:, 1, 0] = -GL*S21;  M[:, 1, 1] = 1-GL*S11
rhs = np.stack([Tf*adrv*np.ones_like(f), 0*f], -1)[..., None]
a = np.linalg.solve(M, rhs)[..., 0]
Vmod_net = T1*a[:, 0] + T2*a[:, 1]

# --- TW formula, tw_electrode_derivation.md 3.5 (light entering ref) ---
th = np.tanh(g*L); Zin = Zc*(Zt+Zc*th)/(Zc+Zt*th)
p1 = Zin/((Zs+Zin)*((Zt+Zc)*np.exp(g*L)+(Zt-Zc)*np.exp(-g*L)))
up, um = g-1j*bo, g+1j*bo
H = p1*((Zt+Zc)*np.exp(g*L)*(1-np.exp(-up*L))/(up*L)
        + (Zt-Zc)*np.exp(-g*L)*(np.exp(um*L)-1)/(um*L))
print("network+T1/T2 vs TW formula x e^{-j bo L}:",
      np.max(abs(Vmod_net - H*np.exp(-1j*bo*L))/abs(H)))

# --- the integral is the N -> infinity limit of N slices (section 8) ---
Vp = Vmod_net*0  # rebuild V(z) from the solved a1, a2
V1 = a[:, 0]*(1+S11)+a[:, 1]*S21; I1 = (a[:, 0]*(1-S11)-a[:, 1]*S21)/R0
Vp, Vm = (V1+Zc*I1)/2, (V1-Zc*I1)/2
k = np.argmin(abs(f-60e9))
for N in (1, 2, 5, 10, 20, 50):
    z = (np.arange(N)+0.5)*L/N            # one lumped OM at each slice centre
    Vz = Vp[k]*np.exp(-g[k]*z)+Vm[k]*np.exp(g[k]*z)
    s = np.mean(Vz*np.exp(1j*bo[k]*z))*np.exp(-1j*bo[k]*L)
    print(f"N={N:3d} slices, 60 GHz: rel. error {abs(s/Vmod_net[k]-1):.2e}")
