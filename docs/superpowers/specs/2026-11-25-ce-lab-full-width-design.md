# CE Lab full-width layout — short design (2026-11-25)

## Intent

The user is viewing `/ce-lab` on a wide screen. The shared `.page` rule caps
content at `78rem` (1248 px), so on a 1920 px display the dashboard is centred
with large empty margins. They asked for the CE Lab page to expand to the full
screen width.

## Goals

- `/ce-lab` uses the full available viewport width instead of the 78rem cap.
- The three columns remain side by side above 1100 px and keep the existing
  1100 / 860 / 560 px degradation.
- No change to `/` or `/spice`, and no change to the simplified-model provenance
  or any engineering values.

## Non-goals / anti-goals

- No browser Fullscreen API, no hiding the site header or nav.
- No change to the analytical DC page or the SPICE Sim page.
- No new production code beyond CSS; no hard-coded or fabricated values.

## Constraints

- `static/style.css` already has a clearly delimited CE-lab section; additions
  stay inside it and do not alter shared tokens or rules.
- Existing tests assert `.ce-lab-grid`, `--ce-navy`, the three breakpoints,
  `prefers-reduced-motion`, and `ceFade`; those must remain intact.
- `bjt/bias.py`, `bjt/params.py`, `bjt/validate.py`, `bjt/steps.py`, and `tests/*`
  stay untouched; new assertions go in `tests_spice/test_ce_lab.py`.

## Chosen approach

Add one scoped CSS rule in the CE-lab section:

```css
body:has(.ce-lab-grid) .page { max-width: none; }
```

- `:has()` scopes the override to pages that actually contain the CE-lab grid.
  The existing `body` padding (1.25rem) is retained, so content still has a
  small gutter from the window edge.
- Alternative considered: add a `ce-lab-page` class to `<body>` in the shared
  `templates/base.html`. Rejected because it edits a shared template for a
  single-page layout change; `:has()` is supported by the Chromium used for
  browser acceptance.
- Alternative considered: remove the cap globally. Rejected because the user
  asked specifically about the CE Lab page.

## Verification left to the implementer

- Add a test in `tests_spice/test_ce_lab.py` asserting the scoped rule is
  present in `static/style.css`.
- Run the focused CE-lab tests and the unfiltered suite; only the five known
  `tests/test_routes.py` failures may remain.
- Browser check at 1920 px: `.page` width tracks the viewport, three columns
  stay on one row, no horizontal overflow. Re-check 1280 / 820 / 390 px so the
  breakpoints still work, and confirm `/` and `/spice` remain capped.
