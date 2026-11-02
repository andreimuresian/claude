"""Even- and odd-run modes (1.2 mm cell, magnetic Ymax, electric Si bottom, 15 deg): index, where the field lives
(cell-centre cross-section, eps-weighted |E|^2 shares by region) and gap pattern (CPW vs slot) per unit
cross-section energy, for comparison with the open-bottom modes."""
import os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = {"even": ({1: 21.7364055801, 2: 28.6810118013, 3: 31.0361181988}, {1: 172.8, 2: 29.86, 3: 26.27},
                 {1: "stripsvsbottom", 2: "slot", 3: "cpw"}),
        "odd": ({1: 23.2683293641, 2: 28.8766572463, 3: 31.0364638690}, {1: 9.477, 2: 33.86, 3: 26.27},
                {1: "AvsB", 2: "slot", 3: "cpw"})}
def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), skiprows=2); return a
for run, (F_GHZ, Q, NAME) in RUNS.items():
 for m in (1, 2, 3):
     n = 69.396 / F_GHZ[m]
     x = load(f"eig_{run}_mode{m}_xsec.txt"); X, Y = x[:, 0], x[:, 1]
     E2 = np.sum(np.abs(x[:, 3::2] + 1j * x[:, 4::2]) ** 2, axis=1)
     eps = np.where(X < -0.0049, 11.9, np.where(X < 0, 3.9, 1.0))
     W = eps * E2; tot = W.sum()
     reg = {"Si": X < -0.0049, "oxide/LN": (X >= -0.0049) & (X < 0), "air above": X >= 0.002,
            "under the line (|y-0.3125|<0.072)": (abs(Y - 0.3125) < 0.072),
            "between the lines (y<0.24)": Y < 0.2405, "outside (y>0.385)": Y > 0.385,
            "Si deeper than 100 um": X < -0.1}
     g = load(f"eig_{run}_mode{m}_{NAME[m]}.txt")
     p = g[np.isclose(g[:, 1], 0.3325), 5] + 1j * g[np.isclose(g[:, 1], 0.3325), 6]
     q = g[np.isclose(g[:, 1], 0.2925), 5] + 1j * g[np.isclose(g[:, 1], 0.2925), 6]
     cpw, slot = np.sqrt(np.mean(abs(p - q) ** 2)) / 2, np.sqrt(np.mean(abs(p + q) ** 2)) / 2
     print(f"{run} mode {m} ({NAME[m]}): f {F_GHZ[m]:.4f} GHz, n {n:.4f}, Q {Q[m]}")
     print("   energy shares: " + ", ".join(f"{k} {W[v].sum()/tot:.2f}" for k, v in reg.items()))
     print(f"   gaps: CPW pattern {cpw:.3e}, slot pattern {slot:.3e} (CPW/slot {cpw/slot:.2f}); "
           f"CPW pattern / sqrt(cross-section energy) {cpw/np.sqrt(tot):.3e}")
