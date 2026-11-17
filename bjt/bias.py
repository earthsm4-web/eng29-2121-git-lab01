"""DC bias solutions for the common-emitter voltage-divider circuit."""

from dataclasses import dataclass
from enum import Enum

from .params import STIFFNESS_FACTOR, BiasParams

__all__ = [
    "VCE_SAT",
    "STIFFNESS_FACTOR",
    "Region",
    "BiasResult",
    "Comparison",
    "solve_exact",
    "solve_saturation",
    "solve_approximate",
    "solve",
    "compare",
    "solve_fixed",
    "solve_emitter",
    "solve_bias",
]

VCE_SAT = 0.2


class Region(str, Enum):
    ACTIVE = "active"
    SATURATION = "saturation"
    CUTOFF = "cutoff"

    @property
    def label(self) -> str:
        return self.value.capitalize()


@dataclass(frozen=True)
class BiasResult:
    region: Region
    ib: float
    ic: float
    ie: float
    vbe: float
    vce: float
    vb: float
    vc: float
    ve: float

    @property
    def active_valid(self) -> bool:
        """False when these numbers came from an invalid active-mode solve."""
        return self.region is not Region.SATURATION


def solve_exact(p: BiasParams) -> BiasResult:
    """Solve the active region with base current reflected into the emitter."""
    ib = (p.vbb - p.vbe) / (p.rbb + (p.beta + 1.0) * p.re)
    ic = p.beta * ib
    ie = (p.beta + 1.0) * ib
    ve = ie * p.re
    vb = ve + p.vbe
    vc = p.vcc - ic * p.rc
    vce = p.vcc - ic * p.rc - ie * p.re
    return BiasResult(Region.ACTIVE, ib, ic, ie, p.vbe, vce, vb, vc, ve)


def solve_saturation(p: BiasParams) -> BiasResult:
    """Solve with the collector-emitter voltage pinned at VCE_SAT."""
    ic = (p.vcc - VCE_SAT) / (p.rc + p.re * (p.beta + 1.0) / p.beta)
    ib = ic / p.beta
    ie = ic * (p.beta + 1.0) / p.beta
    ve = ie * p.re
    vb = ve + p.vbe
    vc = p.vcc - ic * p.rc
    return BiasResult(Region.SATURATION, ib, ic, ie, p.vbe, VCE_SAT, vb, vc, ve)


def solve(p: BiasParams) -> BiasResult:
    """Classify the operating point and return the matching solution."""
    if p.vbb <= p.vbe:
        return BiasResult(Region.CUTOFF, 0.0, 0.0, 0.0, p.vbb,
                          p.vcc, p.vbb, p.vcc, 0.0)

    active = solve_exact(p)
    if active.vce < VCE_SAT:
        return solve_saturation(p)
    return active


@dataclass(frozen=True)
class Comparison:
    approx: BiasResult
    diffs: dict[str, float]
    stiff: bool


def solve_approximate(p: BiasParams) -> BiasResult:
    """Approximate stiff-divider solution: VB taken as VBB, IB ignored."""
    ie = (p.vbb - p.vbe) / p.re
    ic = ie
    ib = ic / p.beta
    ve = ie * p.re
    vb = p.vbb
    vc = p.vcc - ic * p.rc
    vce = p.vcc - ie * (p.rc + p.re)
    return BiasResult(Region.ACTIVE, ib, ic, ie, p.vbe, vce, vb, vc, ve)


def compare(p: BiasParams) -> Comparison:
    """Signed percent differences of the approximate solve against the exact one."""
    exact = solve_exact(p)
    approx = solve_approximate(p)
    diffs = {}
    for key in ("ic", "ie", "vce", "vb"):
        exact_value = getattr(exact, key)
        approx_value = getattr(approx, key)
        diffs[key] = (approx_value - exact_value) / exact_value * 100.0
    return Comparison(approx=approx, diffs=diffs, stiff=p.is_stiff)


def solve_fixed(p: BiasParams) -> BiasResult:
    """Solve fixed-bias common-emitter circuit: RB from VCC to Base, Emitter to ground.

    IB = (VCC − VBE) / RB, VE = 0 V.
    """
    rb = p.rb
    if rb is None:
        raise ValueError("Fixed bias requires RB")

    if p.vcc <= p.vbe:
        return BiasResult(Region.CUTOFF, 0.0, 0.0, 0.0, p.vcc, p.vcc, p.vcc, p.vcc, 0.0)

    ib = (p.vcc - p.vbe) / rb
    ic = p.beta * ib
    ie = (p.beta + 1.0) * ib
    ve = 0.0
    vb = ve + p.vbe
    vc = p.vcc - ic * p.rc
    vce = vc - ve

    if vce < VCE_SAT:
        ic = (p.vcc - VCE_SAT) / p.rc
        ib = ic / p.beta
        ie = ic * (p.beta + 1.0) / p.beta
        ve = 0.0
        vb = ve + p.vbe
        vc = VCE_SAT
        vce = VCE_SAT
        return BiasResult(Region.SATURATION, ib, ic, ie, p.vbe, vce, vb, vc, ve)

    return BiasResult(Region.ACTIVE, ib, ic, ie, p.vbe, vce, vb, vc, ve)


def solve_emitter(p: BiasParams) -> BiasResult:
    """Solve emitter-bias common-emitter circuit: RB from VCC to Base, RE from Emitter to ground.

    IB = (VCC − VBE) / [RB + (β+1)·RE], VE = IE·RE.
    """
    rb = p.rb
    re = p.re
    if rb is None or re is None:
        raise ValueError("Emitter bias requires RB and RE")

    if p.vcc <= p.vbe:
        return BiasResult(Region.CUTOFF, 0.0, 0.0, 0.0, p.vcc, p.vcc, p.vcc, p.vcc, 0.0)

    ib = (p.vcc - p.vbe) / (rb + (p.beta + 1.0) * re)
    ic = p.beta * ib
    ie = (p.beta + 1.0) * ib
    ve = ie * re
    vb = ve + p.vbe
    vc = p.vcc - ic * p.rc
    vce = vc - ve

    if vce < VCE_SAT:
        ic = (p.vcc - VCE_SAT) / (p.rc + re * (p.beta + 1.0) / p.beta)
        ib = ic / p.beta
        ie = ic * (p.beta + 1.0) / p.beta
        ve = ie * re
        vb = ve + p.vbe
        vc = p.vcc - ic * p.rc
        vce = VCE_SAT
        return BiasResult(Region.SATURATION, ib, ic, ie, p.vbe, vce, vb, vc, ve)

    return BiasResult(Region.ACTIVE, ib, ic, ie, p.vbe, vce, vb, vc, ve)


def solve_bias(p: BiasParams) -> BiasResult:
    """Select and run the solver for the circuit's bias mode.

    ``divider`` keeps the original behaviour unchanged.
    """
    if p.mode == "fixed":
        return solve_fixed(p)
    if p.mode == "emitter":
        return solve_emitter(p)
    return solve(p)
