import os
from app import app

# For production deployment (gunicorn, render, etc.)
application = app

if __name__ == "__main__":
    # For development only
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
