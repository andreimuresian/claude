"""Patched copy of the PDK cell Template_RF_launch (the PDK file itself is not modified).

Change with respect to the PDK version: the outer edges of the two ground tapers can start at the outer edge of the
full line ground, i.e. lateral width + an outer band (rf_line_outer_band_left / _right), instead of at the lateral
width only. With both bands at 0 the cell is geometrically identical to the PDK cell.
The RF pin d0 keeps the cross-section of the connection line (XS_rfline without the band), so connections made to
d0 are unchanged.
"""
import nazca as nd
from nazca import hashme

import pdk_20  # same import as in the PDK file: adjust to the project path if needed


@hashme("Template_RF_launch_patch")
def Template_RF_launch_patch(
    rf_line_gap: float = 5.0,
    rf_line_central_width: float = 34.0,
    rf_line_lateral_width: float = 69.5,
    rf_line_lateral_width_left: float = None,
    rf_line_lateral_width_right: float = None,
    rf_line_outer_band_left: float = 0.0,
    rf_line_outer_band_right: float = 0.0,
    pad_gap: float = 50.0,
    pad_central_width: float = 80.0,
    pad_lateral_width: float = 200.0,
    pad_length: float = 80.0,
    taper_length: float = 150.0,
    passivation_buffer: float = 5.0,
    passivation_opening_type: str = "pad",
) -> nd.Cell:
    """Single-ended RF launch pad, ground tapers matched to the full line ground.

    Args:
        rf_line_gap (float, optional): Gap of connection rf line. Defaults to 5.0.
        rf_line_central_width (float, optional): Central width of connection rf line. Defaults to 34.0.
        rf_line_lateral_width (float, optional): Lateral width of connection rf line. Defaults to 69.5.
        rf_line_lateral_width_left (float, optional): Width of the external left connection line. Defaults to None (rf_line_lateral_width is assumed).
        rf_line_lateral_width_right (float, optional): Width of the external right connection line. Defaults to None (rf_line_lateral_width is assumed).
        rf_line_outer_band_left (float, optional): Extra ground width beyond the left lateral line at the line end; the left taper starts at its outer edge. Defaults to 0.0 (PDK geometry).
        rf_line_outer_band_right (float, optional): Same on the right side. Defaults to 0.0 (PDK geometry).
        pad_gap (float, optional): Gap of the launch pad. Defaults to 50.0.
        pad_central_width (float, optional): Width of the central launch pad. Defaults to 80.0.
        pad_lateral_width (float, optional): Width of the lateral ground pads. Defaults to 200.0.
        pad_length (float, optional): Length of the launch pad. Defaults to 80.0.
        taper_length (float, optional): Length of the taper to launch pad. Defaults to 150.0.
        passivation_buffer (float, optional): Buffer between metal and passivation opening on pad. Defaults to 5.0.
        passivation_opening_type (str, optional): How to apply passivation opening. One of 'pad', 'full'. Default to 'pad'.

    Returns:
        nd.Cell: Cell of launch pad
    """
    wl = rf_line_lateral_width if rf_line_lateral_width_left is None else rf_line_lateral_width_left
    wr = rf_line_lateral_width if rf_line_lateral_width_right is None else rf_line_lateral_width_right
    with nd.Cell(hashme=True, autobbox=True) as cell:
        # connection line (pin d0), unchanged
        xs_rf = pdk_20.XS_rfline(
            gap=rf_line_gap,
            central_width=rf_line_central_width,
            lateral_width=rf_line_lateral_width,
            lateral_width_left=rf_line_lateral_width_left,
            lateral_width_right=rf_line_lateral_width_right,
        )
        # start of the taper: lateral widths including the outer band
        xs_taper = pdk_20.XS_rfline(
            gap=rf_line_gap,
            central_width=rf_line_central_width,
            lateral_width=rf_line_lateral_width,
            lateral_width_left=wl + rf_line_outer_band_left,
            lateral_width_right=wr + rf_line_outer_band_right,
        )
        xs_pad = pdk_20.XS_rfline(
            gap=pad_gap,
            central_width=pad_central_width,
            lateral_width=pad_lateral_width,
        )

        ic_taper = nd.ic.Interconnect(xs=xs_taper.name)
        ic_pad = nd.ic.Interconnect(xs=xs_pad.name)

        cell.default_pins("d0", "d0")
        e1 = ic_taper.connect(length=taper_length, ic=ic_pad).put()
        ic_pad.strt(length=pad_length, arrow=False).put()

        nd.Pin("c0", xs="DCline", width=pad_central_width, remark="Central line").put(
            taper_length + 0.5 * pad_length, 0.0, 0.0
        )
        nd.Pin("d0", xs=xs_rf.name, width=nd.get_xsection(xs_rf.name).width, remark="RF port").put(e1.pin["a0"])

        if passivation_opening_type == "pad":
            nd.Polygon(
                points=nd.geom.box(length=pad_length, width=pad_central_width),
                layer="MainPas",
            ).grow(-passivation_buffer, jointype="miter").put(taper_length, 0.0)
            _poly = nd.Polygon(
                points=nd.geom.rectangle(length=pad_length, height=pad_lateral_width),
                layer="MainPas",
            ).grow(-passivation_buffer, jointype="miter")
            _poly.put(taper_length, pad_gap + 0.5 * pad_central_width)
            _poly.put(taper_length, -pad_gap - 0.5 * pad_central_width, flop=True)

        elif passivation_opening_type == "full":
            nd.Polygon(
                points=nd.geom.box(
                    length=taper_length + pad_length + passivation_buffer,
                    width=pad_central_width
                    + 2.0 * (pad_gap + pad_lateral_width + passivation_buffer),
                ),
                layer="MainPas",
            ).put(0, 0, 0)

        nd.put_stub()
    return cell
