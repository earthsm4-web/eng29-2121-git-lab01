"""Parse submitted form strings into validated SI-unit parameters."""

import math
from collections.abc import Mapping

from .params import BiasParams

MODE_FIELDS = {
    "fixed": ("vcc", "rb", "rc", "beta", "vbe"),
    "emitter": ("vcc", "rb", "re", "rc", "beta", "vbe"),
    "divider": ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"),
}

OHM_FIELDS = ("r1", "r2", "rc", "re", "rb")

DISPLAY = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "rb": "RB",
    "beta": "beta",
    "vbe": "VBE",
}


def parse_form(
    form: Mapping[str, str],
    mode: str = "divider",
) -> tuple[BiasParams | None, dict[str, str]]:
    """Return (params, {}) for valid input, or (None, errors) otherwise.

    ``mode`` selects which input fields are required and how they are named.
    Resistances are converted from kΩ (form unit) to Ω (SI unit) once, here.
    """
    if mode not in MODE_FIELDS:
        mode = "divider"

    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    for field in MODE_FIELDS[mode]:
        raw = (form.get(field) or "").strip()
        name = DISPLAY[field]
        if not raw:
            errors[field] = f"{name} is required"
            continue
        try:
            value = float(raw)
        except ValueError:
            errors[field] = f"{name} must be a number"
            continue
        if not math.isfinite(value):
            errors[field] = f"{name} must be a number"
            continue
        values[field] = value

    if "vcc" in values and values["vcc"] <= 0:
        errors["vcc"] = "VCC must be greater than 0"

    for field in OHM_FIELDS:
        if field in values and values[field] <= 0:
            errors[field] = f"{DISPLAY[field]} must be greater than 0"

    if "vbe" in values:
        if values["vbe"] <= 0:
            errors["vbe"] = "VBE must be greater than 0"
        elif "vcc" in values and values["vbe"] >= values["vcc"]:
            errors["vbe"] = "VBE must be less than VCC"

    if "beta" in values and values["beta"] <= 1:
        errors["beta"] = "beta must be greater than 1"

    if errors:
        return None, errors

    for field in OHM_FIELDS:
        if field in values:
            values[field] *= 1000.0

    return BiasParams(mode=mode, **values), {}
