from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from datetime import datetime, timedelta
from functools import wraps
import os
from dotenv import load_dotenv
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_limiter.util import get_remote_address
from email_validator import validate_email, EmailNotValidError
import secrets as _secrets
import pyotp
import qrcode
import io
import base64



load_dotenv()

app = Flask(__name__)

# Security: Use environment variable for SECRET_KEY, raise error if not set
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("ERROR: SECRET_KEY not properly configured. Set it in your .env file!")
app.config['SECRET_KEY'] = SECRET_KEY

# Database configuration - supports both SQLite (dev) and PostgreSQL (production)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///goodchi.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
}

_db_url = (
    os.getenv('DATABASE_URL') or
    os.getenv('SQLALCHEMY_DATABASE_URI') or
    'sqlite:///goodchi.db'
)
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['ADMIN_EMAIL'] = os.getenv('ADMIN_EMAIL', 'admin@thegoodchiexperience.com')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config.get('MAIL_USERNAME'))

# # Session configuration - add timeout
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')  # True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Warning.'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)
    bio             = db.Column(db.Text,    nullable=True)
    avatar          = db.Column(db.String(256), nullable=True)
    notif_new_posts     = db.Column(db.Boolean, default=True)
    notif_new_music     = db.Column(db.Boolean, default=True)
    notif_announcements = db.Column(db.Boolean, default=True)
    notif_email         = db.Column(db.Boolean, default=False)
    totp_secret     = db.Column(db.String(32), nullable=True)
    totp_enabled    = db.Column(db.Boolean, default=False)
    totp_pending    = db.Column(db.String(32), nullable=True)   # secret shown during setup
    notifications   = db.relationship('Notification', backref='user', lazy=True, cascade='all,delete')
    login_history   = db.relationship('LoginHistory',  backref='user', lazy=True, cascade='all,delete')

    def set_password(self, password):
        """Hash password with strict requirements"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'

class ContactMessage(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_read    = db.Column(db.Boolean, default=False)
    is_closed  = db.Column(db.Boolean, default=False)
    subject    = db.Column(db.String(200), nullable=True)
    replies    = db.relationship('ContactReply', backref='ticket', lazy=True,
                                 cascade='all,delete', order_by='ContactReply.created_at')

    def __repr__(self):
        return f'<ContactMessage {self.name} - {self.created_at}>'


class ContactReply(db.Model):
    __tablename__ = 'contact_reply'
    id             = db.Column(db.Integer, primary_key=True)
    ticket_id      = db.Column(db.Integer, db.ForeignKey('contact_message.id'), nullable=False)
    author_id      = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body           = db.Column(db.Text, nullable=False)
    is_admin_reply = db.Column(db.Boolean, default=False)
    read_by_user   = db.Column(db.Boolean, default=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    author         = db.relationship('User', backref='contact_replies', lazy=True)


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_token'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token      = db.Column(db.String(128), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used       = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user       = db.relationship('User', backref='reset_tokens', lazy=True)

    @property
    def is_valid(self):
        return not self.used and datetime.utcnow() < self.expires_at
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    excerpt = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Post {self.title}>'

class DownloadItem(db.Model):
    __tablename__ = 'download_item'
    id             = db.Column(db.Integer,  primary_key=True)
    title          = db.Column(db.String(200), nullable=False)
    artist         = db.Column(db.String(200), nullable=True)
    album          = db.Column(db.String(200), nullable=True)
    producer       = db.Column(db.String(200), nullable=True)
    description    = db.Column(db.Text,       nullable=True)
    audio_path     = db.Column(db.String(512), nullable=False)   # relative to static/
    stream_url     = db.Column(db.String(512), nullable=True)
    sort_order     = db.Column(db.Integer, default=0)
    requires_login = db.Column(db.Boolean, default=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notification'
    id         = db.Column(db.Integer,  primary_key=True)
    user_id    = db.Column(db.Integer,  db.ForeignKey('user.id'), nullable=False)
    type       = db.Column(db.String(50),  default='announcement')   # new_post | new_music | announcement
    title      = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text,        nullable=False)
    link       = db.Column(db.String(512), nullable=True)
    read       = db.Column(db.Boolean,     default=False)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

class BroadcastLog(db.Model):
    __tablename__ = 'broadcast_log'
    id              = db.Column(db.Integer, primary_key=True)
    notif_type      = db.Column(db.String(50))
    title           = db.Column(db.String(200))
    message         = db.Column(db.Text)
    link            = db.Column(db.String(512), nullable=True)
    recipient_count = db.Column(db.Integer, default=0)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

class LoginHistory(db.Model):
    __tablename__ = 'login_history'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ip_address = db.Column(db.String(64), nullable=True)
    success    = db.Column(db.Boolean, default=True)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)

class SupportPayment(db.Model):
    """Tracks every 'pay what you want' support payment."""
    __tablename__ = 'support_payment'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    supporter_name = db.Column(db.String(120), nullable=True)
    email          = db.Column(db.String(120), nullable=True)
    amount         = db.Column(db.Float, nullable=False)
    method         = db.Column(db.String(20), nullable=False, default='card')  # card|crypto|bank
    reference      = db.Column(db.String(64), nullable=True, unique=True)
    stripe_pi_id   = db.Column(db.String(120), nullable=True)
    status         = db.Column(db.String(20), nullable=False, default='pending')  # pending|completed|failed
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    user           = db.relationship('User', backref='payments', lazy=True)


class BankDetail(db.Model):
    """Bank accounts for the Support page — admin-managed, no code change needed."""
    __tablename__ = 'bank_detail'
    id             = db.Column(db.Integer, primary_key=True)
    bank_name      = db.Column(db.String(120), nullable=False)
    account_name   = db.Column(db.String(120), nullable=False)
    account_number = db.Column(db.String(40),  nullable=False)
    sort_code      = db.Column(db.String(40),  nullable=True)
    iban           = db.Column(db.String(80),  nullable=True)
    swift          = db.Column(db.String(20),  nullable=True)
    country        = db.Column(db.String(60),  nullable=True)
    is_active      = db.Column(db.Boolean, default=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)


class CryptoWallet(db.Model):
    """Crypto wallet addresses for the Support page — admin-managed."""
    __tablename__ = 'crypto_wallet'
    id         = db.Column(db.Integer, primary_key=True)
    label      = db.Column(db.String(80),  nullable=False)   # e.g. "Bitcoin (BTC)"
    network    = db.Column(db.String(80),  nullable=True)    # e.g. "Bitcoin Mainnet"
    address    = db.Column(db.String(200), nullable=False)
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# WTForms for validation and CSRF protection
class RegistrationForm(FlaskForm):
    """User registration form with validation"""
    username = StringField('Username', validators=[
        DataRequired("Username is required"),
        Length(min=3, max=80, message="Username must be between 3 and 80 characters")
    ])
    email = StringField('Email', validators=[
        DataRequired("Email is required"),
        Email("Invalid email address")
    ])
    password = PasswordField('Password', validators=[
        DataRequired("Password is required"),
        Length(min=8, message="Password must be at least 8 characters")
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired("Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Register')

    def validate_username(self, field):
        """Check if username already exists"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already taken")

    def validate_email(self, field):
        """Check if email already registered and validate format"""
        try:
            validate_email(field.data)
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email: {str(e)}")

        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered")


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[DataRequired("Username is required")])
    password = PasswordField('Password', validators=[DataRequired("Password is required")])
    submit = SubmitField('Login')


