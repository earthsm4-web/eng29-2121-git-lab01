"""Graph generation from real SPICE results using matplotlib.

Produces base64-encoded PNG images for embedding in Flask/Jinja HTML.
All data comes from real ngspice output -- no mock data.
"""

from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _fig_to_base64(fig) -> str:
    """Save a matplotlib figure to a base64 PNG data URI."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return f"data:image/png;base64,{data}"


def plot_ac_response(frequency, gain_db, phase_deg) -> str:
    """Plot Bode response (Gain / Phase vs Frequency) from real .ac data."""
    fig, (ax_gain, ax_phase) = plt.subplots(
        2, 1, figsize=(6.4, 4.8), sharex=True
    )

    ax_gain.semilogx(frequency, gain_db, color="#0f766e", linewidth=2)
    ax_gain.set_ylabel("Gain (dB)", fontsize=10, fontweight="bold")
    ax_gain.set_title("AC Frequency Response — Gain", fontsize=11, fontweight="bold")
    ax_gain.grid(True, which="both", ls=":", alpha=0.5)
    ax_gain.tick_params(labelsize=9)

    ax_phase.semilogx(frequency, phase_deg, color="#a35a00", linewidth=2)
    ax_phase.set_xlabel("Frequency (Hz)", fontsize=10, fontweight="bold")
    ax_phase.set_ylabel("Phase (°)", fontsize=10, fontweight="bold")
    ax_phase.set_title("AC Frequency Response — Phase", fontsize=11, fontweight="bold")
    ax_phase.grid(True, which="both", ls=":", alpha=0.5)
    ax_phase.tick_params(labelsize=9)

    fig.tight_layout()
    return _fig_to_base64(fig)


def plot_tran_waveforms(time, vin, vout) -> str:
    """Plot Input / Output waveforms (Vin vs Vout vs Time) from real .tran data."""
    fig, ax = plt.subplots(figsize=(6.4, 3.6))

    ax.plot(time, vin, color="#0f766e", linewidth=2, label="Vin (teal)")
    ax.plot(time, vout, color="#a35a00", linewidth=2, label="Vout (orange)")
    ax.set_xlabel("Time (ms)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Voltage (V)", fontsize=10, fontweight="bold")
    ax.set_title("Transient Response — Input / Output Waveforms",
                 fontsize=11, fontweight="bold")
    ax.grid(True, ls=":", alpha=0.5)
    ax.legend(fontsize=9, loc="upper right")
    ax.tick_params(labelsize=9)

    # Convert seconds to milliseconds on x-axis labels for readability
    import matplotlib.ticker as mticker

    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{x * 1e3:.2f}")
    )

    fig.tight_layout()
    return _fig_to_base64(fig)


def plot_op_bars(result) -> str:
    """Plot DC Operating Point bar chart from real .op result."""
    import numpy as np

    fig, ax = plt.subplots(figsize=(6.4, 3.2))

    labels = ["VB", "VE", "VC", "VCE"]
    values = [result.vb, result.ve, result.vc, result.vce]
    colors = ["#0f766e", "#0f766e", "#0f766e", "#a35a00"]

    bars = ax.bar(labels, values, color=colors, width=0.6)
    ax.set_ylabel("Voltage (V)", fontsize=10, fontweight="bold")
    ax.set_title("DC Operating Point (ngspice .op)", fontsize=11, fontweight="bold")
    ax.grid(True, axis="y", ls=":", alpha=0.5)
    ax.tick_params(labelsize=9)

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.3f} V",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    fig.tight_layout()
    return _fig_to_base64(fig)
