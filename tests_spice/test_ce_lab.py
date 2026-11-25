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
        ("source_ampl", "0", "Source amplitude must be greater than 0.0"),
        ("source_freq", "1e7", "Source frequency must be less than or equal to 1000000.0"),
        ("rc", "-1", "RC must be greater than 0.0"),
        ("vbe", "0.01", "VBE must be greater than or equal to 0.1"),
        ("beta", "0", "Beta must be greater than or equal to 1.0"),
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


# Boundary inclusive/strict tests for the approved design bounds
@pytest.mark.parametrize(
    "field, value, should_pass, expected_error_substring",
    [
        ("beta", 1, True, None),      # beta ≥ 1 inclusive
        ("beta", 0, False, "Beta must be greater than or equal to 1.0"),
        ("vbe", 0.1, True, None),     # vbe 0.1–2.0 inclusive
        ("vbe", 2.0, True, None),
        ("vbe", 0.01, False, "VBE must be greater than or equal to 0.1"),
        ("source_ampl", 1.0, True, None),  # source amplitude >0 and ≤1 V
        ("source_ampl", 0.01, True, None),
        ("source_ampl", 0, False, "Source amplitude must be greater than 0.0"),
        ("source_freq", 1, True, None),        # source freq 1–1MHz inclusive
        ("source_freq", 1e6, True, None),
        ("source_freq", 1e7, False, "Source frequency must be less than or equal to 1000000.0"),
        ("rc", 0, False, "RC must be greater than 0.0"),   # strict >0 kΩ
        ("rc", 0.001, True, None),
    ],
)
def test_parse_spice_form_bounds(field, value, should_pass, expected_error_substring):
    form = {
        "vcc": "12", "rc": "2.2", "r1": "100", "r2": "22", "re": "1",
        "rl": "10", "beta": "100", "vbe": "0.7",
        "source_ampl": "0.010", "source_freq": "1000",
    }
    form[field] = str(value)
    result_values, errors = parse_spice_form(form)
    if should_pass:
        assert result_values is not None, f"{field}={value} should be valid but got result_values=None"
        assert errors == {}, f"{field}={value} should have no errors but got {errors}"
    else:
        assert result_values is None, f"{field}={value} should be invalid but got result_values={result_values}"
        assert (
            expected_error_substring in errors[field]
        ), f"{field}={value} should have error '{expected_error_substring}' but got {errors[field]}"
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
    # corroborate passthrough of other fields
    assert result_values["source_ampl"] == 0.01
    assert result_values["source_freq"] == 1000.0
    assert result_values["beta"] == 100
    assert result_values["vbe"] == 0.7


# ---------------------------------------------------------------------------
# Route tests (Step 4/5 of the brief)
# ---------------------------------------------------------------------------

def test_ce_lab_get_renders_skeleton():
    """GET /ce-lab renders the skeleton with nav links."""
    from app import create_app
    app = create_app()
    client = app.test_client()
    response = client.get("/ce-lab")
    assert response.status_code == 200
    html = response.data.decode()
    assert "CE Amplifier Lab" in html
    assert 'name="analysis"' in html
    assert "SPICE SIMULATION RESULTS (NGSPICE)" not in html.upper()


def test_ce_lab_nav_links():
    """Rendered HTML contains nav links to /, /spice, and /ce-lab."""
    from app import create_app
    app = create_app()
    client = app.test_client()
    response = client.get("/ce-lab")
    html = response.data.decode()
    assert 'href="/"' in html
    assert 'href="/spice"' in html
    assert 'href="/ce-lab"' in html


# ---------------------------------------------------------------------------
# POST dispatch + no-stale error rendering tests (Task 3)
# ---------------------------------------------------------------------------

import math
import re

import app as app_module
from bjt.spice_engine import (
    SpiceAcResult,
    SpiceEngineError,
    SpiceOpResult,
    SpiceTranResult,
)
from bjt.spice_metrics import ac_summary, tran_summary


CE_LAB_FORM = {
    "vcc": "12", "rc": "2.2", "r1": "100", "r2": "22", "re": "1",
    "rl": "10", "beta": "100", "vbe": "0.7",
    "source_ampl": "0.010", "source_freq": "1000",
}


def _synthetic_op_result():
    return SpiceOpResult(
        vb=2.0, ve=1.3, vc=7.0, vce=5.7,
        ic=0.0023, ib=0.000023, ie=0.002323,
        region="active",
        netlist="* synthetic op netlist",
        run_log="synthetic op run log",
    )


def _synthetic_ac_result():
    return SpiceAcResult(
        frequency=[10.0, 100.0, 1000.0, 10000.0, 100000.0],
        gain_db=[-20.0, 10.0, 20.0, 10.0, -20.0],
        phase_deg=[170.0, 175.0, 180.0, 175.0, 170.0],
        netlist="* synthetic ac netlist",
        run_log="synthetic ac run log",
    )


