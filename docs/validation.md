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
| 1280 px | `410.703px 391.141px 391.156px` | 411 / 391 / 391 px, all on one row | none (`scrollWidth` 1265) |
| 820 px | `776.219px` | 776 px, stacked | none |
| 390 px | stacked single column | 346 px | none |

Screenshots: `docs/captures/ce-lab-1280.png`, `docs/captures/ce-lab-820.png`,
`docs/captures/ce-lab-390.png`.

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
