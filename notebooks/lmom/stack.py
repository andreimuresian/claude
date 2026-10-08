"""Plane-wave response of the TFLN stack seen from the air half-space above the metal plane.

Coordinates: x lateral, y vertical (up), z along the line.  Air for y > 0; below y = 0:
LN slab (eps_x 28, eps_y 43, eps_z 43: optical axis lateral, so NOT uniaxial about y and
TE/TM couple), SiO2, Si 550 um, Si half-space (CST's stack).  Fields ~ exp(j w t - j kx x
- j beta z).  State vector of tangential fields psi = [Ex, Ez, Hx~, Hz~], H~ = eta0 H:
    d psi / dy = A(kx, beta) psi           (diagonal eps, mu = mu0)
A layer's eigenvectors split into up (decaying / outgoing toward +y) and down waves.

Y (2x2): H~_t = Y E_t at a plane, for the field the stack below allows (outgoing at the
bottom).  Reflection seen from air: E_t,up = R E_t,down at y = 0,
    R = (Y_up - Y_s)^-1 (Y_s - Y_dn).
A current sheet J delta(y - y') (A/m^2 times m) makes the jump
    psi(y'+) - psi(y'-) = eta0 [kx Jy / k0, beta Jy / k0, -Jz, Jx].
All functions are vectorised over an array of kx.
"""
import numpy as np

C0, EPS0, MU0 = 299792458.0, 8.8541878128e-12, 4e-7*np.pi
ETA0 = np.sqrt(MU0/EPS0)


def A_matrix(kx, beta, k0, eps):
    """(..., 4, 4) for psi = [Ex, Ez, Hx~, Hz~]; eps = (ex, ey, ez)."""
    ex, ey, ez = eps
    kx = np.asarray(kx, complex)
    A = np.zeros(kx.shape + (4, 4), complex)
    # dEx/dy = j k0 Hz - j kx Ey,   Ey = (-beta Hx + kx Hz)/(k0 ey)
    A[..., 0, 2] = 1j*kx*beta/(k0*ey)
    A[..., 0, 3] = 1j*k0 - 1j*kx*kx/(k0*ey)
    # dEz/dy = -j k0 Hx - j beta Ey
    A[..., 1, 2] = -1j*k0 + 1j*beta*beta/(k0*ey)
    A[..., 1, 3] = -1j*beta*kx/(k0*ey)
    # dHx/dy = -j k0 ez Ez - j kx Hy,  Hy = (beta Ex - kx Ez)/k0
    A[..., 2, 0] = -1j*kx*beta/k0
    A[..., 2, 1] = -1j*k0*ez + 1j*kx*kx/k0
    # dHz/dy = j k0 ex Ex - j beta Hy
    A[..., 3, 0] = 1j*k0*ex - 1j*beta*beta/k0
    A[..., 3, 1] = 1j*beta*kx/k0
    return A


def modes(kx, beta, k0, eps, outgoing=None):
    """Eigen-split of a homogeneous layer: (lam_up, V_up, lam_dn, V_dn), V (..., 4, 2).
    Up: Re(lam) < 0, or Re(lam) = 0 and Im(lam) < 0 (k_y = j lam with Im k_y <= 0): the proper
    (decaying) choice.  outgoing (bool mask over kx): there, classify by the direction of phase
    travel instead (down = Im(lam) > 0), the improper choice a leaky mode needs in its
    radiation region."""
    lam, V = np.linalg.eig(A_matrix(kx, beta, k0, eps))
    key = lam.real + 1e-9*np.abs(lam)*np.sign(lam.imag)          # tie-break for lossless waves
    if outgoing is not None:
        key = np.where(np.asarray(outgoing)[..., None], lam.imag, key)       # up first: smaller Im
    order = np.argsort(key, axis=-1)
    lam = np.take_along_axis(lam, order, -1)
    V = np.take_along_axis(V, order[..., None, :], -1)
    return lam[..., :2], V[..., :, :2], lam[..., 2:], V[..., :, 2:]


def _adm(V):
    """Y with H_t = Y E_t for the fields spanned by V (..., 4, 2)."""
    return V[..., 2:, :] @ np.linalg.inv(V[..., :2, :])


