"""Derivation rows for the calculation walk-through.

Rows are built from the inputs and the already-computed result; nothing is
re-solved here, so the walk-through can never disagree with the Q-point.
"""

from dataclasses import dataclass

from .bias import VCE_SAT, BiasResult, Region
from .format import fmt_i, fmt_num, fmt_r, fmt_v
from .params import BiasParams


@dataclass(frozen=True)
class Step:
    quantity: str
    formula: str
    substitution: str
    result: str


def _operand(x: float) -> str:
    """Print an operand with enough digits for the arithmetic to reconcile.

    The result column is rounded for display, so operands rounded to the same
    precision would not reproduce it (e.g. 12.8637 µA printed against a
    12.863 µA result). Seven significant digits keep the printed sum within
    half a unit of the last displayed digit while staying readable.
    """
    return f"{x:.7g}"


def _kohm(x: float) -> str:
    return _operand(x / 1000.0)


def _active_steps(p: BiasParams, r: BiasResult) -> list[Step]:
    r1, r2 = _kohm(p.r1), _kohm(p.r2)
    rc, re = _kohm(p.rc), _kohm(p.re)
    return [
        Step(
            "VBB",
            "VBB = VCC · R2 / (R1 + R2)",
            f"{_operand(p.vcc)} · {r2} / ({r1} + {r2})",
            fmt_v(p.vbb),
        ),
        Step(
            "RB",
            "RB = R1 ∥ R2",
            f"({r1} · {r2}) / ({r1} + {r2})",
            fmt_r(p.rbb),
        ),
        Step(
            "IB",
            "IB = (VBB − VBE) / (RB + (β+1) · RE)",
            f"({_operand(p.vbb)} − {_operand(p.vbe)}) / "
            f"({_operand(p.rbb / 1000.0)} + {_operand(p.beta + 1)} · {re})",
            fmt_i(r.ib),
        ),
        Step(
            "IC",
            "IC = β · IB",
            f"{_operand(p.beta)} · {_operand(r.ib * 1e6)} µA",
            fmt_i(r.ic),
        ),
        Step(
            "IE",
            "IE = (β+1) · IB",
            f"{_operand(p.beta + 1)} · {_operand(r.ib * 1e6)} µA",
            fmt_i(r.ie),
        ),
        Step(
            "VE",
            "VE = IE · RE",
            f"{_operand(r.ie * 1e3)} mA · {re} kΩ",
            fmt_v(r.ve),
        ),
        Step(
            "VB",
            "VB = VE + VBE",
            f"{_operand(r.ve)} + {_operand(p.vbe)}",
            fmt_v(r.vb),
        ),
        Step(
            "VC",
            "VC = VCC − IC · RC",
            f"{_operand(p.vcc)} − {_operand(r.ic * 1e3)} mA · {rc} kΩ",
            fmt_v(r.vc),
        ),
        Step(
            "VCE",
            "VCE = VCC − IC · RC − IE · RE",
            f"{_operand(p.vcc)} − {_operand(r.ic * p.rc)} − {_operand(r.ie * p.re)}",
            fmt_v(r.vce),
        ),
    ]


def _saturation_steps(p: BiasParams, r: BiasResult) -> list[Step]:
    rc, re = _kohm(p.rc), _kohm(p.re)
    return [
        Step(
            "IC",
            "IC = (VCC − VCE,sat) / (RC + RE · (β+1)/β)",
            f"({_operand(p.vcc)} − {VCE_SAT:g}) / "
            f"({rc} + {re} · {_operand(p.beta + 1)}/{_operand(p.beta)})",
            fmt_i(r.ic),
        ),
        Step(
            "IB",
            "IB = IC / β",
            f"{_operand(r.ic * 1e3)} mA / {_operand(p.beta)}",
            fmt_i(r.ib),
        ),
        Step(
            "IE",
            "IE = IC · (β+1)/β",
            f"{_operand(r.ic * 1e3)} mA · {_operand(p.beta + 1)}/{_operand(p.beta)}",
            fmt_i(r.ie),
        ),
        Step(
            "VE",
            "VE = IE · RE",
            f"{_operand(r.ie * 1e3)} mA · {re} kΩ",
            fmt_v(r.ve),
        ),
    ]


def _cutoff_steps(p: BiasParams, r: BiasResult) -> list[Step]:
    r1, r2 = _kohm(p.r1), _kohm(p.r2)
    return [
        Step(
            "VBB",
            "VBB = VCC · R2 / (R1 + R2)",
            f"{_operand(p.vcc)} · {r2} / ({r1} + {r2})",
            fmt_v(p.vbb),
        ),
        Step(
            "IB",
            "VBB ≤ VBE ⇒ IB = 0",
            f"{p.vbb:.4f} ≤ {fmt_num(p.vbe)}",
            fmt_i(r.ib),
        ),
    ]


def steps_for(p: BiasParams, result: BiasResult) -> list[Step]:
    """Derivation rows appropriate to the operating region."""
    if result.region is Region.CUTOFF:
        return _cutoff_steps(p, result)
    if result.region is Region.SATURATION:
        return _saturation_steps(p, result)
    return _active_steps(p, result)
