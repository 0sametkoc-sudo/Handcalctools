import math
import pytest
from handcalc.bolted_joint import analyse, member_stiffness, Layer, BoltedJointInput
from handcalc.bolted_joint_examples import DOC_STUD, OLD_BOLT


def rel(a, b):
    return abs(a / b - 1)


def test_doc_member_stiffness_table5():
    """In-house method document Table 5: k_members = 620 902 N/mm."""
    r = analyse(DOC_STUD)
    assert rel(r["km"], 620902) < 0.002
    # split of the housing at mid-grip: t_middle = 2.0 mm, t2new = 15.62 mm (Table 3)
    tu, Du, tl, Dl, _ = r["layers"][3]
    assert tu == pytest.approx(2.0, abs=0.005)
    assert tl == pytest.approx(15.62, abs=0.005)
    assert Du == pytest.approx(28.94, abs=0.01)   # D*
    assert r["layers"][1][1] == pytest.approx(14.14, abs=0.01)  # Dw2
    assert r["layers"][2][1] == pytest.approx(15.08, abs=0.01)  # Dn1


def test_doc_fastener_stiffness_table5():
    """Table 5: kf = 351 941 N/mm (areas from min diameters, ~0.3 % area difference)."""
    r = analyse(DOC_STUD)
    assert r["ld"] == pytest.approx(12.39, abs=0.01)
    assert r["lt"] == pytest.approx(4.9056, abs=0.01)
    assert rel(r["kf"], 351941) < 0.01


def test_symmetric_two_plate_closed_form():
    """Two identical plates, equal bearing diameters -> Shigley closed form (eq. 8-22)."""
    d, D, E, t = 10.0, 15.0, 207000.0, 12.0
    km, _ = member_stiffness([Layer(t, E), Layer(t, E)], d, D, D, 30)
    l = 2 * t
    ta = math.tan(math.radians(30))
    ref = math.pi * ta * E * d / (2 * math.log((2 * (l / 2) * ta + D - d) * (D + d) /
                                                 ((2 * (l / 2) * ta + D + d) * (D - d))))
    assert km == pytest.approx(ref, rel=1e-12)


def test_layer_order_and_split_invariance():
    """Splitting a plate into two identical sub-layers must not change k_members."""
    a, _ = member_stiffness([Layer(5, 70000), Layer(20, 210000)], 8, 13, 13, 30)
    b, _ = member_stiffness([Layer(5, 70000), Layer(8, 210000), Layer(12, 210000)], 8, 13, 13, 30)
    assert a == pytest.approx(b, rel=1e-12)


def test_thick_top_plate_is_split_correctly():
    """Mid-plane inside the top plate (old tools failed here: negative t_middle)."""
    km, det = member_stiffness([Layer(25, 210000), Layer(5, 210000)], 10, 15, 15, 30)
    assert det[0][0] == pytest.approx(15) and det[0][2] == pytest.approx(10)
    ref, _ = member_stiffness([Layer(30, 210000)], 10, 15, 15, 30)
    assert km == pytest.approx(ref, rel=1e-12)


def test_old_bolt_sheet_regression():
    """Stiffness, preload and load sharing of the previous tool's Bolt sheet example."""
    r = analyse(OLD_BOLT)
    assert r["kf"] == pytest.approx(482031.3649, rel=1e-8)
    assert r["km"] == pytest.approx(2282980.6059, rel=1e-8)
    assert r["Fpre"] == pytest.approx(54583.3333, rel=1e-8)
    assert r["fm"]["FM01"][0] == pytest.approx(1.6577376, rel=1e-6)


def test_thread_stripping_follows_method_document():
    """RF = FSu / (1.5 FF fs), fs = (Fpre + Pf)/AS  (1.5 on the total limit load)."""
    r = analyse(OLD_BOLT)
    As = math.pi * 10.863 * 5 / 8 * 10
    fs = (r["Fpre"] + r["Pf"]) / As
    assert r["fm"]["FM03"][0] == pytest.approx(720 / (1.5 * 1.0 * fs))
    assert r["fm"]["FM03"][0] == pytest.approx(1.865, abs=0.001)


def test_applicability():
    r = analyse(OLD_BOLT)
    assert r["fm"]["FM04"][1] == "N/A"          # bolt with nut: no housing thread
    assert r["fm"]["FM11"][1] == "NOT EVALUATED"  # allowable pressure not given
    s = analyse(DOC_STUD)
    assert s["fm"]["FM03"][1] != "N/A" and s["fm"]["FM04"][1] != "N/A"


def test_torque_window_brackets_rf_one():
    """At T = T_max the governing strength RF (yield / stripping) is exactly 1."""
    r = analyse(OLD_BOLT)
    import dataclasses
    rr = analyse(dataclasses.replace(OLD_BOLT, T=r["T_max"]))
    lims = [rr["fm"][k][0] for k in ("FM01", "FM02", "FM03")]
    assert min(lims) == pytest.approx(1.0, rel=1e-9)
