# CE Amplifier Lab Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a separate `/ce-lab` Flask page that runs real ngspice `.op`, `.ac`, and `.tran` analyses for a CE voltage-divider amplifier and presents engineering results in a responsive 3-column dashboard.

**Architecture:** Keep the existing app, `/`, `/spice`, and `bjt/spice_engine.py` intact. Add a new route/template pair, a pure metrics module for derived display values, and scoped UI assets. The route validates input, dispatches one analysis per POST, and renders only real ngspice output; templates never invent or calculate engineering values.

**Tech Stack:** Python 3.13.2 (`.venv`), Flask 3.1.3, pytest 9.2.0, matplotlib 3.11.2, ngspice 47, Jinja templates, plain CSS/JS.

**Spec:** `docs/superpowers/specs/2026-11-25-ce-amplifier-lab-page-design.md`

## Global Constraints

- All displayed SPICE numbers must come from real ngspice stdout parsed by `bjt/spice_engine.py`; no mock data, decorative plots, random values, or hard-coded gain/cutoff/bandwidth.
- `bjt/bias.py`, `bjt/params.py`, `bjt/validate.py`, `bjt/steps.py`, and all files under `tests/` are read-only; new tests go in `tests_spice/test_ce_lab.py`.
- Do not delete or change behavior of `/`, `/spice`, `templates/index.html`, or `templates/spice.html`; adding one nav link to `templates/base.html` is allowed.
- BJT model remains the existing simplified line `.model QNPN NPN(IS=1e-14 BF=100.0)`; UI/docs must label it simplified, not instructor-verified.
- No analytical `dc_bias.py` values appear on `/ce-lab`; analytical comparison remains only on `/spice`.
- `subprocess.run` stays list-form, `shell=False`, isolated temp `cwd`, and `timeout=60` inside the existing adapter.
- Input errors return HTTP 400, list field errors, and never create a netlist or call ngspice.
- Engine errors clear all result/plot state and show the real error/log; no success badge may remain.
- Baseline pytest result is `49 passed, 5 failed` (pre-existing in `tests/test_routes.py`); no new failures allowed.
- Follow layout A from the approved mockup: strict 3 columns on desktop, 2 columns/tablet with results full width, 1 column/mobile.

## Review Focus

- **Invalid amplitude `0 V`, negative resistance, or frequency `1e7 Hz`** → field error and no run; pinned in Task 2 validation tests.
- **ngspice missing/failing/empty stdout** → error panel with real log and no plot/success markup; pinned in Task 3 error tests.
- **AC sweep with no −3 dB crossing** → cutoff/bandwidth blank with an explicit note, never invented; pinned in Task 1 metric tests.
- **Tab/analysis mismatch** → hidden `analysis` field must drive exactly one of `run_op`/`run_ac`/`run_tran`; pinned in Task 3 dispatch tests.
- **Desktop/tablet/mobile clipping or dead tabs** → responsive layout and keyboard-accessible tabs checked in Task 6 browser acceptance.

---

### Task 0: Commit approved product/design documents

**Files:**
- Add: `PRODUCT.md`
- Add: `docs/superpowers/specs/2026-11-25-ce-amplifier-lab-page-design.md`
- Add: `docs/superpowers/plans/2026-11-25-ce-amplifier-lab-page.md`
- Add: `.impeccable/surfaces/ce-lab.md`

**Interfaces:**
- Consumes: approved design doc, application product truth, and layout A pinned by the user.
- Produces: clean committed documentation and surface-contract baseline before source edits.

- [ ] **Step 1: Verify docs are present and contain no build code**

Run: `git status -sb`
Expected: the docs are the only CE-Lab-related untracked/modified files.

- [ ] **Step 2: Write the surface brief**

Create `.impeccable/surfaces/ce-lab.md` with six blocks: `THESIS`, `OWN-WORLD`, `STORY`, `FIRST VIEWPORT`, `FORM`, `FINISH`. Use the approved design and layout A. In `FORM` write `seed: none (pinned)` and quote “strict 3-column dashboard, layout A”. In `FINISH` use the verbatim line: “unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance”. Do not copy the contract into HTML, CSS, JS, or any browser-delivered file.

