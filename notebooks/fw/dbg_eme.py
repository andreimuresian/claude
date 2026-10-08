import sys, numpy as np, pandas as pd
sys.path.insert(0, "../mom"); import stack_params as sp, eme
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, t_LN=sp.TFLN - d.ETCH_DEPTH*1e-6, L1=d.L1*1e-6, L2=d.L2*1e-6, W1=d.W1*1e-6, W2=d.W2*1e-6)
x_si, x_gi = g["WS"]/2, g["WS"]/2 + g["GAP"]; x_go = x_gi + 70e-6
A = eme.Section(g, 20e9, [(0, x_si), (x_gi, x_go)], [x_gi + g["W1"], x_gi + g["W1"] + g["W2"]], 30)
k0 = A.k0
print("n_eff of section A modes:", np.round(A.beta/k0, 3))
print("|V|:", np.round(np.abs(A.V), 3))
S = eme.prop(A, eme.P)
lam, a, b = eme.bloch(S)
g_ = -np.log(lam)/eme.P
print("uniform cell n from Bloch:", np.round(np.sort_complex(g_.imag/k0 - 1j*g_.real/k0), 3)[:10])
Sj = eme.interface(A, A); print("A->A interface: |S21 - I|", np.abs(Sj[1][0] - np.eye(30)).max(), "|S11|", np.abs(Sj[0][0]).max())
