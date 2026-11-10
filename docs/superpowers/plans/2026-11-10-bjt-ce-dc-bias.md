# BJT Common-Emitter DC Bias Calculator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Flask web app that computes a CE voltage-divider bias Q-point, reports its region, and shows the same point from an independent approximate method.

**Architecture:** Pure-function engineering package `bjt/` (params, validate, bias, format) that never imports Flask, wrapped by a thin `app.py` with two routes and three Jinja templates. Tests cover the algebra with hand-computed literals and the routes with Flask's test client.

**Tech Stack:** Python 3.12, Flask, Jinja2, pytest, one plain CSS file. No JavaScript.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-dc-bias-design.md`

## Global Constraints

- Python 3.12 at `C:\Program Files\Python312\python.exe`; virtualenv at `.venv` in the project root; every command below runs from the project root `C:\Users\B6749156\Documents\Default Project`.
- Runtime dependencies: `Flask` only. Dev: `pytest`. Nothing else.
- git is installed at `C:\Users\B6749156\AppData\Local\Programs\Git\cmd\git.exe` but is **not on PATH**. Each shell that uses git starts with:
  `$env:PATH = "C:\Users\B6749156\AppData\Local\Programs\Git\cmd;$env:PATH"`
- All form resistances are entered in **kΩ** and stored internally in **Ω** (multiply by 1000). Voltages in V. Display: V with 4 decimals, mA with 4 decimals, currents below 1 mA in µA with 3 decimals.
- `VCE_SAT = 0.2` and `STIFFNESS_FACTOR = 10.0` are module constants in `bjt/bias.py`. Stiffness test is `beta * re >= STIFFNESS_FACTOR * r2`. Both are never form inputs.
- Validation messages are ASCII words, not symbols: `"<FIELD> is required"`, `"<FIELD> must be a number"`, `"<FIELD> must be greater than 0"`, `"beta must be greater than 1"`, `"VBE must be less than VCC"`. Field names appear uppercase in messages (`VCC`, `R1`, `R2`, `RC`, `RE`, `BETA`, `VBE`).
- Invalid input returns HTTP **400** with the form re-rendered. Valid input returns HTTP **200**.
- UI text is English. No client-side JavaScript. Region labels render exactly `Active`, `Saturation`, `Cutoff`.
- Every test asserts against hand-computed numeric literals or exact strings. A test must never re-derive the formula it is checking.

## Review Focus

Five input classes the spec implies but no task's happy path exercises. Each gets its test in the task that owns the code:

1. **β = 10000** — the divider is nearly ideal, so the exact calculation must converge on the approximate one, stay finite, and stay Active. → Task 2.
2. **R1 = 1 Ω** (0.001 kΩ) — `RB` collapses toward zero, base current explodes; must classify Saturation with no `ZeroDivisionError`. → Task 2.
3. **RC tuned so VCE straddles 0.2 V** — the boundary must not flip between solves because of float noise. → Task 2.
4. **Non-plain numeric input** (`"1e3"`, `" 4.7 "`, `"4,7"`, `"abc"`, blank) — accepted or rejected predictably, never a 500. → Task 1.
5. **VBE ≥ VCC** (VBE = 20, VCC = 12) — rejected by validation before any solving, so no negative `IE` reaches the result page. → Task 1.

---

### Task 1: Repository bootstrap and validated input parsing

**Files:**
- Create: `.gitignore`, `requirements.txt`, `bjt/__init__.py`, `bjt/params.py`, `bjt/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `BiasParams(vcc, r1, r2, rc, re, beta, vbe)` frozen dataclass holding **SI** values (Ω, V) with properties `vbb: float`, `rbb: float`, `is_stiff: bool`; `parse_form(form: Mapping[str, str]) -> tuple[BiasParams | None, dict[str, str]]` where the dict maps form field name to message.

- [ ] **Step 1: Bootstrap the repository**

```powershell
$env:PATH = "C:\Users\B6749156\AppData\Local\Programs\Git\cmd;$env:PATH"
git init
git config user.name "<your name>"
git config user.email "<your email>"
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install flask pytest
```

