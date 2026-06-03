# 🐘 PostgreSQL Migration Guide

## Overview

This guide helps you migrate from SQLite (development) to PostgreSQL (production). The application supports both through environment configuration.

## Why PostgreSQL?

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Concurrent Users | Limited | Unlimited |
| Database Size | Max 2GB | Unlimited |
| ACID Compliance | Basic | Full |
| Scalability | Poor | Excellent |
| Production Ready | No | Yes ✅ |

## Step 1: Install PostgreSQL

### macOS
```bash
# Using Homebrew
brew install postgresql@15
brew services start postgresql@15

# Or with package installer
# Download from https://www.postgresql.org/download/
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Windows
Download installer from https://www.postgresql.org/download/windows/

## Step 2: Create Database & User

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Run these commands:
CREATE DATABASE goodchi_db;
CREATE USER goodchi_user WITH PASSWORD 'strong-secure-password';

# Configure user permissions
ALTER ROLE goodchi_user SET client_encoding TO 'utf8';
ALTER ROLE goodchi_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE goodchi_user SET default_transaction_deferrable TO on;
ALTER ROLE goodchi_user SET timezone TO 'UTC';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE goodchi_db TO goodchi_user;

# Exit
\q
```

### Verify Connection
```bash
psql -U goodchi_user -d goodchi_db -h localhost
# Should connect without password prompt (will ask for password)

\dt  # List tables (empty initially)
\q   # Exit
```

## Step 3: Update Application Configuration

### Update .env
```env
# Change from SQLite
# DATABASE_URL=sqlite:///goodchi.db

# To PostgreSQL
DATABASE_URL=postgresql://goodchi_user:strong-secure-password@localhost:5432/goodchi_db

# For remote PostgreSQL (Heroku, Railway, etc.)
# DATABASE_URL=postgresql://user:password@host:port/database
```

### Install PostgreSQL Driver
```bash
# Already in requirements.txt
pip install psycopg2-binary
```

## Step 4: Migrate Data (If existing SQLite database)

### Option A: Fresh Start (Recommended for new setup)
```bash
source venv/bin/activate
python
>>> from Goodchiwebsite import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()

# Then create admin user and seed data
python create_admin.py
python seed_db.py
```

### Option B: Migrate from SQLite to PostgreSQL

**Requirements**: Must have both databases configured

1. **Export SQLite Data to JSON**
   ```bash
   python
   >>> from Goodchiwebsite import app, db, User, Post, ContactMessage
   >>> import json
   >>>
   >>> with app.app_context():
   ...     users = [u.__dict__ for u in User.query.all()]
   ...     posts = [p.__dict__ for p in Post.query.all()]
   ...     messages = [m.__dict__ for m in ContactMessage.query.all()]
   ...
   ...     # Remove SQLAlchemy metadata
   ...     for u in users: u.pop('_sa_instance_state', None)
   ...     for p in posts: p.pop('_sa_instance_state', None)
   ...     for m in messages: m.pop('_sa_instance_state', None)
   ...
   ...     with open('migration_data.json', 'w') as f:
   ...         json.dump({'users': users, 'posts': posts, 'messages': messages}, f)
   >>> exit()
   ```

2. **Switch to PostgreSQL and Create Tables**
   ```bash
   python
   >>> from Goodchiwebsite import app, db
   >>> with app.app_context():
   ...     db.create_all()
   >>> exit()
   ```

3. **Import Data from JSON**
   ```python
   import json
   from Goodchiwebsite import app, db, User, Post, ContactMessage
   from datetime import datetime

   with open('migration_data.json', 'r') as f:
       data = json.load(f)

   with app.app_context():
       # Import users
       for user_data in data['users']:
           user = User(
               username=user_data['username'],
               email=user_data['email'],
               password_hash=user_data['password_hash'],
               is_admin=user_data.get('is_admin', False),
               created_at=datetime.fromisoformat(user_data.get('created_at', str(datetime.utcnow()))),
           )
           db.session.add(user)

       # Import posts
       for post_data in data['posts']:
           post = Post(
               slug=post_data['slug'],
               title=post_data['title'],
               excerpt=post_data['excerpt'],
               content=post_data['content'],
               date=post_data['date'],
               image=post_data['image'],
               created_at=datetime.fromisoformat(post_data.get('created_at', str(datetime.utcnow()))),
           )
           db.session.add(post)

       db.session.commit()
   ```

