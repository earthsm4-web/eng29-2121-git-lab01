import pytest

from bjt.validate import parse_form

GOOD = {
    "vcc": "12", "r1": "47", "r2": "10", "rc": "4.7",
    "re": "1", "beta": "100", "vbe": "0.7",
}


def test_parses_form_into_si_units():
    params, errors = parse_form(GOOD)
    assert errors == {}
    assert params.vcc == 12.0
    assert params.r1 == pytest.approx(47_000.0)
    assert params.rc == pytest.approx(4_700.0)
    assert params.re == pytest.approx(1_000.0)
    assert params.beta == 100.0
    assert params.vbe == 0.7


def test_missing_field_is_required():
    form = dict(GOOD)
    del form["rc"]
    params, errors = parse_form(form)
    assert params is None
    assert errors["rc"] == "RC is required"


def test_blank_field_is_required():
    params, errors = parse_form(dict(GOOD, re="   "))
    assert params is None
    assert errors["re"] == "RE is required"


@pytest.mark.parametrize("raw", ["abc", "4,7", "1/2"])
def test_non_numeric_field_is_rejected(raw):
    params, errors = parse_form(dict(GOOD, rc=raw))
    assert params is None
    assert errors["rc"] == "RC must be a number"


@pytest.mark.parametrize(
    "field,raw,message",
    [
        ("vcc", "0", "VCC must be greater than 0"),
        ("r1", "-47", "R1 must be greater than 0"),
        ("r2", "0", "R2 must be greater than 0"),
        ("rc", "0", "RC must be greater than 0"),
        ("re", "0", "RE must be greater than 0"),
        ("vbe", "0", "VBE must be greater than 0"),
        ("beta", "1", "beta must be greater than 1"),
    ],
)
def test_range_violations_are_rejected(field, raw, message):
    params, errors = parse_form(dict(GOOD, **{field: raw}))
    assert params is None
    assert errors[field] == message


def test_vbe_at_or_above_vcc_is_rejected():
    params, errors = parse_form(dict(GOOD, vbe="12"))
    assert params is None
    assert errors["vbe"] == "VBE must be less than VCC"

    params, errors = parse_form(dict(GOOD, vbe="20"))
    assert params is None
    assert errors["vbe"] == "VBE must be less than VCC"


def test_scientific_notation_and_surrounding_space_are_accepted():
    params, errors = parse_form(dict(GOOD, rc=" 4.7e0 ", r1="47E3"))
    assert errors == {}
    assert params.rc == pytest.approx(4_700.0)
    assert params.r1 == pytest.approx(47_000_000.0)


def test_all_errors_are_reported_together():
    params, errors = parse_form({"vcc": "-1", "r1": "0", "r2": "0",
                                 "rc": "0", "re": "0", "beta": "0", "vbe": "0"})
    assert params is None
    assert set(errors) == {"vcc", "r1", "r2", "rc", "re", "beta", "vbe"}
