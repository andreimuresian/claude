import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = list(csv.DictReader(open("alumina_sweep.csv")))
T = [float(r["T_nm"]) for r in R]; IL = [float(r["IL_dBcm"]) for r in R]; V = [float(r["VpiL_Vcm"]) for r in R]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.6))
for a, y, c, lab, fmt in [(a1, V, "#1f5aa6", "Vπ·L (V·cm)", "{:.3f}"), (a2, IL, "#c2410c", "IL (dB/cm)", "{:.2f}")]:
    a.plot(T, y, "o-", color=c, lw=2, ms=6)
    for t, v in zip(T, y):
        if t in (0, 40, 100):
            a.annotate(fmt.format(v), (t, v), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=9, color=c)
    a.axvline(40, color="0.6", ls=":", lw=1); a.text(41, a.get_ylim()[0], " nominal 40 nm", fontsize=8.5, color="0.4", va="bottom")
    a.set_xlabel("ALD Al$_2$O$_3$ thickness (nm)"); a.set_ylabel(lab); a.grid(alpha=.3)
    for s in ("top", "right"): a.spines[s].set_visible(False)
a1.set_title("Vπ·L vs Al$_2$O$_3$ thickness", weight="bold"); a2.set_title("Optical attenuation vs Al$_2$O$_3$ thickness", weight="bold")
fig.suptitle("Cordoba, WG_TOP 1.4 µm, CAP_W 2.0 µm, gap 4.2 µm, unetched slab, 1575 nm (femwell)", fontsize=11)
fig.tight_layout(); fig.savefig("alumina_femwell_only.png", dpi=170)
