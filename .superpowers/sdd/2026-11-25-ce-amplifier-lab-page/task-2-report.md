# Task 2: Shared validation and `/ce-lab` GET skeleton (TDD)

## Summary

Implemented Task 2 as specified in the brief. Changes included:

1. **`app.py`**: 
   - Added module-level `parse_spice_form(form)` function with validation bounds (resistances > 0 kΩ, beta ≥ 1, VBE 0.1–2 V, source amplitude > 0 and ≤ 1 V, source frequency 1 Hz–1 MHz, VCC > 0 V, parse finite numbers only, kΩ→Ω conversion after validation)
   - **Deleted the `_parse_spice_form` delegating wrapper inside `create_app()`** — the module-level `parse_spice_form` is used directly by both `/spice/run` and `/ce-lab`; valid-input behavior is unchanged
   - Added `CE_LAB_DEFAULTS = dict(SPICE_DEFAULTS)` beside `SPICE_DEFAULTS`
   - Updated `/spice/run` to use `parse_spice_form()`
   - Added `GET /ce-lab` route with `_ce_lab_dashboard()` helper; passes raw `CE_LAB_DEFAULTS` (kΩ units) to the template so RC renders as `2.2 kΩ` instead of SI-converted `2200.0 Ω`
   - Fixed inclusive lower bounds: `value < lo` for beta (≥1), vbe (0.1–2.0), source_freq (1–1MHz); `value <= lo` (strict >0) for vcc/rc/r1/re/rl/source_ampl

2. **`templates/ce_lab.html`** (new file):
   - Minimal skeleton extending `base.html`
   - Title, hidden `analysis` input, form fields for VCC, RC, source amplitude, source frequency, and placeholder result area

3. **`templates/base.html`** (modified):
   - Added nav link to `/ce-lab` keeping existing DC Bias and SPICE Sim links

4. **`tests_spice/test_ce_lab.py`** (modified):
   - Added `test_ce_lab_get_renders_skeleton` — GET /ce-lab returns 200, contains "CE Amplifier Lab", has `name="analysis"`, no "SPICE SIMULATION RESULTS (NGSPICE)" in HTML
   - Added `test_ce_lab_nav_links` — rendered HTML contains nav links to `/`, `/spice`, and `/ce-lab`
   - Added 11 parametrized `test_parse_spice_form_bounds` tests:
     - `beta=1` passes (inclusive lower bound); `beta=0` fails with "Beta must be greater than or equal to 1.0"
     - `vbe=0.1` and `vbe=2.0` pass (inclusive 0.1–2.0); `vbe=0.01` fails with "VBE must be greater than or equal to 0.1"
     - `source_ampl=1.0` passes (>0 and ≤1 V); `source_ampl=0` fails with "Source amplitude must be greater than 0.0"
     - `source_freq=1` and `source_freq=1e6` pass (inclusive 1–1MHz); `source_freq=1e7` fails with "Source frequency must be less than or equal to 1000000.0"
     - `rc=0` fails (strict >0 kΩ); `rc=0.001` passes
   - Added `source_ampl="0.010"` → `0.01` assertion and corroborated `source_freq`/`beta`/`vbe` passthrough to `test_parse_spice_form_valid`

## Test Results

Full suite run (with pytest from repo root):
```
5 failed, 80 passed in 0.74s
```

The 5 failures are the same pre-existing assertion failures in `tests/test_routes.py`; all `tests_spice/test_ce_lab.py` tests pass. No new failures were introduced.

Prior controller baseline (before these fixes): `5 failed, 66 passed in 0.97s`. Delta: +14 passing tests (from 66 to 80).

## Fix round 1

1. **Missing route tests** — Added `test_ce_lab_get_renders_skeleton` and `test_ce_lab_nav_links` to `tests_spice/test_ce_lab.py`; both pass.
2. **Inclusive lower bounds not honored** — Fixed `app.py` bound checks to use `value < lo` for beta/ vbe/ source_freq (inclusive ≥ lo) and `value <= lo` (strict >0) for vcc/rc/r1/re/rl/source_amp; added 11 boundary parametrized tests `test_parse_spice_form_bounds` covering all specified boundary cases — all pass.
3. **Wrong units on `/ce-lab` for RC** — Changed `ce_lab` route to pass raw `CE_LAB_DEFAULTS` (kΩ units) to `_ce_lab_dashboard` instead of SI-converted values; template now renders `2.2 kΩ` for RC.
4. **Missing valid-form assertion** — Added `assert result_values["source_ampl"] == 0.01` (and corroborated `source_freq`/`beta`/`vbe` passthrough) to `test_parse_spice_form_valid` in `tests_spice/test_ce_lab.py`; all pass.
5. **Report line 9 correction** — Removed false claim that `_parse_spice_form` is a delegating wrapper inside `create_app()`; the wrapper was deleted and the module-level `parse_spice_form` is used directly.

**Files modified**: `app.py`, `templates/ce_lab.html`, `templates/base.html`, `tests_spice/test_ce_lab.py`, `task-2-report.md`

## Status

DONE