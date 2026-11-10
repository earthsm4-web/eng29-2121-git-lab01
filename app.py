"""Flask routes for the common-emitter DC bias calculator."""

from flask import Flask, render_template, request

from bjt.bias import Region, compare, solve
from bjt.format import fmt_i, fmt_v
from bjt.validate import parse_form

DEFAULTS = {
    "vcc": "12", "r1": "47", "r2": "10", "rc": "4.7",
    "re": "1", "beta": "100", "vbe": "0.7",
}

FIELDS = [
    ("vcc", "VCC", "V"),
    ("r1", "R1", "kΩ"),
    ("r2", "R2", "kΩ"),
    ("rc", "RC", "kΩ"),
    ("re", "RE", "kΩ"),
    ("beta", "Beta", ""),
    ("vbe", "VBE", "V"),
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


def create_app() -> Flask:
    app = Flask(__name__)
    app.add_template_filter(fmt_v, "v")
    app.add_template_filter(fmt_i, "i")

    @app.get("/")
    def index():
        return render_template(
            "index.html", values=DEFAULTS, errors={}, fields=FIELDS
        )

    @app.post("/calculate")
    def calculate():
        params, errors = parse_form(request.form)
        if params is None:
            return (
                render_template(
                    "index.html", values=request.form, errors=errors, fields=FIELDS
                ),
                400,
            )

        result = solve(params)
        comparison = compare(params) if result.region is Region.ACTIVE else None
        return render_template(
            "result.html",
            result=result,
            comparison=comparison,
            quantities=QUANTITIES,
            compare_keys=COMPARE_KEYS,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(port=5000)
