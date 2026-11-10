"""Circuit parameters in SI units (ohms, volts, amperes)."""

from dataclasses import dataclass

STIFFNESS_FACTOR = 10.0


@dataclass(frozen=True)
class BiasParams:
    """Voltage-divider common-emitter bias inputs, already in SI units."""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float

    @property
    def vbb(self) -> float:
        """Thevenin equivalent voltage of the R1/R2 divider."""
        return self.vcc * self.r2 / (self.r1 + self.r2)

    @property
    def rbb(self) -> float:
        """Thevenin equivalent resistance of the R1/R2 divider."""
        return self.r1 * self.r2 / (self.r1 + self.r2)

    @property
    def is_stiff(self) -> bool:
        """True when the divider is stiff enough for the approximate method."""
        return self.beta * self.re >= STIFFNESS_FACTOR * self.r2
