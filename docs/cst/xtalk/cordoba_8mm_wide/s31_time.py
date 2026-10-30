"""Time-domain view of column 1 of the widened run's s4p (only port 1 driven): band-limited impulse
response (0-60 GHz, Hann window) of S21, NEXT = S31 and FEXT = S41. A coupled-line NEXT is spread
from 0 to 2 Td (Td = through delay); a wave born at A's far end and returning at n_g,b arrives as a
peak near Td (1 + n_g,b / 2.227)."""
import os, numpy as np, skrf
HERE = os.path.dirname(os.path.abspath(__file__))
n = skrf.Network(os.path.join(HERE, "LINEA_8MM_625UM_PITCH_CORDOBA_OAD_1port.s4p"))
f = n.f; df = f[1] - f[0]; assert abs(f[0]) < 1
w = np.hanning(2 * len(f))[len(f):]                     # one-sided Hann taper to 60 GHz
Nfft = 8192; t = np.arange(Nfft) / (Nfft * df) * 1e12  # ps
def imp(s):
    h = np.fft.irfft(s * w, Nfft); return h / np.abs(h).max()
for lab, k in (("S21", 1), ("NEXT S31", 2), ("FEXT S41", 3)):
    h = imp(n.s[:, k, 0]); m = t < 260
    pk = np.argsort(-np.abs(h[m]))
    peaks = []
    for i in pk:
        if all(abs(t[i] - t[j]) > 6 for j in peaks): peaks.append(i)
        if len(peaks) == 4: break
    env = lambda a, b: np.sqrt(np.mean(h[(t >= a) & (t < b)] ** 2))
    print(f"{lab:9s} peaks (ps, rel.): " + ", ".join(f"{t[i]:.1f} ({abs(h[i]):.2f})" for i in sorted(peaks)) +
          f" | rms 0-50 ps {env(0,50):.3f}, 50-100 {env(50,100):.3f}, 100-140 {env(100,140):.3f}, 140-250 {env(140,250):.3f}")
print("Td (S21 group delay) = 59.5 ps; far-end-born return at n_g 2.43-2.55 would arrive at 124-128 ps")
