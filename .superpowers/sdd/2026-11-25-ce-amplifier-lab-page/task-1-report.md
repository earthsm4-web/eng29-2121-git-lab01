# Task 1: Pure AC/transient metrics with fixed definitions (TDD)

## Implemented

### `bjt/spice_metrics.py`
- `AcSummary` dataclass: `gain_db_at_frequency`, `gain_frequency_hz`, `midband_gain_db`, `phase_deg_at_frequency`, `low_cutoff_hz`, `high_cutoff_hz`, `bandwidth_hz`, `cutoff_note`
- `TranSummary` dataclass: `time_s`, `vin_peak_to_peak_v`, `vout_peak_to_peak_v`, `analysis_window_start_s`, `sample_count`
- `ac_summary(result, target_freq_hz) -> AcSummary`: closest real frequency for gain/phase; `max(gain_db)` for midband; 3-dB cutoffs via linear interpolation around peak index; `None` + note when crossing absent; `ValueError` for empty/mismatched arrays
- `tran_summary(result, source_freq_hz) -> TranSummary`: skips first two cycles; peak-to-peak voltages in window; `ValueError` for zero frequency, empty arrays, mismatched lengths, or no data after window

### `tests_spice/test_ce_lab.py`
- 10 TDD tests verifying pure function behavior with synthetic arrays

## TDD Cycle

**RED**: Initial test collection failed with `ImportError: No module named 'bjt'` — the module did not exist.

**GREEN**: After implementing `bjt/spice_metrics.py`, all 10 tests pass:
- `test_ac_summary_finds_gain_phase_and_3db_bandwidth` — gain=20dB, phase=180°, midband=20dB, low_cutoff≈91Hz, high_cutoff≈1900Hz, bandwidth=1809Hz
- `test_ac_summary_bandwidth_none_when_no_crossing` — `bandwidth_hz is None`, `cutoff_note` contains "not found"
- `test_ac_summary_gain_frequency_hz_returns_real_bin` — off-bin target 950.0 Hz returns real bin 1000.0 with correct gain/phase
- `test_tran_summary_ignores_first_two_cycles` — window_start=0.002s, sample_count=3, vin_ptp=2.0V, vout_ptp=4.0V, time_s=0.004s
- `test_tran_summary_raises_on_zero_freq` — `ValueError` raised for zero frequency
- `test_tran_summary_short_record_raises_valueerror` — short transient record (two-cycle window exceeds dataset) raises `ValueError`
- `test_tran_summary_empty_time_raises_valueerror` — empty `time` array raises `ValueError`
- `test_tran_summary_empty_vin_raises_valueerror` — empty `vin` array raises `ValueError`
- `test_tran_summary_empty_vout_raises_valueerror` — empty `vout` array raises `ValueError`
- `test_tran_summary_mismatched_lengths_raises_valueerror` — mismatched `time`/`vin`/`vout` lengths raise `ValueError`

## Fix round 1

### Finding 1 (Critical): `gain_frequency_hz` reports unmeasured frequency
- **Code**: `bjt/spice_metrics.py:138` returned `target_freq_hz` instead of the real bin frequency
- **Fix**: Changed `gain_frequency_hz=target_freq_hz` to `gain_frequency_hz=freq[target_idx]` (the actual frequency bin closest to target)
- **Test & output**: `test_ac_summary_gain_frequency_hz_returns_real_bin` with target 950.0 Hz
  ```
  eng29-2121-git-lab01/tests_spice/test_ce_lab.py::test_ac_summary_gain_frequency_hz_returns_real_bin PASSED [ 60%]
  ```
  Asserts `summary.gain_frequency_hz == 1000.0` and `summary.gain_db_at_frequency == 20.0`, `summary.phase_deg_at_frequency == 180.0`

