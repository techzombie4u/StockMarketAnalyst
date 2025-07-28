
from app import app

# Simple WSGI application without heavy initialization
application = app

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000)
