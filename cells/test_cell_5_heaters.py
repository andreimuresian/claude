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

from f30_lib.bbs.settings import SGC_Ref, die_length, die_height, DCPad, die_template, cleave_line, lap_line_extension
from f30_lib.data_extraction.data_extraction import get_cell_data_test

from f20_chip_designs.chip_20_test_cells.f30_chip_lib.test_EOPCM_mzm4_default_bend import EOPCM_array_mzi_Test_Cell_3
from f30_lib.bbs.mzms_library import ladder_frame, ladder_no_frame, dumbbell_cells, make_label
from f20_chip_designs.chip_20_test_cells.f30_chip_lib.test_EOPCM_mzm4_default_bend import (
    build_standalone_heaters_length_sweep,
)
from f30_lib.bbs.mzms_library import build_dumbbell_terminations_lw

# Three rows of the same 14 width variations, one row per heater length.
# Lengths are the measured bottom contact rail: -25%, nominal, +25%.
heater_rows = build_standalone_heaters_length_sweep(rail_lengths=(348.0, 464.0, 580.0))

# Dumbbell (TLM) terminations: 3 gap lengths x 8 line widths, frame always on.
# Row-major order -> [0:8] = L28, [8:16] = L38, [16:24] = L48.
dumbbell_lw_cells = build_dumbbell_terminations_lw()


with nd.Cell("inner_Test_cell1", autobbox=True) as inner_main_cell:
    die_template(
        die_length=2*(die_length - 1500)+100,
        die_height=1.5*(die_height - 1400 - 215)-144.5,
        cleave_line=100.0,
        lap_line=0.0,
        cap_area=0.0,
        wg_etch_area=0.0,
        ebeam_marks_ncolumns=0,
        ebeam_marks_nrows=0,
    ).put()


with nd.Cell("TEST_CELL_2") as CELL_FIVE:
    inner_main_cell.put("cc", 0, 0, 180)

    # PLACEMENT OF ALL HEATERS: 3 length rows x 14 width variations
    start_x = -4600.0 - 5400.0
    start_y = 1200.0
    pitch_x = 900.0
    pitch_y = 700.0

    for row_n, heater_row in enumerate(heater_rows):
        current_y = start_y - (row_n * pitch_y)
        for i in range(0, 14):
            current_x = start_x + (i * pitch_x)
            heater_row[i].put(current_x, current_y)

    # PLACEMENT OF DUMBBELL TERMINATIONS: 3 length rows x 8 width variations
    start_x3 = -4600.0 - 5400.0
    start_y3 = start_y - (3 * pitch_y) - 400.0
    pitch_x3 = 800.0
    pitch_y3 = 600.0
    n_cols3 = 8

    for i, wrapper_cell in enumerate(dumbbell_lw_cells):
        row = i // n_cols3
        col = i % n_cols3
        wrapper_cell.put(start_x3 + (col * pitch_x3), start_y3 - (row * pitch_y3))


if __name__ == "__main__":
    cells = [CELL_FIVE]
    nd.export_gds(
        cells,
        filename=str(basedir / "local" / f"{outfile}.gds"),
    )
    # with open(basedir / "local" / f"{outfile}.yaml", "w") as f:
    #     yaml.safe_dump(test_cell_3_interface, f)
