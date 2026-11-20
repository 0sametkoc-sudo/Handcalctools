"""AFSAM workbook (recalculated by LibreOffice) vs. the Python reference and the published AFSAM examples."""
import dataclasses
import os

import pytest

from handcalc.afsam_lug import (double_shear, single_shear, transverse_oblique, multi_shear, design, AxialLug)
from handcalc import afsam_examples as ex
from tests.excel_recalc import recalc, value, soffice

XLSX = os.path.join(os.path.dirname(os.path.dirname(__file__)), "excel", "AFSAM_Lug_Tool.xlsx")
try:
    soffice()
    HAVE_LO = True
except RuntimeError:
    HAVE_LO = False
pytestmark = pytest.mark.skipif(not HAVE_LO, reason="LibreOffice not installed")


def lug_names(L, s):
    return {f"D_{s}": L.D, f"e_{s}": L.e, f"w_{s}": L.w, f"t_{s}": L.t, f"Ftu_{s}": L.Ftux, f"Fty_{s}": L.Ftyx,
            f"Em_{s}": L.E, f"eu_{s}": L.eu, f"FcyB_{s}": L.Fcy_B, f"Kov_{s}": L.K, f"Knov_{s}": L.Kn,
            f"cut_{s}": L.cutoff, f"cap_{s}": "YES" if L.thick_al_cap else "NO", f"Brat_{s}": L.B_ratio,
            f"Fbrum_{s}": L.Fbru_mat, f"Fbrym_{s}": L.Fbry_mat}


def joint_names(J):
    n = {**lug_names(J.outer, "o"), **lug_names(J.inner, "i")}
    n.update(Dp=J.Dp, Dpi=J.Di, FsuP=J.Fsu_P, FtuP=J.Ftu_P, kbP=J.kb_P, gap=J.g, FtuT1=J.Ftu_T1, wTo=J.wT1,
             FtuT2=J.Ftu_T2, wTi=J.wT2, kbT=J.kb_T, varb=J.variant, Plim=J.P_limit, UFa=J.UF, FFa=J.FF)
    return n


def check_joint(wb, ref):
    for s, lug in (("o", ref["outer"]), ("i", ref["inner"])):
        for key in ("K", "Kn", "Fbru", "Fbry", "Pbru", "Pnu", "PuL", "PuLB"):
            assert value(wb, f"{key}_{s}") == pytest.approx(lug[key], rel=1e-9), (s, key)
    for key, xl in (("PuLB", "PuLBj"), ("Pus", "Pus"), ("Pub", "Pub"), ("C", "Cj"), ("Pubmax", "Pubmax"),
                    ("b1", "b1min"), ("b2", "b2min"), ("P_all", "Pall")):
        assert value(wb, xl) == pytest.approx(ref[key], rel=1e-9), key


def test_afsam_96_published():
    J = ex.ex96()
    wb = recalc(XLSX, joint_names(J))
    assert value(wb, "chk_all") == "ALL OK"
    pub = ex.PUB_96
    assert value(wb, "Pbru_o") == pytest.approx(pub["outer_Pbru"], rel=0.005)
    assert value(wb, "PuB_o") == pytest.approx(pub["outer_PuB"], rel=0.005)
    assert value(wb, "Pbru_i") == pytest.approx(pub["inner_Pbru"], rel=0.005)
    assert value(wb, "Pus") == pytest.approx(pub["Pus"], rel=0.005)
    assert value(wb, "Pubmax") == pytest.approx(pub["Pubmax"], rel=0.005)
    assert value(wb, "Pall") == pytest.approx(pub["P_all"], rel=0.005)
    assert value(wb, "PTo") == pytest.approx(pub["PT1"], rel=0.005)
    check_joint(wb, double_shear(J))


JOINTS = {
    "AUTO_96": ex.ex96(True),
    # D/t > 5 (Fig 9-3) with cut-off B, Fty/Ftu between panels, thick-Al cap, eccentric material, no bushing inner
    "FIG93": dataclasses.replace(
        ex.ex96(True),
        outer=AxialLug(D=30, e=55, w=80, t=4, Ftux=480, Ftyx=420, E=71000, eu=0.08, Fcy_B=None, cutoff="B"),
        inner=AxialLug(D=30, e=48, w=90, t=5.5, Ftux=520, Ftyx=360, E=72000, eu=0.11, Fcy_B=400, cutoff="A",
                       thick_al_cap=True, B_ratio=0.9, Fbru_mat=900),
        Dp=26, Di=8, g=1.0, P_limit=15000),
}


@pytest.mark.parametrize("name", list(JOINTS))
def test_joint_matches_reference(name):
    J = JOINTS[name]
    wb = recalc(XLSX, joint_names(J))
    check_joint(wb, double_shear(J))


def test_other_sheets_match_reference():
    L = AxialLug(D=20, e=23.32, w=50, t=18, Ftux=750, Ftyx=500, E=200000, eu=0.12, Fcy_B=1170)
    Lt = AxialLug(D=20, e=30, w=60, t=12, Ftux=850, Ftyx=650, E=200000, eu=0.12, Fcy_B=1170)
    names = {**lug_names(L, "ss"), **lug_names(Lt, "tr")}
    names.update(ss_Dp=20, ss_Di=0, ss_Fsu=720, ss_Ftu=1200, ss_kbP=1.56, ss_kbL=1.4, ss_P=4000, ss_M=60000,
                 ss_UF=1.5, ss_FF=1.15, tr_h1=17, tr_h2=16, tr_h3=15, tr_h4=17, tr_Dp=20, tr_P=20000, tr_alpha=30,
                 tr_UF=1.5, tr_FF=1.15, ms_n=7, ms_P=60000, ms_t1=10, ms_t2=6, ms_Dp=20, ms_Di=0, ms_Fsu=720,
                 ms_Ftu=1200, ms_kbP=1.56, ms_PuL=None, ms_UF=1.5, ms_FF=1.15)
    wb = recalc(XLSX, names)
    s = single_shear(L, 20, 720, 1200, 4000, 60000)
    assert value(wb, "ss_sbr") == pytest.approx(s["s_br"], rel=1e-9)
    assert value(wb, "ss_tau") == pytest.approx(s["tau"], rel=1e-9)
    assert value(wb, "ss_sb") == pytest.approx(s["sb"], rel=1e-9)
    assert value(wb, "ss_RF") == pytest.approx(min(v for v in s["modes"].values() if v), rel=1e-9)
    t = transverse_oblique(Lt, 20, 17, 16, 15, 17, 20000, 30)
    assert value(wb, "tr_Ktru") == pytest.approx(t["Ktru"], rel=1e-9)
    assert value(wb, "tr_Pa") == pytest.approx(t["Palpha"], rel=1e-9)
    m = multi_shear(7, 60000, 10, 6, 20, 720, 1200)
    assert value(wb, "ms_tau") == pytest.approx(m["tau"], rel=1e-9)
    assert value(wb, "ms_sb") == pytest.approx(m["sb"], rel=1e-9)


def test_design_sheet_published():
    wb = recalc(XLSX)
    d = design(**ex.DESIGN_9141)
    for k, xl in (("fb1", "dz_fb1"), ("R", "dz_R"), ("Dp_shear", "dz_Dps"), ("Dp_bend1", "dz_Dpb1"), ("D", "dz_D"),
                  ("Dp_bend2", "dz_Dpb2"), ("Dp_opt", "dz_Dpopt")):
        assert value(wb, xl) == pytest.approx(d[k], rel=1e-9), k
        assert value(wb, xl) == pytest.approx(ex.PUB_9141[k], rel=0.01), k