class ContactForm(FlaskForm):
    """Contact message form"""
    name = StringField('Name', validators=[
        DataRequired("Name is required"),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters")
    ])
    email = StringField('Email', validators=[
        DataRequired("Email is required"),
        Email("Invalid email address")
    ])
    message = TextAreaField('Message', validators=[
        DataRequired("Message is required"),
        Length(min=10, max=5000, message="Message must be between 10 and 5000 characters")
    ])
    submit = SubmitField('Send Message')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_notif_count():
    count = 0
    if current_user.is_authenticated:
        count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    return dict(unread_notification_count=count)

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('❌ You need admin privileges to access this page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def send_contact_notification(contact_message):
    """Send email notification to admin about new contact message"""
    try:
        msg = Message(
            subject=f'New Contact Form Submission from {contact_message.name}',
            recipients=[app.config['ADMIN_EMAIL']],
            body=f"""
                New message from: {contact_message.name}
                Email: {contact_message.email}
                Date: {contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}

                Message:
                {contact_message.message}
                            """,
                            html=f"""
                <h2>New Contact Form Submission</h2>
                <p><strong>From:</strong> {contact_message.name}</p>
                <p><strong>Email:</strong> <a href="mailto:{contact_message.email}">{contact_message.email}</a></p>
                <p><strong>Date:</strong> {contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <h3>Message:</h3>
                <p>{contact_message.message.replace(chr(10), '<br>')}</p>
            """
        )
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

# Authentication Routes

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration with form validation"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            flash('✅ Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except ValueError as e:
            flash(f'❌ {str(e)}', 'danger')
            db.session.rollback()
        except Exception as e:
            flash(f'❌ Registration failed. Please try again.', 'danger')
            db.session.rollback()

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with form validation and feedback"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            history = LoginHistory(
                user_id    = user.id,
                ip_address = request.remote_addr,
                success    = True
            )
            db.session.add(history)
            db.session.commit()

            # If 2FA is enabled, redirect to 2FA verify step instead of logging in fully
            if user.totp_enabled:
                session['totp_user_id'] = user.id          # temporary — not fully logged in yet
                return redirect(url_for('verify_2fa_login'))
            login_user(user)
            user.update_last_login()
            flash(f'✅ Welcome back, {user.username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('❌ Invalid username or password.', 'danger')

    return render_template('login.html', form=form)

# ── 2FA login step ────────────────────────────────────────────
@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa_login():
    user_id = session.get('totp_user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get_or_404(user_id)
    error = None
    if request.method == 'POST':
        code = request.form.get('totp_code', '').strip()
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code, valid_window=1):
            session.pop('totp_user_id', None)
            login_user(user)
            return redirect(url_for('home'))
        error = 'Invalid code — try again.'
    return render_template('verify_2fa.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('👋 You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required  # PROTECTED: Users must log in to access home page
def home():
    """Home page - showcasing all posts (login required)"""
    page  = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.id.desc()).paginate(page=page, per_page=6)
    unread = 0
    if current_user.is_authenticated:
        unread = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    return render_template('index.html',
        posts               = posts.items,
        pagination          = posts,
        unread_notifications= unread,
    )
@app.route('/post/<slug>')
@login_required  # PROTECTED: User must be logged in to view posts
def post(slug):
    """Display individual post"""
    post = Post.query.filter_by(slug=slug).first_or_404()

    genesis_songs = None
    genesis_gallery = None

    # Note: This hardcoded logic should ideally be moved to database in future
    if post.slug == 'genesis-ep-project':
        if post.image != 'images/genesis-art.jpeg':
            post.image = 'images/genesis-art.jpeg'
            db.session.commit()

        genesis_songs = [
            {
                'title': '247pnb',
                'listen_url': url_for('download'),
                'download_url': url_for('download'),
                'video_links': [
                    {'label': '247pnb Official Video', 'url': 'https://youtu.be/0B7rEblVepM?si=FGa_1tbnFA7Qttb3'},
                ]
            },
            {
                'title': 'Sticks n Bones',
                'listen_url': url_for('download'),
                'download_url': url_for('download'),
                'video_links': [
                    {'label': 'Sticks n Bones Official Video', 'url': 'https://youtube.com/shorts/YOk-jRM5d1s?si=7haab0eX_YDQDCIS'},
                    {'label': 'Reels Sticks n Bones', 'url': 'https://youtube.com/shorts/E7d57WegbO0?si=O0s-VDFuzSrFfH12'}
                ]
            },
            {
                'title': 'Say Your Mine',
                'listen_url': url_for('download'),
                'download_url': url_for('download'),
                'video_links': [
                    {'label': 'Say Your Mine Official', 'url': 'https://youtube.com/shorts/LjjBiOk_Uts?si=J0QLIZGZxbWNAFC7'}
                ]
            }
        ]

        genesis_gallery = [
            'images/247pnb shoot16.jpeg',
            'images/sticks n bones shoot.jpeg',
            'images/say your mind photoshoot.jpeg',
            'images/genesis-art-photoshoot.jpeg',
            'images/genesis-art.jpeg'
        ]

    return render_template("post.html", post=post, genesis_songs=genesis_songs, genesis_gallery=genesis_gallery)

@app.route('/download')
@login_required
def download():
    items = DownloadItem.query.order_by(DownloadItem.sort_order, DownloadItem.created_at).all()
    return render_template('download.html', download_items=items)

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    """Handle contact form submissions"""
    form = ContactForm()
    if form.validate_on_submit():
        try:
            contact_msg = ContactMessage(
                name=form.name.data,
                email=form.email.data,
                message=form.message.data,
                user_id=current_user.id
            )
            db.session.add(contact_msg)
            db.session.commit()

            send_contact_notification(contact_msg)

            flash('✅ Your message has been sent successfully!', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            flash(f'❌ Failed to send message. Please try again.', 'danger')
            db.session.rollback()

    return render_template("contact us.html", form=form)

@app.route('/about')
@login_required  # PROTECTED: User must be logged in
def about():
    """About page"""
    return render_template("about.html")

# ── Settings: main page (redirects to profile tab) ────────────
@app.route('/settings')
@login_required
def settings():
    return redirect(url_for('settings_profile'))


@app.route('/settings/profile', methods=['GET', 'POST'])
@login_required
def settings_profile():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        bio      = request.form.get('bio', '').strip()
        avatar   = request.form.get('avatar', '').strip()

        # Check uniqueness (excluding self)
        if username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('Username already taken.', 'error')
                return redirect(url_for('settings_profile') + '#profile')
        if email != current_user.email:
            if User.query.filter_by(email=email).first():
                flash('Email already in use.', 'error')
                return redirect(url_for('settings_profile') + '#profile')

        current_user.username = username
        current_user.email    = email
        current_user.bio      = bio
        current_user.avatar   = avatar or None
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('settings_profile') + '#profile')

    notifications = Notification.query.filter_by(user_id=current_user.id)\
                                      .order_by(Notification.created_at.desc()).limit(20).all()
    login_history  = LoginHistory.query.filter_by(user_id=current_user.id)\
                                       .order_by(LoginHistory.timestamp.desc()).limit(10).all()
    unread         = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    show_qr        = False
    qr_image       = None
    totp_secret    = None

    return render_template('settings.html',
        notifications       = notifications,
        login_history       = login_history,
        unread_notifications= unread,
        show_qr             = show_qr,
        qr_image            = qr_image,
        totp_secret         = totp_secret,
    )


@app.route('/settings/password', methods=['POST'])
@login_required
def settings_password():
    current_pw  = request.form.get('current_password', '')
    new_pw      = request.form.get('new_password', '')
    confirm_pw  = request.form.get('confirm_password', '')

    if not current_user.check_password(current_pw):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('settings_profile') + '#password')
    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('settings_profile') + '#password')
    if len(new_pw) < 8:
        flash('Password must be at least 8 characters.', 'error')
        return redirect(url_for('settings_profile') + '#password')

    current_user.set_password(new_pw)
    db.session.commit()
    flash('Password updated successfully.', 'success')
    return redirect(url_for('settings_profile') + '#password')


