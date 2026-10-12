
# ---- export of the raw solved field for the theory study -----------------
import pickle
bE = fund_mode.basis
(b_t, b_z) = bE.split()
Et_dofs = fund_mode.E[bE.split_indices()[0]]
Ez_dofs = fund_mode.E[bE.split_indices()[1]]

def sample(xs, ys):
    pts = np.vstack([xs, ys])
    Pt = b_t[0].probes(pts) if False else None
    return None

out = dict(neff=complex(n_eff), wl=wl, ne=ne, no=no, n_sio2=n_sio2, eps_au=eps_au,
           p=skfem_mesh.p, t=skfem_mesh.t, mat=np.array(mat_of_el),
           E=fund_mode.E, IL=att_opt_dB_cm, VpiL=Vpi_L_Vcm,
           SLAB_H=SLAB_H, WG_H=WG_H, GAP_BOT=GAP_BOT, SLAB_W=SLAB_W)
pickle.dump(out, open('mode_raw.pkl','wb'))
# probes on regular sets
def probe(pts):
    res = {}
    Pt = b_t.probes(pts); Pz = b_z.probes(pts)
    return Pt, Pz
print("export ok", n_eff, att_opt_dB_cm)
