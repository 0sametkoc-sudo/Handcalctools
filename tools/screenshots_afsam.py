"""Screenshots of the AFSAM Lug workbook for the manual.   python tools/screenshots_afsam.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from screenshots_bolted_joint import ROOT, shot  # noqa: E402

X = os.path.join(ROOT, "excel", "AFSAM_Lug_Tool.xlsx")


def main():
    shot("afsams_input_lugs.png", "Input", 1, "Material bearing yield allowable", cols="B:G", xlsx=X)
    shot("afsams_input_joint.png", "Input", "2. PIN, GAP, TANGS", "ALL INPUT CHECKS", cols="B:G", xlsx=X)
    shot("afsams_results.png", "Results", 1, "MultiShear (9.13)", cols="B:H", xlsx=X)
    shot("afsams_calc_charts.png", "Calc", "Bearing coefficient K", "Lug-bushing ultimate load", cols="B:G", xlsx=X)
    shot("afsams_calc_joint.png", "Calc", "9.4  DOUBLE SHEAR JOINT", "Design ultimate load", cols="B:G", xlsx=X)
    shot("afsams_transverse.png", "Transverse_Oblique", "RESULTS", "GOVERNING", cols="B:F", xlsx=X)


if __name__ == "__main__":
    main()
