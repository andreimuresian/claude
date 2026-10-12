# Electrode-induced optical loss in LN modulators (bulk Ti:LN and TFLN), buffer layers, electrode-waveguide spacing

Verification note: api.crossref.org, doi.org, nature.com, arxiv.org and researching.cn could not be reached from this environment (DNS failure or the proxy refused the connection). "VERIFIED" below means the full citation (DOI included) matched an independent record found by web search, such as a publisher, university repository, NSF PAR or a reference list. "PARTIAL" means the bibliographic data was confirmed but the DOI was not. "UNVERIFIED" means it comes from memory only. No DOI below is invented. Unconfirmed DOIs are flagged as such.

## Q1. Classic bulk Ti:LiNbO3: metal loss and the SiO2 buffer, trade-off with Vpi·L

### Takeaway
In bulk Ti:LN, a SiO2 buffer (typically about 0.2 to 1 µm) under electrodes placed over the waveguide is the standard fix for metal absorption of the TM mode (z-cut). It also helps velocity and impedance matching, at the cost of a lower overlap and so a higher Vpi·L. I found no primary measurement of the loss-vs-thickness curve within this search budget.

### Cited Findings
- Wooten, E. L.; Kissa, K. M.; Yi-Yan, A.; Murphy, E. J.; Lafaw, D. A.; Hallemeier, P. F.; Maack, D.; Attanasio, D. V.; Fritz, D. J.; McBrien, G. J.; Bossi, D. E., "A review of lithium niobate modulators for fiber-optic communications systems," IEEE J. Sel. Top. Quantum Electron. 6(1), 69–82 (2000). PARTIAL: journal, volume 6, start page 69 and year 2000 were confirmed in a reference list. The DOI I believe to be 10.1109/2944.826874 was NOT confirmed. Only the first 3 authors and Maack were seen in sources. — [researching.cn reference list](https://www.researching.cn/articles/OJ9d03e04e9a0ee503/referenceandcitations); [optiwave forum author list](https://optiwave.com/forums/reply/13751/)
- Marcuse, D., "Optimal electrode design for integrated optics modulators," IEEE J. Quantum Electron. QE-18(3), 393–398 (Mar. 1982). PARTIAL: volume, issue and pages come from a 1990s reference list. The DOI was not found or verified. — [Acta Optica Sinica 16(3) 357 (1996) reference list](https://m.researching.cn/articles/OJc50c842a6471c47)
- Kaminow-era primary buffer-layer papers: not located or verified in this pass.

### Inferences
- The buffer works because the metal-clad TM mode (or a surface plasmon) is pushed away. The evanescent field decays through the buffer, so the loss falls roughly exponentially with buffer thickness. This is consistent with your ~38 nm decay constant (inference, not from a source).

### Gaps
- Original Ti:LN papers that measured loss vs buffer thickness (e.g. Kaminow, Ramaswamy, Alferness) were not retrieved, so I have no numbers.

## Q2. TFLN: electrode gap vs optical loss, buffer layers, capacitively loaded electrodes

### Takeaway
In TFLN the absorption limit sets the electrode gap. Most x-cut devices use a gap of about 5 µm or more because the metal loss rises steeply as the gap shrinks. One preprint attributes this to coupling into surface-plasmon modes at the metal–LN interface. Adding about 100 nm of SiO2 under the electrodes reduces the metal loss by more than 100x, which allows a 2.7 to 3 µm gap at under 0.1 to 0.5 dB/cm. I found no paper that reports oscillatory loss vs electrode position.

### Cited Findings
- Wang, C.; Zhang, M.; Chen, X.; Bertrand, M.; Shams-Ansari, A.; Chandrasekhar, S.; Winzer, P.; Lončar, M., "Integrated lithium niobate electro-optic modulators operating at CMOS-compatible voltages," Nature 562, 101–104 (2018), DOI 10.1038/s41586-018-0551-y. UNVERIFIED: no source was reachable to confirm it. Citation is from memory.
- Kharel, P.; Reimer, C.; Luke, K.; He, L.; Zhang, M., "Breaking voltage–bandwidth limits in integrated lithium niobate modulators using micro-structured electrodes," Optica 8(3), 357–363 (2021); arXiv:2011.13422. PARTIAL: the DOI was NOT verified, although it is likely 10.1364/OPTICA.416155. The paper reports Vpi = 1.3 V with a 1.8 dB roll-off at 50 GHz. Its micro-structured (T-shaped, capacitively loaded) electrodes let the gap shrink without the microwave-loss penalty. — [reference list, researching.cn](https://www.researching.cn/articles/OJ9d03e04e9a0ee503/referenceandcitations); [ar5iv](https://ar5iv.labs.arxiv.org/html/2011.13422)
- Zhu, D.; Shao, L.; Yu, M.; Cheng, R.; Desiatov, B.; Xin, C. J.; Hu, Y.; Holzgrafe, J.; Ghosh, S.; Shams-Ansari, A.; Puma, E.; Sinclair, N.; Reimer, C.; Zhang, M.; Lončar, M., "Integrated photonics on thin-film lithium niobate," Adv. Opt. Photon. 13(2), 242–352 (2021), DOI 10.1364/AOP.411024. VERIFIED. — [NSF PAR](https://par.nsf.gov/biblio/10225637); [arXiv 2102.11956](https://arxiv.org/pdf/2102.11956)
- Boes, A.; Chang, L.; Langrock, C.; Yu, M.; Zhang, M.; Lin, Q.; Lončar, M.; Fejer, M.; Bowers, J.; Mitchell, A., "Lithium niobate photonics: Unlocking the electromagnetic spectrum," Science 379(6627), eabj4396 (2023), DOI 10.1126/science.abj4396. VERIFIED. — [Harvard](https://nano-optics.seas.harvard.edu/publication/lithium-niobate-photonics-unlocking-electromagnetic-spectrum); [Adelaide repository](https://eres.library.adelaide.edu.au/dspace/handle/2440/137678)
- Liu, X.; Xiong, B.; Sun, C.; Wang, J.; Hao, Z.; Wang, L.; Han, Y.; Li, H.; Yu, J.; Luo, Y., "Wideband thin-film lithium niobate modulator with low half-wave-voltage length product," Chin. Opt. Lett. 19(6), 060016 (2021), DOI 10.3788/COL202119.060016. VERIFIED. The arXiv version (2103.03684) has a different title: "Low half-wave-voltage, ultra-high bandwidth thin-film LiNbO3 modulator based on hybrid waveguide and periodic capacitively loaded electrodes."
  - A 100 nm silica layer between LN and the electrodes cuts the optical loss by more than two orders of magnitude, keeping it under 0.1 dB/cm at a 3 µm gap.
  - The device reaches Vpi·L = 1.7 V·cm, and a 5 mm device gives Vpi = 3.4 V with under 2 dB roll-off up to 67 GHz.
  - The supplementary analysis attributes the usual >5 µm gaps in x-cut TFLN to absorption that rises sharply as the gap shrinks, via coupling into surface-plasmon modes at the metal–LN interface.
  - These details come from search-engine summaries of the PDF. I could not read the full text directly. — [COL PDF](https://www.researching.cn/ArticlePdf/m00005/2021/19/6/060016.pdf); [arXiv 2103.03684](https://arxiv.org/pdf/2103.03684)
- Other preprints with gap and loss numbers. These are arXiv preprints whose journal versions I did not verify, and the numbers come from search snippets:
  - A 6.5 µm gap gives about 3.0 V·cm and about 0.02 dB/cm. A narrower gap improves overlap but raises absorption. — [arXiv 2605.21073](https://arxiv.org/pdf/2605.21073)
  - With a buffer, a 2.7 µm gap gives under 0.5 dB/cm, again a two-orders reduction from the buffer. — [arXiv 2411.15037](https://arxiv.org/pdf/2411.15037)
  - A mid-IR device (no-buffer case) shows loss rising sharply below a 12 µm gap on a 0.9 µm film and below 8 µm on a 1.5 µm film, attributed to plasmonic absorption. — [arXiv 2505.23632](https://arxiv.org/pdf/2505.23632)
  - A 5.5 µm gap gives 2.2 V·cm and under 0.1 dB/cm. — [arXiv 2201.10790](https://arxiv.org/pdf/2201.10790)
  - A 4 µm gap with a 450 nm buffer adds about 0.08 dB/cm. — [arXiv 2207.02608](https://arxiv.org/pdf/2207.02608)

### Inferences
- Reported TFLN behavior is a monotonic, roughly exponential rise in loss as the gap shrinks, and a buffer of about 100 nm or more removes it. This matches your IL ∝ exp(-3.3·gap) and the suppression by a 200 nm SiO2 buffer.

### Gaps
- None of the TFLN papers found report oscillatory or resonant loss vs electrode gap or edge position, or sensitivity to lithography misalignment.
- I found no paper that systematically measures excess loss for electrodes placed directly on the slab with no buffer.

## Q3. Lateral leakage and hybrid-mode coupling on a slab (SOI and LNOI): the likely origin of your 0.9 µm oscillation period

### Takeaway
The closest published analogue to your oscillation is TM lateral leakage in thin-ridge waveguides. The TM-like guided mode couples to the TE slab mode, and the loss shows sharp periodic minima vs ridge width. These come from interference between the leakage launched at the two ridge edges, the same physics as a lateral cavity. In LNOI, birefringence and crystal cut can swap which polarization leaks. I found no paper that links this to metal electrodes.

### Cited Findings
- Webster, M. A.; Pafchek, R. M.; Mitchell, A.; Koch, T. L., "Width dependence of inherent TM-mode lateral leakage loss in silicon-on-insulator ridge waveguides," IEEE Photon. Technol. Lett. 19(6), 429–431 (2007), DOI 10.1109/LPT.2007.891979. VERIFIED (per a search-engine summary of the records, which also confirmed the 19(6) 429–431 citation).
  - Reports the first optical-domain observation of width-dependent TM lateral leakage, with sharp cyclic loss minima at specific widths. — [Univ. Arizona experts record](https://experts.arizona.edu/en/publications/width-dependence-of-inherent-tm-mode-lateral-leakage-loss-in-sili/); [CiNii](https://cir.nii.ac.jp/crid/1361418520655615488)
- Kakihara, Saitoh and Koshiba (numerical study): TM-like lateral leakage is minimized at particular widths. Details are in JLT 27(23), 5492–5499 (2009). PARTIAL: confirmed from the Hokkaido repository filename only; the title and DOI were not verified. — [HUSCAP PDF](https://eprints.lib.hokudai.ac.jp/repo/huscap/all/39952/JLT27-23_p5492-5499.pdf)
- Lateral leakage in LNOI. Because LN is birefringent, the leaking polarization depends on crystal orientation, and engineering the leakage improves SHG in PPLN waveguides. arXiv preprint; journal version not verified. — [arXiv 1906.02383](https://arxiv.org/pdf/1906.02383)
- In shallow x-cut LNOI ridges, which polarization leaks (TE or TM) switches with ridge height. IEEE Photonics Journal (2013); authors and DOI not verified. — [DOAJ](https://doaj.org/article/ee24ead2a8ca45e4801c3c4bd117f069)
- Symmetric "plus-shaped" cross-sections suppress TM lateral leakage. JOSA B preprint (Paderborn); DOI not verified. — [preprint PDF](https://ris.uni-paderborn.de/download/55751/55753/2024-08%20Farheen%20-%20JOSA%20B%20-%20Symmetry-protected%20TM%20modes%20in%20rib-like,%20plus-shaped%20optical%20waveguides%20with%20shallow%20etching%20(preprint).pdf)
- Bound-state-in-continuum guided modes in a multilayer EO platform, a related BIC/lateral-leakage mechanism. — [arXiv 2309.13004](https://arxiv.org/pdf/2309.13004); also [arXiv 1810.06734](https://arxiv.org/pdf/1810.06734) ("Ridge resonance", silicon)

### Inferences
- Electrodes on the slab would create a lateral Fabry–Perot or leaky cavity between the ridge edge and the metal edge. Leakage launched into the slab then interferes, and the period is set by the slab-mode lateral wavevector (period ≈ λ / (2·sqrt(n_slab² − n_eff²))-type relation). This is the Webster-type mechanism applied to a metal boundary. It is my synthesis; no paper states it.

### Gaps
- I found no paper on metal contacts on the slab causing resonant or oscillatory loss vs contact distance, in either silicon modulators or TFLN.
- I found no measurement of insertion loss vs lithographic misalignment of the electrode edge.
