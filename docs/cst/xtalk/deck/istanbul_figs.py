"""Figures for the Istanbul EO crosstalk deck (build_istanbul.py). All dB axes start at 0 dB at the top.
Sources: Cordoba values from the run READMEs (12 monitor frequencies, tables copied below with their file);
Istanbul curves from the run CSVs; lab curves digitized by the user (istanbul_run_d/lab_*.csv)."""
import os
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); X = os.path.join(HERE, ".."); OUT = os.path.join(HERE, "istanbul_img")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "axes.edgecolor": "#5A606E", "axes.labelcolor": "#1A1A1A",
                     "xtick.color": "#5A606E", "ytick.color": "#5A606E", "axes.spines.top": False, "axes.spines.right": False})
NAVY, RED, GREY, TEAL, ORANGE, BLUE, PURPLE = "#0E2268", "#F20013", "#9AA0AC", "#1BAA7D", "#EB6834", "#2A78D6", "#7A4BD1"
F12 = np.arange(5, 61, 5)

def ax_(figsize=(7.6, 4.0), ylim=(-100, 0), xlim=(0, 60), ylab="EO crosstalk (dB)"):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel(ylab); ax.grid(alpha=0.3)
    return fig, ax

def save(fig, ax, name, loc="lower right"):
    ax.legend(frameon=False, fontsize=11.5, loc=loc); fig.tight_layout(); fig.savefig(os.path.join(OUT, name), dpi=200); plt.close(fig)

# Cordoba: lateral width (cordoba_8mm_wide/results.md, -27 dB runs)
narrow = [-93.1, -90.6, -82.6, -86.0, -77.0, -76.3, -74.4, -70.3, -72.8, -69.6, -69.5, -70.5]
wide = [-90.9, -87.5, -81.0, -84.3, -74.8, -75.2, -72.0, -68.8, -70.7, -67.7, -68.0, -68.5]
fig, ax = ax_(ylim=(-110, 0))
ax.plot(F12, narrow, "o-", color=GREY, label="substrate 21 µm beyond the outer ground")
ax.plot(F12, wide, "o-", color=NAVY, label="substrate 625 µm beyond the outer ground")
save(fig, ax, "cordoba_width.png")

# Cordoba: electric bottom (cordoba_8mm_wide_ebottom/results.md; open = electric - difference)
elec = np.array([-96.5, -97.1, -86.2, -83.4, -78.7, -71.6, -69.9, -65.8, -65.9, -64.9, -62.9, -66.5])
diff = np.array([-5.6, -9.7, -5.2, +0.8, -3.8, +3.6, +2.1, +3.0, +4.8, +2.8, +5.0, +2.0])
fig, ax = ax_(ylim=(-110, 0))
ax.plot(F12, elec - diff, "o-", color=GREY, label="open bottom (silicon without end)")
ax.plot(F12, elec, "o-", color=NAVY, label="electric bottom (conductive glue under the chip)")
save(fig, ax, "cordoba_bottom.png")

# Cordoba: accuracy (cordoba_8mm_wide_ebottom_60dB/README.md; -40 dB from the dense run)
r27 = [-96.5, -97.1, -86.2, -83.4, -78.7, -71.6, -69.9, -65.8, -65.9, -64.9, -62.9, -66.5]
r45 = [-83.8, -82.4, -74.6, -65.0, -69.8, -68.0, -63.9, -68.6, -67.8, -65.0, -63.7, -64.7]
dense = np.loadtxt(os.path.join(X, "cordoba_8mm_wide_ebottom_40dB_dense", "dense_eo.csv"), delimiter=",")
fd, ed = dense[:, 0], dense[:, 3]
fig, ax = ax_(ylim=(-110, 0))
ax.plot(F12, r27, "o-", color=GREY, label="stopped at −27 dB")
ax.plot(F12, np.interp(F12, fd, ed), "s-", color=RED, label="stopped at −40 dB")
ax.plot(F12, r45, "o--", color=NAVY, label="stopped at −44.5 dB (reference)")
save(fig, ax, "cordoba_accuracy.png")

# Cordoba: monitor spacing (dense -40 dB run, 1 GHz vs every 5 GHz)
fig, ax = ax_(ylim=(-110, 0))
ax.plot(fd, ed, "-", color=NAVY, lw=1.6, label="monitor every 1 GHz")
ax.plot(F12, np.interp(F12, fd, ed), "o--", color=RED, label="same run, sampled every 5 GHz")
save(fig, ax, "cordoba_monitors.png")

