"""Review questions on the Istanbul crosstalk deck: V(z), EE and EO crosstalk from the S-parameters vs from the fields.

S-parameter route (uniform coupled pair assumed): even/odd 2-ports S_e,o = S(i,j) +- S(i,j') of the 4-port; per mode
ABCD -> cosh(gamma L) = (A+D)/2, Zc = sqrt(B/C). V_A = V_e + V_o, V_B = V_e - V_o, each mode a uniform line with 50 ohm
source (a = 1/2 per mode) and load: V(z) = V(0) cosh(gamma z) - Zc I(0) sinh(gamma z).
Field route: line voltage = mean of the two gap voltages from E_y (mzm_interconnect.xtalk_fields, 50 ohm, as the deck).
Both V(z) normalised to V_A at the far end (a real port in every run).
EE crosstalk with all ports matched: V_port = b sqrt(Z0) where no wave is incident, so
  NEXT = S31 = S21 * V_B(near)/V_A(far),  FEXT = S41 = S21 * V_B(far)/V_A(far)   (field route: |S21| only as scale).
EO crosstalk: X = H[V_B]/H[V_A], H[V] = (1/L) int V(z) exp(j beta_o (z-L)) dz (symmetric gaps, push-pull).
Runs: a = bare pair, c = + input launch pads, d = + driver carrier and bond wires (|S| only: no S-route V(z))."""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__)); X = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(X, "istanbul_run_a")); sys.path.insert(0, os.path.abspath(os.path.join(X, "../../..")))
import numpy as np, skrf as rf
from mzm_interconnect import parameters as P, xtalk_fields as XF
from mzm_interconnect.physics import C0
from load_fields import load
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0; R0 = 50.0; NG = 2.27
LA = "e-field (f=1) [1]_lineA.zip"; BAD = (2.0, 15.0)
RUN = {"a": dict(fd=lambda: load(skip_f=BAD), s4p=os.path.join(X, "istanbul_run_a", "v0_istanbul_rf_line.s4p")),
       "c": dict(fd=lambda: load(base=os.path.join(X, "istanbul_run_c"), a_zip=LA, drop="first", skip_f=BAD),
                 s4p=os.path.join(X, "istanbul_run_c", "v0_istanbul_rf_lineLaunch.s4p")),
       "d": dict(fd=lambda: load(base=os.path.join(X, "istanbul_run_d"), a_zip=LA, drop="first", skip_f=BAD), s4p=None)}

def s2abcd(S):
    s11, s12, s21, s22 = S[:, 0, 0], S[:, 0, 1], S[:, 1, 0], S[:, 1, 1]
    A = ((1+s11)*(1-s22)+s12*s21)/(2*s21); B = R0*((1+s11)*(1+s22)-s12*s21)/(2*s21)
    C = ((1-s11)*(1-s22)-s12*s21)/(2*s21)/R0; D = ((1-s11)*(1+s22)+s12*s21)/(2*s21)
    return A, B, C, D

def full_from_col1(c):
    """Only port 1 is excited in the runs: the uniform-pair assumption (A <-> B mirror, end reversal, reciprocity) fills
    the 4-port from column 1: S11 = S22 = S33 = S44, S21 = S43, S31 = S42, S41 = S32."""
    s11, s21, s31, s41 = c[:, 0], c[:, 1], c[:, 2], c[:, 3]
    return np.stack([np.stack(r, -1) for r in ((s11, s21, s31, s41), (s21, s11, s41, s31), (s31, s41, s11, s21), (s41, s31, s21, s11))], -2)

def modal_line(S, L):
    """gamma, Zc of the even and odd mode of a symmetric 4-port (1 A near, 2 A far, 3 B near, 4 B far)."""
    S = full_from_col1(S[:, :, 0]); out = {}
    for m, sg in (("e", 1), ("o", -1)):
        M = np.empty((len(S), 2, 2), complex)
        for i, (a, a2) in enumerate(((0, 2), (1, 3))):
            for j, (b, b2) in enumerate(((0, 2), (1, 3))):
                M[:, i, j] = S[:, a, b] + sg*S[:, a, b2]
        A, B, C, D = s2abcd(M); ch = (A+D)/2
        r = np.sqrt(ch*ch-1+0j); y = ch-r; y = np.where(abs(y) > 1, ch+r, y)     # y = exp(-gamma L)
        gL = -np.log(abs(y)) - 1j*np.unwrap(np.angle(y))
        Z = np.sqrt(B/C); Z = np.where(Z.real < 0, -Z, Z)
        out[m] = (gL/L, Z)
    return out