Write `.gitignore`:

```
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.superpowers/
```

Write `requirements.txt` with exactly:

```
Flask
```

Expected: `git status --short` prints `?? .gitignore`, `?? requirements.txt`, and no `.venv/` entry.

- [ ] **Step 2: Write the failing tests**

Create `tests/test_validate.py`:

```python
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
```

Note `r1="47E3"` means 47 000 kΩ → 47 000 000 Ω; the form's kΩ unit applies to the parsed number.

- [ ] **Step 3: Run the tests to watch them fail**

```powershell
.\.venv\Scripts\python -m pytest tests/test_validate.py -v
```

Expected: collection error, `ModuleNotFoundError: No module named 'bjt'`.

- [ ] **Step 4: Implement `bjt/params.py` and `bjt/validate.py`**

Create `bjt/__init__.py` empty.

Create `bjt/params.py` with a frozen dataclass `BiasParams` whose fields are `vcc, r1, r2, rc, re, beta, vbe` (float) and three properties:

- `vbb = vcc * r2 / (r1 + r2)` — Thevenin divider voltage.
- `rbb = r1 * r2 / (r1 + r2)` — Thevenin resistance of the divider.
- `is_stiff = beta * re >= STIFFNESS_FACTOR * r2` — import `STIFFNESS_FACTOR` from `bjt.bias`.

Create `bjt/validate.py` with `parse_form(form)`:

```python
FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
OHM_FIELDS = ("r1", "r2", "rc", "re")
```

Parse each field with `float(raw.strip())`, catching `ValueError`; blank or missing → required message; unparseable → number message; multiply the four `OHM_FIELDS` by `1000.0`; then apply the range rules in this order — `vcc > 0`, each resistance `> 0`, `0 < vbe < vcc`, `beta > 1`. Collect **all** errors, and return `(None, errors)` if any exist, otherwise `(BiasParams(...), {})`. Message text is built from an uppercase display name map (`{"vcc": "VCC", "beta": "beta", ...}`), with the beta message hard-coded as `"beta must be greater than 1"`.

- [ ] **Step 5: Run the tests to watch them pass**

```powershell
.\.venv\Scripts\python -m pytest tests/test_validate.py -v
```

Expected: 20 passed (7 parametrized range cases + 3 parametrized numeric cases count individually).

- [ ] **Step 6: Commit**

```powershell
git add .gitignore requirements.txt bjt tests
git commit -m "feat: parse and validate BJT bias inputs into SI units"
```

---

### Task 2: Exact solver, saturation solve, and region classification

**Files:**
- Create: `bjt/bias.py`
- Test: `tests/test_bias.py`

**Interfaces:**
- Consumes: `BiasParams` and its `vbb` / `rbb` / `is_stiff` properties from Task 1.
- Produces:
  - `VCE_SAT: float = 0.2`, `STIFFNESS_FACTOR: float = 10.0`
  - `class Region(str, Enum)` with members `ACTIVE = "active"`, `SATURATION = "saturation"`, `CUTOFF = "cutoff"` and `.label` property returning `"Active" | "Saturation" | "Cutoff"`
  - `@dataclass(frozen=True) class BiasResult` with fields `region: Region, ib: float, ic: float, ie: float, vbe: float, vce: float, vb: float, vc: float, ve: float` (SI: A and V) and property `active_valid: bool` (`region is not Region.SATURATION`)
  - `solve_exact(p: BiasParams) -> BiasResult` — active-mode algebra, `region=Region.ACTIVE`
  - `solve_saturation(p: BiasParams) -> BiasResult` — `region=Region.SATURATION`
  - `solve(p: BiasParams) -> BiasResult` — dispatcher returning the correct region

- [ ] **Step 1: Write the failing tests**

Create `tests/test_bias.py`:

```python
import pytest

from bjt.bias import VCE_SAT, Region, solve, solve_saturation
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
```

Add `solve_exact` to the import line.

- [ ] **Step 2: Run the tests to watch them fail**

```powershell
.\.venv\Scripts\python -m pytest tests/test_bias.py -v
```

