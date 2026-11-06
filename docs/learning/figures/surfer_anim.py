"""Animation: the light (surfer) crossing the line while the RF field changes. The Pockels push at each moment is the
field at the surfer's position and time; the modulation is the push accumulated over the trip.
Normalised units: line length 1, light speed 1 (transit time 1), RF period 1/2.2 (2.2 periods per transit). The light enters at
the moment that lets it collect the most (centred phase): the final value is then the modulation amplitude eta.
Cases: matched forward wave, slightly slower forward wave (slips half a wavelength), field oscillating in place, backward wave."""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
w = 2 * np.pi * 2.2
CASES = [("Forward wave, same speed as the light", w, "#1baa7d"),
         ("Forward wave, a bit slower (slips half a wave)", w - np.pi, "#2a78d6"),
         ("Field oscillating in place (P1)", 0.0, "#eb6834"),
         ("Backward wave (P2b)", -w, "#c0392b")]
z = np.linspace(0, 1, 400); T = np.linspace(0, 1, 90); Tf = np.r_[T, np.ones(25)]
fig, axs = plt.subplots(4, 2, figsize=(11, 9), gridspec_kw=dict(width_ratios=[1.6, 1]))
art = []
for r, (name, k, col) in enumerate(CASES):
    a, b = axs[r]
    line, = a.plot([], [], color="0.4", lw=1.5)
    dot, = a.plot([], [], "o", ms=12, color=col, mec="k", zorder=5)
    arr = a.annotate("", (0, 0), (0, 0), arrowprops=dict(arrowstyle="-|>", lw=2.5, color=col))
    a.axhline(0, color="0.8", lw=0.8); a.set_xlim(0, 1); a.set_ylim(-1.3, 1.3); a.set_yticks([])
    a.set_title(name, fontsize=10, loc="left"); a.set_xticks([0, 1]); a.set_xticklabels(["light in", "light out"] if r == 3 else ["", ""])
    ph = -(w - k) / 2; seen = np.cos((w - k) * T + ph); acc = np.r_[0, np.cumsum((seen[1:] + seen[:-1]) / 2 * np.diff(T))]
    b.plot(T, T, "--", color="0.75", lw=1); acc_l, = b.plot([], [], color=col, lw=2.5)
    txt = b.text(0.02, 0.85, "", fontsize=10, transform=b.transAxes)
    b.set_xlim(0, 1); b.set_ylim(-0.35, 1.05); b.axhline(0, color="0.8", lw=0.8); b.set_yticks([0, 1])
    b.set_xticks([0, 1]); b.set_xticklabels(["", ""] if r < 3 else ["start", "end of trip"])
    if r == 0: b.set_title("total push collected (dashed: ideal)", fontsize=10)
    art.append((k, ph, line, dot, arr, acc_l, txt, acc))
fig.suptitle("The light (dot) crosses the line; the arrow is the push it gets from the field where it is, right now\n(light enters at the best moment, so the final value is the modulation efficiency)",
             fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.96))

def frame(i):
    t = Tf[i]; j = min(i, len(T) - 1)
    for k, ph, line, dot, arr, acc_l, txt, acc in art:
        line.set_data(z, np.cos(w * t - k * z + ph))
        e = np.cos((w - k) * t + ph)
        dot.set_data([t], [e]); arr.xy = (t, e * 0.95); arr.set_position((t, 0))
        acc_l.set_data(T[:j + 1], acc[:j + 1])
        txt.set_text(f"collected: {acc[j] * 100:+.0f} %")
    return []
FuncAnimation(fig, frame, frames=len(Tf), interval=80).save("surfer.gif", writer=PillowWriter(fps=12), dpi=80)
fig.savefig("surfer_last.png", dpi=80)
