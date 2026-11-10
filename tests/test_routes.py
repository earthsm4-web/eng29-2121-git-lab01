import pytest

from app import app

GOOD = {
    "vcc": "12", "r1": "47", "r2": "10", "rc": "4.7",
    "re": "1", "beta": "100", "vbe": "0.7",
}


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


def test_index_renders_form_with_lab_defaults(client):
    html = client.get("/").get_data(as_text=True)
    for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
        assert f'name="{field}"' in html
    assert 'value="47"' in html
    assert 'value="100"' in html


def test_calculate_renders_active_result_with_units(client):
    rv = client.post("/calculate", data=GOOD)
    assert rv.status_code == 200
    html = rv.get_data(as_text=True)
    assert "Active" in html
    assert "1.2863 mA" in html
    assert "4.6550 V" in html
    assert "12.863" in html


def test_calculate_renders_comparison_table_when_active(client):
    html = client.post("/calculate", data=GOOD).get_data(as_text=True)
    assert "Approximate" in html
    assert "9.24" in html
    assert "-14.28" in html


def test_invalid_input_returns_400_and_keeps_typed_values(client):
    rv = client.post("/calculate", data=dict(GOOD, re="0", rc="9.1"))
    assert rv.status_code == 400
    html = rv.get_data(as_text=True)
    assert "RE must be greater than 0" in html
    assert 'value="9.1"' in html


def test_cutoff_has_no_comparison_table(client):
    html = client.post("/calculate", data=dict(GOOD, r1="100", r2="1")).get_data(as_text=True)
    assert "Cutoff" in html
    assert "Approximate" not in html


def test_saturation_warns_that_active_equations_do_not_apply(client):
    html = client.post("/calculate", data=dict(GOOD, rc="10")).get_data(as_text=True)
    assert "Saturation" in html
    assert "do not apply" in html


def test_active_page_shows_schematic_and_walkthrough(client):
    html = client.post("/calculate", data=GOOD).get_data(as_text=True)
    assert 'class="schematic"' in html
    assert "R1 47 kΩ" in html
    assert "RB = R1 ∥ R2" in html
    assert "4.6550 V" in html


def test_cutoff_page_still_shows_the_walkthrough(client):
    html = client.post("/calculate", data=dict(GOOD, r1="100", r2="1")).get_data(as_text=True)
    assert "How this was calculated" in html
    assert "IB = 0" in html
    assert "Approximate" not in html


def test_schematic_follows_the_computed_point(client):
    html = client.post("/calculate", data=dict(GOOD, rc="2")).get_data(as_text=True)
    assert "VC 9.4273 V" in html
    assert "VCE 8.1281 V" in html


def test_schematic_reports_the_saturation_qpoint(client):
    html = client.post("/calculate", data=dict(GOOD, rc="10")).get_data(as_text=True)
    assert "VCE 0.2000 V" in html
    assert "IC 1.0718 mA" in html


def test_schematic_reports_the_cutoff_qpoint(client):
    html = client.post("/calculate", data=dict(GOOD, r1="100", r2="1")).get_data(as_text=True)
    assert "IC 0.000 µA" in html
    assert "VCE 12.0000 V" in html


def test_index_renders_the_dashboard_with_defaults(client):
    html = client.get("/").get_data(as_text=True)
    assert "Lab 02: BJT DC Bias Web App" in html
    assert "Input Parameters" in html
    assert "Circuit: Common-Emitter Amplifier" in html
    assert "DC Bias Results" in html
    assert "Week 2 Goal" in html
    assert 'class="schematic"' in html
    assert "1.2863 mA" in html
    assert "4.6550 V" in html


def test_invalid_input_hides_the_results(client):
    rv = client.post("/calculate", data=dict(GOOD, re="0", rc="9.1"))
    assert rv.status_code == 400
    html = rv.get_data(as_text=True)
    assert "RE must be greater than 0" in html
    assert 'value="9.1"' in html
    assert "Fix the input errors" in html
    assert "1.2863 mA" not in html
