"""Flask routes for the common-emitter DC bias calculator."""

import math

from flask import Flask, render_template, request

from bjt.bias import Region, compare, solve, solve_bias
from bjt.format import fmt_i, fmt_num, fmt_r, fmt_v
from bjt.steps import steps_for
from bjt.validate import parse_form
from bjt.spice_engine import SpiceParams, run_op, run_ac, run_tran
from bjt.spice_metrics import ac_summary, tran_summary
from bjt.spice_plot import plot_op_bars, plot_ac_response, plot_tran_waveforms

DEFAULTS = {
    "vcc": "12", "r1": "47", "r2": "10", "rc": "4.7",
    "re": "1", "beta": "100", "vbe": "0.7", "mode": "divider",
}

SPICE_DEFAULTS = {
    "vcc": "12", "rc": "2.2", "r1": "100", "r2": "22", "re": "1",
    "rl": "10", "beta": "100", "vbe": "0.7",
    "source_ampl": "0.010", "source_freq": "1000",
}

CE_LAB_DEFAULTS = dict(SPICE_DEFAULTS)

FIELDS = [
    ("vcc", "VCC", "V", "Supply Voltage"),
    ("r1", "R1", "kΩ", "Upper Divider"),
    ("r2", "R2", "kΩ", "Lower Divider"),
    ("rc", "RC", "kΩ", "Collector Resistor"),
    ("re", "RE", "kΩ", "Emitter Resistor"),
    ("beta", "Beta", "–", "Current Gain"),
    ("vbe", "VBE", "V", "Base-Emitter Voltage"),
]

QUANTITIES = [
    ("ib", "IB", "i"),
    ("ic", "IC", "i"),
    ("ie", "IE", "i"),
    ("vbe", "VBE", "v"),
    ("vce", "VCE", "v"),
    ("vb", "VB", "v"),
    ("vc", "VC", "v"),
    ("ve", "VE", "v"),
]

COMPARE_KEYS = [
    ("ic", "IC", "i"),
    ("ie", "IE", "i"),
    ("vce", "VCE", "v"),
    ("vb", "VB", "v"),
]


def _dashboard(values, errors=None, params=None) -> str:
    """Render the single-page dashboard, solving only when params are valid."""
    result = steps = comparison = None
    if params is not None:
        result = solve_bias(params)
        steps = steps_for(params, result)
        comparison = (
            compare(params)
            if result.region is Region.ACTIVE and params.mode == "divider"
            else None
        )

    return render_template(
        "index.html",
        values=values,
        errors=errors or {},
        fields=FIELDS,
        result=result,
        params=params,
        steps=steps,
        comparison=comparison,
        quantities=QUANTITIES,
        compare_keys=COMPARE_KEYS,
        mode=params.mode if params else "divider",
    )


def _spice_defaults() -> dict:
    """Return default SPICE parameters (kΩ / V / Hz units for the form)."""
    return dict(SPICE_DEFAULTS)


def _spice_dashboard(values=None, errors=None, spice_result=None,
                     spice_error=None, analytical_result=None,
                     analytical_error=None, analysis="op", run_ts=None,
                     run_artifact=None) -> str:
    """Render the SPICE simulation page, separating SPICE from Analytical results."""
    return render_template(
        "spice.html",
        values=values or {},
        errors=errors or {},
        spice_result=spice_result,
        spice_error=spice_error,
        analytical_result=analytical_result,
        analytical_error=analytical_error,
        analysis=analysis,
        run_ts=run_ts,
        run_artifact=run_artifact,
        plot_op_bars=plot_op_bars,
        plot_ac_response=plot_ac_response,
        plot_tran_waveforms=plot_tran_waveforms,
    )


