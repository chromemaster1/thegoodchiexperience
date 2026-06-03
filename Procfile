web: gunicorn -w 4 -b 0.0.0.0:$PORT wsgi:app
release: python -c "from Goodchiwebsite import app, db; app.app_context().push(); db.create_all()"
