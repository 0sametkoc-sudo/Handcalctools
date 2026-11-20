import pytest
from handcalc.hsb_clevis import lug, joint, ktb1_straight, rbry, H_factor
from handcalc.hsb_clevis_examples import HSB_FEMALE, HSB_MALE, HSB_J, PUBLISHED, ECC_FEMALE, ECC_MALE


@pytest.mark.parametrize("i,L", [(0, HSB_FEMALE), (1, HSB_MALE)])
def test_hsb_worked_example(i, L):
    """All 24 published values of the HSB 26101-01 worked example within 0.2 %."""
    r = lug(L, HSB_J)
    for key, vals in PUBLISHED.items():
        assert r[key] == pytest.approx(vals[i], rel=0.002), key


def test_continuity_of_branches():
    a, _, _ = ktb1_straight(1.723, 90)
    b, _, _ = ktb1_straight(1.72300001, 90)
    assert a == pytest.approx(b, rel=2e-3)
    assert rbry(1.5, 500, 600) == pytest.approx(500)
    assert rbry(2.0, 500, 600) == pytest.approx(600)
    assert rbry(1.75, 500, 600) == pytest.approx(550)
    assert H_factor(1.0, 37) == pytest.approx(1.0)


def test_joint_load_share_and_rf():
    res = joint(HSB_FEMALE, HSB_MALE, P_limit=20000, j=1.5, FF=1.15)
    f, m = res["female"], res["male"]
    assert res["modes"]["F-case1"][0] == pytest.approx(f["F_Lu"] / (1.5 * 1.15 * 10000))
    assert res["modes"]["M-case2"][0] == pytest.approx(m["F_Ly"] / (1.5 * 1.15 * 20000))
    assert res["P_joint_cap"] == pytest.approx(min(2 * f["F_cap"], m["F_cap"]) / 1.15)


def test_no_bushing_is_na():
    res = joint(ECC_FEMALE, ECC_MALE, P_limit=10000)
    assert res["modes"]["F-bushing"] == (None, "N/A")
    assert res["female"]["H"] != pytest.approx(1.0)
