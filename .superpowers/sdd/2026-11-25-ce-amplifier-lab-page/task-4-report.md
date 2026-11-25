# Task 4 report — Full CE schematic and input/result panels

**Status:** DONE
**Commit:** `e7234bb` — `feat(lab4): add CE schematic and engineering result panels`
**Branch:** `feat/lab4-ce-spice-ngspice`

## Files changed

- Created `templates/_ce_circuit.html` — accessible inline SVG schematic.
- Modified `templates/ce_lab.html` — 3-column layout markup (left input + schematic, middle tab strip/panels, right always-visible engineering results).
- Appended 5 tests to `tests_spice/test_ce_lab.py` (no prior tests rewritten).

## RED

Command:

```
.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k schematic -v
```

Exact final summary:

```
================= 3 failed, 2 passed, 39 deselected in 0.75s ==================
```

Failures:

```
FAILED tests_spice/test_ce_lab.py::test_ce_lab_schematic_has_all_components_and_no_fabricated_values
FAILED tests_spice/test_ce_lab.py::test_ce_lab_schematic_engineering_panel_names
FAILED tests_spice/test_ce_lab.py::test_ce_lab_schematic_result_placeholders_on_get
```

The two early passes were precondition checks that already held in the Task 3 skeleton: the form already rendered `VCC (V)`, `RC (kΩ)`, etc., and there was already exactly one `name="analysis"` field. The new schematic, panel-name, and placeholder assertions were RED as required.

## GREEN

Command:

```
.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k schematic -v
```

Exact final summary:

```
====================== 5 passed, 39 deselected in 0.64s =======================
```

Focused file sanity check (all Task 1–4 CE lab tests):

```
44 passed in 1.73s
```

## Full suite

Command (run once):

```
.venv\Scripts\python -m pytest -q
```

Exact final summary line:

```
5 failed, 93 passed in 1.84s
```

Only the five known pre-existing `tests/test_routes.py` failures remain:

```
FAILED tests/test_routes.py::test_active_page_shows_schematic_and_walkthrough
FAILED tests/test_routes.py::test_schematic_follows_the_computed_point
FAILED tests/test_routes.py::test_schematic_reports_the_saturation_qpoint
FAILED tests/test_routes.py::test_schematic_reports_the_cutoff_qpoint
FAILED tests/test_routes.py::test_index_renders_the_dashboard_with_defaults
```

Baseline was `5 failed, 88 passed`; now `5 failed, 93 passed` (+5 new passing tests, no new failures).

## What was implemented

### `templates/_ce_circuit.html`

- `<svg role="img" aria-labelledby="ce-circuit-title ce-circuit-desc">`.
- `<title id="ce-circuit-title">Common-emitter amplifier with voltage-divider bias</title>`.
- `<desc id="ce-circuit-desc">` naming the topology (VCC, R1/R2 divider, Q1, RC, RE, Cout, RL, Cin, Vin, GND).
- Visible labels: `Q1`, `NPN`, `R1`, `R2`, `RC`, `RE`, `Cin`, `Cout`, `RL`, `VCC`, `Vin`, `GND`.
- No numeric voltage/current annotations; only geometry coordinates. A test rejects digit+unit patterns inside the SVG.

### `templates/ce_lab.html`

- `.ce-lab-grid` wrapper with exactly three column sections (Task 5 owns the CSS that makes them 3 columns).
- Left: schematic include in a `<figure>`, the single visible `<select name="analysis">`, all ten parameter fields with units, field errors, and the Run button.
- Middle: `.ce-lab-tabs` with three basic tab buttons and three `.ce-lab-panel` panels (`op`, `ac`, `tran`). The active analysis's panel shows the real plot; other panels show empty-state messages. No `role`/`aria` tab attributes or JS were added (Task 5 scope).
- Middle also carries success provenance `SPICE (ngspice)`, netlist, simplified-model note, and run log only when `spice_result` exists.
- Right: three always-rendered result sections:
  - `#ce-dc-results`: VB, VE, VC, VCE, IB (µA), IC (mA), IE (mA), Region.
  - `#ce-ac-results`: Voltage Gain (dB), Midband Gain, Phase (°), Frequency (Hz), Low/High Cutoff, Bandwidth; `cutoff_note` row only when `bandwidth_hz is None`.
  - `#ce-tran-results`: Vin/Vout peak-to-peak (V), Time (ms), Window Start, Samples.
  - Every cell renders `—` when its data is absent (GET, validation error, or a run of another analysis type).
- Error card and the generic "Configure parameters…" placeholder preserved; placeholder now suppressed when field errors are present.

## Self-review

- No engineering values computed or hard-coded in Jinja; only unit scaling of real parsed values (mA/µA/ms), consistent with Task 3.
- Existing Task 3 behaviors verified by the full CE lab file: validation field errors, `SPICE (ngspice)` provenance on success, no stale success markup on engine/processing errors, real plot data URI, simplified-model note near netlist, and absence of `DC Analytical` / `dc_bias.py` on `/ce-lab`.
- Exactly one `name="analysis"` occurrence on the page (asserted).
- `app.py`, `bjt/*`, `tests/*`, `/`, `/spice`, `index.html`, `spice.html`, CSS, and JS untouched.
- Task 5 handoff: markup already uses `.ce-lab-grid`, `.ce-lab-tabs`, `.ce-lab-tab`, `.ce-lab-panel`, and `data-analysis` attributes; no `role`/`aria-selected`/`hidden` yet, so Task 5 can add its asserted ARIA state and script hook without renaming or duplicating the analysis field.

## Concerns