def v_model(g, Z, z):
    """Voltage along a uniform line, 50 ohm source with incident wave 1/2 (per mode), 50 ohm load."""
    gl = g*z[-1]; Zin = Z*(R0*np.cosh(gl)+Z*np.sinh(gl))/(Z*np.cosh(gl)+R0*np.sinh(gl))
    V0 = 0.5*np.sqrt(R0)*2*Zin/(Zin+R0); I0 = V0/Zin
    return V0*np.cosh(g*z) - Z*I0*np.sinh(g*z)

def forward_amp(V, z, f):
    """Amplitude at z = 0 of the forward wave of a line voltage: two-wave fit V = V+ e^{-gz} + V- e^{gz} over the whole
    line, n (2.0-2.6, step 0.002) and alpha (0-40 Np/m) scanned. Returns V+(0) and the relative residual."""
    b0 = 2*np.pi*f*1e9/C0; best = (np.inf, 0)
    for n in np.arange(2.0, 2.6, 0.002):
        for a in (0, 5, 10, 20, 40):
            g = a + 1j*b0*n; A = np.stack([np.exp(-g*z), np.exp(g*z)], 1); c, *_ = np.linalg.lstsq(A, V, rcond=None)
            r = np.linalg.norm(V - A @ c)/np.linalg.norm(V)
            if r < best[0]: best = (r, c[0])
    return best[1], best[0]

def H(V, z, f):
    return np.trapezoid(V*np.exp(1j*2*np.pi*f*1e9*NG/C0*(z-z[-1])), z)/(z[-1]-z[0])