def _synthetic_tran_result():
    # 5 ms at 1000 Hz = five cycles; 101 samples.
    time = [i * 0.00005 for i in range(101)]
    vin = [0.01 * math.sin(2.0 * math.pi * 1000.0 * t) for t in time]
    vout = [-1.0 * math.sin(2.0 * math.pi * 1000.0 * t) for t in time]
    return SpiceTranResult(
        time=time, vin=vin, vout=vout,
        netlist="* synthetic tran netlist",
        run_log="synthetic tran run log",
    )


def _patch_engine(monkeypatch, fakes):
    """Patch every run_* so no test ever touches the real ngspice binary."""
    calls = {"op": 0, "ac": 0, "tran": 0}
    defaults = {
        "op": lambda p: _synthetic_op_result(),
        "ac": lambda p: _synthetic_ac_result(),
        "tran": lambda p: _synthetic_tran_result(),
    }

    def wrap(name):
        def run(p):
            calls[name] += 1
            return fakes.get(name, defaults[name])(p)
        return run

    monkeypatch.setattr(app_module, "run_op", wrap("op"))
    monkeypatch.setattr(app_module, "run_ac", wrap("ac"))
    monkeypatch.setattr(app_module, "run_tran", wrap("tran"))
    return calls


@pytest.mark.parametrize(
    "analysis, expected_call",
    [("op", "op"), ("ac", "ac"), ("tran", "tran")],
)
def test_ce_lab_run_dispatches_to_matching_engine(monkeypatch, analysis, expected_call):
    """Each analysis calls exactly its own engine function and shows SPICE provenance."""
    calls = _patch_engine(monkeypatch, {})

    response = app_module.create_app().test_client().post(
        "/ce-lab/run", data={**CE_LAB_FORM, "analysis": analysis}
    )

    assert response.status_code == 200
    assert calls[expected_call] == 1
    assert sum(calls.values()) == 1

    html = response.data.decode()
    assert "SPICE (ngspice)" in html
    assert "SPICE SIMULATION RESULTS (NGSPICE)" in html.upper()
    assert "DC Analytical" not in html
    assert "dc_bias.py" not in html
    assert re.search(r'<img[^>]+src="data:image/png;base64,', html)
    assert ".model QNPN NPN(IS=1e-14 BF=" in html
    assert "not instructor-verified" in html


def test_ce_lab_run_ac_derives_metrics_from_real_arrays(monkeypatch):
    """AC metrics on the page are derived from the parsed result arrays."""
    _patch_engine(monkeypatch, {})
    expected = ac_summary(_synthetic_ac_result(), 1000.0)

    response = app_module.create_app().test_client().post(
        "/ce-lab/run", data={**CE_LAB_FORM, "analysis": "ac"}
    )

    assert response.status_code == 200
    html = response.data.decode()
    assert f"{expected.gain_db_at_frequency:.2f}" in html
    assert f"{expected.midband_gain_db:.2f}" in html


def test_ce_lab_run_tran_derives_metrics_from_real_arrays(monkeypatch):
    """Transient metrics on the page are derived from the parsed result arrays."""
    _patch_engine(monkeypatch, {})
    expected = tran_summary(_synthetic_tran_result(), 1000.0)

    response = app_module.create_app().test_client().post(
        "/ce-lab/run", data={**CE_LAB_FORM, "analysis": "tran"}
    )

    assert response.status_code == 200
    html = response.data.decode()
    assert f"{expected.vout_peak_to_peak_v:.3f}" in html
    assert f"{expected.vin_peak_to_peak_v:.3f}" in html


def test_ce_lab_run_engine_error_renders_log_without_stale_success(monkeypatch):
    """A failing AC run renders the real engine log and no stale success state."""
    def boom(_params):
        raise SpiceEngineError("synthetic ngspice failure: log-token-XYZZY")

    _patch_engine(monkeypatch, {"ac": boom})

    response = app_module.create_app().test_client().post(
        "/ce-lab/run", data={**CE_LAB_FORM, "analysis": "ac"}
    )

    assert response.status_code == 200
    html = response.data.decode()
    assert "log-token-XYZZY" in html
    assert "ngspice run failed" in html
    assert "SPICE SIMULATION RESULTS (NGSPICE)" not in html.upper()
    assert "SPICE (ngspice)" not in html
    assert not re.search(r'<img[^>]+src="data:image/png', html)
    assert ".model QNPN" not in html


