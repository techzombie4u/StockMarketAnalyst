
from src.core.app import create_app

if __name__ == "__main__":
    app = create_app()
    # IMPORTANT: reloader OFF and port forced to 5000 for validator
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
