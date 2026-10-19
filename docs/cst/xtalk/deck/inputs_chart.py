import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
f = [6, 18, 30, 42, 60]; dn = [1.50, 1.51, 1.51, 1.52, 1.57]
z1 = [0.44, 0.44, 0.45, 0.45, 0.46]; z2 = [0.30, 0.30, 0.30, 0.30, 0.31]
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
ax[0].plot(f, dn, "o-", color="#0E2268", lw=2); ax[0].set_ylim(1.0, 2.0)
ax[0].set_title("n_even − n_odd  (×10⁻³), from CST β"); ax[0].set_xlabel("frequency (GHz)")
for x, y in zip(f, dn): ax[0].annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center")
ax[1].fill_between(f, z2, z1, color="#F20013", alpha=.2, label="uncertainty band used in the model")
ax[1].plot(f, z1, "o-", color="#0E2268", lw=2, label="rows inside the metal"); ax[1].plot(f, z2, "s--", color="#5A606E", lw=2, label="row at metal top")
ax[1].set_ylim(0, 0.6); ax[1].set_title("Z_even / Z_odd − 1  (%), from field integration"); ax[1].set_xlabel("frequency (GHz)"); ax[1].legend(fontsize=9, loc="lower right")
for a in ax: a.grid(alpha=.3); a.set_xticks(f)
fig.tight_layout(); fig.savefig("../inputs_vs_f.png", dpi=130)
