
# src/core/app.py
import os
from flask import Flask, render_template

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "..", "web", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "..", "web", "static")
    )

    # -------- Register Blueprints (keep your existing ones too) --------
    # Equities / Options (if already exist, keep them)
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

    # Fusion blueprint (new / fixed)
    from src.fusion.api import fusion_bp
    app.register_blueprint(fusion_bp, url_prefix="/api/fusion")

    # -------- Minimal route for the Fusion dashboard page --------
    @app.route("/fusion-dashboard")
    def fusion_dashboard_page():
        # template includes required element IDs the validator checks for
        return render_template("fusion_dashboard.html")

    @app.route("/")
    def root():
        return "Stock Analyst server is running"

    @app.route("/healthz")
    def healthz():
        return {"status": "ok", "message": "Flask server is running"}

    return app
