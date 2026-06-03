<<<<<<< HEAD
# TheGoodchiExperience
The Goodchi experience is a creative digital space created by the artist "Goodchi" to allow user experience a more immersive creative experience and also have fun while downloading or enjoying any of our art piece or stories. immerse yourself in a whole new world of redefined creativity. 
=======
# 🌟 The Goodchi Experience - Portfolio Web Application

A beautiful, production-ready web application for indie artists to showcase their creative works and journey. Built with Flask, featuring secure authentication, dynamic content management, and stunning astro-adventure themed UI.

## 🚀 Features

- **🔐 Secure Authentication System**
  - User registration with strong password requirements (8+ characters)
  - Login with rate limiting (5 attempts per minute)
  - CSRF protection on all forms
  - Session management with 24-hour timeout
  - Admin dashboard for content management

- **📝 Portfolio Management**
  - Create, edit, and delete posts
  - Rich content support with multimedia
  - Beautiful post galleries
  - Pagination support

- **✉️ Contact System**
  - Secure contact form with validation
  - Email notifications to admin
  - Message tracking and history

- **🎨 Responsive Design**
  - Mobile-friendly astro-adventure theme
  - Modern UI with cosmic styling
  - Interactive elements and animations

- **🛡️ Production Ready**
  - PostgreSQL database support
  - Gunicorn WSGI server configuration
  - Environment-based configuration
  - Security best practices implemented
  - Rate limiting and input validation

## 📋 System Requirements

- Python 3.8+
- PostgreSQL 12+ (for production)
- pip (Python package manager)

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd "the goodchi experience project"
```

### 2. Create Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
SECRET_KEY=your-very-secret-key-generate-a-strong-one
DATABASE_URL=sqlite:///goodchi.db  # For development
# DATABASE_URL=postgresql://user:password@localhost:5432/goodchi_db  # For production

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
ADMIN_EMAIL=your-email@gmail.com
```

### 5. Initialize Database
```bash
python
>>> from Goodchiwebsite import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### 6. Create Admin User
```bash
python create_admin.py
# Follow the prompts to create an admin account
```

### 7. Seed Sample Data (Optional)
```bash
python seed_db.py
```

## 🏃 Running Locally

### Development Mode
```bash
python Goodchiwebsite.py
# Visit http://localhost:5000
```

### Production Mode with Gunicorn
```bash
# Install Gunicorn (included in requirements.txt)
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app

# With more options:
gunicorn -w 4 -b 0.0.0.0:8000 --timeout 60 --access-logfile - wsgi:app
```

## 🐘 PostgreSQL Setup (Production)

### macOS with Homebrew
```bash
brew install postgresql@15
brew services start postgresql@15

# Create database and user
psql postgres
CREATE DATABASE goodchi_db;
CREATE USER goodchi_user WITH PASSWORD 'secure-password';
ALTER ROLE goodchi_user SET client_encoding TO 'utf8';
ALTER ROLE goodchi_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE goodchi_user SET default_transaction_deferrable TO on;
ALTER ROLE goodchi_user SET default_transaction_read_committed TO on;
GRANT ALL PRIVILEGES ON DATABASE goodchi_db TO goodchi_user;
\q
```

### Update .env
```env
DATABASE_URL=postgresql://goodchi_user:secure-password@localhost:5432/goodchi_db
```

### Initialize PostgreSQL Database
```bash
python
>>> from Goodchiwebsite import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

## 📝 Configuration Guide

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `your-long-random-string` |
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@localhost/db` |
| `MAIL_SERVER` | SMTP server for emails | `smtp.gmail.com` |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USERNAME` | Email account for notifications | `your-email@gmail.com` |
| `MAIL_PASSWORD` | Email password or app password | `your-app-password` |
| `ADMIN_EMAIL` | Admin email for notifications | `admin@example.com` |
| `FLASK_ENV` | Environment mode | `production` or `development` |
| `SESSION_COOKIE_SECURE` | Use secure cookies with HTTPS | `True` |

## 🚢 Deployment

### Heroku Deployment

1. **Install Heroku CLI** and login
   ```bash
   heroku login
   ```

2. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

3. **Add PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

4. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set FLASK_ENV=production
   heroku config:set SESSION_COOKIE_SECURE=True
   ```

5. **Deploy**
   ```bash
   git push heroku main
   heroku run python
   >>> from Goodchiwebsite import app, db
   >>> with app.app_context():
   ...     db.create_all()
   >>> exit()
   ```

### Railway Deployment

1. Connect your GitHub repository
2. Add PostgreSQL plugin
3. Set environment variables in Railway dashboard
4. Deploy automatically on push

### Self-Hosted with Nginx + Gunicorn

1. **Install Nginx and Gunicorn** (already in requirements.txt)

2. **Create Systemd service** (`/etc/systemd/system/goodchi.service`):
   ```ini
   [Unit]
   Description=Goodchi Experience Flask App
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/goodchi
   ExecStart=/var/www/goodchi/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. **Configure Nginx** as reverse proxy:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

