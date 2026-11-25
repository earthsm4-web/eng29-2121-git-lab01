# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Students in ENG29 2121 who are learning common-emitter BJT amplifier analysis. They arrive with component values and want to see whether the circuit biases correctly and how it responds in DC, AC, and time domain. (Inferred from the course brief and existing app; confirm during design-doc review.)

## Product Purpose

Provide a teaching tool that turns entered CE amplifier parameters into real circuit-analysis evidence. Success means a student can change VCC, resistors, source amplitude, or frequency and immediately see trustworthy operating-point, frequency-response, and waveform results with clear units and provenance. (Inferred from the request.)

## Positioning

The tool separates analytical DC reference values from SPICE results and exposes the actual netlist, engine status, and run log. It does not invent data: every numeric result shown as ngspice output comes from a real ngspice run. (Confirmed by AGENTS.md and user request.)

## Operating Context

Local Flask app on the student's or instructor's machine. Existing routes `/` and `/spice` remain available. ngspice 47 is installed locally and is invoked in batch mode. The new page is used beside the existing DC Bias and SPICE Sim pages.

## Capabilities and Constraints

- New page `CE Amplifier Lab` with a strict 3-column desktop dashboard and DC / AC / Transient tabs.
- Reuse Flask, Jinja templates, Matplotlib plotting, CSS design tokens, and the existing `bjt/spice_engine.py` adapter.
- Real `.op`, `.ac`, and `.tran` runs only; no mock data, static decorative plots, or fabricated gain/cutoff values.
- Do not modify `bjt/bias.py`, `bjt/params.py`, `bjt/validate.py`, `bjt/steps.py`, or files under `tests/`.
- Do not delete or alter the existing `/` and `/spice` behavior.
- User explicitly approved using the existing simplified BJT model line already in the code for this build; it must be labelled as simplified, not instructor-verified.
- The attached reference image is present in session upload storage but cannot be read by this model; the detailed written brief is the design source of truth for this session.
- Open decision: none blocking after design-doc approval.

## Brand Commitments

Course identity: `CE Amplifier Lab`, ENG29 2121. Visual language inherited from the existing app: Navy Blue, White, Light Gray, thin borders, rounded cards, tabular numerals. Thai/English mixed technical labels are acceptable.

## Evidence on Hand

- Existing repo: `app.py`, `templates/base.html`, `templates/spice.html`, `templates/index.html`, `static/style.css`, `bjt/spice_engine.py`, `bjt/spice_plot.py`, `tests/`.
- AGENTS.md provenance and no-mock rules.
- Prior approved design/plan documents under `docs/superpowers/`.
- Attached reference image path: `C:\Users\ASUS\AppData\Local\Temp\opencode\uploads\29cfa007-789d-4961-9b21-cddf3747a464\image.png` (not visually readable in this session).
- Existing simplified model: `.model QNPN NPN(IS=1e-14 BF=100.0)`.

## Product Principles

1. Real solver output beats plausible-looking output.
2. Preserve the working lab app; extend it with a separate page.
3. Make provenance visible at every result table and plot.
4. Show units, assumptions, and failure states instead of hiding them.
5. Keep calculation logic out of templates.

## Accessibility & Inclusion

Inputs and tabs must be keyboard reachable with visible focus. Plots need text alternatives and numeric result tables. Document language may remain mixed Thai/English because the course already uses both.
