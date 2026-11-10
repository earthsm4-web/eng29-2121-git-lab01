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


def _kohm(x: float) -> str:
    return fmt_num(x / 1000.0)


def _active_steps(p: BiasParams, r: BiasResult) -> list[Step]:
    r1, r2 = _kohm(p.r1), _kohm(p.r2)
    rc, re = _kohm(p.rc), _kohm(p.re)
    return [
        Step(
            "VBB",
            "VBB = VCC · R2 / (R1 + R2)",
            f"{fmt_num(p.vcc)} · {r2} / ({r1} + {r2})",
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
            f"({p.vbb:.4f} − {fmt_num(p.vbe)}) / "
            f"({p.rbb / 1000.0:.4f} + {fmt_num(p.beta + 1)} · {re})",
            fmt_i(r.ib),
        ),
        Step(
            "IC",
            "IC = β · IB",
            f"{fmt_num(p.beta)} · {r.ib * 1e6:.3f} µA",
            fmt_i(r.ic),
        ),
        Step(
            "IE",
            "IE = (β+1) · IB",
            f"{fmt_num(p.beta + 1)} · {r.ib * 1e6:.3f} µA",
            fmt_i(r.ie),
        ),
        Step(
            "VE",
            "VE = IE · RE",
            f"{r.ie * 1e3:.4f} mA · {re} kΩ",
            fmt_v(r.ve),
        ),
        Step(
            "VB",
            "VB = VE + VBE",
            f"{r.ve:.4f} + {fmt_num(p.vbe)}",
            fmt_v(r.vb),
        ),
        Step(
            "VC",
            "VC = VCC − IC · RC",
            f"{fmt_num(p.vcc)} − {r.ic * 1e3:.4f} mA · {rc} kΩ",
            fmt_v(r.vc),
        ),
        Step(
            "VCE",
            "VCE = VCC − IC · RC − IE · RE",
            f"{fmt_num(p.vcc)} − {r.ic * p.rc:.4f} − {r.ie * p.re:.4f}",
            fmt_v(r.vce),
        ),
    ]


def _saturation_steps(p: BiasParams, r: BiasResult) -> list[Step]:
    rc, re = _kohm(p.rc), _kohm(p.re)
    return [
        Step(
            "IC",
            "IC = (VCC − VCE,sat) / (RC + RE · (β+1)/β)",
            f"({fmt_num(p.vcc)} − {VCE_SAT:g}) / "
            f"({rc} + {re} · {fmt_num(p.beta + 1)}/{fmt_num(p.beta)})",
            fmt_i(r.ic),
        ),
        Step(
            "IB",
            "IB = IC / β",
            f"{r.ic * 1e3:.4f} mA / {fmt_num(p.beta)}",
            fmt_i(r.ib),
        ),
        Step(
            "IE",
            "IE = IC · (β+1)/β",
            f"{r.ic * 1e3:.4f} mA · {fmt_num(p.beta + 1)}/{fmt_num(p.beta)}",
            fmt_i(r.ie),
        ),
        Step(
            "VE",
            "VE = IE · RE",
            f"{r.ie * 1e3:.4f} mA · {re} kΩ",
            fmt_v(r.ve),
        ),
    ]


def _cutoff_steps(p: BiasParams, r: BiasResult) -> list[Step]:
    r1, r2 = _kohm(p.r1), _kohm(p.r2)
    return [
        Step(
            "VBB",
            "VBB = VCC · R2 / (R1 + R2)",
            f"{fmt_num(p.vcc)} · {r2} / ({r1} + {r2})",
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
