# Textbooks on guided-mode field physics (TFLN rib waveguide beside gold electrodes)

Verification status: bibliographic data (publisher, year, ISBN) marked [V] was confirmed from catalog/publisher/retailer search results cited inline. Chapter/section numbers marked [U] come from prior knowledge of these books and could NOT be checked: publisher TOC pages (Springer, Elsevier booksite, Wiley) returned DNS errors from this sandbox. Check them against the physical TOC before citing.

## Q1: Longitudinal field component, its formula and the 90 degree phase relation

### Takeaway
The best derivations are Snyder & Love (exact vector field relations and the weak-guidance expansion, where Ez is O(Delta^1/2) and in quadrature with Et) and Okamoto Ch. 1-2 (Ez from Maxwell for the slab and rectangular guides). Ez = (-j/β)(∇t·(εEt))/ε comes from Gauss's law ∇·(εE)=0 with an exp(-jβz) dependence. Because of the -j factor, Ez is 90 degrees out of phase with Et. Its parity is opposite to that of Ex (Ex even, so Ez is odd in x).

### Cited Findings
- Snyder, A. W. & Love, J. D., *Optical Waveguide Theory*, Chapman & Hall, London/New York, 1983, viii+734 pp. ISBN 0-412-09950-0 (hb) / 0-412-24250-8 (pb); Springer reissue e-ISBN 978-1-4613-2813-1 [V]. 40 chapters [V] — [Springer](https://link.springer.com/book/9780412099502), [Altmetric record](https://link.altmetric.com/details/11317963), [UPenn catalog](https://find.library.upenn.edu/catalog/991699543503681)
  - Sections [U]. Ch. 11, "Waveguides with small index differences" (weak-guidance approximation; shows Ez/Et ~ (2Δ)^1/2 with a j factor). Ch. 30, "Exact solutions of Maxwell's equations" (general modal field relations, including Ez from the transverse fields). Ch. 13 covers non-circular / rectangular weakly guiding waveguides. Ch. 12 covers circular fibers and the hybrid HE/EH modes. Note: these chapters explain why the "TE" label is only approximate. Since the longitudinal component scales as the index contrast, a high-contrast TFLN rib (n of about 2.2 against 1.44) is expected to have Ez/Ex of about 0.2.
- Okamoto, K., *Fundamentals of Optical Waveguides*, 2nd ed., Academic Press/Elsevier, 2006 (released Dec 2005), xvi+561 pp., ISBN 978-0-12-525096-2 [V] — [British Library](https://eld.bl.uk/catalog/017701882), [Tenlong](https://www.tenlong.com.tw/products/9780125250962)
  - [V] Topics include wave theory of optical waveguides, planar waveguides, optical fibers, coupled-mode theory, FEM, BPM, and key theorems and formulas.
  - Sections [U]. Ch. 1, "Wave theory of optical waveguides": Maxwell's equations in waveguide form, with Ez expressed through the transverse fields. Ch. 2, "Planar optical waveguides": slab TE/TM modes, rectangular guides via Marcatili and the effective-index method (EIM), and coupled-mode theory. Ch. 6, "Finite element method": scalar and vector FEM for waveguides.
- Chuang, S. L., *Physics of Photonic Devices*, 2nd ed., Wiley, 2009, ISBN 978-0-470-29319-5 [V] (the "two ISBNs" in one search summary are the same number, with and without hyphens) — [Wiley-VCH](https://www.wiley-vch.de/en/areas-interest/engineering/physics-of-photonic-devices-978-0-470-29319-5), [Tenlong](https://www.tenlong.com.tw/products/9780470293195)
  - Sections [U]. Ch. 7, "Theory of optical waveguides": symmetric slab TE/TM, asymmetric slab, rectangular guides via Marcatili and EIM. Ch. 8 covers coupled-mode theory.

### Inferences
- The femwell result (Ez about 0.2 Ex, in quadrature, odd in x) follows directly from Gauss's law. Ex is even with a peak at the rib center, so ∂x(εEx) is odd. That parity argument, combined with the -j/β factor, is the full explanation.

### Gaps
- No bibliographic data was verified for Marcuse (*Theory of Dielectric Optical Waveguides*, 2nd ed., Academic Press 1991 [U]), Haus (*Waves and Fields in Optoelectronics*, Prentice-Hall 1984 [U]; the search returned nothing), Tamir ed. (*Integrated Optics*, Topics in Applied Physics vol. 7, Springer 1975/2nd ed. 1979, Kogelnik Ch. 2, "Theory of dielectric waveguides" [U]), or Pollock & Lipson (*Integrated Photonics*, Kluwer 2003 [U]).

## Q2: TE/TM/TEM/hybrid/quasi-TE definitions; why TEM cannot exist in a dielectric guide

### Takeaway
Okamoto Ch. 1-2, Snyder & Love Ch. 11-12, Marcuse Ch. 1-2 and Collin Ch. 3 [all U] define these mode classes. The no-TEM argument is in Collin and in Pozar Ch. 3 [U]. A TEM field must satisfy the 2-D Laplace equation in the cross-section and travel at a single velocity, which requires a homogeneous medium and two conductors. An inhomogeneous dielectric cross-section therefore forces hybrid modes. In a rectangular or rib dielectric guide every mode is hybrid, and "quasi-TE" (Marcatili E^x_pq) simply labels the dominant component.

### Cited Findings
- Collin, R. E., *Field Theory of Guided Waves*, 2nd ed., IEEE Press (Wiley-IEEE), 1991 (Wiley lists Dec 1990), ISBN 0-87942-237-8; Oxford co-edition 0-19-859213-2 [V]. The 2nd edition adds layered media, microstrip, dielectric resonators and integral equations [V] — [Wiley-VCH](https://www.wiley-vch.de/de/fachgebiete/ingenieurwesen/field-theory-of-guided-waves-978-0-87942-237-0), [CGU library](https://web20.lib.cgu.edu.tw/detail/800608)
  - [U] Ch. 3, "Transmission lines" (TEM conditions). Ch. 5, "Waveguides and cavities". Ch. 6, "Inhomogeneously filled waveguides and dielectric resonators": proves that a partially filled guide cannot support pure TE/TM modes and that its modes are LSE/LSM. This maps directly onto the rib above a substrate. Ch. 11, "Surface waveguides": dielectric slab and corrugated surfaces, with surface waves and their evanescent fields.
- Pozar, D. M., *Microwave Engineering*, 4th ed., Wiley, 2011/2012, ISBN 978-0-470-63155-3 [V] — [Schweitzer](https://www.schweitzer-online.de/en/buch/Pozar/Microwave-Engineering/9780471448785/A28616853/), [eBay catalog](https://www.ebay.com/p/109226747)
  - [U] Ch. 3 opens with the general TEM/TE/TM solutions (3.1). Sections then cover the partially loaded guide (LSE modes) and the transverse resonance technique; that section is numbered 3.9 in the 3rd and 4th editions. Not verified.

### Gaps
- The exact section numbers could not be checked against a TOC.

## Q3: Evanescent tails, effective-index method for rib guides, leaky modes, interface boundary conditions

### Takeaway
[U, standard content]. The evanescent decay γ = k0(n_eff^2 - n_clad^2)^1/2 and the slab dispersion relation are in Okamoto Ch. 2, Chuang Ch. 7 and Marcuse Ch. 1. The EIM for rib and channel guides is in Okamoto Ch. 2 and Chuang Ch. 7. Snyder & Love treat leaky and radiation modes in Ch. 24-25 [U]. Marcuse covers radiation modes (Ch. 1 of Theory of Dielectric Optical Waveguides). Normal D is continuous, so En jumps by ε1/ε2. That condition is in every text, e.g. Collin Ch. 1 or Okamoto Ch. 1. Lateral leakage of TM-like modes in rib guides (the relevant leakage mechanism) is a journal topic (Webster, Pregla et al.; Koshiba). It appears only briefly in textbooks.

### Gaps
- None of the section numbers here could be verified online.

## Q4: Standing waves / Fabry-Perot with complex reflection; transverse resonance

### Takeaway
[U] The transverse resonance method is in Collin (Ch. 6 for inhomogeneously filled guides, and in the surface-wave chapter) and in Pozar (§3.9 in the 4th edition, unverified). Fabry-Perot with complex mirror reflection r = |r|e^{jφ} gives the resonance condition 2βL + φ1 + φ2 = 2πm. It is covered in Saleh & Teich, *Fundamentals of Photonics* (Ch. on resonator optics, unverified edition), and Chuang. The same round-trip phase condition also gives the slab dispersion relation (Okamoto Ch. 2 ray picture). A laterally propagating metal-bound wave that reflects off the electrode edges therefore forms a standing wave whose node positions shift with the reflection phase.

### Gaps
- Saleh & Teich was not verified in this session.

## Q5: SPPs, IMI/MIM stacks, SPP field-component ratios

### Takeaway
Maier Ch. 2 is the canonical derivation. It starts from the wave equation at a single interface and shows that SPPs exist only as TM, with |Ez/Ex| = |β/k_z,i| in Maier's coordinates (x along propagation, z normal to the interface). It then treats IMI and MIM multilayers as coupled odd/even modes. Ch. 7 covers plasmon waveguides. In the femwell geometry the normal axis is y, so the strong components are Ey (normal) and Ez (along propagation). This matches the TM-like metal-bound wave.

### Cited Findings
- Maier, S. A., *Plasmonics: Fundamentals and Applications*, Springer, New York, 2007, ISBN 978-0-387-33150-8 (hb), e-ISBN 978-0-387-37825-1, 224 pp. [V]. Chapters [V]: 1 Electromagnetics of Metals; 2 Surface Plasmon Polaritons at Metal/Insulator Interfaces; 3 Excitation of SPPs at Planar Interfaces; 4 Imaging SPP Propagation; 5 Localized Surface Plasmons; 6 Electromagnetic Surface Modes at Low Frequencies; 7 Plasmon Waveguides; ... 12 Concluding Remarks — [Springer](https://link.springer.com/978-0-387-37825-1), [Ellibs](https://www.ellibs.com/book/9780387378251/plasmonics-fundamentals-and-applications)
  - [U] Subsections. §2.2 SPPs at a single interface: TE gives no solution; TM gives the dispersion relation and the field-ratio expressions. §2.3 Multilayer systems: IMI and MIM, odd/even modes. §2.4 Energy confinement and effective mode length. §1.2 Drude model, which sets ε_Au of about -115+11j at 1.55 µm.
- Novotny, L. & Hecht, B., *Principles of Nano-Optics*, 2nd ed., Cambridge University Press, 2012, ISBN 978-1-107-00546-4; ebook 978-0-511-79419-3 [V] — [Cambridge copyright page](https://assets.cambridge.org/97811070/05464/copyright/9781107005464_copyright_info.pdf)
  - [U] The 2nd edition's "Surface plasmons" chapter (Ch. 12, unconfirmed; Cambridge Core lists a chapter titled "Plasmonics" [V], [link](https://resolve.cambridge.org/core/books/principles-of-nanooptics/plasmonics/B2AE480B61977BB646DD81FC6BCD2422)) derives the SPP at a planar interface and gives the explicit field components.
- Raether, H., *Surface Plasmons on Smooth and Rough Surfaces and on Gratings*, Springer Tracts in Modern Physics vol. 111, 1988 [U, not verified]. Ch. 2 covers the dispersion relation and fields of SPPs.

### Gaps
- Maier's subsection numbers and Novotny's chapter number are unverified.

## Q6: Full-vector FEM mode solvers with edge (Nédélec) elements for Et and nodal elements for Ez

### Takeaway
The standard reference is Jin, 3rd ed. Its chapter on 2-D/3-D waveguide eigenproblems [U: Ch. 8 "Finite element analysis of ... waveguides" / the vector-element chapter] explains several points. Nodal elements for all three field components produce spurious non-physical modes, because they enforce full continuity and do not respect the null space of the curl operator. Tangential (Whitney/Nédélec) edge elements for Et, combined with nodal Lagrange elements for Ez, remove these modes. The primary paper is Lee, Sun & Cendes 1991. femwell uses this Et (Nédélec) + Ez (Lagrange) formulation.

### Cited Findings
- Jin, J.-M., *The Finite Element Method in Electromagnetics*, 3rd ed., Wiley-IEEE Press, Hoboken NJ, March 2014, 876 pp., ISBN 978-1-118-57136-1 [V] — [O'Reilly](https://www.oreilly.com/library/view/-/9781118571361/), [Tenlong](https://tenlong.com.tw/products/9781118571361)
- Lee, J.-F., Sun, D.-K., Cendes, Z. J., "Full-wave analysis of dielectric waveguides using tangential vector finite elements," IEEE Trans. Microw. Theory Tech., vol. 39, no. 8, pp. 1262–1271, Aug. 1991 [V via citing paper] — [arXiv 1603.03791 bibliography](https://arxiv.org/pdf/1603.03791)
- Okamoto 2nd ed. includes an FEM chapter [V topic, U chapter number] — [British Library](https://eld.bl.uk/catalog/017701882)

### Gaps
- Jin's exact chapter number for waveguide eigenanalysis was not verified; check the O'Reilly TOC.
