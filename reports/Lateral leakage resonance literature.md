# Rib-edge leakage theory explains the gold-electrode resonance

The literature supports every one of our FEM observations through mechanisms that are already published, but **no published paper puts these mechanisms together for a metal electrode sitting directly on a TFLN slab**. That combined explanation is our own synthesis. Results (a), (b) and (d) follow from standard textbook guided-wave and plasmonics theory: Snyder & Love, Okamoto and Maier Ch. 2. Result (c) is a direct analogue of the Oliner–Peng theory of polarization-converting lateral leakage (1981) and the SOI "magic width" experiments (Webster et al. 2007). In those works the quasi-TE/TM guided mode leaks into a slab wave of the other polarization whose index is higher, and interference between leaked waves produces loss that oscillates with geometry. Our case differs in two ways. The higher-index wave is a TM-like wave bound to the gold (n≈2.07), and the interfering reflections come from the end of the gold–LN overlap rather than from the two rib edges. A quick check confirms the observed period: with n_eff=1.884 and n_lat=2.07 at 1575 nm, k_x = k0·√(2.07²−1.884²) gives **λ_x ≈ 1.84 µm and λ_x/2 ≈ 0.92 µm**, which matches the ~0.9 µm FP period (our calculation). Result (e) has direct TFLN precedent: about 100 nm of SiO2 cuts electrode loss by more than 100×. Result (f), robustness on a real chip, has **no dedicated published study**. The nearest evidence is Koshiba's finding that leakage minima are narrow and have low tolerance. So the oscillation should be treated as a fragile simulation feature, not as something to design around.

## Verification status and how to read this report

None of the research sessions could reach Crossref or doi.org directly. Each citation was checked against publisher, repository or catalog records found by web search. The labels mean the following. **VERIFIED**: the bibliographic data and DOI were seen in an independent record. **PARTIAL**: the bibliographic data was confirmed but the DOI was not, or the DOI came only from a search summary or a URL pattern. **UNVERIFIED**: the citation comes from memory or was not found. Where the notes disagreed, the lower status is used. Textbook chapter numbers are almost all unverified, because the publishers' table-of-contents pages could not be reached. Check them against a physical copy before citing. **No DOI listed below was invented.** DOIs marked "not confirmed" must be checked on Crossref before publication.

## Annotated bibliography grouped by topic

### A. Textbooks: guided-mode fundamentals and field components

