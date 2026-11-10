"""Display formatting for voltages and currents."""


def fmt_v(x: float) -> str:
    return f"{x:.4f} V"


def fmt_i(x: float) -> str:
    return f"{x * 1e6:.3f} µA" if abs(x) < 1e-3 else f"{x * 1e3:.4f} mA"