# Istanbul build-up
def csv(p, skip=1): return np.loadtxt(os.path.join(X, p), delimiter=",", skiprows=skip)
d = csv("istanbul_run_d/xtalk_run_d.csv")   # f, NEXT_d, FEXT_d, EO_d, EO_a, EO_b, EO_c (2 and 15 GHz left out)
f = d[:, 0]; EO = {"a": d[:, 4], "b": d[:, 5], "c": d[:, 6], "d": d[:, 3]}
LAB = {"a": "(a) bare lines", "b": "(b) + real terminations", "c": "(c) + launch pads", "d": "(d) + driver (full module)"}
COL = {"a": ORANGE, "b": BLUE, "c": TEAL, "d": PURPLE}
fig, ax = ax_(figsize=(7.6, 4.2), ylim=(-80, 0))
for r in "abcd": ax.plot(f, EO[r], "o-", ms=3, lw=1.3, color=COL[r], label=LAB[r])
save(fig, ax, "istanbul_eo_abcd.png")
for a_, b_ in (("a", "b"), ("b", "c"), ("c", "d")):
    fig, ax = ax_(figsize=(7.0, 3.9), ylim=(-80, 0))
    for r in "abcd":
        if r not in (a_, b_): ax.plot(f, EO[r], "-", lw=0.8, color="#D5D8DE")
    ax.plot(f, EO[a_], "o-", ms=3, lw=1.2, color=GREY, label=LAB[a_]); ax.plot(f, EO[b_], "o-", ms=3, lw=1.5, color=COL[b_], label=LAB[b_])
    save(fig, ax, f"step_{a_}{b_}.png")

# EO vs FEXT, run (a) and run (d)
a = csv("istanbul_run_a/xtalk_run_a.csv")
fig, axs = plt.subplots(1, 2, figsize=(10.4, 3.9), sharey=True)
for ax, (fx, fe, eo, t) in zip(axs, ((a[:, 0], a[:, 2], a[:, 3], "(a) bare lines: EO about FEXT − 5 dB"),
                                        (f, d[:, 2], d[:, 3], "(d) full module: EO about equal to FEXT"))):
    ax.plot(fx, fe, "-", color=GREY, lw=1.4, label="FEXT (far-end crosstalk, |S41|)")
    ax.plot(fx, eo, "o-", ms=3, color=NAVY if t.startswith("(a)") else PURPLE, label="EO crosstalk")
    ax.set_xlim(0, 60); ax.set_ylim(-80, 0); ax.grid(alpha=0.3); ax.set_xlabel("Frequency (GHz)"); ax.set_title(t, fontsize=13)
    ax.legend(frameon=False, fontsize=11, loc="lower right")
axs[0].set_ylabel("dB"); fig.tight_layout(); fig.savefig(os.path.join(OUT, "eo_vs_fext_a_d.png"), dpi=200); plt.close(fig)

# Run (d): NEXT, FEXT, EO
fig, ax = ax_(figsize=(7.0, 3.9), ylim=(-80, 0), ylab="dB")
ax.plot(f, d[:, 1], "-", color=GREY, label="NEXT, at the driver port of line B (|S51|)")
ax.plot(f, d[:, 2], "-", color="#1A1A1A", lw=1.2, label="FEXT (|S41|)")
ax.plot(f, d[:, 3], "o-", ms=3, color=PURPLE, label="EO crosstalk")
save(fig, ax, "run_d_ports.png")

# Simulation vs lab
m1 = csv("istanbul_run_d/lab_MZ3toMZ4_extracted.csv", 2); m2 = csv("istanbul_run_d/lab_MZ4toMZ3_extracted.csv", 3)
fig, ax = ax_(figsize=(8.0, 4.3), ylim=(-70, 0), xlim=(0, 62))
ax.plot(f, d[:, 3], "o-", ms=3, lw=1.6, color=PURPLE, label="simulation, run (d) full module")
ax.plot(m1[:, 0], m1[:, 1], "s-", ms=2.5, lw=1.1, color=ORANGE, label="lab MZ3toMZ4 (digitized)")
ax.plot(m2[:, 0], m2[:, 1], "s-", ms=2.5, lw=1.1, color=BLUE, label="lab MZ4toMZ3 (digitized)")
ax.plot([0, 60, 60, 62], [-30, -30, -22, -22], "--", color="#1A1A1A", lw=1, label="specification")
ax.legend(frameon=False, fontsize=11, loc="lower center", ncol=2); fig.tight_layout(); fig.savefig(os.path.join(OUT, "sim_vs_lab.png"), dpi=200); plt.close(fig)
print("figures written to", OUT)

