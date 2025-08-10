
import os
import sys
import traceback
from flask import Flask, jsonify, render_template

def create_app():
    """Create and configure Flask app with error handling"""
    
    try:
        # Set up paths
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        
        print(f"📂 Base directory: {base}")
        print(f"📂 Template folder: {os.path.join(base, 'web', 'templates')}")
        print(f"📂 Static folder: {os.path.join(base, 'web', 'static')}")
        
        # Create Flask app
        app = Flask(
            __name__,
            template_folder=os.path.join(base, "web", "templates"),
            static_folder=os.path.join(base, "web", "static"),
        )

        @app.route("/healthz")
        def healthz():
            return jsonify({"status": "ok", "message": "Flask server is running"}), 200

        # Register Fusion API with error handling
        try:
            print("🔗 Registering Fusion API blueprint...")
            from src.api.fusion_api import fusion_bp
            app.register_blueprint(fusion_bp)
            print("✅ Fusion API blueprint registered successfully")
        except Exception as e:
            print(f"⚠️  Fusion blueprint failed to import: {e}")
            traceback.print_exc()
            
            # Add error route for debugging
            @app.route("/fusion-import-error")
            def fusion_import_error():
                return jsonify({
                    "error": "Fusion blueprint failed to import", 
                    "details": str(e),
                    "status": "error"
                }), 500

        # HTML page for validator smoke test
        @app.route("/fusion-dashboard")
        def fusion_dashboard_page():
            try:
                return render_template("fusion_dashboard.html")
            except Exception as e:
                print(f"⚠️  Template rendering error: {e}")
                return f"Template error: {e}", 500

        # Root route for basic testing
        @app.route("/")
        def index():
            return jsonify({
                "message": "Flask server is running",
                "status": "ok",
                "endpoints": {
                    "health": "/healthz",
                    "fusion_dashboard": "/fusion-dashboard",
                    "fusion_api": "/api/fusion/dashboard"
                }
            })

        print("✅ Flask app created successfully with all routes")
        return app
        
    except Exception as e:
        print(f"❌ Error creating Flask app: {e}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
