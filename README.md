# TFLN modulator figures of merit, in pure Python

A closed Python replacement for the two-simulator workflow (COMSOL 2D
cross-section + CST Multilayer 2.5D) used to predict the RF figures of merit of
a periodically loaded thin-film lithium niobate travelling-wave modulator.

The **decomposed method is unchanged**: a 2D cross-sectional baseline plus a
periodic perturbation extracted from one unit cell, superposed as

    L_3D = L_2D + dL/d        C_3D = C_2D + dC/d        alpha_3D = alpha_2D + d_alpha

What changes is only the engines. In particular the unit cell is solved with
mirror/periodic conditions instead of driven ports, so **there are no ports, no
Touchstone export, no ABCD de-embedding and no N+1 minus N difference** — those
exist only to cancel port artefacts, and there are none to cancel.

---

## Running locally

### 1. Python

Use **Python 3.10, 3.11 or 3.12**. (3.13 still has wheel gaps in this stack.)

```bash
python3 --version
```

### 2. Get the code

```bash
git clone https://github.com/andreimuresian/claude.git
cd claude
git checkout 2D-+-2.5D
```

### 3. Virtual environment

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Dependencies

```bash
pip install -r requirements.txt
```

This pulls femwell, which brings a large CAD/visualisation tail (vtk, cadquery,
trame). Expect a few minutes and roughly 1 GB.

**Linux only** — gmsh needs system OpenGL libraries even when run headless:

```bash
sudo apt-get install -y libglu1-mesa libxrender1 libxcursor1 libxft2 libxinerama1
```

macOS and Windows wheels are self-contained; nothing extra is needed.

Check it imported:
```bash
python -c "import gmsh, femwell, skfem, pyamg; print('ok')"
```

### 5. Run

```bash
python run_demo.py
```

That is **the file to run**. It executes the whole chain for one geometry:

1. 2D cross-section  -> baseline `n_m`, `Z0`, `alpha`   (replaces COMSOL)
2. 3D unit cell      -> lumped penalties `dL`, `dC`     (replaces CST MoM)
3. synthesis         -> 3D, tee-perturbed `n_m`, `Z0`

Roughly **70 s** end to end at around 3 GB peak.

| command | what it does | time |
|---|---|---|
| `python run_demo.py --2d-only` | cross-section only, no 3D | ~6 s |
| `python run_demo.py` | full chain, coarse 3D mesh | ~70 s |
| `python run_demo.py --full` | full chain, finer 3D mesh | ~10 min, ~6 GB |

### 6. In VSCode

Open the `claude` folder, then **Ctrl/Cmd+Shift+P -> Python: Select
Interpreter** and pick the `.venv` you just made. Open `run_demo.py` and press
the Run button, or from the integrated terminal:

```bash
python run_demo.py
```

Run it from the **repository root** — the scripts put the root on `sys.path`
themselves, so running from a subfolder will fail to import `tfln2d`.

---

## Changing the geometry

Everything the demo sweeps lives at the top of `run_demo.py`:

```python
GEOMETRY = dict(ws=35.0, gap=6.0, t_au=1.0)          # cross-section
STUB     = dict(L1=20.0, L2=60.0, W1=15.0, W2=25.0)  # T-stub
PITCH    = 200.0
```

These are the thesis symbols: `ws` = W_S, `gap` = G, `t_au` = MTX, and the four
T-stub parameters. The remaining cross-section degrees of freedom (`w_cap`,
`d_etch`) are arguments of `CrossSection` in `tfln2d/geometry.py`.

---

## Layout

| path | role |
|---|---|
| `run_demo.py` | **entry point** — the whole chain for one geometry |
| `tfln2d/geometry.py` | parametric cross-section |
| `tfln2d/materials.py` | RF and optical material models, Sellmeier |
| `tfln2d/mesh.py` | 2D meshing |
| `tfln2d/quasistatic.py` | (L, C) -> n_m, Z0, conductor loss |
| `tfln2d/modesolve.py` | full-wave vector mode analysis |
| `tfln2d/synthesis.py` | baseline + penalties -> 3D kinematics |
| `tfln3d/cell.py` | layered-extrusion mesher for the unit cell |
| `tfln3d/electrostatic.py` | capacitance per cell -> dL, dC |
| `studies/` | convergence and validation sweeps |

`tfln2d/README.md` holds the measured results, the validation against the
thesis' CST anchors, and the two known gaps.

---

## State

Working and mesh-converged: `n_m`, `Z0`, `dL`, `dC`.

Not yet implemented: `d_alpha`, the attenuation perturbation. The demo prints
`alpha_3D` equal to the 2D baseline and says so. See `tfln2d/README.md`.

Also open: the vector mode solver needs tensor-valued permittivity (LN
anisotropy moves `n_m` by 5%), and conductor loss needs a Robin
surface-impedance condition rather than the perturbative route.

**First thing worth doing:** run one geometry that already exists in the
500-sample CST campaign and compare `dL` and `dC` against the MoM values. That
is the check that tells you whether the unit cell is reproducing the
perturbation correctly.
