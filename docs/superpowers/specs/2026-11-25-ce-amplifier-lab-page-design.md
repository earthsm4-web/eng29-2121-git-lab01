# CE Amplifier Lab Page — Design

Date: 2026-11-25

## Intent

Add a separate, teaching-oriented **CE Amplifier Lab** page to the existing ENG29 2121 Flask app. The page should let a student edit CE divider-bias parameters, run real ngspice analyses, and read DC / AC / Transient evidence in a 3-column engineering dashboard. It must not disturb the existing DC Bias calculator (`/`) or SPICE Sim page (`/spice`).

## Goals

- New route `/ce-lab` with a strict 3-column desktop layout chosen from mockup **A**.
- Left column: inline CE schematic (NPN Q1, R1/R2, RC, RE, Cin, Cout, RL, VCC, Vin, GND) plus editable VCC, RC, R1, R2, RE, RL, input amplitude, frequency, beta, VBE, and **Run Simulation**.
- Middle column: accessible tabs **DC Analysis**, **AC Analysis**, **Transient Analysis**; each tab renders only plots/results from a real ngspice run of that type.
- Right column: engineering results with explicit units; sections for DC operating point, AC frequency response (gain, phase, frequency, cutoff, bandwidth), and transient response (Vin, Vout, time).
- Reuse `bjt/spice_engine.py`, `bjt/spice_plot.py`, the existing Flask/Jinja/CSS stack, and existing validation patterns.
- Keep analytical DC comparison only on the existing `/spice` page; the new page shows SPICE evidence only and never mixes analytical values into any tab.
- Validate invalid input before netlist generation and show field-level errors without stale success state.
- Responsive at desktop, tablet, and mobile widths; reduced-motion respected.
- Tests added only in a new `tests_spice/` file; `tests/*` and protected `bjt/*` analytical files untouched.

## Non-goals

- No new solver, no replacement architecture, no standalone app.
- No bypass-capacitor switch in v1.
- No claim that the existing `.model QNPN NPN(IS=1e-14 BF=100.0)` is instructor-verified; it is a simplified model the user explicitly allowed for this build.
- No static/decorative plots, random values, hard-coded gain/cutoff/bandwidth, or hidden ngspice errors.
- No modification of `/`, `/spice`, `bjt/bias.py`, `bjt/params.py`, `bjt/validate.py`, `bjt/steps.py`, or existing tests.

## Constraints

- `AGENTS.md` is binding: all displayed SPICE numbers must come from real ngspice stdout artifacts; comparison to `dc_bias.py` is DC-only with assumptions stated.
- `ngspice` is invoked via `subprocess.run([...], cwd=<isolated temp dir>, timeout=60)`, no `shell=True` (existing adapter already does this).
- The reference image could not be visually decoded by this model; the written brief is authoritative. Layout A was selected by the user from a browser mockup.
- The route must work alongside existing routes; adding one nav link to `base.html` is permitted but existing links stay intact.

## Approaches considered

### 1. New page, run active tab only — **chosen**

Add `/ce-lab`, a new template, a small route helper, and scoped CSS. Reuse the current engine and plot functions. The form carries a hidden `analysis` value set by the tab UI; pressing **Run Simulation** runs `.op`, `.ac`, or `.tran` for the selected tab. Results for other tabs are not invented or reused after parameter changes.

Trade-off: switching tabs after a run may show an empty state until that tab is run; this is preferable to showing stale or fabricated results.

### 2. New page, one click runs all three analyses

One POST runs `.op`, `.ac`, and `.tran`, filling every tab. More complete at first glance, but three solver runs per click, three independent error paths, longer waits, and greater risk of mixing a failed analysis with a successful one.

### 3. Modify `/spice` in place

Fewer files, but it changes an existing page that current behavior and tests may rely on. It conflicts with the request to add a page without affecting the old system.

## How it will be built

### Routing and views

- `app.py`: add module-level `parse_spice_form(form)` consumed by both the old nested helper and the new route; add `GET /ce-lab` and `POST /ce-lab/run`.
- Render with a new `_ce_lab_dashboard(...)` helper that passes explicit `analysis`, `values`, `errors`, `spice_result`, `spice_error`, and derived metrics to the template.
- On error: `spice_result=None`, no plot markup, no success badge, and the real log/error text shown.

### Calculation / presentation separation

- New `bjt/spice_metrics.py`: pure functions deriving AC and transient display values from real `SpiceAcResult` / `SpiceTranResult` arrays. Definitions are fixed below so identical arrays always produce identical displayed numbers.

