import os
from src.wsgi import app

if __name__ == "__main__":
    # Avoid debug reloader spawning extra processes in CI/validators
    app.run(host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", "5000")),
            debug=False, use_reloader=False)