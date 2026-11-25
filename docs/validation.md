# การทดสอบเว็บฟอร์ม BJT DC Bias Web App (เคส A1–A5)

## ค่าคงที่ระบบ
| รายการ | ค่า |
|--------|-----|
| VCC | 12 V |
| RC | 2.2 kΩ |
| β | 100 |
| VBE | 0.70 V |

## ค่าอ้างอิงที่คำนวณไว้ล่วงหน้า (Engineering Electronics)

| เคส | โหมด | อินพุต | IC อ้างอิง (mA) | VCE อ้างอิง (V) | โซนการทำงาน | หมายเหตุ |
|-----|------|--------|-----------------|----------------|-------------|----------|
| A1 | Voltage Divider | R1=100 kΩ, R2=22 kΩ, RE=1 kΩ | 1.2299 | 8.0522 | Active | โหมดเดิมของ Lab 2 |
| A2 | Fixed Bias | RB=1 MΩ | 1.1300 | 9.5140 | Active | ไม่มี RE |
| A3 | Emitter Bias | RB=1 MΩ, RE=1 kΩ | 1.0263 | 8.7055 | Active | — |
| A4 | Emitter Bias | RB=1 MΩ, RE=2 kΩ | 0.9401 | 8.0328 | Active | RE เพิ่มจาก A3 → IC คาดว่าจะลดลง |
| A5 | Fixed Bias | RB=0 | — | — | — | คาดว่าจะมีข้อความแจ้งเตือน Error |

**สูตรอ้างอิง:**
- Divider: VTH = VCC·R2/(R1+R2), RTH = R1·R2/(R1+R2), IB = (VTH−VBE)/[RTH+(β+1)·RE]
- Fixed: IB = (VCC−VBE)/RB
- Emitter: IB = (VCC−VBE)/[RB+(β+1)·RE]
- ร่วม: IC = β·IB, IE = (β+1)·IB, VE = IE·RE (Fixed: VE=0), VB = VE+VBE, VC = VCC−IC·RC, VCE = VC−VE

## เกณฑ์ผ่าน
- IC: ความต่างไม่เกิน 0.01 mA
- VCE: ความต่างไม่เกิน 0.02 V
- A5: เว็บต้องไม่ล่ม และไม่แสดงผลลัพธ์เก่าค้างอยู่

## ตารางผลการทดสอบ

| เคส | โหมด | อินพุต | IC เห็นจริง (mA) | VCE เห็นจริง (V) | ผลต่าง IC (mA) | ผลต่าง VCE (V) | วิธีตรวจ | สถานะ |
|-----|------|--------|------------------|------------------|-----------------|-----------------|-----------|--------|
| A1 | Voltage Divider | R1=100k, R2=22k, RE=1k | 1.2299 | 8.0522 | 0.0000 | 0.0000 | OpenCode (HTTP POST via Python) | ผ่าน |
| A2 | Fixed Bias | RB=1M | 1.1300 | 9.5140 | 0.0000 | 0.0000 | OpenCode (HTTP POST via Python) | ผ่าน |
| A3 | Emitter Bias | RB=1M, RE=1k | 1.0263 | 8.7054 | 0.0000 | 0.0001 | OpenCode (HTTP POST via Python) | ผ่าน |
| A4 | Emitter Bias | RB=1M, RE=2k | 0.9401 | 8.0328 | 0.0000 | 0.0000 | OpenCode (HTTP POST via Python) | ผ่าน |
| A5 | Fixed Bias | RB=0 | — | — | — | — | OpenCode (HTTP POST via Python) | ผ่าน |

## หมายเหตุ
- ค่าเห็นจริงอ่านจากตารางผลลัพธ์บนหน้าเว็บ (แสดง 4 ตำแหน่งทศนิยมสำหรับ mA และ V)
- การทดสอบดำเนินทีละเคส โดยเคสถัดไปจะเริ่มหลังจากบันทึกเคสก่อนแล้ว


