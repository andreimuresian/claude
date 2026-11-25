# 10 conclusions
s = new("Conclusions", "Madrid 1 (tri-galvanic), λ = 1625 nm, no ALD")
table(s, [["Design", "GAP", "BUFFER", "Vπ·L (V·cm)", "IL (dB/cm)", "IL at −40 nm"],
          ["Baseline", "3.20", "100", "1.827", "0.261", "—"], ["Optimum (nominal)", "3.05", "150", "1.747", "0.377", "0.552"],
          ["Optimum (robust)", "3.05", "190", "1.801", "0.276", "0.377"], ["GAP ≥ 3.5, nominal", "3.50", "100", "1.857", "0.233", "0.579"],
          ["GAP ≥ 3.5, robust", "3.50", "115", "1.880", "0.192", "0.371"], ["GAP 3.5 + U-slot (tongues)", "3.50", "130", "1.790", "0.189", "0.324"], ["Madrid B (reference)", "3.20", "120", "1.854", "0.209", "—"]],
      0.6, 1.8, 7.9, [2.3, 0.8, 1.0, 1.3, 1.2, 1.3], size=11.5, highlight=(6,))
text(s, 0.6, 4.75, 7.9, 0.4, [("All values FEM (λ = 1625 nm). −40 nm column: IL with the buffer 40 nm thinner than nominal", {"size": 10, "color": MUT})])
box(s, 8.8, 1.8, 4.0, 4.6, [H("Takeaways"), ("Standing wave: present without buffer, removed for buffer ≥ 50 nm across 1525–1625 nm", B),
    ("Best geometry: gap at minimum, cap filling the gap, thick ground tongue; CAP_H irrelevant", B),
    ("Geometry alone gains ≈ 3–6 %; the U-slot (from the Gemini search) adds −5 % at equal IL at gap 3.5 µm", B),
    ("Recommended: gap 3.5 µm + U-slot with gold tongues: 1.790 V·cm / 0.189 dB/cm, worst case < 0.33 dB/cm", B),
    ("Tools delivered: dataset, GP surrogate, optimiser, offline predictor", B)])
