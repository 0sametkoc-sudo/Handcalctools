"""HSB clevis workbook (recalculated by LibreOffice) vs. published values and the Python reference."""
import os

import pytest

from handcalc.hsb_clevis import joint
from handcalc import hsb_clevis_examples as ex
from tests.excel_recalc import recalc, value, soffice

XLSX = os.path.join(os.path.dirname(os.path.dirname(__file__)), "excel", "HSB_Clevis_Tool.xlsx")
try:
    soffice()
    HAVE_LO = True
except RuntimeError:
    HAVE_LO = False
pytestmark = pytest.mark.skipif(not HAVE_LO, reason="LibreOffice not installed")

ATTR = {"d": "d", "r": "r", "h": "h", "e": "e", "w": "w", "t": "t", "beta": "beta", "phi": "phi", "Rm": "Rm",
        "Rp": "Rp02", "Rb15": "Rbry15", "Rb20": "Rbry20", "bush": "bushing", "da": "da", "Rc": "Rc02"}
XL_KEYS = {"Ktb1": "k1", "H": "Hc", "Ktb": "Ktb", "KBR": "KBR", "F_Lu": "FLu", "F_Ly1": "FLy1", "ratio": "ratio",
           "C": "Cc", "F_Ly2": "FLy2", "Rbry": "Rbry", "F_Lybr": "FLybr", "F_B": "FB"}


def names_for(fem, mal, P, j, FF, share):
    n = {"P_lim": P, "j_sf": j, "FF_fit": FF, "share": share}
    for s, L in (("f", fem), ("m", mal)):
        for k, a in ATTR.items():
            v = getattr(L, a)
            if isinstance(v, bool):
                v = "YES" if v else "NO"
            n[f"{k}_{s}"] = v
    return n


CASES = {
    "HSB_EXAMPLE": (ex.HSB_FEMALE, ex.HSB_MALE, 20000, 1.5, 1.15, 0.5),
    "ECCENTRIC": (ex.ECC_FEMALE, ex.ECC_MALE, 15000, 1.5, 1.0, 0.6),
}


def test_published_hsb_example_in_excel():
    wb = recalc(XLSX, names_for(*CASES["HSB_EXAMPLE"]))
    assert value(wb, "chk_all") == "ALL OK"
    for key, (pf, pm) in ex.PUBLISHED.items():
        assert value(wb, XL_KEYS[key] + "_f") == pytest.approx(pf, rel=0.002), key
        assert value(wb, XL_KEYS[key] + "_m") == pytest.approx(pm, rel=0.002), key


@pytest.mark.parametrize("name", list(CASES))
def test_excel_matches_reference(name):
    fem, mal, P, j, FF, share = CASES[name]
    wb = recalc(XLSX, names_for(fem, mal, P, j, FF, share))
    ref = joint(fem, mal, P, j, FF, share)
    for s, rr in (("f", ref["female"]), ("m", ref["male"])):
        for key, xl in XL_KEYS.items():
            v = rr[key]
            if v is None:
                assert value(wb, f"{xl}_{s}") in (None, "")
            else:
                assert value(wb, f"{xl}_{s}") == pytest.approx(v, rel=1e-9), (s, key)
    assert value(wb, "RF_gov") == pytest.approx(ref["RF_gov"], rel=1e-9)
    ws = wb["Results"]
    statuses = [ws.cell(r, 8).value for r in range(12, 20)]
    order = ["F-case1", "F-case2", "F-case3", "F-bushing", "M-case1", "M-case2", "M-case3", "M-bushing"]
    assert statuses == [ref["modes"][k][1] for k in order]


def test_check_catches_full_width_input():
    n = names_for(*CASES["HSB_EXAMPLE"])
    n["w_f"] = 10  # smaller than d/2 -> net section undefined
    wb = recalc(XLSX, n)
    assert value(wb, "chk_all") == "CHECK INPUTS"