Expected: collection error, `ImportError: cannot import name 'VCE_SAT' from 'bjt.bias'`.

- [ ] **Step 3: Implement `bjt/bias.py`**

Use the equations from the spec's *The engineering* section verbatim.

- `solve_exact`: compute `ib = (p.vbb - p.vbe) / (p.rbb + (p.beta + 1) * p.re)`, then `ic = p.beta * ib`, `ie = (p.beta + 1) * ib`, `ve = ie * p.re`, `vb = ve + p.vbe`, `vc = p.vcc - ic * p.rc`, `vce = p.vcc - ic * p.rc - ie * p.re`.
- `solve_saturation`: assume `vce = VCE_SAT` and solve collector current from KVL, `ic = (p.vcc - VCE_SAT) / (p.rc + p.re * (p.beta + 1) / p.beta)`, then `ib = ic / p.beta`, `ie = ic * (p.beta + 1) / p.beta`, `ve = ie * p.re`, `vb = ve + p.vbe`, `vc = p.vcc - ic * p.rc`.
- `solve` dispatch order: if `p.vbb <= p.vbe` return the cutoff result (`ib = ic = ie = 0`, `ve = 0`, `vb = p.vbb`, `vc = p.vcc`, `vce = p.vcc`, `vbe = p.vbe`); else compute `solve_exact`; if its `vce < VCE_SAT` return `solve_saturation(p)`; else return the exact result.
  The one exception to "no region logic in `solve_exact`": `solve_exact` always sets `region=Region.ACTIVE`, so `solve` must call it first and only then decide.

- [ ] **Step 4: Run the tests to watch them pass**

```powershell
.\.venv\Scripts\python -m pytest tests/test_bias.py -v
```

Expected: 9 passed.

- [ ] **Step 5: Commit**

```powershell
git add bjt/bias.py tests/test_bias.py
git commit -m "feat: exact Q-point solver with cutoff and saturation detection"
```

---

### Task 3: Approximate solver and comparison

**Files:**
- Modify: `bjt/bias.py` (add `solve_approximate`, `Comparison`, `compare`)
- Test: `tests/test_bias.py` (append)

**Interfaces:**
- Consumes: everything from Task 2.
- Produces:
  - `solve_approximate(p: BiasParams) -> BiasResult` — `region=Region.ACTIVE`
  - `@dataclass(frozen=True) class Comparison` with `approx: BiasResult` and `diffs: dict[str, float]` keyed exactly `"ic"`, `"ie"`, `"vce"`, `"vb"`, holding signed percent differences relative to the exact value, and `stiff: bool`
  - `compare(p: BiasParams) -> Comparison`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_bias.py`:

```python
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
```

Add `compare`, `solve_approximate` to the import line.

- [ ] **Step 2: Run the tests to watch them fail**

```powershell
.\.venv\Scripts\python -m pytest tests/test_bias.py -v
```

Expected: `ImportError: cannot import name 'compare' from 'bjt.bias'`.

- [ ] **Step 3: Implement `solve_approximate` and `compare`**

- `solve_approximate`: `ie = (p.vbb - p.vbe) / p.re`, `ic = ie`, `ib = ic / p.beta`, `ve = ie * p.re`, `vb = p.vbb`, `vc = p.vcc - ic * p.rc`, `vce = p.vcc - ie * (p.rc + p.re)`.
- `compare`: compute `exact = solve_exact(p)` and `approx = solve_approximate(p)`, then for each key in `("ic", "ie", "vce", "vb")` store `(approx_value - exact_value) / exact_value * 100.0`, and `stiff = p.is_stiff`.

- [ ] **Step 4: Run the full suite to watch it pass**

```powershell
.\.venv\Scripts\python -m pytest -v
```

Expected: 33 passed (20 + 13), `bjt/params.py` importing `STIFFNESS_FACTOR` from `bjt/bias.py` still resolves.

- [ ] **Step 5: Commit**

```powershell
git add bjt/bias.py tests/test_bias.py
git commit -m "feat: approximate stiff-divider solver and exact/approximate comparison"
```

---

### Task 4: Formatting helpers, Flask routes, and templates

**Files:**
- Create: `bjt/format.py`, `app.py`, `templates/base.html`, `templates/index.html`, `templates/result.html`
- Test: `tests/test_routes.py`

**Interfaces:**
- Consumes: `parse_form`, `solve`, `compare`, `Region`, `BiasResult`, `Comparison`.
- Produces: `fmt_v(x: float) -> str`, `fmt_i(x: float) -> str`; `create_app() -> Flask`; module-level `app`; Jinja filters named `v` and `i`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_routes.py`:

```python
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
    assert "9.2456" in html
    assert "-14.2859" in html


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
```

- [ ] **Step 2: Run the tests to watch them fail**

```powershell
.\.venv\Scripts\python -m pytest tests/test_routes.py -v
```

Expected: `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Implement `bjt/format.py`, `app.py`, and the three templates**

`bjt/format.py`:

```python
def fmt_v(x: float) -> str:
    return f"{x:.4f} V"


def fmt_i(x: float) -> str:
    return f"{x * 1e6:.3f} µA" if abs(x) < 1e-3 else f"{x * 1e3:.4f} mA"
```

`app.py` — `create_app()` builds the Flask app, registers `add_template_filter(fmt_v, "v")` and `add_template_filter(fmt_i, "i")`, then defines:

```python
DEFAULTS = {"vcc": "12", "r1": "47", "r2": "10", "rc": "4.7",
            "re": "1", "beta": "100", "vbe": "0.7"}
```

- `GET /` → `render_template("index.html", values=DEFAULTS, errors={})`
- `POST /calculate` → `parse_form(request.form)`; if `params is None`, `render_template("index.html", values=request.form, errors=errors), 400`; else `result = solve(params)`, `comparison = compare(params) if result.region is Region.ACTIVE else None`, `render_template("result.html", values=request.form, result=result, comparison=comparison)`
- module level `app = create_app()` and `if __name__ == "__main__": app.run(port=5000)`

Templates:
- `base.html` — `<!doctype html>`, `<meta charset="utf-8">`, links `url_for('static', filename='style.css')`, `<title>CE Bias Calculator</title>`, `{% block content %}{% endblock %}`.
- `index.html` — extends base; one `<form method="post" action="{{ url_for('calculate') }}">` with a labelled number input per field (`step="any"`, `name` = field key, `value="{{ values.get(field, '') }}"`), a `kΩ` suffix on the four resistances, per-field error text from `errors[field]` rendered in `<p class="error">`, and a submit button.
- `result.html` — extends base; region banner showing `result.region.label`; a definition list of `IB, IC, IE, VBE, VCE, VB, VC, VE` using the `i` filter for currents and `v` for voltages; when `result.region.value == "saturation"` a warning paragraph containing the words `active equations do not apply`; when `comparison` is not `None`, a table with a header cell containing `Approximate` and one row per key in `comparison.diffs` showing the approximate value and `{{ "%.4f"|format(comparison.diffs[key]) }}` percent, plus a stiffness verdict line.

- [ ] **Step 4: Run the full suite to watch it pass**

```powershell
.\.venv\Scripts\python -m pytest -v
```

Expected: 39 passed.

- [ ] **Step 5: Commit**

```powershell
git add app.py bjt/format.py templates tests/test_routes.py
git commit -m "feat: Flask routes and templates rendering the Q-point"
```

---

### Task 5: Stylesheet, README, localhost demonstration, and GitHub push

**Files:**
- Create: `static/style.css`, `README.md`
- Modify: nothing

**Interfaces:**
- Consumes: the running app from Task 4.
- Produces: a served page at `http://127.0.0.1:5000/`.

- [ ] **Step 1: Write `static/style.css`**

Single stylesheet, no framework: readable 16px system font stack, a centred `max-width: 60rem` column, a two-column responsive form grid, `.error` in `#b00020`, a `.badge` class with distinct background per region (`.badge-active`, `.badge-saturation`, `.badge-cutoff`), a bordered comparison table with right-aligned numeric cells, and `font-variant-numeric: tabular-nums` on numbers.

