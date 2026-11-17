"""Flask routes for the common-emitter DC bias calculator."""

from flask import Flask, render_template, request

from bjt.bias import Region, compare, solve, solve_bias
from bjt.format import fmt_i, fmt_num, fmt_r, fmt_v
from bjt.steps import steps_for
from bjt.validate import parse_form

DEFAULTS = {
    "vcc": "12", "r1": "47", "r2": "10", "rc": "4.7",
    "re": "1", "beta": "100", "vbe": "0.7", "mode": "divider",
}

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

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5000)