# ---- additions for the revised deck (2026-11-10)
import sys
sys.path.insert(0, os.path.join(X, "istanbul_run_a")); import load_fields as LF
# why FEXT is not enough: two victim profiles with the same far-end value
z = np.linspace(0, 1, 200)
fig, ax = plt.subplots(figsize=(6.4, 3.4))
ax.plot(z, z, color=NAVY, lw=2.2, label="built along the line: light sees ½ FEXT (−6 dB)")
ax.plot(z, np.ones_like(z), color=RED, lw=2.2, label="present from the input: light sees FEXT (0 dB)")
ax.plot([1], [1], "o", color="#1A1A1A", ms=7); ax.annotate("same FEXT", (1, 1), (0.62, 0.55), fontsize=12, arrowprops=dict(arrowstyle="->", color="#1A1A1A"))
ax.set_xlim(0, 1.05); ax.set_ylim(0, 1.6); ax.set_xlabel("position along line B, z / L"); ax.set_ylabel("forward wave on line B / FEXT")
ax.grid(alpha=0.3); ax.legend(frameon=False, fontsize=11, loc="upper left"); fig.tight_layout(); fig.savefig(os.path.join(OUT, "fext_ambiguity.png"), dpi=200); plt.close(fig)

# eigenmode: error scale on line A vs size of line B (Cordoba 8 mm)
bars = [("Line A field (reference)", 0, 0, NAVY),
        ("Line A error from the solver index mismatch\n(0.004–0.01 over 8 mm, 30 GHz)", -34, -26, RED),
        ("Part of line A not described by six modes", -46, -26, RED),
        ("Line B field (whole crosstalk signal)", -75, -55, TEAL)]
fig, ax = plt.subplots(figsize=(6.4, 3.4))
for i, (lab, lo, hi, c) in enumerate(bars):
    if lo == hi: ax.plot([lo], [i], "s", color=c, ms=12)
    else: ax.barh(i, hi - lo, left=lo, height=0.5, color=c, alpha=0.85)
ax.set_yticks(range(len(bars))); ax.set_yticklabels([b[0] for b in bars], fontsize=12); ax.invert_yaxis()
ax.set_xlim(-80, 0); ax.set_xlabel("level relative to line A field (dB)"); ax.grid(axis="x", alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "eigen_error_scale.png"), dpi=200, bbox_inches="tight", pad_inches=0.1); plt.close(fig)

# victim push-pull field along z, relative to line A, 9 GHz: runs a, c, d
R = {"a": LF.load(), "c": LF.load(base=os.path.join(X, "istanbul_run_c"), a_zip="e-field (f=1) [1]_lineA.zip", drop="first", skip_f=(2.0, 15.0)),
     "d": LF.load(base=os.path.join(X, "istanbul_run_d"), a_zip="e-field (f=1) [1]_lineA.zip", drop="first")}
fig, ax = plt.subplots(figsize=(6.4, 3.4))
for r in "acd":
    D = R[r]; p = D["ports"][9.0][1]; A = p["A"][0] - p["A"][1]; B = p["B"][0] - p["B"][1]
    from scipy.ndimage import median_filter
    y = median_filter(20 * np.log10(abs(B) / np.mean(abs(A))), size=41, mode="nearest")  # removes the slot-cell spikes (180 um period)
    ax.plot(D["z"] * 1e3 - 0.3, y, color=COL[r], lw=1.8, label=LAB[r])
ax.set_xlim(0, 8.75); ax.set_ylim(-105, 0); ax.set_xlabel("position along the line (mm)"); ax.set_ylabel("line B / line A (dB)")
ax.grid(alpha=0.3); ax.legend(frameon=False, fontsize=10.5, loc="lower center", ncol=3, handlelength=1.2); ax.set_title("Victim field along the line, 9 GHz (median over 0.2 mm)", fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "victim_profile_9GHz.png"), dpi=200); plt.close(fig)

# equations (mathtext)
EQ = {"eq_time": r"$t(z) = t_0 + z\,n_g/c$",
      "eq_phase": r"$\Delta\varphi_k(t_0) = \kappa \int_0^L E_{y,k}\,(z,\,t(z))\;dz$",
      "eq_H": r"$H_k = \frac{1}{L}\int_0^L E_{y,k}(z)\,e^{\,j\beta_o z}\,dz,\qquad \beta_o = \omega\, n_g/c$",
      "eq_pp": r"$H_{\mathrm{line}} = H_{+} - H_{-}\qquad X(f) = \frac{H_B}{H_A}$"}
for k, v in EQ.items():
    fig = plt.figure(figsize=(0.1, 0.1)); fig.text(0, 0, v, fontsize=22, color="#1A1A1A")
    fig.savefig(os.path.join(OUT, k + ".png"), dpi=200, bbox_inches="tight", pad_inches=0.05, transparent=True); plt.close(fig)
print("revised-deck figures written")
