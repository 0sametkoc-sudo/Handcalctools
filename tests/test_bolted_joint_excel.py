"""Check the Excel workbook (recalculated by LibreOffice) against the Python reference."""
import dataclasses
import os

import openpyxl
import pytest

from handcalc.bolted_joint import analyse
from handcalc import bolted_joint_examples as ex
from tests.excel_recalc import recalc, value, soffice

XLSX = os.path.join(os.path.dirname(os.path.dirname(__file__)), "excel", "Bolted_Joint_Tool.xlsx")

try:
    soffice()
    HAVE_LO = True
except RuntimeError:
    HAVE_LO = False
pytestmark = pytest.mark.skipif(not HAVE_LO, reason="LibreOffice not installed")

FIELDS = {  # Excel input name -> attribute
    "ftype": "fastener_type", "d_in": "d", "dp_in": "dp", "dr_in": "dr", "ds_in": "d_s", "dps_in": "dp_s",
    "drs_in": "dr_s", "dsh_in": "d_shank", "L_f": "L", "LT_f": "LT", "LT_s": "LT_s", "Le_nut": "Le_nut",
    "Le_h": "Le_h", "Dw_top": "Dw_top", "Dw_bot_in": "Dw_bot", "alpha_deg": "alpha", "Ef": "Ef", "Fty": "Fty",
    "Ftu": "Ftu", "Fsu_in": "Fsu", "Fsu_nut": "Fsu_nut", "Fsu_h": "Fsu_h", "Pex_in": "Pex", "Pshear": "Pshear",
    "UF_ult": "UF", "FF_fit": "FF", "CF_cast": "CF", "T_tq": "T", "K_nut": "K", "mu_f": "mu", "Gamma_s": "Gamma",
    "fz_e": "fz", "thr_sh": "threads_in_shear_plane", "D_hole": "D_hole", "p_allow": "p_allow", "t_plate": "t_min",
    "Fbru": "Fbru", "P_alt": "P_alt", "P_mean_in": "P_mean", "Se_f": "Se",
}


def excel_inputs(case):
    names = {"thread_n": "CUSTOM", "thread_s": "CUSTOM"}
    for n, attr in FIELDS.items():
        v = getattr(case, attr)
        if isinstance(v, bool):
            v = "YES" if v else "NO"
        names[n] = v
    wb = openpyxl.load_workbook(XLSX)
    sh, rng = wb.defined_names["lay_t"].attr_text.split("!")
    first = int(rng.split(":")[0].split("$")[-1])
    last = int(rng.split(":")[1].split("$")[-1])
    cells = {}
    for i, row in enumerate(range(first, last + 1)):
        L = case.layers[i] if i < len(case.layers) else None
        cells[f"Input!D{row}"] = L.t if L else None
        cells[f"Input!F{row}"] = L.E if L else None
    return names, cells


CASES = dict(ex.ALL)
CASES["BOLT_SHEAR_FULL"] = dataclasses.replace(
    ex.OLD_BOLT, Pshear=4000, Gamma=0.3, fz=0.006, D_hole=13, p_allow=400, t_min=12, Fbru=600,
    P_alt=900, P_mean=900, Se=162, Fsu_nut=500,
    layers=[ex.Layer(21.245, 210000), ex.Layer(12, 70000), ex.Layer(3, 210000)])  # thick plate on top
CASES["BOLT_NEGATIVE_LOAD"] = dataclasses.replace(ex.OLD_BOLT, Pex=-500, Pshear=0)


@pytest.mark.parametrize("name", list(CASES))
def test_excel_matches_reference(name):
    case = CASES[name]
    names, cells = excel_inputs(case)
    wb = recalc(XLSX, names, cells)
    ref = analyse(case)
    assert value(wb, "chk_all") == "ALL OK"
    for key, xl in [("kf", "kf"), ("km", "km"), ("Fpre", "Fpre"), ("T_min", "T_min"), ("T_max", "T_max"),
                    ("Pf", "Pf"), ("Fpre_min", "Fpre_min")]:
        assert value(wb, xl) == pytest.approx(ref[key], rel=1e-9, abs=1e-9), key
    ws = wb["Results"]
    rows = {ws.cell(r, 2).value: (ws.cell(r, 4).value, ws.cell(r, 5).value) for r in range(1, 40)}
    for fid, (rf, st) in ref["fm"].items():
        xl_rf, xl_st = rows[fid]
        assert xl_st == st, fid
        if rf is None:
            assert xl_rf in (None, ""), fid
        else:
            assert xl_rf == pytest.approx(rf, rel=1e-9), fid
    assert value(wb, "RF_gov") == pytest.approx(ref["RF_gov"], rel=1e-9)


def test_input_check_catches_bad_stack():
    names, cells = excel_inputs(ex.OLD_BOLT)
    names["Dw_top"] = 10  # smaller than d = 12
    wb = recalc(XLSX, names, cells)
    assert value(wb, "chk_all") == "CHECK INPUTS"
    assert value(wb, "status_all").startswith("INPUT ERROR")
