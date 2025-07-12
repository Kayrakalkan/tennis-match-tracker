import os
from app import app

if __name__ == "__main__":
    # For development
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
else:
    # For production (gunicorn)
    application = app
