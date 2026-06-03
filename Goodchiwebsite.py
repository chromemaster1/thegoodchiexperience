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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from email_validator import validate_email, EmailNotValidError

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

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['ADMIN_EMAIL'] = os.getenv('ADMIN_EMAIL', 'admin@thegoodchiexperience.com')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config.get('MAIL_USERNAME'))

# Session configuration - add timeout
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
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
login_manager.login_message = 'Please log in to access this page.'

# Rate limiter for security
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)

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
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<ContactMessage {self.name} - {self.created_at}>'

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
@limiter.limit("5 per minute")  # Rate limiting: 5 attempts per minute
def login():
    """Handle user login with rate limiting"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            login_user(user)
            user.update_last_login()  # Track last login
            next_page = request.args.get('next')
            flash(f'✅ Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('❌ Invalid username or password.', 'danger')

    return render_template('login.html', form=form)

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
    page = request.args.get('page', 1, type=int)
    per_page = 4
    pagination = Post.query.order_by(Post.id.asc()).paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items
    return render_template("index.html", posts=posts, pagination=pagination)

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
    return render_template("download.html")

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

@app.route('/debug')
@login_required
def debug():
    """Debug endpoint - shows user information (remove in production)"""
    if not current_user.is_admin:
        flash('❌ Access denied.', 'danger')
        return redirect(url_for('home'))

    return f"""
    <h1>Debug Info</h1>
    <p><strong>Username:</strong> {current_user.username}</p>
    <p><strong>Email:</strong> {current_user.email}</p>
    <p><strong>Is Admin:</strong> {current_user.is_admin}</p>
    <p><strong>Is Authenticated:</strong> {current_user.is_authenticated}</p>
    <p><strong>Last Login:</strong> {current_user.last_login}</p>
    <a href="{url_for('home')}">Back to Home</a>
    """

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
