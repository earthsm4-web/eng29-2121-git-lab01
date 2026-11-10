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
