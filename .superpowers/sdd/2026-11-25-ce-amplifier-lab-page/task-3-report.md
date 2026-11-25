# Task 3 Report — POST dispatch, derived metrics, no-stale error rendering

Date: 2026-11-25
Branch: `feat/lab4-ce-spice-ngspice`
Repo: `C:\Users\ASUS\Documents\Default Project\eng29-2121-git-lab01`

## Scope delivered

- Added `POST /ce-lab/run` in `app.py` with validation-first dispatch:
  - validation errors → HTTP 400, no `run_*` call, no success state;
  - exactly one of `run_op` / `run_ac` / `run_tran` on valid input;
  - AC derives `ac_summary(result, values["source_freq"])`;
  - transient derives `tran_summary(result, values["source_freq"])`;
  - plot data URI computed in the route with the existing `bjt.spice_plot`
    helpers and passed to the template as `plot_uri`;
  - engine/metric/plot exceptions caught into `spice_error` with
    `spice_result=None`, `ac_metrics=None`, `tran_metrics=None`,
    `plot_uri=None`.
- Moved `_ce_lab_dashboard` to module level with the requested parameters:
  `_ce_lab_dashboard(values, errors=None, analysis="op", spice_result=None, spice_error=None, ac_metrics=None, tran_metrics=None, *, plot_uri=None)`.
- Reworked `templates/ce_lab.html`:
  - POST form with all ten validated fields and analysis selector;
  - success block only when `spice_result` exists, with `SPICE (ngspice)`
    provenance badge and `SPICE Simulation Results (ngspice)` heading;
  - `<img>` only when `plot_uri` is present;
  - OP / AC / transient result tables from real dataclass/metric values;
  - error block only when `spice_error` exists, showing the real engine text;
  - netlist plus simplified-model note (`.model QNPN NPN(IS=1e-14 BF=<beta>)`,
    simplified and not instructor-verified);
  - no `DC Analytical` and no `dc_bias.py` comparison anywhere on `/ce-lab`.
- Appended only new tests to `tests_spice/test_ce_lab.py` (existing tests untouched).

## RED evidence

Command (exact):

```
.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k "dispatch or error" -v
```

Result before implementation:

```
FAILED tests_spice/test_ce_lab.py::test_ce_lab_run_dispatches_to_matching_engine[op-op]
FAILED tests_spice/test_ce_lab.py::test_ce_lab_run_dispatches_to_matching_engine[ac-ac]
FAILED tests_spice/test_ce_lab.py::test_ce_lab_run_dispatches_to_matching_engine[tran-tran]
FAILED tests_spice/test_ce_lab.py::test_ce_lab_run_engine_error_renders_log_without_stale_success
FAILED tests_spice/test_ce_lab.py::test_ce_lab_run_validation_error_returns_400_and_calls_no_engine
================= 5 failed, 5 passed, 28 deselected in 0.73s ==================
```

All five failures were `assert 404 == ...` because `POST /ce-lab/run` did not
exist yet. The five passing selections were pre-existing `tran_summary` tests
whose names match `error`, as expected.

## GREEN evidence

Command (exact):

```
.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k "dispatch or error" -v
```

Result after implementation:

```
tests_spice/test_ce_lab.py::test_ce_lab_run_dispatches_to_matching_engine[op-op] PASSED
tests_spice/test_ce_lab.py::test_ce_lab_run_dispatches_to_matching_engine[ac-ac] PASSED
tests_spice/test_ce_lab.py::test_ce_lab_run_dispatches_to_matching_engine[tran-tran] PASSED
tests_spice/test_ce_lab.py::test_ce_lab_run_engine_error_renders_log_without_stale_success PASSED
tests_spice/test_ce_lab.py::test_ce_lab_run_validation_error_returns_400_and_calls_no_engine PASSED
====================== 10 passed, 28 deselected in 1.29s ======================
```

Full CE-lab file:

```
.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -q
38 passed in 1.95s
```

## Full suite (run once)

Command (exact):

```
.venv\Scripts\python -m pytest -q
```

Exact final summary line:

```
5 failed, 87 passed in 1.93s
```

The five failures are the same pre-existing `tests/test_routes.py`
assertion failures reported by the controller at baseline:
`test_active_page_shows_schematic_and_walkthrough`,
`test_schematic_follows_the_computed_point`,
`test_schematic_reports_the_saturation_qpoint`,
`test_schematic_reports_the_cutoff_qpoint`,
`test_index_renders_the_dashboard_with_defaults`.
Baseline was `5 failed, 80 passed`; the seven added tests account for
`87 passed`. No new failures and no collection errors.

## Files changed

- `app.py` — metrics imports, module-level `_ce_lab_dashboard`, `POST /ce-lab/run`.
- `templates/ce_lab.html` — POST form, success/error blocks, tables, plot, model note.
- `tests_spice/test_ce_lab.py` — seven appended tests (dispatch parametrized ×3,
  AC metric derivation, transient metric derivation, engine-error no-stale,
  validation no-engine-call).

## Self-review findings

- Dispatch uses module-level `run_op` / `run_ac` / `run_tran` lookups, so
  `monkeypatch.setattr(app_module, "run_ac", ...)` intercepts the call made by
  the route. No direct ngspice invocation was added to `app.py`.
- One `try` wraps engine call, metric derivation, and plot generation. Any
  failure resets every result/metric/plot field, so no stale success markup can
  render on that response.
- Validation happens before `SpiceParams` construction and before any engine
  call; the invalid response returns 400 with field errors only.
- Template success markup is gated by `{% if spice_result %}`; the data URI is
  only emitted by `{% if plot_uri %}`; error markup is gated by
  `{% if spice_error %}`. The badge text is exactly `SPICE (ngspice)`.
- Verified the template contains no `DC Analytical` or `dc_bias.py` text.
- All displayed metric numbers come from `ac_summary` / `tran_summary` applied
  to the returned dataclass arrays; the plot URI is generated from those same
  arrays. Nothing is computed in Jinja.
- Read-only files (`bjt/bias.py`, `bjt/params.py`, `bjt/validate.py`,
  `bjt/steps.py`, `tests/`) were not modified. `/`, `/spice`,
  `templates/index.html`, and `templates/spice.html` were not modified.

## Concerns

1. **`plot_uri` parameter:** the requested dashboard signature is preserved as
   the first seven parameters, but a keyword-only `plot_uri=None` was added so
   the route can pass the route-computed data URI into the template, per the
   instruction to compute the URI in the route. If the controller intended a
   literal seven-parameter signature with no extension, this is the only
   deviation.
2. **Form fields:** the Task 2 skeleton form exposed four fields, but
   `parse_spice_form` requires all ten. The template now exposes all ten with
   defaults so real `/ce-lab` POSTs validate. GET still renders no success
   state.
3. The five full-suite failures are pre-existing and confined to
   `tests/test_routes.py`; they were not touched.
