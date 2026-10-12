# Plasmonic / hybrid-plasmonic waves on metal–thin-dielectric stacks and their Fabry-Perot resonances

## Verification method and limits
Crossref (api.crossref.org) could not be reached from this environment: the proxy returned 403 and WebFetch got a DNS failure. Each citation was therefore checked with web search against publisher, DOI-resolver or repository records, and against reference lists in other papers. Each entry is marked:
- VERIFIED: the bibliographic data and DOI were seen in a publisher, doi.org or repository record.
- PARTIAL: the bibliographic data was confirmed but the DOI was not seen. A DOI that follows the publisher's standard pattern is labelled "pattern-derived, check it".
- UNVERIFIED: not found.

## Our case (reference)
- Structure: Au electrode / 275 nm LN slab / SiO2 BOX, at 1575 nm.
- Mode: a TM-like hybrid wave with n_eff ~2.07.
- Field components: Ey (normal to the metal) dominates. Ez and Ex are the in-plane components; how they split depends on the propagation direction. Ex is about 8 dB below Ez.
- Resonance: the wave reflects at the end of the gold–LN overlap and forms standing waves. The Ex nulls are shifted a quarter period relative to the Ey/Ez nulls.

## 1. Hybrid plasmonic mode (metal / thin dielectric / high-index)
**Oulton, R. F., Sorger, V. J., Genov, D. A., Pile, D. F. P., Zhang, X., "A hybrid plasmonic waveguide for subwavelength confinement and long-range propagation," Nature Photonics 2(8), 496–500 (2008). DOI 10.1038/nphoton.2008.131. VERIFIED** (Wikipedia/Imperial Spiral record and several citing papers. Accepted manuscript: spiral.imperial.ac.uk/handle/10044/1/19117.)
- What it shows: a high-index cylinder separated from a metal by a thin low-index gap. The SPP and the dielectric mode couple into a hybrid mode. Its field is concentrated in the low-index gap and is mainly the component normal to the metal (E-normal). Propagation stays long while confinement is subwavelength.
- Mapping to our case: our stack (Au / LN with n~2.1–2.2, possibly with an SiO2 or air interface) is a planar relative of this structure. A dominant Ey normal to the metal and n_eff ~2.07, just below the LN index, are what one expects for a TM-like hybrid mode that is mostly dielectric-like. The Oulton geometry places the low-index layer between the metal and the high-index layer. If our stack has no buffer layer, the mode is closer to a "dielectric-loaded SPP / TM0 of a metal-clad slab" than to the textbook gap-hybrid mode. This should be stated explicitly.

## 2. Fabry-Perot resonances of plasmonic waves (reflection at terminations)
**Ditlbacher, H., Hohenau, A., Wagner, D., Kreibig, U., Rogers, M., Hofer, F., Aussenegg, F. R., Krenn, J. R., "Silver nanowires as surface plasmon resonators," Phys. Rev. Lett. 95, 257403 (2005). DOI 10.1103/PhysRevLett.95.257403. VERIFIED** (doi.org record. The full author list is from memory; only "Ditlbacher et al." was confirmed.)
- What it shows: Ag nanowires about 100 nm in diameter support SPP modes whose wavelength is about half the excitation wavelength. The wire ends reflect the SPP with a reflectivity of about 25%. The wires act as SPP Fabry-Perot resonators, confirmed by scattered-light spectra and by near-field imaging of standing-wave patterns.
- Mapping to our case: this is the direct precedent for a metal-bound wave reflecting at an abrupt termination and forming standing waves. It supports treating the gold–LN overlap edge as a partially reflecting mirror with a non-trivial reflection phase. That phase sets the absolute positions of the nulls, but not the λ/(2 n_eff) period.

**Kuttge, M., Vesseur, E. J. R., Polman, A., "Fabry-Perot resonators for surface plasmon polaritons probed by cathodoluminescence," Appl. Phys. Lett. 94, 183104 (2009). PARTIAL** (AMOLF record. DOI not seen; no DOI is given here.)
- What it shows: SPP cavities formed between two FIB-milled grooves in single-crystal Au. Mode numbers up to 10 were resolved. Q reaches 21 at a groove depth of 100 nm and λ = 690 nm. Mirror reflectivity, and so Q, depends strongly on the termination geometry.
- Mapping to our case: standing-wave orders are imaged directly. The termination geometry sets the reflection magnitude, so the edge profile and slope of the electrode set the contrast of our standing waves.

**Dionne, J. A., Sweatlock, L. A., Atwater, H. A., Polman, A., "Plasmon slot waveguides: Towards chip-scale propagation with subwavelength-scale localization," Phys. Rev. B 73, 035407 (2006). PARTIAL** (AMOLF and Caltech records. DOI 10.1103/PhysRevB.73.035407 is pattern-derived; check it.)
- What it shows: dispersion of Ag/SiO2/Ag MIM modes for core thicknesses of 12–250 nm. Propagation reaches tens of µm while confinement is about 20 nm. This is the field-profile basis for MIM Fabry-Perot resonators.
- Mapping to our case: a reference for how the TM field components (normal E dominant, longitudinal E weaker and 90° out of phase) behave in metal–dielectric guides.