def parse_spice_form(form) -> tuple[dict[str, float] | None, dict[str, str]]:
    """Parse and validate SPICE form inputs (kΩ, V, Hz units).

    Returns (values_in_SI, {}) or (None, errors).
    Bounds (validated before netlist creation):
      - resistances > 0 kΩ
      - beta ≥ 1
      - VBE 0.1–2 V
      - source amplitude > 0 and ≤ 1 V
      - source frequency 1 Hz–1 MHz
      - VCC > 0 V
    Parse finite numbers only. Convert kΩ→Ω after validation.
    """
    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    numeric_fields = {
        "vcc": ("VCC", 0.0, None),
        "rc": ("RC", 0.0, None),
        "r1": ("R1", 0.0, None),
        "r2": ("R2", 0.0, None),
        "re": ("RE", 0.0, None),
        "rl": ("RL", 0.0, None),
        "beta": ("Beta", 1.0, None),
        "vbe": ("VBE", 0.1, 2.0),
        "source_ampl": ("Source amplitude", 0.0, 1.0),
        "source_freq": ("Source frequency", 1.0, 1_000_000.0),
    }

    for field, (label, lo, hi) in numeric_fields.items():
        raw = (form.get(field) or "").strip()
        if not raw:
            errors[field] = f"{label} is required"
            continue
        try:
            value = float(raw)
        except ValueError:
            errors[field] = f"{label} must be a number"
            continue
        if not math.isfinite(value):
            errors[field] = f"{label} must be a number"
            continue
        if lo is not None:
            # Inclusive lower bound for beta (≥1), vbe (0.1–2.0), source_freq (1–1MHz);
            # strict lower bound (>0) for vcc/rc/r1/re/rl/source_ampl
            if field in ("beta", "vbe", "source_freq"):
                if value < lo:
                    errors[field] = f"{label} must be greater than or equal to {lo}"
                    continue
            else:
                if value <= lo:
                    errors[field] = f"{label} must be greater than {lo}"
                    continue
        if hi is not None and value > hi:
            errors[field] = f"{label} must be less than or equal to {hi}"
            continue
        values[field] = value

    if errors:
        return None, errors

    # Convert kΩ → Ω for resistances
    for field in ("rc", "r1", "r2", "re", "rl"):
        values[field] *= 1000.0

    return values, {}


def _ce_lab_dashboard(values, errors=None, analysis="op", spice_result=None,
                      spice_error=None, ac_metrics=None, tran_metrics=None,
                      *, plot_uri=None) -> str:
    """Render the CE lab page with SPICE-only provenance.

    ``plot_uri`` is computed in the route from the real parsed result (never in
    Jinja) and is only rendered when ``spice_result`` is present.
    """
    return render_template(
        "ce_lab.html",
        values=values or {},
        errors=errors or {},
        analysis=analysis,
        spice_result=spice_result,
        spice_error=spice_error,
        ac_metrics=ac_metrics,
        tran_metrics=tran_metrics,
        plot_uri=plot_uri,
    )