- [ ] **Step 3: Commit the documentation**

```bash
git add PRODUCT.md docs/superpowers/specs/2026-11-25-ce-amplifier-lab-page-design.md docs/superpowers/plans/2026-11-25-ce-amplifier-lab-page.md .impeccable/surfaces/ce-lab.md
git commit -m "docs(lab4): approve CE amplifier lab page design"
```

- [ ] **Step 4: Confirm clean baseline**

Run: `git status -sb`
Expected: no 2026-11-25 CE-Lab documentation files remain uncommitted; the older 2026-11-24 docs may remain untracked from prior work and are outside this plan.

---

### Task 1: Pure AC/transient metrics with fixed definitions (TDD)

**Files:**
- Create: `bjt/spice_metrics.py`
- Test: `tests_spice/test_ce_lab.py`

**Interfaces:**
- Consumes: `SpiceAcResult`, `SpiceTranResult` from `bjt.spice_engine`.
- Produces:
  - `AcSummary` dataclass with `gain_db_at_frequency: float`, `gain_frequency_hz: float`, `midband_gain_db: float`, `phase_deg_at_frequency: float`, `low_cutoff_hz: float | None`, `high_cutoff_hz: float | None`, `bandwidth_hz: float | None`, `cutoff_note: str`.
  - `TranSummary` dataclass with `time_s: float`, `vin_peak_to_peak_v: float`, `vout_peak_to_peak_v: float`, `analysis_window_start_s: float`, `sample_count: int`.
  - `ac_summary(result: SpiceAcResult, target_freq_hz: float) -> AcSummary`
  - `tran_summary(result: SpiceTranResult, source_freq_hz: float) -> TranSummary`

- [ ] **Step 1: Write failing tests for `ac_summary`**

Use synthetic arrays only as unit-test fixtures for this pure function (never rendered as ngspice results). Assert:

```python
def test_ac_summary_finds_gain_phase_and_3db_bandwidth():
    result = SpiceAcResult(
        frequency=[1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0],
        gain_db=[-40.0, -10.0, 20.0, 20.0, -10.0, -40.0],
        phase_deg=[170.0, 175.0, 180.0, 180.0, 175.0, 170.0],
        netlist="", run_log="",
    )
    summary = ac_summary(result, 1000.0)
    assert summary.gain_db_at_frequency == 20.0
    assert summary.gain_frequency_hz == 1000.0
    assert summary.phase_deg_at_frequency == 180.0
    assert summary.midband_gain_db == 20.0
    assert summary.low_cutoff_hz is not None and 10.0 < summary.low_cutoff_hz < 100.0
    assert summary.high_cutoff_hz is not None and 1000.0 < summary.high_cutoff_hz < 10000.0
    assert summary.bandwidth_hz is not None and summary.bandwidth_hz > 0.0
```

Also assert `ac_summary(result_without_crossing, 1000.0).bandwidth_hz is None` and its `cutoff_note` contains `not found`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k ac_summary -v`
Expected: FAIL with import/collection error for `bjt.spice_metrics`.

- [ ] **Step 3: Implement `bjt/spice_metrics.py`**

Define both dataclasses and both functions with the signatures in Interfaces. Use the spec's fixed definitions: closest real frequency for gain/phase; `max(gain_db)` for midband; upward/downward crossings of `midband - 3` around the peak index with linear interpolation; `None` plus `cutoff_note` when either crossing is absent. Raise `ValueError` for empty/mismatched arrays.

- [ ] **Step 4: Write failing tests for `tran_summary`**

Assert:

```python
def test_tran_summary_ignores_first_two_cycles():
    result = SpiceTranResult(
        time=[0.0, 0.001, 0.002, 0.003, 0.004],
        vin=[99.0, 1.0, -1.0, 1.0, -1.0],
        vout=[99.0, 2.0, -2.0, 2.0, -2.0],
        netlist="", run_log="",
    )
    summary = tran_summary(result, 1000.0)
    assert summary.analysis_window_start_s == 0.002
    assert summary.sample_count == 3
    assert summary.vin_peak_to_peak_v == 2.0
    assert summary.vout_peak_to_peak_v == 4.0
    assert summary.time_s == 0.004
