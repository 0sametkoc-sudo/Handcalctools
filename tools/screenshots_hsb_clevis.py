"""Screenshots of the HSB clevis workbook for the manual.   python tools/screenshots_hsb_clevis.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from screenshots_bolted_joint import ROOT, shot  # noqa: E402

X = os.path.join(ROOT, "excel", "HSB_Clevis_Tool.xlsx")


def main():
    shot("hsbs_input.png", "Input", 1, "Bushing compressive yield strength", cols="B:G", xlsx=X)
    shot("hsbs_input_joint.png", "Input", "4. JOINT LOAD", "ALL INPUT CHECKS", cols="B:G", xlsx=X)
    shot("hsbs_results.png", "Results", 1, "Notes", cols="B:I", extra_rows=3, xlsx=X)
    shot("hsbs_calc.png", "Calc", 1, "RF bushing", cols="B:G", xlsx=X)


if __name__ == "__main__":
    main()
