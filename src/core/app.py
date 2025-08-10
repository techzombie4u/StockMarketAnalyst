
# src/core/app.py
from flask import Flask, jsonify, render_template, request
import os

def _rule_exists(app, rule: str) -> bool:
    try:
        return any(r.rule == rule for r in app.url_map.iter_rules())
    except Exception:
        return False

def _attach_agents_fallback_routes(app):
    """
    Only used if /api/agents* routes are still missing after attempting to
    register the blueprint. Implements the minimal contract used by tests.
    """
    from src.agents.registry import REGISTRY, Agent
    from src.agents.builtin_agents import run_new_ai_analyzer, run_sentiment_analyzer

    # Ensure agents registered
    cur = {a["key"] for a in REGISTRY.list()}
    if "new_ai_analyzer" not in cur:
        REGISTRY.register(Agent(key="new_ai_analyzer", name="New AI Analyzer", run_fn=run_new_ai_analyzer))
    if "sentiment_analyzer" not in cur:
        REGISTRY.register(Agent(key="sentiment_analyzer", name="Sentiment Analyzer", run_fn=run_sentiment_analyzer))

    # List – accept both with and without trailing slash
    if not _rule_exists(app, "/api/agents"):
        @app.get("/api/agents")
        @app.get("/api/agents/")
        def agents_list_fallback():
            return jsonify({"success": True, "agents": REGISTRY.list()})

    # Run, enable, disable, result, config, run_all, history
    if not _rule_exists(app, "/api/agents/<key>/run"):
        @app.post("/api/agents/<key>/run")
        def agents_run_fallback(key):
            out = REGISTRY.run(key)
            return jsonify(out), (200 if out.get("success") else 400)

    if not _rule_exists(app, "/api/agents/<key>/enable"):
        @app.post("/api/agents/<key>/enable")
        def agents_enable_fallback(key):
            ok = REGISTRY.enable(key)
            return (jsonify({"success": ok}), 200 if ok else 404)

    if not _rule_exists(app, "/api/agents/<key>/disable"):
        @app.post("/api/agents/<key>/disable")
        def agents_disable_fallback(key):
            ok = REGISTRY.disable(key)
            return (jsonify({"success": ok}), 200 if ok else 404)

    if not _rule_exists(app, "/api/agents/<key>/result"):
        @app.get("/api/agents/<key>/result")
        def agents_result_fallback(key):
            r = REGISTRY.get_last_result(key)
            if not r:
                return jsonify({"success": False, "error": "no result"}), 404
            return jsonify({"success": True, "result": r})

    if not _rule_exists(app, "/api/agents/config"):
        @app.get("/api/agents/config")
        def agents_cfg_get_fallback():
            return jsonify(REGISTRY.get_config())

        @app.post("/api/agents/config")
        def agents_cfg_set_fallback():
            payload = request.get_json(silent=True) or {}
            if not isinstance(payload, dict):
                payload = {}
            out = REGISTRY.set_config(payload)
            return jsonify(out), (200 if out.get("success") else 400)

    if not _rule_exists(app, "/api/agents/run_all"):
        @app.post("/api/agents/run_all")
        def agents_run_all_fallback():
            return jsonify(REGISTRY.run_all())

    if not _rule_exists(app, "/api/agents/history"):
        @app.get("/api/agents/history")
        def agents_history_fallback():
            from src.agents.registry import REGISTRY
            key = request.args.get("agent", "").strip()
            if not key:
                return jsonify({"success": False, "error": "missing agent"}), 400
            return jsonify(REGISTRY.history(key))


def create_app():
    # Point templates/static to /web
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # /.../src
    template_dir = os.path.normpath(os.path.join(base_dir, "..", "web", "templates"))
    static_dir   = os.path.normpath(os.path.join(base_dir, "..", "web", "static"))

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # /health guard
    if not any(r.endpoint == "health" for r in app.url_map.iter_rules()):
        @app.route("/health", endpoint="health")
        def health():
            return jsonify({"status": "ok"})

    # Dashboard route (keep if you already have different one)
    if not _rule_exists(app, "/fusion-dashboard"):
        @app.route("/fusion-dashboard", endpoint="fusion_dashboard")
        def fusion_dashboard():
            try:
                return render_template("dashboard.html")
            except Exception:
                return "Fusion Dashboard page not available", 404

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
                        <li><a href="/api/agents">Agents API</a></li>
                    </ul>
                </body>
            </html>
            """, 200

    # Register Fusion API if available
    try:
        from src.api.fusion_api import fusion_bp
        app.register_blueprint(fusion_bp)
        print("✅ Fusion API blueprint registered")
    except Exception as e:
        print(f"⚠️ Fusion blueprint not registered: {e}")

    # Try to register Agents blueprint
    agents_registered = False
    try:
        from src.agents.api.agents import agents_bp
        app.register_blueprint(agents_bp, url_prefix="/api/agents")
        agents_registered = True
        print("✅ Agents API blueprint registered")
    except Exception as e:
        print(f"⚠️ Agents blueprint not registered: {e}")

    # If routes still missing for any reason, attach fallbacks
    if not _rule_exists(app, "/api/agents"):
        print("ℹ️ /api/agents not found in url_map — attaching fallback routes.")
        _attach_agents_fallback_routes(app)
    else:
        print("✅ /api/agents route present.")

    # --- SAFE STOP ROUTE (used by tests/utils/server_manager.py) ---
    if '__stop__' not in app.view_functions:
        @app.route("/__stop__", methods=["GET"])
        def __stop__():
            # Allows the test harness to stop the server if it locked the port
            from flask import request
            shutdown = request.environ.get('werkzeug.server.shutdown')
            if shutdown:
                shutdown()
            return "OK", 200

    # Log routes once to verify on boot
    try:
        rules = sorted([str(r.rule) for r in app.url_map.iter_rules()])
        app.logger.info("🔎 URL map:\n  " + "\n  ".join(rules))
    except Exception:
        pass

    return app
