
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

    # --- trivial health ---
    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # --- root page remains simple ---
    @app.route("/")
    def root():
        return "Stock Analyst server is running", 200

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
    try:
        from src.fusion.api.fusion import fusion_bp
        app.register_blueprint(fusion_bp, url_prefix="/api/fusion")
    except Exception as e:
        app.logger.warning(f"Fusion blueprint not registered: {e}")

    # Register Agents blueprint
    try:
        from src.agents.api import agents_bp
        app.register_blueprint(agents_bp)
    except Exception as e:
        app.logger.warning(f"Agents blueprint not registered: {e}")

    # Register KPI blueprint
    try:
        from src.kpi.api import kpi_bp
        app.register_blueprint(kpi_bp)
    except Exception as e:
        app.logger.warning(f"KPI blueprint not registered: {e}")

    # --- bind agent run functions to registry (after registry load) ---
    try:
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

    return app
