from flask import Flask, jsonify, render_template, request
from datetime import datetime
from core.logging import before_request, after_request
from core.metrics import snapshot
# NOTE: Imports for blueprints were adjusted to match the provided changes, though they appear to be identical to the original.
from src.fusion.api.fusion import fusion_bp
from src.agents.api import agents_bp
from src.equities.api import equities_bp
from src.options.api import options_bp
from src.commodities.api import commodities_bp
from src.kpi.api import kpi_bp
from src.core.pins_locks import pins_locks_bp

def create_app():
    app = Flask(__name__, template_folder='../../web/templates', static_folder='../../web/static')
    app.before_request(before_request); app.after_request(after_request)

    @app.get("/health")
    def health(): return jsonify({"ok": True, "ts": datetime.utcnow().isoformat()+"Z"})

    @app.get("/metrics")
    def metrics(): return jsonify({"counters": snapshot()})

    # Blueprints (MUST match exact prefixes from prior phases)
    # The following registrations are kept as per the provided changes, ensuring consistency.
    app.register_blueprint(fusion_bp, url_prefix='/api/fusion')
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    app.register_blueprint(equities_bp, url_prefix='/api/equities')
    app.register_blueprint(options_bp, url_prefix='/api/options')
    app.register_blueprint(commodities_bp, url_prefix='/api/commodities')
    app.register_blueprint(kpi_bp, url_prefix='/api/kpi')
    app.register_blueprint(pins_locks_bp, url_prefix='/api')

    # Pages — KEEP LAYOUT IDENTICAL to prototype
    @app.get("/dashboard")
    def dashboard():   return render_template("dashboard.html")
    @app.get("/equities")
    def equities():    return render_template("equities.html")
    @app.get("/options")
    def options():     return render_template("options.html")
    @app.get("/commodities")
    def commodities(): return render_template("commodities.html")
    @app.get("/")
    def root():        return render_template("dashboard.html")

    return app