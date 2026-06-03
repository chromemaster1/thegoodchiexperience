# 🚀 Deployment Guide

## Quick Start for Production

### Prerequisites
- Git repository set up
- PostgreSQL database created
- Domain name (optional)

### Option 1: Heroku (Easiest for Beginners)

1. **Install Heroku CLI**
   ```bash
   brew tap heroku/brew && brew install heroku
   heroku login
   ```

2. **Create and Deploy**
   ```bash
   heroku create your-goodchi-app
   heroku addons:create heroku-postgresql:hobby-dev
   git push heroku main
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
   heroku config:set FLASK_ENV=production
   heroku config:set SESSION_COOKIE_SECURE=True
   heroku config:set MAIL_USERNAME=your-email@gmail.com
   heroku config:set MAIL_PASSWORD=your-app-password
   ```

4. **Initialize Database**
   ```bash
   heroku run python
   >>> from Goodchiwebsite import app, db
   >>> with app.app_context():
   ...     db.create_all()
   >>> exit()
   ```

5. **Create Admin User**
   ```bash
   heroku run python create_admin.py
   ```

### Option 2: Railway (GitHub Integration)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Production ready"
   git push origin main
   ```

2. **Connect Railway**
   - Go to railway.app
   - Create new project
   - Connect your GitHub repo
   - Add PostgreSQL plugin
   - Set environment variables

3. **Deploy**
   - Railway auto-deploys on push

### Option 3: Self-Hosted (DigitalOcean/Linode)

1. **Setup Server**
   ```bash
   # SSH into server
   ssh root@your_server_ip

   # Install dependencies
   apt update && apt upgrade -y
   apt install -y python3-pip python3-venv postgresql nginx certbot python3-certbot-nginx git
   ```

2. **Clone Repository**
   ```bash
   cd /var/www
   git clone your-repo goodchi
   cd goodchi
   ```

3. **Setup Python Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Setup PostgreSQL**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE goodchi_db;
   CREATE USER goodchi_user WITH PASSWORD 'strong-password';
   ALTER ROLE goodchi_user SET client_encoding TO 'utf8';
   ALTER ROLE goodchi_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE goodchi_user SET default_transaction_deferrable TO on;
   GRANT ALL PRIVILEGES ON DATABASE goodchi_db TO goodchi_user;
   \q
   ```

5. **Create .env File**
   ```bash
   nano .env
   # Add all your environment variables
   ```

6. **Initialize Database**
   ```bash
   source venv/bin/activate
   python -c "from Goodchiwebsite import app, db; app.app_context().push(); db.create_all()"
   ```

7. **Create Systemd Service**
   ```bash
   sudo nano /etc/systemd/system/goodchi.service
   ```

   Add:
   ```ini
   [Unit]
   Description=Goodchi Experience Flask App
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/goodchi
   Environment="PATH=/var/www/goodchi/venv/bin"
   ExecStart=/var/www/goodchi/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 --timeout 60 wsgi:app
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

8. **Enable Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable goodchi
   sudo systemctl start goodchi
   ```

9. **Setup Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/goodchi
   ```

   Add:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       # Increase upload size for images
       client_max_body_size 50M;
   }
   ```

10. **Enable Nginx Site**
    ```bash
    sudo ln -s /etc/nginx/sites-available/goodchi /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

11. **Setup SSL with Certbot**
    ```bash
    sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
    ```

### Option 4: Docker (Advanced)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "wsgi:app"]
```

Build and run:
```bash
docker build -t goodchi .
docker run -p 8000:8000 --env-file .env goodchi
```

## Environment Variables for Production

```env
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/goodchi_db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@example.com
SESSION_COOKIE_SECURE=True
```

## Database Backups

### PostgreSQL Backup
```bash
# Backup
pg_dump goodchi_db > backup_$(date +%Y%m%d).sql

# Restore
psql goodchi_db < backup_20240101.sql
```

### Automated Daily Backups
Create `/usr/local/bin/backup-db.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/goodchi"
mkdir -p $BACKUP_DIR
pg_dump goodchi_db | gzip > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-db.sh
```

## Monitoring & Logs

### View Application Logs
```bash
# Systemd logs
sudo journalctl -u goodchi -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Troubleshooting

### Secret Key Error
Generate a new one:
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Database Connection Issues
Check PostgreSQL status:
```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "\l"  # List databases
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

## Performance Tips

1. **Enable Gzip Compression**
   ```nginx
   gzip on;
   gzip_types text/plain text/css text/javascript application/json;
   ```

2. **Add Caching Headers**
   ```nginx
   location /static {
       expires 30d;
       add_header Cache-Control "public, immutable";
   }
   ```

3. **Optimize Gunicorn Workers**
   ```bash
   # For 4GB RAM: typically 4-8 workers
   gunicorn -w 8 -b 0.0.0.0:8000 wsgi:app
   ```

4. **Enable Database Connection Pooling**
   Already configured in `Goodchiwebsite.py`

## Security Hardening

✅ HTTPS/SSL enabled
✅ Strong password hashing (PBKDF2)
✅ CSRF protection on all forms
✅ Rate limiting on login
✅ Secure session cookies
✅ Environment-based secrets
✅ SQL injection prevention (SQLAlchemy ORM)

---

For more help, check the main README.md
