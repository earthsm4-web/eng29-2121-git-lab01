# CE Lab Full-Width Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/ce-lab` use the full browser width on wide screens while `/` and `/spice` keep their existing 78rem cap.

**Architecture:** A single CSS override scoped with `body:has(.ce-lab-grid)` removes the shared `.page` max-width only on the CE Lab page. Existing CE-lab grid and breakpoint rules remain untouched, so column degradation at 1100/860/560 px still works. A test pins both the override and the retained cap, and browser checks confirm the rendered widths.

**Tech Stack:** Flask/Jinja templates, plain CSS (`:has()`), pytest, in-app Chromium browser for acceptance.

**Spec:** `docs/superpowers/specs/2026-11-25-ce-lab-full-width-design.md`

## Global Constraints

- Additions stay inside the delimited CE-lab section of `static/style.css`; do not alter shared tokens or rules.
- Keep `.ce-lab-grid` 3-column layout above 1100 px and keep `@media (max-width: 1100px)`, `@media (max-width: 860px)`, `@media (max-width: 560px)`, `prefers-reduced-motion`, and `ceFade` intact.
- Do not change `/`, `/spice`, `templates/index.html`, `templates/spice.html`, `templates/base.html`, `app.py`, or any `bjt/*` file.
- `bjt/bias.py`, `bjt/params.py`, `bjt/validate.py`, `bjt/steps.py`, and `tests/*` are read-only; new assertions go only in `tests_spice/test_ce_lab.py`.
- No mock, random, static, or hard-coded engineering values; no `dc_bias.py` comparison or `DC Analytical` badge on `/ce-lab`.
- Python 3.13.2 / pytest 9.2.0 in `.venv`; verify with `.venv\Scripts\python -m pytest -q`.
- Baseline: `5 failed, 98 passed in 2.00s`; only the five pre-existing `tests/test_routes.py` assertion failures may remain.
- Root-level untracked runner scripts (`run_*`, `check_bounds.py`, `verify_*.py`), `test_output.txt`, `.playwright-mcp/`, and older 2026-11-24 docs are unrelated — do not add, edit, or delete them.

## Review Focus

- **Wide desktop (1920 px):** the user's actual complaint — `.page` must track the viewport instead of stopping at 1248 px. Pinned by the browser check in Task 1 Step 5.
- **Existing mid/narrow widths (1280/820/390 px):** widening must not break the 3-column layout or the stacked fallbacks. Pinned by Task 1 Step 5.
- **Other pages:** the override must not leak — `/` and `/spice` must still lack `.ce-lab-grid` and keep the shared cap. Pinned by the route assertions in Task 1 Step 1.
- **Accidental global cap removal:** the original `.page { max-width: 78rem }` rule must survive. Pinned by the regex assertion in Task 1 Step 1.
- **Horizontal overflow:** full width must not introduce a horizontal scrollbar at any checked width. Pinned by `document.documentElement.scrollWidth` in Task 1 Step 5.

---

### Task 1: Scoped full-width override for `/ce-lab`

**Files:**
- Modify: `tests_spice/test_ce_lab.py` (append one test at EOF)
- Modify: `static/style.css` (inside the Task 5 CE-lab section, near `.ce-lab-grid`)

**Interfaces:**
- Consumes: `.page` rule at `static/style.css:33-36` (`max-width: 78rem`), `.ce-lab-grid` at `static/style.css:652`, module-level `app_module` and `re` already imported in `tests_spice/test_ce_lab.py`.
- Produces: rendered `/ce-lab` with no 78rem cap; no other page or interface changes.

- [ ] **Step 1: Write the failing test**

Append to `tests_spice/test_ce_lab.py`:

```python
def test_ce_lab_full_width_override_is_scoped():
    """Only the CE-lab page drops the shared 78rem width cap."""
    from pathlib import Path

    css_path = Path(__file__).resolve().parents[1] / "static" / "style.css"
    css = css_path.read_text(encoding="utf-8")

    assert "body:has(.ce-lab-grid) .page" in css
    assert re.search(
        r"body:has\(\.ce-lab-grid\) \.page\s*\{\s*max-width:\s*none", css
    ), "CE-lab width override must set max-width: none"
    assert re.search(r"\.page\s*\{\s*max-width:\s*78rem", css), (
        "shared .page cap must remain for other pages"
    )

    client = app_module.create_app().test_client()
    for path in ("/", "/spice"):
        assert "ce-lab-grid" not in client.get(path).data.decode(), (
            f"{path} must not contain the CE-lab grid"
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k full_width -v`
Expected: FAIL on `assert "body:has(.ce-lab-grid) .page" in css`.

- [ ] **Step 3: Implement the CSS override**

In `static/style.css`, immediately before the `.ce-lab-grid` rule at line 652, add:

```css
/* Full-width dashboard: only pages containing the CE-lab grid opt out of
   the shared .page cap (the user views this page on a wide monitor). */
body:has(.ce-lab-grid) .page { max-width: none; }
```

Keep the body padding and every existing CE-lab rule unchanged.

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv\Scripts\python -m pytest tests_spice/test_ce_lab.py -k full_width -v`
Expected: PASS.

- [ ] **Step 5: Browser acceptance at four widths**

Start/restart Flask with `.venv\Scripts\python -m flask --app app run --debug --no-reload --port 5001` if needed, then open `http://127.0.0.1:5001/ce-lab`. For each width in 1920, 1280, 820, 390 px, evaluate in the page:

```js
() => {
  const page = document.querySelector('.page');
  const cols = Array.from(document.querySelectorAll('.ce-lab-column'))
    .map(c => Math.round(c.getBoundingClientRect().width));
  return {
    vw: innerWidth,
    pageWidth: Math.round(page.getBoundingClientRect().width),
    cols,
    scrollW: document.documentElement.scrollWidth
  };
}
```

Expected: `pageWidth` is approximately `vw - 40` at every width (no 1248 px cap at 1920); `cols.length === 3` and all on one row at 1920/1280, stacked at 820/390; `scrollW <= vw` at every width. Then open `/` and `/spice` at 1920 px and confirm `.page` width is still capped at 1248 px.

- [ ] **Step 6: Run the full suite once**

Run: `.venv\Scripts\python -m pytest -q`
Expected: `5 failed, 99 passed` (or higher pass count) with only the five pre-existing `tests/test_routes.py` assertion failures. Do not filter, ignore, or invent collection errors.

- [ ] **Step 7: Commit**

```bash
git add tests_spice/test_ce_lab.py static/style.css
git commit -m "feat(lab4): let CE lab page use full viewport width"
```

Verify with `git log --oneline -1` and `git status -sb` from the repo directory `C:\Users\ASUS\Documents\Default Project\eng29-2121-git-lab01`.