def analyse(r):
    fd = RUN[r]["fd"](); Xf = XF.eo_crosstalk_fields(p, fd); f = Xf["f_GHz"]; z = fd["z"] - fd["z"][0]; L = z[-1]
    Vf = {k: np.array([(Xf["V"][q][k][0]+Xf["V"][q][k][1])/2 for q in f]) for k in "AB"}
    # cell loading (pitch 0.2 mm): the E_y sample drops by 20-40 % on 2 of the 40 points of each cell. Those points are
    # found from line A (mean over f of |V| against its running median) and replaced by interpolation, on both lines.
    Vraw = {k: v.copy() for k, v in Vf.items()}
    a = np.mean(abs(Vf["A"]), 0); med = np.array([np.median(a[max(0, j-20):j+21]) for j in range(len(a))])
    bad = a < 0.9*med; good = ~bad
    for k in "AB":
        Vf[k] = np.array([np.interp(z, z[good], v.real[good])+1j*np.interp(z, z[good], v.imag[good]) for v in Vf[k]])
    end = lambda v, sl, z0: np.polyval(np.polyfit(z[sl]-z0, v[sl], 2), 0)      # quadratic fit over the end 0.3 mm
    n3 = int(round(0.3e-3/(z[1]-z[0])))
    Vend = {k: (np.array([end(v, slice(0, n3), 0) for v in Vf[k]]), np.array([end(v, slice(-n3, None), L) for v in Vf[k]])) for k in "AB"}
    nA = Vend["A"][1][:, None]
    out = dict(f=f, z=z, L=L, Vf_A=Vf["A"]/nA, Vf_B=Vf["B"]/nA, EO_f=Xf["X"], bad=bad)
    if RUN[r]["s4p"]:
        n = rf.Network(RUN[r]["s4p"]); fi = lambda s: np.interp(f*1e9, n.f, s.real)+1j*np.interp(f*1e9, n.f, s.imag)
        ml = modal_line(n.s, L); g = {m: fi(ml[m][0]) for m in "eo"}; Zc = {m: fi(ml[m][1]) for m in "eo"}
        VA, VB = [], []
        for i in range(len(f)):
            ve, vo = v_model(g["e"][i], Zc["e"][i], z), v_model(g["o"][i], Zc["o"][i], z)
            VA.append(ve+vo); VB.append(ve-vo)
        VA, VB = np.array(VA), np.array(VB)
        out.update(Vs_A=VA/VA[:, -1:], Vs_B=VB/VA[:, -1:], EO_s=np.array([H(VB[i], z, q)/H(VA[i], z, q) for i, q in enumerate(f)]),
                   S21=fi(n.s[:, 1, 0]), S31=fi(n.s[:, 2, 0]), S41=fi(n.s[:, 3, 0]), ne=g["e"].imag*C0/(2*np.pi*f*1e9),
                   no=g["o"].imag*C0/(2*np.pi*f*1e9), Ze=Zc["e"], Zo=Zc["o"])
    else:   # run d: CST ASCII magnitudes (dB) of S11, S21, S41, S51
        Sd, key = {}, None
        for ln in open(os.path.join(X, "istanbul_run_d", "v0_istanbul_rf_module_allS.txt")):
            m = re.search(r'"(S\d,\d) \[Magnitude / dB\]"', ln)
            if m: key = m.group(1); Sd[key] = []; continue
            if ln.startswith("#") or not ln.strip(): continue
            Sd[key].append([float(v) for v in ln.split()])
        g = lambda k: 10**(np.interp(f, *np.array(Sd[k]).T)/20)
        out.update(S21=g("S2,1"), S31=g("S5,1"), S41=g("S4,1"))
    # fields only: victim at the line ends (first and last sample) over the aggressor forward wave entering the line
    VAp = np.array([forward_amp(Vf["A"][i], z, q)[0] for i, q in enumerate(f)])
    out["NEXT_p"] = abs(Vraw["B"][:, 0]/VAp); out["FEXT_p"] = abs(Vraw["B"][:, -1]/VAp)
    s21 = abs(out["S21"])
    out["NEXT_f"] = s21*abs(Vend["B"][0]/Vend["A"][1]); out["FEXT_f"] = s21*abs(Vend["B"][1]/Vend["A"][1])
    return out

if __name__ == "__main__":
    dB = lambda x: 20*np.log10(abs(x)); R = {r: analyse(r) for r in "acd"}
    np.savez(os.path.join(HERE, "s_vs_fields.npz"), **{f"{r}_{k}": v for r, d in R.items() for k, v in d.items()})
    m = R["a"]["f"] >= 5
    for r in "acd":
        d = R[r]; print(f"--- run {r}")
        for lab, s, fl in (("NEXT", d["S31"], d["NEXT_f"]), ("FEXT", d["S41"], d["FEXT_f"])):
            e = dB(fl)-dB(s); print(f"{lab}: field - S median {np.median(e[m]):+.1f} dB, 5-95% {np.percentile(e[m],5):+.1f}..{np.percentile(e[m],95):+.1f}")
        if "EO_s" in d:
            e = dB(d["EO_s"])-dB(d["EO_f"]); print(f"EO: S-route - field median {np.median(e[m]):+.1f}, 5-95% {np.percentile(e[m],5):+.1f}..{np.percentile(e[m],95):+.1f};"
                  f" medians S {np.median(dB(d['EO_s'][m])):.1f}, field {np.median(dB(d['EO_f'][m])):.1f}")
            for q in (10, 20, 40):
                i = np.argmin(abs(d["f"]-q)); ea = np.sqrt(np.mean(abs(d["Vs_A"][i]-d["Vf_A"][i])**2)); eb = np.sqrt(np.mean(abs(d["Vs_B"][i]-d["Vf_B"][i])**2))/np.sqrt(np.mean(abs(d["Vf_B"][i])**2))
                print(f"  {q} GHz: n_e {d['ne'][i]:.3f} n_o {d['no'][i]:.3f} Z_e {d['Ze'][i].real:.1f} Z_o {d['Zo'][i].real:.1f}; V_A rms err {ea:.3f}, V_B rel rms err {eb:.2f}")
