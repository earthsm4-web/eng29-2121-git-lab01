# BJT Common-Emitter DC Bias Calculator

A small Flask app for the ENG29 2121 lab. It solves the DC operating point of
a common-emitter amplifier with voltage-divider bias, reports the region the
transistor is in, and shows the same operating point computed a second,
independent way so the numbers can be trusted.

## Inputs

Resistances are entered in **kΩ**, voltages in **V**.

| Input | Meaning |
|-------|---------|
| `VCC` | supply voltage |
| `R1` | divider resistor from VCC to base |
| `R2` | divider resistor from base to ground |
| `RC` | collector resistor |
| `RE` | emitter resistor |
| `beta` | transistor current gain |
| `VBE` | forward base-emitter drop |

## Outputs

`IB`, `IC`, `IE`, `VBE`, `VCE`, `VB`, `VC`, `VE`, plus a region label:

- **Active** — the transistor amplifies; the comparison table is enabled.
- **Saturation** — `VCE` came out at or below the assumed `VCE_SAT = 0.2 V`.
  The active equations do not apply, so the app re-solves with `VCE` pinned
  at 0.2 V and warns about it.
- **Cutoff** — the divider voltage `VBB` is at or below `VBE`; no collector
  current flows.

## Two methods, one answer

The **exact** path solves base current with the emitter resistance reflected
into the base:

```
VBB = VCC * R2 / (R1 + R2)      RB = R1 * R2 / (R1 + R2)
IB  = (VBB - VBE) / (RB + (beta + 1) * RE)
IC  = beta * IB                 IE = (beta + 1) * IB
VCE = VCC - IC * RC - IE * RE
```

The **approximate** path assumes the divider is stiff: `VB ≈ VBB`, so base
current is ignored and `IE ≈ (VBB - VBE) / RE`.

The app shows both and the signed percent difference. The rule of thumb that
justifies the approximation is `beta * RE >= 10 * R2`; the app reports whether
the divider meets it.

### Worked example

`VCC = 12 V, R1 = 47 kΩ, R2 = 10 kΩ, RC = 4.7 kΩ, RE = 1 kΩ, beta = 100,
VBE = 0.7 V`

| Quantity | Exact | Approximate |
|----------|-------|-------------|
| `IC` | 1.2863 mA | 1.4053 mA |
| `VCE` | 4.6550 V | 3.9900 V |
| `VB` | 1.9992 V | 2.1053 V |

`beta * RE = 100 kΩ` and `10 * R2 = 100 kΩ`, so the divider just meets the
stiffness rule — and `IC` is still off by about 9%. That gap is the lesson.

## CE Amplifier Lab (`/ce-lab`)

หน้าใหม่สำหรับจำลองวงจร CE Voltage Divider ด้วย **ngspice จริงเท่านั้น**
(A new page that simulates the CE voltage-divider amplifier with **real ngspice
only**). Values in the plots and result tables are parsed from `.op`, `.ac`, and
`.tran` output — there is no mock data and no `dc_bias.py` comparison on this
page.

### Inputs and units

| Input | Unit | Meaning |
|-------|------|---------|
| `VCC` | V | supply voltage |
| `RC`, `R1`, `R2`, `RE`, `RL` | kΩ | collector / divider / emitter / load resistors |
| `beta` | – | forward current gain (`BF` in the SPICE model) |
| `VBE` | V | hand-analysis reference drop; the solver uses the nonlinear model |
| `Source amplitude` | V | sinusoidal input amplitude, `> 0` and `≤ 1 V` |
| `Source frequency` | Hz | input frequency, `1 Hz`–`1 MHz` |

Resistances are entered in kΩ and converted to Ω only after validation.
Amplitude `0` is rejected because the AC ratio `vm(6)/vm(2)` would be undefined.

### Netlist node definitions

| Node | Meaning |
|------|---------|
| `V(2)` | `Vin` before `CIN` (source terminal) |
| `V(6)` | `Vout` after `COUT`, across `RL` |
| `V(4)` | collector of `Q1` |
| `V(5)` | emitter of `Q1` |
| `VCE` | `V(4) − V(5)` |
| `IC` | collector current, positive **into** node 4 (collector → emitter) |

`VIN 2 0 SIN(0 <amplitude> <frequency>) AC <amplitude>` sources the circuit;
`CIN` and `COUT` are 10 µF coupling capacitors.

### ⚠️ Simplified transistor model

