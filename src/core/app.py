
import os
from flask import Flask, jsonify, render_template

def create_app():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    app = Flask(
        __name__,
        template_folder=os.path.join(base, "web", "templates"),
        static_folder=os.path.join(base, "web", "static"),
    )

    @app.route("/healthz")
    def healthz():
        return jsonify({"status": "ok"}), 200

    # Register Fusion API
    try:
        from src.api.fusion_api import fusion_bp
        app.register_blueprint(fusion_bp)
    except Exception as e:
        # Keep server alive even if fusion import fails, so you see the error.
        @app.route("/fusion-import-error")
        def fusion_import_error():
            return f"Fusion blueprint failed to import: {e}", 500

    # HTML page used by validator smoke test
    @app.route("/fusion-dashboard")
    def fusion_dashboard_page():
        return render_template("fusion_dashboard.html")

    return app