@app.route('/settings/notifications', methods=['POST'])
@login_required
def settings_notifications():
    current_user.notif_new_posts     = 'notif_new_posts'     in request.form
    current_user.notif_new_music     = 'notif_new_music'     in request.form
    current_user.notif_announcements = 'notif_announcements' in request.form
    current_user.notif_email         = 'notif_email'         in request.form
    db.session.commit()
    flash('Notification preferences saved.', 'success')
    return redirect(url_for('settings_profile') + '#notifications')


# ── 2FA Setup ─────────────────────────────────────────────────
@app.route('/settings/enable-2fa', methods=['POST'])
@login_required
def settings_enable_2fa():
    secret = pyotp.random_base32()
    current_user.totp_pending = secret
    db.session.commit()

    totp     = pyotp.TOTP(secret)
    otp_uri  = totp.provisioning_uri(name=current_user.email, issuer_name='Goodchi Experience')
    img      = qrcode.make(otp_uri)
    buf      = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64   = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

    notifications = Notification.query.filter_by(user_id=current_user.id)\
                                      .order_by(Notification.created_at.desc()).limit(20).all()
    login_history  = LoginHistory.query.filter_by(user_id=current_user.id)\
                                       .order_by(LoginHistory.timestamp.desc()).limit(10).all()
    unread         = Notification.query.filter_by(user_id=current_user.id, read=False).count()

    return render_template('settings.html',
        notifications       = notifications,
        login_history       = login_history,
        unread_notifications= unread,
        show_qr             = True,
        qr_image            = qr_b64,
        totp_secret         = secret,
    )