The netlist uses:

```
.model QNPN NPN(IS=1e-14 BF=<beta>)
```

This is a **simplified, lab-local model — not instructor-verified**. The `VBE`
field is a hand-analysis reference; ngspice uses the nonlinear `IS`/`BF` model
instead, so DC numbers differ slightly from `dc_bias.py`. Do not treat this
model as a validated device card.

### Using the page

Left column: schematic and parameters. Middle column: DC / AC / Transient tabs
— choose a tab, then click **Run Simulation** (tabs never auto-submit; without
JavaScript the DC tab is the default). Right column: engineering results with
units V, mA, µA, Hz, dB, °, and ms. AC gain/phase are read from the closest real
frequency bin; cutoffs use −3 dB interpolation and show `—` / a note when no
crossing exists. Transient values use only samples after the first two source
cycles. Engine, metric, and plot failures are labelled separately so a post-run
bug is never reported as an ngspice failure.

## Install and verify ngspice 47 (Lab 4)

The SPICE adapter in `bjt/spice_engine.py` looks for
`C:\tools\ngspice-47\Spice64\bin\ngspice_con.exe` first. If that exact file is
missing, it falls back to `ngspice` or `ngspice_con` on `PATH`. If neither is
found, the app reports an `ngspice binary not found` error instead of showing
simulation results.

1. Download the Windows 64-bit ngspice 47 build from the official
   [ngspice download page](https://ngspice.sourceforge.io/download.html).
2. Extract/install it, for example to `C:\tools\ngspice-47\Spice64\`, so the
   executable is at `C:\tools\ngspice-47\Spice64\bin\ngspice_con.exe`.
   Alternatively, add the folder containing `ngspice_con.exe` to your `PATH`.
3. Verify the installed binary in PowerShell:

   ```powershell
   & 'C:\tools\ngspice-47\Spice64\bin\ngspice_con.exe' -v
   ```

   If it is on `PATH`, this also works:

   ```powershell
   ngspice_con.exe -v
   ```

   The banner should start with `** ngspice-47 : Circuit level simulation
   program`. The validation record quotes the full banner, including the
   `Aug 11 2026` creation date for the binary used in this lab.

## Run it

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

Then open <http://127.0.0.1:5000/> for the DC bias calculator or
<http://127.0.0.1:5000/ce-lab> for the CE Amplifier Lab.

With auto-reload instead of the plain server:

```powershell
.\.venv\Scripts\python -m flask --app app run --debug
```

## Test it

```powershell
.\.venv\Scripts\python -m pytest
```

`pytest` is listed in `requirements.txt`, so the install step above is enough.
The suite uses pytest fixtures and `pytest.mark.parametrize`, so
`python -m unittest discover -s tests` cannot collect it — use `pytest`.

## Layout

```
app.py                    Flask routes + SPICE dispatch
bjt/params.py             validated SI-unit inputs
bjt/validate.py           form strings -> params or field errors
bjt/bias.py               exact and approximate solvers, region classification
bjt/format.py             V / mA / µA display formatting
bjt/steps.py              walk-through derivation rows
bjt/spice_engine.py       ngspice adapter: .op / .ac / .tran
bjt/spice_metrics.py      gain/phase/cutoff/transient metrics from SPICE data
bjt/spice_plot.py         matplotlib plots from real SPICE data
templates/base.html       dashboard shell with header
templates/index.html      single-page DC dashboard with inline JS (replaces form + result pages)
templates/_schematic.html inline-SVG circuit with computed node voltages
templates/_steps.html     How this was calculated card
templates/_comparison.html Approximate method check card
templates/spice.html      SPICE Sim page (real ngspice output)
templates/ce_lab.html     CE Amplifier Lab 3-column page
templates/_ce_circuit.html inline-SVG CE circuit (labels only)
static/style.css          shared stylesheet + scoped CE-lab rules
static/ce_lab.js          CE-lab ARIA tab controller
tests/                    original pytest suite (unmodified)
tests_spice/              SPICE + CE-lab pytest suite
```

`bjt/` never imports Flask, so the engineering logic is tested without a web
server.

## Scope

The DC bias calculator (`/`) is analytical only. The SPICE Sim page (`/spice`)
and CE Amplifier Lab (`/ce-lab`) run real ngspice `.op`, `.ac`, and `.tran`
analyses. There is no load-line tool, FET support, or circuit editor — this is
the small lab deliverable.
