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

## Run it

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

Then open <http://127.0.0.1:5000/>.

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
app.py              Flask routes only
bjt/params.py       validated SI-unit inputs
bjt/validate.py     form strings -> params or field errors
bjt/bias.py         exact and approximate solvers, region classification
bjt/format.py       V / mA / µA display formatting
bjt/steps.py        walk-through derivation rows
templates/base.html dashboard shell with header
templates/index.html single-page dashboard (replaces form + result pages)
templates/_schematic.html inline-SVG circuit with computed node voltages
templates/_steps.html   How this was calculated card
templates/_comparison.html Approximate method check card
static/style.css           single stylesheet
tests/              pytest suite
```

`bjt/` never imports Flask, so the engineering logic is tested without a web
server.

## Scope

DC only. No AC analysis, transient response, load lines, FETs, or circuit
editor — this is the small lab deliverable.