@app.route('/settings/verify-2fa', methods=['POST'])
@login_required
def settings_verify_2fa():
    code   = request.form.get('totp_code', '').strip()
    secret = current_user.totp_pending
    if not secret:
        flash('No pending 2FA setup.', 'error')
        return redirect(url_for('settings_profile') + '#security')
    totp = pyotp.TOTP(secret)
    if totp.verify(code, valid_window=1):
        current_user.totp_secret  = secret
        current_user.totp_pending = None
        current_user.totp_enabled = True
        db.session.commit()
        flash('Two-factor authentication is now active.', 'success')
    else:
        flash('Invalid code. Please try again.', 'error')
    return redirect(url_for('settings_profile') + '#security')


@app.route('/settings/disable-2fa', methods=['POST'])
@login_required
def settings_disable_2fa():
    current_user.totp_enabled = False
    current_user.totp_secret  = None
    current_user.totp_pending = None
    db.session.commit()
    flash('Two-factor authentication has been disabled.', 'success')
    return redirect(url_for('settings_profile') + '#security')

# ── Notification inbox ────────────────────────────────────────
@app.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id)\
                               .order_by(Notification.created_at.desc()).all()
    # Mark all as read when viewed
    for n in notifs:
        n.read = True
    db.session.commit()
    return render_template('notifications.html', notifications=notifs)


@app.route('/notifications/mark-read', methods=['POST'])
@login_required
def notifications_mark_read():
    Notification.query.filter_by(user_id=current_user.id, read=False)\
                      .update({'read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications'))


@app.route('/notifications/clear', methods=['POST'])
@login_required
def notifications_clear():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Notifications cleared.', 'success')
    return redirect(url_for('notifications'))


@app.route('/notifications/<int:notif_id>/delete', methods=['POST'])
@login_required
def notification_delete(notif_id):
    n = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    db.session.delete(n)
    db.session.commit()
    return redirect(url_for('notifications'))


# ── Download management (admin) ───────────────────────────────
@app.route('/admin/downloads/add', methods=['POST'])
@admin_required
def admin_add_download():
    if not current_user.is_admin:
        abort(403)
    item = DownloadItem(
        title          = request.form['title'].strip(),
        artist         = request.form.get('artist', '').strip() or None,
        album          = request.form.get('album',  '').strip() or None,
        producer       = request.form.get('producer', '').strip() or None,
        description    = request.form.get('description', '').strip() or None,
        audio_path     = request.form['audio_path'].strip(),
        stream_url     = request.form.get('stream_url', '').strip() or None,
        sort_order     = int(request.form.get('sort_order', 0) or 0),
        requires_login = 'requires_login' in request.form,
    )
    db.session.add(item)
    db.session.commit()
    # Optionally notify users who want new music alerts
    _broadcast_notification(
        notif_type = 'new_music',
        title      = f'New track: {item.title}',
        message    = f'{item.artist or "Goodchi"} just added "{item.title}" to Downloads.',
        link       = url_for('download'),
        pref_field = 'notif_new_music',
    )
    flash(f'Track "{item.title}" added.', 'success')
    return redirect(url_for('admin_dashboard') + '#downloads')