---

# Lab 4 — CE Amplifier (ngspice) Validation

## Environment
- ngspice binary: `C:\tools\ngspice-47\Spice64\bin\ngspice_con.exe`
- ngspice version: 47 (Spice64)
- Python: 3.12.7 (.venv)
- matplotlib: installed in .venv
- Date: 2026-11-24

## CE Voltage Divider v1 (Reference Circuit)
| Parameter | Value |
|-----------|-------|
| VCC | 12 V |
| RC | 2.2 kΩ |
| R1 | 100 kΩ |
| R2 | 22 kΩ |
| RE | 1 kΩ |
| RL | 10 kΩ |
| Beta | 100 |
| VBE (analytical ref) | 0.70 V |
| Source | 10 mV amplitude, 1 kHz (SIN) |
| Coupling caps | CIN=10u, COUT=10u |

## DC Operating Point (.op) — ngspice vs Analytical (dc_bias.py)

| Quantity | SPICE (ngspice) | Analytical (dc_bias.py) | Difference | Unit |
|----------|-----------------|-------------------------|------------|------|
| VB | 1.9363 | 1.9422 | -0.0059 | V |
| VE | 1.2751 | 1.2422 | +0.0329 | V |
| VC | 9.2225 | 9.2943 | -0.0718 | V |
| VCE | 7.9474 | 8.0522 | -0.1047 | V |
| IC | 1.2637 | 1.2299 | +0.0338 | mA |
| IB | 12.6366 | 12.2990 | +0.3376 | µA |
| IE | 1.2763 | 1.2422 | +0.0341 | mA |
| Region | active | ACTIVE | agree | — |

**Note:** Small differences are expected because ngspice uses the nonlinear BJT model (IS/BF) while dc_bias.py uses the hand-analysis constant-VBE approximation. Comparison is valid (same circuit, same DC assumptions).

## AC Analysis (.ac) — ngspice
- Sweep: `.ac dec 10 1 1e6` (61 points)
- At ~1 kHz (mid-band): Gain ≈ 4.86 dB, Phase ≈ -3.14°
- Plot: Bode (Gain dB / Phase ° vs Frequency Hz) generated from real ngspice data
- No comparison with dc_bias.py (AC mode — per AGENTS.md rule)

## Transient Analysis (.tran) — ngspice
- Sweep: `.tran 5u 5m` (5 cycles at 1 kHz, 59 points)
- Signals: Vin (node 2), Vout (node 6 through COUT)
- Plot: Vin/Vout vs Time (ms) generated from real ngspice data
- No comparison with dc_bias.py (Transient mode — per AGENTS.md rule)

## Browser Acceptance (Playwright MCP) — rerun after hardening (2026-11-24 18:10 local)
| Test | Result | Evidence |
|------|--------|----------|
| GET /spice loads | PASS | `docs/captures/spice-initial.png` |
| DC .op: SPICE + Analytical + Compare + Warnings + Netlist + Saved run | PASS | `docs/captures/spice-dc-op.png`, `docs/captures/spice-op-20261124-181033.txt` |
| AC .ac: Bode plot + no analytical compare warning + Netlist + Saved run | PASS | `docs/captures/spice-ac.png`, `docs/captures/spice-ac-20261124-181035.txt` |
| Tran .tran: waveform + no analytical compare warning + Netlist + Saved run | PASS | `docs/captures/spice-tran.png`, `docs/captures/spice-tran-20261124-181037.txt` |
| Engine status shown (ngspice OK) | PASS | all mode screenshots |
| Console errors | 0 errors | Playwright `browser_console_messages(level=error)` |

**Hardening verified:** `spice_engine.py` saves stdout output file and verifies exists+non-empty before parse; returncode!=0 raises `SpiceEngineError`; UI shows `Saved run` artifact path.

