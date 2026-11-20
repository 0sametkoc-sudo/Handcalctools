import pytest
from handcalc.afsam_lug import double_shear, design, k_fig9_2, k_fig9_3, kn_fig9_4, k_fig9_8, axial_lug, AxialLug
from handcalc.afsam_examples import ex96, PUB_96, CHART_96, DESIGN_9141, PUB_9141


def vals(r):
    return dict(outer_Pbru=r['outer']['Pbru'], outer_PuB=r['outer']['PuB'], outer_PuLB=r['outer']['PuLB'],
                inner_Pbru=r['inner']['Pbru'], inner_PuB=r['inner']['PuB'], inner_PuLB=r['inner']['PuLB'],
                PuLB=r['PuLB'], Pus=r['Pus'], Pub=r['Pub'], C=r['C'], Pubmax=r['Pubmax'], b1=r['b1'], b2=r['b2'],
                P_all=r['P_all'], PT1=r['PT1'], PT2=r['PT2'])


def test_afsam_96_published_with_published_chart_readings():
    """AFSAM 9.6: all 16 published values within 0.5 % (AFSAM prints 3 significant figures)."""
    v = vals(double_shear(ex96()))
    for k, ref in PUB_96.items():
        assert v[k] == pytest.approx(ref, rel=0.005), k


def test_afsam_96_digitized_charts_reproduce_published_readings():
    """The digitized Fig 9-2 / 9-4 give the chart readings printed in the example within 0.01."""
    r = double_shear(ex96(auto_charts=True))
    assert r['outer']['K'] == pytest.approx(CHART_96['K_outer'], abs=0.01)
    assert r['inner']['K'] == pytest.approx(CHART_96['K_inner'], abs=0.01)
    assert r['outer']['Kn'] == pytest.approx(CHART_96['Kn_outer'], abs=0.01)
    assert r['inner']['Kn'] == pytest.approx(CHART_96['Kn_inner'], abs=0.01)
    assert r['P_all'] == pytest.approx(PUB_96['P_all'], rel=0.005)


def test_afsam_9141_design_example():
    d = design(**DESIGN_9141)
    for k, ref in PUB_9141.items():
        assert d[k] == pytest.approx(ref, rel=0.01), k


def test_chart_sanity():
    assert k_fig9_2(1.5) == pytest.approx(1.33, abs=0.01)       # minimum of Fig 9-2
    assert k_fig9_3(0.5, 10) < 0.06                              # curves start at e/D = 0.5
    assert k_fig9_3(4.0, 2) == pytest.approx(2.95, abs=0.02)
    assert k_fig9_3(4.0, 30) == pytest.approx(0.41, abs=0.02)
    assert k_fig9_3(3.0, 2, "B") == pytest.approx(1.12, abs=0.02)   # cut-off B
    assert kn_fig9_4(1.0, 0.8, 0.5) == pytest.approx(1.0, abs=1e-9)
    assert kn_fig9_4(0.0, 0.8, 0.5) == pytest.approx(0.0, abs=1e-9)
    ku, ky = k_fig9_8(1.4)
    assert ku > ky


def test_fig9_3_monotonic():
    for d in (2, 5, 10, 30):
        prev = -1
        for i in range(50, 401, 5):
            k = k_fig9_3(i / 100, d)
            assert k >= prev - 1e-9
            prev = k


def test_fig9_3_entered_with_centre_to_edge_distance():
    """D/t <= 2: Fig 9-3 (K D t Ftu) agrees with Fig 9-2 (K a t Ftu) within ~10 % at e/D = 1.0 ... 2.0."""
    for ed in (1.0, 1.25, 1.5, 2.0):
        f92 = k_fig9_2(ed) * ((ed - 0.5) if ed < 1.5 else 1.0)
        assert k_fig9_3(ed, 2) == pytest.approx(f92, rel=0.12)
