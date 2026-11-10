import pytest

from bjt.bias import VCE_SAT, Region, compare, solve, solve_approximate, solve_exact, solve_saturation
from bjt.params import BiasParams

LAB = BiasParams(vcc=12.0, r1=47_000.0, r2=10_000.0, rc=4_700.0,
                 re=1_000.0, beta=100.0, vbe=0.7)


def test_thevenin_quantities():
    assert LAB.vbb == pytest.approx(2.105263, rel=1e-5)
    assert LAB.rbb == pytest.approx(8245.614, rel=1e-5)


def test_exact_solver_matches_hand_calculation():
    r = solve_exact(LAB)
    assert r.ib == pytest.approx(12.8633e-6, rel=1e-5)
    assert r.ic == pytest.approx(1.28633e-3, rel=1e-5)
    assert r.ie == pytest.approx(1.29920e-3, rel=1e-5)
    assert r.ve == pytest.approx(1.29920, rel=1e-5)
    assert r.vb == pytest.approx(1.99920, rel=1e-5)
    assert r.vc == pytest.approx(5.95423, rel=1e-5)
    assert r.vce == pytest.approx(4.65503, rel=1e-5)
    assert r.region is Region.ACTIVE


def test_default_lab_values_are_active():
    assert solve(LAB).region is Region.ACTIVE


def test_cutoff_when_divider_cannot_forward_bias_junction():
    p = BiasParams(vcc=12.0, r1=100_000.0, r2=1_000.0, rc=4_700.0,
                   re=1_000.0, beta=100.0, vbe=0.7)
    r = solve(p)
    assert r.region is Region.CUTOFF
    assert (r.ib, r.ic, r.ie) == (0.0, 0.0, 0.0)
    assert r.ve == 0.0
    assert r.vce == pytest.approx(12.0)
    assert r.vc == pytest.approx(12.0)
    assert r.vb == pytest.approx(p.vbb)


def test_saturation_when_collector_resistor_too_large():
    p = BiasParams(vcc=12.0, r1=47_000.0, r2=10_000.0, rc=10_000.0,
                   re=1_000.0, beta=100.0, vbe=0.7)
    r = solve(p)
    assert r.region is Region.SATURATION
    assert r.vce == pytest.approx(VCE_SAT)
    assert r.ic == pytest.approx(1.071753e-3, rel=1e-5)
    assert r.ie == pytest.approx(1.082470e-3, rel=1e-5)
    assert r.ib == pytest.approx(1.071753e-5, rel=1e-5)
    assert r.active_valid is False


def test_saturation_boundary_is_decided_by_vce_at_or_below_threshold():
    below = BiasParams(vcc=12.0, r1=47_000.0, r2=10_000.0, rc=8_163.0,
                       re=1_000.0, beta=100.0, vbe=0.7)
    above = BiasParams(vcc=12.0, r1=47_000.0, r2=10_000.0, rc=8_164.0,
                       re=1_000.0, beta=100.0, vbe=0.7)
    assert solve(below).region is Region.ACTIVE
    assert solve(above).region is Region.SATURATION


def test_very_high_beta_converges_towards_approximate_values():
    p = BiasParams(vcc=12.0, r1=47_000.0, r2=10_000.0, rc=4_700.0,
                   re=1_000.0, beta=10_000.0, vbe=0.7)
    r = solve(p)
    assert r.region is Region.ACTIVE
    assert abs(r.vb - p.vbb) < 0.01
    assert r.ic > 0.0


def test_tiny_base_resistor_lands_in_saturation_without_dividing_by_zero():
    p = BiasParams(vcc=12.0, r1=1.0, r2=10_000.0, rc=4_700.0,
                   re=1_000.0, beta=100.0, vbe=0.7)
    r = solve(p)
    assert r.region is Region.SATURATION
    assert r.ic == pytest.approx(2.066550e-3, rel=1e-5)


def test_solve_saturation_is_consistent_with_kvl():
    p = BiasParams(vcc=12.0, r1=47_000.0, r2=10_000.0, rc=10_000.0,
                   re=1_000.0, beta=100.0, vbe=0.7)
    r = solve_saturation(p)
    assert r.ic * p.rc + r.vce + r.ie * p.re == pytest.approx(p.vcc, rel=1e-9)
    assert r.ib * p.beta == pytest.approx(r.ic, rel=1e-9)
    assert r.vb - r.ve == pytest.approx(p.vbe, rel=1e-9)

def test_approximate_solver_matches_hand_calculation():
    a = solve_approximate(LAB)
    assert a.ie == pytest.approx(1.405263e-3, rel=1e-5)
    assert a.ic == pytest.approx(1.405263e-3, rel=1e-5)
    assert a.ib == pytest.approx(1.405263e-5, rel=1e-5)
    assert a.vb == pytest.approx(2.105263, rel=1e-5)
    assert a.vc == pytest.approx(5.395263, rel=1e-5)
    assert a.vce == pytest.approx(3.990000, rel=1e-5)


def test_comparison_reports_signed_percent_differences():
    c = compare(LAB)
    assert c.stiff is True
    assert set(c.diffs) == {"ic", "ie", "vce", "vb"}
    assert c.diffs["ic"] == pytest.approx(9.2456, rel=1e-3)
    assert c.diffs["ie"] == pytest.approx(8.1637, rel=1e-3)
    assert c.diffs["vce"] == pytest.approx(-14.2859, rel=1e-3)
    assert c.diffs["vb"] == pytest.approx(5.3053, rel=1e-3)


def test_non_stiff_divider_is_flagged():
    p = BiasParams(vcc=12.0, r1=47_000.0, r2=10_000.0, rc=4_700.0,
                   re=1_000.0, beta=20.0, vbe=0.7)
    assert compare(p).stiff is False


def test_comparison_stiffness_boundary_is_inclusive():
    p = BiasParams(vcc=12.0, r1=47_000.0, r2=10_000.0, rc=4_700.0,
                   re=1_000.0, beta=100.0, vbe=0.7)
    assert p.beta * p.re == 10 * p.r2
    assert compare(p).stiff is True