| Source | Status | Chapters (status) | Why it matters for us |
|---|---|---|---|
| Snyder & Love, *Optical Waveguide Theory*, Chapman & Hall 1983, ISBN 0-412-09950-0 ([Springer](https://link.springer.com/book/9780412099502)) | VERIFIED (biblio) | Ch. 11 weak guidance; Ch. 12 hybrid modes; Ch. 13 non-circular guides; Ch. 24–25 leaky/radiation modes; Ch. 30 exact field relations (all chapter numbers UNVERIFIED) | Shows that Ez is in quadrature with Et and scales with index contrast. This explains (a). |
| Okamoto, *Fundamentals of Optical Waveguides*, 2nd ed., Academic Press 2006, ISBN 978-0-12-525096-2 ([BL](https://eld.bl.uk/catalog/017701882)) | VERIFIED (biblio) | Ch. 1 wave theory, Ez from transverse fields; Ch. 2 slab, Marcatili, EIM; Ch. 6 FEM (UNVERIFIED numbers) | Best engineering-level derivation of (a) and (b). Also covers the FEM background. |
| Chuang, *Physics of Photonic Devices*, 2nd ed., Wiley 2009, ISBN 978-0-470-29319-5 ([Wiley-VCH](https://www.wiley-vch.de/en/areas-interest/engineering/physics-of-photonic-devices-978-0-470-29319-5)) | VERIFIED (biblio) | Ch. 7 waveguide theory; Ch. 8 coupled modes (UNVERIFIED) | Accessible treatment of slab TE/TM modes, evanescent decay and EIM. |
| Collin, *Field Theory of Guided Waves*, 2nd ed., IEEE Press 1991, ISBN 0-87942-237-8 ([Wiley-VCH](https://www.wiley-vch.de/de/fachgebiete/ingenieurwesen/field-theory-of-guided-waves-978-0-87942-237-0)) | VERIFIED (biblio) | Ch. 3 TEM; Ch. 6 inhomogeneously filled guides (LSE/LSM, transverse resonance); Ch. 11 surface waveguides (UNVERIFIED) | Rigorous proof that an inhomogeneous cross-section forbids pure TE/TM/TEM modes. Transverse resonance is the formal tool behind (c). |
| Pozar, *Microwave Engineering*, 4th ed., Wiley 2011, ISBN 978-0-470-63155-3 ([Schweitzer](https://www.schweitzer-online.de/en/buch/Pozar/Microwave-Engineering/9780471448785/A28616853/)) | VERIFIED (biblio) | Ch. 3.1 TEM/TE/TM; partially loaded guide and transverse resonance (~§3.9, UNVERIFIED) | Shortest clear route to TEM vs TE/TM, and to standing waves with complex reflection. |
| Marcuse, *Theory of Dielectric Optical Waveguides*, 2nd ed., Academic Press 1991 | UNVERIFIED | Ch. 1–2 slab and radiation modes (UNVERIFIED) | Classic treatment of radiation and leaky modes. |
| Saleh & Teich, *Fundamentals of Photonics* | UNVERIFIED (edition) | Resonator optics chapter | FP condition 2βL+φ1+φ2=2πm. |
| Haus, *Waves and Fields in Optoelectronics* (1984); Tamir (ed.), *Integrated Optics* (Kogelnik Ch. 2); Pollock & Lipson, *Integrated Photonics* | UNVERIFIED | — | Optional alternatives. Search returned nothing to confirm them. |

### B. Textbooks and papers: plasmonic and hybrid metal-bound waves

| Source | Status | Notes |
|---|---|---|
| Maier, *Plasmonics: Fundamentals and Applications*, Springer 2007, ISBN 978-0-387-33150-8 ([Springer](https://link.springer.com/978-0-387-37825-1)) | VERIFIED (biblio and chapter titles) | Ch. 2 SPPs at metal/insulator interfaces: SPPs exist only as TM; field-ratio expressions; IMI/MIM multilayers (subsection numbers UNVERIFIED). Ch. 7 plasmon waveguides. Core reference for (c) and (d). |
| Novotny & Hecht, *Principles of Nano-Optics*, 2nd ed., CUP 2012, ISBN 978-1-107-00546-4 ([CUP](https://assets.cambridge.org/97811070/05464/copyright/9781107005464_copyright_info.pdf)) | VERIFIED (biblio); chapter number UNVERIFIED | Has a "Plasmonics" chapter with explicit SPP field components. |
| Raether, *Surface Plasmons on Smooth and Rough Surfaces and on Gratings*, Springer 1988 | UNVERIFIED | Relevant to roughness scattering (f). |
| Oulton et al., "A hybrid plasmonic waveguide…," Nat. Photon. 2, 496 (2008), DOI 10.1038/nphoton.2008.131 | VERIFIED | Hybrid SPP–dielectric mode. The normal E component dominates. Caveat: Oulton's structure has a low-index gap, and our unbuffered case does not. Our wave is closer to the TM0 mode of a metal-clad slab. |
| Ditlbacher et al., "Silver nanowires as surface plasmon resonators," PRL 95, 257403 (2005), DOI 10.1103/PhysRevLett.95.257403 | VERIFIED (DOI); full author list PARTIAL | Precedent for a metal-bound wave reflecting at an abrupt end (~25% reflectivity) and forming FP standing waves. |
| Kuttge, Vesseur, Polman, APL 94, 183104 (2009) | PARTIAL (no DOI) | SPP FP cavities. The termination geometry sets mirror reflectivity and Q. Relevant to (f). |
| Dionne et al., PRB 73, 035407 (2006) | PARTIAL (DOI pattern-derived, not confirmed) | MIM mode dispersion and field profiles. |
| Bozhevolnyi & Søndergaard, Opt. Express 15, 10869 (2007) | PARTIAL (DOI not confirmed) | FP condition 2k·L+2φ_r=2πm with end-reflection phase. Use it to fit our null positions. |
| Berini, PRB 61, 10484 (2000); PRB 63, 125417 (2001) | PARTIAL | Metal-stripe mode families. Cladding asymmetry controls how strongly the mode is bound. |
| Gordon PRB 73, 153405 (2006); Søndergaard & Bozhevolnyi PRB 75, 073402 (2007); Weeber et al. PRB 64, 045411 (2001) | UNVERIFIED | Do not cite until checked. |

### C. Lateral leakage, polarization conversion and geometric loss oscillations

| Source | Status | Notes |
|---|---|---|
| Peng & Oliner, "Guidance and leakage properties of a class of open dielectric waveguides: Part I — Mathematical formulations," IEEE T-MTT 29(9), 843–855 (1981) ([record](https://iris.uniroma1.it/handle/11573/244593)) | PARTIAL (DOI not confirmed) | Foundational. At a step, a guided mode converts into the slab surface wave of the other polarization. It leaks when that wave's index is higher. Phase matching sets the leakage angle. |
| Oliner, Peng, Hsu & Sanchez, "… Part II — New physical effects," same issue, 855–869 ([record](https://iris.uniroma1.it/handle/11573/241716)) | PARTIAL | Leakage oscillates with strip width and cancels at specific widths. This is the conceptual parent of (c). |
| Webster, Pafchek, Mitchell, Koch, IEEE PTL 19(6), 429–431 (2007) ([Arizona](https://experts.arizona.edu/en/publications/width-dependence-of-inherent-tm-mode-lateral-leakage-loss-in-sili/)) | PARTIAL (DOI 10.1109/LPT.2007.891979 reported by one search summary only; the notes disagree) | First optical observation of sharp cyclic loss minima ("magic widths"). Notes that the effect is inherent where lateral electrical access is needed. |
| Nguyen, Tummidi, Koch, Mitchell, IEEE PTL 21(7), 486–488 (2009), DOI 10.1109/LPT.2009.2013965 ([RMIT](https://research-repository.rmit.edu.au/articles/journal_contribution/Rigorous_modeling_of_lateral_leakage_loss_in_SOI_thin-ridge_waveguides_and_couplers/27433650)) | VERIFIED | Rigorous mode-matching model of lateral leakage. |
| Kakihara, Saitoh, Koshiba, JLT 27(23), 5492–5499 (2009), DOI 10.1109/JLT.2009.2027720 ([HUSCAP](https://eprints.lib.hokudai.ac.jp/dspace/handle/2115/39952)) | VERIFIED (one note: PARTIAL on title) | Simple theory. Minima are narrow, with low width and wavelength tolerance. The main evidence for (f). |
| Koshiba, Kakihara, Saitoh, Opt. Lett. 33, 2008 (2008) | PARTIAL (no DOI) | Reduced TM-like leakage designs. |
| Dalvand et al., Opt. Express 19(6), 5635 (2011), DOI 10.1364/OE.19.005635 ([Arizona](https://experts.arizona.edu/en/publications/thin-ridge-silicon-on-insulator-waveguides-with-directional-contr/)) | VERIFIED | Engineered interference of leaked waves. The closest analogue of a designed lateral cavity. |
| Mitchell/Nguyen et al., "magic radius" in bends and rings, Opt. Express 2010 ([Arizona](https://experts.arizona.edu/en/publications/lateral-leakage-of-tm-like-mode-in-thin-ridge-silicon-on-insulato/)) | PARTIAL (no vol./DOI) | The oscillation persists in curved geometry. |
| Boes et al., "Improved second harmonic performance in periodically poled LNOI waveguides through engineering of lateral leakage," Opt. Express 27, 23919 (2019); arXiv:1906.02383 ([arXiv](https://arxiv.org/pdf/1906.02383)) | PARTIAL (DOI not confirmed) | In LNOI, birefringence lets the **TE** mode leak into TM slab waves. This is the TFLN precedent for TE→TM leakage. |
| Yu et al., "Photonic integrated circuits with bound states in the continuum," Optica 6(10), 1342 (2019), DOI 10.1364/OPTICA.6.001342 ([HKU](https://hub.hku.hk/handle/10722/351392)) | VERIFIED | BIC (leakage-cancelling) waveguides on LN. |
| Čtyroký & Petráček, comment, Optica 9(7), 681 (2022), DOI 10.1364/OPTICA.457746 | VERIFIED | Disputes the EO efficiency claimed in Yu et al. |
| Mitchell group, SPIE 11689, 116890O (2021), DOI 10.1117/12.2587988 ([SPIE](https://www.spiedigitallibrary.org/conference-proceedings-of-spie/11689/116890O/Harnessing-polarisation-in-lithium-niobate-on-insulator-integrated-optics/10.1117/12.2587988.full)) | PARTIAL (DOI from URL) | Polarization conversion causes leakage of both TE and TM in LNOI. |
| Farheen et al., "plus-shaped" symmetry-protected TM modes, JOSA B preprint ([PDF](https://ris.uni-paderborn.de/download/55751/55753/2024-08%20Farheen%20-%20JOSA%20B%20-%20Symmetry-protected%20TM%20modes%20in%20rib-like,%20plus-shaped%20optical%20waveguides%20with%20shallow%20etching%20(preprint).pdf)) | PARTIAL | Uses symmetry to suppress leakage. |

### D. Electrode-induced loss and buffers in LN modulators

| Source | Status | Notes |
|---|---|---|
| Zhu et al., "Integrated photonics on thin-film lithium niobate," Adv. Opt. Photon. 13(2), 242 (2021), DOI 10.1364/AOP.411024 ([NSF PAR](https://par.nsf.gov/biblio/10225637)) | VERIFIED | Review. Background on the gap vs loss trade-off. |
| Boes et al., "Lithium niobate photonics: Unlocking the electromagnetic spectrum," Science 379, eabj4396 (2023), DOI 10.1126/science.abj4396 | VERIFIED | Review. |
| Liu et al., Chin. Opt. Lett. 19(6), 060016 (2021), DOI 10.3788/COL202119.060016 ([PDF](https://www.researching.cn/ArticlePdf/m00005/2021/19/6/060016.pdf)) | VERIFIED (details from search summary) | 100 nm SiO2 cuts metal loss by **>100×** (<0.1 dB/cm at 3 µm gap). Attributes the steep gap dependence to coupling into surface-plasmon modes at the metal–LN interface. The strongest single support for (b), (c) and (e). |
| Kharel et al., Optica 8(3), 357 (2021); arXiv:2011.13422 ([ar5iv](https://ar5iv.labs.arxiv.org/html/2011.13422)) | PARTIAL (DOI not confirmed) | Capacitively loaded electrodes allow small gaps. |
| Wang et al., Nature 562, 101 (2018) | UNVERIFIED (DOI from memory, not given) | Landmark TFLN modulator. |
| Wooten et al., IEEE JSTQE 6(1), 69 (2000) ([ref list](https://www.researching.cn/articles/OJ9d03e04e9a0ee503/referenceandcitations)) | PARTIAL | Bulk Ti:LN review. Buffer layers are standard. |
| Marcuse, "Optimal electrode design for integrated optics modulators," IEEE JQE 18(3), 393 (1982) | PARTIAL | Classic electrode-design trade-offs. |
| Preprints: arXiv [2411.15037](https://arxiv.org/pdf/2411.15037), [2207.02608](https://arxiv.org/pdf/2207.02608), [2201.10790](https://arxiv.org/pdf/2201.10790), [2505.23632](https://arxiv.org/pdf/2505.23632) | PARTIAL (journal versions not checked) | Monotonic loss rise as the gap shrinks. Buffer reduces loss about 100×. Mid-IR case blames plasmonic absorption. |

### E. FEM methodology

Jin, *The Finite Element Method in Electromagnetics*, 3rd ed., Wiley-IEEE 2014, ISBN 978-1-118-57136-1 ([O'Reilly](https://www.oreilly.com/library/view/-/9781118571361/)): VERIFIED biblio, waveguide-eigenproblem chapter UNVERIFIED. Lee, Sun & Cendes, IEEE T-MTT 39(8), 1262–1271 (1991) ([cited in](https://arxiv.org/pdf/1603.03791)): PARTIAL, no DOI. These two justify the Nédélec-Et plus Lagrange-Ez formulation used by femwell. They also explain why our Ez is computed separately and is free of spurious modes.

## Result-by-result mapping to sources

| Result | Best support | Strength | Our own reasoning (not in any source) |
|---|---|---|---|
| (a) Ez at 90°, odd in x | Snyder & Love Ch. 11/30; Okamoto Ch. 1 | **Strong, textbook** | Ez = (−j/β)∇t·(εEt)/ε follows from Gauss's law. The −j gives quadrature. An even Ex makes ∂x(εEx) odd. The ratio Ez/Ex ≈ 0.2 is consistent with high contrast. This is a standard derivation applied to our geometry. |
| (b) IL ∝ exp(−3.3·gap) | Okamoto Ch. 2, Chuang Ch. 7 (evanescent γ); Liu 2021 and TFLN preprints (steep monotonic gap dependence) | **Strong qualitatively.** No paper reports a fitted exponent. | Loss ∝ \|field at metal\|², which decays as exp(−2γ·gap). Here γ is the lateral decay in the slab region, γ = k0√(n_eff²−n_slab,TE²). An exponent of 3.3 µm⁻¹ implies an equivalent slab TE index of about 1.83–1.84. This is plausible for a 275 nm LN slab but has not been checked. |
| (c) Leakage into TM-like metal-bound wave (n≈2.07), lateral FP, period ≈0.9 µm | Peng & Oliner 1981; Webster 2007; Kakihara 2009; Boes 2019 (TE→TM in LNOI); Maier Ch. 2; Ditlbacher 2005 and Bozhevolnyi 2007 (FP of plasmonic waves); Liu 2021 (plasmon coupling cited as loss cause) | **Mechanism analogous; specific configuration unpublished** | The phase-matching period λ_x/2 = λ/(2√(n_lat²−n_eff²)) ≈ 0.92 µm is our calculation. **No paper reports FP oscillation of IL versus gold–LN overlap length.** |
| (d) Ey, Ez strong; Ex ~8 dB below Ez; Ex nulls shifted λ/4 | Maier Ch. 2 (TM SPP: normal plus longitudinal components, in quadrature); Peng & Oliner (oblique decomposition at an edge) | **Partial** | Our reading: the lateral wave travels obliquely, at an angle whose cosine is about n_eff/n_lat (≈24° off the z-axis). Its in-plane E splits into Ez (large) and Ex (small). Ex is the component normal to the reflecting end. As the longitudinal component of the standing wave, it sits in quadrature, so its nulls fall at the maxima of Ey. **No source measures this quarter-period shift.** The −8 dB ratio needs a projection check against the angle: tan²(24°) ≈ −7 dB, which is consistent but not proven. |
| (e) 200 nm SiO2 suppresses loss | Liu 2021 (>100× with 100 nm); arXiv 2411.15037; Wooten 2000 (bulk-LN practice); Oulton 2008 and Berini (low-index layer changes the metal-bound mode) | **Strong** | The buffer adds an evanescent barrier. It also lowers the index of the metal-bound mode below 1.884, which removes the phase-matching condition. The second effect is our hypothesis and should be checked by computing the buffered metal-mode index. |
| (f) Robustness on real chip | Kakihara 2009 (narrow minima); Kuttge 2009 (edge geometry sets reflectivity); Raether (roughness) | **Weak. No direct study.** | The period is set by k_x and is robust. The phase of the oscillation, and especially its contrast, depend on the reflection at the gold end. Edge tilt, roughness, misalignment, gold loss and wavelength all degrade or shift that reflection. Expect the average leakage loss to survive while the oscillation washes out. |

## Explicit gaps in the published record

Four claims have no published source. The first is that a gold electrode placed directly on a TFLN slab hosts a TM-like wave with an index above the quasi-TE rib mode, and so causes Oliner-type leakage. Liu 2021 points at "surface-plasmon coupling" but does not give a phase-matching analysis. The second is any measured or simulated oscillation of insertion loss versus electrode overlap length or edge position, in TFLN or in silicon modulators. The third is a quarter-period shift between field components in a plasmonic standing wave. The fourth is any study of how sidewall angle, roughness or lithographic misalignment affects lateral-leakage oscillations. Everything in the right-hand column of the mapping table is our reasoning. That includes the 0.92 µm period check, the slab-index reading of the 3.3 µm⁻¹ exponent, the oblique-projection account of Ex, and the expectation that contrast washes out on real chips. The cheapest validation steps are these: compute the buffered metal-bound mode index; sweep wavelength to confirm that the period scales as λ/(2√(n_lat²−n_eff²)); and add an edge tilt or a lossy rough edge in FEM to see how the contrast responds.

## Prioritized reading plan for re-learning guided-mode physics

| Order | Reading | Goal | Approx. effort |
|---|---|---|---|
| 1 | Pozar Ch. 3 (opening sections and partially loaded guide) | TEM vs TE/TM. Why TEM needs two conductors and a homogeneous medium. Transverse resonance. | 1 day |
| 2 | Okamoto Ch. 1–2 | Maxwell in waveguide form, Ez from Et, slab TE/TM, evanescent γ, Marcatili/EIM, meaning of quasi-TE (E^x_pq) | 2–3 days |
| 3 | Snyder & Love Ch. 11–13, then Ch. 30 | Weak-guidance expansion, the order of magnitude and phase of Ez, why all rib modes are hybrid | 2–3 days |
| 4 | Saleh & Teich resonator chapter, plus revisit Pozar on standing waves | Travelling vs standing waves; FP condition with complex mirror phase | 1 day |
| 5 | Maier Ch. 2 (then Ch. 7) | TM-only SPPs, field ratios, IMI/MIM; the metal-bound wave in (c) and (d) | 2 days |
| 6 | Collin Ch. 6 and 11 | Rigorous LSE/LSM picture for inhomogeneous guides; surface waves | optional, 2 days |
| 7 | Peng & Oliner Part II, then Webster 2007 and Kakihara 2009, then Boes 2019 | Lateral leakage, magic widths, tolerance, TFLN-specific TE leakage | 2 days |
| 8 | Liu 2021 COL, then Zhu 2021 review §§ on modulators | Electrode loss and buffers in practice | 1 day |
| 9 | Jin 3rd ed. waveguide chapter; Lee/Sun/Cendes 1991 | Why the FEM formulation gives trustworthy Ez | optional |

## Conclusion

The defensible framing for a report or paper has two parts. First, our quasi-TE mode experiences **metal-induced Oliner–Peng lateral leakage**: the gold turns the slab under it into a host for a TM-like wave of higher index. Second, the IL oscillation is the length-domain counterpart of the magic-width effect, with the gold–LN overlap end acting as the second "edge". Both ingredients are well sourced, but the combination is new and should be presented as our interpretation. Pin it down with the wavelength-scaling test before claiming it.

For design, the practical lesson is to use the buffer and not chase resonance minima. Published tolerance data on magic widths show that minima are narrow. A real gold edge, with its tilt, grain roughness and alignment error, will reduce mirror contrast. The 200 nm SiO2 buffer removes the phase-matching condition entirely, and TFLN practice shows it costs little.
