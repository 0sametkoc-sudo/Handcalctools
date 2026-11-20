"""Recalculate an .xlsx with LibreOffice (headless) and read the values back.

Used by the tests so that the Excel formulas themselves are checked, not a copy of them.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

import openpyxl

_PROFILE = os.path.join(tempfile.gettempdir(), "handcalc_lo_profile")
_XCU = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value></prop></item>
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="ODFRecalcMode" oor:op="fuse"><value>0</value></prop></item>
</oor:items>
"""


def _profile():
    user = os.path.join(_PROFILE, "user")
    os.makedirs(user, exist_ok=True)
    with open(os.path.join(user, "registrymodifications.xcu"), "w") as f:
        f.write(_XCU)
    return "file://" + _PROFILE


def soffice():
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        raise RuntimeError("LibreOffice (soffice) not found")
    return exe


def recalc(path: str, set_names: dict | None = None, set_cells: dict | None = None) -> openpyxl.Workbook:
    """Copy the workbook, write inputs (by defined name or 'Sheet!A1'), recalc, return data-only workbook."""
    tmp = tempfile.mkdtemp(prefix="handcalc_")
    src = os.path.join(tmp, "in.xlsx")
    wb = openpyxl.load_workbook(path)
    for name, value in (set_names or {}).items():
        dest = wb.defined_names[name].attr_text  # e.g. Input!$D$8
        sh, ref = dest.split("!")
        wb[sh.strip("'")][ref.replace("$", "")].value = value
    for addr, value in (set_cells or {}).items():
        sh, ref = addr.split("!")
        wb[sh][ref].value = value
    wb.save(src)
    out = os.path.join(tmp, "out")
    os.makedirs(out)
    subprocess.run([soffice(), f"-env:UserInstallation={_profile()}", "--headless", "--calc",
                    "--convert-to", "xlsx", "--outdir", out, src],
                   check=True, capture_output=True, timeout=180)
    return openpyxl.load_workbook(os.path.join(out, "in.xlsx"), data_only=True)


def value(wb: openpyxl.Workbook, name: str):
    """Value of a single-cell defined name."""
    dest = wb.defined_names[name].attr_text
    sh, ref = dest.split("!")
    return wb[sh.strip("'")][ref.replace("$", "")].value