def create_app() -> Flask:
    app = Flask(__name__)
    app.add_template_filter(fmt_v, "v")
    app.add_template_filter(fmt_i, "i")
    app.add_template_filter(fmt_r, "r")
    app.add_template_filter(fmt_num, "num")

    @app.get("/")
    def index():
        params, _ = parse_form(DEFAULTS, mode=DEFAULTS.get("mode", "divider"))
        return _dashboard(DEFAULTS, params=params)

    @app.post("/calculate")
    def calculate():
        mode = request.form.get("mode", "divider")
        params, errors = parse_form(request.form, mode=mode)
        if params is None:
            return _dashboard(request.form, errors=errors), 400
        return _dashboard(request.form, params=params)

    @app.get("/spice")
    def spice_index():
        return _spice_dashboard(values=_spice_defaults(), analysis="op")

    @app.post("/spice/run")
    def spice_run():
        analysis = request.form.get("analysis", "op")
        if analysis not in ("op", "ac", "tran"):
            analysis = "op"

        values, errors = parse_spice_form(request.form)
        if errors:
            return _spice_dashboard(
                values=request.form, errors=errors, analysis=analysis
            ), 400

        # Build validated SI-unit params for the SPICE engine
        spice_params = SpiceParams(
            vcc=values["vcc"],
            rc=values["rc"],
            r1=values["r1"],
            r2=values["r2"],
            re=values["re"],
            rl=values["rl"],
            beta=values["beta"],
            vbe=values["vbe"],
            source_ampl=values["source_ampl"],
            source_freq=values["source_freq"],
        )

        # Also compute the analytical DC reference (same circuit, same params)
        from bjt.params import BiasParams as _BiasParams
        analytical_result = None
        analytical_error = None
        try:
            analytical_params = _BiasParams(
                vcc=values["vcc"], rc=values["rc"], beta=values["beta"],
                vbe=values["vbe"], mode="divider",
                r1=values["r1"], r2=values["r2"], re=values["re"],
            )
            from bjt.bias import solve_bias as _solve_bias
            analytical_result = _solve_bias(analytical_params)
        except Exception as exc:  # noqa: BLE001
            analytical_error = str(exc)

        # Run the real SPICE simulation
        spice_result = None
        spice_error = None
        try:
            if analysis == "op":
                spice_result = run_op(spice_params)
            elif analysis == "ac":
                spice_result = run_ac(spice_params)
            elif analysis == "tran":
                spice_result = run_tran(spice_params)
        except Exception as exc:  # noqa: BLE001
            spice_error = str(exc)

        import datetime, os
        run_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        artifact_path = None
        try:
            runs_dir = os.path.join(os.path.dirname(__file__), "docs", "captures")
            os.makedirs(runs_dir, exist_ok=True)
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            artifact_path = os.path.join(runs_dir, f"spice-{analysis}-{stamp}.txt")
            with open(artifact_path, "w", encoding="utf-8") as f:
                f.write(f"analysis: {analysis}\n")
                f.write(f"timestamp: {run_ts}\n")
                f.write("\n=== NETLIST ===\n")
                f.write((spice_result.netlist if spice_result else "") + "\n")
                f.write("\n=== RUN LOG ===\n")
                f.write((spice_result.run_log if spice_result else spice_error or "") + "\n")
        except Exception:
            artifact_path = None

        return _spice_dashboard(
            values={k: str(v) for k, v in request.form.items()},
            errors={},
            spice_result=spice_result,
            spice_error=spice_error,
            analytical_result=analytical_result,
            analytical_error=analytical_error,
            analysis=analysis,
            run_ts=run_ts,
            run_artifact=artifact_path,
        )

    @app.get("/ce-lab")
    def ce_lab():
        return _ce_lab_dashboard(values=CE_LAB_DEFAULTS, analysis="op")

    @app.post("/ce-lab/run")
    def ce_lab_run():
        analysis = request.form.get("analysis", "op")
        if analysis not in ("op", "ac", "tran"):
            analysis = "op"

        values, errors = parse_spice_form(request.form)
        if errors:
            return _ce_lab_dashboard(
                values=request.form, errors=errors, analysis=analysis
            ), 400

        spice_params = SpiceParams(
            vcc=values["vcc"],
            rc=values["rc"],
            r1=values["r1"],
            r2=values["r2"],
            re=values["re"],
            rl=values["rl"],
            beta=values["beta"],
            vbe=values["vbe"],
            source_ampl=values["source_ampl"],
            source_freq=values["source_freq"],
        )

        spice_result = None
        spice_error = None
        ac_metrics = None
        tran_metrics = None
        plot_uri = None

        try:
            if analysis == "op":
                spice_result = run_op(spice_params)
                plot_uri = plot_op_bars(spice_result)
            elif analysis == "ac":
                spice_result = run_ac(spice_params)
                ac_metrics = ac_summary(spice_result, values["source_freq"])
                plot_uri = plot_ac_response(
                    spice_result.frequency,
                    spice_result.gain_db,
                    spice_result.phase_deg,
                )
            else:
                spice_result = run_tran(spice_params)
                tran_metrics = tran_summary(spice_result, values["source_freq"])
                plot_uri = plot_tran_waveforms(
                    spice_result.time,
                    spice_result.vin,
                    spice_result.vout,
                )
        except Exception as exc:  # noqa: BLE001 -- surface engine/metric errors
            spice_result = None
            spice_error = str(exc)
            ac_metrics = None
            tran_metrics = None
            plot_uri = None

        return _ce_lab_dashboard(
            values={k: str(v) for k, v in request.form.items()},
            errors={},
            analysis=analysis,
            spice_result=spice_result,
            spice_error=spice_error,
            ac_metrics=ac_metrics,
            tran_metrics=tran_metrics,
            plot_uri=plot_uri,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5000)
