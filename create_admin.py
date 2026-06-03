#!/usr/bin/env python3
"""
Create Admin User Script
Run this to create an admin user for the Goodchi website.
"""

from Goodchiwebsite import app, db, User

def create_admin_user():
    username = input("Enter admin username: ").strip()
    email = input("Enter admin email: ").strip()
    password = input("Enter admin password: ").strip()

    if not all([username, email, password]):
        print("❌ All fields are required!")
        return

    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            print(f"❌ User with username '{username}' or email '{email}' already exists!")
            return

        # Create admin user
        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        print(f"✅ Admin user '{username}' created successfully!")
        print("You can now login and access the Admin Panel from the navigation menu.")

if __name__ == '__main__':
    create_admin_user()