```

Also assert `tran_summary(result, 0.0)` raises `ValueError`.

- [ ] **Step 5: Run metric tests to verify they pass**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k "ac_summary or tran_summary" -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add bjt/spice_metrics.py tests_spice/test_ce_lab.py
git commit -m "feat(lab4): derive CE lab metrics from real analysis arrays"
```

---

### Task 2: Shared validation and `/ce-lab` GET skeleton (TDD)

**Files:**
- Modify: `app.py` (add module-level `parse_spice_form`; make existing nested helper delegate to it; add routes)
- Create: `templates/ce_lab.html` (minimal skeleton only)
- Modify: `templates/base.html` (add CE Lab nav link, keep existing links)
- Test: `tests_spice/test_ce_lab.py`

**Interfaces:**
- Consumes: `SPICE_DEFAULTS` from `app.py`; `parse_spice_form` returns `(dict[str, float] | None, dict[str, str])` with SI values and kΩ→Ω conversion.
- Produces: `CE_LAB_DEFAULTS = dict(SPICE_DEFAULTS)` in `app.py`; `GET /ce-lab` → 200 render with `analysis="op"`, defaults, no result/error; `parse_spice_form(form)` used by both `/spice/run` and `/ce-lab/run`.

- [ ] **Step 1: Write failing validation tests**

Assert valid form converts `rc="2.2"` to `2200.0`, `source_ampl="0.010"` to `0.01`, and `errors == {}`. Parametrize invalid inputs: `source_ampl="0"`, `source_freq="1e7"`, `rc="-1"`, `vbe="0.01"`, `beta="0"`, `vcc="abc"`. Assert each field name is in `errors` and returned values are `None`.

- [ ] **Step 2: Run validation tests to verify they fail**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k validation -v`
Expected: FAIL with `ImportError: cannot import name 'parse_spice_form'`.

- [ ] **Step 3: Implement module-level `parse_spice_form`**

Move the current numeric parsing body from nested `_parse_spice_form` into module-level `parse_spice_form(form)`, add the bounds from Global Constraints, and keep the nested function as a one-line delegating wrapper so `/spice/run` behavior is unchanged.

- [ ] **Step 4: Write failing route tests**

```python
def test_ce_lab_get_renders_skeleton():
    client = create_app().test_client()
    response = client.get("/ce-lab")
    assert response.status_code == 200
    html = response.data.decode()
    assert "CE Amplifier Lab" in html
    assert 'name="analysis"' in html
    assert "SPICE SIMULATION RESULTS (NGSPICE)" not in html.upper()
```

Also assert the navigation contains links to `/`, `/spice`, and `/ce-lab`.

- [ ] **Step 5: Run route tests to verify they fail**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k "validation or ce_lab_get" -v`
Expected: FAIL with 404 for `/ce-lab` before implementation.

- [ ] **Step 6: Implement `GET /ce-lab` and skeleton template**

Add `CE_LAB_DEFAULTS = dict(SPICE_DEFAULTS)` beside `SPICE_DEFAULTS`. Add `@app.get("/ce-lab")` calling a new `_ce_lab_dashboard(values=CE_LAB_DEFAULTS, analysis="op")` helper. Add minimal `templates/ce_lab.html` extending `base.html` with title, hidden `analysis` input, and a placeholder result area. Add nav link only.

