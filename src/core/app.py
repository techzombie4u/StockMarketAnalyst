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

    # ---- Register the working Fusion API ----
    try:
        from src.api.fusion_api import fusion_bp
        app.register_blueprint(fusion_bp)
        app.logger.info("✅ Registered fusion API blueprint at /api/fusion")
    except Exception as e:
        app.logger.warning(f"❌ Fusion API blueprint not registered: {e}")

    # ---- Register Agents blueprint ----
    try:
        from src.agents.api.agents import agents_bp
        app.register_blueprint(agents_bp)
        app.logger.info("✅ Registered agents blueprint at /api/agents")
    except Exception as e:
        app.logger.warning(f"❌ Agents blueprint not registered: {e}")

    # ---- Main dashboard routes ----
    @app.route("/")
    def root():
        try:
            return render_template("dashboard.html")
        except Exception as e:
            app.logger.warning(f"Failed to load main dashboard: {e}")
            return f"""
            <html>
                <head><title>Stock Analyst Dashboard</title></head>
                <body>
                    <h1>📊 Stock Analyst Server</h1>
                    <p>Server is running successfully!</p>
                    <ul>
                        <li><a href="/fusion-dashboard">Fusion Dashboard</a></li>
                        <li><a href="/health">Health Check</a></li>
                        <li><a href="/api/fusion/dashboard">Fusion API</a></li>
                        <li><a href="/api/agents/health">Agents API</a></li>
                    </ul>
                </body>
            </html>
            """, 200

    @app.route("/fusion-dashboard")
    def fusion_dashboard():
        try:
            return render_template("dashboard.html")
        except Exception:
            return "Fusion Dashboard page not available", 404

    # ---- Bind agent registry entries at startup ----
    try:
        from src.agents.core.registry import registry
        from src.agents.new_ai_agent import run as new_ai_run
        from src.agents.sentiment_agent import run as sentiment_run

        # (Re)bind run fns & ensure proper meta entries
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
        app.logger.info("✅ Agent registry initialized")
    except Exception as e:
        app.logger.warning(f"Failed to bind agents: {e}")

    # Log routes once to verify on boot
    try:
        rules = sorted([str(r.rule) for r in app.url_map.iter_rules()])
        app.logger.info("🔎 URL map:\n  " + "\n  ".join(rules))
    except Exception:
        pass

    # --- SAFE HEALTH ROUTE (guarded) ---
    if 'health' not in app.view_functions:
        @app.route("/health", endpoint="health")
        def health():
            return {"ok": True}, 200

    # --- SAFE STOP ROUTE (used by tests/utils/server_manager.py) ---
    if '__stop__' not in app.view_functions:
        @app.route("/__stop__", methods=["GET"])
        def __stop__():
            # Allows the test harness to stop the server if it locked the port
            shutdown = request.environ.get('werkzeug.server.shutdown')
            if shutdown:
                shutdown()
            return "OK", 200

    return app