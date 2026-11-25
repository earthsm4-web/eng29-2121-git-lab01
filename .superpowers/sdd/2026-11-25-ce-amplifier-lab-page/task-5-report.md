# Task 5 report — Accessible tabs, scoped styling, and responsive motion

**Status:** DONE
**Commit:** `c8226a6` — `feat(lab4): add accessible CE lab tabs and responsive styling`
**Branch:** `feat/lab4-ce-spice-ngspice`

## Files changed

- Created `static/ce_lab.js` — no-dependency ARIA tab controller (IIFE + `DOMContentLoaded`, no-op when tablist absent).
- Modified `static/style.css` — appended clearly delimited Task 5 CE-lab section (scoped tokens, tabs, panels, results, unit chips, `ceFade`, reduced-motion, breakpoints).
- Modified `templates/ce_lab.html` — replaced visible `<select name="analysis">` with the single hidden input, added ARIA tab/tablist/tabpanel markup, hint text, script include, folded inline `style=` attributes into scoped classes.
- Modified `tests_spice/test_ce_lab.py` — appended 4 new tests (no earlier tests rewritten).

## RED

Command:

```
.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k tabs -v
```

Exact final summary:

```
====================== 4 failed, 44 deselected in 0.72s =======================
```

Failures (all four new Task 5 tests failed before implementation):

```
FAILED tests_spice/test_ce_lab.py::test_ce_lab_tabs_render_aria_tablist_tabpanel_markup
FAILED tests_spice/test_ce_lab.py::test_ce_lab_tabs_hidden_analysis_field_is_single_hidden_input
FAILED tests_spice/test_ce_lab.py::test_ce_lab_tabs_scoped_stylesheet_has_required_ce_lab_rules
FAILED tests_spice/test_ce_lab.py::test_ce_lab_tabs_javascript_controller_source
```

The first two failed on missing ARIA markup / single hidden input; the stylesheet test failed on missing `.ce-lab-grid` / `--ce-navy` / breakpoints / `ceFade`; the JS test failed because `static/ce_lab.js` did not exist.

## GREEN

Command:

```
.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k tabs -v
```

Exact final summary:

```
====================== 4 passed, 44 deselected in 0.58s =======================
```

All four Task 5 tests PASSED.

Focused file sanity check (all Task 1–5 CE lab tests):

```
.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -v
```

Exact final summary line:

```
============================= 48 passed in 1.83s ==============================
```

(All 44 pre-existing Task 1–4 tests plus the 4 new Task 5 tests pass.)

## Full suite

Command (run once):

```
.venv\Scripts\python -m pytest -q
```

Exact final summary line:

```
5 failed, 97 passed in 2.00s
```

The five failures remain only the known pre-existing `tests/test_routes.py` assertions (`test_active_page_shows_schematic_and_walkthrough`, `test_schematic_follows_the_computed_point`, `test_schematic_reports_the_saturation_qpoint`, `test_schematic_reports_the_cutoff_qpoint`, `test_index_renders_the_dashboard_with_defaults`). Baseline before Task 5 was `5 failed, 93 passed`; now `5 failed, 97 passed` (+4 new passing tests, no new failures, no collection errors).

## What was implemented

### `templates/ce_lab.html`

- Replaced the visible `<select id="analysis" name="analysis">` (+ label) with exactly one hidden input:
  `<input type="hidden" id="analysis" name="analysis" value="{{ analysis }}">` (server passes `analysis` on GET and POST, so the hidden value persists across submits).
- `.ce-lab-tabs` now carries `role="tablist"` and `aria-label="Analysis modes"`; three buttons carry `role="tab"`, unique ids (`ce-tab-op` / `ce-tab-ac` / `ce-tab-tran`), `data-analysis`, `aria-controls`, `aria-selected` (`true`/`false`), and `tabindex` (`0` selected / `-1` otherwise).
- Panels carry `role="tabpanel"`, matching `id`, and `aria-labelledby` pointing at their tab; inactive panels get the `hidden` attribute. The active panel (`analysis == "op"` on GET) is visible with no-JS default DC.
- Visible hint added: "Choose an analysis, then click Run Simulation."
- Added `<script src="{{ url_for('static', filename='ce_lab.js') }}"></script>` near the end of the content block.
- Folded inline `style=` attributes into scoped classes (`ce-model-note`, `ce-details`, `ce-details-summary`, `ce-run-log`, `ce-error-log`) and removed them from the template.

### `static/ce_lab.js`

- IIFE + `DOMContentLoaded` listener; no-op when no `.ce-lab-tabs[role="tablist"]` is present.
- Click activates the tab; ArrowLeft/ArrowRight wrap around; Home/End jump to first/last.
- Activation sets `aria-selected`, `tabindex`, toggles panel `hidden`, moves focus to the newly active tab, and writes the tab's `data-analysis` into the single hidden `#analysis` input.
- Never calls `form.submit()` or dispatches submit; user clicks "Run Simulation".
- On load, syncs UI to the hidden input's current value (so a POST returning `analysis="ac"` shows AC before any click).

### `static/style.css`

- Appended a clearly delimited Task 5 section; existing `.dashboard`, `.card`, `.field`, and other shared rules untouched.
- `.ce-lab-grid` scoped `--ce-navy` (plus `--ce-navy-soft`, `--ce-navy-line`) tokens, 3-column grid on wide screens.
- `.ce-lab-tabs`, `.ce-lab-tab` (selected state via `aria-selected="true"`), `.ce-lab-tab-hint`, `.ce-lab-panel`, `.ce-lab-result`, `.ce-lab-grid .unit-chip` styling.
- `@keyframes ceFade` applied to `.ce-lab-panel:not([hidden])`; `@media (prefers-reduced-motion: reduce) { ... animation: none ... }`.

### `tests_spice/test_ce_lab.py`

- Appended 4 tests only (no earlier tests rewritten):
  - `test_ce_lab_tabs_render_aria_tablist_tabpanel_markup` — `role="tablist"`, three `role="tab"`, three `role="tabpanel"`, `aria-selected="true"` on DC, `hidden` on inactive panels, hint, `/static/ce_lab.js` script ref, no inline `style=`.
  - `test_ce_lab_tabs_hidden_analysis_field_is_single_hidden_input` — `html.count('name="analysis"') == 1`, hidden input form, no `<select`.
  - `test_ce_lab_tabs_scoped_stylesheet_has_required_ce_lab_rules` — stylesheet tokens/breakpoints/animation.
  - `test_ce_lab_tabs_javascript_controller_source` — JS file exists, ArrowLeft/ArrowRight, no `form.submit()`.

## Self-review

- Exactly one `name="analysis"` remains in the rendered `/ce-lab` HTML and it is a hidden input; DC (`op`) is the no-JS default with its panel visible and inactive panels carrying `hidden`.
- Engineering numbers still come only from real ngspice output; no mock/random/static values, no hard-coded gain/cutoff/bandwidth; no `app.py` or `bjt/*` changes; no analytical comparison on `/ce-lab`.
- Shared CSS rules (`.dashboard`, `.card`, `.field`, existing media queries) were not altered; only appended CE-lab-scoped rules.

## Concerns

- None blocking. Minor: browser-level keyboard interaction (focus ring, actual arrow-key behavior) is verified by source assertions only, not a live browser run (Task 6 scope).
- Minor: `.ce-lab-grid .unit-chip` adds a scoped override for unit chips that are primarily used on other pages; harmless and additive.

## Fix-round commit

- Source commit: `feat(lab4): add accessible CE lab tabs and responsive styling` (`c8226a6`)
- Report commit: `docs(lab4): record Task 5 evidence`