Expected: restyling changes nothing the tests assert — the suite still reports 39 passed.

- [ ] **Step 2: Write `README.md`**

Contents, in this order: what the app computes, the seven inputs with units (V and kΩ), the two methods and the stiffness rule, how to run (`py -3.12 -m venv .venv`, `.\.venv\Scripts\python -m pip install -r requirements.txt`, `.\.venv\Scripts\python app.py`, open `http://127.0.0.1:5000`), how to test (`.\.venv\Scripts\python -m pytest`), the golden example with its numbers, and a one-line note that `VCE_SAT = 0.2 V` is a fixed constant.

- [ ] **Step 3: Demonstrate it running on localhost**

```powershell
.\.venv\Scripts\python app.py
```

In a second shell:

```powershell
(Invoke-WebRequest http://127.0.0.1:5000/).StatusCode
(Invoke-WebRequest http://127.0.0.1:5000/calculate -Method POST -Body @{vcc="12";r1="47";r2="10";rc="4.7";re="1";beta="100";vbe="0.7"}).Content | Select-String -Pattern "Active|1.2863 mA|4.6550 V"
```

Expected: `200`, then matches for `Active`, `1.2863 mA`, `4.6550 V`. Leave the server running and report the URL to your human partner.

- [ ] **Step 4: Commit and push**

```powershell
git add static/style.css README.md
git commit -m "feat: stylesheet, README, and localhost demo notes"
git remote add origin <repo-url>   # supplied by your human partner
git push -u origin HEAD
```

Expected: `git log --oneline` shows five commits; `git push` reports the branch tracking the new remote.

If no remote URL or commit identity is available, stop before the push and ask — this is the one step that needs your human partner's input.

---

## Task 6: Circuit schematic and calculation walk-through

**Files:**
- Create: `bjt/steps.py`, `templates/_schematic.html`, `templates/_steps.html`, `tests/test_steps.py`
- Modify: `bjt/format.py`, `app.py`, `templates/result.html`, `static/style.css`, `tests/test_routes.py`

**Interfaces:**
- Consumes: `BiasParams`, `BiasResult`, `Region`, `fmt_v`, `fmt_i`.
- Produces: `@dataclass(frozen=True) class Step` with `quantity: str, formula: str, substitution: str, result: str`; `steps_for(p: BiasParams, result: BiasResult) -> list[Step]`; `fmt_r(x: float) -> str`; `fmt_num(x: float) -> str`; Jinja filters `r` and `num`.

Golden strings for `LAB = BiasParams(vcc=12, r1=47k, r2=10k, rc=4.7k, re=1k, beta=100, vbe=0.7)`:

| # | quantity | result |
|---|---|---|
| 1 | VBB | `2.1053 V` |
| 2 | RB | `8.2456 kΩ` |
| 3 | IB | `12.863 µA` |
| 4 | IC | `1.2863 mA` |
| 5 | IE | `1.2992 mA` |
| 6 | VE | `1.2992 V` |
| 7 | VB | `1.9992 V` |
| 8 | VC | `5.9542 V` |
| 9 | VCE | `4.6550 V` |

- [ ] **Step 1: Write the failing tests**

`tests/test_steps.py` must assert: nine Active steps in that order with those
`result` strings; `substitution` for step 1 equals `12 · 10 / (47 + 10)` and
for step 3 equals `(2.1053 − 0.7) / (8.2456 + 101 · 1)`; four Saturation steps
for `rc=10k` starting with `1.0718 mA`; two Cutoff steps for `r1=100k, r2=1k`
ending with `0.000 µA`; `fmt_r(47_000) == "47 kΩ"`, `fmt_r(4_700) == "4.7 kΩ"`,
`fmt_r(8245.614035) == "8.2456 kΩ"`; `fmt_num(12.0) == "12"`.

Append to `tests/test_routes.py`: the Active page contains `class="schematic"`,
`R1 47 kΩ`, `RB = R1 ∥ R2`, and `4.6550 V`; the Cutoff page contains the
walk-through heading and `IB = 0`, and still no `Approximate`.

