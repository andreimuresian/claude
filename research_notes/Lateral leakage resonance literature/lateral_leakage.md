# Lateral leakage of rib/ridge modes into slab modes of the other polarisation, and loss oscillations versus geometry

Verification note: Crossref, doi.org, arxiv.org and experts.arizona.edu could not be reached directly from this sandbox (the proxy returned 403 or DNS failed). The citations below were checked against web-search snippets of publisher, repository and institutional records. Each DOI is tagged as either VERIFIED-VIA-SEARCH (seen in a repository or publisher record) or UNVERIFIED (not seen anywhere, so not given). None of the DOIs were checked against Crossref itself, so do one Crossref pass before publishing.

## Q1: Oliner/Peng et al. 1981 (IEEE MTT), Parts I and II

### Takeaway
The two papers are real, but the author lists differ between the parts. Part I is by Peng and Oliner only. Part II is by Oliner, Peng, Hsu and Sanchez. They set out the foundational theory: at a rib edge, a guided mode of one polarisation converts into the slab surface wave of the other polarisation. When that slab wave has a higher effective index than the guided mode, the mode becomes leaky. The leakage angle obeys a phase-matching condition, and destructive interference between radiation from the two edges gives near-zero leakage at particular widths.

### Cited Findings
- Part I: S.-T. Peng, A. A. Oliner, "Guidance and leakage properties of a class of open dielectric waveguides: Part I — Mathematical formulations," IEEE Trans. Microwave Theory Tech., vol. MTT-29, no. 9, pp. 843–855, Sept. 1981 — [iris.uniroma1 record / search](https://iris.uniroma1.it/handle/11573/244593)
- Part II: A. A. Oliner, S.-T. Peng, T.-I. Hsu, A. Sanchez, "... Part II — New physical effects," IEEE Trans. MTT, vol. MTT-29, no. 9, pp. 855–869, Sept. 1981 — [same search](https://iris.uniroma1.it/handle/11573/241716)
- DOI: UNVERIFIED. My recollection is 10.1109/TMTT.1981.1130466 / ...1130467 or similar, but I could not confirm it, so it is withheld. Look it up on IEEE Xplore using vol. 29, no. 9, p. 843 / p. 855.
- Content (from general knowledge of the papers, not re-read in full text here): the analysis uses a rigorous mode-matching/transverse-resonance treatment of a strip/rib on a slab. A TE-like guided mode couples to the slab TM surface wave at the step discontinuities, and vice versa. Leakage happens when the guided mode's β is smaller than the β of the slab mode of the other polarisation. The leakage constant varies periodically with strip width, and at certain widths it falls to zero (cancellation of the waves leaking from the two edges).

### Inferences
- This maps directly onto our case. Our quasi-TE rib mode (n_eff below the TM-like gold-loaded slab index) meets exactly the Oliner leakage condition. The leaked wave travels at angle θ given by cos θ = n_rib/n_slab,TM, so its lateral wavevector is k_x = k0·sqrt(n_slab² − n_rib²). A Fabry-Perot in a region of length L along x then has resonances with period ΔL = π/k_x = λ_x/2, consistent with the observed ~0.9 µm.

### Gaps
- No full text or DOI was obtained for either part.

## Q2: Webster, Pafchek, Koch et al. — "magic widths"

### Takeaway
The 2007 IEEE PTL paper exists. Its authors are Webster, Pafchek, Mitchell and Koch; the "Sukumaran" in the brief appears to be a mix-up. It reports the first optical observation of strongly width-dependent TM-like lateral leakage loss in SOI ridges, with sharp cyclic minima ("magic widths") at particular widths. Follow-up work by the same group and by Koshiba's group developed the theory, extended it to bends and rings ("magic radius"), and quantified tolerance.

### Cited Findings
- M. A. Webster, R. M. Pafchek, A. Mitchell, T. L. Koch, "Width dependence of inherent TM-mode lateral leakage loss in silicon-on-insulator ridge waveguides," IEEE Photon. Technol. Lett. 19(6), 429–431 (2007). DOI UNVERIFIED. Shows sharp cyclic loss minima versus width, which effective-index methods do not predict. The authors say the effect is inherent to geometries that need lateral electrical access — [Arizona experts record](https://experts.arizona.edu/en/publications/width-dependence-of-inherent-tm-mode-lateral-leakage-loss-in-sili/), [CiNii](https://cir.nii.ac.jp/crid/1361418520655615488)
- Webster et al., APL 2005 (low-loss quasi-planar ridge waveguides): NOT FOUND or verified in this pass.
- T. G. Nguyen, R. S. Tummidi, T. L. Koch, A. Mitchell, "Rigorous modeling of lateral leakage loss in SOI thin-ridge waveguides and couplers," IEEE PTL 21(7), 486–488 (2009), DOI 10.1109/LPT.2009.2013965 (VERIFIED-VIA-SEARCH, RMIT/Arizona records). Uses mode matching with a laterally open window — [RMIT](https://research-repository.rmit.edu.au/articles/journal_contribution/Rigorous_modeling_of_lateral_leakage_loss_in_SOI_thin-ridge_waveguides_and_couplers/27433650)
- K. Kakihara, K. Saitoh, M. Koshiba, "Generalized simple theory for estimating lateral leakage loss behavior in silicon-on-insulator ridge waveguides," J. Lightwave Technol. 27(23), 5492–5499 (2009), DOI 10.1109/JLT.2009.2027720 (VERIFIED-VIA-SEARCH, Hokkaido repository). Says the loss minimum occurs only at a specific width, with small tolerance to width and wavelength. Proposes a ridge with a dimple for a low-loss, tolerant design — [HUSCAP](https://eprints.lib.hokudai.ac.jp/dspace/handle/2115/39952)
- M. Koshiba, K. Kakihara, K. Saitoh, "Reduced lateral leakage losses of TM-like modes in silicon-on-insulator ridge waveguides," Opt. Lett. 33, 2008–2010 (2008). DOI UNVERIFIED — [cited in HUSCAP search result](https://eprints.lib.hokudai.ac.jp/dspace/handle/2115/39952)
- Mitchell/Nguyen et al., "Lateral leakage of TM-like mode in thin-ridge SOI bent waveguides and ring resonators," Opt. Express (2010). Shows that both radius and width set the leakage, with low-loss width–radius combinations ("magic radius"). Volume, pages and DOI UNVERIFIED — [Arizona record](https://experts.arizona.edu/en/publications/lateral-leakage-of-tm-like-mode-in-thin-ridge-silicon-on-insulato/)
- N. Dalvand, T. G. Nguyen, R. S. Tummidi, T. L. Koch, A. Mitchell, "Thin-ridge silicon-on-insulator waveguides with directional control of lateral leakage radiation," Opt. Express 19(6), 5635–5643 (2011), DOI 10.1364/OE.19.005635 (VERIFIED-VIA-SEARCH). TM guided light emits TE radiation from one side only. The spacing between radiating elements has to be chosen so that the phase and amplitude of the leaked waves stay consistent, which is an explicit interference and cavity-design effect — [Arizona](https://experts.arizona.edu/en/publications/thin-ridge-silicon-on-insulator-waveguides-with-directional-contr/)
- Nguyen, Sekhar, Webster, Koch, Mitchell, "Analysis of lateral leakage loss in SOI thin-rib waveguides," OECC/ACOFT 2008 (conference paper, no DOI found). The "Dalton" in the brief is probably Dalvand — [Arizona](https://experts.arizona.edu/en/publications/analysis-of-lateral-leakage-loss-in-silicon-on-insulator-thin-rib/)

### Inferences
- The magic-width mechanism is two-edge interference of leaked slab waves. Loss is ∝ sin² or cos² of (k_x·W + edge phases), giving a period of about λ_x/2 in width. Our IL oscillation versus the length of the gold-on-slab region is the same physics with the interfering paths moved to the ends of the gold region (reflection at the index step) instead of the rib edges. The period should be λ_x/2, where λ_x is set by the TM-like gold-slab index, not the bare-slab index. Koshiba's finding of narrow minima suggests the oscillation contrast will be sensitive to wavelength and width. Dalvand 2011 is the closest analogue of a designed lateral cavity or array for the leaked wave.

### Gaps
- The 2007 PTL DOI and the APL 2005 paper are unconfirmed. No full texts were read, so numerical loss values are not given.

## Q3: TFLN/LNOI lateral leakage and BIC waveguides

### Takeaway
In LNOI, LN's birefringence lets even the TE mode leak into TM slab modes, mainly in X-cut films. Leakage is more likely with thicker slabs and shorter wavelengths. BIC waveguides (a low-index strip on LN) turn the same two-edge interference into a design tool, giving zero leakage at specific widths.

### Cited Findings
- A. Boes, L. Chang, M. Knoerzer, T. G. Nguyen, J. D. Peters, J. E. Bowers, A. Mitchell, "Improved second harmonic performance in periodically poled LNOI waveguides through engineering of lateral leakage," Opt. Express 27, 23919 (2019). DOI UNVERIFIED (probably 10.1364/OE.27.023919, which matches the OE pattern but was not confirmed); arXiv:1906.02383. Shows TE lateral leakage in X-cut LNOI from birefringence. Avoiding it at the SH wavelength gave about 1160 %W⁻¹cm⁻² — [arXiv](https://arxiv.org/pdf/1906.02383)
- Review statement: for a given rib height, lateral leakage is more likely with a thicker slab or a shorter wavelength — [Photonics 11, 769 (2024), MDPI](https://www.mdpi.com/2304-6732/11/8/769/htm)
- Z. Yu, X. Xi, J. Ma, H. K. Tsang, C.-L. Zou, X. Sun, "Photonic integrated circuits with bound states in the continuum," Optica 6(10), 1342–1348 (2019), DOI 10.1364/OPTICA.6.001342 (VERIFIED-VIA-SEARCH, HKU repository). Uses a low-index strip on LN with geometry tuned so the leakage into the continuum cancels; demonstrates waveguides, rings, couplers and modulators — [HKU](https://hub.hku.hk/handle/10722/351392)
- Comment: J. Čtyroký, J. Petráček, Optica 9(7), 681–682 (2022), DOI 10.1364/OPTICA.457746 (VERIFIED-VIA-SEARCH). Disputes the EO modulation efficiency as more than 10× overstated — [VUT record](https://www.fch.vut.cz/vav/vysledky/detail/178569)
- C.-L. Zou, J.-M. Cui, F.-W. Sun, X. Xiong, X.-B. Zou, Z.-F. Han, G.-C. Guo, "Guiding light through optical bound states in the continuum for ultrahigh-Q microresonators," Laser Photon. Rev. 9, 114–119 (2015). DOI UNVERIFIED — [reference list](https://www.researching.cn/articles/OJ9e7564f3f242140c/referenceandcitations)
- SPIE 11689, 116890O (2021), "Harnessing polarisation in lithium-niobate-on-insulator integrated optics" (Mitchell group). Inherent polarisation conversion causes surprising leakage for both TE and TM — [SPIE](https://www.spiedigitallibrary.org/conference-proceedings-of-spie/11689/116890O/Harnessing-polarisation-in-lithium-niobate-on-insulator-integrated-optics/10.1117/12.2587988.full) (DOI 10.1117/12.2587988 from URL)

### Inferences
- Our 275 nm slab is thick, which favours leakage. The gold changes the slab's TM-like mode (to a plasmonic/hybrid MIM-like wave with raised index), so the TE rib mode falls below it. This is a metal-induced version of the Boes/Mitchell birefringence-induced leakage. The BIC papers suggest that choosing the width of the gold-slab region (or rib–gold gap) at a cancellation condition can suppress the loss, the same lever as magic widths.

### Gaps
- No TFLN paper was found that specifically treats metal-loaded slabs and lateral FP oscillations versus electrode length.

## Q4: Resonant/oscillatory loss from finite slab/trench reflections; robustness

### Takeaway
The oscillatory loss is well documented versus rib width (two-edge interference) and ring radius. Explicit cavity designs for leaked slab waves appear in Dalvand 2011. Tolerance studies (Koshiba 2009) show the minima are narrow. I found no dedicated papers on sidewall angle, roughness or misalignment for this effect.

### Cited Findings
- Narrow minima and low width/wavelength tolerance; a dimple ridge improves tolerance — [Kakihara 2009](https://eprints.lib.hokudai.ac.jp/dspace/handle/2115/39952)
- Spacing of radiating elements sets the coherent build-up of leaked radiation — [Dalvand 2011](https://experts.arizona.edu/en/publications/thin-ridge-silicon-on-insulator-waveguides-with-directional-contr/)
- "Magic radius" in rings — [Arizona](https://experts.arizona.edu/en/publications/magic-radius-phenomenon-in-thin-ridge-soi-ring-resonators-theory-/)
- Thermal oxidation plus magic widths gave 0.94 dB/cm TM loss (Pafchek et al., Applied Optics; details UNVERIFIED) — [Arizona](https://experts.arizona.edu/en/publications/low-loss-silicon-on-insulator-shallow-ridge-te-and-tm-waveguides-/)

### Inferences
- Since the FP period depends only on k_x, sidewall angle and slab thickness changes mainly shift the phase of the oscillation (through the rib/slab n_eff) and barely change its period. Misalignment of the gold edge shifts the effective cavity length directly. These points are expectations, not sourced.

### Gaps
- No peer-reviewed study was found of FP oscillation versus the length of a metal-covered slab segment, or of sidewall-angle and roughness robustness for lateral leakage.