@app.route('/admin/downloads/<int:item_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_download(item_id):
    if not current_user.is_admin:
        abort(403)
    item = DownloadItem.query.get_or_404(item_id)
    if request.method == 'POST':
        item.title          = request.form['title'].strip()
        item.artist         = request.form.get('artist', '').strip() or None
        item.album          = request.form.get('album',  '').strip() or None
        item.producer       = request.form.get('producer', '').strip() or None
        item.description    = request.form.get('description', '').strip() or None
        item.audio_path     = request.form['audio_path'].strip()
        item.stream_url     = request.form.get('stream_url', '').strip() or None
        item.sort_order     = int(request.form.get('sort_order', 0) or 0)
        item.requires_login = 'requires_login' in request.form
        db.session.commit()
        flash('Track updated.', 'success')
        return redirect(url_for('admin_dashboard') + '#downloads')
    return render_template('admin_edit_download.html', item=item)


@app.route('/admin/downloads/<int:item_id>/delete', methods=['POST'])
@admin_required
def admin_delete_download(item_id):
    if not current_user.is_admin:
        abort(403)
    item = DownloadItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Track deleted.', 'success')
    return redirect(url_for('admin_dashboard') + '#downloads')

# ── Admin: broadcast notification ────────────────────────────
@app.route('/admin/notifications/broadcast', methods=['POST'])
@admin_required
def admin_broadcast_notification():
    if not current_user.is_admin:
        abort(403)
    notif_type = request.form.get('notif_type', 'announcement')
    title      = request.form['title'].strip()
    message    = request.form['message'].strip()
    link       = request.form.get('link', '').strip() or None

    pref_map = {
        'new_post':     'notif_new_posts',
        'new_music':    'notif_new_music',
        'announcement': 'notif_announcements',
    }
    count = _broadcast_notification(
        notif_type = notif_type,
        title      = title,
        message    = message,
        link       = link,
        pref_field = pref_map.get(notif_type, 'notif_announcements'),
    )
    flash(f'Notification sent to {count} user(s).', 'success')
    return redirect(url_for('admin_dashboard') + '#notifications_admin')


# ── Internal broadcast helper ────────────────────────────────
def _broadcast_notification(notif_type, title, message, link=None, pref_field=None):
    """Create a Notification row for each qualifying user. Returns recipient count."""
    query = User.query
    if pref_field:
        query = query.filter(getattr(User, pref_field) == True)
    users = query.all()

    for u in users:
        n = Notification(
            user_id = u.id,
            type    = notif_type,
            title   = title,
            message = message,
            link    = link,
        )
        db.session.add(n)

    log = BroadcastLog(
        notif_type      = notif_type,
        title           = title,
        message         = message,
        link            = link,
        recipient_count = len(users),
    )
    db.session.add(log)
    db.session.commit()
    return len(users)


# Admin Dashboard Routes
@app.route('/admin/posts')
@admin_required
def admin_posts():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template("admin/posts.html", posts=posts)

@app.route('/admin/post/new', methods=['GET', 'POST'])
@admin_required
def admin_new_post():
    if request.method == 'POST':
        slug = request.form.get('slug')
        title = request.form.get('title')
        excerpt = request.form.get('excerpt')
        content = request.form.get('content')
        date = request.form.get('date')
        image = request.form.get('image')

        if not all([slug, title, excerpt, content, date, image]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin_new_post'))

        if Post.query.filter_by(slug=slug).first():
            flash('A post with this slug already exists.', 'danger')
            return redirect(url_for('admin_new_post'))

        post = Post(slug=slug, title=title, excerpt=excerpt, content=content, date=date, image=image)
        db.session.add(post)
        db.session.commit()

        _broadcast_notification(
        notif_type = 'new_post',
        title      = f'New story: {post.title}',
        message    = post.excerpt[:120] if post.excerpt else 'A new story just dropped.',
        link       = url_for('post', slug=post.slug),
        pref_field = 'notif_new_posts',
    )
        flash(f'Post "{title}" created successfully!', 'success')
        return redirect(url_for('admin_posts'))

    return render_template("admin/new_post.html")

@app.route('/admin/post/<int:post_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        post.slug = request.form.get('slug')
        post.title = request.form.get('title')
        post.excerpt = request.form.get('excerpt')
        post.content = request.form.get('content')
        post.date = request.form.get('date')
        post.image = request.form.get('image')

        if not all([post.slug, post.title, post.excerpt, post.content, post.date, post.image]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin_edit_post', post_id=post_id))

        existing_post = Post.query.filter_by(slug=post.slug).first()
        if existing_post and existing_post.id != post_id:
            flash('A post with this slug already exists.', 'danger')
            return redirect(url_for('admin_edit_post', post_id=post_id))

        db.session.commit()
        flash(f'Post "{post.title}" updated successfully!', 'success')
        return redirect(url_for('admin_posts'))

    return render_template("admin/edit_post.html", post=post)

@app.route('/admin/post/<int:post_id>/delete', methods=['POST'])
@admin_required
def admin_delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    title = post.title
    db.session.delete(post)
    db.session.commit()

    flash(f'Post "{title}" deleted successfully!', 'success')
    return redirect(url_for('admin_posts'))

@app.route('/support')
@login_required
def support_page():
    bank_details   = BankDetail.query.filter_by(is_active=True).all()
    crypto_wallets = CryptoWallet.query.filter_by(is_active=True).all()
    return render_template('support.html',
                           bank_details=bank_details,
                           crypto_wallets=crypto_wallets)


@app.route('/support/pay', methods=['POST'])
@login_required
def support_pay():
    """
    Handle card payment submission.
    In production: integrate Stripe here.
    For now: record the intent and return success so the UI flow works.

    To add real Stripe:
        pip install stripe
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        intent = stripe.PaymentIntent.create(amount=int(amount*100), currency='usd', ...)
    """
    data   = request.get_json(force=True) or {}
    amount = float(data.get('amount', 0) or 0)
    name   = (data.get('name') or '').strip()

    if amount < 1:
        return jsonify({'success': False, 'error': 'Minimum amount is $1.'}), 400

    try:
        ref = _secrets.token_hex(16)
        p   = SupportPayment(
            user_id        = current_user.id if current_user.is_authenticated else None,
            supporter_name = name or None,
            amount         = amount,
            method         = 'card',
            reference      = ref,
            status         = 'completed',   # replace with 'pending' when Stripe webhook confirms
        )
        db.session.add(p)
        db.session.commit()
        return jsonify({'success': True, 'reference': ref})
    except Exception as e:
        db.session.rollback()
        app.logger.error('support_pay: %s', e)
        return jsonify({'success': False, 'error': 'Could not record payment.'}), 500


# ── Admin dashboard ────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    total_users     = User.query.count()
    total_payments  = SupportPayment.query.count()
    total_supported = db.session.query(db.func.sum(SupportPayment.amount))\
                        .filter_by(status='completed').scalar() or 0.0
    total_posts     = Post.query.count()
    recent_payments = SupportPayment.query.order_by(SupportPayment.created_at.desc()).limit(8).all()
    all_payments    = SupportPayment.query.order_by(SupportPayment.created_at.desc()).all()
    all_users       = User.query.order_by(User.created_at.desc()).all()
    bank_details    = BankDetail.query.order_by(BankDetail.created_at.desc()).all()
    crypto_wallets  = CryptoWallet.query.order_by(CryptoWallet.created_at.desc()).all()
    all_db_posts    = Post.query.order_by(Post.created_at.desc()).all()
    download_items    = DownloadItem.query.order_by(DownloadItem.sort_order, DownloadItem.created_at).all()
    recent_broadcasts = BroadcastLog.query.order_by(BroadcastLog.created_at.desc()).limit(10).all()
    open_tickets      = ContactMessage.query.filter_by(is_closed=False).count()
    unread_tickets    = ContactMessage.query.filter_by(is_read=False, is_closed=False).count()
    recent_tickets    = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(10).all()

    return render_template('admin_dashboard.html',
        total_users       = total_users,
        total_payments    = total_payments,
        total_supported   = total_supported,
        total_posts       = total_posts,
        recent_payments   = recent_payments,
        all_payments      = all_payments,
        all_users         = all_users,
        bank_details      = bank_details,
        crypto_wallets    = crypto_wallets,
        all_db_posts      = all_db_posts,
        download_items    = download_items,
        recent_broadcasts = recent_broadcasts,
        open_tickets      = open_tickets,
        unread_tickets    = unread_tickets,
        recent_tickets    = recent_tickets,
    )


@app.route('/admin/user/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def admin_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'warning')
        return redirect(url_for('admin_dashboard'))
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"{'Made' if user.is_admin else 'Removed'} admin: {user.username}", 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account from here.', 'danger')
        return redirect(url_for('admin_dashboard'))
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/bank/add', methods=['POST'])
@admin_required
def admin_add_bank():
    bank = BankDetail(
        bank_name      = request.form.get('bank_name', '').strip(),
        account_name   = request.form.get('account_name', '').strip(),
        account_number = request.form.get('account_number', '').strip(),
        sort_code      = request.form.get('sort_code', '').strip() or None,
        iban           = request.form.get('iban', '').strip() or None,
        swift          = request.form.get('swift', '').strip() or None,
        country        = request.form.get('country', '').strip() or None,
    )
    db.session.add(bank)
    db.session.commit()
    flash('Bank account saved.', 'success')
    return redirect(url_for('admin_dashboard') + '#tab-bank-trigger')


@app.route('/admin/bank/<int:bank_id>/delete', methods=['POST'])
@admin_required
def admin_delete_bank(bank_id):
    bank = BankDetail.query.get_or_404(bank_id)
    db.session.delete(bank)
    db.session.commit()
    flash('Bank account deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/wallet/add', methods=['POST'])
@admin_required
def admin_add_wallet():
    wallet = CryptoWallet(
        label   = request.form.get('label',   '').strip(),
        network = request.form.get('network', '').strip() or None,
        address = request.form.get('address', '').strip(),
    )
    db.session.add(wallet)
    db.session.commit()
    flash('Crypto wallet saved.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/wallet/<int:wallet_id>/delete', methods=['POST'])
@admin_required
def admin_delete_wallet(wallet_id):
    wallet = CryptoWallet.query.get_or_404(wallet_id)
    db.session.delete(wallet)
    db.session.commit()
    flash('Wallet address deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


# ══════════════════════════════════════════════════════════════
#  ADMIN — SUPPORT MESSAGES / TICKETS
# ══════════════════════════════════════════════════════════════

@app.route('/admin/messages')
@admin_required
def admin_messages():
    status  = request.args.get('status', 'open')
    query   = ContactMessage.query
    if status == 'open':
        query = query.filter_by(is_closed=False)
    elif status == 'closed':
        query = query.filter_by(is_closed=True)
    tickets = query.order_by(ContactMessage.created_at.desc()).all()
    for t in tickets:
        if not t.is_read:
            t.is_read = True
    db.session.commit()
    return render_template('admin_messages.html', tickets=tickets, status=status)


@app.route('/admin/messages/<int:ticket_id>')
@admin_required
def admin_view_ticket(ticket_id):
    ticket = ContactMessage.query.get_or_404(ticket_id)
    ticket.is_read = True
    db.session.commit()
    return render_template('admin_ticket_view.html', ticket=ticket)


@app.route('/admin/messages/<int:ticket_id>/reply', methods=['POST'])
@admin_required
def admin_reply_ticket(ticket_id):
    ticket = ContactMessage.query.get_or_404(ticket_id)
    body   = request.form.get('body', '').strip()
    if not body:
        flash('Reply cannot be empty.', 'danger')
        return redirect(url_for('admin_view_ticket', ticket_id=ticket_id))

    reply = ContactReply(
        ticket_id      = ticket_id,
        author_id      = current_user.id,
        body           = body,
        is_admin_reply = True,
        read_by_user   = False,
    )
    db.session.add(reply)

    # In-app notification for the ticket owner
    n = Notification(
        user_id = ticket.user_id,
        type    = 'announcement',
        title   = 'New reply to your support message',
        message = body[:120] + ('…' if len(body) > 120 else ''),
        link    = url_for('view_ticket', ticket_id=ticket_id),
    )
    db.session.add(n)

    # Email the user
    try:
        msg = Message(
            subject    = 'Re: Your support message — Goodchi Experience',
            recipients = [ticket.email],
            html       = f'''
                <p>Hi {ticket.name},</p>
                <p>You have a new reply to your support message:</p>
                <blockquote style="border-left:3px solid #00f5c4;padding-left:12px;color:#555">
                  {body.replace(chr(10), "<br>")}
                </blockquote>
                <p><a href="{url_for('view_ticket', ticket_id=ticket_id, _external=True)}">
                  View the full conversation →</a></p>
                <p style="font-size:12px;color:#999">— The Goodchi Experience Team</p>
            ''',
            body = f'Hi {ticket.name},\n\nNew reply:\n\n{body}\n\n— Goodchi Experience',
        )
        mail.send(msg)
    except Exception as e:
        app.logger.warning('Reply email failed: %s', e)

    db.session.commit()
    flash('Reply sent.', 'success')
    return redirect(url_for('admin_view_ticket', ticket_id=ticket_id))


@app.route('/admin/messages/<int:ticket_id>/close', methods=['POST'])
@admin_required
def admin_close_ticket(ticket_id):
    ticket = ContactMessage.query.get_or_404(ticket_id)
    ticket.is_closed = True
    db.session.commit()
    flash('Ticket closed.', 'success')
    return redirect(url_for('admin_messages'))


@app.route('/admin/messages/<int:ticket_id>/reopen', methods=['POST'])
@admin_required
def admin_reopen_ticket(ticket_id):
    ticket = ContactMessage.query.get_or_404(ticket_id)
    ticket.is_closed = False
    db.session.commit()
    flash('Ticket reopened.', 'success')
    return redirect(url_for('admin_view_ticket', ticket_id=ticket_id))


@app.route('/admin/messages/<int:ticket_id>/delete', methods=['POST'])
@admin_required
def admin_delete_ticket(ticket_id):
    ticket = ContactMessage.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    flash('Ticket deleted.', 'success')
    return redirect(url_for('admin_messages'))


# ══════════════════════════════════════════════════════════════
#  USER — VIEW OWN TICKET THREAD
# ══════════════════════════════════════════════════════════════

@app.route('/contact/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = ContactMessage.query.get_or_404(ticket_id)
    if ticket.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    # Mark admin replies as seen
    for r in ticket.replies:
        if r.is_admin_reply and not r.read_by_user:
            r.read_by_user = True
    db.session.commit()
    return render_template('ticket_view.html', ticket=ticket)


@app.route('/contact/ticket/<int:ticket_id>/reply', methods=['POST'])
@login_required
def reply_ticket(ticket_id):
    ticket = ContactMessage.query.get_or_404(ticket_id)
    if ticket.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    body = request.form.get('body', '').strip()
    if not body:
        flash('Reply cannot be empty.', 'danger')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))

    reply = ContactReply(
        ticket_id      = ticket_id,
        author_id      = current_user.id,
        body           = body,
        is_admin_reply = False,
        read_by_user   = True,
    )
    if ticket.is_closed:
        ticket.is_closed = False   # user reply re-opens ticket
    db.session.add(reply)
    db.session.commit()
    flash('Follow-up sent.', 'success')
    return redirect(url_for('view_ticket', ticket_id=ticket_id))


# ══════════════════════════════════════════════════════════════
#  PASSWORD RESET
# ══════════════════════════════════════════════════════════════

def _send_reset_email(user, token):
    reset_url = url_for('password_reset_confirm', token=token, _external=True)
    try:
        msg = Message(
            subject    = 'Reset your Goodchi Experience password',
            recipients = [user.email],
            html       = f'''
                <h2>Password Reset</h2>
                <p>Hi {user.username},</p>
                <p>Click below to reset your password. This link expires in <strong>30 minutes</strong>.</p>
                <p><a href="{reset_url}"
                      style="display:inline-block;padding:12px 24px;background:#00f5c4;
                             color:#0a0a1a;text-decoration:none;border-radius:6px;font-weight:700">
                  Reset Password →</a></p>
                <p style="font-size:12px;color:#999">
                  If you didn't request this, ignore this email.</p>
            ''',
            body = f'Hi {user.username},\n\nReset link (expires in 30 min):\n{reset_url}\n\nIgnore if you didn\'t request this.',
        )
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error('Reset email failed: %s', e)
        return False


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = User.query.filter(db.func.lower(User.email) == email).first()
        # Same message whether email exists or not — prevents enumeration
        flash('If that email is registered, a reset link has been sent.', 'info')
        if user:
            PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
            db.session.commit()
            token = _secrets.token_urlsafe(48)
            prt   = PasswordResetToken(
                user_id    = user.id,
                token      = token,
                expires_at = datetime.utcnow() + timedelta(minutes=30),
            )
            db.session.add(prt)
            db.session.commit()
            _send_reset_email(user, token)
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def password_reset_confirm(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    prt = PasswordResetToken.query.filter_by(token=token).first()
    if not prt or not prt.is_valid:
        flash('This reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        new_pw     = request.form.get('new_password', '')
        confirm_pw = request.form.get('confirm_password', '')
        if len(new_pw) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('password_reset_confirm', token=token))
        if new_pw != confirm_pw:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('password_reset_confirm', token=token))
        prt.user.set_password(new_pw)
        prt.used = True
        db.session.commit()
        flash('✅ Password updated! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)


# ── One-time admin promotion ───────────────────────────────────
@app.route('/make-me-admin')
@login_required
def make_me_admin():
    setup_key = os.getenv('ADMIN_SETUP_KEY', '')
    provided  = request.args.get('key', '')
    if not setup_key:
        flash('Admin setup key not configured.', 'danger')
        return redirect(url_for('home'))
    if not provided or provided != setup_key:
        flash('Invalid setup key.', 'danger')
        return redirect(url_for('home'))
    if current_user.is_admin:
        flash(f'Already an admin, {current_user.username}.', 'info')
        return redirect(url_for('admin_dashboard'))
    current_user.is_admin = True
    db.session.commit()
    flash(f'✅ {current_user.username} is now an admin!', 'success')
    return redirect(url_for('admin_dashboard'))

# ── Startup: create tables + migrate columns + seed posts ─────
# Runs under both gunicorn (Render) and the dev server.
def _run_startup_migrations():
    """Add any missing columns to existing tables. Safe to call repeatedly."""
    from sqlalchemy import text, inspect as sa_inspect

    def col_exists(table, col):
        try:
            inspector = sa_inspect(db.engine)
            return col in [c['name'] for c in inspector.get_columns(table)]
        except Exception:
            return False

    pending = [
        # contact_message new columns
        ('contact_message', 'is_closed', 'BOOLEAN DEFAULT 0 NOT NULL'),
        ('contact_message', 'subject',   'VARCHAR(200)'),
        # user new columns
        ('user', 'bio',                  'TEXT'),
        ('user', 'avatar',               'VARCHAR(256)'),
        ('user', 'notif_new_posts',      'BOOLEAN DEFAULT 1 NOT NULL'),
        ('user', 'notif_new_music',      'BOOLEAN DEFAULT 1 NOT NULL'),
        ('user', 'notif_announcements',  'BOOLEAN DEFAULT 1 NOT NULL'),
        ('user', 'notif_email',          'BOOLEAN DEFAULT 0 NOT NULL'),
        ('user', 'totp_secret',          'VARCHAR(32)'),
        ('user', 'totp_enabled',         'BOOLEAN DEFAULT 0 NOT NULL'),
        ('user', 'totp_pending',         'VARCHAR(32)'),
    ]

    with db.engine.connect() as conn:
        for table, col, defn in pending:
            if not col_exists(table, col):
                try:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {defn}'))
                    conn.commit()
                    print(f'[migrate] added {table}.{col}')
                except Exception as e:
                    print(f'[migrate] skip {table}.{col}: {e}')


with app.app_context():
    db.create_all()           # creates any brand-new tables
    _run_startup_migrations() # adds missing columns to existing tables
    try:
        seed_posts(verbose=False)
    except Exception as _seed_err:
        print(f"[seed] skipped: {_seed_err}")

    # Auto-promote ADMIN_EMAIL user on startup
    _admin_email = os.getenv('ADMIN_EMAIL', '')
    if _admin_email:
        _admin_user = User.query.filter_by(email=_admin_email).first()
        if _admin_user and not _admin_user.is_admin:
            _admin_user.is_admin = True
            db.session.commit()
            print(f"[startup] Promoted {_admin_email} to admin.")

if __name__ == '__main__':
    app.run(debug=True)
