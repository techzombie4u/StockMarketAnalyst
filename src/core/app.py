
# src/core/app.py
import os, sys
from flask import Flask, jsonify, render_template

def create_app():
    # Point templates/static to /web
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # /.../src
    template_dir = os.path.normpath(os.path.join(base_dir, "..", "web", "templates"))
    static_dir   = os.path.normpath(os.path.join(base_dir, "..", "web", "static"))

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # ---- Register Fusion blueprint/UI ----
    fusion_bp = None
    try:
        from fusion.api.fusion import fusion_bp as fb
        fusion_bp = fb
    except Exception:
        try:
            from src.fusion.api.fusion import fusion_bp as fb
            fusion_bp = fb
        except Exception as e:
            app.logger.warning(f"Fusion blueprint not registered: {e}")
    if fusion_bp:
        app.register_blueprint(fusion_bp)

    # Provide /fusion-dashboard if not in BP (failsafe)
    @app.route("/fusion-dashboard")
    def fusion_dashboard_fallback():
        # If the blueprint already defined this, Flask will ignore this duplicate.
        try:
            return render_template("fusion_dashboard.html")
        except Exception:
            return "Fusion Dashboard page not available", 404

    # ---- Register Agents blueprint ----
    agents_bp = None
    try:
        from agents.api import agents_bp as abp
        agents_bp = abp
    except Exception:
        try:
            from src.agents.api import agents_bp as abp
            agents_bp = abp
        except Exception as e:
            app.logger.warning(f"Agents blueprint not registered: {e}")
    if agents_bp:
        app.register_blueprint(agents_bp)

    # ---- Bind/repair agent registry entries at startup ----
    try:
        try:
            from agents.registry import registry
            from agents.new_ai_agent import run as new_ai_run
            from agents.sentiment_agent import run as sentiment_run
        except Exception:
            from src.agents.registry import registry
            from src.agents.new_ai_agent import run as new_ai_run
            from src.agents.sentiment_agent import run as sentiment_run

        # (Re)bind run fns & ensure proper meta entries (self-heals malformed registry.json)
        registry.register_or_bind(
            agent_id="new_ai_analyzer",
            name="New AI Analyzer",
            run_fn=new_ai_run,
            description="Lightweight analyzer for orchestration tests",
            enabled=True,
        )
        registry.register_or_bind(
            agent_id="sentiment_analyzer",
            name="Sentiment Analyzer",
            run_fn=sentiment_run,
            description="Lightweight sentiment agent for orchestration tests",
            enabled=True,
        )
    except Exception as e:
        app.logger.warning(f"Failed to bind agents: {e}")

    @app.route("/")
    def root():
        return "Stock Analyst server is running", 200

    return app