- [ ] **Step 2: Run to watch them fail** — `.\.venv\Scripts\python -m pytest -q` → `ModuleNotFoundError: bjt.steps`.

- [ ] **Step 3: Implement** `fmt_r`/`fmt_num` in `bjt/format.py`; `bjt/steps.py` building each row from `BiasParams` and the already-computed `BiasResult` (never re-solving); `steps_for` dispatching on `result.region`; register the `r` and `num` filters in `app.py` and pass `params` and `steps` to the result template; add the two SVG/table partials and include them in `result.html`; add styles.

- [ ] **Step 4: Run the full suite** — expected 39 existing + new tests, all passing.

- [ ] **Step 5: Commit** — `git add ... && git commit -m "feat: circuit schematic and calculation walk-through on the result page"`.

### Task 7: Single-page dashboard UI

**Files:**
- Modify: `app.py`, `templates/base.html`, `templates/index.html`, `templates/_schematic.html`, `templates/_steps.html`, `static/style.css`, `tests/test_routes.py`, `README.md`
- Create: `templates/_comparison.html`
- Delete: `templates/result.html`

**Interfaces:**
- Consumes: `parse_form`, `DEFAULTS`, `FIELDS`, `QUANTITIES`, `COMPARE_KEYS`, `solve`, `compare`, `steps_for`, `Region`, and the `v`/`i`/`r`/`num` filters.
- Produces: `_dashboard(values, errors=None, params=None) -> str` in `app.py`; the template context gains `fields` as four-tuples `(name, label, unit, description)` and keeps `result`, `params`, `steps`, `comparison`, `quantities`, `compare_keys`. No new public API.

- [ ] **Step 1: Write the failing route tests**

Append to `tests/test_routes.py`:

```python
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
```

- [ ] **Step 2: Run to watch them fail**

Run: `.\.venv\Scripts\python -m pytest tests/test_routes.py -q`
Expected: the first test fails on the missing dashboard text (`GET /` renders only the form); the second fails on `Fix the input errors`. The other 11 route tests still pass.

- [ ] **Step 3: Implement the shared dashboard renderer in `app.py`**

Add `_dashboard(values, errors=None, params=None)` that solves only when `params` is given, builds `steps` and `comparison` exactly as the old `calculate` route did, and renders `index.html` with `values`, `errors or {}`, `fields`, `result`, `params`, `steps`, `comparison`, `quantities`, `compare_keys`. `GET /` calls `parse_form(DEFAULTS)` and passes the parsed params, so the first load is fully populated. `POST /calculate` returns `_dashboard(request.form, errors)`, 400 when parsing fails, else `_dashboard(request.form, params=parsed)`. Extend each `FIELDS` entry with its description: `Supply Voltage`, `Upper Divider`, `Lower Divider`, `Collector Resistor`, `Emitter Resistor`, `Current Gain`, `Base-Emitter Voltage`.

- [ ] **Step 4: Write `base.html`**

Header with an inline-SVG chip icon, `h1` exactly `Lab 02: BJT DC Bias Web App`, subtitle `ENG29 2121 – Common Emitter (Voltage Divider Bias)`, and the right-hand badge `Computer Programming for Electrical Engineers` with a code icon. `<title>` matches the `h1`. Keep `{% block content %}` inside `<main class="page">`.

- [ ] **Step 5: Write `index.html`**

