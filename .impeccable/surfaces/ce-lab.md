# .impeccable surfaces contract for CE Amplifier Lab

## THESIS

A teaching‑oriented CE Amplifier Lab page lets students explore common‑emitter voltage‑divider bias with real ngspice evidence, shown in a strict 3‑column dashboard. Every numeric result traces back to a parsed ngspice artifact; no fabricated values or mock data appear. The page preserves the existing analytical DC page (`/spice`) as the sole venue for dc_bias.py comparison, keeping provenance distinct.

## OWN‑WORLD

Within the ENG29 2121 course, the CE Amplifier Lab page sits alongside the existing DC Bias and SPICE Sim pages. It inherits the app’s visual language—Navy Blue, White, Light Gray, thin borders, rounded cards—and extends it with a 3‑column desktop layout (Layout A), tabbed DC/AC/Transient panels, and unit‑chipped result cards. The page must never mix analytical dc_bias.py values with SPICE output, and the simplified BJT model must be labelled as such.

## STORY

The page was conceived because students needed a dedicated space to edit CE divider parameters, run three ngspice analyses, and read engineering results with explicit units and provenance. Prior to this, they had to toggle between the DC Bias calculator and the generic SPICE Sim page, which did not present the same structured dashboard or guarantee that results came from a single calibrated netlist. The new page gives them a single, coherent workflow: adjust parameters, click Run Simulation on the desired tab, and read DC operating point, AC gain/phase/cutoff, or Transient peaks—all marked as SPICE (ngspice).

## FIRST VIEWPORT

On first opening `/ce-lab`, the student sees a form pre‑populated with default CE divider values (VCC=12 V, RC=2.2 kΩ, R1=100 kΩ, R2=22 kΩ, RE=1 kΩ, RL=10 kΩ, source amplitude 10 mV, frequency 1 kHz, beta=100, VBE=0.70 V). The left column shows the NPN Q1 schematic with component labels. The middle column defaults to the DC Analysis tab; the right column shows “—” placeholders for operating‑point values. A “Run Simulation” button is disabled until the form passes validation.

## FORM

seed: none (pinned)

“strict 3-column dashboard, layout A”

The form collects VCC, RC, R1, R2, RE, RL, source amplitude, frequency, beta, and VBE. Validation rejects zero source amplitude, negative resistances, beta < 1, VBE outside 0.1–2 V, frequency outside 1 Hz–1 MHz, and non‑numeric entries. Errors are keyed by field and rendered inline; a 400 response is returned without calling ngspice. The hidden `analysis` field defaults to `op` and is updated by tab selection.

## FINISH

“unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance”