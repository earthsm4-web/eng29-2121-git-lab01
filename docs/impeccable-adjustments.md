# Impeccable adjustments — CE Amplifier Lab

## Audit outcome

- Setup: `.impeccable/config.json` was corrected to `{"buildPath": "code"}` and the doctor recheck reported no findings (`ca2e7c2`).
- Layout decision: **A — strict 3 columns** for `/ce-lab`. The 1440 px and 1280 px captures show three columns on one row; 820 px and 390 px show the stacked fallback. No "before" screenshot was captured, so none is claimed here.
- A scoped full-width override was added for pages containing `.ce-lab-grid`; `/` and `/spice` keep the shared 78rem cap. The stale-build audit found no production defect.
- The one post-change detector run returned `[]` findings. It could not resolve the Jinja `url_for` stylesheet link, so color/custom-property checks were incomplete; no finding was invented to fill that gap.
- This file records the audited state only; no new visual change was made in this step.

## Existing captures (after-state only)

| Viewport | Capture | Observed |
|----------|---------|----------|
| 1440 px | `docs/captures/ce-lab-1440.png` | Three columns on one row: about 466 / 444 / 444 px; no horizontal overflow. |
| 1280 px | `docs/captures/ce-lab-1280.png` | Three columns on one row: about 411 / 391 / 391 px; no horizontal overflow. |
| 820 px | `docs/captures/ce-lab-820.png` | Single stacked column of about 776 px; no horizontal overflow. |
| 390 px | `docs/captures/ce-lab-390.png` | Single stacked column of about 346 px; `clipped=[]`; no horizontal overflow. |

The numeric observations above are the recorded bounding-box values from `docs/validation.md`. Every screenshot is an existing after-state capture; none was generated or edited for this document.
