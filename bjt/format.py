"""Display formatting for voltages, currents, resistances, and plain numbers."""


def fmt_v(x: float) -> str:
    return f"{x:.4f} V"


def fmt_i(x: float) -> str:
    return f"{x * 1e6:.3f} µA" if abs(x) < 1e-3 else f"{x * 1e3:.4f} mA"


def _trim(s: str) -> str:
    return s.rstrip("0").rstrip(".")


def fmt_r(x: float) -> str:
    return f"{_trim(f'{x / 1000.0:.4f}')} kΩ"


def fmt_num(x: float) -> str:
    return _trim(f"{x:.4f}")
