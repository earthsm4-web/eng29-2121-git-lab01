# BJT Common-Emitter DC Bias Calculator — Design

**Course:** ENG29 2121 · **Date:** 2026-11-10 · **Status:** awaiting approval

## Intent

A small Flask web app that computes the DC operating point of a
common-emitter (voltage-divider) bias circuit from seven inputs, tells the
student which region the transistor is in, and shows the same operating
point computed a second, independent way so the result can be trusted.

The lab's teaching point is *why the approximate divider method is allowed*:
the app computes both paths and shows how far apart they are.

## Goals

- One form: `VCC, R1, R2, RC, RE, beta, VBE` → full Q-point with units.
- Region classification: active / saturation / cutoff, with a warning whose
  wording says what is wrong with the numbers when the active equations fail.
- Side-by-side comparison: exact Thevenin vs approximate stiff-divider, with
  percent differences and the validity verdict `beta * RE >= 10 * R2`.
- Engineering logic importable and testable with no Flask involved.
- Runs on `localhost` with `flask run`; one `pytest` command runs the suite.

## Non-goals

AC analysis, small-signal parameters, transient, frequency response, load
line plots, FET/MOSFET, circuit editor or schematic capture, database, auth,
deployment, JS framework.

## Anti-goals

- Reporting a number without stating its region.
- Presenting the approximate result as if it were exact.
- A validation failure surfacing as HTTP 500 or a bare traceback.
- Duplicating the bias equation inside a test (a test must carry
  hand-computed literals, not a re-implementation of the code it checks).

## Constraints

- Python 3.12 (installed), Flask + pytest only; no other runtime dependency.
- Server-rendered Jinja templates, one stylesheet, no client-side JS.
- Inputs in V and kΩ; internal computation in SI (Ω, A); display in V and mA.
- UI text in English (engineering labels); can be switched to Thai on request.
- Single git commit-able deliverable today.

## Approaches considered

| # | Approach | Verdict |
|---|---|---|
| A | Exact Thevenin vs approximate stiff-divider, both implemented | **chosen** — teaches the lab's actual point, no new dependency |
| B | Exact vs iterative Ebers–Moll nodal solve | rejected — beyond 2121, doubles the code and test surface |
| C | Compare against user-entered or SPICE reference | rejected — turns a calculator into a checker; ngspice not installed |

## The engineering

Thevenin equivalent of the divider (`R1` from VCC to base, `R2` base to ground):

```
VBB = VCC * R2 / (R1 + R2)          RB = R1 * R2 / (R1 + R2)
```

**Exact path** — solves base current with the emitter reflection:

```
IB  = (VBB - VBE) / (RB + (beta + 1) * RE)
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * RE
VB  = VE + VBE
VC  = VCC - IC * RC
VCE = VCC - IC * RC - IE * RE
```

**Approximate path** — assumes the divider is stiff, so `VB ≈ VBB` and base
current is ignored:

```
IE  ~= (VBB - VBE) / RE
IC  ~= IE
IB  ~= IC / beta
VCE ~= VCC - IE * (RC + RE)
```

**Validity rule:** `beta * RE >= 10 * R2` (textbook stiffness rule of thumb;
the constant `10` and use of `R2` are named in code as `STIFFNESS_FACTOR`
and documented, so the choice is visible rather than buried).

**Comparison:** IC, IE, VCE, VB — each with `%diff = |exact - approx| /
|exact| * 100`. Rendered only when both paths are valid (i.e. active region
and `VBB > VBE`).

## Region logic

`VCE_SAT = 0.2 V` is a module constant; it is not an input field.

| Condition | Region | What is reported |
|---|---|---|
| `VBB <= VBE` | **cutoff** | `IB = IC = IE = 0`, `VCE = VCC`, `VC = VCC`, `VE = 0`; warn the divider cannot forward-bias the junction |
| active solution has `VCE < VCE_SAT` | **saturation** | active-mode numbers still shown but marked invalid, plus a re-solve with `VCE = VCE_SAT`: `IC = (VCC - VCE_SAT) / (RC + RE * (beta + 1) / beta)`; warn that the active equations do not apply |
| otherwise | **active** | exact Q-point, comparison table enabled |

Validation runs first and rejects impossible inputs before any solving:
`VCC > 0`, `R1,R2,RC,RE > 0`, `beta > 1`, `0 < VBE < VCC`, all fields numeric.
`RE = 0` is rejected because the approximate path divides by it.

## Components

```
app.py                  Flask routes only
bjt/__init__.py
bjt/params.py           BiasParams dataclass (SI units, validated)
bjt/validate.py         form strings -> BiasParams | field errors
bjt/bias.py             solve_exact, solve_approximate, classify_region, compare
bjt/format.py           SI -> V/mA/microA strings, 3-decimal engineering format
templates/base.html     layout + form-error block
templates/index.html    the form, pre-filled defaults, error rendering
templates/result.html   Q-point, region banner, comparison table
static/style.css        single stylesheet
tests/test_validate.py  parsing and each validation rejection
tests/test_bias.py      hand-computed golden vectors (active, cutoff, saturation)
tests/test_routes.py    GET / 200; POST valid 200 + values; POST invalid 400 + messages
requirements.txt, README.md, .gitignore
```

Routes: `GET /` renders the form with lab defaults
(`12, 47, 10, 4.7, 1, 100, 0.7`); `POST /calculate` re-renders the form with
field errors at HTTP 400, or renders the result page at HTTP 200.

## Golden values for tests

Hand-computed, to be used as literals in `tests/test_bias.py`
(tolerance `rel=1e-6`):

Active — `VCC=12, R1=47k, R2=10k, RC=4.7k, RE=1k, beta=100, VBE=0.7`:

| | exact | approximate |
|---|---|---|
| VBB | 2.10526 V | — |
| RB | 8.24561 kΩ | — |
| IB | 12.864 µA | ~13.95 µA |
| IC | 1.28644 mA | 1.40526 mA |
| VCE | 4.65456 V | 3.99053 V |

Validity: `100 * 1k = 100k >= 10 * 10k = 100k` → **stiff (borderline)**;
IC differs by ~9.2%, which is exactly the lesson.

Cutoff — `VCC=12, R1=100k, R2=1k` → `VBB = 0.1188 V < 0.7` → IC = 0, VCE = 12.
Saturation — `VCC=12, R1=47k, R2=10k, RC=10k, RE=1k` → active math gives
VCE < 0 → saturation; `IC_sat = (12 - 0.2) / (10k + 1k * 1.01) = 1.0718 mA`.

## Left to the builder

Exact visual styling, wording of the warning sentences, number of decimal
places beyond 3, and whether the comparison table also shows `%diff` as a
bar. All are cosmetic and settle without changing what gets built.

## Delivery notes (not part of the app design)

Blockers found during recon, to be handled in Task 0 of the plan:
git is installed but not on `PATH`; `git config user.name/email` are unset;
no GitHub CLI, so the remote must be created on the web or supplied as a URL
with credentials.
