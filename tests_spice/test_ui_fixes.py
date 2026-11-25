"""Regression tests for B1 bias-mode switching and B8 phone layout.

``tests/*`` is read-only per AGENTS.md, so these guards live in tests_spice.
The CSS guard is a structural tripwire only; real layout behavior is proven
by the Playwright MCP viewport checks recorded in docs/validation.md.
"""

import re
from pathlib import Path

import app as app_module

ROOT = Path(__file__).resolve().parents[1]


def _client():
    return app_module.create_app().test_client()


def test_index_renders_every_mode_field_so_js_can_switch_modes():
    """GET / must ship rb in the DOM; JS toggleFields only hides existing fields."""
    html = _client().get("/").get_data(as_text=True)

    for field in ("vcc", "rb", "r1", "r2", "rc", "re", "beta", "vbe"):
        assert f'name="{field}"' in html, f"GET / omitted mode field {field}"


def test_index_has_exactly_one_mode_control():
    """A hidden mode input before the select makes Flask read the stale value."""
    html = _client().get("/").get_data(as_text=True)

    assert len(re.findall(r'name="mode"', html)) == 1, (
        "index.html must have a single name=mode control (the visible select)"
    )


def test_fixed_mode_validation_error_keeps_fixed_mode_and_shows_rb_error():
    """An RB error must render in Fixed mode, not silently fall back to Divider."""
    html = _client().post(
        "/calculate",
        data={
            "mode": "fixed", "vcc": "12", "rb": "0",
            "rc": "2.2", "beta": "100", "vbe": "0.7",
        },
    ).get_data(as_text=True)

    assert "RB must be greater than 0" in html
    assert '<option value="fixed" selected>' in html


def test_responsive_dashboard_tracks_can_shrink_below_min_content():
    """Phone layout guard: 1fr resolves to min-content and overflows after a run."""
    css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

    narrow_rules = re.findall(
        r"@media \(max-width: (?:1100|860)px\)\s*\{\s*\.dashboard\s*\{\s*"
        r"grid-template-columns:\s*([^;]+);",
        css,
    )
    assert narrow_rules, "no responsive .dashboard grid rule found"
    for value in narrow_rules:
        assert "minmax(0, 1fr)" in value, (
            f"responsive grid track {value!r} cannot shrink below min-content"
        )
