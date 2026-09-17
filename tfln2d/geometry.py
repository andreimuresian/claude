"""Parametric TFLN modulator cross-section.

The cross-section is described by the same five degrees of freedom the 2D
COMSOL baseline used (WS, G, TAu, Wcap, Detch); everything else is a fixed
process constant.  All lengths are micrometres.
"""

from collections import OrderedDict
from dataclasses import dataclass

from shapely.geometry import Polygon, box
from shapely.ops import unary_union


@dataclass(frozen=True)
class CrossSection:
    """Geometry of one TFLN coplanar-waveguide cross-section."""

    # --- swept degrees of freedom ---
    ws: float = 35.0        # signal electrode width
    gap: float = 3.0        # signal-to-ground gap
    t_au: float = 1.0       # electrode thickness (MTX)
    w_cap: float = 1.65     # SiO2 cap width over the rib
    d_etch: float = 0.23    # LN rib etch depth

    # --- process constants ---
    ln_total: float = 0.46  # total LN film thickness
    wg_top: float = 0.8     # rib top width
    sidewall_deg: float = 60.0
    h_cap: float = 1.4      # SiO2 cap height
    box_h: float = 4.7      # buried oxide thickness
    si_h: float = 550.0     # silicon substrate depth
    w_gnd: float = 70.0     # ground electrode width
    pad: float = 400.0      # lateral "Goldilocks" padding
    air_h: float = 200.0    # air above the stack

    @property
    def slab_h(self) -> float:
        return self.ln_total - self.d_etch

    @property
    def half_width(self) -> float:
        return self.ws / 2 + self.gap + self.w_gnd + self.pad

    # layer interface heights, measured from the top of the silicon
    @property
    def y(self) -> dict:
        box_t = self.box_h
        slab_t = box_t + self.slab_h
        rib_t = slab_t + self.d_etch
        return {
            "si_bot": -self.si_h,
            "si_top": 0.0,
            "box_top": box_t,
            "slab_top": slab_t,
            "rib_top": rib_t,
            # electrodes are deposited on the etched slab, beside the ribs
            "au_bot": slab_t,
            "au_top": slab_t + self.t_au,
            "air_top": slab_t + self.t_au + self.air_h,
        }

    def _rib(self, x_centre: float) -> Polygon:
        """LN rib: trapezoid with the given sidewall angle."""
        from math import radians, tan

        y = self.y
        run = self.d_etch / tan(radians(self.sidewall_deg))
        half_top = self.wg_top / 2
        half_bot = half_top + run
        return Polygon([
            (x_centre - half_bot, y["slab_top"]),
            (x_centre + half_bot, y["slab_top"]),
            (x_centre + half_top, y["rib_top"]),
            (x_centre - half_top, y["rib_top"]),
        ])

    def rib_centres(self) -> list:
        """One rib per modulating gap, centred in the gap."""
        offset = self.ws / 2 + self.gap / 2
        return [-offset, offset]

    def polygons(self, optical_half: bool = False) -> OrderedDict:
        """Ordered polygons for meshing.

        Later entries are carved out of earlier ones by the mesher, so the
        order matters: metals and ribs must precede the bulk dielectrics.
        """
        y = self.y
        hw = self.half_width

        signal = box(-self.ws / 2, y["au_bot"], self.ws / 2, y["au_top"])
        gnd_r = box(self.ws / 2 + self.gap, y["au_bot"],
                    self.ws / 2 + self.gap + self.w_gnd, y["au_top"])
        gnd_l = box(-(self.ws / 2 + self.gap + self.w_gnd), y["au_bot"],
                    -(self.ws / 2 + self.gap), y["au_top"])

        centres = self.rib_centres()
        if optical_half:
            centres = centres[1:]

        ribs = [self._rib(x) for x in centres]
        caps = [box(x - self.w_cap / 2, y["rib_top"],
                    x + self.w_cap / 2, y["rib_top"] + self.h_cap)
                for x in centres]

        slab = box(-hw, y["box_top"], hw, y["slab_top"])
        oxide = box(-hw, y["si_top"], hw, y["box_top"])
        silicon = box(-hw, y["si_bot"], hw, y["si_top"])

        solids = unary_union([signal, gnd_l, gnd_r] + ribs + caps)
        air = box(-hw, y["slab_top"], hw, y["air_top"]).difference(solids)

        polys = OrderedDict()
        polys["signal"] = signal
        polys["ground_l"] = gnd_l
        polys["ground_r"] = gnd_r
        for i, (rib, cap) in enumerate(zip(ribs, caps)):
            polys[f"rib_{i}"] = rib
            polys[f"cap_{i}"] = cap
        polys["slab"] = slab
        polys["oxide"] = oxide
        polys["silicon"] = silicon
        polys["air"] = air
        return polys

    def metal_names(self) -> list:
        return ["signal", "ground_l", "ground_r"]

    def rib_names(self) -> list:
        return [f"rib_{i}" for i in range(len(self.rib_centres()))]
