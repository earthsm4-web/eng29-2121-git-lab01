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
