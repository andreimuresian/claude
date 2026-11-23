"""Figures for the review slides of the Istanbul deck (S-parameters vs fields). Data: ../review_s_vs_fields/s_vs_fields.py.
All dB axes start at 0 dB at the top."""
import os, sys
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "istanbul_img")
sys.path.insert(0, os.path.join(HERE, "..", "review_s_vs_fields")); import s_vs_fields as M
def top_legend(fig, axes, ncol=4, top=0.84):
    """One legend for the figure, above the panels (never on the curves)."""
    h, l = [], []
    for a in axes:
        for hh, ll in zip(*a.get_legend_handles_labels()):
            if ll not in l: h.append(hh); l.append(ll)
    fig.legend(h, l, loc="upper center", ncol=ncol, frameon=False, fontsize=11, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, top))

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.edgecolor": "#5A606E", "axes.labelcolor": "#1A1A1A",
                     "xtick.color": "#5A606E", "ytick.color": "#5A606E", "axes.spines.top": False, "axes.spines.right": False})
NAVY, RED, GREY, TEAL, ORANGE, BLUE = "#0E2268", "#F20013", "#9AA0AC", "#1BAA7D", "#EB6834", "#2A78D6"
dB = lambda x: 20*np.log10(np.maximum(abs(x), 1e-12))
R = {r: M.analyse(r) for r in "acd"}; TT = {"a": "(a) bare line pair", "c": "(c) + input launch pads", "d": "(d) + driver and bond wires"}
m5 = R["a"]["f"] >= 5

# V(z): profiles at 40 GHz (a, c)
fig, ax = plt.subplots(1, 2, figsize=(13, 3.9), sharey=True)
q = 40
for k, r in enumerate("ac"):
    d = R[r]; i = np.argmin(abs(d["f"]-q)); z = d["z"]*1e3; n = np.max(abs(d["Vf_A"][i])); ns = np.max(abs(d["Vs_A"][i]))
    ax[k].plot(z, dB(d["Vf_A"][i]/n), color=NAVY, lw=1.6, label="line A (aggressor), fields")
    ax[k].plot(z, dB(d["Vs_A"][i]/ns), "--", color=BLUE, lw=1.5, label="line A, from S-parameters")
    ax[k].plot(z, dB(d["Vf_B"][i]/n), color=ORANGE, lw=1.6, label="line B (victim), fields")
    ax[k].plot(z, dB(d["Vs_B"][i]/ns), "--", color=RED, lw=1.5, label="line B, from S-parameters")
    ax[k].set_ylim(-60, 0); ax[k].set_xlim(0, 8.75); ax[k].set_xlabel("Position along the line z (mm)"); ax[k].grid(alpha=0.3)
    ax[k].set_title(f"{TT[r]}, {q} GHz", fontsize=12)
ax[0].set_ylabel("|V(z)| (dB, line A max = 0)")
top_legend(fig, ax, ncol=4, top=0.9); fig.savefig(os.path.join(OUT, "review_vz.png"), dpi=200); plt.close(fig)

# EE crosstalk: S-parameters vs fields
fig, ax = plt.subplots(1, 3, figsize=(15, 4.3), sharey=True)
for k, r in enumerate("acd"):
    d = R[r]; f = d["f"]
    nl = "NEXT |S31| (run d: |S51|)"
    ax[k].plot(f, dB(d["S31"]), color=NAVY, lw=1.6, label=nl); ax[k].plot(f, dB(d["NEXT_f"]), "--", color=BLUE, lw=1.4, label="NEXT from fields")
    ax[k].plot(f, dB(d["S41"]), color=ORANGE, lw=1.6, label="FEXT |S41|"); ax[k].plot(f, dB(d["FEXT_f"]), "--", color=RED, lw=1.4, label="FEXT from fields")
    ax[k].set_ylim(-80, 0); ax[k].set_xlim(0, 60); ax[k].set_xlabel("Frequency (GHz)"); ax[k].grid(alpha=0.3); ax[k].set_title(TT[r], fontsize=12)
    for lab, s, fl in (("NEXT", d["S31"], d["NEXT_f"]), ("FEXT", d["S41"], d["FEXT_f"])):
        e = dB(fl)-dB(s); print(r, lab, "field - S, 5-60 GHz: median %+.1f, mean |diff| %.1f dB" % (np.median(e[m5]), np.mean(abs(e[m5]))))
ax[0].set_ylabel("EE crosstalk (dB)")
top_legend(fig, ax, ncol=5, top=0.9); fig.savefig(os.path.join(OUT, "review_ee.png"), dpi=200); plt.close(fig)

# EO crosstalk: S-parameter route vs fields
fig, ax = plt.subplots(1, 3, figsize=(15, 4.3), sharey=True)
for k, r in enumerate("acd"):
    d = R[r]; f = d["f"]
    ax[k].plot(f, dB(d["EO_f"]), "o-", color=NAVY, ms=3, lw=1.6, label="EO from fields")
    if "EO_s" in d:
        ax[k].plot(f, dB(d["EO_s"]), "s--", color=RED, ms=3, lw=1.4, label="EO from S (uniform pair V(z))")
        e = dB(d["EO_s"])-dB(d["EO_f"]); print(r, "EO S - field, 5-60 GHz: median %+.1f, mean |diff| %.1f; medians S %.1f field %.1f" % (np.median(e[m5]), np.mean(abs(e[m5])), np.median(dB(d["EO_s"])[m5]), np.median(dB(d["EO_f"])[m5])))
    else:
        ax[k].plot(f, dB(d["S41"]), "--", color=ORANGE, lw=1.4, label="FEXT |S41| (no phase: no V(z))")
    ax[k].set_ylim(-80, 0); ax[k].set_xlim(0, 60); ax[k].set_xlabel("Frequency (GHz)"); ax[k].grid(alpha=0.3); ax[k].set_title(TT[r], fontsize=12)
ax[0].set_ylabel("EO crosstalk (dB)")
top_legend(fig, ax, ncol=4, top=0.86); fig.savefig(os.path.join(OUT, "review_eo.png"), dpi=200); plt.close(fig)

# Slide 3: victim V(z) with matching ends (NEXT, FEXT) but a different profile in between
fig, ax = plt.subplots(1, 2, figsize=(9.6, 4.6), sharey=True)
for k, (r, q) in enumerate((("a", 20), ("c", 30))):
    d = R[r]; i = np.argmin(abs(d["f"]-q)); z = d["z"]*1e3; n = np.max(abs(d["Vf_A"][i])); ns = np.max(abs(d["Vs_A"][i]))
    ax[k].plot(z, dB(d["Vf_B"][i]/n), color=NAVY, lw=1.6, label="victim V(z), full-wave fields")
    ax[k].plot(z, dB(d["Vs_B"][i]/ns), "--", color=RED, lw=1.6, label="victim V(z), S-parameters + uniform-pair model")
    ax[k].set_ylim(-60, 0); ax[k].set_xlim(0, 8.75); ax[k].set_xlabel("Position along the line z (mm)"); ax[k].grid(alpha=0.3)
    ax[k].set_title(f"{TT[r]}, {q} GHz", fontsize=12)
    ax[k].annotate("NEXT end", (0.1, -8), fontsize=11, color="#5A606E"); ax[k].annotate("FEXT end", (6.6, -8), fontsize=11, color="#5A606E")
ax[0].set_ylabel("|V(z)| (dB, aggressor max = 0)")
top_legend(fig, ax, ncol=1, top=0.82); fig.savefig(os.path.join(OUT, "slide3_victim.png"), dpi=200); plt.close(fig)