Three-card grid. Input card heading `Input Parameters` with a gear icon; each row is the label (`V<sub>CC</sub>`; `β` for beta) plus its description, the input, a unit chip (`V`, `kΩ`, `–`), and an `aria-hidden` chevron; submit button text `Calculate DC Bias` with a calculator icon. Circuit card heading `Circuit: Common-Emitter Amplifier` with a nodes icon, containing `{% include "_schematic.html" %}`. Results card heading `DC Bias Results` with a bars icon, a zebra table of `quantities` rendering `{{ label[0] }}<sub>{{ label[1:] }}</sub>`, and the region callout: `Active region — equations apply` (green check), `Saturation — active equations do not apply` (amber, keeps the words `do not apply`), `Cutoff — transistor off` (slate). When `result` is `None`, both cards render `Fix the input errors to see the circuit.` / `...the results.` instead of numbers. Below the grid: the `Week 2 Goal` banner (target icon, pill, the screenshot's sentence), then `{% include "_steps.html" %}`, then `{% if comparison %}{% include "_comparison.html" %}{% endif %}`.

- [ ] **Step 6: Write the partials and delete `result.html`**

`_steps.html`: wrap the existing 9/4/2-row table in a card with heading `How this was calculated`; keep every row string unchanged. `_comparison.html`: the table and verdict text moved out of `result.html`, keeping the heading `Approximate method check` and the word `Approximate`. `_schematic.html`: add `Q1 NPN (β = {{ params.beta|num }})` beside the transistor; keep node voltages and the Q-point box. Delete `templates/result.html`.

- [ ] **Step 7: Rewrite `static/style.css`**

Tokens: page `#eef2f6`, card `#fff`, ink `#16202a`, muted `#5d6b78`, line `#dbe4ec`, teal `#0f766e`, teal-dark `#0b5d57`, green `#1d6f42`, amber `#a35a00`. Segoe UI stack, `font-variant-numeric: tabular-nums` on values. Grid `1.05fr 1.35fr 1fr`, gap `1rem`, max-width `78rem`; two columns at 1100 px, one at 860 px. Cards: `border: 1px solid var(--line)`, `border-radius: 10px`, subtle shadow, `padding: 1rem 1.1rem`. Zebra rows `tbody tr:nth-child(even) { background: #f4f7fa; }`. Callout colours keyed to `region.value`. Keep a visible `:focus-visible` ring on inputs and the button. Text labels accompany every colour.

- [ ] **Step 8: Run the full suite**

Run: `.\.venv\Scripts\python -m pytest -q`
Expected: 54 passed (52 existing + 2 new).

- [ ] **Step 9: Verify the live page**

Restart the demo and check `GET /` (header, three headings, `1.2863 mA`, `4.6550 V`), a Saturation POST (`do not apply`), a Cutoff POST (no `Approximate`), and an invalid POST (400, `Fix the input errors`).

- [ ] **Step 10: Update `README.md` and commit**

Replace the layout block: `templates/index.html` is the dashboard, `templates/result.html` no longer exists, add `_steps.html`/`_comparison.html`. Then:

```bash
git add app.py templates static tests/test_routes.py README.md
git commit -m "feat: single-page dashboard UI matching the lab handout"
```

## Self-Review

**1. Spec coverage.** Form and defaults → Task 4. Exact equations → Task 2. Approximate equations and comparison → Task 3. Stiffness rule → Task 1 (`is_stiff`) and Task 3 (surfaced). Region logic and `VCE_SAT` → Task 2. Validation → Task 1. Units/formatting → Task 4. Separate logic/templates/CSS/tests → Tasks 1–5. Localhost demo → Task 5. GitHub commit → Tasks 1–5 commit each task, push in Task 5. Calculation illustrations → Task 6. Single-page dashboard, first-load results, and the 400 placeholder → Task 7.

**2. Step scan.** Each step names one action with checkable output. No `TBD`, no "handle edge cases".

**3. Type consistency.** `BiasParams` fields and the `vbb`/`rbb`/`is_stiff` properties are used identically in Tasks 1–3. `BiasResult.region` is a `Region` everywhere; `Comparison.diffs` keys `ic, ie, vce, vb` match Task 3's test and Task 4's template loop. `parse_form` returns a 2-tuple everywhere. Task 7's four-tuple `FIELDS` entries are produced and consumed only in `app.py` and `index.html` within that task.

**4. Review Focus.** Every line has a test in the named task: high β and tiny R1 and the VCE boundary in Task 2; numeric-format variants in Task 1; `VBE ≥ VCC` in Task 1.

**5. Proportion.** Five tasks, ~370 lines of implementation for ~330 lines of tests. The plan carries equations, signatures, and assertions; no function bodies beyond the two formatting helpers and the stiffness formula.
