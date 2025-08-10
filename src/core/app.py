# src/core/app.py
from flask import Flask, jsonify

def create_app():
    app = Flask(__name__, template_folder="../../web/templates", static_folder="../../web/static")

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # --- Fusion API/UI ---
    try:
        from fusion.api.fusion import fusion_bp
    except Exception:
        try:
            from src.fusion.api.fusion import fusion_bp
        except Exception as e:
            app.logger.warning(f"Fusion blueprint not registered: {e}")
            fusion_bp = None
    if fusion_bp:
        app.register_blueprint(fusion_bp)

    # --- Agents API ---
    try:
        from agents.api import agents_bp
    except Exception:
        try:
            from src.agents.api import agents_bp
        except Exception as e:
            app.logger.warning(f"Agents blueprint not registered: {e}")
            agents_bp = None
    if agents_bp:
        app.register_blueprint(agents_bp)

    # --- (Optional) KPI blueprint if you have one ---
    try:
        from kpi.api import kpi_bp  # only if exists
        app.register_blueprint(kpi_bp)
    except Exception as e:
        app.logger.warning(f"KPI blueprint not registered: {e}")

    # --- Bind agent run functions AFTER registry loads ---
    try:
        try:
            from agents.registry import registry
            from agents.new_ai_agent import run as new_ai_run
            from agents.sentiment_agent import run as sentiment_run
        except Exception:
            from src.agents.registry import registry
            from src.agents.new_ai_agent import run as new_ai_run
            from src.agents.sentiment_agent import run as sentiment_run

        registry.register_or_bind(
            agent_id="new_ai_analyzer",
            name="New AI Analyzer",
            run_fn=new_ai_run,
            description="Placeholder AI analyzer",
            enabled=True
        )
        registry.register_or_bind(
            agent_id="sentiment_analyzer",
            name="Sentiment Analyzer",
            run_fn=sentiment_run,
            description="Placeholder sentiment analyzer",
            enabled=True
        )
    except Exception as e:
        app.logger.warning(f"Failed to bind agents: {e}")

    @app.route("/")
    def root():
        return "Stock Analyst server is running", 200

    return app