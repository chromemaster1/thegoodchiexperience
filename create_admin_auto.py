"""
Create admin non-interactively for development.
Reads ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD from environment, else uses defaults.
"""
import os
from Goodchiwebsite import app, db, User

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'adminpass123')

with app.app_context():
    existing = User.query.filter((User.username==ADMIN_USERNAME)|(User.email==ADMIN_EMAIL)).first()
    if existing:
        print(f"User already exists: {existing.username} ({existing.email})")
    else:
        user = User(username=ADMIN_USERNAME, email=ADMIN_EMAIL, is_admin=True)
        user.set_password(ADMIN_PASSWORD)
        db.session.add(user)
        db.session.commit()
        print(f"Created admin user: {ADMIN_USERNAME} / {ADMIN_EMAIL}")