- [ ] **Step 7: Run tests to verify they pass**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k "validation or ce_lab_get" -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add app.py templates/ce_lab.html templates/base.html tests_spice/test_ce_lab.py
git commit -m "feat(lab4): add CE lab route and shared form validation"
```

---

### Task 3: POST dispatch, derived metrics, and no-stale error rendering (TDD)

**Files:**
- Modify: `app.py` (`POST /ce-lab/run`, `_ce_lab_dashboard`)
- Modify: `templates/ce_lab.html` (result/error markup; still basic)
- Test: `tests_spice/test_ce_lab.py`

**Interfaces:**
- Consumes: `parse_spice_form`, `SpiceParams`, `run_op`, `run_ac`, `run_tran`, `ac_summary`, `tran_summary`; plot helpers from `bjt.spice_plot`.
- Produces: `_ce_lab_dashboard(values, errors=None, analysis="op", spice_result=None, spice_error=None, ac_metrics=None, tran_metrics=None)`; `POST /ce-lab/run` returns 400 on validation error and 200 otherwise.

- [ ] **Step 1: Write failing dispatch tests using monkeypatched engine functions**

For each `analysis` in `op`, `ac`, `tran`, patch only the matching `app.run_*` function to return an appropriate real-shaped dataclass, POST the default form, and assert the matching function was called once and the others zero times. Assert HTML contains `SPICE (ngspice)` and not `DC Analytical`.

- [ ] **Step 2: Write failing error/no-stale tests**

Patch `app.run_ac` to raise a `SpiceEngineError` with a synthetic log string. Assert response status 200, HTML contains the log string, and contains neither `SPICE SIMULATION RESULTS (NGSPICE)` nor a `<img` tag whose `src` starts with `data:image/png`. Repeat for validation error: assert 400 and that no `run_*` function was called.

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k "dispatch or error" -v`
Expected: FAIL with 405/404 before POST implementation.

- [ ] **Step 4: Implement `POST /ce-lab/run`**

Validate first; on error return `_ce_lab_dashboard(..., errors=errors), 400`. Build `SpiceParams`, call exactly one engine function, derive `ac_metrics` or `tran_metrics` from the returned arrays, and pass plot data URI from the existing plot helpers. Catch engine exceptions into `spice_error` with `spice_result=None`. Do not call `bjt.bias`.

- [ ] **Step 5: Update template result/error blocks**

Render plot/result tables only when `spice_result` exists; render error text only when `spice_error` exists; always show a `SPICE (ngspice)` provenance badge on successful result blocks and a simplified-model note near the netlist details.

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k "dispatch or error" -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app.py templates/ce_lab.html tests_spice/test_ce_lab.py
git commit -m "feat(lab4): dispatch CE lab analyses and clear stale results on failure"
```

---

### Task 4: Full CE schematic and input/result panels (TDD)

**Files:**
- Create: `templates/_ce_circuit.html`
- Modify: `templates/ce_lab.html`
- Test: `tests_spice/test_ce_lab.py`

**Interfaces:**
- Consumes: form `values`, `spice_result`, `ac_metrics`, `tran_metrics` from Task 3.
- Produces: a template that shows all required circuit components and three result sections with units.

- [ ] **Step 1: Write failing template-content tests**

GET `/ce-lab` and assert HTML contains `Q1`, `NPN`, `R1`, `R2`, `RC`, `RE`, `Cin`, `Cout`, `RL`, `VCC`, `Vin`, and `GND`. Assert labels/units for VCC, RC, R1, R2, RE, RL, input amplitude, and frequency are present. Assert the DC section names `VB`, `VE`, `VC`, `VCE`, `IB`, `IC`, `IE`; the AC section names `Voltage Gain`, `Phase`, `Frequency`, `Cutoff`, `Bandwidth`; and the transient section names `Vin`, `Vout`, `Time`. Assert placeholders `—` exist for all three engineering result sections when no run has happened.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k schematic -v`
Expected: FAIL because the skeleton has no schematic.

- [ ] **Step 3: Create the accessible schematic partial**

Create `templates/_ce_circuit.html` with an inline `<svg role="img" aria-labelledby="ce-circuit-title ce-circuit-desc">`, `<title id="ce-circuit-title">Common-emitter amplifier with voltage-divider bias</title>`, `<desc>` listing the topology, and visible labels for every required component. No numeric voltages or currents may be drawn.

- [ ] **Step 4: Replace skeleton body with full 3-column markup**