- Minor: the three middle panels are all visible until Task 5 adds CSS/JS to hide inactive panels. This is expected for the sequential split and not test-visible.
- Minor: schematic label text uses plain SVG `<text>` without explicit `dominant-baseline`; geometry was chosen with generous spacing, but browser visual acceptance is Task 6's scope.
- Minor: labels for the analysis select remain a visible `<select>` rather than the hidden input described in the design; this preserves Task 3 behavior/no-JS fallback, and Task 5 is chartered to convert it.

## Fix round 1

Reviewer verdict: structure approved; two Important test-strength gaps. Both fixed in `tests_spice/test_ce_lab.py` only. No template or `app.py` change was needed — the current markup already satisfies the strengthened assertions.

### Finding 1 — all result cells must be placeholders on GET

**Gap:** `test_ce_lab_schematic_result_placeholders_on_get` only checked that each section contained at least one `—`, so a section could mix one placeholder with fabricated hard-coded values.

**Change:** added the helper

```python
def _ce_table_cells(section):
    """Return every result cell's text, unescaped and stripped."""
    from html import unescape

    return [
        unescape(cell).strip()
        for cell in re.findall(r"<td[^>]*>(.*?)</td>", section, re.DOTALL)
    ]
```

and rewrote the body of `test_ce_lab_schematic_result_placeholders_on_get` to extract every `<td>` in each of `ce-dc-results`, `ce-ac-results`, and `ce-tran-results`, require a non-empty cell list, and assert each stripped cell equals `—`:

```python
        cells = _ce_table_cells(section)
        assert cells, f"no result cells in #{section_id}"
        for cell in cells:
            assert cell == "—", (
                f"fabricated value in #{section_id}: {cell!r}; "
                "every GET result cell must be —"
            )
```

Covering test: `tests_spice/test_ce_lab.py::test_ce_lab_schematic_result_placeholders_on_get`.

### Finding 2 — SVG text must be exactly the allowed label set

**Gap:** the old guard caught only numbers that carried a unit suffix, so a bare annotation such as `<text>12</text>` or `<text>0.7</text>` slipped through.

**Change:** added the helper

```python
def _ce_svg_texts(svg):
    """Return the set of visible <text> labels drawn in the schematic."""
    from html import unescape

    return {
        unescape(text).strip()
        for text in re.findall(r"<text[^>]*>(.*?)</text>", svg, re.DOTALL)
    }
```

and added an exact set-equality assertion in `test_ce_lab_schematic_has_all_components_and_no_fabricated_values`, keeping the existing per-label presence loop and the digit+unit guard:

```python
    assert _ce_svg_texts(svg) == {
        "Q1", "NPN", "R1", "R2", "RC", "RE",
        "Cin", "Cout", "RL", "VCC", "Vin", "GND",
    }, f"unexpected schematic text labels: {_ce_svg_texts(svg)}"
```

Covering test: `tests_spice/test_ce_lab.py::test_ce_lab_schematic_has_all_components_and_no_fabricated_values`.

### RED demonstration (one-off, no committed template edits)

A temporary script loaded the real test module helpers and ran the strengthened assertions against deliberately violated in-memory strings. It was deleted after the run; no template or product file was modified.

Fabricated fixtures:

- Section: `<td>2.0 V</td>` plus `<td>&mdash;</td>`
- SVG: `<text>Q1</text><text>12</text>`

Exact output:

```
fabricated section cells: ['2.0 V', '�']
finding 1 guard: REJECTED -> fabricated value in #ce-dc-results: '2.0 V'
fabricated svg texts: ['12', 'Q1']
finding 2 guard: REJECTED -> unexpected schematic text labels: {'Q1', '12'}
real #ce-dc-results: 8 cells, all em-dash
real #ce-ac-results: 7 cells, all em-dash
real #ce-tran-results: 5 cells, all em-dash
real schematic labels: ['Cin', 'Cout', 'GND', 'NPN', 'Q1', 'R1', 'R2', 'RC', 'RE', 'RL', 'VCC', 'Vin']
REAL PAGE: both guards PASS
```

(The console rendered the em dash as `�` under the Windows code page; the assertions themselves used `\u2014` and the real-page check passed, confirming correct UTF-8 output.)

### Post-fix focused run

Command:

```
.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k schematic -v
```

Exact final summary line:

```
====================== 5 passed, 39 deselected in 0.62s =======================
```

All five schematic tests PASSED:

```
tests_spice/test_ce_lab.py::test_ce_lab_schematic_has_all_components_and_no_fabricated_values PASSED
tests_spice/test_ce_lab.py::test_ce_lab_schematic_form_labels_have_units PASSED
tests_spice/test_ce_lab.py::test_ce_lab_schematic_engineering_panel_names PASSED
tests_spice/test_ce_lab.py::test_ce_lab_schematic_result_placeholders_on_get PASSED
tests_spice/test_ce_lab.py::test_ce_lab_schematic_analysis_field_is_not_duplicated PASSED
```

### Post-fix full suite (run once)

Command:

```
.venv\Scripts\python -m pytest -q
```

Exact final summary line:

```
5 failed, 93 passed in 1.85s
```

The five failures remain only the known pre-existing `tests/test_routes.py` assertions (`test_active_page_shows_schematic_and_walkthrough`, `test_schematic_follows_the_computed_point`, `test_schematic_reports_the_saturation_qpoint`, `test_schematic_reports_the_cutoff_qpoint`, `test_index_renders_the_dashboard_with_defaults`). No new failures or collection errors.

### Fix-round commit

- Test-only commit: `test(lab4): pin CE placeholders and schematic label set`
- Report commit: `docs(lab4): record Task 4 fix evidence`


