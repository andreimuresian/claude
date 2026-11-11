# ALD: |S11| and |S21| before and after ALD, raw and smoothed chip averages

Wafers: CORDOBA 4CA0162 (15 chips), 4CA0163 (14 chips, chip 04 excluded), JEREZ 6JZ0011 (15), HELSINKI 5HK0005 (8, 13 mm).

- `s_smoothed_plots.py`: for each wafer and state, the raw average is the mean over chips of |S| in dB. The smoothed curve
  is `scipy.signal.savgol_filter(raw average, 21, 3)`, i.e. 21 points (0.79 GHz) and order 3.
  Outputs: `S11_<wafer>.png`, `S21_<wafer>.png`, `smoothing_example.png`, `smoothing_stats.csv` (rms of raw − smoothed per band).
  There is no modelled curve.
- `build_deck.py` produces `ALD_S_parameters_smoothed.pptx`. It has 6 slides: title, smoothing method, and one slide per wafer.

Window check: with 21 points the S11 null depths below 20 GHz move by at most 0.1 dB (CORDOBA, HELSINKI ALD).
With 41 points they move by up to 0.4 dB.