def stack_admittance(kx, beta, k0, layers, bottom, leaky=False):
    """Y_s at the top of `layers` (list of (eps, d) from the top down), bottom half-space eps.
    leaky: outgoing (improper) bottom waves for |Re kx| below the bottom branch point."""
    out = None
    if leaky:
        kb2 = (np.real(bottom[0])*k0**2 - np.real(beta)**2)
        out = np.abs(np.real(kx)) < np.sqrt(max(kb2, 0.0))
    _, _, _, Vd = modes(kx, beta, k0, bottom, outgoing=out)
    Y = _adm(Vd)
    for eps, d in layers[::-1]:
        same = out is not None and np.allclose(np.asarray(eps, complex), np.asarray(bottom, complex))
        lu, Vu, ld, Vd = modes(kx, beta, k0, eps, outgoing=out if same else None)
        Pu = np.exp(lu*d)[..., None, :]*np.eye(2)                  # up waves referenced at the bottom
        Pd = np.exp(-ld*d)[..., None, :]*np.eye(2)                 # down waves referenced at the top
        VuE, VuH, VdE, VdH = Vu[..., :2, :], Vu[..., 2:, :], Vd[..., :2, :], Vd[..., 2:, :]
        Q = -np.linalg.solve(VuH - Y @ VuE, (VdH - Y @ VdE) @ Pd)
        Y = (VuH @ Pu @ Q + VdH) @ np.linalg.inv(VuE @ Pu @ Q + VdE)
    return Y


def tfln_layers(tLN, eps_si, eps_ln=(28.0, 43.0, 43.0), box=4.7e-6, si=550e-6):
    return [(eps_ln, tLN), ((3.9,)*3, box), ((eps_si,)*3, si)], (eps_si,)*3


class Air:
    """Air half-space quantities for an array of kx at fixed beta, k0."""

    def __init__(self, kx, beta, k0):
        self.kx, self.beta, self.k0 = np.asarray(kx, complex), beta, k0
        lu, Vu, ld, Vd = modes(kx, beta, k0, (1.0, 1.0, 1.0))
        self.lam_u = lu[..., 0]                                     # both up waves share k_y in air
        self.Vu, self.Vd = Vu, Vd
        self.Yu, self.Yd = _adm(Vu), _adm(Vd)
        self.ky = 1j*self.lam_u                                     # Im <= 0

    def reflection(self, Ys):
        return np.linalg.solve(self.Yu - Ys, Ys - self.Yd)

    def sheet_down(self, J):
        """Downgoing E_t (2-vector) just below a unit sheet with current components J =
        (Jx, Jy, Jz) (each scalar or array over kx): solves psi+ - psi- = jump."""
        Jx, Jy, Jz = (np.broadcast_to(np.asarray(c, complex), self.kx.shape) for c in J)
        jump = ETA0*np.stack([self.kx*Jy/self.k0, self.beta*Jy/self.k0, -Jz, Jx], -1)
        M = np.concatenate([self.Vu, -self.Vd], -1)                 # [U, -D] (a; b) = jump
        ab = np.linalg.solve(M, jump[..., None])[..., 0]
        return (self.Vd[..., :2, :] @ ab[..., 2:, None])[..., 0], (self.Vu[..., :2, :] @ ab[..., :2, None])[..., 0]

    def up_field(self, Et):
        """Full E (Ex, Ey, Ez) of the up wave with tangential E_t at the reference plane."""
        c = np.linalg.solve(self.Vu[..., :2, :], Et[..., None])
        psi = (self.Vu @ c)[..., 0]
        Ey = (-self.beta*psi[..., 2] + self.kx*psi[..., 3])/self.k0
        return np.stack([psi[..., 0], Ey, psi[..., 1]], -1)

    def down_field(self, Et):
        c = np.linalg.solve(self.Vd[..., :2, :], Et[..., None])
        psi = (self.Vd @ c)[..., 0]
        Ey = (-self.beta*psi[..., 2] + self.kx*psi[..., 3])/self.k0
        return np.stack([psi[..., 0], Ey, psi[..., 1]], -1)
