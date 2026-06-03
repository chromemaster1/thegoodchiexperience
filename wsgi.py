"""
WSGI application entry point for Gunicorn.
This file allows the application to be served by Gunicorn in production.
"""

from Goodchiwebsite import app, db

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