## pytest (existing suite)
- Command: `.venv\Scripts\python -m pytest -q`
- Result: **49 passed, 5 failed** (5 failures are pre-existing in test_routes.py: Lab 02 title expectation and schematic _r1 variable rendering; no regressions from Lab 4 changes; tests/* not modified)

## Known pre-existing test failures (not modified per AGENTS.md)
1. `test_active_page_shows_schematic_and_walkthrough` — expects "R1 47 kΩ" in schematic; template uses `_r1` variable not passed by _dashboard
2. `test_schematic_follows_the_computed_point` — same schematic variable issue
3. `test_schematic_reports_the_saturation_qpoint` — same schematic variable issue
4. `test_schematic_reports_the_cutoff_qpoint` — same schematic variable issue
5. `test_index_renders_the_dashboard_with_defaults` — expects "Lab 02..." title; base.html is Lab 03/04

---

# CE Amplifier Lab (`/ce-lab`) — observed verification (2026-11-25)

All numbers in this section were read from a real browser run on
`http://127.0.0.1:5001/ce-lab` or from the exact commands shown. The transistor
model in the generated netlist was `.model QNPN NPN(IS=1e-14 BF=100.0)` — a
simplified, lab-local model, not an instructor-verified device card. No
`dc_bias.py` value is compared anywhere on this page.

## Engine smoke (real ngspice)

Command:

```
.venv\Scripts\python -c "from bjt.spice_engine import SpiceParams,run_op,run_ac,run_tran; p=SpiceParams(vcc=12,rc=2200,r1=100000,r2=22000,re=1000,rl=10000,beta=100,vbe=0.7,source_ampl=0.01,source_freq=1000); print(len(run_op(p).run_log), len(run_ac(p).frequency), len(run_tran(p).time))"
```

Final output after the transient fix: `9802 61 1008`
(run-log characters, AC frequency bins, transient samples). Before the fix the
third number was `59`.

## Browser acceptance — DC (`.op`)

| Quantity | Observed value |
|----------|----------------|
| VB | 1.9363 V |
| VE | 1.2751 V |
| VC | 9.2225 V |
| VCE | 7.9474 V |
| IB | 12.6366 µA |
| IC | 1.2637 mA |
| IE | 1.2763 mA |
| Region | active |

Evidence: a rendered `img.spice-plot` with `alt="Plot from real ngspice op output"`
(natural size 944×465), provenance heading `SPICE Simulation Results (ngspice)`,
run-log section present, and the generated netlist visible on the page. The
hidden `analysis` input read `op`; only the DC panel was visible.

## Browser acceptance — AC (`.ac`)

| Quantity | Observed value |
|----------|----------------|
| Gain at 1 kHz | 4.86 dB |
| Midband max gain | 4.86 dB |
| Phase at 1 kHz | −3.14 ° |
| Closest frequency bin | 1000.0 Hz |
| Low −3 dB cutoff | 1.9 Hz |
| High −3 dB cutoff | not found |
| Bandwidth | not found |
| Cutoff Note | `low 3 dB cutoff at 1.9 Hz, high not found` |

Evidence: `img.spice-plot` with `alt="Plot from real ngspice ac output"`
(944×704). Clicking the AC tab changed the single hidden `analysis` input to
`ac` and revealed only the AC panel; the run then produced the values above.
No analytical comparison was shown.

## Browser acceptance — Transient (`.tran`)

| Quantity | Observed value |
|----------|----------------|
| Vin amplitude in analysis window | 0.020 V |
| Vout amplitude in analysis window | 0.035 V |
| Recorded duration | 5.000 ms |
| Analysis window | 2.000 ms |
| Samples in window | 601 |

Evidence: `img.spice-plot` with `alt="Plot from real ngspice tran output"`,
generated netlist directive `.tran 5e-06 0.005`, provenance heading
`SPICE Simulation Results (ngspice)`, and no error callout.

### Transient defect found and fixed during acceptance

The first transient run failed with:

```
CE Lab Error
Run could not be completed
CE lab processing error after ngspice run: no data after analysis window (first two cycles extend beyond dataset)
```

Direct engine inspection showed the generated directive `.tran 0.005 5e-06` and
`n=59`, `last=5e-06` — ngspice reads `.tran TSTEP TSTOP`, so the two arguments
were reversed and the run stopped after 5 µs instead of 5 ms. The directive was
corrected to `.tran {tstep} {tstop}` in `bjt/spice_engine.py`. After the fix the
same command reported `first 0.0 last 0.005 n 1008`, and the browser run showed
the values in the table above. A regression test
`test_tran_netlist_uses_ngspice_tstep_tstop_order` was added: RED before the fix,
GREEN after with `1 passed, 48 deselected in 0.56s`.

This also explains the `59 points` transient record in the earlier 2026-11-24
section above: that record came from the swapped directive and is superseded by
the corrected 1008-sample run.

## Invalid input — source amplitude `0`

Browser submission with `Source amplitude = 0` returned HTTP 400 and showed:

- field error: `Source amplitude must be greater than 0.0`
- the rejected value `0` retained in the field
- zero plot images, no provenance heading, no success heading
- every cell in `#ce-dc-results`, `#ce-ac-results`, and `#ce-tran-results`
  still showing `—`

The only browser console error was the expected `400 (BAD REQUEST)` for that
submission; no JavaScript errors were observed.

## Responsive layout (observed bounding boxes)

| Viewport | `grid-template-columns` | Column widths | Horizontal overflow |
|----------|-------------------------|---------------|---------------------|
| 1440 px | `465.781px 443.609px 443.609px` | 466 / 444 / 444 px, all on one row; `Analysis Workbench` at `x=502, y=155` beside `Circuit & Parameters` | none (`scrollWidth` 1425) |
| 1280 px | `410.703px 391.141px 391.156px` | 411 / 391 / 391 px, all on one row; workbench at `x=447, y=155` | none (`scrollWidth` 1265) |
| 820 px | `776.219px` | 776 px, stacked | none (`scrollWidth` 805) |
| 390 px | stacked single column | 346 px; `clipped=[]` | none (`scrollWidth` 375) |

Screenshots: `docs/captures/ce-lab-1440.png`, `docs/captures/ce-lab-1280.png`,
`docs/captures/ce-lab-820.png`, `docs/captures/ce-lab-390.png`.

Stale-build audit (2026-11-25): both local Flask processes (ports 5000 and
5001) were started from this repo and serve the same `static/style.css`
(SHA-256 `6E197B96F72223C3CBD39F543051D1A60620F30E8049806B26577A0717FB7938`).
There is only one `style.css` under `C:\Users\ASUS` and no git worktree. Flask
returns `Cache-Control: no-cache` plus an ETag, and a fresh fetch still contains
`body:has(.ce-lab-grid) .page { max-width: none; }` and the three-column
`.ce-lab-grid` rule. The in-app browser at 1000 px also shows two columns with
the workbench beside the sidebar. No narrow-left-column/empty-right defect is
present on `b5563e4`; if it remains visible, check browser zoom and the actual
`innerWidth` at the viewing surface.

## Test suite

Final command and result after all CE Lab changes and the transient fix:

```
.venv\Scripts\python -m pytest -q
5 failed, 98 passed in 2.00s
```

An immediately preceding identical run reported `5 failed, 98 passed in 2.09s`.

The five failures are the same pre-existing `tests/test_routes.py` assertion
failures listed above; `tests/*` was not modified. All `tests_spice` tests pass.
Observed Python/pytest during this run: Python 3.13.2, pytest 9.2.0.

---

# Lab 4 handout B1–B8 — real running-app validation (2026-11-25)

## Pre-flight (before any case)

| Check | Observed |
|-------|----------|
| Playwright MCP visible | Yes — 25 `tools.playwright.*` tools listed (including `browser_navigate`, `browser_snapshot`, `browser_fill_form`, `browser_select_option`, `browser_click`, `browser_evaluate`, `browser_take_screenshot`, `browser_resize`, `browser_console_messages`). |
| Flask localhost reachable | HTTP 200 on `http://127.0.0.1:5000/`, `http://127.0.0.1:5001/`, `/ce-lab` and `/spice`. |
| Server used for all evidence | `http://127.0.0.1:5001` (post-fix server; port 5000 is stale). |
| Method | Playwright MCP only for browser evidence. One shell command was used solely to read the ngspice binary version banner (`ngspice_con.exe -v`); it is labeled as a shell check, not browser evidence. Direct `fetch()` POSTs from the browser page context are labeled "direct POST" and are not presented as UI-flow clicks. |
| Application code | The original B1–B8 run used unmodified code. After the two defects were diagnosed, fixes were applied to `app.py`, `templates/index.html` and `static/style.css`, the `:5001` server was restarted, and B1/B8 were re-run against the fixed code (see "Fix re-verification" below). |

## Engine and model actually used

| Item | Value | Source |
|------|-------|--------|
| ngspice version | `ngspice-47 : Circuit level simulation program`, "Compiled with KLU Direct Linear Solver", Creation Date `Aug 11 2026 13:55:25` | Shell check: `C:\tools\ngspice-47\Spice64\bin\ngspice_con.exe -v` (exact banner quoted). Note: the saved run logs print "Using SPARSE 1.3 as Direct Linear Solver" at runtime; the version banner above is the authoritative version string. |
| BJT model | `.model QNPN NPN(IS=1e-14 BF=100.0)` for β=100 | Exact line copied from the netlist printed on every `/spice` run page and written to each saved run log, e.g. `docs/captures/spice-op-20261125-134735.txt` line 21. This is a simplified, lab-local model — not an instructor-verified device card. |
| Engine status observed | `ngspice OK — op/ac/tran analysis completed (<timestamp>)` plus a `Saved run:` artifact path | Every successful `/spice` run page. |

## Results

| Case | Method | Input | Expected/Reference | Observed | Evidence | Status |
|------|--------|-------|--------------------|----------|----------|--------|
| B1 (Regression) | Playwright MCP UI on `/` and `/calculate` after fix; every A1–A5 case driven through visible form controls (no direct POST) | Divider A1: VCC 12, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, β 100, VBE 0.7 V. Fixed A2: RB 1 MΩ. Emitter A3: RB 1 MΩ, RE 1 kΩ; A4: RB 1 MΩ, RE 2 kΩ. A5: Fixed RB 0. | A1 IC 1.2299 mA / VCE 8.0522 V; A2 IC 1.1300 mA / VCE 9.5140 V; A3 IC 1.0263 mA / VCE 8.7055 V; A4 IC 0.9401 mA / VCE 8.0328 V; A5 error, no stale result. **Mode switching must work cleanly.** | All five cases now run through the UI. A1: IC 1.2299 mA, VCE 8.0522 V — matches. Switching to Fixed exposes RB: `rbExists=true`, exactly one `name="mode"`, `visibleFields=[vcc,rb,rc,beta,vbe]`; A2 IC 1.1300 mA / VCE 9.5140 V — matches. Switching to Emitter gives `visibleFields=[vcc,rb,re,rc,beta,vbe]`; A3 IC 1.0263 mA / VCE 8.7054 V (handout 8.7055, Δ 0.0001 V), A4 IC shown as 940.100 µA (=0.9401 mA) / VCE 8.0328 V — matches. A5: HTTP 400, `RB must be greater than 0`, mode stays `fixed`, no result table and no stale IC. | Snapshots recorded `selectValue` and `visibleFields` for each mode; network log shows `POST /calculate => [400]` for A5. Final pass re-captured all five screenshots at 2026-11-25 13:46: `docs/captures/b1-divider.png`, `docs/captures/b1-fixed-ui-switch.png`, `docs/captures/b1-emitter-ui.png`, `docs/captures/b1-emitter-re2k-ui.png`, `docs/captures/b1-fixed-error.png`. | **PASS** (UI mode switching and A1–A5) |
| B2 (DC SPICE) | Playwright MCP UI: `/spice` → click Run (defaults = CE reference) → read table/log → screenshot; final pass 2026-11-25 13:47:35 | VCC 12 V, RC 2.2 kΩ, R1 100 kΩ, R2 22 kΩ, RE 1 kΩ, RL 10 kΩ, β 100, VBE 0.7 V; analysis `.op` | VB/VE/VC/VCE/IC from real ngspice output; run status, version and model recorded. | Table read from fresh run: VB 1.9363 V, VE 1.2751 V, VC 9.2225 V, VCE 7.9474 V, IC 1.2637 mA, IB 12.6366 µA, IE 1.2763 mA, region `active`. Engine `ngspice OK — op analysis completed (2026-11-25 13:47:35)`; saved `spice-op-20261125-134735.txt`; plot `DC Operating Point bar chart from ngspice .op` 944×465. Saved log shows raw node voltages `V(5) 1.275104e+00`, `V(4) 9.222546e+00`, `V(3) 1.936274e+00`. | `docs/captures/b2-dc-op.png`; log `docs/captures/spice-op-20261125-134735.txt`; netlist and engine status quoted above. | **PASS** |
| B3 (Change RE) | Playwright MCP UI: `/spice` → fill RE → click Run → read table/netlist → screenshot; final pass 2026-11-25 13:47:37 | RE changed from 1 kΩ to single new value 2 kΩ; all else defaults; `.op` | Operating Point/gain must update from simulation, not stale/cached values. | New run: VB 2.0395 V, VE 1.3940 V, VC 10.4818 V, VCE 9.0879 V, IC 0.6901 mA (was 1.2637 mA), IB 6.9015 µA. Netlist now `* RE=2000.0` / `RE 5 0 2000.0`. Engine `ngspice OK — op analysis completed (2026-11-25 13:47:37)`, new saved `spice-op-20261125-134737.txt`; raw `V(5) 1.393968e+00`, `V(4) 1.048182e+01`, `V(3) 2.039493e+00`. Values changed in the expected direction (IC down, VCE up). | `docs/captures/b3-re2k-dc.png`; log `docs/captures/spice-op-20261125-134737.txt`; netlist and table read from post-click page. | **PASS** |
| B4 (AC) | Playwright MCP UI: `/spice` → select AC → click Run → read plot/log → screenshot; final pass 2026-11-25 13:47:47 | Defaults; analysis `.ac`, netlist `.ac dec 10 1 1e6` / `.print ac vm(6) vm(2) vp(6) vp(2)` | Bode plot with frequency axis, gain magnitude and phase with units, values from real simulation; no analytical comparison. | `AC Bode plot from ngspice .ac`, 944×704; plot labels `Frequency (Hz)`, `Gain (dB)`, `Phase (°)`. Engine `ngspice OK — ac analysis completed (2026-11-25 13:47:47)`, saved `spice-ac-20261125-134747.txt` (61 frequency points / 122 raw rows). At 1 kHz the fresh log has `vm(6)=1.749958e-02`, `vm(2)=1.000000e-02` → gain `20·log10(vm6/vm2)=4.86 dB`, and `vp(6)=-3.13925e+00`, `vp(2)=0` → phase −3.139°. These are the values plotted, not a hard-coded chart. No `DC Analytical Results` on page; warning correctly states analytical comparison is DC-only. | `docs/captures/b4-ac-bode.png`; log `docs/captures/spice-ac-20261125-134747.txt` with the quoted 1 kHz rows; page snapshot with plot alt text. | **PASS** |
| B5 (Transient) | Playwright MCP UI: `/spice` → select `.tran` → click Run → read plot/log → screenshot; final pass 2026-11-25 13:47:51 | Source 10 mV peak, 1 kHz; netlist `.tran 5e-06 0.005`, `.print tran v(2) v(6)` | Vin/Vout over selected time with time/voltage values and phase inversion; screenshot and phase summary. | `Transient waveform from ngspice .tran`, 944×524; engine `ngspice OK — tran analysis completed (2026-11-25 13:47:51)`, saved `spice-tran-20261125-134751.txt` (1014 raw rows). Fresh log shows inversion: at t=3.14e-05 s, `v(2)=+1.960146e-03`, `v(6)=-3.47153e-03`; Vin and Vout are opposite sign in the sampled window (CE common-emitter inversion). Plot axes `Time (ms)` / `Voltage (V)`. No analytical comparison. | `docs/captures/b5-tran.png`; log `docs/captures/spice-tran-20261125-134751.txt` with the quoted row; page snapshot with plot alt text. | **PASS** |
| B6 (Change Source) | Playwright MCP UI: `/spice` → select `.tran` → fill amplitude/frequency → click Run → read netlist/log → screenshot; final pass 2026-11-25 13:47:53 | Source amplitude 0.010 V → 0.020 V; frequency 1000 Hz → 2000 Hz | Waveform must change according to new settings, not a hard-coded plot. | Fresh netlist `VIN 2 0 SIN(0 0.02 2000.0) AC 0.02` and `.tran 2.5e-06 0.0025` (tstop halved for 5 cycles at 2 kHz), versus B5's `SIN(0 0.01 1000.0)` / `.tran 5e-06 0.005`. Engine `ngspice OK — tran analysis completed (2026-11-25 13:47:53)`, saved `spice-tran-20261125-134753.txt` (1014 raw rows). Parsing the two fresh logs gives max \|vin\| = 0.0099996 V (B5) vs 0.0199992 V (B6) — the amplitude doubled; timestep and duration also changed, proving a new simulation rather than a cached plot. | `docs/captures/b6-tran-20mv-2khz.png`; logs `docs/captures/spice-tran-20261125-134751.txt` and `docs/captures/spice-tran-20261125-134753.txt`; netlist from post-click page. | **PASS** |
| B7 (Invalid / Fail) | Playwright MCP UI: `/spice` → fill RE=0 → click Run → read error → screenshot (re-run in final pass) | `RE = 0` | Proper error handling, no hang, no fake success; record exact message. | HTTP 400 BAD REQUEST (`POST /spice/run => [400]` in the final network log). Field error exactly `RE must be greater than 0.0`; rejected value `0` retained in RE field; 0 plots, 0 result tables, no `Engine status` and no saved-run artifact; `Simulation & Plots` still shows placeholder `Configure parameters and click Run SPICE Simulation.` and Engineering Results shows `Results will appear here after running SPICE simulation.` — no fake chart or success message. | `docs/captures/b7-re0-error.png` (re-captured); post-click snapshot with HTTP status 400 and error text; `browser_network_requests` showing the 400. | **PASS** |
| B8 (UI) | Playwright MCP `browser_resize` + real `.tran` run on `/spice` (and comparison on `/ce-lab`) after fix, desktop then phone, with screenshots | Desktop 1440×900 and phone 390×844; analysis `.tran` selected and a real ngspice run completed on each | Charts, units and buttons readable with no critical content clipped at both sizes. | **Desktop 1440:** PASS — `scrollWidth=1440`, `.dashboard` resolved to three columns `375.5px 482.8px 357.6px`, plot and netlist present, no element past the viewport. **Phone 390 on `/spice`: PASS** — after a real `.tran` run, `document.documentElement.scrollWidth=375` (≤390), `.dashboard` single column 346 px, `.input-card` 346 px, form/plot/netlist 309 px with right edge 342; `clipped=[]` for headings, buttons, unit chips, selects, inputs and images. `injectedFixPresent=false`, so no test-only CSS was involved. **Phone 390 on `/ce-lab`:** PASS — `scrollWidth=375`, `clipped=[]`. | Final pass re-captured `docs/captures/b8-desktop.png`, `docs/captures/b8-phone.png`, `docs/captures/b8-phone-ce-lab.png`; bounding-box metrics quoted above were read in that pass. Both desktop and phone layout runs were real ngspice `.tran` runs, saved as `docs/captures/spice-tran-20261125-135203.txt` (desktop) and `docs/captures/spice-tran-20261125-135205.txt` (phone). | **PASS** (desktop and phone `/spice`, plus phone `/ce-lab`) |

## Fix re-verification (after code changes)

| Item | Evidence |
|------|----------|
| B1 root cause | `index.html` rendered only the active mode's inputs, so `rb` did not exist and `toggleFields()` could not reveal it; a hidden `name="mode"` before the visible select made Flask read the stale `divider` value; on validation errors `_dashboard()` forced `mode="divider"`. |
| B1 fix | Ship all mode fields in the DOM (JS hides the inactive ones), remove the duplicate hidden `mode`, add `rb` to `FIELDS`, and preserve a valid submitted mode on validation errors. |
| B8 root cause | The responsive `.dashboard { grid-template-columns: 1fr }` resolves to min-content (~512 px) once the SPICE results are present, widening the grid tracks beyond the phone viewport. |
| B8 fix | Use `minmax(0, 1fr)` for the responsive `.dashboard` tracks (1100 px and 860 px rules), so grid items may shrink below their min-content size. |
| Automated checks | `.venv\Scripts\python -m pytest tests_spice/test_ui_fixes.py -v` → `4 passed`. Full suite → `5 failed, 103 passed`; the 5 failures are the same pre-existing `tests/test_routes.py` failures recorded before the fix (99 passed then; +4 new regression tests now). |
| Browser re-run | Playwright MCP on the restarted `:5001` server: A1–A5 via UI clicks in B1; desktop and 390 px `.tran` runs in B8. No direct POST and no injected CSS in the re-verification. |

## Status summary

| Case | Status |
|------|--------|
| B1 | PASS — UI mode switching works; A1–A5 all reachable and correct through the form, including the fixed-mode validation error. |
| B2 | PASS |
| B3 | PASS |
| B4 | PASS |
| B5 | PASS |
| B6 | PASS |
| B7 | PASS |
| B8 | PASS — `/spice` at 390 px has `scrollWidth=375` with no clipped inputs, button or plot; desktop and `/ce-lab` phone are also fine. |

## Notes on accuracy rules

- No ngspice failure was observed in B2–B6; every plot came with an `ngspice OK` status and a saved non-empty log, so no fake/stale success was accepted as PASS.
- B5/B6 phase inversion and waveform change were verified from saved ngspice stdout rows, not from source-code constants or mock plots.
- The AC/Transient pages correctly omit the `dc_bias.py` comparison and display a DC-only comparison warning.
- The only direct POSTs were in the original failing B1 run, used because the UI could not render Fixed/Emitter modes from a fresh page load. They were labeled as direct POST and not counted as UI-flow PASS. After the fix, A1–A5 were re-run entirely through UI clicks and are counted as UI-flow PASS.
- No mock data or hard-coded plots were used in the re-verification; B8's plot and netlist came from a real `.tran` ngspice run on the restarted server. B4–B6 plots in the final pass are backed by the fresh logs `spice-ac-20261125-134747.txt`, `spice-tran-20261125-134751.txt` and `spice-tran-20261125-134753.txt`.
- Honest unverified/not-run items: no instructor SPICE deck and no hardware measurement were available, so the simplified lab-local `.model QNPN NPN(IS=1e-14 BF=100.0)` is the only transistor model used; it is not an instructor-verified device card. B1 is analytical DC (no ngspice), and B7 is an intentional validation failure (no ngspice run by design). The 5 failing `tests/test_routes.py` cases are pre-existing legacy assertions in read-only `tests/` and were not modified or fixed in this task; the 4 new regression tests in `tests_spice/test_ui_fixes.py` pass.