#### Metric definitions (designer's call)

- `gain_at_frequency_db`: gain at the frequency in the real sweep closest to the user's entered source frequency; this is the value labelled “Voltage Gain @ f_in”.
- `midband_gain_db`: maximum `gain_db` in the real sweep; this is the reference for −3 dB crossings, not a hand-entered constant.
- `f_low_hz`: first ascending crossing where `gain_db <= midband_gain_db - 3`; `f_high_hz`: last descending crossing of the same threshold. `bandwidth_hz = f_high_hz - f_low_hz` only when both exist. Otherwise UI shows “not found in 1 Hz–1 MHz sweep” and leaves the numeric field blank.
- `phase_at_frequency_deg`: `phase_deg` at the same closest-frequency sample; the wrapped value from ngspice is kept, not artificially unwrapped.
- Transient values are computed only from samples after the first two source cycles of the real `.tran` window: `vin_peak_to_peak`, `vout_peak_to_peak`, and the final sample time. This avoids startup transients being reported as steady-state amplitude. Values remain real parsed ngspice data.
- Templates never compute engineering values; they only format values passed from Flask with explicit units.
- `bjt/spice_engine.py` stays the only module that invokes ngspice.

### UI / UX

- `templates/ce_lab.html` extends `base.html`; `templates/_ce_circuit.html` holds an accessible inline SVG schematic with component labels and no fabricated node voltages.
- `static/style.css` gets scoped `.ce-lab*` additions: 3-column grid, tab strip, result cards, small-unit chips, subtle fade-in for active panel, and breakpoints at 1100px / 860px / 560px.
- `static/ce_lab.js` (small, progressive enhancement): tab selection updates `aria-selected`, hidden panel state, and hidden `analysis` field. Without JS, the form still posts the default `op` analysis.
- Result provenance badge: `SPICE (ngspice)` only. This new page does not display `dc_bias.py` values; the existing `/spice` page remains the only place for DC analytical comparison and its assumptions note.
- Model provenance note: the simplified model line is shown in the netlist details and labelled as simplified, not instructor-verified.

### Input validation

- Reuse existing finite-number checks and add engineering bounds before netlist creation: resistances > 0 kΩ; beta ≥ 1; VBE 0.1–2 V; source amplitude > 0 and ≤ 1 V (zero is rejected because AC `vm(6)/vm(2)` gain would be undefined); frequency 1 Hz–1 MHz; VCC > 0 V.
- Errors are keyed by form field and rendered inline; a 400 response is returned without calling ngspice.

### Testing

- New `tests_spice/test_ce_lab.py` only.
- Tests: route availability, invalid input rejection, no stale success markup on engine error, correct tab state, metric functions from synthetic arrays used only as unit-test fixtures for the metric functions (never rendered as ngspice results), and a real ngspice smoke run for each analysis when the local binary is present.
- Browser acceptance: open `/ce-lab`, run each tab with real values, verify plot, netlist, engine status, error path, and responsive widths.

## Files expected to change or be added

- Modify: `app.py`, `templates/base.html`, `static/style.css`, `README.md`, `docs/validation.md`
- Add: `templates/ce_lab.html`, `templates/_ce_circuit.html`, `static/ce_lab.js`, `bjt/spice_metrics.py`, `tests_spice/test_ce_lab.py`, `PRODUCT.md`, this spec
- Read-only: `bjt/bias.py`, `bjt/params.py`, `bjt/validate.py`, `bjt/steps.py`, `tests/*`, existing `/` and `/spice` templates/behavior

## Success criteria

- `GET /ce-lab` renders without needing a run.
- Each tab's Run button launches the matching real ngspice analysis and updates only that tab's plot/results.
- Invalid input produces a field error and no netlist/run.
- ngspice failure shows error/log and no success-state markup.
- Gain/cutoff/bandwidth and transient peaks are derived from the parsed real arrays.
- Existing `pytest` failures remain at the known baseline; no new failures appear.
- Desktop / tablet / mobile browser checks pass with no clipped controls or unreadable plots.

## Builder latitude

The implementer may decide exact CSS class names, tab-panel markup, SVG geometry, and small helper structure, provided the constraints and success criteria above are met. Any decision that changes provenance labelling, model claims, or the no-stale-result rule must come back for approval.

## Next step

Approve this design, then write the implementation plan with `writing-plans` before any product code is changed.