**Bozhevolnyi, S. I., Søndergaard, T., "General properties of slow-plasmon resonant nanostructures: nano-antennas and resonators," Optics Express 15, 10869–10877 (2007). PARTIAL** (seen only in a citing reference list. The DOI would be 10.1364/OE.15.010869, pattern-derived and unverified.)
- What it shows: a Fabry-Perot model of finite plasmonic strips. The resonance condition is 2·k_SPP·L + 2φ_r = 2πm, where φ_r is the phase of the end reflection.
- Mapping to our case: this is the formula to fit our null positions with. The extracted φ_r gives the end-reflection phase at the gold–LN overlap edge.

**Søndergaard & Bozhevolnyi, "Slow-plasmon resonant nanostructures: scattering and field enhancements," Phys. Rev. B 75, 073402 (2007). UNVERIFIED.** It was not found in search; do not cite it without checking.

**Gordon, R., "Light in a subwavelength slit in a metal: propagation and reflection," Phys. Rev. B 73, 153405 (2006). UNVERIFIED.** Only related UVic work by Gordon on slit reflection phase, including the effect of loss on the reflection phase, was found. Do not cite until checked.

**Weeber, J.-C., Krenn, J. R., Dereux, A., et al., "Near-field observation of surface plasmon polariton propagation on thin metal stripes," Phys. Rev. B 64, 045411 (2001). PARTIAL / UNVERIFIED.** Citing papers refer to Weeber et al. 2001 PSTM imaging of SPPs on stripes, including propagation length versus stripe width. The exact title, volume and pages were not confirmed.

## 3. Thin metal films / IMI, long-range vs short-range (buffer-layer question)
**Berini, P., "Plasmon-polariton waves guided by thin lossy metal films of finite width: Bound modes of symmetric structures," Phys. Rev. B 61(15), 10484 (2000). PARTIAL** (citations in several patents agree on 10484; one gives 10454. The DOI 10.1103/PhysRevB.61.10484 is pattern-derived.)
**Berini, P., companion paper on asymmetric structures, Phys. Rev. B 63, 125417 (2001). PARTIAL** (title not seen in full).
- What they show: the mode families of a finite-width metal stripe, including long-range (symmetric) and short-range (asymmetric) modes. A cladding asymmetry, such as LN above and SiO2 below, pushes the long-range mode toward cutoff.
- Mapping to our case: an asymmetric index environment (LN vs SiO2 vs air) has the same effect. It decides whether a metal-bound wave is well bound or close to cutoff. A low-index buffer between the Au and the LN would move the mode toward the Oulton gap-hybrid regime.

## 4. Oblique propagation / field-component decomposition at an edge
**Peng, S. T., Oliner, A. A., "Guidance and leakage properties of a class of open dielectric waveguides: Part I—Mathematical formulations," IEEE Trans. Microwave Theory Tech. MTT-29(9), 843–855 (1981). PARTIAL** (several reference lists agree. The DOI was not seen; IEEE's would be of the form 10.1109/TMTT.1981.1130465, which is unverified, so check it.)
**Oliner, A. A., Peng, S. T., Hsu, T. I., Sanchez, A., "… Part II—New physical effects," same issue, 855–869 (1981). PARTIAL.**
- What they show: a slab TM/TE mode hitting a step or edge at an oblique angle is decomposed into components parallel and perpendicular to the edge. Polarization conversion and lateral leakage appear once the transverse wavenumber exceeds the cutoff of the other polarization.
- Mapping to our case: this is the formal basis for splitting the in-plane E into Ez and Ex according to propagation direction. It also explains why Ex, the component tangential to the reflecting edge, has a different reflection phase from Ey and Ez. A difference of about π/2 in the effective reflection phase shifts its standing-wave nulls by a quarter period (λ/(4 n_eff)). For a propagating TM wave, Ez (longitudinal) is in quadrature with Ey, so in a standing wave the longitudinal-component nulls sit at the maxima of the normal component. This is textbook behaviour (from Maxwell: E_long ∝ ∂H/∂normal ... ∝ i·k·E_normal-type relation). Check carefully which of our components is "longitudinal" relative to the standing-wave axis.
- Not found: a peer-reviewed paper that measures a quarter-period shift between components in an SPP standing wave. The searches here did not turn one up.

## Gaps / to do
- Run Crossref checks from an unrestricted machine for every PARTIAL DOI.
- Gordon PRB 2006, Søndergaard PRB 2007 and Weeber PRB 2001 still need full verification.
- Marcuse (oblique slab modes) was not searched.
- No source was found that specifically treats Au on thin LN. The closest are LN-on-insulator electro-optic modulator papers, which are outside this scope.
