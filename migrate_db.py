"""
migrate_db.py  —  Goodchi Experience
======================================
Adds new columns to existing tables WITHOUT dropping any data.
Safe to run multiple times — skips columns that already exist.

Run once:
    python migrate_db.py

Then restart your app.
"""

from Goodchiwebsite import app, db
import sqlalchemy as sa
from sqlalchemy import text, inspect


def column_exists(conn, table, column):
    """Return True if column already exists in table."""
    inspector = inspect(conn)
    cols = [c['name'] for c in inspector.get_columns(table)]
    return column in cols


def migrate():
    with app.app_context():
        conn = db.engine.connect()

        migrations = [
            # (table_name, column_name, column_definition)
            ('contact_message', 'is_closed', 'BOOLEAN DEFAULT 0 NOT NULL'),
            ('contact_message', 'subject',   'VARCHAR(200)'),

            # contact_reply table — created fresh by db.create_all() if missing
            # password_reset_token — same

            # These User columns may also be missing if you're on an old DB
            ('user', 'bio',                 'TEXT'),
            ('user', 'avatar',              'VARCHAR(256)'),
            ('user', 'notif_new_posts',     'BOOLEAN DEFAULT 1 NOT NULL'),
            ('user', 'notif_new_music',     'BOOLEAN DEFAULT 1 NOT NULL'),
            ('user', 'notif_announcements', 'BOOLEAN DEFAULT 1 NOT NULL'),
            ('user', 'notif_email',         'BOOLEAN DEFAULT 0 NOT NULL'),
            ('user', 'totp_secret',         'VARCHAR(32)'),
            ('user', 'totp_enabled',        'BOOLEAN DEFAULT 0 NOT NULL'),
            ('user', 'totp_pending',        'VARCHAR(32)'),
        ]

        added   = 0
        skipped = 0

        for table, col, definition in migrations:
            try:
                if column_exists(conn, table, col):
                    print(f"  · skip   {table}.{col}  (already exists)")
                    skipped += 1
                else:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {definition}'))
                    conn.commit()
                    print(f"  + added  {table}.{col}")
                    added += 1
            except Exception as e:
                print(f"  ! error  {table}.{col}: {e}")

        conn.close()

        # Create any brand-new tables (contact_reply, password_reset_token, etc.)
        print("\nCreating any missing tables...")
        db.create_all()

        print(f"\n✓ Migration complete — {added} column(s) added, {skipped} already present.")
        print("  Restart your Flask app now.\n")


if __name__ == '__main__':
    migrate()
