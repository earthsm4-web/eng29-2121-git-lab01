import pytest

from bjt.bias import solve
from bjt.format import fmt_num, fmt_r
from bjt.params import BiasParams
from bjt.steps import steps_for

LAB = BiasParams(vcc=12.0, r1=47_000.0, r2=10_000.0, rc=4_700.0,
                 re=1_000.0, beta=100.0, vbe=0.7)

SATURATED = BiasParams(vcc=12.0, r1=47_000.0, r2=10_000.0, rc=10_000.0,
                       re=1_000.0, beta=100.0, vbe=0.7)

OFF = BiasParams(vcc=12.0, r1=100_000.0, r2=1_000.0, rc=4_700.0,
                 re=1_000.0, beta=100.0, vbe=0.7)


def test_resistance_formatter_uses_kilo_ohms():
    assert fmt_r(47_000.0) == "47 kΩ"
    assert fmt_r(4_700.0) == "4.7 kΩ"
    assert fmt_r(8245.614035) == "8.2456 kΩ"


def test_plain_number_formatter_trims_trailing_zeros():
    assert fmt_num(12.0) == "12"
    assert fmt_num(4.7) == "4.7"
    assert fmt_num(101.0) == "101"


def test_active_walkthrough_has_nine_rows_in_derivation_order():
    steps = steps_for(LAB, solve(LAB))
    assert [s.quantity for s in steps] == [
        "VBB", "RB", "IB", "IC", "IE", "VE", "VB", "VC", "VCE",
    ]
    assert [s.result for s in steps] == [
        "2.1053 V", "8.2456 kΩ", "12.863 µA", "1.2863 mA", "1.2992 mA",
        "1.2992 V", "1.9992 V", "5.9542 V", "4.6550 V",
    ]


def test_active_walkthrough_shows_the_arithmetic():
    by_quantity = {s.quantity: s for s in steps_for(LAB, solve(LAB))}
    assert by_quantity["VBB"].substitution == "12 · 10 / (47 + 10)"
    assert by_quantity["RB"].substitution == "(47 · 10) / (47 + 10)"
    assert by_quantity["IB"].substitution == "(2.1053 − 0.7) / (8.2456 + 101 · 1)"
    assert by_quantity["VBB"].formula == "VBB = VCC · R2 / (R1 + R2)"
    assert by_quantity["IB"].formula == "IB = (VBB − VBE) / (RB + (β+1) · RE)"


def test_saturation_walkthrough_shows_the_pinned_vce_solve():
    steps = steps_for(SATURATED, solve(SATURATED))
    assert [s.quantity for s in steps] == ["IC", "IB", "IE", "VE"]
    assert steps[0].result == "1.0718 mA"
    assert steps[0].substitution == "(12 − 0.2) / (10 + 1 · 101/100)"
    assert steps[-1].result == "1.0825 V"


def test_cutoff_walkthrough_compares_divider_voltage_with_vbe():
    steps = steps_for(OFF, solve(OFF))
    assert [s.quantity for s in steps] == ["VBB", "IB"]
    assert steps[0].result == "0.1188 V"
    assert steps[1].substitution == "0.1188 ≤ 0.7"
    assert steps[1].result == "0.000 µA"