### Finding 2 (Important): `tran_summary` insufficient-window path silently uses first two cycles
- **Code**: `bjt/spice_metrics.py:166` set `start_idx = 0` with no sentinel; `if not window_time` at line 176 could never be true for records where time extends past the window start
- **Fix**: Changed `start_idx` to `start_idx: int | None = None`; added `if start_idx is None: raise ValueError("no data after analysis window (first two cycles extend beyond dataset)")`; added empty-array and mismatched-length validation before window computation
- **Test & output**: `test_tran_summary_short_record_raises_valueerror` with `time=[0.0, 0.0001]`, `vin=[1.0, 2.0]`, `vout=[1.0, 2.0]`, source 1000 Hz
  ```
  eng29-2121-git-lab01/tests_spice/test_ce_lab.py::test_tran_summary_short_record_raises_valueerror PASSED [ 60%]
  ```
  Asserts `ValueError` is raised because the two-cycle analysis window (2.0ms) extends beyond the dataset maximum time (0.0001s).

### Finding 3 (Important): `tran_summary` lacks empty/mismatched array validation
- **Code**: `bjt/spice_metrics.py:158-181` indexed `max/min` on slices without checking empty `time`/`vin`/`vout` or equal lengths
- **Fix**: Added explicit `ValueError` raises for `not time`, `not vin`, `not vout`, and `len(time) != len(vin) or len(time) != len(vout)` before any window computation
- **Test & output**: `test_tran_summary_empty_time_raises_valueerror`, `test_tran_summary_empty_vin_raises_valueerror`, `test_tran_summary_empty_vout_raises_valueerror`, `test_tran_summary_mismatched_lengths_raises_valueerror`
  ```
  eng29-2121-git-lab01/tests_spice/test_ce_lab.py::test_tran_summary_empty_time_raises_valueerror PASSED [ 70%]
  eng29-2121-git-lab01/tests_spice/test_ce_lab.py::test_tran_summary_empty_vin_raises_valueerror PASSED [ 80%]
  eng29-2121-git-lab01/tests_spice/test_ce_lab.py::test_tran_summary_empty_vout_raises_valueerror PASSED [ 90%]
  eng29-2121-git-lab01/tests_spice/test_ce_lab.py::test_tran_summary_mismatched_lengths_raises_valueerror PASSED [100%]
  ```

### Finding 4 (Important): Tests only use exact-bin target 1000.0
- **Test**: Added `test_ac_summary_gain_frequency_hz_returns_real_bin` with target 950.0 Hz, asserting `gain_frequency_hz == 1000.0` (the measured closest real bin) and correct gain/phase at that bin
- **Code**: No code change needed beyond the `gain_frequency_hz=freq[target_idx]` fix above

### Finding 5 (Important): Report correction — controller-verified full-suite evidence
- **Controller command**: `.venv\Scripts\python -m pytest -q` run from repo root
- **Exact final summary line**: `5 failed, 59 passed in 0.93s`
- **Failing tests** (all pre-existing assertion failures in `tests/test_routes.py`):
  - `test_active_page_shows_schematic_and_walkthrough`
  - `test_schematic_follows_the_computed_point`
  - `test_schematic_reports_the_saturation_qpoint`
  - `test_schematic_reports_the_cutoff_qpoint`
  - `test_index_renders_the_dashboard_with_defaults`
- **Delta from prior baseline**: Baseline was `5 failed, 49 passed`. After Task 1 fixes (no code changes to `tests/*`, `bias.py`, `params.py`, `validate.py`, `steps.py`): `5 failed, 59 passed`; the five pre-existing assertion failures in `tests/test_routes.py` are unchanged; all 10 `tests_spice/test_ce_lab.py` tests pass with no new failures.
- **No filtered-suite or collection-error claims**: The exact command `.venv\Scripts\python -m pytest -q` from the repo root ran successfully with the summary above; no matplotlib errors, no runner-file import mismatches, and no suite-filtering was applied.

## Commit

```
f1a63d5 fix(lab4): report measured AC bin and validate transient window
  - bjt/spice_metrics.py (new)
  - tests_spice/test_ce_lab.py (new)
```