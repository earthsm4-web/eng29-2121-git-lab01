"""TDD tests for pure AC/transient metrics (Task 1)."""

import pytest

from bjt.spice_engine import SpiceAcResult, SpiceTranResult
from bjt.spice_metrics import ac_summary, tran_summary


# ---------------------------------------------------------------------------
# ac_summary tests
# ---------------------------------------------------------------------------


def test_ac_summary_finds_gain_phase_and_3db_bandwidth():
    result = SpiceAcResult(
        frequency=[1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0],
        gain_db=[-40.0, -10.0, 20.0, 20.0, -10.0, -40.0],
        phase_deg=[170.0, 175.0, 180.0, 180.0, 175.0, 170.0],
        netlist="",
        run_log="",
    )
    summary = ac_summary(result, 1000.0)
    assert summary.gain_db_at_frequency == 20.0
    assert summary.gain_frequency_hz == 1000.0
    assert summary.phase_deg_at_frequency == 180.0
    assert summary.midband_gain_db == 20.0
    assert summary.low_cutoff_hz is not None and 10.0 < summary.low_cutoff_hz < 100.0
    assert summary.high_cutoff_hz is not None and 1000.0 < summary.high_cutoff_hz < 10000.0
    assert summary.bandwidth_hz is not None and summary.bandwidth_hz > 0.0


def test_ac_summary_bandwidth_none_when_no_crossing():
    # Gain that never drops 3 dB below midband (all values at midband)
    result = SpiceAcResult(
        frequency=[1.0, 10.0, 100.0, 1000.0, 10000.0],
        gain_db=[20.0, 20.0, 20.0, 20.0, 20.0],
        phase_deg=[0.0, 0.0, 0.0, 0.0, 0.0],
        netlist="",
        run_log="",
    )
    summary = ac_summary(result, 1000.0)
    assert summary.bandwidth_hz is None
    assert "not found" in summary.cutoff_note


def test_ac_summary_gain_frequency_hz_returns_real_bin():
    # Target 950.0 Hz is not exactly in the array [1.0, 10.0, 100.0, 1000.0, ...]
    # The closest bin is 1000.0 (index 3), so gain_frequency_hz must be 1000.0
    result = SpiceAcResult(
        frequency=[1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0],
        gain_db=[-40.0, -10.0, 20.0, 20.0, -10.0, -40.0],
        phase_deg=[170.0, 175.0, 180.0, 180.0, 175.0, 170.0],
        netlist="",
        run_log="",
    )
    summary = ac_summary(result, 950.0)
    assert summary.gain_frequency_hz == 1000.0
    assert summary.gain_db_at_frequency == 20.0
    assert summary.phase_deg_at_frequency == 180.0


# ---------------------------------------------------------------------------
# tran_summary tests
# ---------------------------------------------------------------------------


def test_tran_summary_ignores_first_two_cycles():
    result = SpiceTranResult(
        time=[0.0, 0.001, 0.002, 0.003, 0.004],
        vin=[99.0, 1.0, -1.0, 1.0, -1.0],
        vout=[99.0, 2.0, -2.0, 2.0, -2.0],
        netlist="",
        run_log="",
    )
    summary = tran_summary(result, 1000.0)
    assert summary.analysis_window_start_s == 0.002
    assert summary.sample_count == 3
    assert summary.vin_peak_to_peak_v == 2.0
    assert summary.vout_peak_to_peak_v == 4.0
    assert summary.time_s == 0.004


def test_tran_summary_raises_on_zero_freq():
    result = SpiceTranResult(
        time=[0.0, 0.001, 0.002],
        vin=[1.0, 2.0, 3.0],
        vout=[1.0, 2.0, 3.0],
        netlist="",
        run_log="",
    )
    with pytest.raises(ValueError):
        tran_summary(result, 0.0)


def test_tran_summary_short_record_raises_valueerror():
    # Two cycles at 1000 Hz = 2ms window, but record only has 0.0001s
    result = SpiceTranResult(
        time=[0.0, 0.0001],
        vin=[1.0, 2.0],
        vout=[1.0, 2.0],
        netlist="",
        run_log="",
    )
    with pytest.raises(ValueError):
        tran_summary(result, 1000.0)


def test_tran_summary_empty_time_raises_valueerror():
    result = SpiceTranResult(
        time=[],
        vin=[1.0],
        vout=[1.0],
        netlist="",
        run_log="",
    )
    with pytest.raises(ValueError):
        tran_summary(result, 1000.0)


def test_tran_summary_empty_vin_raises_valueerror():
    result = SpiceTranResult(
        time=[0.0, 0.001],
        vin=[],
        vout=[1.0],
        netlist="",
        run_log="",
    )
    with pytest.raises(ValueError):
        tran_summary(result, 1000.0)


def test_tran_summary_empty_vout_raises_valueerror():
    result = SpiceTranResult(
        time=[0.0, 0.001],
        vin=[1.0, 2.0],
        vout=[],
        netlist="",
        run_log="",
    )
    with pytest.raises(ValueError):
        tran_summary(result, 1000.0)


def test_tran_summary_mismatched_lengths_raises_valueerror():
    result = SpiceTranResult(
        time=[0.0, 0.001, 0.002],
        vin=[1.0, 2.0],
        vout=[1.0, 2.0, 3.0, 4.0],
        netlist="",
        run_log="",
    )
    with pytest.raises(ValueError):
        tran_summary(result, 1000.0)


# ---------------------------------------------------------------------------
# parse_spice_form validation tests
# ---------------------------------------------------------------------------

import pytest

from app import parse_spice_form


@pytest.mark.parametrize(
    "field, value, expected_error_substring",
    [
        ("source_ampl", "0", "Source amplitude must be greater than 0"),
        ("source_freq", "1e7", "Source frequency must be less than or equal to 1000000.0"),
        ("rc", "-1", "RC must be greater than 0"),
        ("vbe", "0.01", "VBE must be greater than 0.1"),
        ("beta", "0", "Beta must be greater than 1"),
        ("vcc", "abc", "VCC must be a number"),
    ],
)
def test_parse_spice_form_invalid(field, value, expected_error_substring):
    form = {
        "vcc": "12", "rc": "2.2", "r1": "100", "r2": "22", "re": "1",
        "rl": "10", "beta": "100", "vbe": "0.7",
        "source_ampl": "0.010", "source_freq": "1000",
    }
    form[field] = value
    result_values, errors = parse_spice_form(form)
    assert result_values is None
    assert field in errors
    assert expected_error_substring in errors[field]


def test_parse_spice_form_valid():
    form = {
        "vcc": "12", "rc": "2.2", "r1": "100", "r2": "22", "re": "1",
        "rl": "10", "beta": "100", "vbe": "0.7",
        "source_ampl": "0.010", "source_freq": "1000",
    }
    result_values, errors = parse_spice_form(form)
    assert result_values is not None
    assert errors == {}
    # kΩ → Ω conversion: rc and r1 are the resistances that get converted
    assert result_values["rc"] == 2200.0
    assert result_values["r1"] == 100000.0