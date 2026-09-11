import logging
from pathlib import Path
import yaml

basedir = Path(__file__).parent
outfile = Path(__file__).stem

import nazca as nd
import pandas as pd

if len(nd.logger.handlers) < 2:
    filehandler = logging.FileHandler(str(basedir / "local" / f"{outfile}.log"), "w")
    filehandler.setFormatter(nd.logging.formatter0)
    nd.logger.addHandler(filehandler)

from f30_lib.bbs.settings import die_length, die_height, die_template
from f30_lib.data_extraction.data_extraction import get_cell_data_test

from f30_lib.bbs.mzms_library import (
    build_tee_frame_terminations_dynamic,
    build_tee_frame_terminations_extra_dynamic,
)

# Tee-with-frame terminations using the DYNAMIC (adaptive) frame instead
# of the hardcoded 300x400 one. These are drop-in teeF lists: the main
# builder returns 38 (TP01..TP38), the extra builder returns 4 (REF01..04).
doe_termination_cells2 = build_tee_frame_terminations_dynamic()
doe_termination_cells_extra = build_tee_frame_terminations_extra_dynamic()


GC_distance_long = 11414.174
align_length = 668

# =========================================================================
# GEOMETRY SCALING
# -------------------------------------------------------------------------
# This cell is a 2x-wide / 0.5x-tall replica of TEST_CELL_2: it must be
# exactly twice as wide (so two of the original cells fit side by side
# under it in the field), while the height only needs to be roughly
# halved -- HEIGHT_SCALE is kept as a single knob in case the DOE grid
# needs a little more vertical room once placed against real settings.
# =========================================================================
WIDTH_SCALE = 2.0
HEIGHT_SCALE = 0.5

inner_die_length = (die_length - 1500) * WIDTH_SCALE
inner_die_height = (die_height - 1400 - 215) * HEIGHT_SCALE

with nd.Cell("inner_Test_cell1_wide", autobbox=True) as inner_main_cell:
    die_template(
        die_length=inner_die_length,
        die_height=inner_die_height,
        cleave_line=100.0,
        lap_line=0.0,
        cap_area=0.0,
        wg_etch_area=0.0,
        ebeam_marks_ncolumns=0,
        ebeam_marks_nrows=0,
    ).put()


with nd.Cell("TEST_CELL_2_WIDE", autobbox=True) as CELL_ONE:
    inner_main_cell.put("cc", 0, 0, 180)

    # =====================================================================
    # PLACE THE DOE TERMINATION PATTERNS (TP01 to TP38 + 4 extra refs)
    # -----------------------------------------------------------------------
    # Same pitches as the original (pitch_x=728, row pitch=850) -- only the
    # row/column split changes, from 3 rows of 14 down to 2 rows of 21, so
    # that the same 42 patterns end up twice as wide and half as tall.
    # =====================================================================
    start_x = -4800.0
    start_y = 900.0
    pitch_x = 728.0
    pitch_y = 850.0

    # Row 1: 21 patterns (TP01-TP21)
    for i in range(0, 21):
        current_x = start_x + (i * pitch_x)
        doe_termination_cells2[i].put(current_x, start_y)

    # Row 2: remaining 17 patterns (TP22-TP38)
    start_y2 = start_y - pitch_y
    for i in range(21, 38):
        current_x2 = start_x + ((i - 21) * pitch_x)
        doe_termination_cells2[i].put(current_x2, start_y2)

    # Row 2 continued: 4 extra reference terminations (columns 18-21)
    start_x4 = start_x + (17 * pitch_x)
    for i in range(0, 4):
        current_x4 = start_x4 + (i * pitch_x)
        doe_termination_cells_extra[i].put(current_x4, start_y2)

    # ADDING ALIGNMENT CROSSES FOR EACH FIELD
    nd.Polygon(points=nd.geom.box(length=20, width=70), layer="TerminationFrame").put(-4700 -590, 1320)
    nd.Polygon(points=nd.geom.box(length=20, width=70), layer="TerminationFrame").put(-4700 -590 + 10, 1320 -10, 90)



print("Bounding box:", CELL_ONE.bbox)

xmin, ymin, xmax, ymax = CELL_ONE.bbox
width = xmax - xmin
height = ymax - ymin
print(f"Width: {width}, Height: {height}")



if __name__ == "__main__":
    cells = [CELL_ONE]
    nd.export_gds(
        cells,
        filename=str(basedir / "local" / f"{outfile}.gds"),
    )
    # with open(basedir / "local" / f"{outfile}.yaml", "w") as f:
    #     yaml.safe_dump(test_cell_3_interface, f)