4. **Enable SSL with Certbot**:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

## 🔐 Security Checklist

- [x] CSRF protection enabled on all forms
- [x] Password hashing with PBKDF2:SHA256
- [x] Rate limiting on login endpoint
- [x] Input validation and sanitization
- [x] HTTPS/SSL support configured
- [x] Secure session cookies (HTTPOnly, SameSite)
- [x] Environment-based configuration
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] XSS protection in templates
- [x] Admin authentication required

## 🗄️ Database Schema

### Users Table
- `id` (Primary Key)
- `username` (Unique)
- `email` (Unique)
- `password_hash`
- `created_at`, `updated_at`
- `is_admin`
- `last_login`

### Posts Table
- `id` (Primary Key)
- `slug` (Unique)
- `title`
- `excerpt`
- `content`
- `date`
- `image`
- `created_at`, `updated_at`

### ContactMessages Table
- `id` (Primary Key)
- `name`
- `email`
- `message`
- `user_id` (Foreign Key)
- `created_at`
- `is_read`

## 🤝 Admin Features

### Access Admin Panel
1. Log in with admin account
2. Click "⚙️ Admin Panel" in navigation
3. Manage posts:
   - Create new posts
   - Edit existing posts
   - Delete posts
   - View all posts

## 🐛 Troubleshooting

### "SECRET_KEY not properly configured"
**Solution**: Generate a secure key and add to `.env`:
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Database Connection Error
**Solution**: Verify `DATABASE_URL` in `.env` and ensure database service is running

### Email Not Sending
**Solution**:
- For Gmail: Use an [App Password](https://support.google.com/accounts/answer/185833)
- Verify SMTP settings in `.env`
- Check email logs: `heroku logs --tail`

### Rate Limiting Too Strict
**Solution**: Modify rate limit in `login()` route in `Goodchiwebsite.py`:
```python
@limiter.limit("10 per minute")  # Change this value
```

## 📚 Project Structure

```
the goodchi experience project/
├── Goodchiwebsite.py           # Main Flask application
├── wsgi.py                     # WSGI entry point for Gunicorn
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .env                        # Environment configuration (not in git)
├── create_admin.py             # Admin user creation script
├── seed_db.py                  # Database seeding script
├── static/
│   ├── assets/
│   │   ├── css/
│   │   │   ├── styles.css      # Main stylesheet
│   │   │   └── noscript.css    # No-JS fallback
│   │   └── images/             # Static images
│   └── [other assets]
├── templates/
│   ├── base.html               # Base template
│   ├── index.html              # Home page
│   ├── login.html              # Login form
│   ├── register.html           # Registration form
│   ├── post.html               # Post detail page
│   ├── about.html              # About page
│   ├── contact us.html         # Contact form
│   ├── download.html           # Download page
│   └── admin/
│       ├── posts.html          # Admin posts list
│       ├── new_post.html       # Create post form
│       └── edit_post.html      # Edit post form
├── instance/                   # Instance-specific files (not in git)
└── audio file/                 # Audio files directory
```

## 🔄 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Yes | Home page with posts |
| GET | `/post/<slug>` | Yes | View individual post |
| GET/POST | `/register` | No | User registration |
| GET/POST | `/login` | No | User login |
| GET | `/logout` | Yes | User logout |
| GET/POST | `/contact` | Yes | Contact form |
| GET | `/about` | Yes | About page |
| GET | `/download` | Yes | Download page |
| GET | `/admin/posts` | Admin | All posts management |
| GET/POST | `/admin/post/new` | Admin | Create new post |
| GET/POST | `/admin/post/<id>/edit` | Admin | Edit post |
| POST | `/admin/post/<id>/delete` | Admin | Delete post |

## 📞 Support & Contact

For inquiries and collaborations:
- 📧 Email: gchibueze96@gmail.com
- 🐦 Twitter: [@iam_ggmusic](https://x.com/iam_ggmusic)
- 📸 Instagram: [@Goodchi_thesound](https://instagram.com/Goodchi_thesound)
- 💬 WhatsApp: +234-703-220-5608

## 📄 License

This project is created for The Goodchi Experience. All rights reserved.

## 🙏 Acknowledgments

- Built with Flask and Flask-SQLAlchemy
- Astro-adventure theme design
- Community feedback and support

---

**Last Updated**: June 2026
**Status**: Production Ready ✅
**Version**: 2.0
>>>>>>> 42987fb (feat: push full project includig static files)