Left: schematic include plus the parameter form and Run button. Middle: tab strip and three panels. Right: DC / AC / Transient result sections. Use explicit units: V, mA, µA, kΩ, Hz, dB, °, ms. Format numbers with existing Jinja filters. Show `cutoff_note` when `bandwidth_hz is None`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k schematic -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add templates/_ce_circuit.html templates/ce_lab.html tests_spice/test_ce_lab.py
git commit -m "feat(lab4): add CE schematic and engineering result panels"
```

---

### Task 5: Accessible tabs, scoped styling, and responsive motion (TDD)

**Files:**
- Create: `static/ce_lab.js`
- Modify: `static/style.css`
- Modify: `templates/ce_lab.html` (link JS, ARIA attributes)
- Test: `tests_spice/test_ce_lab.py`

**Interfaces:**
- Consumes: tab markup from Task 4 and hidden `analysis` input from Task 2.
- Produces: keyboard-accessible tabs that update `aria-selected`, panel `hidden`, hidden `analysis`, and a CSS fade-in that respects `prefers-reduced-motion`.

- [ ] **Step 1: Write failing markup/asset tests**

Assert `/ce-lab` HTML contains `role="tablist"`, three elements with `role="tab"`, three with `role="tabpanel"`, `aria-selected="true"` on the DC tab, and a `<script src="/static/ce_lab.js">` reference. Assert `static/style.css` text contains `.ce-lab-grid`, `--ce-navy`, `@media (max-width: 1100px)`, `@media (max-width: 860px)`, `@media (max-width: 560px)`, and `prefers-reduced-motion`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k tabs -v`
Expected: FAIL.

- [ ] **Step 3: Implement `static/ce_lab.js`**

Add no-dependency tab controller: click and ArrowLeft/ArrowRight switch tabs, set `aria-selected` and `hidden`, update hidden `analysis`, and submit nothing by itself. Preserve default DC tab when JS is absent.

- [ ] **Step 4: Add scoped CSS**

Add `.ce-lab-grid` 3-column layout, `.ce-lab-tabs`, `.ce-lab-panel`, result cards, unit chips, `ceFade` animation, and breakpoints 1100/860/560px. Do not change existing `.dashboard` behavior used by other pages.

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k tabs -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add static/ce_lab.js static/style.css templates/ce_lab.html tests_spice/test_ce_lab.py
git commit -m "feat(lab4): add accessible CE lab tabs and responsive styling"
```

---

### Task 6: Real ngspice smoke, browser acceptance, docs, and final verification

**Files:**
- Modify: `README.md`
- Modify: `docs/validation.md`
- No new production code expected

**Interfaces:**
- Consumes: all previous tasks.
- Produces: documented local evidence and a clean final commit.

- [ ] **Step 1: Run real engine smoke tests**

```bash
.venv\Scripts\python -c "from bjt.spice_engine import SpiceParams,run_op,run_ac,run_tran; p=SpiceParams(vcc=12,rc=2200,r1=100000,r2=22000,re=1000,rl=10000,beta=100,vbe=0.7,source_ampl=0.01,source_freq=1000); print(len(run_op(p).run_log), len(run_ac(p).frequency), len(run_tran(p).time))"
```

Expected: three positive numbers; no exception.

- [ ] **Step 2: Run full test suite**

Run: `.venv\Scripts\python -m pytest -q`
Expected: all `tests_spice` tests pass; only the known five pre-existing `tests/test_routes.py` failures remain.

- [ ] **Step 3: Browser acceptance**

Start Flask with `.venv\Scripts\python -m flask --app app run --debug`, open `http://127.0.0.1:5000/ce-lab`, run DC, AC, and Transient tabs with real values. Verify plot appears, netlist details include the simplified model line, engine status is shown, invalid amplitude `0` shows field error, and no console errors. Capture 1280px, 820px, and 390px widths.

- [ ] **Step 4: Update docs with observed evidence only**

`README.md`: Thai/English notes for `/ce-lab`, input units, node definitions `V(2)=Vin before CIN`, `V(6)=Vout after COUT`, `VCE=V(4)-V(5)`, IC direction, simplified-model warning, and how to run. `docs/validation.md`: record only this machine's actual runs and browser observations; no invented gain/cutoff values.

- [ ] **Step 5: Final status and commit/push**

```bash
git status -sb
git add README.md docs/validation.md
git commit -m "docs(lab4): document CE lab page and local verification"
git push origin feat/lab4-ce-spice-ngspice
```

Expected: clean working tree after push except pre-existing ignored/generated artifacts.
