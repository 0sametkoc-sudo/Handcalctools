"""Screenshots of cell ranges of the recalculated workbook, for the manual.

Each shot: copy the workbook, keep one sheet visible, set its print area, export to PDF with
LibreOffice, render page 1 to PNG and trim.     python tools/screenshots_bolted_joint.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

import openpyxl
from PIL import Image, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.excel_recalc import _profile, soffice  # noqa: E402

XLSX = os.path.join(ROOT, "excel", "Bolted_Joint_Tool.xlsx")
OUT = os.path.join(ROOT, "docs", "figures")


def find_row(ws, text, col=None):
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith(text) and (col is None or c.column == col):
                return c.row
    raise KeyError(text)


def trim(im, pad=10):
    bg = Image.new(im.mode, im.size, (255, 255, 255))
    box = ImageChops.difference(im, bg).getbbox()
    l, t, r, b = box
    return im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))


_RECALC = {}


def recalculated(xlsx=XLSX):
    """Recalculate once with LibreOffice; return path of an .xlsx whose cells hold values."""
    if xlsx not in _RECALC:
        tmp = tempfile.mkdtemp()
        subprocess.run([soffice(), f"-env:UserInstallation={_profile()}", "--headless", "--calc", "--convert-to",
                        "xlsx", "--outdir", tmp, xlsx], check=True, capture_output=True, timeout=180)
        wb = openpyxl.load_workbook(os.path.join(tmp, os.path.basename(xlsx)), data_only=True)
        _RECALC[xlsx] = os.path.join(tmp, "values.xlsx")
        wb.save(_RECALC[xlsx])
    return _RECALC[xlsx]


def shot(name, sheet, first_marker, last_marker, cols="B:H", extra_rows=0, xlsx=XLSX):
    tmp = tempfile.mkdtemp()
    wb = openpyxl.load_workbook(recalculated(xlsx))
    ws = wb[sheet]
    r0 = find_row(ws, first_marker) if isinstance(first_marker, str) else first_marker
    r1 = (find_row(ws, last_marker) if isinstance(last_marker, str) else last_marker) + extra_rows
    for other in list(wb.worksheets):
        if other.title != sheet:
            wb.remove(other)
    for n in list(wb.defined_names):
        del wb.defined_names[n]
    ws._images = []
    c0, c1 = cols.split(":")
    ws.print_area = f"{c0}{r0}:{c1}{r1}"
    ws.freeze_panes = None
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    src = os.path.join(tmp, "s.xlsx")
    wb.save(src)
    subprocess.run([soffice(), f"-env:UserInstallation={_profile()}", "--headless", "--convert-to", "pdf",
                    "--outdir", tmp, src], check=True, capture_output=True, timeout=180)
    subprocess.run(["pdftoppm", "-r", "150", "-png", "-f", "1", "-l", "1", "-singlefile",
                    os.path.join(tmp, "s.pdf"), os.path.join(tmp, "p")], check=True)
    trim(Image.open(os.path.join(tmp, "p.png")).convert("RGB")).save(os.path.join(OUT, name))
    shutil.rmtree(tmp)


def main():
    shot("bjs_input_thread.png", "Input", 1, "3. JOINT STACK", extra_rows=-1)
    shot("bjs_input_stack.png", "Input", "3. JOINT STACK", "Pressure-cone half angle")
    shot("bjs_input_loads.png", "Input", "4. MATERIALS", "Embedment (settlement) loss")
    shot("bjs_input_optional.png", "Input", "7. INPUTS FOR THE OPTIONAL", "ALL INPUT CHECKS")
    shot("bjs_results.png", "Results", 1, "FM16", cols="B:I")
    shot("bjs_results_torque.png", "Results", "TIGHTENING TORQUE WINDOW", "Tensile stress area At", cols="C:E")
    shot("bjs_calc_layers.png", "Calc", "D. Member stiffness", "External load taken from the members", cols="B:L")
    shot("bjs_calc_rf.png", "Calc", "H. Reserve factors", "Tightening torque window", cols="B:G")
    print(OUT)


if __name__ == "__main__":
    main()