## Step 5: Initialize Database Tables

```bash
source venv/bin/activate
python
>>> from Goodchiwebsite import app, db
>>> with app.app_context():
...     db.create_all()
...     print("✅ Tables created successfully!")
>>> exit()
```

### Verify Tables Created
```bash
psql -U goodchi_user -d goodchi_db

# In psql:
\dt                    # List all tables
\d user                # Describe user table
\d post                # Describe post table
\d contact_message     # Describe contact_message table
\q
```

## Step 6: Test the Connection

```bash
python
>>> from Goodchiwebsite import app, db
>>> with app.app_context():
...     result = db.session.execute(db.text("SELECT 1"))
...     print("✅ PostgreSQL connection successful!")
>>> exit()
```

## Step 7: Backup & Recovery

### Create a Backup
```bash
# Full database backup
pg_dump -U goodchi_user goodchi_db > backup_$(date +%Y%m%d).sql

# Compressed backup
pg_dump -U goodchi_user goodchi_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore from Backup
```bash
# If you need to restore
psql -U goodchi_user goodchi_db < backup_20240101.sql

# Or from compressed backup
gunzip -c backup_20240101.sql.gz | psql -U goodchi_user goodchi_db
```

## Step 8: Connection Pooling (Production)

Connection pooling is already configured in the app:
```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
}
```

For high traffic, consider pgBouncer:
```bash
# Install
sudo apt install pgbouncer

# Configure /etc/pgbouncer/pgbouncer.ini
[databases]
goodchi_db = host=localhost port=5432 dbname=goodchi_db

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

## Remote PostgreSQL (Cloud Providers)

### Heroku PostgreSQL
```bash
# Heroku creates DATABASE_URL automatically
heroku config | grep DATABASE_URL
```

### AWS RDS
```env
DATABASE_URL=postgresql://user:password@mydb.123456.us-east-1.rds.amazonaws.com:5432/goodchi_db
```

### Railway PostgreSQL
```env
# Railway provides DATABASE_URL automatically in production
```

### DigitalOcean Managed PostgreSQL
```env
DATABASE_URL=postgresql://user:password@db-mysql-nyc3-1234.ondigitalocean.com:25060/goodchi_db?sslmode=require
```

## Troubleshooting

### Connection Error: "could not connect to server"
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Or on macOS
brew services list

# Verify credentials
psql -U goodchi_user -h localhost -d goodchi_db
```

### Error: "database does not exist"
```bash
# Create database if missing
sudo -u postgres createdb goodchi_db
```

### Error: "role does not exist"
```bash
# Create user role
sudo -u postgres psql
CREATE USER goodchi_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE goodchi_db TO goodchi_user;
\q
```

### Performance Slow
```bash
# Check indexes
psql -U goodchi_user goodchi_db
\d+ user
ANALYZE;
\q

# Increase work_mem in postgresql.conf
# shared_buffers = 256MB (for 1GB RAM)
```

### "Disk space full"
```bash
# Check database size
SELECT pg_size_pretty(pg_database_size('goodchi_db'));

# Vacuum and analyze
VACUUM ANALYZE;
```

## Maintenance Tasks

### Daily
- Monitor database size
- Check error logs

### Weekly
- Run VACUUM and ANALYZE
- Backup database

### Monthly
- Review slow queries
- Update statistics
- Check for unused indexes

### Quarterly
- Full database optimization
- Review backup restore process

## Performance Tuning

### Optimize PostgreSQL config (`postgresql.conf`)
```ini
# For 1GB RAM server
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### Create Indexes for Performance
```sql
-- Already created by application
-- But you can add more:

-- Index for login lookups
CREATE INDEX idx_user_username ON "user"(username);
CREATE INDEX idx_user_email ON "user"(email);

-- Index for post queries
CREATE INDEX idx_post_slug ON post(slug);

-- Index for contact messages
CREATE INDEX idx_contact_created_at ON contact_message(created_at DESC);
```

## Migration Complete ✅

Your application is now using PostgreSQL!

To verify:
1. Check connection: `psql -U goodchi_user -d goodchi_db`
2. Run app: `python Goodchiwebsite.py`
3. Login and create a post
4. Verify data in PostgreSQL: `SELECT COUNT(*) FROM post;`

---

**For issues or questions, refer to**:
- [PostgreSQL Official Docs](https://www.postgresql.org/docs/)
- [SQLAlchemy PostgreSQL Guide](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
