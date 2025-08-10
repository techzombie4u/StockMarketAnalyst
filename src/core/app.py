# src/core/app.py
import os, pathlib
from flask import Flask, render_template, request, jsonify, redirect, url_for

def _guess_template_folder():
    # Prefer web/templates if present; fallback to src/templates
    here = pathlib.Path(__file__).resolve()
    cand1 = here.parents[2] / "web" / "templates"
    cand2 = here.parents[1] / "templates"
    return str(cand1 if cand1.exists() else cand2)

def _guess_static_folder():
    # Optional static folder; try web/static then src/static
    here = pathlib.Path(__file__).resolve()
    cand1 = here.parents[2] / "web" / "static"
    cand2 = here.parents[1] / "static"
    return str(cand1 if cand1.exists() else cand2)

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=_guess_template_folder(),
        static_folder=_guess_static_folder()
    )

    # Register existing product blueprints if available
    try:
        from src.products.equities.api import equity_bp
        app.register_blueprint(equity_bp, url_prefix="/api/equities")
    except Exception:
        pass

    try:
        from src.products.options.api import options_bp
        app.register_blueprint(options_bp, url_prefix="/api/options")
    except Exception:
        pass

    # Register Fusion blueprint (required by validator)
    from src.fusion.api.fusion import fusion_bp
    app.register_blueprint(fusion_bp, url_prefix="/api/fusion")

    # Register blueprints
    app.register_blueprint(fusion_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(meta_bp)
    app.register_blueprint(equities_bp)
    app.register_blueprint(options_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(shared_kpi_bp)

    # Register KPI blueprint
    from ..kpi.api import kpi_bp
    app.register_blueprint(kpi_bp)

    @app.route("/fusion-dashboard")
    def fusion_dashboard_page():
        return render_template("fusion_dashboard.html")

    @app.route("/")
    def root():
        # Was: return "Stock Analyst server is running"
        return redirect(url_for("fusion_dashboard_page"))

    @app.route("/kpi")
    def kpi_page():
        return render_template("kpi.html")

    return app