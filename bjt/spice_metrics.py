"""Pure AC/transient metric calculations.

Derived metrics from SpiceAcResult and SpiceTranResult — no Flask, no ngspice,
no plotting.  All values come from input arrays; definitions follow the spec
verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass

from bjt.spice_engine import SpiceAcResult, SpiceTranResult


@dataclass(frozen=True)
class AcSummary:
    """Summary metrics from an AC analysis result."""

    gain_db_at_frequency: float
    gain_frequency_hz: float
    midband_gain_db: float
    phase_deg_at_frequency: float
    low_cutoff_hz: float | None
    high_cutoff_hz: float | None
    bandwidth_hz: float | None
    cutoff_note: str


@dataclass(frozen=True)
class TranSummary:
    """Summary metrics from a transient analysis result."""

    time_s: float
    vin_peak_to_peak_v: float
    vout_peak_to_peak_v: float
    analysis_window_start_s: float
    sample_count: int


def _find_closest_freq_index(frequency: list[float], target_hz: float) -> int:
    """Return the index of the frequency closest to target_hz."""
    return min(range(len(frequency)), key=lambda i: abs(frequency[i] - target_hz))


def _linear_interpolate_x(y_target: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Interpolate x given y_target between (x1,y1) and (x2,y2)."""
    if x2 == x1:
        return x1
    return x1 + (y_target - y1) * (x2 - x1) / (y2 - y1)


def ac_summary(result: SpiceAcResult, target_freq_hz: float) -> AcSummary:
    """Derive AC summary metrics from :class:`SpiceAcResult`.

    Uses the closest real frequency for gain/phase at the target frequency.
    Midband gain is ``max(gain_db)``.  3-dB cutoffs are found by upward/downward
    crossing of ``midband - 3`` around the peak index with linear interpolation.
    Returns ``None`` for a cutoff when the crossing is absent, with a note.
    Raises ``ValueError`` for empty or mismatched arrays.
    """
    if not result.frequency:
        raise ValueError("frequency array is empty")
    if not result.gain_db:
        raise ValueError("gain_db array is empty")
    if not result.phase_deg:
        raise ValueError("phase_deg array is empty")
    if len(result.frequency) != len(result.gain_db) or len(result.frequency) != len(result.phase_deg):
        raise ValueError("arrays have mismatched lengths")

    freq = result.frequency
    n = len(freq)
    peak_idx = max(range(n), key=lambda i: result.gain_db[i])
    midband = result.gain_db[peak_idx]
    target_gain = midband - 3.0

    # Gain at target frequency (closest real bin)
    target_idx = _find_closest_freq_index(freq, target_freq_hz)
    gain_at_target = result.gain_db[target_idx]
    phase_at_target = result.phase_deg[target_idx]

    # --- find low-frequency (lower) 3-dB crossing ---
    low_crossing_hz: float | None = None
    low_found = False
    # Search left of peak (lower frequencies), from peak down to index 1
    for i in range(peak_idx, 0, -1):
        y1, y2 = result.gain_db[i - 1], result.gain_db[i]
        x1, x2 = freq[i - 1], freq[i]
        if (y1 <= target_gain < y2) or (y2 <= target_gain < y1):
            low_crossing_hz = _linear_interpolate_x(target_gain, x1, y1, x2, y2)
            low_found = True
            break
    # Also check segment 0->1 if peak is at index 0
    if not low_found and peak_idx > 0:
        for i in range(0, peak_idx):
            y1, y2 = result.gain_db[i], result.gain_db[i + 1]
            x1, x2 = freq[i], freq[i + 1]
            if (y1 <= target_gain < y2) or (y2 <= target_gain < y1):
                low_crossing_hz = _linear_interpolate_x(target_gain, x1, y1, x2, y2)
                low_found = True
                break

    # --- find high-frequency (upper) 3-dB crossing ---
    high_crossing_hz: float | None = None
    high_found = False
    for i in range(peak_idx, n - 1):
        y1, y2 = result.gain_db[i], result.gain_db[i + 1]
        x1, x2 = freq[i], freq[i + 1]
        if (y1 <= target_gain < y2) or (y2 <= target_gain < y1):
            high_crossing_hz = _linear_interpolate_x(target_gain, x1, y1, x2, y2)
            high_found = True
            break

    # Build result note and bandwidth
    if low_found and high_found:
        if low_crossing_hz is not None and high_crossing_hz is not None:
            bandwidth = high_crossing_hz - low_crossing_hz
        else:
            bandwidth = None
        note = "3 dB bandwidth"
    elif low_found:
        low_hz = low_crossing_hz if low_crossing_hz is not None else 0.0
        note = f"low 3 dB cutoff at {low_hz:.1f} Hz, high not found"
        high_crossing_hz = None
        bandwidth = None
    elif high_found:
        high_hz = high_crossing_hz if high_crossing_hz is not None else 0.0
        note = f"high 3 dB cutoff at {high_hz:.1f} Hz, low not found"
        low_crossing_hz = None
        bandwidth = None
    else:
        note = "3 dB cutoffs not found"
        low_crossing_hz = None
        high_crossing_hz = None
        bandwidth = None

    return AcSummary(
        gain_db_at_frequency=gain_at_target,
        gain_frequency_hz=target_freq_hz,
        midband_gain_db=midband,
        phase_deg_at_frequency=phase_at_target,
        low_cutoff_hz=low_crossing_hz,
        high_cutoff_hz=high_crossing_hz,
        bandwidth_hz=bandwidth,
        cutoff_note=note,
    )


def tran_summary(result: SpiceTranResult, source_freq_hz: float) -> TranSummary:
    """Derive transient summary metrics from :class:`SpiceTranResult`.

    Ignores the first two complete cycles of the source waveform.
    Raises ``ValueError`` if ``source_freq_hz`` is zero or the result has
    insufficient data after the analysis window.
    """
    if source_freq_hz == 0:
        raise ValueError("source_freq_hz must be non-zero")

    time = result.time
    vin = result.vin
    vout = result.vout

    period = 1.0 / source_freq_hz
    window_start = 2.0 * period  # skip first two cycles

    # Find first index with time >= window_start
    start_idx = 0
    for i, t in enumerate(time):
        if t >= window_start:
            start_idx = i
            break

    window_time = time[start_idx:]
    window_vin = vin[start_idx:]
    window_vout = vout[start_idx:]

    if not window_time:
        raise ValueError("no data after analysis window")

    vin_ptp = max(window_vin) - min(window_vin)
    vout_ptp = max(window_vout) - min(window_vout)
    sample_count = len(window_time)
    last_time = window_time[-1]

    return TranSummary(
        time_s=last_time,
        vin_peak_to_peak_v=vin_ptp,
        vout_peak_to_peak_v=vout_ptp,
        analysis_window_start_s=window_start,
        sample_count=sample_count,
    )