def test_ce_lab_run_processing_error_does_not_blame_engine(monkeypatch):
    """A metric/plot failure after a good run is labeled as processing, not engine."""
    _patch_engine(monkeypatch, {})

    def boom_metrics(_result, _source_freq):
        raise RuntimeError("metric derivation exploded: metric-token-ABC")

    monkeypatch.setattr(app_module, "ac_summary", boom_metrics)

    response = app_module.create_app().test_client().post(
        "/ce-lab/run", data={**CE_LAB_FORM, "analysis": "ac"}
    )

    assert response.status_code == 200
    html = response.data.decode()
    assert "CE lab processing error after ngspice run: metric derivation exploded: metric-token-ABC" in html
    assert "ngspice run failed" not in html
    assert "SPICE (ngspice)" not in html
    assert "SPICE SIMULATION RESULTS (NGSPICE)" not in html.upper()
    assert not re.search(r'<img[^>]+src="data:image/png', html)
    assert ".model QNPN" not in html


def test_ce_lab_run_validation_error_returns_400_and_calls_no_engine(monkeypatch):
    """Invalid input is rejected before any engine function is called."""
    calls = _patch_engine(monkeypatch, {})

    response = app_module.create_app().test_client().post(
        "/ce-lab/run",
        data={**CE_LAB_FORM, "analysis": "ac", "source_ampl": "0"},
    )

    assert response.status_code == 400
    assert calls == {"op": 0, "ac": 0, "tran": 0}
    html = response.data.decode()
    assert "Source amplitude must be greater than 0.0" in html
    assert "SPICE SIMULATION RESULTS (NGSPICE)" not in html.upper()
    assert "SPICE (ngspice)" not in html
    assert not re.search(r'<img[^>]+src="data:image/png', html)


# ---------------------------------------------------------------------------
# Task 4: schematic, parameter labels, and engineering result panels
# ---------------------------------------------------------------------------


def _ce_lab_get_html():
    return app_module.create_app().test_client().get("/ce-lab").data.decode()


def _ce_svg_block(html):
    match = re.search(
        r'<svg[^>]*aria-labelledby="ce-circuit-title ce-circuit-desc".*?</svg>',
        html,
        re.DOTALL,
    )
    assert match, "accessible CE circuit SVG with aria-labelledby not found"
    return match.group(0)


def _ce_result_section(html, section_id):
    match = re.search(
        rf'<section[^>]*id="{section_id}".*?</section>',
        html,
        re.DOTALL,
    )
    assert match, f"engineering result section #{section_id} not found"
    return match.group(0)


def test_ce_lab_schematic_has_all_components_and_no_fabricated_values():
    html = _ce_lab_get_html()
    svg = _ce_svg_block(html)

    assert (
        '<title id="ce-circuit-title">'
        "Common-emitter amplifier with voltage-divider bias"
        "</title>" in svg
    )
    assert re.search(r"<desc[^>]*>.+</desc>", svg, re.DOTALL)
    assert 'role="img"' in svg.split(">", 1)[0]

    for label in (
        "Q1", "NPN", "R1", "R2", "RC", "RE",
        "Cin", "Cout", "RL", "VCC", "Vin", "GND",
    ):
        assert re.search(rf">\s*{re.escape(label)}\s*<", svg), (
            f"component label {label!r} missing from schematic"
        )

    # No numeric voltage/current annotations may be drawn in the schematic.
    assert not re.search(r"\d+(?:\.\d+)?\s*(?:mV|µA|uA|mA|V|A)\b", svg)


def test_ce_lab_schematic_form_labels_have_units():
    html = _ce_lab_get_html()

    for label in (
        "VCC (V)",
        "RC (kΩ)",
        "R1 (kΩ)",
        "R2 (kΩ)",
        "RE (kΩ)",
        "RL (kΩ)",
        "Source amplitude (V)",
        "Source frequency (Hz)",
    ):
        assert label in html, f"parameter label/unit {label!r} missing"


def test_ce_lab_schematic_engineering_panel_names():
    html = _ce_lab_get_html()

    dc = _ce_result_section(html, "ce-dc-results")
    for name in ("VB", "VE", "VC", "VCE", "IB", "IC", "IE"):
        assert f">{name}<" in dc, f"DC quantity {name!r} missing"

    ac = _ce_result_section(html, "ce-ac-results")
    for name in ("Voltage Gain", "Phase", "Frequency", "Cutoff", "Bandwidth"):
        assert name in ac, f"AC quantity {name!r} missing"

    tran = _ce_result_section(html, "ce-tran-results")
    for name in ("Vin", "Vout", "Time"):
        assert name in tran, f"transient quantity {name!r} missing"


def test_ce_lab_schematic_result_placeholders_on_get():
    html = _ce_lab_get_html()

    for section_id in ("ce-dc-results", "ce-ac-results", "ce-tran-results"):
        section = _ce_result_section(html, section_id)
        assert "—" in section, f"no placeholder in #{section_id}"


def test_ce_lab_schematic_analysis_field_is_not_duplicated():
    html = _ce_lab_get_html()

    assert html.count('name="analysis"') == 1