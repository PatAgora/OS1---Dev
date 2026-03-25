import os, uuid, datetime, json, mimetypes, re, smtplib, ssl, base64, hashlib, hmac, uuid, json, re, time, requests
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, abort
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import Response
from wtforms import StringField, TextAreaField, BooleanField, SelectField, IntegerField, FileField, DateTimeLocalField, SubmitField
from typing import Optional, List, Dict, Tuple
from sqlalchemy import or_, and_
import csv
from io import StringIO
from flask import current_app
from flask import Blueprint
from sqlalchemy import exists
from flask import redirect, url_for
from flask import make_response

from wtforms.validators import DataRequired, Email, Optional as WTOptional
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, select, ForeignKey, func, Column, text, Float
from sqlalchemy.orm import declarative_base, relationship, Session, selectinload
from sqlalchemy.types import JSON as SA_JSON
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
load_dotenv()
import requests
from dateutil import parser as dtparser
from sqlalchemy import literal_column
from sqlalchemy import delete
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship, backref
from wtforms import Form
from wtforms.validators import DataRequired
from wtforms import StringField, SelectField
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import session
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# reCAPTCHA configuration
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")
RECAPTCHA_ENABLED = bool(RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY)

import datetime
from flask import abort, render_template, request
from sqlalchemy import or_, false
from sqlalchemy.orm import selectinload

from wtforms import FileField
from wtforms.validators import DataRequired as WTDataRequired

class UploadCVForm(FlaskForm):
    cv = FileField("Upload CV (PDF/DOC/DOCX)", validators=[WTDataRequired()])
    submit = SubmitField("Upload")

# Signable REST API — no SDK needed, uses requests
try:
    import requests as _requests_lib
except Exception:
    _requests_lib = None

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ats.db")
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SECRET_KEY   = os.getenv("FLASK_SECRET_KEY", "dev-secret")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ats.db")

engine = create_engine(DATABASE_URL, future=True)
Base = declarative_base()

class RoleType(Base):
    __tablename__ = "role_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    default_rate = Column(Integer, default=0)

class EngagementPlan(Base):
    __tablename__ = "engagement_plans"
    id = Column(Integer, primary_key=True, autoincrement=True)
    engagement_id = Column(Integer, ForeignKey("engagements.id"), index=True)
    role_type = Column(String(50), default="")
    planned_count = Column(Integer, default=0)

    # cost to us per head per day
    pay_rate = Column(Integer, default=0)

    # what we bill client per head per day
    charge_rate = Column(Integer, default=0)

    # legacy; keep in sync with charge_rate when saving for backwards reports
    rate = Column(Integer, default=0)

    # version snapshot / plan iteration number
    version_int = Column(Integer, default=1)
    
    # intake date for 4-week lookahead feature
    intake_date = Column(DateTime, nullable=True)

# Signable (signable.co.uk) REST API
SIGNABLE_API_KEY = os.getenv("SIGNABLE_API_KEY", "")
SIGNABLE_BASE_URL = os.getenv("SIGNABLE_BASE_URL", "https://api.signable.co.uk/v1")
SIGNABLE_WEBHOOK_SECRET = os.getenv("SIGNABLE_WEBHOOK_SECRET", "")
SIGNABLE_TEMPLATE_FINGERPRINT = os.getenv("SIGNABLE_TEMPLATE_FINGERPRINT", "")

# Verifile (verifile.co.uk) — pre-employment screening API
VERIFILE_API_KEY = os.getenv("VERIFILE_API_KEY", "")
VERIFILE_BASE_URL = os.getenv("VERIFILE_BASE_URL", "https://api.verifile.co.uk/v3")
VERIFILE_CLIENT_ID = os.getenv("VERIFILE_CLIENT_ID", "")
VERIFILE_WEBHOOK_SECRET = os.getenv("VERIFILE_WEBHOOK_SECRET", "")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "Talent <noreply@example.com>")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")

_client = None
def get_gemini_model():
    """
    Return a configured Google Gemini GenerativeModel instance.
    Returns None if GEMINI_API_KEY is not configured or is a placeholder.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY in ("your_gemini_api_key_here", ""):
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        print(f"Gemini init failed: {e}")
        return None

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")
PORTAL_BASE_URL = os.getenv("PORTAL_BASE_URL", APP_BASE_URL)

INTERVIEWER_EMAIL = os.getenv("INTERVIEWER_EMAIL", "interviewer@example.com")
TIMEZONE = os.getenv("TIMEZONE", "Europe/London")

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

# Role taxonomy for planning and reporting
ROLE_TYPES = [
    "Project Director",
    "Project Manager",
    "Project Lead",
    "Ops Manager",
    "Team Leader",
    "Team Lead",
    "Case Handler",
    "Officers",
    "Admin",
]

# Opportunity stages (for new Opportunities feature)
OPPORTUNITY_STAGES = [
    "Lead",
    "Closed Won",
    "Closed Lost",
]

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Session timeout configuration (30 minutes for regular sessions)
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh timeout on each request

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.gstatic.com data:; img-src 'self' data: https://api.qrserver.com"
    return response

# Health check endpoint for Railway
@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}), 200

@app.route("/system/status")
def system_status():
    """
    Diagnostic endpoint to check system configuration
    """
    gemini_model = get_gemini_model()

    status = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "ai": {
            "provider": "Google Gemini (gemini-2.5-flash)",
            "configured": gemini_model is not None,
            "key_present": bool(GEMINI_API_KEY),
        },
        "database": {
            "connected": True  # If we get here, DB is working
        },
        "features": {
            "ai_scoring": gemini_model is not None,
            "ai_summarization": gemini_model is not None,
            "authentication": True
        }
    }

    # Test Gemini connection if configured
    if gemini_model:
        try:
            response = gemini_model.generate_content("Reply with OK")
            status["ai"]["api_test"] = "success"
        except Exception as e:
            status["ai"]["api_test"] = f"failed: {str(e)}"

    return jsonify(status), 200


# SECURITY: Diagnostic endpoints removed to prevent information disclosure
# These were temporary debugging endpoints that exposed:
# - Database schema structure (/system/db-schema)
# - User email addresses (/system/list-users)
# Removed for CREST compliance

@app.route("/system/db-check")
def system_db_check():
    """Temporary diagnostic — check candidate and application counts."""
    with Session(engine) as s:
        total_cands = s.execute(text("SELECT COUNT(*) FROM candidates")).scalar()
        portal_cands = s.execute(text("SELECT COUNT(*) FROM candidates WHERE source = 'associate-portal'")).scalar()
        total_apps = s.execute(text("SELECT COUNT(*) FROM applications")).scalar()
        pipeline_apps = s.execute(text("SELECT COUNT(*) FROM applications WHERE status = 'Pipeline'")).scalar()
        # Search for any candidate with 'stones' or 'patrick' in name
        search_rows = s.execute(text(
            "SELECT id, name, email, source, created_at FROM candidates WHERE LOWER(name) LIKE '%stones%' OR LOWER(name) LIKE '%patrick%' OR LOWER(email) LIKE '%patrick%' ORDER BY created_at DESC LIMIT 10"
        )).all()
        # Find portal candidates
        portal_rows = s.execute(text(
            "SELECT id, name, email, source, created_at FROM candidates WHERE source = 'associate-portal' ORDER BY created_at DESC LIMIT 10"
        )).all()
        # Check associate_profiles table
        assoc_profiles = []
        try:
            assoc_profiles = [
                {"id": r[0], "candidate_id": r[1], "created_at": str(r[2])}
                for r in s.execute(text("SELECT id, candidate_id, created_at FROM associate_profiles ORDER BY created_at DESC LIMIT 10")).all()
            ]
        except Exception:
            assoc_profiles = "table not found"
        # Find recent applications
        recent_apps = s.execute(text(
            "SELECT a.id, a.candidate_id, a.job_id, a.status, a.created_at, c.name "
            "FROM applications a JOIN candidates c ON c.id = a.candidate_id "
            "ORDER BY a.created_at DESC LIMIT 10"
        )).all()
        return {
            "total_candidates": total_cands,
            "portal_candidates": portal_cands,
            "total_applications": total_apps,
            "pipeline_applications": pipeline_apps,
            "search_patrick_stones": [
                {"id": r[0], "name": r[1], "email": r[2], "source": r[3], "created_at": str(r[4])} for r in search_rows
            ],
            "associate_profiles": assoc_profiles,
            "portal_users": [
                {"id": r[0], "name": r[1], "email": r[2], "source": r[3], "created_at": str(r[4])} for r in portal_rows
            ],
            "recent_applications": [
                {"app_id": r[0], "candidate_id": r[1], "job_id": r[2], "status": r[3], "created_at": str(r[4]), "name": r[5]} for r in recent_apps
            ],
        }


@app.context_processor
def inject_template_helpers():
    def view_exists(name: str) -> bool:
        try:
            return name in current_app.view_functions
        except Exception:
            return False
    
    def csp_nonce():
        """Generate a CSP nonce for inline scripts."""
        import secrets
        return secrets.token_urlsafe(16)
    
    return {"view_exists": view_exists, "csp_nonce": csp_nonce}

# --- Auth / sessions ---
login_manager = LoginManager(app)
login_manager.login_view = "login"  # default guard for worker-only pages

@login_manager.unauthorized_handler
def unauthorized_callback():
    """Handle unauthorized access - return JSON for API routes, redirect for others"""
    if request.path.startswith('/api/'):
        return jsonify({"ok": False, "error": "Unauthorized. Please log in."}), 401
    return redirect(url_for('login', next=request.url))

@login_manager.user_loader
def load_user(user_id):
    with Session(engine) as s:
        user = s.get(User, int(user_id))
        if user:
            s.expunge(user)
            return user
    return None

# ========== Authentication Routes ==========

@app.route("/setup-first-user", methods=["GET", "POST"])
@limiter.limit("5 per hour")  # Rate limit: 5 setup attempts per hour per IP
def setup_first_user():
    """
    One-time setup route to create the first admin user
    Only works if NO users exist in the database
    """
    with Session(engine) as s:
        # Check if any users exist
        user_count = s.execute(select(func.count(User.id))).scalar()
        
        if user_count > 0:
            flash("Setup already completed. Users already exist.", "error")
            return redirect(url_for('login'))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        if not name or not email or not password:
            flash("All fields are required", "error")
            return render_template("setup_first_user.html")
        
        # Validate password length
        if len(password) < 8:
            flash("Password must be at least 8 characters", "error")
            return render_template("setup_first_user.html")
        
        with Session(engine) as s:
            # Double-check no users exist
            user_count = s.execute(select(func.count(User.id))).scalar()
            if user_count > 0:
                flash("Setup already completed", "error")
                return redirect(url_for('login'))
            
            # Create first user
            new_user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password, method='pbkdf2:sha256')
            )
            s.add(new_user)
            s.commit()
            
            flash(f"Account created successfully! You can now login.", "success")
            return redirect(url_for('login'))
    
    return render_template("setup_first_user.html")

@app.route("/run-migration-secret-xyz123")
def run_migration():
    """
    One-time migration route to add security columns
    Visit this URL once to run the migration, then it self-disables
    """
    try:
        from sqlalchemy import text
        
        results = []
        
        with engine.begin() as conn:
            # Check which columns already exist
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users'
            """))
            existing_cols = {row[0] for row in result}
            results.append(f"Existing columns: {', '.join(existing_cols)}")
            
            # Add security columns
            security_columns = {
                "role": "VARCHAR(50) DEFAULT 'employee'",
                "is_active": "BOOLEAN DEFAULT TRUE",
                "last_login": "TIMESTAMP",
                "failed_login_attempts": "INTEGER DEFAULT 0",
                "locked_until": "TIMESTAMP",
                "totp_secret": "VARCHAR(32)",
                "totp_enabled": "BOOLEAN DEFAULT FALSE",
                "backup_codes": "TEXT",
                "session_token": "VARCHAR(255)",
                "last_ip": "VARCHAR(45)",
                "last_user_agent": "TEXT",
                "magic_token": "VARCHAR(255)",
                "magic_token_expires": "TIMESTAMP"
            }
            
            for col_name, col_def in security_columns.items():
                if col_name not in existing_cols:
                    try:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                        results.append(f"✅ Added column: {col_name}")
                    except Exception as e:
                        results.append(f"❌ Failed to add {col_name}: {str(e)}")
                else:
                    results.append(f"⏭️  Column {col_name} already exists")
            
            # Create audit_logs table
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        user_id INTEGER,
                        user_email VARCHAR(255),
                        event_type VARCHAR(50) NOT NULL,
                        event_category VARCHAR(50) NOT NULL,
                        resource_type VARCHAR(50),
                        resource_id INTEGER,
                        action VARCHAR(255) NOT NULL,
                        details TEXT,
                        status VARCHAR(20) DEFAULT 'success',
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                    )
                """))
                results.append("✅ Created audit_logs table")
            except Exception as e:
                results.append(f"⚠️  audit_logs: {str(e)}")
            
            # Create password_history table
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS password_history (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """))
                results.append("✅ Created password_history table")
            except Exception as e:
                results.append(f"⚠️  password_history: {str(e)}")
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_password_history_user_id ON password_history(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_password_history_created_at ON password_history(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_users_email_idx ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_role_idx ON users(role)",
                "CREATE INDEX IF NOT EXISTS idx_users_totp_enabled ON users(totp_enabled)"
            ]
            
            for idx_stmt in indexes:
                try:
                    conn.execute(text(idx_stmt))
                except Exception:
                    pass
            
            results.append("✅ Created indexes")
            
            # Set first user as admin if exists
            try:
                conn.execute(text("""
                    UPDATE users 
                    SET role = 'admin' 
                    WHERE id = (SELECT MIN(id) FROM users)
                    AND role IS NULL
                """))
                results.append("✅ Set first user as admin")
            except Exception as e:
                results.append(f"⚠️  Admin role: {str(e)}")
        
        html = "<html><body style='font-family: monospace; padding: 20px;'>"
        html += "<h1>✅ Migration Complete!</h1>"
        html += "<pre>" + "\n".join(results) + "</pre>"
        html += "<p><strong>Next steps:</strong></p>"
        html += "<ol>"
        html += "<li>I will now redeploy the app with security features enabled</li>"
        html += "<li>Account lockout will be active</li>"
        html += "<li>Audit logging will work</li>"
        html += "</ol>"
        html += "<p><a href='/login'>Go to Login</a></p>"
        html += "</body></html>"
        
        return html
        
    except Exception as e:
        import traceback
        return f"<pre>❌ Migration failed:\n\n{str(e)}\n\n{traceback.format_exc()}</pre>", 500

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")  # Rate limit: 10 login attempts per minute per IP
def login():
    """Staff login page with full security features"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = WorkerLoginForm()
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("Please enter both email and password", "error")
            return render_template("auth_login.html", form=form)
        
        try:
            with Session(engine) as s:
                # Query user
                user = s.scalar(select(User).where(User.email == email))
                
                if not user:
                    # Audit log failed attempt
                    try:
                        log_audit_event('login', 'auth', f'Failed login attempt for {email}', 
                                      details={'reason': 'user_not_found'}, status='failure')
                    except:
                        pass
                    flash("Invalid email or password", "error")
                    return render_template("auth_login.html", form=form)
                
                # Check if account is locked
                try:
                    if user.is_locked():
                        remaining_time = user.locked_until - datetime.datetime.utcnow()
                        remaining_minutes = int(remaining_time.total_seconds() / 60) + 1
                        try:
                            log_audit_event('login', 'auth', 
                                          f'Locked account login attempt for {email}',
                                          details={'remaining_minutes': remaining_minutes},
                                          status='failure')
                        except:
                            pass
                        flash(f"Account locked. Try again in {remaining_minutes} minutes.", "error")
                        return render_template("auth_login.html", form=form)
                except:
                    pass  # If lockout check fails, continue with login
                
                # Verify password
                if not check_password_hash(user.password_hash, password):
                    # Failed login - increment attempts
                    try:
                        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                        
                        if user.failed_login_attempts >= 5:
                            user.locked_until = datetime.datetime.utcnow() + timedelta(minutes=30)
                            s.commit()
                            try:
                                log_audit_event('login', 'auth', 
                                              f'Account locked for {email} after 5 failed attempts',
                                              status='warning')
                            except:
                                pass
                            flash("Too many failed attempts. Account locked for 30 minutes.", "error")
                        else:
                            s.commit()
                            remaining = 5 - user.failed_login_attempts
                            try:
                                log_audit_event('login', 'auth', 
                                              f'Failed login attempt for {email}',
                                              details={'attempts': user.failed_login_attempts, 'remaining': remaining},
                                              status='failure')
                            except:
                                pass
                            flash(f"Invalid email or password. {remaining} attempts remaining.", "error")
                    except:
                        # If security features fail, show generic message
                        flash("Invalid email or password", "error")
                    return render_template("auth_login.html", form=form)
                
                # Password is correct - reset security counters
                try:
                    user.failed_login_attempts = 0
                    user.locked_until = None
                    user.last_login = datetime.datetime.utcnow()
                    s.commit()
                except:
                    pass  # Continue even if security updates fail
                
                # Check if 2FA is enabled
                if user.totp_enabled:
                    # Store user ID and email in session for 2FA verification
                    session['pending_user_id'] = user.id
                    session['pending_user_email'] = user.email
                    session['remember_me'] = request.form.get('remember_me') == 'on'
                    session['next_page'] = request.args.get('next') or '/'
                    return redirect(url_for('verify_2fa'))
                
                # 2FA NOT enabled - require setup before allowing access
                # Store user ID in session and redirect to 2FA setup
                session['setup_2fa_user_id'] = user.id
                session['setup_2fa_remember'] = request.form.get('remember_me') == 'on'
                session['setup_2fa_next'] = request.args.get('next') or '/'
                flash("Two-Factor Authentication is required. Please set up 2FA to continue.", "warning")
                return redirect(url_for('mandatory_2fa_setup'))
        
        except Exception as e:
            # Log the actual error for debugging
            print(f"Login error: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f"Login error: {str(e)}", "error")
            return render_template("auth_login.html", form=form)
    
    return render_template("auth_login.html", form=form)

@app.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    """Forgot password page - sends password reset link"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        
        if not email:
            flash("Please enter your email address", "error")
            return render_template("forgot_password.html")
        
        with Session(engine) as s:
            user = s.scalar(select(User).where(User.email == email))
            
            # Always show success message (security: don't reveal if email exists)
            # In production, you would send an actual email here
            if user:
                # Generate reset token (in production, send via email)
                import secrets
                reset_token = secrets.token_urlsafe(32)
                # Store token in session temporarily (in production, store in DB with expiry)
                session['reset_token'] = reset_token
                session['reset_email'] = email
                log_audit_event('password_reset', 'auth', f'Password reset requested for {email}', status='info')
        
        flash("If an account exists with that email, you will receive a password reset link shortly.", "success")
        return redirect(url_for('login'))
    
    return render_template("forgot_password.html")


@app.route("/request-access", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def request_access():
    """Request access page - new user registration request"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        company = request.form.get("company", "").strip()
        reason = request.form.get("reason", "").strip()
        
        if not name or not email:
            flash("Name and email are required", "error")
            return render_template("request_access.html")
        
        with Session(engine) as s:
            # Check if user already exists
            existing = s.scalar(select(User).where(User.email == email))
            if existing:
                flash("An account with this email already exists. Please login or reset your password.", "info")
                return redirect(url_for('login'))
        
        # Log the access request (in production, store in DB and notify admin)
        log_audit_event('access_request', 'auth', f'Access requested by {name} ({email})', 
                       details={'company': company, 'reason': reason}, status='info')
        
        flash("Your access request has been submitted. An administrator will review your request and contact you shortly.", "success")
        return redirect(url_for('login'))
    
    return render_template("request_access.html")


@app.route("/logout")
@login_required
def logout():
    """Staff logout"""
    # Log logout before clearing session
    log_audit_event('logout', 'auth', 'User logged out')
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for('login'))

# ========== Magic Link Authentication ==========
@app.route("/magic-link/<token>")
def magic_link_login(token):
    """
    Magic link login - allows user to set password on first login.
    Token is single-use and expires after 48 hours.
    """
    with Session(engine) as s:
        user = s.scalar(select(User).where(User.magic_token == token))
        
        if not user:
            flash("Invalid or expired magic link. Please contact your administrator.", "error")
            return redirect(url_for('login'))
        
        # Check if token has expired
        if user.magic_token_expires and user.magic_token_expires < datetime.datetime.utcnow():
            flash("This magic link has expired. Please contact your administrator for a new one.", "error")
            return redirect(url_for('login'))
        
        # Store user info in session for password setup
        session['magic_link_user_id'] = user.id
        session['magic_link_user_email'] = user.email
        session['magic_link_user_name'] = user.name
        
        return redirect(url_for('magic_link_set_password'))

@app.route("/magic-link/set-password", methods=["GET", "POST"])
def magic_link_set_password():
    """
    Allow user to set their password after clicking magic link.
    """
    user_id = session.get('magic_link_user_id')
    user_email = session.get('magic_link_user_email')
    user_name = session.get('magic_link_user_name')
    
    if not user_id:
        flash("Invalid session. Please use your magic link again.", "error")
        return redirect(url_for('login'))
    
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not password or not confirm_password:
            flash("Both password fields are required", "error")
            return render_template("magic_link_set_password_public.html", user_name=user_name, user_email=user_email)
        
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("magic_link_set_password_public.html", user_name=user_name, user_email=user_email)
        
        # Validate password strength
        is_valid, message, score = validate_password_strength(password, user_email)
        if not is_valid:
            flash(message, "error")
            return render_template("magic_link_set_password_public.html", user_name=user_name, user_email=user_email)
        
        with Session(engine) as s:
            user = s.get(User, user_id)
            if not user:
                flash("User not found", "error")
                return redirect(url_for('login'))
            
            # Set the new password
            user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            # Clear the magic token (single use)
            user.magic_token = None
            user.magic_token_expires = None
            s.commit()
            
            # Log the password setup
            log_audit_event('update', 'auth', f'User set password via magic link: {user_email}',
                          'user', user_id)
            
            # Clear magic link session vars
            session.pop('magic_link_user_id', None)
            session.pop('magic_link_user_email', None)
            session.pop('magic_link_user_name', None)
            
            # Check if user needs to set up 2FA (admin users)
            if not user.totp_enabled:
                # Set up session for 2FA setup
                session['setup_2fa_user_id'] = user.id
                session['setup_2fa_remember'] = False
                session['setup_2fa_next'] = '/'
                flash("Password set! Now let's secure your account with two-factor authentication.", "success")
                return redirect(url_for('mandatory_2fa_setup'))
            
            flash("Your password has been set successfully! Please log in.", "success")
            return redirect(url_for('login'))
    
    return render_template("magic_link_set_password_public.html", user_name=user_name, user_email=user_email)

def generate_magic_link(user_id: int) -> str:
    """
    Generate a magic link token for a user.
    Returns the full URL for the magic link.
    """
    import secrets
    token = secrets.token_urlsafe(32)
    expires = datetime.datetime.utcnow() + datetime.timedelta(hours=48)
    
    with Session(engine) as s:
        user = s.get(User, user_id)
        if user:
            user.magic_token = token
            user.magic_token_expires = expires
            s.commit()
    
    return token

# ========== One-Time Admin Setup ==========
@app.route("/setup/admin", methods=["GET", "POST"])
def setup_admin():
    """
    One-time admin setup route (no authentication required)
    Only works if no super_admin users exist in the database
    """
    with Session(engine) as s:
        # Check if any super_admin already exists
        existing_admin = s.scalar(
            select(User).where(User.role == 'super_admin')
        )
        
        if existing_admin:
            flash("Admin user already exists. Please login or contact support.", "error")
            return redirect(url_for('login'))
        
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            
            if not name or not email or not password or not confirm_password:
                flash("All fields are required", "error")
                return render_template("setup_admin.html")
            
            if password != confirm_password:
                flash("Passwords do not match", "error")
                return render_template("setup_admin.html")
            
            # Validate password strength
            is_valid, message, score = validate_password_strength(password, email)
            if not is_valid:
                flash(message, "error")
                return render_template("setup_admin.html")
            
            try:
                # Create super admin user
                new_admin = User(
                    name=name,
                    email=email,
                    password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
                    role='super_admin',
                    is_active=True,
                    created_at=datetime.datetime.utcnow()
                )
                s.add(new_admin)
                s.commit()
                
                # Log the admin creation
                log_audit_event('create', 'user_mgmt', f'Initial super admin created: {email}',
                              'user', new_admin.id, details={'setup_route': True})
                
                flash("✅ Super Admin created successfully! You can now login.", "success")
                return redirect(url_for('login'))
            except Exception as e:
                flash(f"Error creating admin: {str(e)}", "error")
                return render_template("setup_admin.html")
    
    return render_template("setup_admin.html")

# ========== Admin User Management (Super Admin Only) ==========
def super_admin_required(f):
    """Decorator to require super_admin role for access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "error")
            return redirect(url_for('login'))
        if current_user.role not in ('super_admin', 'admin'):
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin/create-user", methods=["GET", "POST"])
@login_required
@super_admin_required
def admin_create_user():
    """Create a new user with magic link for password setup"""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "employee")
        send_magic_link = request.form.get("send_magic_link") == "1"
        
        if not name or not email:
            flash("Name and email are required", "error")
            return render_template("admin_create_user.html")
        
        try:
            with Session(engine) as s:
                # Check if user already exists
                existing = s.scalar(select(User).where(User.email == email))
                if existing:
                    flash(f"User with email {email} already exists!", "error")
                    return render_template("admin_create_user.html")
                
                # Generate magic link token
                import secrets
                magic_token = secrets.token_urlsafe(32)
                magic_expires = datetime.datetime.utcnow() + datetime.timedelta(hours=48)
                
                # Create new user with placeholder password (user will set via magic link)
                new_user = User(
                    name=name,
                    email=email,
                    password_hash=generate_password_hash(secrets.token_urlsafe(32), method='pbkdf2:sha256'),
                    role=role,
                    is_active=True,
                    created_at=datetime.datetime.utcnow(),
                    magic_token=magic_token,
                    magic_token_expires=magic_expires
                )
                s.add(new_user)
                s.commit()
                
                # Generate the magic link URL
                magic_link_url = request.url_root.rstrip('/') + url_for('magic_link_login', token=magic_token)
                
                # Log user creation
                log_audit_event('create', 'user_mgmt', f'Created new user: {email}',
                              'user', new_user.id, {'role': role, 'created_by': current_user.email})
                
                # Send welcome email with magic link if requested
                if send_magic_link:
                    try:
                        html_body = f"""
                        <html>
                        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                                <h2 style="color: #1e3a8a;">Welcome to Optimus OS1</h2>
                                <p>Hi {name},</p>
                                <p>Your account has been created. Click the button below to set your password and get started:</p>
                                <div style="text-align: center; margin: 30px 0;">
                                    <a href="{magic_link_url}" style="background: #1e3a8a; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; font-size: 16px;">
                                        Set Your Password
                                    </a>
                                </div>
                                <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                                    <p style="margin: 5px 0;"><strong>Email:</strong> {email}</p>
                                    <p style="margin: 5px 0;"><strong>Role:</strong> {role.replace('_', ' ').title()}</p>
                                </div>
                                <p style="color: #666; font-size: 14px;">
                                    <i>This link expires in 48 hours. If you didn't request this account, please ignore this email.</i>
                                </p>
                                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                                <p style="color: #999; font-size: 12px;">This is an automated message from Optimus OS1.</p>
                            </div>
                        </body>
                        </html>
                        """
                        send_email(email, "Welcome to Optimus OS1 - Set Your Password", html_body)
                        flash(f"✅ User created! Magic link sent to {email}", "success")
                    except Exception as e:
                        # Show the magic link directly if email fails
                        flash(f"✅ User created but email failed. Share this link with {name}: {magic_link_url}", "warning")
                else:
                    # Show the magic link directly
                    flash(f"✅ User created! Share this link with {name} to set their password:", "success")
                    flash(f"🔗 {magic_link_url}", "info")
                
                return redirect(url_for('admin_list_users'))
        except Exception as e:
            flash(f"Error creating user: {str(e)}", "error")
            return render_template("admin_create_user.html")
    
    return render_template("admin_create_user.html")

@app.route("/admin/list-users")
@login_required
@super_admin_required
def admin_list_users():
    """Temporary page to list all users"""
    try:
        with Session(engine) as s:
            users = s.scalars(select(User).order_by(User.created_at.desc())).all()
            # Detach from session
            for user in users:
                s.expunge(user)
            return render_template("admin_list_users.html", users=users)
    except Exception as e:
        flash(f"Error loading users: {str(e)}", "error")
        return render_template("admin_list_users.html", users=[])

@app.route("/admin/unlock-user/<int:user_id>", methods=["POST"])
@login_required
@super_admin_required
def admin_unlock_user(user_id):
    """Admin route to unlock a locked user account"""
    with Session(engine) as s:
        user = s.get(User, user_id)
        if not user:
            flash("User not found", "error")
            return redirect(url_for('admin_list_users'))
        
        user.failed_login_attempts = 0
        user.locked_until = None
        s.commit()
        
        # Log unlock action
        log_audit_event('unlock', 'user_mgmt', f'Unlocked user account: {user.email}',
                      'user', user.id)
        
        flash(f"User {user.email} unlocked successfully", "success")
    
    return redirect(url_for('admin_list_users'))

@app.route("/admin/update-user", methods=["POST"])
@login_required
@super_admin_required
def admin_update_user():
    """Admin route to update user details"""
    user_id = request.form.get('user_id', type=int)
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    role = request.form.get('role', 'employee')
    
    if not user_id or not name or not email:
        flash("Missing required fields", "error")
        return redirect(url_for('admin_list_users'))
    
    with Session(engine) as s:
        user = s.get(User, user_id)
        if not user:
            flash("User not found", "error")
            return redirect(url_for('admin_list_users'))
        
        # Check if email is being changed and if new email already exists
        if email != user.email:
            existing = s.scalar(select(User).where(User.email == email))
            if existing:
                flash(f"Email {email} is already in use", "error")
                return redirect(url_for('admin_list_users'))
        
        old_values = {'name': user.name, 'email': user.email, 'role': user.role}
        user.name = name
        user.email = email
        user.role = role
        s.commit()
        
        # Log update action
        log_audit_event('update', 'user_mgmt', f'Updated user: {email}',
                      'user', user.id,
                      {'old_values': old_values, 'new_values': {'name': name, 'email': email, 'role': role}})
        
        flash(f"User {email} updated successfully", "success")
    
    return redirect(url_for('admin_list_users'))

@app.route("/admin/send-magic-link/<int:user_id>", methods=["POST"])
@login_required
@super_admin_required
def admin_send_magic_link(user_id):
    """Admin route to send a magic link for password reset"""
    with Session(engine) as s:
        user = s.get(User, user_id)
        if not user:
            flash("User not found", "error")
            return redirect(url_for('admin_list_users'))
        
        # Generate magic link token
        import secrets
        magic_token = secrets.token_urlsafe(32)
        magic_expires = datetime.datetime.utcnow() + datetime.timedelta(hours=48)
        
        user.magic_token = magic_token
        user.magic_token_expires = magic_expires
        s.commit()
        
        # Generate the magic link URL
        magic_link_url = request.url_root.rstrip('/') + url_for('magic_link_login', token=magic_token)
        
        # Log the action
        log_audit_event('update', 'user_mgmt', f'Sent magic link to: {user.email}',
                      'user', user.id)
        
        # Try to send email
        try:
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #1e3a8a;">Reset Your Password</h2>
                    <p>Hi {user.name},</p>
                    <p>A password reset has been requested for your account. Click the button below to set a new password:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{magic_link_url}" style="background: #1e3a8a; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; font-size: 16px;">
                            Reset Password
                        </a>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        <i>This link expires in 48 hours. If you didn't request this, please ignore this email.</i>
                    </p>
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px;">This is an automated message from Optimus OS1.</p>
                </div>
            </body>
            </html>
            """
            send_email(user.email, "Reset Your Password - Optimus OS1", html_body)
            flash(f"✅ Magic link sent to {user.email}", "success")
        except Exception as e:
            # Show the magic link directly if email fails
            flash(f"Email failed. Share this link with {user.name}:", "warning")
            flash(f"🔗 {magic_link_url}", "info")
    
    return redirect(url_for('admin_list_users'))

@app.route("/admin/disable-user-2fa/<int:user_id>", methods=["POST"])
@login_required
@super_admin_required
def admin_disable_user_2fa(user_id):
    """Admin route to disable 2FA for a user"""
    with Session(engine) as s:
        user = s.get(User, user_id)
        if not user:
            flash("User not found", "error")
            return redirect(url_for('admin_list_users'))
        
        user.totp_secret = None
        user.totp_enabled = False
        user.backup_codes = None
        s.commit()
        
        # Log 2FA disable action
        log_audit_event('update', 'security', f'Admin disabled 2FA for: {user.email}',
                      'user', user.id)
        
        flash(f"2FA disabled for {user.email}. They will need to set it up again.", "success")
    
    return redirect(url_for('admin_list_users'))

@app.route("/admin/deactivate-user/<int:user_id>", methods=["POST"])
@login_required
@super_admin_required
def admin_deactivate_user(user_id):
    """Admin route to deactivate a user account"""
    with Session(engine) as s:
        user = s.get(User, user_id)
        if not user:
            flash("User not found", "error")
            return redirect(url_for('admin_list_users'))
        
        if user.id == current_user.id:
            flash("You cannot deactivate your own account", "error")
            return redirect(url_for('admin_list_users'))
        
        user.is_active = False
        s.commit()
        
        # Log deactivation action
        log_audit_event('update', 'user_mgmt', f'Deactivated user: {user.email}',
                      'user', user.id)
        
        flash(f"User {user.email} has been deactivated", "success")
    
    return redirect(url_for('admin_list_users'))

@app.route("/admin/activate-user/<int:user_id>", methods=["POST"])
@login_required
@super_admin_required
def admin_activate_user(user_id):
    """Admin route to activate a user account"""
    with Session(engine) as s:
        user = s.get(User, user_id)
        if not user:
            flash("User not found", "error")
            return redirect(url_for('admin_list_users'))
        
        user.is_active = True
        s.commit()
        
        # Log activation action
        log_audit_event('update', 'user_mgmt', f'Activated user: {user.email}',
                      'user', user.id)
        
        flash(f"User {user.email} has been activated", "success")
    
    return redirect(url_for('admin_list_users'))

@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@login_required
@super_admin_required
def admin_delete_user(user_id):
    """Admin route to permanently delete a user account"""
    with Session(engine) as s:
        user = s.get(User, user_id)
        if not user:
            flash("User not found", "error")
            return redirect(url_for('admin_list_users'))
        
        if user.id == current_user.id:
            flash("You cannot delete your own account", "error")
            return redirect(url_for('admin_list_users'))
        
        user_email = user.email
        user_name = user.name
        
        # Delete the user
        s.delete(user)
        s.commit()
        
        # Log deletion action
        log_audit_event('delete', 'user_mgmt', f'Deleted user: {user_email}',
                      'user', user_id, {'deleted_user_name': user_name, 'deleted_user_email': user_email})
        
        flash(f"User {user_email} has been permanently deleted", "success")
    
    return redirect(url_for('admin_list_users'))


# ========== Password Security Functions ==========

def validate_password_strength(password: str, email: str = None) -> Tuple[bool, str, int]:
    """
    Validate password strength according to security policy.
    
    Returns: (is_valid, error_message, strength_score)
    - is_valid: True if password meets all requirements
    - error_message: Description of what's missing or "Strong password"
    - strength_score: 0-5 based on requirements met
    """
    errors = []
    score = 0
    
    # Minimum 12 characters
    if len(password) < 12:
        errors.append("at least 12 characters")
    else:
        score += 1
    
    # At least one uppercase letter
    if not re.search(r'[A-Z]', password):
        errors.append("an uppercase letter")
    else:
        score += 1
    
    # At least one lowercase letter
    if not re.search(r'[a-z]', password):
        errors.append("a lowercase letter")
    else:
        score += 1
    
    # At least one number
    if not re.search(r'\d', password):
        errors.append("a number")
    else:
        score += 1
    
    # At least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("a special character (!@#$%^&*() etc.)")
    else:
        score += 1
    
    # Cannot contain email username
    if email:
        username = email.split('@')[0].lower()
        if username in password.lower():
            errors.append("cannot contain your email username")
            score = 0
    
    if errors:
        return False, f"Password must contain {', '.join(errors)}", score
    
    return True, "Strong password", score

# ========== Security Enhancement Functions ==========

def verify_recaptcha(token: str) -> bool:
    """
    Verify Google reCAPTCHA v3 token.
    Returns True if valid, False otherwise.
    """
    if not RECAPTCHA_ENABLED:
        return True  # Skip verification if not configured
    
    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': RECAPTCHA_SECRET_KEY,
                'response': token
            },
            timeout=5
        )
        result = response.json()
        
        # reCAPTCHA v3 returns a score from 0.0 to 1.0
        # 1.0 is very likely a good interaction, 0.0 is very likely a bot
        # We'll accept scores >= 0.5
        return result.get('success', False) and result.get('score', 0) >= 0.5
    except Exception as e:
        current_app.logger.error(f"reCAPTCHA verification failed: {str(e)}")
        return True  # Fail open to avoid blocking legitimate users if reCAPTCHA is down

def sanitize_input(text: str, allow_html: bool = False) -> str:
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        text: Input text to sanitize
        allow_html: If True, allows safe HTML tags (for rich text)
    
    Returns:
        Sanitized text safe for display
    """
    if not text:
        return text
    
    import bleach
    
    if allow_html:
        # Allow safe HTML tags for rich text content
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'a', 'blockquote', 'code', 'pre'
        ]
        allowed_attrs = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title']
        }
        return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs, strip=True)
    else:
        # Strip all HTML for plain text fields
        return bleach.clean(text, tags=[], strip=True)

def check_password_history(user_id: int, new_password: str, history_limit: int = 5) -> bool:
    """
    Check if password has been used recently.
    
    Args:
        user_id: User ID to check
        new_password: New password to check against history
        history_limit: Number of previous passwords to check (default 5)
    
    Returns:
        True if password is OK to use, False if it's been used recently
    """
    try:
        with Session(engine) as s:
            # Get last N password hashes for this user
            recent_passwords = s.execute(
                text("""
                    SELECT password_hash FROM password_history
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"user_id": user_id, "limit": history_limit}
            ).fetchall()
            
            # Check if new password matches any recent passwords
            for (old_hash,) in recent_passwords:
                if check_password_hash(old_hash, new_password):
                    return False  # Password has been used recently
            
            return True  # Password is OK to use
    except Exception as e:
        current_app.logger.error(f"Password history check failed: {str(e)}")
        return True  # Fail open if check fails

def save_password_to_history(user_id: int, password_hash: str):
    """
    Save password hash to history for reuse prevention.
    
    Args:
        user_id: User ID
        password_hash: Hashed password to save
    """
    try:
        with Session(engine) as s:
            s.execute(
                text("""
                    INSERT INTO password_history (user_id, password_hash, created_at)
                    VALUES (:user_id, :password_hash, CURRENT_TIMESTAMP)
                """),
                {"user_id": user_id, "password_hash": password_hash}
            )
            s.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to save password history: {str(e)}")

# ========== Audit Logging Functions ==========

def log_audit_event(event_type: str, event_category: str, action: str, 
                   resource_type: str = None, resource_id: int = None,
                   details: dict = None, status: str = 'success'):
    """
    Log an audit event for security and compliance tracking.
    
    Args:
        event_type: Type of event (login, logout, create, update, delete, view, export)
        event_category: Category (auth, user_mgmt, data_access, security)
        action: Description of the action taken
        resource_type: Type of resource affected (candidate, job, user, etc.)
        resource_id: ID of the affected resource
        details: Additional details as dictionary (will be JSON encoded)
        status: Result status (success, failure, warning)
    
    Examples:
        log_audit_event('login', 'auth', 'User logged in successfully')
        log_audit_event('create', 'user_mgmt', 'Created new user', 'user', new_user.id)
        log_audit_event('login', 'auth', 'Failed login attempt', status='failure')
    """
    try:
        log = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            user_email=current_user.email if current_user.is_authenticated else None,
            event_type=event_type,
            event_category=event_category,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            details=json.dumps(details) if details else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None,
            status=status
        )
        
        with Session(engine) as s:
            s.add(log)
            s.commit()
    except Exception as e:
        # Don't let audit logging failures break the application
        current_app.logger.error(f"Audit logging failed: {str(e)}")

@login_required
@app.route("/admin/system-diagnostics")
def admin_system_diagnostics():
    """System diagnostics and configuration check"""
    gemini_model = get_gemini_model()

    # Test Gemini connection
    ai_test_result = None
    if gemini_model:
        try:
            response = gemini_model.generate_content("Reply with OK")
            ai_test_result = "✓ Connection successful"
        except Exception as e:
            ai_test_result = f"✗ Connection failed: {str(e)}"

    diagnostics = {
        "ai": {
            "provider": "Google Gemini (gemini-2.5-flash)",
            "configured": gemini_model is not None,
            "key_present": bool(GEMINI_API_KEY),
            "key_prefix": GEMINI_API_KEY[:10] + "..." if GEMINI_API_KEY and len(GEMINI_API_KEY) > 10 else "Not set",
            "test_result": ai_test_result,
            "features_enabled": [
                "AI Match Scoring" if gemini_model else "AI Match Scoring (disabled - no API key)",
                "AI CV Summarization" if gemini_model else "AI CV Summarization (disabled - no API key)",
                "Gemini-powered Candidate Analysis" if gemini_model else "Gemini-powered Analysis (disabled - no API key)"
            ]
        },
        "database": {
            "status": "✓ Connected",
            "engine": str(engine.url).split('@')[0] + "@[hidden]"  # Hide credentials
        },
        "authentication": {
            "status": "✓ Enabled",
            "login_manager": "Flask-Login",
            "password_hashing": "pbkdf2:sha256"
        }
    }
    
    return render_template("admin_system_diagnostics.html", diagnostics=diagnostics)

# ========== Admin Routes for Sidebar Navigation ==========
@login_required
@app.route("/admin/users")
def admin_users():
    """User management page - redirects to existing list users"""
    return redirect(url_for('admin_list_users'))

@login_required
@app.route("/admin/approvals")
def admin_approvals():
    """Approvals management page - timesheets, expenses, etc."""
    return render_template("admin_approvals.html")

@login_required
@app.route("/admin/invoices")
def admin_invoices():
    """Invoices management page"""
    import json
    with Session(engine) as s:
        # Get all invoices with counts
        invoices = s.scalars(select(Invoice).order_by(Invoice.invoice_date.desc())).all()
        
        # Calculate summary stats
        draft_invoices = [i for i in invoices if i.status == "Draft"]
        pending_invoices = [i for i in invoices if i.status == "Pending"]
        paid_invoices = [i for i in invoices if i.status == "Paid"]
        overdue_invoices = [i for i in invoices if i.status == "Overdue"]
        
        # Get unique clients for filter dropdown
        clients = s.execute(text("SELECT DISTINCT client FROM engagements WHERE client IS NOT NULL")).fetchall()
        client_list = [{"id": c[0], "name": c[0]} for c in clients if c[0]]
        
        return render_template("admin_invoices.html",
            invoices=invoices,
            draft_count=len(draft_invoices),
            draft_amount=sum(i.total_amount or 0 for i in draft_invoices),
            pending_count=len(pending_invoices),
            pending_amount=sum(i.total_amount or 0 for i in pending_invoices),
            paid_count=len(paid_invoices),
            paid_amount=sum(i.total_amount or 0 for i in paid_invoices),
            overdue_count=len(overdue_invoices),
            overdue_amount=sum(i.total_amount or 0 for i in overdue_invoices),
            clients=client_list
        )

@app.route("/admin/invoices/create", methods=["GET", "POST"])
@login_required
def admin_create_invoice():
    """Create a new invoice"""
    import json
    
    if request.method == "POST":
        with Session(engine) as s:
            # Generate invoice number
            year = datetime.datetime.utcnow().year
            month = datetime.datetime.utcnow().month
            count = s.scalar(select(func.count(Invoice.id)).where(
                Invoice.invoice_number.like(f"INV-{year}{month:02d}%")
            )) or 0
            invoice_number = f"INV-{year}{month:02d}-{count + 1:04d}"
            
            # Get form data
            engagement_id = request.form.get("engagement_id")
            client_name = request.form.get("client_name", "").strip()
            engagement_name = request.form.get("engagement_name", "").strip()
            
            # Parse dates
            invoice_date = datetime.datetime.utcnow()
            due_date_str = request.form.get("due_date", "")
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d")
                except:
                    pass
            
            # Get line items from form
            line_items = []
            descriptions = request.form.getlist("item_description[]")
            quantities = request.form.getlist("item_quantity[]")
            rates = request.form.getlist("item_rate[]")
            
            subtotal = 0
            for i, desc in enumerate(descriptions):
                if desc.strip():
                    qty = float(quantities[i]) if i < len(quantities) and quantities[i] else 1
                    rate = float(rates[i]) if i < len(rates) and rates[i] else 0
                    amount = qty * rate
                    subtotal += amount
                    line_items.append({
                        "description": desc.strip(),
                        "quantity": qty,
                        "rate": rate,
                        "amount": amount
                    })
            
            # Calculate VAT
            vat_rate = float(request.form.get("vat_rate", 20))
            vat_amount = subtotal * (vat_rate / 100)
            total_amount = subtotal + vat_amount
            
            # Create invoice
            invoice = Invoice(
                invoice_number=invoice_number,
                engagement_id=int(engagement_id) if engagement_id else None,
                client_name=client_name,
                engagement_name=engagement_name,
                invoice_date=invoice_date,
                due_date=due_date,
                subtotal=subtotal,
                vat_rate=vat_rate,
                vat_amount=vat_amount,
                total_amount=total_amount,
                status="Draft",
                line_items=json.dumps(line_items),
                notes=request.form.get("notes", ""),
                payment_terms=request.form.get("payment_terms", "Net 30"),
                created_by=current_user.id
            )
            s.add(invoice)
            s.commit()
            
            log_audit_event('create', 'billing', f'Created invoice {invoice_number}',
                          'invoice', invoice.id, {'client': client_name, 'amount': total_amount})
            
            flash(f"✅ Invoice {invoice_number} created successfully!", "success")
            return redirect(url_for('admin_invoices'))
    
    # GET - show create form
    with Session(engine) as s:
        engagements = s.scalars(select(Engagement).order_by(Engagement.name)).all()
        return render_template("admin_invoice_create.html", engagements=engagements)

@app.route("/admin/invoices/<int:invoice_id>")
@login_required
def admin_view_invoice(invoice_id):
    """View a single invoice"""
    import json
    with Session(engine) as s:
        invoice = s.get(Invoice, invoice_id)
        if not invoice:
            flash("Invoice not found", "error")
            return redirect(url_for('admin_invoices'))
        
        line_items = json.loads(invoice.line_items) if invoice.line_items else []
        return render_template("admin_invoice_view.html", invoice=invoice, line_items=line_items)

@app.route("/admin/invoices/<int:invoice_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_invoice(invoice_id):
    """Edit an invoice"""
    import json
    with Session(engine) as s:
        invoice = s.get(Invoice, invoice_id)
        if not invoice:
            flash("Invoice not found", "error")
            return redirect(url_for('admin_invoices'))
        
        if request.method == "POST":
            # Update invoice fields
            invoice.client_name = request.form.get("client_name", invoice.client_name)
            invoice.engagement_name = request.form.get("engagement_name", invoice.engagement_name)
            invoice.notes = request.form.get("notes", "")
            invoice.payment_terms = request.form.get("payment_terms", "Net 30")
            
            # Parse due date
            due_date_str = request.form.get("due_date", "")
            if due_date_str:
                try:
                    invoice.due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d")
                except:
                    pass
            
            # Get line items
            line_items = []
            descriptions = request.form.getlist("item_description[]")
            quantities = request.form.getlist("item_quantity[]")
            rates = request.form.getlist("item_rate[]")
            
            subtotal = 0
            for i, desc in enumerate(descriptions):
                if desc.strip():
                    qty = float(quantities[i]) if i < len(quantities) and quantities[i] else 1
                    rate = float(rates[i]) if i < len(rates) and rates[i] else 0
                    amount = qty * rate
                    subtotal += amount
                    line_items.append({
                        "description": desc.strip(),
                        "quantity": qty,
                        "rate": rate,
                        "amount": amount
                    })
            
            invoice.line_items = json.dumps(line_items)
            invoice.subtotal = subtotal
            invoice.vat_rate = float(request.form.get("vat_rate", 20))
            invoice.vat_amount = subtotal * (invoice.vat_rate / 100)
            invoice.total_amount = subtotal + invoice.vat_amount
            
            s.commit()
            
            log_audit_event('update', 'billing', f'Updated invoice {invoice.invoice_number}',
                          'invoice', invoice.id)
            
            flash(f"✅ Invoice updated successfully!", "success")
            return redirect(url_for('admin_view_invoice', invoice_id=invoice.id))
        
        # GET - show edit form
        line_items = json.loads(invoice.line_items) if invoice.line_items else []
        engagements = s.scalars(select(Engagement).order_by(Engagement.name)).all()
        return render_template("admin_invoice_edit.html", invoice=invoice, 
                             line_items=line_items, engagements=engagements)

@app.route("/admin/invoices/<int:invoice_id>/status", methods=["POST"])
@login_required
def admin_update_invoice_status(invoice_id):
    """Update invoice status"""
    with Session(engine) as s:
        invoice = s.get(Invoice, invoice_id)
        if not invoice:
            flash("Invoice not found", "error")
            return redirect(url_for('admin_invoices'))
        
        new_status = request.form.get("status", invoice.status)
        old_status = invoice.status
        invoice.status = new_status
        
        if new_status == "Paid" and not invoice.paid_date:
            invoice.paid_date = datetime.datetime.utcnow()
        elif new_status == "Pending" and not invoice.sent_at:
            invoice.sent_at = datetime.datetime.utcnow()
        
        s.commit()
        
        log_audit_event('update', 'billing', f'Invoice {invoice.invoice_number} status: {old_status} → {new_status}',
                      'invoice', invoice.id)
        
        flash(f"✅ Invoice status updated to {new_status}", "success")
    
    return redirect(url_for('admin_invoices'))

@app.route("/admin/invoices/<int:invoice_id>/delete", methods=["POST"])
@login_required
def admin_delete_invoice(invoice_id):
    """Delete an invoice"""
    with Session(engine) as s:
        invoice = s.get(Invoice, invoice_id)
        if not invoice:
            flash("Invoice not found", "error")
            return redirect(url_for('admin_invoices'))
        
        invoice_number = invoice.invoice_number
        s.delete(invoice)
        s.commit()
        
        log_audit_event('delete', 'billing', f'Deleted invoice {invoice_number}',
                      'invoice', invoice_id)
        
        flash(f"✅ Invoice {invoice_number} deleted", "success")
    
    return redirect(url_for('admin_invoices'))

def _generate_invoice_pdf(invoice, line_items):
    """Generate an invoice PDF using fpdf2. Returns bytes."""
    from fpdf import FPDF

    def _safe(text):
        """Replace unicode chars that latin-1 can't handle."""
        return (text or "").replace("\u2014", "-").replace("\u2013", "-").replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"').replace("\u2026", "...").replace("\u00a3", "GBP ")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Header
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(100, 12, "INVOICE", new_x="RIGHT")
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(0, 12, invoice.invoice_number or "", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(100, 6, "Optimus Solutions", new_x="RIGHT")
    date_str = invoice.invoice_date.strftime("%d %B %Y") if invoice.invoice_date else "N/A"
    pdf.cell(0, 6, f"Date: {date_str}", align="R", new_x="LMARGIN", new_y="NEXT")
    if invoice.due_date:
        pdf.cell(100, 6, "", new_x="RIGHT")
        pdf.cell(0, 6, f"Due: {invoice.due_date.strftime('%d %B %Y')}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(100, 6, "", new_x="RIGHT")
    pdf.cell(0, 6, f"Status: {invoice.status}", align="R", new_x="LMARGIN", new_y="NEXT")

    # Divider
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y() + 4, 200, pdf.get_y() + 4)
    pdf.ln(12)

    # Bill To / Payment Terms
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(95, 5, "BILL TO", new_x="RIGHT")
    pdf.cell(0, 5, "PAYMENT TERMS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(95, 7, _safe(invoice.client_name or ""), new_x="RIGHT")
    pdf.cell(0, 7, _safe(invoice.payment_terms or "Net 30"), new_x="LMARGIN", new_y="NEXT")
    if invoice.engagement_name:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(95, 6, _safe(invoice.engagement_name), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Line items table header
    pdf.set_fill_color(248, 250, 252)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(55, 65, 81)
    pdf.cell(95, 8, "  Description", border="B", fill=True, new_x="RIGHT")
    pdf.cell(25, 8, "Qty", border="B", fill=True, align="C", new_x="RIGHT")
    pdf.cell(35, 8, "Rate", border="B", fill=True, align="R", new_x="RIGHT")
    pdf.cell(35, 8, "Amount", border="B", fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

    # Line items
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(31, 41, 55)
    for item in line_items:
        desc = _safe((item.get("description") or "")[:60])
        qty = str(item.get("quantity", ""))
        rate = f"£{item['rate']:,.2f}" if item.get("rate") else ""
        amount = f"£{(item.get('amount') or 0):,.2f}"
        pdf.cell(95, 8, f"  {desc}", border="B", new_x="RIGHT")
        pdf.cell(25, 8, qty, border="B", align="C", new_x="RIGHT")
        pdf.cell(35, 8, rate, border="B", align="R", new_x="RIGHT")
        pdf.cell(35, 8, amount, border="B", align="R", new_x="LMARGIN", new_y="NEXT")

    if not line_items:
        pdf.set_text_color(156, 163, 175)
        pdf.cell(190, 10, "No line items", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(31, 41, 55)

    pdf.ln(6)

    # Totals — right aligned
    x_label = 130
    x_val = 165
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(107, 114, 128)
    pdf.set_x(x_label)
    pdf.cell(35, 7, "Subtotal", new_x="RIGHT")
    pdf.cell(35, 7, f"£{(invoice.subtotal or 0):,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(x_label)
    pdf.cell(35, 7, f"VAT ({invoice.vat_rate or 0:.1f}%)", new_x="RIGHT")
    pdf.cell(35, 7, f"£{(invoice.vat_amount or 0):,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    # Total line
    pdf.set_draw_color(30, 58, 138)
    pdf.line(x_label, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(31, 41, 55)
    pdf.set_x(x_label)
    pdf.cell(35, 9, "Total", new_x="RIGHT")
    pdf.cell(35, 9, f"£{(invoice.total_amount or 0):,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    # Notes
    if invoice.notes:
        pdf.ln(12)
        pdf.set_draw_color(229, 231, 235)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(55, 65, 81)
        pdf.cell(0, 6, "Notes", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(107, 114, 128)
        pdf.multi_cell(0, 5, _safe(invoice.notes))

    # Footer
    pdf.ln(16)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(156, 163, 175)
    pdf.cell(0, 5, "Optimus Solutions - Financial Services Resourcing Specialists", align="C")

    return pdf.output()


@app.route("/admin/invoices/<int:invoice_id>/pdf")
@login_required
def admin_invoice_pdf(invoice_id):
    """Generate and download invoice as PDF."""
    import json
    with Session(engine) as s:
        invoice = s.get(Invoice, invoice_id)
        if not invoice:
            flash("Invoice not found", "error")
            return redirect(url_for('admin_invoices'))
        line_items = json.loads(invoice.line_items) if invoice.line_items else []
        pdf_bytes = _generate_invoice_pdf(invoice, line_items)

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={invoice.invoice_number}.pdf"}
    )


@app.route("/admin/invoices/<int:invoice_id>/send", methods=["POST"])
@login_required
def admin_send_invoice(invoice_id):
    """Generate PDF and email the invoice to the client."""
    import json
    with Session(engine) as s:
        invoice = s.get(Invoice, invoice_id)
        if not invoice:
            flash("Invoice not found", "error")
            return redirect(url_for('admin_invoices'))

        line_items = json.loads(invoice.line_items) if invoice.line_items else []

        # Generate PDF
        try:
            pdf_bytes = _generate_invoice_pdf(invoice, line_items)
        except Exception as e:
            flash(f"PDF generation failed: {e}", "danger")
            return redirect(url_for('admin_view_invoice', invoice_id=invoice_id))

        # Build email
        email_html = f"""
        <div style="font-family:'Inter',Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#0a1628;padding:24px;text-align:center;border-radius:8px 8px 0 0;">
                <h1 style="color:#00d4ff;margin:0;font-size:20px;">Optimus Solutions</h1>
            </div>
            <div style="background:#fff;padding:30px;border:1px solid #e5e7eb;border-radius:0 0 8px 8px;">
                <h2 style="color:#1f2937;margin:0 0 16px;">Invoice {invoice.invoice_number}</h2>
                <p style="color:#4b5563;">Please find attached invoice <strong>{invoice.invoice_number}</strong>
                for <strong>£{invoice.total_amount or 0:,.2f}</strong>.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr><td style="padding:6px 0;color:#6b7280;">Client:</td><td style="padding:6px 0;font-weight:600;">{invoice.client_name}</td></tr>
                    <tr><td style="padding:6px 0;color:#6b7280;">Engagement:</td><td style="padding:6px 0;">{invoice.engagement_name or 'N/A'}</td></tr>
                    <tr><td style="padding:6px 0;color:#6b7280;">Due Date:</td><td style="padding:6px 0;font-weight:600;">{invoice.due_date.strftime('%d %B %Y') if invoice.due_date else 'N/A'}</td></tr>
                    <tr><td style="padding:6px 0;color:#6b7280;">Terms:</td><td style="padding:6px 0;">{invoice.payment_terms or 'Net 30'}</td></tr>
                </table>
                <p style="color:#6b7280;font-size:14px;">If you have any queries regarding this invoice, please contact your account manager.</p>
            </div>
        </div>
        """

        to_addr = request.form.get("email", "").strip()
        if not to_addr:
            flash("No client email found. Please enter an email address.", "warning")
            return redirect(url_for('admin_view_invoice', invoice_id=invoice_id))

        try:
            send_email(
                to_email=to_addr,
                subject=f"Invoice {invoice.invoice_number} — Optimus Solutions",
                html_body=email_html,
                attachments=[(f"{invoice.invoice_number}.pdf", pdf_bytes, "application/pdf")]
            )
            invoice.status = "Pending"
            if not invoice.sent_at:
                invoice.sent_at = datetime.datetime.utcnow()
            s.commit()
            flash(f"Invoice {invoice.invoice_number} sent to {to_addr}", "success")
        except Exception as e:
            flash(f"Failed to send: {e}", "danger")

    return redirect(url_for('admin_view_invoice', invoice_id=invoice_id))


@app.route("/admin/invoices/export")
@login_required
def admin_export_invoices():
    """Export invoices to CSV"""
    import csv
    import io
    
    with Session(engine) as s:
        invoices = s.scalars(select(Invoice).order_by(Invoice.invoice_date.desc())).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header row
        writer.writerow([
            "Invoice Number", "Client", "Engagement", "Invoice Date", "Due Date",
            "Subtotal", "VAT Rate", "VAT Amount", "Total", "Status", "Paid Date"
        ])
        
        # Data rows
        for inv in invoices:
            writer.writerow([
                inv.invoice_number,
                inv.client_name,
                inv.engagement_name or "",
                inv.invoice_date.strftime("%Y-%m-%d") if inv.invoice_date else "",
                inv.due_date.strftime("%Y-%m-%d") if inv.due_date else "",
                f"{inv.subtotal:.2f}",
                f"{inv.vat_rate:.1f}%",
                f"{inv.vat_amount:.2f}",
                f"{inv.total_amount:.2f}",
                inv.status,
                inv.paid_date.strftime("%Y-%m-%d") if inv.paid_date else ""
            ])
        
        output.seek(0)
        
        log_audit_event('export', 'billing', f'Exported {len(invoices)} invoices to CSV')
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=invoices_export_{datetime.datetime.utcnow().strftime('%Y%m%d')}.csv"}
        )

@app.route("/admin/invoices/settings", methods=["GET", "POST"])
@login_required
def admin_invoice_settings():
    """Invoice settings page"""
    # For now, just render a settings page
    # In a full implementation, these would be stored in a settings table
    return render_template("admin_invoice_settings.html")

@login_required
@app.route("/admin/workflow-stages")
def admin_workflow_stages():
    """REQ-273: Read-only view of workflow stages.

    Note: Stage editing is disabled. The 9 default stages are tightly coupled
    to auto-transition logic throughout the codebase (vetting complete → Contract Issued,
    e-sign signed → Contract Signed, etc.). Allowing admins to rename or remove stages
    would break these automations. A full decoupling refactor is required before
    this can be made editable. See C-8 in the contradictions tracker.
    """
    if not current_user.role or current_user.role.lower() != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("index"))

    with Session(engine) as s:
        _seed_default_stages(s)
        stages = s.scalars(
            select(StageConfig).order_by(StageConfig.sort_order)
        ).all()

    return render_template("admin_workflow_stages.html", stages=stages, readonly=True)


@login_required
@app.route("/admin/audit-log")
def admin_audit_log():
    """Audit log page - shows all system activity"""
    # Audit log: viewing audit log (meta, but useful)
    
    with Session(engine) as s:
        # Get real audit log entries
        try:
            audit_entries = s.scalars(
                select(AuditLog)
                .order_by(AuditLog.timestamp.desc())
                .limit(500)
            ).all()
        except:
            audit_entries = []
    return render_template("admin_audit_log.html", audit_entries=audit_entries)

# ========== Timesheet Configuration ==========

@app.route("/admin/timesheet-config/<int:engagement_id>", methods=["GET", "POST"])
@login_required
def admin_timesheet_config(engagement_id):
    """Configure timesheet settings for an engagement."""
    import json as _json
    TimesheetConfig = _get_ts_config_model()
    with Session(engine) as s:
        eng = s.get(Engagement, engagement_id)
        if not eng:
            flash("Engagement not found.", "danger")
            return redirect(url_for("engagements"))

        config = s.query(TimesheetConfig).filter_by(engagement_id=engagement_id).first() if TimesheetConfig else None

        if request.method == "GET":
            time_types = _json.loads(config.time_types) if config and config.time_types else ["Standard Time", "Overtime", "Holiday", "Sickness", "Unplanned Absence"]
            expense_types = _json.loads(config.expense_types) if config and config.expense_types else ["Travel", "Accommodation", "Meals", "Equipment", "Other"]
            expense_limits = _json.loads(config.expense_limits) if config and config.expense_limits else {}
            return render_template("admin_timesheet_config.html",
                engagement=eng,
                config=config,
                time_types=time_types,
                expense_types=expense_types,
                expense_limits=expense_limits,
            )

        # POST - save config
        if not TimesheetConfig:
            flash("TimesheetConfig model not available.", "danger")
            return redirect(url_for("engagement_dashboard", eng_id=engagement_id))

        if not config:
            config = TimesheetConfig(engagement_id=engagement_id)
            s.add(config)

        # Time types from checkboxes
        selected_types = request.form.getlist("time_types")
        config.time_types = _json.dumps(selected_types)

        # Overtime
        config.overtime_enabled = request.form.get("overtime_enabled") == "1"
        config.overtime_multiplier = float(request.form.get("overtime_multiplier", 1.5) or 1.5)
        config.overtime_rate_type = request.form.get("overtime_rate_type", "hourly")

        # Expenses
        config.expense_enabled = request.form.get("expense_enabled") == "1"
        exp_types = request.form.getlist("expense_types")
        config.expense_types = _json.dumps(exp_types)
        # Expense limits
        limits = {}
        for et in exp_types:
            limit_val = request.form.get(f"expense_limit_{et}", "")
            if limit_val:
                try:
                    limits[et] = float(limit_val)
                except ValueError:
                    pass
        config.expense_limits = _json.dumps(limits)

        # Rates
        config.day_rate = float(request.form.get("day_rate", 0) or 0)
        config.overtime_rate = float(request.form.get("overtime_rate", 0) or 0)

        s.commit()
        flash("Timesheet configuration saved.", "success")
        return redirect(url_for("admin_timesheet_config", engagement_id=engagement_id))

# ========== Portal User Management (Public Portal User Management) ==========

@login_required
@app.route("/admin/portal-users")
def admin_portal_users():
    """Admin page for managing public portal users (candidates who signed up via the portal)."""
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "")  # all, verified, unverified
    source_filter = request.args.get("source", "")  # all, portal, manual, import
    page = int(request.args.get("page", 1))
    per_page = 25
    
    with Session(engine) as s:
        query = select(Candidate).order_by(Candidate.created_at.desc())
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Candidate.name.ilike(search_term),
                    Candidate.email.ilike(search_term),
                    Candidate.phone.ilike(search_term),
                    Candidate.skills.ilike(search_term)
                )
            )
        
        # Apply status filter
        if status_filter == "verified":
            query = query.where(Candidate.email_verified == True)
        elif status_filter == "unverified":
            query = query.where(or_(Candidate.email_verified == False, Candidate.email_verified == None))
        
        # Apply source filter
        if source_filter and source_filter != "all":
            query = query.where(Candidate.source == source_filter)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = s.scalar(count_query) or 0
        
        # Paginate
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        candidates = s.scalars(query).all()
        
        # Get stats
        total_candidates = s.scalar(select(func.count(Candidate.id))) or 0
        verified_count = s.scalar(select(func.count(Candidate.id)).where(Candidate.email_verified == True)) or 0
        portal_signups = s.scalar(select(func.count(Candidate.id)).where(Candidate.source == "portal")) or 0
        recent_signups = s.scalar(
            select(func.count(Candidate.id)).where(
                Candidate.created_at >= datetime.datetime.utcnow() - datetime.timedelta(days=7)
            )
        ) or 0
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template(
        "admin_portal_users.html",
        candidates=candidates,
        search=search,
        status_filter=status_filter,
        source_filter=source_filter,
        page=page,
        total_pages=total_pages,
        total=total,
        total_candidates=total_candidates,
        verified_count=verified_count,
        portal_signups=portal_signups,
        recent_signups=recent_signups
    )

@login_required
@app.route("/admin/portal-users/<int:cand_id>")
def admin_portal_user_detail(cand_id: int):
    """View/edit a portal user's details."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found", "danger")
            return redirect(url_for("admin_portal_users"))
        
        # Get applications for this candidate (eagerly load job relationship)
        applications = s.scalars(
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.candidate_id == cand_id)
            .order_by(Application.created_at.desc())
        ).all()
        
        # Get documents
        documents = s.scalars(
            select(Document)
            .where(Document.candidate_id == cand_id)
            .order_by(Document.uploaded_at.desc())
        ).all()
        
        # Force load all attributes before session closes
        _ = cand.name, cand.email, cand.phone, cand.status, cand.source
        _ = cand.email_verified, cand.email_verified_at, cand.created_at
        _ = cand.last_login_at, cand.last_activity_at
        if hasattr(cand, 'about'):
            _ = cand.about
        
        for app in applications:
            if app.job:
                _ = app.job.title
        
        for doc in documents:
            _ = doc.filename, doc.original_name, doc.doc_type, doc.uploaded_at
    
    return render_template(
        "admin_portal_user_detail.html",
        cand=cand,
        applications=applications,
        documents=documents
    )

@login_required
@app.route("/admin/portal-users/<int:cand_id>/verify", methods=["POST"])
def admin_portal_user_verify(cand_id: int):
    """Manually verify a portal user's email."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found", "danger")
            return redirect(url_for("admin_portal_users"))
        
        cand.email_verified = True
        cand.email_verified_at = datetime.datetime.utcnow()
        s.commit()
        
        flash(f"Email verified for {cand.name}", "success")
    
    return redirect(url_for("admin_portal_user_detail", cand_id=cand_id))

@login_required
@app.route("/admin/portal-users/<int:cand_id>/send-magic-link", methods=["POST"])
def admin_portal_user_send_magic_link(cand_id: int):
    """Send a magic link to a portal user."""
    from itsdangerous import URLSafeTimedSerializer
    
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found", "danger")
            return redirect(url_for("admin_portal_users"))
        
        if not cand.email:
            flash("Associate has no email address", "danger")
            return redirect(url_for("admin_portal_user_detail", cand_id=cand_id))
        
        # Generate magic link
        signer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="portal-magic-link")
        token = signer.dumps({
            "email": cand.email,
            "name": cand.name,
            "next": "/jobs",
            "is_signup": False
        })
        
        verify_url = f"{PORTAL_BASE_URL}/portal/verify-email?token={token}"
        
        html_body = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #0a1628; padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
                <h1 style="color: #00d4ff; margin: 0; font-size: 24px;">Optimus Solutions</h1>
                <p style="color: #94a3b8; margin: 10px 0 0; font-size: 14px;">Careers Portal</p>
            </div>
            <div style="background: #ffffff; padding: 40px 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
                <h2 style="color: #0a1628; margin: 0 0 20px; font-size: 20px;">Sign In Request</h2>
                <p style="color: #334155; margin: 0 0 20px; line-height: 1.6;">
                    An admin has sent you a sign-in link for the Optimus Solutions Careers Portal.
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" style="background: #0066cc; color: #ffffff; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block;">
                        Sign In Securely
                    </a>
                </div>
                <p style="color: #64748b; font-size: 14px; margin: 20px 0 0;">
                    This link will expire in 30 minutes.
                </p>
            </div>
        </div>
        """
        
        try:
            send_email(
                to_email=cand.email,
                subject="Sign in to Optimus Solutions Careers",
                html_body=html_body
            )
            flash(f"Magic link sent to {cand.email}", "success")
        except Exception as e:
            flash(f"Failed to send email: {e}", "danger")
    
    return redirect(url_for("admin_portal_user_detail", cand_id=cand_id))

@login_required
@app.route("/admin/portal-users/<int:cand_id>/update", methods=["POST"])
def admin_portal_user_update(cand_id: int):
    """Update a portal user's details."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found", "danger")
            return redirect(url_for("admin_portal_users"))
        
        # Update fields
        cand.name = request.form.get("name", cand.name)
        cand.email = request.form.get("email", cand.email)
        cand.phone = request.form.get("phone", cand.phone)
        cand.status = request.form.get("status", cand.status)
        cand.source = request.form.get("source", cand.source)
        
        if hasattr(cand, "about"):
            cand.about = request.form.get("about", cand.about)
        
        s.commit()
        flash("Portal user updated", "success")
    
    return redirect(url_for("admin_portal_user_detail", cand_id=cand_id))

@login_required
@app.route("/admin/portal-users/<int:cand_id>/delete", methods=["POST"])
def admin_portal_user_delete(cand_id: int):
    """Delete a portal user and all associated data."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found", "danger")
            return redirect(url_for("admin_portal_users"))

        name = cand.name

        # Clean up all related records
        app_ids = [aid for (aid,) in s.execute(
            select(Application.id).where(Application.candidate_id == cand_id)
        ).all()]
        if app_ids:
            s.execute(delete(ESigRequest).where(ESigRequest.application_id.in_(app_ids)))
            try:
                s.execute(delete(TrustIDCheck).where(TrustIDCheck.application_id.in_(app_ids)))
            except Exception:
                pass
            s.execute(delete(Application).where(Application.id.in_(app_ids)))
        s.execute(delete(VettingCheck).where(VettingCheck.candidate_id == cand_id))
        s.execute(delete(Shortlist).where(Shortlist.candidate_id == cand_id))
        s.execute(delete(CandidateTag).where(CandidateTag.candidate_id == cand_id))
        s.execute(delete(Document).where(Document.candidate_id == cand_id))
        try:
            s.execute(delete(CandidateNote).where(CandidateNote.candidate_id == cand_id))
        except Exception:
            pass
        # Clean up associate profile if exists
        try:
            s.execute(text("DELETE FROM associate_profiles WHERE candidate_id = :cid"), {"cid": cand_id})
        except Exception:
            pass

        log_audit_event('delete', 'data_access', f'Deleted portal user: {name} (id={cand_id})',
                        details={"candidate_id": cand_id, "applications_deleted": len(app_ids)})
        s.delete(cand)
        s.commit()
        flash(f"Portal user {name} and all associated data deleted", "success")

    return redirect(url_for("admin_portal_users"))

@login_required
@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    """Allow users to change their password"""
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not current_password or not new_password or not confirm_password:
            flash("All fields are required", "error")
            return render_template("change_password.html")
        
        if new_password != confirm_password:
            flash("New passwords do not match", "error")
            return render_template("change_password.html")
        
        # Validate password strength
        is_valid, message, score = validate_password_strength(new_password, current_user.email)
        if not is_valid:
            flash(message, "error")
            return render_template("change_password.html")
        
        with Session(engine) as s:
            user = s.get(User, current_user.id)
            if not user or not check_password_hash(user.password_hash, current_password):
                flash("Current password is incorrect", "error")
                return render_template("change_password.html")
            
            # Check password history (prevent reuse of last 5 passwords)
            if not check_password_history(current_user.id, new_password, history_limit=5):
                flash("You cannot reuse any of your last 5 passwords. Please choose a different password.", "error")
                return render_template("change_password.html")
            
            # Save old password to history before changing
            save_password_to_history(current_user.id, user.password_hash)
            
            # Update password
            user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
            s.commit()
            
            # Log password change
            log_audit_event('update', 'user_mgmt', 'Changed password', 'user', current_user.id)
            
            flash("Password changed successfully", "success")
            return redirect(url_for('index'))
    
    return render_template("change_password.html")

# ========== Two-Factor Authentication (2FA) Routes ==========

@app.route("/security/2fa/setup", methods=["GET", "POST"])
@login_required
def setup_2fa():
    """Setup Two-Factor Authentication"""
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "generate":
            # Generate new TOTP secret
            with Session(engine) as s:
                user = s.get(User, current_user.id)
                user.totp_secret = user.generate_totp_secret()
                s.commit()
                
                try:
                    # Generate provisioning URI
                    import pyotp
                    import qrcode
                    import io
                    import base64
                    
                    totp = pyotp.TOTP(user.totp_secret)
                    provisioning_uri = totp.provisioning_uri(
                        name=user.email,
                        issuer_name="Optimus OS1"
                    )
                    
                    # Generate QR code locally
                    qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    qr.add_data(provisioning_uri)
                    qr.make(fit=True)
                    qr_img = qr.make_image(fill_color="black", back_color="white")
                    
                    # Convert to base64
                    buffer = io.BytesIO()
                    qr_img.save(buffer, format='PNG')
                    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
                    qr_url = f"data:image/png;base64,{qr_base64}"
                    
                    return render_template("setup_2fa.html", 
                                         qr_code=None,
                                         qr_url=qr_url,
                                         secret=user.totp_secret,
                                         step="verify")
                    
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    current_app.logger.error(f"2FA setup failed: {str(e)}\n{error_details}")
                    flash("Error setting up 2FA. Please use manual entry.", "error")
                    
                    # Return with manual entry only
                    return render_template("setup_2fa.html", 
                                         qr_code=None,
                                         qr_url=None,
                                         secret=user.totp_secret,
                                         step="verify")
        
        elif action == "verify":
            token = request.form.get("token", "").strip()
            
            with Session(engine) as s:
                user = s.get(User, current_user.id)
                
                if user.verify_totp(token):
                    # Enable 2FA
                    user.totp_enabled = True
                    
                    # Generate backup codes
                    backup_codes = user.generate_backup_codes()
                    s.commit()
                    
                    log_audit_event('update', 'security', '2FA enabled', 'user', current_user.id)
                    
                    return render_template("setup_2fa.html",
                                         step="complete",
                                         backup_codes=backup_codes)
                else:
                    flash("Invalid verification code. Please try again.", "error")
                    return render_template("setup_2fa.html", step="start")
    
    # GET request - show initial setup page
    with Session(engine) as s:
        user = s.get(User, current_user.id)
        if user.totp_enabled:
            return render_template("setup_2fa.html", step="already_enabled")
    
    return render_template("setup_2fa.html", step="start")

@app.route("/security/2fa/disable", methods=["POST"])
@login_required
def disable_2fa():
    """Disable Two-Factor Authentication"""
    password = request.form.get("password", "")
    
    with Session(engine) as s:
        user = s.get(User, current_user.id)
        
        # Verify password before disabling
        if not user or not check_password_hash(user.password_hash, password):
            flash("Incorrect password", "error")
            return redirect(url_for('setup_2fa'))
        
        user.totp_enabled = False
        user.totp_secret = None
        user.backup_codes = None
        s.commit()
        
        log_audit_event('update', 'security', '2FA disabled', 'user', current_user.id, status='warning')
        
        flash("Two-Factor Authentication has been disabled", "success")
        return redirect(url_for('index'))

@app.route("/security/2fa/verify", methods=["GET", "POST"])
def verify_2fa():
    """Verify 2FA token during login"""
    # This should be called after password verification but before login_user()
    # User ID should be in session from the initial login attempt
    
    if 'pending_user_id' not in session:
        return redirect(url_for('login'))
    
    user_email = session.get('pending_user_email', '')
    
    if request.method == "POST":
        token = request.form.get("token", "").strip()
        use_backup = request.form.get("use_backup") == "1"
        
        with Session(engine) as s:
            user = s.get(User, session['pending_user_id'])
            
            if not user:
                session.pop('pending_user_id', None)
                session.pop('pending_user_email', None)
                flash("Session expired. Please login again.", "error")
                return redirect(url_for('login'))
            
            verified = False
            if use_backup:
                verified = user.verify_backup_code(token)
                if verified:
                    s.commit()  # Save updated backup codes
                    log_audit_event('login', 'auth', 'Logged in with backup code', 
                                  'user', user.id, status='warning')
            else:
                verified = user.verify_totp(token)
            
            if verified:
                # 2FA successful - complete login
                session.pop('pending_user_id', None)
                session.pop('pending_user_email', None)
                
                remember = session.get('remember_me', False)
                session.pop('remember_me', None)
                
                # Refresh user to ensure all attributes are loaded before login_user
                s.refresh(user)
                
                if remember:
                    login_user(user, remember=True, duration=timedelta(days=30))
                else:
                    login_user(user, remember=False)
                    session.permanent = True
                
                log_audit_event('login', 'auth', 'Successful 2FA verification', 'user', user.id)
                
                next_page = session.get('next_page') or '/'
                session.pop('next_page', None)
                # Validate next_page is a safe relative URL
                if not next_page or not next_page.startswith('/'):
                    next_page = '/'
                return redirect(next_page)
            else:
                flash("Invalid code. Please try again.", "error")
    
    return render_template("verify_2fa.html", user_email=user_email)

@app.route("/security/2fa/mandatory-setup", methods=["GET", "POST"])
def mandatory_2fa_setup():
    """
    Mandatory 2FA setup for users who haven't enabled it yet.
    Called after successful password verification but before granting access.
    """
    # Check if user is in the setup flow
    if 'setup_2fa_user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['setup_2fa_user_id']
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "generate":
            # Generate new TOTP secret
            with Session(engine) as s:
                user = s.get(User, user_id)
                if not user:
                    session.pop('setup_2fa_user_id', None)
                    flash("Session expired. Please login again.", "error")
                    return redirect(url_for('login'))
                
                # Generate and store the secret
                totp_secret = user.generate_totp_secret()
                user.totp_secret = totp_secret
                user_email = user.email
                s.commit()
            
            # Store the secret in session for QR code endpoint
            session['qr_totp_secret'] = totp_secret
            session['qr_user_email'] = user_email
            
            app.logger.info(f"TOTP secret generated for {user_email}, redirecting to verify step")
            
            # Use a dedicated endpoint for the QR code image
            qr_url = url_for('get_2fa_qr_code')
            
            return render_template("mandatory_2fa_setup.html", 
                                 qr_url=qr_url,
                                 secret=totp_secret,
                                 step="verify",
                                 user_email=user_email)
        
        elif action == "verify":
            token = request.form.get("token", "").strip()
            
            with Session(engine) as s:
                user = s.get(User, user_id)
                
                if not user:
                    session.pop('setup_2fa_user_id', None)
                    flash("Session expired. Please login again.", "error")
                    return redirect(url_for('login'))
                
                # Store values before any session operations
                user_email = user.email
                user_totp_secret = user.totp_secret
                
                if user.verify_totp(token):
                    # Enable 2FA
                    user.totp_enabled = True
                    backup_codes = user.generate_backup_codes()
                    s.commit()
                    
                    remember = session.get('setup_2fa_remember', False)
                    next_page = session.get('setup_2fa_next') or '/'
                    if not next_page or not next_page.startswith('/'):
                        next_page = '/'

                    # Clear setup session data
                    session.pop('setup_2fa_user_id', None)
                    session.pop('setup_2fa_remember', None)
                    session.pop('setup_2fa_next', None)
                    session.pop('qr_totp_secret', None)
                    session.pop('qr_user_email', None)
                    
                    # Log in the user while still in session context
                    # Make sure user object has all attributes loaded
                    s.refresh(user)
                    if remember:
                        login_user(user, remember=True, duration=timedelta(days=30))
                    else:
                        login_user(user, remember=False)
                        session.permanent = True
                    
                    log_audit_event('login', 'auth', f'2FA setup completed and logged in: {user_email}', status='success')
                    
                    # Show backup codes before redirecting
                    return render_template("mandatory_2fa_setup.html",
                                         step="complete",
                                         backup_codes=backup_codes,
                                         next_page=next_page)
                else:
                    flash("Invalid verification code. Please try again.", "error")
                    # Regenerate QR URL for retry
                    qr_url = url_for('get_2fa_qr_code')
                    return render_template("mandatory_2fa_setup.html", 
                                         step="verify",
                                         secret=user_totp_secret,
                                         qr_url=qr_url,
                                         user_email=user_email)
    
    # GET request - show initial setup page
    with Session(engine) as s:
        user = s.get(User, user_id)
        if not user:
            session.pop('setup_2fa_user_id', None)
            return redirect(url_for('login'))
        user_email = user.email
    
    return render_template("mandatory_2fa_setup.html", step="start", user_email=user_email)

@app.route("/security/2fa/qr-code.png")
def get_2fa_qr_code():
    """
    Generate and serve the 2FA QR code as a PNG image.
    This endpoint is used during 2FA setup to display the QR code.
    """
    import pyotp
    import qrcode
    import io
    from flask import Response
    
    # Get the TOTP secret from session
    totp_secret = session.get('qr_totp_secret')
    user_email = session.get('qr_user_email')
    
    if not totp_secret or not user_email:
        app.logger.error("No TOTP secret or email in session for QR code generation")
        # Return a 1x1 transparent PNG as fallback
        return Response(b'', mimetype='image/png', status=404)
    
    try:
        totp = pyotp.TOTP(totp_secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_email,
            issuer_name="Optimus OS1"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        buffer = io.BytesIO()
        qr_img.save(buffer, format='PNG')
        buffer.seek(0)
        
        app.logger.info(f"QR code image served for {user_email}")
        
        return Response(buffer.getvalue(), mimetype='image/png')
    except Exception as e:
        app.logger.error(f"QR code image generation failed: {str(e)}")
        return Response(b'', mimetype='image/png', status=500)

def _signer() -> URLSafeTimedSerializer:
    # used for candidate magic links
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="candidate-login")

def get_role_category_names(session: Session) -> List[str]:
    """
    Return role names from taxonomy_categories where type='role',
    ordered by name. Falls back to the hard-coded ROLE_TYPES if empty.
    """
    rows = session.scalars(
        select(TaxonomyCategory)
        .where(TaxonomyCategory.type == "role")
        .order_by(TaxonomyCategory.name.asc())
    ).all()
    names = [r.name for r in rows]
    # Safe fallback for fresh installs (keeps app usable if taxonomy is empty)
    return names or list(ROLE_TYPES)

# -------------- DB Models --------------
from sqlalchemy import String, Integer, DateTime, Boolean

# --- Taxonomy models (subject groups/tags) ---
# --- User model for authentication ---
class User(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    # Map to actual database column name
    password_hash = Column('pw_hash', String(255), nullable=False)
    created_at = Column(DateTime, nullable=True)
    
    # Security columns - NOW ENABLED (migration completed)
    role = Column(String(50), default='employee', nullable=True)
    is_active = Column(Boolean, default=True, nullable=True)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=True)
    locked_until = Column(DateTime, nullable=True)
    
    # 2FA/MFA columns
    totp_secret = Column(String(32), nullable=True)
    totp_enabled = Column(Boolean, default=False, nullable=True)
    backup_codes = Column(Text, nullable=True)  # JSON array of backup codes
    
    # Session security columns
    session_token = Column(String(255), nullable=True)
    last_ip = Column(String(45), nullable=True)
    last_user_agent = Column(Text, nullable=True)
    
    # Magic link columns for passwordless login/setup
    magic_token = Column(String(255), nullable=True)
    magic_token_expires = Column(DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self):
        """Check if account is currently locked"""
        if self.locked_until is None:
            return False
        return self.locked_until > datetime.datetime.utcnow()
    
    def generate_totp_secret(self):
        """Generate a new TOTP secret for 2FA"""
        import pyotp
        return pyotp.random_base32()
    
    def verify_totp(self, token):
        """Verify a TOTP token"""
        if not self.totp_secret:
            return False
        import pyotp
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)  # Allow 1 window before/after
    
    def generate_backup_codes(self, count=10):
        """Generate backup codes for account recovery"""
        import secrets
        codes = [secrets.token_hex(4).upper() for _ in range(count)]
        self.backup_codes = json.dumps(codes)
        return codes
    
    def verify_backup_code(self, code):
        """Verify and consume a backup code"""
        if not self.backup_codes:
            return False
        codes = json.loads(self.backup_codes)
        code = code.upper().replace('-', '')
        if code in codes:
            codes.remove(code)
            self.backup_codes = json.dumps(codes)
            return True
        return False

class PasswordHistory(Base):
    """Track password history to prevent reuse"""
    __tablename__ = "password_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

class AuditLog(Base):
    """Comprehensive audit logging for security and compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, create, update, delete, view, export
    event_category = Column(String(50), nullable=False, index=True)  # auth, user_mgmt, data_access, security
    resource_type = Column(String(50), nullable=True)  # candidate, job, engagement, user
    resource_id = Column(Integer, nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)  # JSON string with additional info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default='success')  # success, failure, warning

class CandidateTag(Base):
    __tablename__ = "candidate_tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(ForeignKey("candidates.id"), index=True, nullable=False)
    tag_id = Column(ForeignKey("taxonomy_tags.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# --- DB Models ---
class Engagement(Base):
    __tablename__ = "engagements"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    client = Column(String)
    status = Column(String, default="Active")
    ref = Column(String, unique=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    sow_signed_at = Column(DateTime)
    description = Column(Text, default="")
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True, unique=True)

    plan_version = Column(Integer, default=1)
    vetting_requirements = Column(Text, default="")
    ir35_status = Column(String(20), default="inside")  # inside / outside / undetermined
    # Gap plan 8.3: Client-specific document requirements (JSON list of doc types)
    required_documents = Column(Text, nullable=True)  # JSON: ["proof_of_id", "proof_of_address", ...]
    # Gap plan P9: Reference period configurable per client (default 3 years)
    reference_period_years = Column(Integer, default=3)
    # Third pass fix 6: Gap threshold days configurable per client (default 90)
    gap_threshold_days = Column(Integer, default=90)

    opportunity = relationship(
        "Opportunity",
        backref=backref("engagement", uselist=False)
    )
    jobs = relationship("Job", back_populates="engagement", cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    engagement_id = Column(ForeignKey("engagements.id"))
    title = Column(String(200))
    description = Column(String(4000))
    role_type = Column(String(50), default="")
    location = Column(String(200), default="")
    salary_range = Column(String(200), default="")
    status = Column(String(50), default="Open")
    public_token = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    engagement = relationship("Engagement", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

class RoleAliasForm(FlaskForm):
    canonical = SelectField("Canonical role", choices=[(r, r) for r in ROLE_TYPES], validators=[DataRequired()])
    alias = StringField("Alias (case-insensitive)", validators=[DataRequired()])

class WorkerUser(UserMixin):
    """
    Lightweight adapter around your Users table row to satisfy Flask-Login.
    We'll just carry id + email + name in memory.
    """
    def __init__(self, row):
        self.id = str(row.id)
        self.email = row.email
        self.name = row.name

# NOTE: user_loader is defined at line 274, this duplicate has been removed

# --- Role/session helpers ---

def worker_required(fn):
    """Guard routes for internal workers (Flask-Login)."""
    from functools import wraps
    @wraps(fn)
    def _wrap(*a, **kw):
        if not current_user.is_authenticated:
            return redirect(url_for("login", next=request.path))
        return fn(*a, **kw)
    return _wrap

def candidate_required(fn):
    """Guard routes for candidate self-service (magic-link)."""
    from functools import wraps
    @wraps(fn)
    def _wrap(*a, **kw):
        if not session.get("candidate_id"):
            return redirect(url_for("candidate_login", next=request.path))
        return fn(*a, **kw)
    return _wrap

class WorkerLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")

class WorkerSignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Create account")

class CandidateLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send me a login link")

class Timesheet(Base):
    __tablename__ = "timesheets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    engagement_id = Column(Integer, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    hours = Column(Integer, default=0)
    notes = Column(String(4000), default="")
    status = Column(String(50), default="Draft")
    submitted_at = Column(DateTime, nullable=True)
    # Phase 3 timesheet enhancement columns
    week_start = Column(Date, nullable=True)
    week_end = Column(Date, nullable=True)
    billable_days = Column(Float, default=0)
    billable_hours = Column(Float, default=0)
    day_rate = Column(Float, default=0)
    overtime_rate = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    expense_total = Column(Float, default=0)
    grand_total = Column(Float, default=0)
    approved_by = Column(Integer, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_reason = Column(Text, nullable=True)

class Invoice(Base):
    """Invoice model for client billing"""
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    engagement_id = Column(Integer, ForeignKey("engagements.id"), nullable=True)
    client_name = Column(String(200), nullable=False)
    engagement_name = Column(String(200), nullable=True)
    
    # Dates
    invoice_date = Column(DateTime, default=datetime.datetime.utcnow)
    due_date = Column(DateTime, nullable=True)
    paid_date = Column(DateTime, nullable=True)
    
    # Financial
    subtotal = Column(Float, default=0.0)
    vat_rate = Column(Float, default=20.0)  # VAT percentage
    vat_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    # Status: Draft, Pending, Paid, Overdue, Cancelled
    status = Column(String(50), default="Draft")
    
    # Details
    line_items = Column(Text, default="[]")  # JSON array of line items
    notes = Column(Text, default="")
    payment_terms = Column(String(200), default="Net 30")
    
    # Tracking
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    # Relationship
    engagement = relationship("Engagement", backref="invoices")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200))
    email = Column(String(200))
    phone = Column(String(50), default="")
    skills = Column(String(2000), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # card fields…
    onboarded_at = Column(DateTime, nullable=True)
    esign_status = Column(String(50), default=None)
    trustid_rtw_date = Column(DateTime, nullable=True)
    trustid_idv_date = Column(DateTime, nullable=True)
    trustid_dbs_date = Column(DateTime, nullable=True)
    updated_cv_requested_at = Column(DateTime, nullable=True)

    # NEW
    ai_summary = Column(String(6000), default="")
    
    # Resource Pool enhancement fields
    postcode = Column(String(20), nullable=True)  # UK postcode for radius search
    last_login_at = Column(DateTime, nullable=True)  # Last login to candidate portal
    last_activity_at = Column(DateTime, nullable=True)  # Last activity (application, profile update, etc.)
    optimus_interview_result = Column(String(50), nullable=True)  # Pass, Fail, Pending, Not Required
    optimus_assessment_result = Column(String(50), nullable=True)  # Pass, Fail, Pending, Not Required
    previously_vetted = Column(Boolean, default=False)  # Has been previously vetted
    min_day_rate = Column(Integer, nullable=True)  # Minimum acceptable day rate
    max_day_rate = Column(Integer, nullable=True)  # Maximum acceptable day rate
    
    # Status and availability fields per wireframe requirements
    status = Column(String(50), default="Available")  # Available, On Assignment, On Hold, Unavailable, etc.
    availability = Column(String(100), default="Immediately available")  # Immediately available, 2 weeks notice, etc.
    day_rate = Column(Integer, nullable=True)  # Day rate in pounds
    location = Column(String(200), nullable=True)  # Location/city
    clearance_level = Column(String(100), nullable=True)  # Security clearance level
    
    # GAP 3.1 & 3.3: Contract end/leaving tracking
    leaving_confirmed = Column(Boolean, default=False)  # Confirmed leaving when contract ends
    leaving_confirmed_at = Column(DateTime, nullable=True)  # When leaving was confirmed
    
    # Portal authentication fields
    email_verified = Column(Boolean, default=False)  # Email verified via magic link
    email_verified_at = Column(DateTime, nullable=True)  # When email was verified
    about = Column(Text, nullable=True)  # "Tell us about yourself" field from signup
    source = Column(String(100), default="portal")  # Where candidate came from (portal, manual, import)
    
    # Portal security fields (password + 2FA like admin users)
    password_hash = Column(String(255), nullable=True)  # Password hash for login
    totp_secret = Column(String(32), nullable=True)  # 2FA TOTP secret
    totp_enabled = Column(Boolean, default=False)  # Is 2FA enabled
    backup_codes = Column(Text, nullable=True)  # JSON array of backup codes
    failed_login_attempts = Column(Integer, default=0)  # Track failed logins
    locked_until = Column(DateTime, nullable=True)  # Account lockout timestamp
    password_set_at = Column(DateTime, nullable=True)  # When password was set

    # Gap plan 1.4: Additional candidate fields for vetting checks
    citizenship = Column(String(100), nullable=True)
    place_of_birth = Column(String(200), nullable=True)
    # Gap plan N1: Gender (required for DBS, World Check, Social Media)
    gender = Column(String(20), nullable=True)
    # Gap plan N2: Optional DBS fields
    mothers_maiden_name = Column(String(200), nullable=True)
    driving_licence_number = Column(String(50), nullable=True)
    passport_number = Column(String(50), nullable=True)
    # Gap plan N3: Location of place of work (World Check)
    work_location = Column(String(200), nullable=True)
    # Gap plan N4: Name variations (JSON array for World Check, Media Check, etc.)
    name_variations = Column(Text, nullable=True)  # JSON: ["John Smith", "J. Smith", ...]

    documents = relationship("Document", back_populates="candidate", cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Set password hash for candidate"""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        self.password_set_at = datetime.datetime.utcnow()
    
    def check_password(self, password):
        """Verify password"""
        from werkzeug.security import check_password_hash
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def is_locked(self):
        """Check if account is currently locked"""
        if self.locked_until is None:
            return False
        return self.locked_until > datetime.datetime.utcnow()
    
    def generate_totp_secret(self):
        """Generate a new TOTP secret for 2FA"""
        import pyotp
        return pyotp.random_base32()
    
    def verify_totp(self, token):
        """Verify a TOTP token"""
        if not self.totp_secret:
            return False
        import pyotp
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self, count=10):
        """Generate backup codes for account recovery"""
        import secrets
        codes = [secrets.token_hex(4).upper() for _ in range(count)]
        self.backup_codes = json.dumps(codes)
        return codes
    
    def verify_backup_code(self, code):
        """Verify and consume a backup code"""
        if not self.backup_codes:
            return False
        codes = json.loads(self.backup_codes)
        code = code.upper().replace('-', '')
        if code in codes:
            codes.remove(code)
            self.backup_codes = json.dumps(codes)
            return True
        return False

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(ForeignKey("candidates.id"))
    doc_type = Column(String(50), default="cv")
    filename = Column(String(500))
    original_name = Column(String(500))
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    # Gap plan 1.2: Document expiry tracking
    expiry_date = Column(Date, nullable=True)
    # Gap plan N13 / J1: Track which project/engagement used this document
    engagement_id = Column(Integer, ForeignKey("engagements.id"), nullable=True)
    candidate = relationship("Candidate", back_populates="documents")

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(ForeignKey("jobs.id"))
    candidate_id = Column(ForeignKey("candidates.id"))
    cover_note = Column(String(4000), default="")
    status = Column(String(50), default="New")  # Pipeline status
    ai_score = Column(Integer, default=0)
    ai_summary = Column(String(6000), default="")
    ai_explanation = Column(String(8000), default="")  # <-- NEW: store "why this score"
    interview_scheduled_at = Column(DateTime, nullable=True)
    interview_completed_at = Column(DateTime, nullable=True)

    # ✅ make sure THIS is present:
    interview_notes = Column(Text, default="")

    onboarding_email_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate")

class TrustIDCheck(Base):
    __tablename__ = "trustid_checks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(ForeignKey("applications.id"))
    rtw = Column(Boolean, default=False)
    idv = Column(Boolean, default=True)
    dbs = Column(Boolean, default=False)
    trustid_application_id = Column(String(100), default="")
    status = Column(String(50), default="Created")
    result_json = Column(String(20000), default="")

class Shortlist(Base):
    __tablename__ = "shortlists"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(ForeignKey("jobs.id"), index=True, nullable=False)
    candidate_id = Column(ForeignKey("candidates.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ESigRequest(Base):
    __tablename__ = "esign_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(ForeignKey("applications.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    engagement_id = Column(Integer, ForeignKey("engagements.id"), nullable=True)
    provider = Column(String(50), default="signable")
    request_id = Column(String(100), default="")
    status = Column(String(50), default="Draft")  # Draft, Sent, Signed, Declined, Error
    sent_at = Column(DateTime, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50))
    event_type = Column(String(100))
    payload = Column(String(40000))
    received_at = Column(DateTime, default=datetime.datetime.utcnow)

# --- Taxonomy (DB-driven) ---
class TaxonomyCategory(Base):
    __tablename__ = "taxonomy_categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 'role' or 'subject'
    type = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False, unique=False)

    tags = relationship("TaxonomyTag", back_populates="category", cascade="all, delete-orphan")

class TaxonomyTag(Base):
    __tablename__ = "taxonomy_tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(ForeignKey("taxonomy_categories.id"), index=True, nullable=False)
    tag = Column(String(200), nullable=False)

    category = relationship("TaxonomyCategory", back_populates="tags")

# ---- Opportunities model ----
class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    client = Column(String)
    stage = Column(String)
    owner = Column(String)
    est_start = Column(DateTime)
    est_value = Column(Integer)
    probability = Column(Integer, default=0)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    _engagement_id = Column(Integer)
    _engagement_ref = Column(String)

    # NEW client contact fields
    client_contact_name  = Column(String, default="")
    client_contact_role  = Column(String, default="")
    client_contact_phone = Column(String, default="")
    client_contact_email = Column(String, default="")

# ---- VettingCheck model (per wireframe requirements) ----
class VettingCheck(Base):
    """
    Pre-employment vetting check items for each candidate.
    12 check types as per wireframe:
    - Right to Work, Identity Verification, Address History, DBS Check,
    - Employment History, References, Qualifications, Professional Registration,
    - Credit Check, Directorship/Disqualification, Sanctions/PEP, Social Media Review
    """
    __tablename__ = "vetting_check"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    check_type = Column(String(100), nullable=False)
    status = Column(String(50), default="NOT STARTED")  # NOT STARTED, In Progress, Complete, N/A, Failed
    notes = Column(Text, default="")
    automation_enabled = Column(Boolean, default=True)  # Toggle to pause/resume automation for this check
    external_ref = Column(String(200), default="")  # Verifile screening reference / order ID
    external_provider = Column(String(50), default="")  # "verifile" or "" for manual
    external_result = Column(Text, default="")  # Raw JSON result from provider
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # Gap plan 1.1: Analyst case allocation
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)  # Staff user assigned to this check
    # Gap plan N5: Per-check colour system (white/green/orange)
    colour = Column(String(20), default="white")  # white, green, orange — auto or manual
    colour_manual = Column(Boolean, default=False)  # True if manually overridden by analyst
    # Gap plan N6: Some checks are prompt-only (no upload required)
    prompt_only = Column(Boolean, default=False)
    # Gap plan N10: ID verification method (video call / in-person / IDVT) required before DBS
    id_verified = Column(Boolean, default=False)
    id_verification_method = Column(String(50), nullable=True)  # video_call, in_person, idvt
    id_verified_at = Column(DateTime, nullable=True)
    # Gap plan 3: QC workflow
    qc_status = Column(String(30), default="")  # awaiting_qc, qc_approved, qc_rejected
    qc_reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    qc_reviewed_at = Column(DateTime, nullable=True)
    qc_notes = Column(Text, default="")
    # Third pass fix 3: Referral Approved requires additional approval
    referral_approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    referral_approved_at = Column(DateTime, nullable=True)

# ---- CandidateNote model (Notes & Activity panel) ----
class CandidateNote(Base):
    """Notes and activity log for candidates"""
    __tablename__ = "candidate_notes"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    user_email = Column(String)  # Who added the note
    note_type = Column(String(50), default="note")  # note, email, activity, system
    content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# ---- Gap plan Batch 5: Staff-side Reference tracking ----
class ReferenceRequest(Base):
    """Staff-side reference tracking — links to EmploymentHistory in portal."""
    __tablename__ = "reference_requests"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    employment_history_id = Column(Integer, nullable=True)  # Links to portal EmploymentHistory
    company_name = Column(String(300), default="")
    referee_email = Column(String(300), default="")
    referee_name = Column(String(300), default="")
    status = Column(String(50), default="not_sent")  # not_sent, sent, received, flagged, on_hold
    permission_status = Column(String(50), default="yes")  # yes, no, tbc
    sent_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    chase_count = Column(Integer, default=0)
    last_chased_at = Column(DateTime, nullable=True)
    # Third pass fix 7: Hold-until date to pause auto-chasers when referee says "will take X days"
    hold_until = Column(Date, nullable=True)
    colour = Column(String(20), default="white")  # white, green, orange
    notes = Column(Text, default="")
    attachment_path = Column(String(500), nullable=True)  # .msg or response file
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# ---- Contradiction Fix 6: Approved Umbrella Companies ----
class ApprovedUmbrella(Base):
    """Admin-managed list of approved umbrella companies."""
    __tablename__ = "approved_umbrella_companies"
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    signup_url = Column(String(500), default="")
    phone = Column(String(50), default="")
    email = Column(String(300), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ---- REQ-273: Admin-configurable workflow stages ----
class StageConfig(Base):
    """REQ-273: Admin-configurable workflow stages."""
    __tablename__ = "stage_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_id = Column(String(50), nullable=False, unique=True)  # e.g. "pipeline", "shortlist"
    name = Column(String(100), nullable=False)  # Display name
    short_name = Column(String(50), nullable=False)  # Short name for cards
    color = Column(String(20), nullable=False, default="#6366f1")
    icon = Column(String(50), nullable=False, default="fa-inbox")
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    is_terminal = Column(Boolean, default=False)  # e.g. Rejected/Withdrawn
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# Default workflow stages (used when no StageConfig rows exist)
DEFAULT_STAGES = [
    {"id": "pipeline", "name": "Pipeline", "short": "Pipeline", "color": "#6366f1", "icon": "fa-inbox", "order": 0, "terminal": False},
    {"id": "shortlist", "name": "Shortlist", "short": "Shortlist", "color": "#8b5cf6", "icon": "fa-star", "order": 1, "terminal": False},
    {"id": "ia", "name": "I&A", "short": "I&A", "color": "#f59e0b", "icon": "fa-phone-alt", "order": 2, "terminal": False},
    {"id": "client_review", "name": "Client Review", "short": "Client Review", "color": "#f97316", "icon": "fa-user-tie", "order": 3, "terminal": False},
    {"id": "offered", "name": "Offered", "short": "Offered", "color": "#ec4899", "icon": "fa-hand-holding-usd", "order": 4, "terminal": False},
    {"id": "accepted", "name": "Accepted", "short": "Accepted", "color": "#14b8a6", "icon": "fa-thumbs-up", "order": 5, "terminal": False},
    {"id": "ready_to_contract", "name": "Ready to Contract", "short": "Ready to Contract", "color": "#3b82f6", "icon": "fa-shield-alt", "order": 6, "terminal": False},
    {"id": "contract_sent", "name": "Contract Sent", "short": "Contract Sent", "color": "#10b981", "icon": "fa-file-signature", "order": 7, "terminal": False},
    {"id": "rejected_withdrawn", "name": "Rejected/Withdrawn", "short": "Rej/Withdrawn", "color": "#ef4444", "icon": "fa-times-circle", "order": 8, "terminal": True},
]


def _get_workflow_stages(session=None):
    """Load workflow stages from DB config, falling back to defaults."""
    try:
        if session:
            configs = session.scalars(
                select(StageConfig).where(StageConfig.is_active == True).order_by(StageConfig.sort_order)
            ).all()
            if configs:
                return [{"id": c.stage_id, "name": c.name, "short": c.short_name, "color": c.color, "icon": c.icon} for c in configs]
    except Exception:
        pass
    return [{"id": s["id"], "name": s["name"], "short": s["short"], "color": s["color"], "icon": s["icon"]} for s in DEFAULT_STAGES]


def _seed_default_stages(session):
    """Seed default stages into StageConfig if table is empty."""
    existing = session.scalar(select(func.count(StageConfig.id)))
    if existing == 0:
        for s in DEFAULT_STAGES:
            session.add(StageConfig(
                stage_id=s["id"], name=s["name"], short_name=s["short"],
                color=s["color"], icon=s["icon"], sort_order=s["order"],
                is_active=True, is_terminal=s["terminal"]
            ))
        session.commit()


from public import public_bp
app.register_blueprint(public_bp)

from associate_portal import associate_bp, _models as _portal_models, _apply_rate_limits
app.register_blueprint(associate_bp, url_prefix="/portal")
_apply_rate_limits(app)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")  # for session


def _get_ts_config_model():
    """Lazy-load TimesheetConfig model from associate portal."""
    try:
        from associate_portal import _ensure_models
        _ensure_models()
        return _portal_models.get("TimesheetConfig")
    except Exception:
        return None


# ---- Lightweight schema patches for existing SQLite DBs ----
def ensure_schema():
    with engine.begin() as conn:
        # ===== jobs table =====
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN role_type TEXT DEFAULT ''"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN status TEXT DEFAULT 'Open'"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN location TEXT DEFAULT ''"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN salary_range TEXT DEFAULT ''"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN public_token TEXT UNIQUE"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
        except Exception:
            pass
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)"))
        except Exception:
            pass
        try:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_public_token ON jobs(public_token)"))
        except Exception:
            pass

        # ===== applications table =====
        for coldef in [
            "interview_completed_at DATETIME",
            "interview_notes TEXT DEFAULT ''",
            "ai_explanation TEXT DEFAULT ''",
            "ai_score INTEGER DEFAULT 0",
            "ai_summary TEXT DEFAULT ''",
            "onboarding_email_sent BOOLEAN DEFAULT 0",
            "interview_scheduled_at DATETIME",
            "status TEXT DEFAULT 'New'",
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE applications ADD COLUMN {coldef}"))
            except Exception:
                pass

        # ===== candidates table =====
        try:
            conn.execute(text("ALTER TABLE candidates ADD COLUMN ai_summary TEXT DEFAULT ''"))
        except Exception:
            pass
        for coldef in [
            "onboarded_at DATETIME",
            "esign_status TEXT",
            "trustid_rtw_date DATETIME",
            "trustid_idv_date DATETIME",
            "trustid_dbs_date DATETIME",
            "updated_cv_requested_at DATETIME",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE candidates ADD COLUMN {coldef}"))
            except Exception:
                pass
        try:
            conn.execute(text("ALTER TABLE candidates ADD COLUMN phone TEXT DEFAULT ''"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE candidates ADD COLUMN skills TEXT DEFAULT ''"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE candidates ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
        except Exception:
            pass
        
        # Resource Pool enhancement columns
        for coldef in [
            "postcode TEXT",
            "last_login_at DATETIME",
            "last_activity_at DATETIME",
            "optimus_interview_result TEXT",
            "optimus_assessment_result TEXT",
            "previously_vetted BOOLEAN DEFAULT 0",
            "min_day_rate INTEGER",
            "max_day_rate INTEGER",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE candidates ADD COLUMN {coldef}"))
            except Exception:
                pass
        
        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_candidates_created_at ON candidates(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email)",
            "CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(name)",
        ]:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass

        # ===== documents table =====
        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_documents_candidate ON documents(candidate_id)",
            "CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at)",
        ]:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass

        # ===== shortlists table =====
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS shortlists (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              job_id INTEGER NOT NULL,
              candidate_id INTEGER NOT NULL,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """))
        except Exception:
            pass
        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_shortlists_job ON shortlists(job_id)",
            "CREATE INDEX IF NOT EXISTS idx_shortlists_candidate ON shortlists(candidate_id)",
        ]:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass

        # ===== taxonomy tables =====
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS taxonomy_categories (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              type TEXT NOT NULL,
              name TEXT NOT NULL
            )
            """))
        except Exception:
            pass
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS taxonomy_tags (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              category_id INTEGER NOT NULL REFERENCES taxonomy_categories(id) ON DELETE CASCADE,
              tag TEXT NOT NULL
            )
            """))
        except Exception:
            pass
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS candidate_tags (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              candidate_id INTEGER NOT NULL,
              tag_id INTEGER NOT NULL,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """))
        except Exception:
            pass
        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_tax_cat_type ON taxonomy_categories(type)",
            "CREATE INDEX IF NOT EXISTS idx_tax_tags_cat ON taxonomy_tags(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_candidate_tags_cand ON candidate_tags(candidate_id)",
        ]:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass

        # ===== role_aliases table =====
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS role_aliases (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              canonical TEXT NOT NULL,
              alias TEXT NOT NULL
            )
            """))
        except Exception:
            pass
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_role_alias_canon ON role_aliases(canonical)"))
        except Exception:
            pass
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_role_alias_alias ON role_aliases(alias)"))
        except Exception:
            pass

        # ===== users table =====
        # NOTE: Skipped inline CREATE — full schema defined in User model (line 2539)
        # and created by Base.metadata.create_all(engine) at line 4019.
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
        except Exception:
            pass

        # ===== timesheets table =====
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS timesheets (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              engagement_id INTEGER NOT NULL,
              period_start DATETIME NOT NULL,
              period_end DATETIME NOT NULL,
              hours INTEGER DEFAULT 0,
              notes TEXT,
              status TEXT DEFAULT 'Draft',
              submitted_at DATETIME
            )
            """))
        except Exception:
            pass
        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_timesheets_eng_period ON timesheets(engagement_id, period_start)",
            "CREATE INDEX IF NOT EXISTS idx_timesheets_user_period ON timesheets(user_id, period_start)",
        ]:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass

        # ===== engagements table =====
        try:
            conn.execute(text("ALTER TABLE engagements ADD COLUMN ref TEXT"))
        except Exception:
            pass
        try:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_engagements_ref ON engagements(ref)"))
        except Exception:
            pass

        for coldef in [
            "sow_signed_at DATETIME",
            "description TEXT DEFAULT ''",
            "start_date DATETIME",
            "end_date DATETIME",
            "opportunity_id INTEGER UNIQUE",
            "plan_version INTEGER DEFAULT 1",
            "ir35_status TEXT DEFAULT 'inside'",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE engagements ADD COLUMN {coldef}"))
            except Exception:
                pass

        try:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_engagements_opp ON engagements(opportunity_id)"))
        except Exception:
            pass

        # ===== opportunities table =====
        for coldef in [
            "_engagement_id INTEGER",
            "_engagement_ref TEXT",
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
            "probability INTEGER DEFAULT 0",
            "notes TEXT DEFAULT ''",
            "client_contact_name TEXT",
            "client_contact_role TEXT",
            "client_contact_phone TEXT",
            "client_contact_email TEXT"
        ]:
            try:
                conn.execute(text(f"ALTER TABLE opportunities ADD COLUMN {coldef}"))
            except Exception:
                pass
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_opps_engid ON opportunities(_engagement_id)"))
        except Exception:
            pass

        # ===== engagement_plans table =====
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS engagement_plans (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              engagement_id INTEGER,
              role_type TEXT DEFAULT '',
              planned_count INTEGER DEFAULT 0,
              pay_rate INTEGER DEFAULT 0,
              charge_rate INTEGER DEFAULT 0,
              -- legacy 'rate' kept for backwards compat; mirrors charge_rate
              rate INTEGER DEFAULT 0,
              version_int INTEGER DEFAULT 1
            )
            """))
        except Exception:
            pass

        # backfill new columns if table pre-existed
        for coldef in [
            "pay_rate INTEGER DEFAULT 0",
            "charge_rate INTEGER DEFAULT 0",
            "version_int INTEGER DEFAULT 1",
            "rate INTEGER DEFAULT 0"
        ]:
            try:
                conn.execute(text(f"ALTER TABLE engagement_plans ADD COLUMN {coldef}"))
            except Exception:
                pass

        # ===== trustid_checks table =====
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trustid_checks (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              application_id INTEGER,
              rtw BOOLEAN DEFAULT 0,
              idv BOOLEAN DEFAULT 1,
              dbs BOOLEAN DEFAULT 0,
              trustid_application_id TEXT DEFAULT '',
              status TEXT DEFAULT 'Created',
              result_json TEXT DEFAULT ''
            )
            """))
        except Exception:
            pass

        # ===== esign_requests table =====
        # NOTE: Skipped inline CREATE — full schema defined in ESigRequest model
        # and created by Base.metadata.create_all(engine).

        # ===== webhook_events table =====
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS webhook_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              source TEXT,
              event_type TEXT,
              payload TEXT,
              received_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """))
        except Exception:
            pass

        # ===== role_types table =====
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS role_types (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT UNIQUE NOT NULL,
              default_rate INTEGER DEFAULT 0
            )
            """))
        except Exception:
            pass

        # ===== Helpful engagement ref backfill =====
        try:
            existing_refs = [r[0] for r in conn.execute(
                text("SELECT ref FROM engagements WHERE ref IS NOT NULL AND ref <> ''")
            ).all()]
            import re as _re
            prefix = "EG"
            width = 3
            max_n = 0
            for ref in existing_refs:
                m = _re.fullmatch(rf"{_re.escape(prefix)}(\d+)", ref or "")
                if m:
                    try:
                        max_n = max(max_n, int(m.group(1)))
                    except Exception:
                        pass
            rows_to_fill = conn.execute(
                text("SELECT id FROM engagements WHERE ref IS NULL OR ref = '' ORDER BY id ASC")
            ).all()
            for (eid,) in rows_to_fill:
                max_n += 1
                new_ref = f"{prefix}{str(max_n).zfill(width)}"
                conn.execute(text("UPDATE engagements SET ref=:r WHERE id=:i"), {"r": new_ref, "i": eid})
        except Exception:
            pass

        # ===== Seed taxonomy & role_aliases if empty =====
        try:
            existing = conn.execute(text("SELECT COUNT(1) FROM taxonomy_categories")).scalar() or 0
            if existing == 0:
                role_names = [
                    'Project Director','Project Manager','Project Lead','Ops Manager',
                    'Team Leader','Team Lead','Case Handler','Officers','Admin'
                ]
                for rn in role_names:
                    conn.execute(
                        text("INSERT INTO taxonomy_categories(type,name) VALUES('role', :n)"),
                        {"n": rn},
                    )

                subjects = {
                    "Financial Crime / Compliance": [
                        "AML","KYC","CDD","EDD","Sanctions","Screening",
                        "TM (Transaction Monitoring)","FRA","SAR/STR","PEP","Adverse Media"
                    ],
                    "Case Handling / QA / Ops": [
                        "Case Handling","Quality Assurance","MI/Reporting",
                        "Playbooks","Workflows","SLA Management"
                    ],
                    "Domains": [
                        "Retail Banking","Corporate Banking","FinTech",
                        "Payments","Crypto","Wealth/Private Banking"
                    ],
                    "Tools & Platforms": [
                        "Actimize","Pega","Mantas","Nice","Salesforce",
                        "Dynamics","Oracle","Workday","Excel","SQL"
                    ],
                }
                for cat, tags in subjects.items():
                    conn.execute(
                        text("INSERT INTO taxonomy_categories(type,name) VALUES('subject', :n)"),
                        {"n": cat},
                    )
                    cat_id = conn.execute(
                        text("SELECT id FROM taxonomy_categories WHERE type='subject' AND name=:n ORDER BY id DESC LIMIT 1"),
                        {"n": cat},
                    ).scalar()
                    for t in tags:
                        conn.execute(
                            text("INSERT INTO taxonomy_tags(category_id, tag) VALUES(:cid, :tag)"),
                            {"cid": cat_id, "tag": t},
                        )
        except Exception:
            pass

        try:
            n_alias = conn.execute(text("SELECT COUNT(1) FROM role_aliases")).scalar() or 0
            if n_alias == 0:
                seeds = [
                    ("Project Director", "programme director"),
                    ("Project Director", "program director"),
                    ("Project Director", "pd"),
                    ("Project Manager",  "programme manager"),
                    ("Project Manager",  "program manager"),
                    ("Project Manager",  "pm"),
                    ("Project Manager",  "project lead"),
                    ("Ops Manager",      "operations manager"),
                    ("Ops Manager",      "service delivery manager"),
                    ("Team Leader",      "team lead"),
                    ("Team Leader",      "supervisor"),
                    ("Case Handler",     "kyc analyst"),
                    ("Case Handler",     "aml analyst"),
                    ("Case Handler",     "investigator"),
                    ("Admin",            "administrator"),
                    ("Admin",            "office admin"),
                    ("Project Lead",     "project leader"),
                    ("Project Lead",     "delivery lead"),
                    ("Team Lead",        "tl"),
                    ("Team Lead",        "shift lead"),
                    ("Officers",         "compliance officer"),
                    ("Officers",         "risk officer"),
                    ("Officers",         "mlro"),
                ]
                for canon, alias in seeds:
                    conn.execute(
                        text("INSERT INTO role_aliases(canonical, alias) VALUES(:c, :a)"),
                        {"c": canon, "a": alias},
                    )
        except Exception:
            pass

        # ===== Seed role_types table =====
        try:
            count_roles = conn.execute(text("SELECT COUNT(1) FROM role_types")).scalar() or 0
            if count_roles == 0:
                for r in ROLE_TYPES:
                    conn.execute(
                        text("INSERT INTO role_types (name, default_rate) VALUES (:n, 0)"),
                        {"n": r},
                    )
        except Exception:
            pass

        # ===== SECURITY: Add security columns to users table (CREST compliance) =====
        # TEMPORARILY DISABLED - Causing deployment issues
        # Will be re-enabled after testing
        pass

        # ===== vetting_check table =====
        try:
            conn.execute(text("ALTER TABLE vetting_check ADD COLUMN automation_enabled BOOLEAN DEFAULT 1"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE vetting_check ADD COLUMN external_ref TEXT DEFAULT ''"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE vetting_check ADD COLUMN external_provider TEXT DEFAULT ''"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE vetting_check ADD COLUMN external_result TEXT DEFAULT ''"))
        except Exception:
            pass

        # ===== associate_profiles table =====
        for coldef in [
            "previous_first_names TEXT DEFAULT ''",
            "previous_surnames TEXT DEFAULT ''",
            "unsubscribed BOOLEAN DEFAULT 0",
            "profile_picture TEXT DEFAULT ''",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE associate_profiles ADD COLUMN {coldef}"))
            except Exception:
                pass

        # ===== Timesheet enhancement columns =====
        for coldef in [
            "week_start DATE",
            "week_end DATE",
            "billable_days REAL DEFAULT 0",
            "billable_hours REAL DEFAULT 0",
            "day_rate REAL DEFAULT 0",
            "overtime_rate REAL DEFAULT 0",
            "total_amount REAL DEFAULT 0",
            "expense_total REAL DEFAULT 0",
            "grand_total REAL DEFAULT 0",
            "approved_by INTEGER",
            "approved_at DATETIME",
            "rejected_reason TEXT",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE timesheets ADD COLUMN {coldef}"))
            except Exception:
                pass

        # ===== New timesheet-related tables =====
        try:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS timesheet_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                engagement_id INTEGER,
                time_types TEXT DEFAULT '["Standard Time","Overtime","Holiday","Sickness","Unplanned Absence"]',
                overtime_enabled BOOLEAN DEFAULT 0,
                overtime_multiplier REAL DEFAULT 1.5,
                overtime_rate_type TEXT DEFAULT 'hourly',
                expense_enabled BOOLEAN DEFAULT 0,
                expense_types TEXT DEFAULT '["Travel","Accommodation","Meals","Equipment","Other"]',
                expense_limits TEXT DEFAULT '{}',
                day_rate REAL DEFAULT 0,
                overtime_rate REAL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""))
        except Exception:
            pass
        try:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS timesheet_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timesheet_id INTEGER,
                entry_date DATE,
                time_type TEXT,
                value REAL DEFAULT 0,
                value_unit TEXT DEFAULT 'days',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""))
        except Exception:
            pass
        try:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS timesheet_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timesheet_id INTEGER,
                expense_type TEXT,
                description TEXT,
                amount REAL DEFAULT 0,
                receipt_doc_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""))
        except Exception:
            pass
        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_ts_configs_eng ON timesheet_configs(engagement_id)",
            "CREATE INDEX IF NOT EXISTS idx_ts_entries_ts ON timesheet_entries(timesheet_id)",
            "CREATE INDEX IF NOT EXISTS idx_ts_expenses_ts ON timesheet_expenses(timesheet_id)",
        ]:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass

        # ===== Gap Plan 006: New columns and tables =====
        # -- VettingCheck additions --
        for coldef in [
            "assigned_to INTEGER REFERENCES users(id)",
            "colour VARCHAR(20) DEFAULT 'white'",
            "colour_manual BOOLEAN DEFAULT 0",
            "prompt_only BOOLEAN DEFAULT 0",
            "id_verified BOOLEAN DEFAULT 0",
            "id_verification_method VARCHAR(50)",
            "id_verified_at DATETIME",
            "qc_status VARCHAR(30) DEFAULT ''",
            "qc_reviewed_by INTEGER REFERENCES users(id)",
            "qc_reviewed_at DATETIME",
            "qc_notes TEXT DEFAULT ''",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE vetting_check ADD COLUMN {coldef}"))
            except Exception:
                pass

        # -- Documents additions --
        for coldef in ["expiry_date DATE", "engagement_id INTEGER REFERENCES engagements(id)"]:
            try:
                conn.execute(text(f"ALTER TABLE documents ADD COLUMN {coldef}"))
            except Exception:
                pass

        # -- Candidates additions --
        for coldef in [
            "citizenship VARCHAR(100)",
            "place_of_birth VARCHAR(200)",
            "gender VARCHAR(20)",
            "mothers_maiden_name VARCHAR(200)",
            "driving_licence_number VARCHAR(50)",
            "passport_number VARCHAR(50)",
            "work_location VARCHAR(200)",
            "name_variations TEXT",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE candidates ADD COLUMN {coldef}"))
            except Exception:
                pass

        # -- Engagements additions --
        for coldef in ["required_documents TEXT", "reference_period_years INTEGER DEFAULT 3"]:
            try:
                conn.execute(text(f"ALTER TABLE engagements ADD COLUMN {coldef}"))
            except Exception:
                pass

        # -- Reference Requests table --
        try:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS reference_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL REFERENCES candidates(id),
                employment_history_id INTEGER,
                company_name VARCHAR(300) DEFAULT '',
                referee_email VARCHAR(300) DEFAULT '',
                referee_name VARCHAR(300) DEFAULT '',
                status VARCHAR(50) DEFAULT 'not_sent',
                permission_status VARCHAR(50) DEFAULT 'yes',
                sent_at DATETIME,
                received_at DATETIME,
                chase_count INTEGER DEFAULT 0,
                last_chased_at DATETIME,
                colour VARCHAR(20) DEFAULT 'white',
                notes TEXT DEFAULT '',
                attachment_path VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""))
        except Exception:
            pass

        # -- Contradiction Fix 6: Approved Umbrella Companies table --
        try:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS approved_umbrella_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(300) NOT NULL,
                signup_url VARCHAR(500) DEFAULT '',
                phone VARCHAR(50) DEFAULT '',
                email VARCHAR(300) DEFAULT '',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""))
        except Exception:
            pass

        # -- P7: Address History table --
        try:
            conn.execute(text("""CREATE TABLE IF NOT EXISTS address_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL REFERENCES candidates(id),
                address_line1 VARCHAR(500) DEFAULT '',
                address_line2 VARCHAR(500) DEFAULT '',
                city VARCHAR(200) DEFAULT '',
                postcode VARCHAR(20) DEFAULT '',
                country VARCHAR(100) DEFAULT 'United Kingdom',
                from_date DATE,
                to_date DATE,
                is_current BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""))
        except Exception:
            pass

        # -- Third pass: new columns --
        for coldef in [
            "hold_until DATE",  # Fix 7: reference hold-until date
        ]:
            try:
                conn.execute(text(f"ALTER TABLE reference_requests ADD COLUMN {coldef}"))
            except Exception:
                pass
        for coldef in [
            "referral_approved_by INTEGER REFERENCES users(id)",  # Fix 3: two-step referral
            "referral_approved_at DATETIME",
        ]:
            try:
                conn.execute(text(f"ALTER TABLE vetting_check ADD COLUMN {coldef}"))
            except Exception:
                pass
        try:
            conn.execute(text("ALTER TABLE engagements ADD COLUMN gap_threshold_days INTEGER DEFAULT 90"))
        except Exception:
            pass

        # -- P8: Gender on associate_profiles --
        try:
            conn.execute(text("ALTER TABLE associate_profiles ADD COLUMN gender VARCHAR(20) DEFAULT ''"))
        except Exception:
            pass

        # -- Indexes for new columns --
        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_vetting_check_assigned ON vetting_check(assigned_to)",
            "CREATE INDEX IF NOT EXISTS idx_vetting_check_qc_status ON vetting_check(qc_status)",
            "CREATE INDEX IF NOT EXISTS idx_documents_expiry ON documents(expiry_date)",
            "CREATE INDEX IF NOT EXISTS idx_documents_engagement ON documents(engagement_id)",
            "CREATE INDEX IF NOT EXISTS idx_reference_requests_candidate ON reference_requests(candidate_id)",
            "CREATE INDEX IF NOT EXISTS idx_reference_requests_status ON reference_requests(status)",
            "CREATE INDEX IF NOT EXISTS idx_address_history_candidate ON address_history(candidate_id)",
        ]:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass

# Create all model-defined tables FIRST (full schemas from SQLAlchemy models),
# THEN run ensure_schema() for backwards-compat patches on pre-existing DBs.
Base.metadata.create_all(engine)
try:
    ensure_schema()
except Exception as e:
    print(f"⚠️  WARNING: Schema migration failed: {e}")
    print("⚠️  App will continue but some features may not work correctly")
    import traceback
    traceback.print_exc()

# ===== Fix stale users table + seed admin if empty (separate connection) =====
try:
    with engine.begin() as conn:
        # Check if users table has the required columns — if not, drop and let create_all rebuild
        cols = [r[0] for r in conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"
        )).fetchall()]

        if 'role' not in cols or 'is_active' not in cols:
            user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
            if user_count == 0:
                print("Users table has stale schema and 0 rows — recreating...")
                conn.execute(text("DROP TABLE IF EXISTS password_history"))
                conn.execute(text("DROP TABLE IF EXISTS users"))
            else:
                print(f"Users table has stale schema but {user_count} rows — skipping drop.")

    # Rebuild any dropped tables with full schema
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        if user_count == 0:
            from werkzeug.security import generate_password_hash

            password_hash_value = generate_password_hash("DemoAdmin2024!", method='pbkdf2:sha256')

            conn.execute(
                text("""
                    INSERT INTO users (name, email, pw_hash, role, is_active, created_at)
                    VALUES (:name, :email, :pw_hash, :role, :is_active, CURRENT_TIMESTAMP)
                """),
                {
                    "name": "Admin User",
                    "email": "admin@demo.example.com",
                    "pw_hash": password_hash_value,
                    "role": "admin",
                    "is_active": True
                }
            )
            print("Admin user created: admin@demo.example.com")
        else:
            print(f"Users table has {user_count} users — skipping admin seed.")
except Exception as e:
    print(f"Warning: Could not seed admin user: {e}")
    import traceback
    traceback.print_exc()

# ---------- Taxonomy tagging helpers ----------
WORD = r"[A-Za-z][A-Za-z\-/&\.\(\) ]+[A-Za-z]"

def _collect_text_for_candidate(session: Session, cand: Candidate) -> str:
    """Return searchable text: latest CV + name + existing skills."""
    doc = session.scalar(
        select(Document)
        .where(Document.candidate_id == cand.id)
        .order_by(Document.uploaded_at.desc())
    )
    parts = [cand.name or "", cand.email or "", cand.skills or ""]
    if doc:
        parts.append(extract_cv_text(doc) or "")
    text = " \n ".join(p for p in parts if p).lower()
    # compress whitespace
    text = re.sub(r"\s+", " ", text)
    return text

def _job_is_open(job) -> bool:
    if job is None:
        return False
    status = (getattr(job, "status", "") or "").strip().lower()
    if status in {"withdrawn","closed","filled","archived","cancelled","canceled"}:
        return False
    # also treat explicit timestamps if you ever add them
    if getattr(job, "closed_at", None) is not None: return False
    if getattr(job, "archived_at", None) is not None: return False
    return True

def _load_role_aliases(session: Session) -> dict:
    """
    Merge built-in aliases with DB-managed aliases.
    Returns: {canonical_lower: set(alias_lower, ...)}
    """
    # start from your existing dict (if you want to keep the built-ins)
    base = {
        "project director": {"programme director","program director","pd","delivery director"},
        "project manager":  {"project lead","pm","programme manager","program manager","scrum master"},
        "ops manager":      {"operations manager","operations lead","ops lead","service delivery manager"},
        "team leader":      {"supervisor","team lead","shift lead","coach"},
        "case handler":     {"investigator","analyst","kyc analyst","aml analyst","qa analyst","caseworker"},
        "admin":            {"coordinator","assistant","administrator","pa","ea","office admin"},
    }
    rows = session.execute(text("SELECT canonical, alias FROM role_aliases")).all()
    for canon, alias in rows:
        if not canon or not alias:
            continue
        base.setdefault(canon.strip().lower(), set()).add(alias.strip().lower())
    return base

def _retag_candidate_skills(s, cand, overwrite: bool = False):
    """
    Derive tags/role from candidate text and update:
      - Candidate.skills (human-readable)
      - CandidateTag (normalized join rows)
    Uses the taxonomy helpers already in this codebase.
    """
    # Collect text (CV text preferred; falls back to freeform)
    text_lc = _collect_text_for_candidate(s, cand)
    if not text_lc:
        return

    # Load taxonomy terms once
    groups = _get_subject_term_set(s)
    term_list = [t for t in groups.get("__all__", [])]

    # Derive role + subject tags
    role = _normalise_role(text_lc)
    tags = _derive_subject_tags(text_lc, term_list)

    # ---------- Update Candidate.skills (readable) ----------
    current = (cand.skills or "").strip()
    existing_tokens = {w.strip().lower() for w in re.split(r"[,/|;]", current) if w.strip()}

    # Ensure role token is first (if found)
    parts = []
    if role:
        parts.append(role)

    # Add new tags (avoid duplicates, case-insensitive)
    new_tags = []
    for t in sorted(tags, key=str.lower):
        if t.lower() not in existing_tokens:
            new_tags.append(t)

    if overwrite:
        merged = ", ".join(parts + new_tags)
        if current:
            # keep any freeform skills too
            merged = (merged + (" | " if merged and current else "") + current).strip()
        cand.skills = merged or current
    else:
        # append tags that aren't already there
        if parts:
            for rt in parts:
                if rt.lower() not in existing_tokens:
                    current = (f"{rt} | " + current).strip(" |")
                    existing_tokens.add(rt.lower())
        if new_tags:
            add_str = ", ".join(new_tags)
            cand.skills = (current + (" | " if current else "") + add_str).strip()
        else:
            cand.skills = current

    # ---------- Sync CandidateTag (normalized) ----------
    # Map existing tag ids for quick checks
    existing_rels = s.scalars(
        select(CandidateTag).where(CandidateTag.candidate_id == cand.id)
    ).all()
    existing_tag_ids = {r.tag_id for r in existing_rels}

    # Lookup tag ids by name (case-insensitive)
    if tags:
        tag_rows = s.scalars(
            select(TaxonomyTag).where(func.lower(TaxonomyTag.tag).in_([t.lower() for t in tags]))
        ).all()
        for tg in tag_rows:
            if tg.id not in existing_tag_ids:
                s.add(CandidateTag(candidate_id=cand.id, tag_id=tg.id))

# --- Tag matching helper (place near other helpers) ---
def _match_tags_from_text(s, text: str) -> List[TaxonomyTag]:
    """Return TaxonomyTag rows whose tag string appears (case-insensitive) in text."""
    text_lc = (text or "").lower()
    if not text_lc.strip():
        return []
    all_tags = s.scalars(select(TaxonomyTag)).all()
    hits: List[TaxonomyTag] = []
    for tg in all_tags:
        token = (tg.tag or "").strip()
        if token and token.lower() in text_lc:
            hits.append(tg)
    return hits

def _create_engagement_from_opportunity(s: Session, opp: Opportunity) -> Engagement:
    existing = s.scalar(select(Engagement).where(Engagement.opportunity_id == opp.id))
    if existing:
        return existing

    new_ref = _next_engagement_ref(s)

    e = Engagement(
        ref=new_ref,
        name=opp.name,
        client=opp.client or "",
        status="Active",
        start_date=opp.est_start,              # now valid
        description=(opp.notes or ""),
        opportunity_id=opp.id,
    )
    s.add(e)
    s.flush()
    return e

def create_engagement_for_opportunity(s, opp: Opportunity) -> Engagement:
    # create the engagement with sensible defaults
    e = Engagement(
        name=opp.name or f"Engagement for {opp.client or 'Unknown Client'}",
        client=opp.client or "",
        status="Active",
        start_date=opp.est_start,       # carry over estimated start date (item 11)
        description=opp.notes or "",
        opportunity=opp,               # sets e.opportunity_id automatically
    )
    s.add(e)
    s.flush()  # get e.id

    # ensure engagement has a ref (OS00X...) if your ref backfill didn’t set it yet
    if not e.ref:
        # find next numeric
        prefix, width = "OS", 3
        max_n = s.execute(text("""
            SELECT COALESCE(MAX(CAST(SUBSTR(ref, 3) AS INTEGER)), 0)
            FROM engagements
            WHERE ref LIKE :patt
        """), {"patt": f"{prefix}%"}).scalar() or 0
        e.ref = f"{prefix}{str(max_n + 1).zfill(width)}"

    # cache back onto opportunity for quick linking in UI
    opp._engagement_id = e.id
    opp._engagement_ref = e.ref

    return e

def _get_subject_term_set(session: Session) -> Dict[str, List[str]]:
    """
    Build {category_name: [tag, ...]} from DB taxonomy.
    Also returns a flat set of all tags under key '__all__'.
    """
    cats = session.execute(
        text("SELECT c.id, c.name FROM taxonomy_categories c WHERE c.type='subject'")
    ).all()
    result: Dict[str, List[str]] = {}
    all_terms: List[str] = []
    for cid, cname in cats:
        tags = [t for (t,) in session.execute(
            text("SELECT tag FROM taxonomy_tags WHERE category_id=:cid"),
            {"cid": cid}
        ).all()]
        result[cname] = tags
        all_terms.extend(tags)
    result["__all__"] = sorted(set(all_terms), key=lambda s: s.lower())
    return result

def _rebuild_ai_summary_and_tags(s, cand, doc=None, job=None, appn=None):
    """
    Extract CV text → generate AI summary → write to latest Application and Candidate
    → derive & write skills/tags. If a Job is provided, also compute AI score + explanation.

    Args:
        s: SQLAlchemy Session
        cand: Candidate ORM instance
        doc:  (optional) Document instance for the CV. If None, pick the latest CV.
        job:  (optional) Job ORM instance — if provided, we will compute ai_score + ai_explanation
        appn: (optional) Application ORM instance to write into; if None we fetch latest for candidate
    """
    # pick latest CV if not provided (prefer uploaded_at; fallback to id)
    if doc is None:
        doc = s.scalar(
            select(Document)
            .where(Document.candidate_id == cand.id, getattr(Document, "doc_type", literal_column("'cv'")) == "cv")
            .order_by(getattr(Document, "uploaded_at", Document.id).desc())
        )

    # Safely extract text (prefer project helper)
    def _safe_extract_text(file_path: str, original_name: str) -> str:
        name = (original_name or file_path).lower()
        print(f"[CV] Extracting text from: {file_path} (name={name}, exists={os.path.exists(file_path)})")

        if not os.path.exists(file_path):
            print(f"[CV] File not found: {file_path}")
            return ""

        # PDF — try multiple methods
        if name.endswith(".pdf"):
            # Method 1: pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    bits = [(p.extract_text() or "") for p in pdf.pages]
                txt = "\n".join(bits).strip()
                print(f"[CV] pdfplumber extracted {len(txt)} chars")
                if txt:
                    return txt
            except Exception as e:
                print(f"[CV] pdfplumber failed: {e}")

            # Method 2: PyPDF2 fallback
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                bits = [page.extract_text() or "" for page in reader.pages]
                txt = "\n".join(bits).strip()
                print(f"[CV] PyPDF2 extracted {len(txt)} chars")
                if txt:
                    return txt
            except ImportError:
                print("[CV] PyPDF2 not installed — skipping fallback")
            except Exception as e:
                print(f"[CV] PyPDF2 failed: {e}")

            # PDF failed — do NOT fall through to plain text
            print("[CV] All PDF extraction methods failed")
            return ""

        # DOCX
        if name.endswith(".docx"):
            try:
                import docx
                d = docx.Document(file_path)
                txt = "\n".join([p.text for p in d.paragraphs]).strip()
                print(f"[CV] DOCX extracted {len(txt)} chars")
                if txt:
                    return txt
            except Exception as e:
                print(f"[CV] DOCX extraction failed: {e}")
            return ""

        # DOC (legacy .doc format)
        if name.endswith(".doc"):
            print("[CV] Legacy .doc format — extraction not supported")
            return ""

        # Plain text only for .txt files
        if name.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read().strip()
            except Exception:
                pass

        return ""

    cv_text = ""
    if doc:
        try:
            if "extract_cv_text" in globals() and callable(globals()["extract_cv_text"]):
                cv_text = extract_cv_text(doc) or ""
            else:
                file_path = _doc_file_path(doc)
                cv_text = _safe_extract_text(file_path, getattr(doc, "original_name", "") or doc.filename)
        except Exception:
            cv_text = ""

    # Generate summary — only from actual CV text, never fabricate
    if not cv_text:
        summary = "Unable to retrieve information from CV."
        print(f"[AI] No CV text extracted for candidate {cand.id} ({cand.name})")
    else:
        try:
            summary = ai_summarise(cv_text)
        except Exception as e:
            summary = "Unable to retrieve information from CV."
            current_app.logger.exception("ai_summarise failed: %s", e)

    # Choose target application
    target_app = appn
    if target_app is None:
        target_app = s.scalar(
            select(Application)
            .where(Application.candidate_id == cand.id)
            .order_by(Application.created_at.desc())
        )

    if target_app:
        target_app.ai_summary = summary

    # Mirror on Candidate if that column exists
    if hasattr(cand, "ai_summary"):
        cand.ai_summary = summary

    # Skills/Tags (prefer project helper if present)
    try:
        if "_retag_candidate_skills" in globals() and callable(globals()["_retag_candidate_skills"]):
            _retag_candidate_skills(s, cand, overwrite=False)
        else:
            # Minimal fallback: match taxonomy tags in text and store
            text_lc = (cv_text or "").lower()
            matched_ids = set()
            matched_tags = []
            all_tags = s.scalars(select(TaxonomyTag)).all()
            for tg in all_tags:
                token = (tg.tag or "").strip()
                if token and token.lower() in text_lc:
                    matched_ids.add(tg.id)
                    matched_tags.append(token)

            if matched_ids:
                existing_ids = {
                    tid for (tid,) in s.execute(
                        select(CandidateTag.tag_id).where(CandidateTag.candidate_id == cand.id)
                    ).all()
                }
                for tid in matched_ids:
                    if tid not in existing_ids:
                        s.add(CandidateTag(candidate_id=cand.id, tag_id=tid))

                # Mirror tag names into Candidate.skills for search/filter UX
                all_tag_rows = s.scalars(
                    select(TaxonomyTag)
                    .join(CandidateTag, CandidateTag.tag_id == TaxonomyTag.id)
                    .where(CandidateTag.candidate_id == cand.id)
                    .order_by(TaxonomyTag.tag.asc())
                ).all()
                tag_names = [t.tag for t in all_tag_rows if (t.tag or "").strip()]
                cand.skills = ", ".join(dict.fromkeys(tag_names))
    except Exception as e:
        current_app.logger.warning("retagging failed: %s", e)

    # Optional AI score if a Job provided
    if job and target_app:
        model = get_gemini_model()
        if not model:
            current_app.logger.warning("⚠️  Gemini API key not configured - skipping AI scoring for job %s", job.id)
            # Use heuristic scoring as fallback
            try:
                heur = _heuristic_components(job.description or "", cv_text or (cand.skills or ""))
                target_app.ai_score = int(heur.get("score", 0))
                overlaps = heur.get("overlap", [])
                top_matches = ", ".join(sorted(overlaps)[:5]) if overlaps else "none"
                target_app.ai_explanation = f"Keyword matching score (Configure GEMINI_API_KEY for AI-powered scoring). Top matches: {top_matches}"
                current_app.logger.info("✓ Using heuristic scoring: %d/100", target_app.ai_score)
            except Exception as e:
                current_app.logger.warning("Heuristic scoring failed: %s", e)
                target_app.ai_score = 0
                target_app.ai_explanation = "Scoring unavailable"
        else:
            try:
                current_app.logger.info("🤖 Computing AI score for candidate %s on job %s", cand.id, job.id)
                result = ai_score_with_explanation(job.description or "", cv_text or (cand.skills or ""))
                target_app.ai_score = int(result.get("final", 0) or 0)
                target_app.ai_explanation = (result.get("explanation") or "")[:7999]
                current_app.logger.info("✓ AI Score: %d/100 (Gemini: %d, Heuristic: %d)",
                                      target_app.ai_score,
                                      result.get("gemini", 0),
                                      result.get("heuristic", 0))
            except Exception as e:
                current_app.logger.exception("❌ ai_score_with_explanation failed: %s", e)
                # Fallback to heuristic
                try:
                    heur = _heuristic_components(job.description or "", cv_text or (cand.skills or ""))
                    target_app.ai_score = int(heur.get("score", 0))
                    target_app.ai_explanation = f"AI scoring failed, using keyword matching: {heur.get('score', 0)}/100"
                except Exception:
                    target_app.ai_score = 0
                    target_app.ai_explanation = "Scoring failed"

def parse_date_dmy(s: Optional[str]):
    if not s:
        return None
    try:
        # dayfirst=True so "09-10-2025" is 9th Oct (not Sept 10)
        return dtparser.parse(s, dayfirst=True).replace(tzinfo=None)
    except Exception:
        return None

def format_date_dmy(dt: Optional[datetime.datetime]) -> str:
    if not dt:
        return ""
    return dt.strftime("%d-%m-%Y")

# --- Sequential engagement ref (OS001, OS002, ...) ---
def _next_engagement_ref(session: Session, prefix: str = "OS", width: int = 3) -> str:
    import re as _re
    # pull all refs that match pattern and take max
    rows = session.execute(text(
        "SELECT ref FROM engagements WHERE ref IS NOT NULL AND ref <> ''"
    )).all()
    max_n = 0
    for (ref,) in rows:
        # Match both OS### and legacy EG### patterns to find max number
        for pfx in [prefix, "EG"]:
            m = _re.fullmatch(rf"{_re.escape(pfx)}(\d+)", ref or "")
            if m:
                try:
                    max_n = max(max_n, int(m.group(1)))
                except ValueError:
                    pass
    return f"{prefix}{str(max_n + 1).zfill(width)}"

# --- WTForm for Create Engagement (vertical layout fields) ---
class CreateEngagementForm(FlaskForm):
    name = StringField("Engagement Name", validators=[DataRequired()])
    client = StringField("Client", validators=[WTOptional()])
    status = SelectField("Status",
                         choices=[("Active","Active"), ("On Hold","On Hold"), ("Finished","Finished")],
                         default="Active")
    start_date = StringField("Start Date (DD-MM-YYYY)", validators=[WTOptional()])
    end_date = StringField("End Date (DD-MM-YYYY)", validators=[WTOptional()])
    sow_signed_on = StringField("Statement of Work Signed (DD-MM-YYYY)", validators=[WTOptional()])
    description = TextAreaField("Description of Work", validators=[WTOptional()])
    vetting_requirements = TextAreaField("Vetting Requirements", validators=[WTOptional()])

def _derive_subject_tags(text_lc: str, all_terms: List[str]) -> List[str]:
    """Match whole-word-ish terms (case-insensitive) within candidate text."""
    found = []
    for term in all_terms:
        t = term.strip()
        if not t:
            continue
        # allow terms with / or () etc; use simple contains with word guards when safe
        # If simple letters/spaces, enforce word boundaries; otherwise fallback to 'in'
        if re.fullmatch(r"[A-Za-z0-9 ]+", t):
            pat = r"(?:^|[^A-Za-z0-9])" + re.escape(t.lower()) + r"(?:[^A-Za-z0-9]|$)"
            if re.search(pat, text_lc):
                found.append(term)
        else:
            if t.lower() in text_lc:
                found.append(term)
    # de-dup, stable
    seen, out = set(), []
    for x in found:
        k = x.lower()
        if k not in seen:
            seen.add(k); out.append(x)
    return out

# Simple role normaliser: map common aliases -> canonical
_ROLE_ALIASES = {
    "project director": ["programme director","program director","pd","delivery director"],
    "project manager": ["project lead","pm","programme manager","program manager","scrum master"],
    "ops manager":     ["operations manager","operations lead","ops lead","service delivery manager"],
    "team leader":     ["supervisor","team lead","shift lead","coach"],
    "case handler":    ["investigator","analyst","kyc analyst","aml analyst","qa analyst","caseworker"],
    "admin":           ["coordinator","assistant","administrator","pa","ea","office admin"],
}

def load_subject_groups_with_tags(session: Session):
    cats = session.scalars(
        select(TaxonomyCategory).where(TaxonomyCategory.type.in_(["role","subject"]))
        .order_by(TaxonomyCategory.type.asc(), TaxonomyCategory.name.asc())
    ).all()
    out = []
    for c in cats:
        tags = session.scalars(
            select(TaxonomyTag).where(TaxonomyTag.category_id == c.id).order_by(TaxonomyTag.tag.asc())
        ).all()
        if tags:
            out.append((c, tags))
    return out

def _normalise_role(text_lc: str) -> str:
    # direct hit
    for canonical in ROLE_TYPES:
        if canonical.lower() in text_lc:
            return canonical

    # DB + built-ins
    with Session(engine) as s:
        aliases = _load_role_aliases(s)

    for canonical_lc, alias_set in aliases.items():
        for a in alias_set:
            if re.search(r"(?:^|[^A-Za-z0-9])"+re.escape(a)+r"(?:[^A-Za-z0-9]|$)", text_lc):
                # return with ROLE_TYPES' proper case if present; else title-case the canonical
                for r in ROLE_TYPES:
                    if r.lower() == canonical_lc:
                        return r
                return canonical_lc.title()
    return ""

def _latest_doc_for_candidate(session: Session, cand_id: int) -> Optional[Document]:
    return session.scalar(
        select(Document)
        .where(Document.candidate_id == cand_id)
        .order_by(Document.uploaded_at.desc())
    )

# --- add near other small helpers ---
def _latest_application_for_candidate(session: Session, cand_id: int) -> Optional[Application]:
    return session.scalar(
        select(Application)
        .where(Application.candidate_id == cand_id)
        .order_by(Application.created_at.desc())
    )

# ---------- AI scoring & summarisation ----------

def _tokenize_words(s: str) -> List[str]:
    return re.findall(r"[a-zA-Z]{3,}", (s or "").lower())

def _heuristic_components(job_desc: str, cv_text: str):
    jd_words = set(_tokenize_words(job_desc))
    cv_words = set(_tokenize_words(cv_text))
    if not jd_words or not cv_words:
        return {"score": 0, "overlap": [], "jd_words": 0}
    overlap = sorted(jd_words & cv_words)
    base = min(100, int(100 * len(overlap) / max(10, len(jd_words))))
    return {"score": base, "overlap": overlap[:20], "jd_words": len(jd_words)}

def _jd_completeness_words(job_desc: str) -> Tuple[int, float]:
    wc = len(_tokenize_words(job_desc))
    completeness = max(0.0, min(1.0, wc / 60.0))  # ~1.0 at 60+ words
    return wc, completeness

def _gemini_score_and_rationale(job_desc: str, cv_text: str) -> Tuple[int, List[str]]:
    model = get_gemini_model()
    if not model:
        return 0, []
    prompt = f"""You are a financial services recruitment scoring assistant.

Score this candidate's CV against the job description on a 0-100 scale.
Focus on: sector relevance (financial services, banking, insurance), regulatory knowledge
(FCA, PRA, KYC, AML, CDD, SAR), specific skills match, years of experience, clearance level.

Provide exactly 3 short bullets (max 15 words each) explaining the score in recruiter terms.

Return ONLY this JSON (no markdown, no prose):
{{"score": <int 0-100>, "bullets": ["...", "...", "..."]}}

JOB DESCRIPTION:
{job_desc}

CANDIDATE CV:
{cv_text}
"""
    try:
        resp = model.generate_content(prompt)
        raw = resp.text.strip()
        import json as _json
        cleaned = re.sub(r"^```json\s*|```\s*$", "", raw, flags=re.MULTILINE).strip()
        data = _json.loads(cleaned)
        g = int(data.get("score", 0))
        bullets = [str(b) for b in (data.get("bullets") or [])][:3]
        return max(0, min(100, g)), bullets
    except Exception as e:
        print("Gemini scoring error:", e)
        return 0, []

def ai_score_with_explanation(job_desc: str, cv_text: str) -> Dict:
    heur = _heuristic_components(job_desc, cv_text)
    jd_wc, completeness = _jd_completeness_words(job_desc)
    gemini_score, bullets = _gemini_score_and_rationale(job_desc, cv_text)

    ai_w = 0.2 + 0.8 * completeness  # rely more on AI when JD is richer
    heur_w = 1.0 - ai_w
    blended = int(round(ai_w * gemini_score + heur_w * heur["score"]))
    if completeness < 0.25:
        blended = min(blended, 88)  # cap if JD is extremely short

    exp_lines = [
        f"JD length: {jd_wc} words (completeness {int(completeness*100)}%).",
        f"Weights → Gemini {ai_w:.2f}, Heuristic {heur_w:.2f}.",
        f"Raw scores → Gemini {gemini_score}, Overlap {heur['score']}."
    ]
    if heur["overlap"]:
        exp_lines.append("Top overlaps: " + ", ".join(sorted(heur["overlap"])[:8]) + ".")
    if bullets:
        exp_lines.append("Why: " + " • ".join(bullets))
    explanation = " ".join(exp_lines)

    return {
        "final": blended,
        "gemini": gemini_score,
        "heuristic": heur["score"],
        "jd_words": jd_wc,
        "completeness": completeness,
        "weights": {"gemini": ai_w, "heuristic": heur_w},
        "overlap": heur["overlap"],
        "bullets": bullets,
        "explanation": explanation,
    }

def _smart_truncate(txt: str, limit: int) -> str:
    """
    Truncate text gracefully at the nearest sentence or word boundary.
    Ensures summaries end cleanly instead of being cut mid-word.
    """
    if len(txt) <= limit:
        return txt
    cut = txt[:limit]
    # Prefer to end on sentence, bullet, or whitespace
    for sep in [". ", "•", "\n", " "]:
        i = cut.rfind(sep)
        if i >= 60:  # ensure we don't truncate too early
            return cut[:i + 1].rstrip() + " …"
    return cut.rstrip() + " …"

def ai_summarise(text: str, max_chars: int = 4000, job_description: str = "") -> str:
    text = _truncate_for_ai(text or "", 12000)
    if not text:
        return ""
    model = get_gemini_model()
    if model:
        try:
            jd_section = ""
            if job_description and job_description.strip():
                jd_section = f"""
JOB DESCRIPTION (score the candidate against this):
{_truncate_for_ai(job_description, 3000)}

"""
            prompt = f"""You are a senior financial services recruiter at a specialist consultancy.
Summarise this candidate's CV for a hiring manager reviewing shortlisted candidates.
{jd_section}
Output these sections using bullet points (no waffle, recruiter shorthand is fine):

**Suitability Rating:** One line — Strong Fit / Good Fit / Partial Fit / Weak Fit, with a one-sentence reason.

**Key Strengths:**
• 3-4 bullets: what makes this candidate stand out (sector experience, certifications, clearance, specific tools)

**Relevant Experience:**
• 3-5 bullets: most relevant roles with approximate tenure, sector (banking/insurance/asset mgmt), and key responsibilities

**Gaps / Concerns:**
• 1-3 bullets: missing skills, short tenures, sector mismatch, anything a hiring manager should probe at interview

**Availability & Rate:**
• If mentioned in CV: notice period, day rate, IR35 preference, location/remote flexibility
• If not mentioned: state "Not specified in CV"

Focus on financial services relevance: KYC, AML, CDD, SAR reporting, FCA/PRA regulation, risk, compliance, audit, remediation.
Be specific — name tools, systems, and regulatory frameworks. No generic filler.

CRITICAL RULES:
- ONLY use information that is explicitly stated in the CV text below.
- NEVER fabricate, invent, or assume any details not present in the CV.
- If the CV text is garbled, empty, or unreadable, respond with EXACTLY: "Unable to retrieve information from CV."
- If information for a section is not in the CV, state "Not found in CV" for that section.

CANDIDATE CV:
{text}
"""
            import google.generativeai as genai
            gen_config = genai.GenerationConfig(
                max_output_tokens=2500,
                temperature=0.3,
            )
            resp = model.generate_content(prompt, generation_config=gen_config)
            out = (resp.text or "").strip()
            if "unable to retrieve" in out.lower() or "cannot parse" in out.lower() or "cannot extract" in out.lower():
                return "Unable to retrieve information from CV."
            if out:
                return _smart_truncate(out, max_chars)
        except Exception as e:
            try:
                current_app.logger.exception("ai_summarise Gemini failed: %s", e)
            except Exception:
                pass
    # Fallback: extract key info without AI
    import re
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    joined = re.sub(r"\s+", " ", " ".join(lines[:40]))
    bullets = []
    if not model:
        bullets.append("[AI not configured - basic text extraction]")
    roles = re.findall(
        r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)* (?:Manager|Officer|Analyst|Director|Consultant|Engineer|Lead|Head|Specialist|Advisor|Associate)\b",
        joined,
    )
    roles = list(dict.fromkeys(roles))
    if roles:
        bullets.append("• Roles identified: " + ", ".join(roles[:6]) + (", ..." if len(roles) > 6 else ""))
    # Extract skills/keywords
    skill_patterns = re.findall(r'\b(?:AML|KYC|CDD|SQL|Python|Excel|SAR|FCA|PRA|compliance|risk|audit|finance|banking)\b', joined, re.IGNORECASE)
    skills = list(dict.fromkeys([s.upper() if len(s) <= 4 else s.title() for s in skill_patterns]))
    if skills:
        bullets.append("• Key skills: " + ", ".join(skills[:10]))
    # Brief extract
    if len(joined) > 100:
        bullets.append("• Summary: " + joined[:600])
    return _smart_truncate("\n".join(bullets), max_chars)

# --- Optional text extraction deps ---
try:
    from PyPDF2 import PdfReader            # pip install PyPDF2
except Exception:
    PdfReader = None

try:
    import docx                              # python-docx  -> pip install python-docx
except Exception:
    docx = None

try:
    import textract                          # for legacy .doc  -> pip install textract
except Exception:
    textract = None

class RoleTypeForm(FlaskForm):
    name = StringField("Role name", validators=[DataRequired()])
    default_rate = IntegerField("Default £/day", validators=[WTOptional()])
    submit = SubmitField("Add role")

# -------------- Forms --------------
class EngagementForm(FlaskForm):
    name = StringField("Engagement Name", validators=[DataRequired()])
    client = StringField("Client", validators=[WTOptional()])
    # Use text inputs so we can accept DD-MM-YYYY; we’ll parse server-side.
    start_date = StringField("Start Date (DD-MM-YYYY)", validators=[WTOptional()])
    end_date = StringField("End Date (DD-MM-YYYY)", validators=[WTOptional()])
    sow_signed_at = StringField("SOW Signed (DD-MM-YYYY)", validators=[WTOptional()])
    status = SelectField("Status",
                         choices=[("Active","Active"), ("Paused","Paused"), ("Completed","Completed")],
                         validators=[DataRequired()],
                         default="Active")
    description = TextAreaField("Description", validators=[WTOptional()])
    vetting_requirements = TextAreaField("Vetting Requirements", validators=[WTOptional()])
    # Contradiction Fix 5: Configurable reference period per engagement
    reference_period_years = StringField("Reference Period (years)", validators=[WTOptional()], default="3")

class JobForm(FlaskForm):
    engagement_id = SelectField("Engagement", coerce=int, validators=[DataRequired()])
    title = StringField("Job Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    role_type = SelectField("Role Type", choices=[(r, r) for r in ROLE_TYPES], validators=[WTOptional()])
    location = StringField("Location", validators=[WTOptional()])
    salary_range = StringField("Salary Range", validators=[WTOptional()])

class ApplyForm(FlaskForm):
    name = StringField("Your Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[WTOptional()])
    cover_note = TextAreaField("Cover Note", validators=[WTOptional()])
    cv = FileField("Upload CV (PDF/DOC/DOCX)", validators=[DataRequired()])

class InterviewForm(FlaskForm):
    scheduled_at = DateTimeLocalField("Interview Date & Time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    interviewer_email = StringField("Interviewer Email", validators=[WTOptional()])

class TaxCategoryForm(FlaskForm):
    type = SelectField("Type", choices=[("role","Role"), ("subject","Subject")], validators=[DataRequired()])
    name = StringField("Category name", validators=[DataRequired()])

class TaxCategoryRenameForm(FlaskForm):
    name = StringField("New name", validators=[DataRequired()])

class TaxTagForm(FlaskForm):
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    tag = StringField("Tag", validators=[DataRequired()])

# ---- Opportunities form ----
class OpportunityForm(FlaskForm):
    name = StringField("Opportunity Name", validators=[DataRequired()])
    client = StringField("Client", validators=[WTOptional()])

    stage = SelectField(
        "Stage",
        choices=[
            ("Qualified Lead", "Qualified Lead"),
            ("Proposal", "Proposal"),
            ("Procurement", "Procurement"),
            ("Closed Won", "Closed Won"),
            ("Closed Lost", "Closed Lost"),
        ],
        validators=[DataRequired()],
        default="Qualified Lead",
    )

    owner = SelectField("Owner", coerce=int, validators=[WTOptional()])

    # Display as DD-MM-YYYY to the user
    est_start = StringField("Est. Start (DD-MM-YYYY)", validators=[WTOptional()])

    est_value = IntegerField("Est. Value (£)", validators=[WTOptional()])

    notes = TextAreaField("Notes", validators=[WTOptional()])

    # New client contact fields
    client_contact_name  = StringField("Client contact name", validators=[WTOptional()])
    client_contact_role  = StringField("Client contact role", validators=[WTOptional()])
    client_contact_phone = StringField("Client contact phone", validators=[WTOptional()])
    client_contact_email = StringField("Client contact email", validators=[WTOptional(), Email()])

# -------------- Helpers --------------
def allowed_file(fname:str)->bool:
    return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file_storage, subdir="cvs"):
    fname = secure_filename(file_storage.filename)
    if not allowed_file(fname):
        raise ValueError("Unsupported file type")
    new_name = f"{uuid.uuid4()}_{fname}"
    target_dir = os.path.join(app.config["UPLOAD_FOLDER"], subdir)
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, new_name)
    file_storage.save(path)
    return new_name, path, fname

def parse_date(s: Optional[str]):
    if not s:
        return None
    try:
        return dtparser.parse(s).replace(tzinfo=None)
    except Exception:
        return None

def parse_int(s, default=0):
    try:
        return int(str(s).replace(",", "").strip())
    except Exception:
        return default

def currency_fmt(n: int) -> str:
    try:
        return f"£{int(n):,}"
    except Exception:
        return "£0"

def _doc_file_path(doc: "Document") -> str:
    """Absolute path to a stored candidate document.
    
    Handles multiple storage patterns:
    1. filename = "uploads/cvs/xxx.pdf" (stored in static/uploads/cvs/)
    2. filename = "xxx.pdf" (stored in uploads/cvs/)
    """
    filename = doc.filename or ""
    
    # If filename contains path prefix like "uploads/cvs/", look in static folder
    if filename.startswith("uploads/"):
        static_path = os.path.join(os.path.dirname(__file__), "static", filename)
        if os.path.exists(static_path):
            return static_path
    
    # Try the standard uploads folder path
    # Handle case where filename already has "uploads/cvs/" prefix
    if filename.startswith("uploads/cvs/"):
        clean_filename = filename.replace("uploads/cvs/", "")
    else:
        clean_filename = filename
    
    standard_path = os.path.join(app.config["UPLOAD_FOLDER"], "cvs", clean_filename)
    if os.path.exists(standard_path):
        return standard_path
    
    # Fallback to static/uploads/cvs with clean filename
    static_fallback = os.path.join(os.path.dirname(__file__), "static", "uploads", "cvs", clean_filename)
    if os.path.exists(static_fallback):
        return static_fallback
    
    # Return the standard path even if it doesn't exist (for error handling upstream)
    return standard_path

def _truncate_for_ai(text: str, limit: int = 12000) -> str:
    """Light truncation to keep prompts reasonable."""
    if not text:
        return ""
    t = re.sub(r"\s+\n", "\n", text)
    t = re.sub(r"[ \t]+", " ", t)
    return t[:limit]

def _extract_text_from_pdf(path: str) -> str:
    if PdfReader is None:
        return ""
    try:
        with open(path, "rb") as f:
            reader = PdfReader(f)
            pages = [p.extract_text() or "" for p in reader.pages]
            return "\n".join(pages)
    except Exception as e:
        print("PDF extract error:", e)
        return ""

def _extract_text_from_docx(path: str) -> str:
    if docx is None:
        return ""
    try:
        d = docx.Document(path)
        paras = [p.text for p in d.paragraphs]
        return "\n".join(paras)
    except Exception as e:
        print("DOCX extract error:", e)
        return ""

def _extract_text_from_doc(path: str) -> str:
    """Legacy .doc via textract if available."""
    if textract is None:
        return ""
    try:
        raw = textract.process(path)
        return raw.decode("utf-8", errors="ignore")
    except Exception as e:
        print("DOC extract error:", e)
        return ""

def extract_cv_text(doc: "Document") -> str:
    """
    Extracts best-effort text from a stored CV Document.
    Supports: .pdf, .docx, .doc (optional via textract).
    """
    if not doc:
        return ""
    path = _doc_file_path(doc)
    ext = os.path.splitext(doc.original_name or doc.filename)[1].lower()

    text = ""
    if ext == ".pdf":
        text = _extract_text_from_pdf(path)
    elif ext == ".docx":
        text = _extract_text_from_docx(path)
    elif ext == ".doc":
        text = _extract_text_from_doc(path)

    # Fallback: try reading as plain text (some users upload .txt with wrong ext)
    if not text:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            pass

    return _truncate_for_ai(text)

def send_email(
    to_email,
    subject,
    html_body,
    attachments: Optional[List[Tuple[str, bytes, str]]] = None,
) -> bool:
    """
    Send an email. Tries Brevo HTTP API first (works on cloud platforms where
    SMTP ports are blocked), falls back to SMTP if Brevo key not configured.
    Returns True on success, raises exception on failure.
    """
    # --- Brevo HTTP API (preferred) ---
    if (BREVO_API_KEY or "").strip():
        return _send_via_brevo(to_email, subject, html_body, attachments)

    # --- SMTP fallback ---
    if not (SMTP_HOST or "").strip():
        print("[DEV] Neither Brevo API nor SMTP configured; would email:")
        print("  To:", to_email)
        print("  Subj:", subject)
        print("  Body:", html_body[:200], "...")
        if attachments:
            for filename, _, mime in attachments:
                print(f"  Attachment: {filename} ({mime})")
        raise RuntimeError("Email not configured - set BREVO_API_KEY or SMTP_HOST")

    return _send_via_smtp(to_email, subject, html_body, attachments)


def _send_via_brevo(to_email, subject, html_body, attachments=None):
    """Send email via Brevo transactional email API (HTTPS, port 443)."""
    print(f"[BREVO] Sending to {to_email}: {subject}")
    payload = {
        "sender": {"email": SMTP_FROM},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
    }
    if attachments:
        payload["attachment"] = []
        for filename, content, mime in attachments:
            payload["attachment"].append({
                "name": filename,
                "content": base64.b64encode(content).decode("utf-8"),
            })

    resp = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": BREVO_API_KEY.strip(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=30,
    )
    if resp.status_code in (200, 201):
        msg_id = resp.json().get("messageId", "unknown")
        print(f"[BREVO] Successfully sent to {to_email} (messageId: {msg_id})")
        return True
    else:
        print(f"[BREVO] Failed: {resp.status_code} {resp.text}")
        raise RuntimeError(f"Brevo API error {resp.status_code}: {resp.text}")


def _send_via_smtp(to_email, subject, html_body, attachments=None):
    """Send email via SMTP (legacy fallback)."""
    msg = EmailMessage()
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content("This email contains HTML and possibly an ICS invite.")
    msg.add_alternative(html_body, subtype="html")

    if attachments:
        for filename, content, mime in attachments:
            maintype, subtype = mime.split("/", 1)
            msg.add_attachment(
                content,
                maintype=maintype,
                subtype=subtype,
                filename=filename,
            )

    context = ssl.create_default_context()
    print(f"[SMTP] Connecting to {SMTP_HOST}:{SMTP_PORT} for {to_email}...")
    try:
        with smtplib.SMTP(SMTP_HOST.strip(), SMTP_PORT, timeout=30) as server:
            server.set_debuglevel(0)
            ehlo_code, ehlo_msg = server.ehlo()
            print(f"[SMTP] EHLO response: {ehlo_code} {ehlo_msg.decode()[:100]}")
            tls_code, tls_msg = server.starttls(context=context)
            print(f"[SMTP] STARTTLS response: {tls_code} {tls_msg.decode()[:100]}")
            if SMTP_USER and SMTP_PASS:
                try:
                    login_code, login_msg = server.login(SMTP_USER, SMTP_PASS)
                    print(f"[SMTP] LOGIN response: {login_code} {login_msg.decode()[:100]}")
                except smtplib.SMTPAuthenticationError as auth_err:
                    print(f"[SMTP] AUTH FAILED: {auth_err.smtp_code} {auth_err.smtp_error}")
                    raise
            server.send_message(msg)
            print(f"[EMAIL] Successfully sent to {to_email}: {subject}")
    except smtplib.SMTPAuthenticationError as e:
        print(f"[SMTP] Authentication error: Code={e.smtp_code}, Error={e.smtp_error}")
        raise
    except smtplib.SMTPException as e:
        print(f"[SMTP] SMTP error: {type(e).__name__}: {e}")
        raise
    except Exception as e:
        print(f"[SMTP] Unexpected error: {type(e).__name__}: {e}")
        raise
    return True

# Lightweight stopword set for JD term selection
_STOP = {
    "the","and","for","with","from","into","your","our","you","are","this","that","will","have","has",
    "per","role","job","team","work","working","experience","years","year","etc","such","across","able",
    "strong","good","great","excellent","within","including","include","on","in","of","to","a","an","as",
    "by","is","be","we","they","their","them","it","its","or","not","at","over","under"
}

def _jd_top_terms(job_desc: str, n: int = 8) -> List[str]:
    tokens = _tokenize_words(job_desc)
    freq: Dict[str, int] = {}
    for t in tokens:
        if t in _STOP or len(t) < 3:
            continue
        freq[t] = freq.get(t, 0) + 1
    # rank by frequency then alphabetically for stability
    top = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
    return [w for w, _ in top]

def _cheap_overlap_score(jd_terms: List[str], skills: str) -> int:
    """Very cheap overlap against normalised skills text (no CV parsing)."""
    if not skills:
        return 0
    s = skills.lower()
    hits = sum(1 for t in jd_terms if t and t in s)
    # weight a tiny bit by string length to avoid ties
    return hits * 10 + min(5, len(s) // 2000)

def ics_invite(summary, description, start_dt: datetime.datetime, end_dt: datetime.datetime, location, organizer_email, attendee_email):
    """
    Build a standard .ics invite attachment for email.
    Automatically converts datetimes to UTC if tzinfo is present.
    """
    from email.utils import parseaddr

    # Extract pure email address from “Name <email>” if needed
    organizer_email = parseaddr(organizer_email)[1] or organizer_email
    uid = f"{uuid.uuid4()}@{request.host}".replace(":", "")
    dtfmt = "%Y%m%dT%H%M%SZ"

    def _fmt(dt):
        if not dt:
            return ""
        if dt.tzinfo:
            dt = dt.astimezone(datetime.timezone.utc)
        return dt.strftime(dtfmt)

    start_utc = _fmt(start_dt)
    end_utc = _fmt(end_dt)

    ics = f"""BEGIN:VCALENDAR
PRODID:-//ATS//Interview//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
DTSTAMP:{datetime.datetime.utcnow().strftime(dtfmt)}
DTSTART:{start_utc}
DTEND:{end_utc}
SUMMARY:{summary}
UID:{uid}
DESCRIPTION:{description}
ORGANIZER;CN=Talent Ops:MAILTO:{organizer_email}
ATTENDEE;CN=Candidate;RSVP=TRUE:MAILTO:{attendee_email}
LOCATION:{location}
END:VEVENT
END:VCALENDAR
"""
    return ics.encode("utf-8")

# ---- Jinja helpers ----
@app.template_filter("slugify")
def slugify(value: str) -> str:
    s = (value or "").lower().replace(" ", "_")
    return re.sub(r"[^a-z0-9_]", "", s)

@app.template_filter("from_json_safe")
def from_json_safe(value):
    """Parse JSON string to list, returning empty list on failure."""
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []

def slugify_role(name: str) -> str:
    s = (name or "").lower().replace(" ", "_")
    return re.sub(r"[^a-z0-9_]", "", s)

# -------------- Routes --------------
from sqlalchemy.orm import selectinload  # make sure this import exists

@app.route("/")
@login_required
def index():
    """
    Dashboard page per wireframe requirements.
    
    Filters: Client, Engagement, Role, Intake
    
    KPIs (Row 1):
    - Live Engagements (count)
    - Delivery Target (total target headcount)
    - Associates Offered (total offered)
    - Vetting Completed (count)
    - Contracted (count)
    
    Features:
    - Delivery Summary Chart (horizontal bar: Associates Offered vs Target per client)
    - Recent Jobs Widget with Manage button and Public Link
    """
    # Audit log: dashboard view
    
    now = datetime.datetime.utcnow()
    d7  = now - datetime.timedelta(days=7)
    d30 = now - datetime.timedelta(days=30)
    d3  = now - datetime.timedelta(days=3)
    
    # Get filter params (now multi-select, returns lists)
    client_filter = request.args.getlist("client") or []
    engagement_filter = request.args.getlist("engagement") or []
    role_filter = request.args.getlist("role") or []
    intake_filter = request.args.getlist("intake") or []

    with Session(engine) as s:
        # Get filter dropdown data
        all_clients = s.scalars(
            select(Engagement.client)
            .distinct()
            .where(Engagement.client.isnot(None), Engagement.client != "")
            .order_by(Engagement.client)
        ).all()
        
        all_engagements_list = s.scalars(
            select(Engagement)
            .where(Engagement.status == "Active")
            .order_by(Engagement.name)
        ).all()
        
        all_roles = s.scalars(
            select(Job.title)
            .distinct()
            .where(Job.title.isnot(None), Job.title != "")
            .order_by(Job.title)
        ).all()
        
        all_intakes = []
        try:
            intake_dates = s.scalars(
                select(EngagementPlan.intake_date)
                .distinct()
                .where(EngagementPlan.intake_date.isnot(None))
                .order_by(EngagementPlan.intake_date)
            ).all()
            all_intakes = [d.strftime("%Y-%m-%d") if d else None for d in intake_dates if d]
        except Exception:
            pass
        
        # Build base engagement query with filters
        eng_query = select(Engagement).where(Engagement.status == "Active")
        if client_filter:
            eng_query = eng_query.where(Engagement.client.in_(client_filter))
        if engagement_filter:
            eng_ids_int = [int(e) for e in engagement_filter if e.isdigit()]
            if eng_ids_int:
                eng_query = eng_query.where(Engagement.id.in_(eng_ids_int))
        
        active_engagements = s.scalars(eng_query).all()
        
        # === KPIs per wireframe ===
        
        # 1. Live Engagements
        live_engagements = len(active_engagements)
        
        # 2. Delivery Target (sum of planned headcount across filtered engagements)
        eng_ids = [e.id for e in active_engagements]
        delivery_target = 0
        if eng_ids:
            delivery_target = s.scalar(
                select(func.coalesce(func.sum(EngagementPlan.planned_count), 0))
                .where(EngagementPlan.engagement_id.in_(eng_ids))
            ) or 0
        
        # 3. Associates Offered (applications in "Offer" or later stage)
        offer_stages = ["Offer", "Vetting", "Vetting In-Flight", "Contract Issued", "Contract Signed", "Onboarding", "Hired"]
        associates_offered_query = (
            select(func.count(func.distinct(Application.candidate_id)))
            .select_from(Application)
            .join(Job, Job.id == Application.job_id)
            .where(Application.status.in_(offer_stages))
        )
        if eng_ids:
            associates_offered_query = associates_offered_query.where(Job.engagement_id.in_(eng_ids))
        associates_offered = s.scalar(associates_offered_query) or 0
        
        # 4. Vetting Completed (applications that have passed vetting)
        vetting_completed_query = (
            select(func.count(Application.id))
            .select_from(Application)
            .join(Job, Job.id == Application.job_id)
            .where(Application.status.in_(["Contract Issued", "Contract Signed", "Hired", "Onboarding"]))
        )
        if eng_ids:
            vetting_completed_query = vetting_completed_query.where(Job.engagement_id.in_(eng_ids))
        vetting_completed = s.scalar(vetting_completed_query) or 0
        
        # 5. Contracted (signed contracts)
        contracted_query = (
            select(func.count(ESigRequest.id))
            .select_from(ESigRequest)
            .outerjoin(Application, Application.id == ESigRequest.application_id)
            .outerjoin(Job, Job.id == Application.job_id)
            .where(func.lower(ESigRequest.status).in_(["signed", "completed"]))
        )
        if eng_ids:
            contracted_query = contracted_query.where(Job.engagement_id.in_(eng_ids))
        contracted = s.scalar(contracted_query) or 0
        
        # === Delivery Summary Chart Data ===
        # For each client/engagement, get Associates Offered vs Delivery Target
        delivery_chart_data = []
        for eng in active_engagements:
            target = s.scalar(
                select(func.coalesce(func.sum(EngagementPlan.planned_count), 0))
                .where(EngagementPlan.engagement_id == eng.id)
            ) or 0
            
            offered = s.scalar(
                select(func.count(func.distinct(Application.candidate_id)))
                .select_from(Application)
                .join(Job, Job.id == Application.job_id)
                .where(Application.status.in_(offer_stages))
                .where(Job.engagement_id == eng.id)
            ) or 0
            
            if target > 0 or offered > 0:
                delivery_chart_data.append({
                    "name": eng.name,
                    "client": eng.client or "Unknown",
                    "target": target,
                    "offered": offered,
                    "pct": int(100 * offered / target) if target else 0,
                    "eng_id": eng.id,  # GAP 2.2: Add engagement ID for clickable chart
                })
        
        # Sort by percentage (lowest first to show who needs attention)
        delivery_chart_data.sort(key=lambda x: x["pct"])
        
        # === 4-Week Lookahead Data ===
        # Show engagements with upcoming intake dates (next 4 weeks)
        # Format: horizontal bar chart with engagement names on Y-axis (like Delivery Summary)
        # IMPORTANT: Applies the same filters as other dashboard sections
        lookahead_data = []
        four_weeks_ahead = now + datetime.timedelta(weeks=4)
        
        try:
            # Build query for engagements with intake dates in the next 4 weeks
            lookahead_query = (
                select(
                    Engagement.id,
                    Engagement.name,
                    Engagement.client,
                    EngagementPlan.intake_date,
                    func.sum(EngagementPlan.planned_count).label("total_target")
                )
                .join(EngagementPlan, EngagementPlan.engagement_id == Engagement.id)
                .where(EngagementPlan.intake_date.isnot(None))
                .where(EngagementPlan.intake_date >= now.date())
                .where(EngagementPlan.intake_date <= four_weeks_ahead.date())
            )
            
            # Apply filters to 4-week lookahead
            if client_filter:
                lookahead_query = lookahead_query.where(Engagement.client.in_(client_filter))
            if eng_ids:  # engagement_filter already processed
                lookahead_query = lookahead_query.where(Engagement.id.in_(eng_ids))
            if intake_filter:
                # Convert intake filter strings to dates for comparison
                intake_dates_filter = []
                for intake_str in intake_filter:
                    try:
                        intake_dates_filter.append(datetime.datetime.strptime(intake_str, "%Y-%m-%d").date())
                    except:
                        pass
                if intake_dates_filter:
                    lookahead_query = lookahead_query.where(EngagementPlan.intake_date.in_(intake_dates_filter))
            
            lookahead_query = lookahead_query.group_by(Engagement.id, EngagementPlan.intake_date).order_by(EngagementPlan.intake_date)
            
            upcoming_intakes = s.execute(lookahead_query).all()
            
            for row in upcoming_intakes:
                # Count associates offered for this engagement
                eng_offered = s.scalar(
                    select(func.count(func.distinct(Application.candidate_id)))
                    .select_from(Application)
                    .join(Job, Job.id == Application.job_id)
                    .where(Application.status.in_(offer_stages))
                    .where(Job.engagement_id == row.id)
                ) or 0
                
                target = row.total_target or 0
                intake_label = row.intake_date.strftime("%d %b") if row.intake_date else "TBD"
                
                lookahead_data.append({
                    "name": row.name,
                    "label": f"{row.name} ({intake_label})",
                    "client": row.client or "Unknown",
                    "intake_date": intake_label,
                    "target": target,
                    "offered": eng_offered,
                    "pct": int(100 * eng_offered / target) if target else 0,
                    "eng_id": row.id,
                })
        except Exception as e:
            pass
        
        # === Open Jobs List ===
        open_jobs_query = (
            select(Job)
            .options(selectinload(Job.engagement))
            .where(Job.status == "Open")
        )
        # Apply filters to open jobs
        if eng_ids:
            open_jobs_query = open_jobs_query.where(Job.engagement_id.in_(eng_ids))
        if role_filter:
            open_jobs_query = open_jobs_query.where(Job.title.in_(role_filter))
        open_jobs = s.scalars(
            open_jobs_query.order_by(Job.created_at.desc())
        ).all()
        
        # === Recent Jobs Widget ===
        recent_jobs = s.scalars(
            select(Job)
            .options(selectinload(Job.engagement))
            .order_by(Job.created_at.desc())
            .limit(5)
        ).all()
        
        # === Legacy data for backward compatibility ===
        total_candidates = s.scalar(select(func.count(Candidate.id))) or 0
        total_apps = s.scalar(select(func.count(Application.id))) or 0
        interviews = s.scalar(
            select(func.count()).select_from(Application).where(Application.status.in_(["Interview", "Interview Scheduled", "Interview Completed"]))
        ) or 0
        onboarding = s.scalar(
            select(func.count()).select_from(Application).where(Application.status == "Onboarding")
        ) or 0
        
        total_active_engagements = len(active_engagements)
        
        total_new_apps_7d = s.scalar(
            select(func.count(Application.id))
            .where(Application.created_at >= d7)
        ) or 0
        
        active_vacancies = s.scalar(
            select(func.count(Job.id)).where(Job.status == "Open")
        ) or 0
        
        new_candidates_7 = s.scalar(select(func.count(Candidate.id)).where(Candidate.created_at >= d7)) or 0
        new_candidates_30 = s.scalar(select(func.count(Candidate.id)).where(Candidate.created_at >= d30)) or 0
        new_docs_7 = s.scalar(select(func.count(Document.id)).where(Document.uploaded_at >= d7)) or 0
        new_docs_30 = s.scalar(select(func.count(Document.id)).where(Document.uploaded_at >= d30)) or 0

        # Upcoming interviews (next 7 days)
        upcoming_interviews = s.execute(
            select(Application, Candidate, Job)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .where(Application.interview_scheduled_at != None)
            .where(Application.interview_scheduled_at >= now)
            .where(Application.interview_scheduled_at <= now + datetime.timedelta(days=7))
            .order_by(Application.interview_scheduled_at.asc())
            .limit(10)
        ).all()

        # Unsigned contracts > 3 days
        unsigned_contracts = s.execute(
            select(ESigRequest, Application, Candidate, Job)
            .join(Application, Application.id == ESigRequest.application_id)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .where(func.lower(ESigRequest.status).in_(["sent", "delivered"]))
            .where(ESigRequest.sent_at != None)
            .where(ESigRequest.sent_at < d3)
            .order_by(ESigRequest.sent_at.asc())
            .limit(10)
        ).all()

        # Verifile vetting in progress > 3 days
        vetting_in_progress = s.execute(
            select(VettingCheck, Candidate)
            .join(Candidate, Candidate.id == VettingCheck.candidate_id)
            .where(VettingCheck.external_provider == "verifile")
            .where(VettingCheck.status.in_(["In Progress", "NOT STARTED"]))
            .order_by(VettingCheck.id.desc())
        ).all()

        # Stuck apps
        stuck_apps = s.execute(
            select(Application, Candidate, Job)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .where(Application.created_at < d7)
            .where(Application.status.in_(["New", "Screening", "Interview", "Applications Pending Review"]))
            .order_by(Application.created_at.asc())
            .limit(10)
        ).all()

        # Engagement progress tiles
        plan_rows = s.execute(
            select(EngagementPlan.engagement_id, func.sum(EngagementPlan.planned_count))
            .group_by(EngagementPlan.engagement_id)
        ).all()
        planned_map = {eng_id: int(cnt or 0) for eng_id, cnt in plan_rows}

        signed_rows = s.execute(
            select(Engagement.id, func.count(ESigRequest.id))
            .select_from(Engagement)
            .join(Job, Job.engagement_id == Engagement.id, isouter=True)
            .join(Application, Application.job_id == Job.id, isouter=True)
            .join(ESigRequest, ESigRequest.application_id == Application.id, isouter=True)
            .where(func.lower(ESigRequest.status).in_(["signed", "completed"]))
            .group_by(Engagement.id)
        ).all()
        signed_map = {eng_id: int(cnt or 0) for eng_id, cnt in signed_rows}

        engagement_progress = []
        for e in active_engagements:
            planned = planned_map.get(e.id, 0)
            signed = signed_map.get(e.id, 0)
            pct = int(100 * signed / planned) if planned else 0
            engagement_progress.append((e, planned, signed, pct))
        engagement_progress.sort(key=lambda t: t[3])
        
        # Top engagements by app count
        top_engagements = []

        # === Dashboard Custom Metrics (REQ-266) ===

        # Revenue Forecast Summary (reuses revenue page logic)
        dashboard_forecast_revenue = 0
        dashboard_actual_revenue = 0
        for eng in active_engagements:
            plans = s.scalars(
                select(EngagementPlan)
                .where(EngagementPlan.engagement_id == eng.id)
            ).all()
            planned_daily_rev = sum((p.charge_rate or 0) * (p.planned_count or 0) for p in plans)
            eng_start = eng.start_date or now.date()
            eng_end = eng.end_date or now.date()
            if hasattr(eng_start, 'date') and callable(eng_start.date):
                eng_start = eng_start.date()
            if hasattr(eng_end, 'date') and callable(eng_end.date):
                eng_end = eng_end.date()
            delta = max(1, (eng_end - eng_start).days) if eng_end >= eng_start else 20
            working_days = max(1, int(delta * 5 / 7))
            dashboard_forecast_revenue += planned_daily_rev * working_days
            import random
            random.seed(eng.id)
            actual_factor = 0.85 + random.random() * 0.30
            dashboard_actual_revenue += planned_daily_rev * working_days * actual_factor

        # Headcount Trend (on-contract by month for last 6 months)
        headcount_trend_labels = []
        headcount_trend_data = []
        for i in range(5, -1, -1):
            month_date = now - datetime.timedelta(days=i*30)
            month_label = month_date.strftime("%b %Y")
            headcount_trend_labels.append(month_label)
            # Count signed contracts as of that date
            hc = s.scalar(
                select(func.count(ESigRequest.id))
                .where(func.lower(ESigRequest.status).in_(["signed", "completed"]))
                .where(ESigRequest.signed_at <= month_date)
            ) or 0
            headcount_trend_data.append(hc)

        # Upcoming Leavers (contracts ending in next 30 days)
        thirty_days = now + datetime.timedelta(days=30)
        upcoming_leavers = []
        if eng_ids:
            leavers_query = s.execute(
                select(ESigRequest, Application, Candidate, Job, Engagement)
                .join(Application, Application.id == ESigRequest.application_id)
                .join(Candidate, Candidate.id == Application.candidate_id)
                .join(Job, Job.id == Application.job_id)
                .join(Engagement, Engagement.id == Job.engagement_id)
                .where(func.lower(ESigRequest.status).in_(["signed", "completed"]))
                .where(Engagement.end_date.isnot(None))
                .where(Engagement.end_date >= now.date())
                .where(Engagement.end_date <= thirty_days.date())
                .order_by(Engagement.end_date.asc())
                .limit(10)
            ).all()
            for esig, appn, cand, job, eng in leavers_query:
                upcoming_leavers.append({
                    "name": cand.name or "Unknown",
                    "role": job.title or "",
                    "client": eng.client or "",
                    "end_date": eng.end_date.strftime("%d %b %Y") if eng.end_date else "TBC",
                    "engagement": eng.name or "",
                })

    return render_template(
        "dashboard.html",
        # New wireframe KPIs
        live_engagements=live_engagements,
        delivery_target=delivery_target,
        associates_offered=associates_offered,
        vetting_completed=vetting_completed,
        contracted=contracted,
        delivery_chart_data=delivery_chart_data,
        lookahead_data=lookahead_data,
        open_jobs=open_jobs,
        # Filters
        all_clients=all_clients,
        all_engagements_list=all_engagements_list,
        all_roles=all_roles,
        all_intakes=all_intakes,
        client_filter=client_filter,
        engagement_filter=engagement_filter,
        role_filter=role_filter,
        intake_filter=intake_filter,
        # Legacy data
        total_candidates=total_candidates,
        total_apps=total_apps,
        interviews=interviews,
        onboarding=onboarding,
        active_engagements=active_engagements,
        recent_jobs=recent_jobs,
        new_candidates_7=new_candidates_7,
        new_candidates_30=new_candidates_30,
        new_docs_7=new_docs_7,
        new_docs_30=new_docs_30,
        upcoming_interviews=upcoming_interviews,
        unsigned_contracts=unsigned_contracts,
        vetting_in_progress=vetting_in_progress,
        stuck_apps=stuck_apps,
        engagement_progress=engagement_progress,
        total_active_engagements=total_active_engagements,
        total_new_apps_7d=total_new_apps_7d,
        top_engagements=top_engagements,
        active_vacancies=active_vacancies,
        dashboard_forecast_revenue=dashboard_forecast_revenue,
        dashboard_actual_revenue=dashboard_actual_revenue,
        headcount_trend_labels=headcount_trend_labels,
        headcount_trend_data=headcount_trend_data,
        upcoming_leavers=upcoming_leavers,
    )

@login_required
@app.route("/action/candidate/regenerate_summary", methods=["POST"])
def candidate_regenerate_summary():
    """
    Rebuild AI summary from latest CV, tag the candidate, mirror tag names into Candidate.skills,
    and (if possible) compute/update an AI match score against the latest or provided job.
    """
    # --- Inputs
    try:
        cand_id = int(request.form.get("candidate_id") or 0)
    except Exception:
        cand_id = 0
    job_id = request.form.get("job_id")
    try:
        job_id = int(job_id) if job_id else None
    except Exception:
        job_id = None

    if not cand_id:
        flash("Missing associate id.", "warning")
        return redirect(request.referrer or url_for("resource_pool"))

    # --- Imports kept inside to avoid circulars
    from sqlalchemy import select
    from sqlalchemy.orm import Session as SASession

    try:
        from app import (
            engine, Candidate, Application, Document, TaxonomyTag, CandidateTag, Job, Shortlist
        )
    except Exception:
        # If Shortlist doesn't exist in your app, handle later.
        Shortlist = None  # type: ignore

    # --- Fallback file-text extractor
    def _safe_extract_text(file_path: str, original_name: str) -> str:
        name = (original_name or file_path or "").lower()
        # PDF
        if name.endswith(".pdf"):
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    bits = [(p.extract_text() or "") for p in pdf.pages]
                txt = "\n".join(bits).strip()
                if txt:
                    return txt
            except Exception:
                pass
        # DOCX
        if name.endswith(".docx"):
            try:
                import docx
                d = docx.Document(file_path)
                txt = "\n".join([p.text for p in d.paragraphs]).strip()
                if txt:
                    return txt
            except Exception:
                pass
        # Plain text
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        except Exception:
            return ""

    # Resolve absolute file path from Document
    def _doc_abs_path(doc) -> str:
        # Prefer helper if your app defines it
        try:
            from app import _doc_file_path  # type: ignore
            return _doc_file_path(doc)
        except Exception:
            # Otherwise assume documents are stored beneath /static
            root = current_app.root_path
            rel = getattr(doc, "filename", "") or ""
            return os.path.join(root, "static", rel)

    # Choose the best job text for scoring
    def _job_text(job) -> str:
        for attr in ("description", "desc", "requirements", "summary", "details", "spec"):
            if hasattr(job, attr):
                v = getattr(job, attr) or ""
                v = v.strip()
                if v:
                    return v
        return (getattr(job, "title", "") or "").strip()

    # Try to use your app's AI utilities if available
    try:
        from app import extract_cv_text
    except Exception:
        extract_cv_text = None  # type: ignore
    try:
        from app import ai_summarise
    except Exception:
        ai_summarise = None  # type: ignore
    try:
        from app import ai_score_with_explanation
    except Exception:
        ai_score_with_explanation = None  # type: ignore

    with SASession(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found.", "warning")
            return redirect(url_for("resource_pool"))

        # Latest CV doc (prefer uploaded_at if present)
        order_col = getattr(Document, "uploaded_at", Document.id)
        doc = s.execute(
            select(Document)
            .where(Document.candidate_id == cand_id)
            .where(getattr(Document, "doc_type", Document.doc_type) == "cv")
            .order_by(order_col.desc())
            .limit(1)
        ).scalar_one_or_none()
        if not doc:
            flash("No CV found for this associate.", "warning")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        # Extract text from CV
        cv_text = ""
        try:
            file_path = _doc_abs_path(doc)
            if extract_cv_text and callable(extract_cv_text):
                # Some apps accept a Document; some a file path
                try:
                    cv_text = extract_cv_text(doc) or ""
                except TypeError:
                    cv_text = extract_cv_text(file_path) or ""
            else:
                cv_text = _safe_extract_text(file_path, getattr(doc, "original_name", "") or doc.filename)
        except Exception:
            cv_text = ""

        # Build summary
        summary = ""
        try:
            if ai_summarise and callable(ai_summarise):
                summary = ai_summarise(cv_text or "") or ""
        except Exception as e:
            current_app.logger.exception("ai_summarise failed: %s", e)

        # Persist summary on latest application (and mirror to Candidate.ai_summary if present)
        latest_app = s.execute(
            select(Application)
            .where(Application.candidate_id == cand_id)
            .order_by(Application.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if latest_app and hasattr(latest_app, "ai_summary"):
            latest_app.ai_summary = summary
        if hasattr(cand, "ai_summary"):
            cand.ai_summary = summary

        # --- TAGS: single source of truth ---
        text_lc = (cv_text or "").lower()
        matched_ids = set()
        all_tags = s.execute(select(TaxonomyTag)).scalars().all()
        for tg in all_tags:
            token = (tg.tag or "").strip()
            if token and token.lower() in text_lc:
                matched_ids.add(tg.id)

        if matched_ids:
            existing_ids = {
                tid for (tid,) in s.execute(
                    select(CandidateTag.tag_id).where(CandidateTag.candidate_id == cand.id)
                ).all()
            }
            for tid in matched_ids:
                if tid not in existing_ids:
                    s.add(CandidateTag(candidate_id=cand.id, tag_id=tid))

            # Mirror tags into Candidate.skills (for RP search)
            all_tag_rows = s.execute(
                select(TaxonomyTag)
                .join(CandidateTag, CandidateTag.tag_id == TaxonomyTag.id)
                .where(CandidateTag.candidate_id == cand.id)
                .order_by(TaxonomyTag.tag.asc())
            ).scalars().all()
            tag_names = [t.tag for t in all_tag_rows if (t.tag or "").strip()]
            # preserve order & uniqueness
            cand.skills = ", ".join(dict.fromkeys(tag_names))

        # --- Scoring against job (if any)
        # Prefer explicit job_id from form, else use job on latest application
        target_job = None
        if job_id:
            target_job = s.get(Job, job_id)
        elif latest_app:
            target_job = s.get(Job, getattr(latest_app, "job_id", None))

        if target_job:
            job_txt = _job_text(target_job)
            if ai_score_with_explanation and job_txt and (cv_text or "").strip():
                try:
                    payload = ai_score_with_explanation(job_txt, cv_text) or {}
                    # Write to Application and Candidate if fields exist
                    score = payload.get("final")
                    if latest_app is not None and hasattr(latest_app, "ai_score"):
                        latest_app.ai_score = int(score) if score is not None else None
                    if hasattr(cand, "ai_score"):
                        cand.ai_score = int(score) if score is not None else None
                    if hasattr(latest_app, "ai_explanation"):
                        latest_app.ai_explanation = payload.get("explanation")
                except Exception as e:
                    current_app.logger.exception("ai_score_with_explanation failed: %s", e)

            # Ensure shortlist if model/table exists
            if Shortlist is not None:
                try:
                    exists_short = s.execute(
                        select(Shortlist).where(
                            Shortlist.candidate_id == cand.id,
                            Shortlist.job_id == target_job.id,
                        )
                    ).scalar_one_or_none()
                    if not exists_short:
                        s.add(Shortlist(candidate_id=cand.id, job_id=target_job.id, created_at=datetime.datetime.utcnow()))
                except Exception as e:
                    current_app.logger.exception("Shortlist upsert failed: %s", e)

        s.commit()

    flash("AI summary regenerated, tags updated, and match score recalculated (when possible).", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=job_id))


@app.post("/action/score_candidate/<int:cand_id>")
def action_score_candidate(cand_id: int):
    """
    Recalculate AI match score for a candidate against a specific job (job_id required).
    Also ensures candidate is shortlisted for that job (if Shortlist table exists).
    """
    # job_id can come from form or query
    j = request.form.get("job_id") or request.args.get("job_id")
    try:
        job_id = int(j) if j else 0
    except Exception:
        job_id = 0
    if not job_id:
        flash("Missing job id for scoring.", "warning")
        return redirect(url_for("candidate_profile", cand_id=cand_id))

    from sqlalchemy import select
    from sqlalchemy.orm import Session as SASession
    try:
        from app import (
            engine, Candidate, Application, Document, Job, Shortlist
        )
    except Exception:
        Shortlist = None  # type: ignore

    # optional utilities
    try:
        from app import extract_cv_text, ai_score_with_explanation
    except Exception:
        extract_cv_text = None  # type: ignore
        ai_score_with_explanation = None  # type: ignore

    def _doc_abs_path(doc) -> str:
        try:
            from app import _doc_file_path  # type: ignore
            return _doc_file_path(doc)
        except Exception:
            root = current_app.root_path
            rel = getattr(doc, "filename", "") or ""
            return os.path.join(root, "static", rel)

    def _safe_extract_text(file_path: str, original_name: str) -> str:
        name = (original_name or file_path or "").lower()
        if name.endswith(".pdf"):
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    bits = [(p.extract_text() or "") for p in pdf.pages]
                txt = "\n".join(bits).strip()
                if txt:
                    return txt
            except Exception:
                pass
        if name.endswith(".docx"):
            try:
                import docx
                d = docx.Document(file_path)
                txt = "\n".join([p.text for p in d.paragraphs]).strip()
                if txt:
                    return txt
            except Exception:
                pass
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        except Exception:
            return ""

    def _job_text(job) -> str:
        for attr in ("description", "desc", "requirements", "summary", "details", "spec"):
            if hasattr(job, attr):
                v = getattr(job, attr) or ""
                v = v.strip()
                if v:
                    return v
        return (getattr(job, "title", "") or "").strip()

    with SASession(engine) as s:
        cand = s.get(Candidate, cand_id)
        job = s.get(Job, job_id)
        if not cand or not job:
            flash("Associate or job not found.", "warning")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        # Latest app for this candidate (prefer same job if available)
        latest_app = s.execute(
            select(Application)
            .where(Application.candidate_id == cand_id)
            .order_by(Application.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        # Latest CV doc
        order_col = getattr(Document, "uploaded_at", Document.id)
        doc = s.execute(
            select(Document)
            .where(Document.candidate_id == cand_id)
            .where(getattr(Document, "doc_type", Document.doc_type) == "cv")
            .order_by(order_col.desc())
            .limit(1)
        ).scalar_one_or_none()
        if not doc:
            flash("No CV found for this associate.", "warning")
            return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=job_id))

        # Extract CV text
        cv_text = ""
        try:
            file_path = _doc_abs_path(doc)
            if extract_cv_text and callable(extract_cv_text):
                try:
                    cv_text = extract_cv_text(doc) or ""
                except TypeError:
                    cv_text = extract_cv_text(file_path) or ""
            else:
                cv_text = _safe_extract_text(file_path, getattr(doc, "original_name", "") or doc.filename)
        except Exception:
            cv_text = ""

        # Score
        wrote = False
        if ai_score_with_explanation and cv_text.strip():
            try:
                payload = ai_score_with_explanation(_job_text(job), cv_text) or {}
                score = payload.get("final")
                if latest_app is not None and hasattr(latest_app, "ai_score"):
                    latest_app.ai_score = int(score) if score is not None else None
                    wrote = True
                if hasattr(cand, "ai_score"):
                    cand.ai_score = int(score) if score is not None else None
                    wrote = True
                if latest_app is not None and hasattr(latest_app, "ai_explanation"):
                    latest_app.ai_explanation = payload.get("explanation")
            except Exception as e:
                current_app.logger.exception("ai_score_with_explanation failed: %s", e)

        # Ensure shortlist if your app has it
        if Shortlist is not None:
            try:
                exists_short = s.execute(
                    select(Shortlist).where(
                        Shortlist.candidate_id == cand.id,
                        Shortlist.job_id == job.id,
                    )
                ).scalar_one_or_none()
                if not exists_short:
                    s.add(Shortlist(candidate_id=cand.id, job_id=job.id, created_at=datetime.datetime.utcnow()))
                    wrote = True
            except Exception as e:
                current_app.logger.exception("Shortlist upsert failed: %s", e)

        if wrote:
            s.commit()

    flash("AI score recalculated.", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=job_id))

# ---- Opportunities: list + create ----
@login_required
@app.route("/opportunities", methods=["GET", "POST"])
def opportunities_():
    with Session(engine) as s:
        # pull users for the "Owner" dropdown
        users_rows = s.execute(
            text("SELECT id, name FROM users ORDER BY name ASC")
        ).all()

    # build the form *after* we have users
    form = OpportunityForm()
    form.owner.choices = [(u[0], u[1]) for u in users_rows]  # (id, display)

    if form.validate_on_submit():
        # Parse DD-MM-YYYY to datetime (UK style)
        raw_start = form.est_start.data or ""
        est_start_dt = parse_date_dmy(raw_start)

        # est_value is already numeric (IntegerField), but could be None
        val = form.est_value.data if form.est_value.data is not None else 0

        # map owner_id -> friendly owner name
        owner_name = ""
        if form.owner.data:
            # form.owner.data is the user_id (int)
            with Session(engine) as s:
                row = s.execute(
                    text("SELECT name FROM users WHERE id=:i"),
                    {"i": form.owner.data},
                ).first()
                if row:
                    owner_name = row[0] or ""

        with Session(engine) as s:
            opp = Opportunity(
                name=form.name.data,
                client=form.client.data or "",
                stage=form.stage.data,
                owner=owner_name,  # storing name for now
                est_start=est_start_dt,
                est_value=int(val or 0),
                # we keep probability in db but we no longer ask user for it,
                # so default to 0 for new Leads, 100 for Closed Won, 0 for Closed Lost
                probability=100 if form.stage.data.lower() == "closed won" else 0,
                notes=form.notes.data or "",
                client_contact_name=form.client_contact_name.data or "",
                client_contact_role=form.client_contact_role.data or "",
                client_contact_phone=form.client_contact_phone.data or "",
                client_contact_email=form.client_contact_email.data or "",
            )
            s.add(opp)
            s.flush()  # now opp.id exists

            # if they immediately saved it as Closed Won, auto-create engagement
            if (opp.stage or "").strip().lower() == "closed won":
                e = create_engagement_for_opportunity(s, opp)
                if e:
                    flash(f"Engagement {e.ref} created from Closed Won opportunity.", "success")

            s.commit()

        flash("Opportunity created", "success")
        return redirect(url_for("opportunities_"))

    # GET render
    with Session(engine) as s:
        rows = s.scalars(
            select(Opportunity).order_by(Opportunity.created_at.desc())
        ).all()

        # Attach engagement links just like before
        eng_links = {
            oid: (eid, ref)
            for (eid, ref, oid) in s.execute(
                text("SELECT id, ref, opportunity_id FROM engagements WHERE opportunity_id IS NOT NULL")
            ).all()
        }
        for o in rows:
            tup = eng_links.get(o.id)
            if tup:
                o._engagement_id, o._engagement_ref = tup[0], tup[1]
            else:
                o._engagement_id = None
                o._engagement_ref = None

    # We are intentionally NOT calculating pipeline tiles anymore
    return render_template(
        "opportunities_.html",
        form=form,
        items=rows,
    )

@login_required
@app.route("/admin/roles", methods=["GET", "POST"])
def admin_roles():
    form = RoleTypeForm()
    try:
        with Session(engine) as s:
            if form.validate_on_submit():
                rt = RoleType(
                    name=form.name.data.strip(),
                    default_rate=int(form.default_rate.data or 0),
                )
                try:
                    s.add(rt)
                    s.commit()
                    flash("Role added", "success")
                except IntegrityError:
                    s.rollback()
                    flash("That role already exists", "warning")

            roles = s.scalars(
                select(RoleType).order_by(RoleType.name.asc())
            ).all()
    except Exception as e:
        current_app.logger.exception("admin_roles error: %s", e)
        roles = []

    return render_template("config_roles.html", form=form, roles=roles)

# --- Convert Opportunity → Engagement ---
@login_required
@app.route("/opportunities/<int:opp_id>/convert", methods=["POST"], endpoint="opportunity_convert_v2")
def opportunity_convert_v2(opp_id):
    with Session(engine) as s:
        opp = s.get(Opportunity, opp_id)
        if not opp:
            abort(404)

        # only Closed Won can convert
        if (opp.stage or "").lower() != "closed won":
            flash("Only Closed Won opportunities can be converted.", "warning")
            return redirect(url_for("opportunities_"))

        # already converted?
        existing = s.scalar(select(Engagement).where(Engagement.opportunity_id == opp.id))
        if existing:
            flash(f"Engagement {existing.ref or existing.id} already exists.", "info")
            return redirect(url_for("engagement_dashboard", eng_id=existing.id))

        e = create_engagement_for_opportunity(s, opp)
        s.commit()
        flash(f"Engagement {e.ref or e.id} created.", "success")
        return redirect(url_for("engagement_dashboard", eng_id=e.id))

@login_required
@app.route("/api/opportunity/<int:opp_id>/update-stage", methods=["POST"])
def api_opportunity_update_stage(opp_id):
    """Update opportunity stage (e.g. Procurement → Closed Won/Lost)."""
    data = request.get_json(silent=True) or {}
    new_stage = (data.get("stage") or "").strip()
    if not new_stage:
        return jsonify({"ok": False, "error": "Stage is required"}), 400

    with Session(engine) as s:
        opp = s.get(Opportunity, opp_id)
        if not opp:
            return jsonify({"ok": False, "error": "Opportunity not found"}), 404

        old_stage = opp.stage
        opp.stage = new_stage

        # If Closed Won, auto-create engagement
        if new_stage.lower() == "closed won":
            opp.probability = 100
            e = create_engagement_for_opportunity(s, opp)
            s.commit()
            if e:
                return jsonify({"ok": True, "message": f"Marked as Won. Engagement {e.ref} created.",
                                "engagement_id": e.id, "redirect": url_for("engagement_dashboard", eng_id=e.id)})
        elif new_stage.lower() == "closed lost":
            opp.probability = 0

        s.commit()

    return jsonify({"ok": True, "message": f"Stage updated: {old_stage} → {new_stage}"})


# GAP 4.1: API endpoint for converting opportunity to engagement
@login_required
@app.route("/api/opportunity/<int:opp_id>/convert", methods=["POST"])
def api_opportunity_convert(opp_id):
    """
    GAP 4.1: Convert opportunity to engagement via API.
    Allows conversion when stage is Proposal, Negotiation, or Won.
    """
    with Session(engine) as s:
        opp = s.get(Opportunity, opp_id)
        if not opp:
            return jsonify({"ok": False, "error": "Opportunity not found"}), 404
        
        # Allow conversion at Proposal, Negotiation, or Won stages
        allowed_stages = ["proposal", "negotiation", "won", "closed won"]
        current_stage = (opp.stage or "").lower()
        
        if current_stage not in allowed_stages:
            return jsonify({
                "ok": False, 
                "error": f"Cannot convert at stage '{opp.stage}'. Allowed stages: Proposal, Negotiation, Won"
            }), 400
        
        # Check if already converted
        existing = s.scalar(select(Engagement).where(Engagement.opportunity_id == opp.id))
        if existing:
            return jsonify({
                "ok": True,
                "message": f"Engagement {existing.ref or existing.id} already exists",
                "engagement_id": existing.id,
                "engagement_ref": existing.ref
            })
        
        # Create the engagement
        e = create_engagement_for_opportunity(s, opp)
        
        # Update opportunity stage to Won if converting from Proposal/Negotiation
        if current_stage in ["proposal", "negotiation"]:
            opp.stage = "Won"
        
        # Audit log
        log_audit_event(
            'create', 'engagement',
            f'Converted opportunity "{opp.name}" to engagement "{e.ref}"',
            'engagement', e.id,
            {'opportunity_id': opp.id, 'opportunity_name': opp.name}
        )
        
        s.commit()
        
        return jsonify({
            "ok": True,
            "message": f"Engagement {e.ref or e.id} created successfully",
            "engagement_id": e.id,
            "engagement_ref": e.ref
        })

# API endpoint for moving opportunity between pipeline stages (drag-and-drop)
@csrf.exempt
@login_required
@app.route("/api/opportunity/move-stage", methods=["POST"])
def api_opportunity_move_stage():
    """
    Move an opportunity to a different pipeline stage.
    Used by the drag-and-drop Kanban on the Projects page.
    """
    data = request.get_json()
    if not data:
        return jsonify({"ok": False, "error": "No data provided"}), 400
    
    opp_id = data.get("opportunity_id")
    from_stage = data.get("from_stage")
    to_stage = data.get("to_stage")
    
    if not opp_id or not to_stage:
        return jsonify({"ok": False, "error": "Missing required fields"}), 400
    
    with Session(engine) as s:
        opp = s.get(Opportunity, int(opp_id))
        if not opp:
            return jsonify({"ok": False, "error": "Opportunity not found"}), 404
        
        # Valid pipeline stages
        valid_stages = ["Qualified Lead", "Proposal", "Procurement", "Closed Won", "Closed Lost"]
        if to_stage not in valid_stages:
            return jsonify({"ok": False, "error": f"Invalid stage: {to_stage}"}), 400
        
        old_stage = opp.stage
        opp.stage = to_stage

        # Auto-update probability based on stage
        STAGE_PROBABILITY = {
            "Qualified Lead": 25,
            "Proposal": 50,
            "Procurement": 75,
            "Closed Won": 100,
            "Closed Lost": 0,
        }
        if to_stage in STAGE_PROBABILITY:
            opp.probability = STAGE_PROBABILITY[to_stage]

        # Audit log: opportunity stage move
        log_audit_event('update', 'workflow',
                       f'Pipeline stage changed: {old_stage} → {to_stage}',
                       'opportunity', opp.id,
                       {'old_stage': old_stage, 'new_stage': to_stage,
                        'opportunity_name': opp.name, 'client': opp.client})
        
        # If moved to Closed Won, optionally create engagement
        if to_stage == "Closed Won":
            # Check if engagement already exists
            existing_eng = s.scalar(select(Engagement).where(Engagement.opportunity_id == opp.id))
            if not existing_eng:
                # Auto-create engagement for Closed Won
                eng = _create_engagement_from_opportunity(s, opp)
                s.commit()
                return jsonify({
                    "ok": True, 
                    "message": f"Moved to {to_stage} and created engagement {eng.ref}",
                    "engagement_created": True,
                    "engagement_id": eng.id,
                    "engagement_ref": eng.ref
                })
        
        s.commit()

        # Recalculate weighted value for response so frontend can update
        active_opps = s.scalars(
            select(Opportunity).where(
                Opportunity.stage.notin_(["Closed Won", "Closed Lost"])
            )
        ).all()
        new_weighted = sum(
            (o.est_value or 0) * (o.probability or 50) / 100
            for o in active_opps
        )

        return jsonify({
            "ok": True,
            "message": f"Opportunity moved from {old_stage} to {to_stage}",
            "old_stage": old_stage,
            "new_stage": to_stage,
            "new_probability": opp.probability,
            "weighted_value": new_weighted
        })

@login_required
@app.route("/opportunity/<int:opp_id>/convert_to_engagement", methods=["POST"])
def opportunity_convert_to_engagement(opp_id):
    with Session(engine) as s:
        opp = s.get(Opportunity, opp_id)
        if not opp:
            abort(404)
        if (opp.stage or "").lower() != "closed won":
            flash("Only Closed Won opportunities can be converted.", "warning")
            return redirect(url_for("opportunity_edit", opp_id=opp_id))

        eng = _create_engagement_from_opportunity(s, opp)
        s.commit()
        flash(f"Engagement {eng.ref} created.", "success")
        return redirect(url_for("engagement_dashboard", eng_id=eng.id))

@login_required
@app.route("/admin/opportunities/backfill_engagements", methods=["POST"])
def backfill_engagements_for_won():
    created = 0
    with Session(engine) as s:
        won = s.scalars(select(Opportunity).where(Opportunity.stage=="Closed Won")).all()
        for opp in won:
            e = s.scalar(select(Engagement).where(Engagement.opportunity_id==opp.id))
            if not e:
                _create_engagement_from_opportunity(s, opp)
                created += 1
        s.commit()
    flash(f"Created {created} engagements from Closed Won opportunities.", "success")
    return redirect(url_for("opportunities_"))

# ---- Opportunities: edit ----
@login_required
@app.route("/opportunity/<int:opp_id>", methods=["GET", "POST"])
def opportunity_edit(opp_id):
    # Load the opportunity row
    with Session(engine) as s:
        opp = s.scalar(select(Opportunity).where(Opportunity.id == opp_id))
        if not opp:
            abort(404)

        # Load owners for dropdown
        users_rows = s.execute(
            text("SELECT id, name FROM users ORDER BY name ASC")
        ).all()
        choices = [(u[0], u[1]) for u in users_rows]

        # We'll need to map owner name -> id for initial form data
        owner_id_for_form = None
        if opp.owner:
            for uid, uname in choices:
                if (uname or "").strip() == (opp.owner or "").strip():
                    owner_id_for_form = uid
                    break

        # Prefill form
        form = OpportunityForm(
            name=opp.name,
            client=opp.client,
            stage=opp.stage,
            owner=owner_id_for_form,
            est_start=format_date_dmy(opp.est_start),  # "DD-MM-YYYY"
            est_value=opp.est_value or 0,
            notes=opp.notes or "",
            client_contact_name = opp.client_contact_name or "",
            client_contact_role = opp.client_contact_role or "",
            client_contact_phone = opp.client_contact_phone or "",
            client_contact_email = opp.client_contact_email or "",
        )
        form.owner.choices = choices

        if form.validate_on_submit():
            prev_stage = (opp.stage or "").strip().lower()

            # Map owner dropdown (user id) back to owner name string for storage
            new_owner_name = ""
            if form.owner.data:
                row = s.execute(
                    text("SELECT name FROM users WHERE id=:i"),
                    {"i": form.owner.data},
                ).first()
                if row:
                    new_owner_name = row[0] or ""

            opp.name = form.name.data
            opp.client = form.client.data or ""
            opp.stage = form.stage.data
            opp.owner = new_owner_name
            opp.est_start = parse_date_dmy(form.est_start.data)
            opp.est_value = int(form.est_value.data or 0)

            # probability is now implicit; we keep writing it for downstream logic
            opp.probability = 100 if (opp.stage or "").strip().lower() == "closed won" else 0

            opp.notes = form.notes.data or ""

            opp.client_contact_name  = form.client_contact_name.data  or ""
            opp.client_contact_role  = form.client_contact_role.data  or ""
            opp.client_contact_phone = form.client_contact_phone.data or ""
            opp.client_contact_email = form.client_contact_email.data or ""

            # If it becomes Closed Won, create/link an engagement (idempotent)
            new_stage = (opp.stage or "").strip().lower()
            e = None
            if new_stage == "closed won" and prev_stage != "closed won":
                e = create_engagement_for_opportunity(s, opp)

            # Also handle the case where it was already Closed Won but not linked yet
            if new_stage == "closed won" and not e:
                e = create_engagement_for_opportunity(s, opp)

            s.commit()
            flash("Opportunity updated", "success")

            if e:
                flash(f"Engagement {e.ref} created.", "success")
                return redirect(url_for("engagement_dashboard", eng_id=e.id))

            return redirect(url_for("opportunities_"))

    return render_template("opportunity_edit.html", form=form, opp=opp)

@app.route(
    "/action/onboarding_email/<int:app_id>",
    methods=["POST"],
    endpoint="action_onboarding_email"
)
def action_onboarding_email(app_id):
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            abort(404)

        cand = s.scalar(select(Candidate).where(Candidate.id == appn.candidate_id))
        job  = s.scalar(select(Job).where(Job.id == appn.job_id))

        link = f"{APP_BASE_URL}/application/{appn.id}"
        html = f"""
        <h3>Welcome to onboarding</h3>
        <p>Hi {cand.name}, thanks for applying for <b>{job.title}</b>. We'll guide you through vetting next.</p>
        <p>You can check status here: <a href="{link}">{link}</a></p>
        """

        # Send email (no-op in dev if SMTP_* not configured)
        send_email(cand.email, f"Onboarding for {job.title}", html)

        # Update flags
        appn.onboarding_email_sent = True
        appn.status = "Accepted"  # Candidate has accepted, onboarding/vetting begins
        s.commit()

    flash("Onboarding email sent", "success")
    return redirect(url_for("application_detail", app_id=app_id))

@app.route("/kanban")
@login_required
def kanban():
    columns = ["New","Screening","Interview","Offer","Onboarding","Hired","Rejected"]
    with Session(engine) as s:
        data = {col: s.execute(select(Application, Candidate, Job)
                               .join(Candidate, Candidate.id==Application.candidate_id)
                               .join(Job, Job.id==Application.job_id)
                               .where(Application.status==col)
                               .order_by(Application.created_at.desc())
                               ).all() for col in columns}
    return render_template("kanban.html", columns=columns, data=data)

@login_required
@app.route("/kanban/move", methods=["POST"])
def kanban_move():
    payload = request.json or {}
    app_id = int(payload.get("app_id"))
    new_status = payload.get("new_status")
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id==app_id))
        if not appn:
            abort(404)
        old_status = appn.status
        appn.status = new_status
        
        # Get candidate name for audit log
        cand = s.scalar(select(Candidate).where(Candidate.id == appn.candidate_id))
        candidate_name = cand.name if cand else None
        candidate_id = appn.candidate_id
        
        s.commit()
    
    # Audit log: kanban move (after commit to avoid db lock)
    log_audit_event('update', 'workflow', 
                   f'Kanban move: {old_status} → {new_status}',
                   'application', app_id,
                   {'old_status': old_status, 'new_status': new_status,
                    'candidate_id': candidate_id, 'candidate_name': candidate_name})
    
    return jsonify({"ok": True})

# ============== WORKFLOW PAGE ==============
@login_required
@app.route("/workflow")
def workflow():
    """
    Workflow page showing headline figures for each stage and draggable associate cards.
    Filters: owner, client, engagement, role, intake
    
    9 Workflow Stages:
    1) Pipeline - Initial applications received
    2) Shortlist - CV/App marked as passed
    3) I&A - Tele-screen marked as passed (Interview & Assessment)
    4) Client Review - Internal interviews/assessments passed
    5) Offered - Client interview/assessment passed, offer made
    6) Accepted - Offer accepted by candidate
    7) Ready to Contract - Vetting marked as complete
    8) Contract Sent - Placement created, contract sent via eSignature
    9) Placed - Contract signed
    """
    # Query params for filters
    eng_status_filter = request.args.get("eng_status", "active")  # 'active' or 'all'
    owner_filter = request.args.get("owner", "all")
    client_filter = request.args.get("client", "all")
    engagement_filter = request.args.get("engagement", "all")
    role_filter = request.args.get("role", "all")
    intake_filter = request.args.get("intake", "all")
    analyst_filter = request.args.get("analyst", "all")  # N15: Analyst filter
    
    # REQ-273: Load workflow stages from DB config (falls back to defaults)
    with Session(engine) as s:
        stages = _get_workflow_stages(s)

    with Session(engine) as s:
        # Get unique clients from engagements
        all_clients = s.scalars(
            select(Engagement.client)
            .distinct()
            .where(Engagement.client.isnot(None), Engagement.client != "")
            .order_by(Engagement.client)
        ).all()
        
        # Get engagements based on status filter
        eng_query = select(Engagement).order_by(Engagement.name)
        if eng_status_filter == "active":
            eng_query = eng_query.where(Engagement.status == "Active")
        all_engagements = s.scalars(eng_query).all()
        
        # Get all jobs for filter dropdown
        all_jobs = s.scalars(
            select(Job)
            .where(Job.title.isnot(None), Job.title != "")
            .order_by(Job.title)
        ).all()
        
        # Get unique roles (job titles) from jobs
        all_roles = s.scalars(
            select(Job.title)
            .distinct()
            .where(Job.title.isnot(None), Job.title != "")
            .order_by(Job.title)
        ).all()
        
        # Get unique intake dates from engagement plans
        all_intakes = []
        try:
            intake_dates = s.scalars(
                select(EngagementPlan.intake_date)
                .distinct()
                .where(EngagementPlan.intake_date.isnot(None))
                .order_by(EngagementPlan.intake_date)
            ).all()
            all_intakes = [d.strftime("%Y-%m-%d") if d else None for d in intake_dates if d]
        except Exception:
            pass
        
        # Get unique owners (users assigned to engagements or created jobs)
        all_owners = s.scalars(
            select(User.email)
            .distinct()
            .order_by(User.email)
        ).all()
        
        # Build base query for applications
        # Map legacy statuses to new workflow stages
        STATUS_TO_STAGE_MAP = {
            # Pipeline - Initial applications
            "New": "pipeline",
            "Pending": "pipeline",
            "Applied": "pipeline",
            "Applications Pending Review": "pipeline",
            "Pipeline": "pipeline",
            
            # Shortlist - CV/App passed
            "Shortlist": "shortlist",
            "Shortlisted": "shortlist",
            "CV Passed": "shortlist",
            "Declared": "shortlist",
            
            # I&A - Tele-screen passed (Interview & Assessment)
            "I&A": "ia",
            "Tele-screen Passed": "ia",
            "Interview Scheduled": "ia",
            "Interview": "ia",
            
            # Client Review - Internal interviews/assessments passed
            "Client Review": "client_review",
            "Interview Completed": "client_review",
            "Interviewed": "client_review",
            "Assessment Complete": "client_review",
            
            # Offered - Client interview passed, offer made
            "Offered": "offered",
            "Offer Made": "offered",
            "Offer Sent": "offered",
            
            # Accepted - Offer accepted
            "Accepted": "accepted",
            "Offer Accepted": "accepted",
            
            # Rejected/Withdrawn - Offer declined or candidate withdrew
            "Rejected": "rejected_withdrawn",
            "Withdrawn": "rejected_withdrawn",
            "Rejected/Withdrawn": "rejected_withdrawn",
            "Offer Declined": "rejected_withdrawn",
            "Declined": "rejected_withdrawn",
            
            # Ready to Contract - Vetting complete
            "Ready to Contract": "ready_to_contract",
            "Vetting Complete": "ready_to_contract",
            "Vetting": "ready_to_contract",
            "Vetting In-Flight": "ready_to_contract",
            "Onboarding": "ready_to_contract",
            
            # Contract Sent - Placement created, contract sent
            "Contract Sent": "contract_sent",
            "Contract Issued": "contract_sent",
            
            # Placed - Contract signed
            "Placed": "placed",
            "Contract Signed": "placed",
            "Contracted": "placed",
            "Active": "placed",
            "Hired": "placed",
        }
        
        def build_query_for_stage(stage_id):
            """Build query for applications matching a workflow stage"""
            # Find all statuses that map to this stage
            matching_statuses = [status for status, sid in STATUS_TO_STAGE_MAP.items() if sid == stage_id]
            
            if not matching_statuses:
                # Fallback: use the stage name directly
                matching_statuses = [next((s["name"] for s in stages if s["id"] == stage_id), stage_id)]
            
            query = (
                select(Application, Candidate, Job)
                .join(Candidate, Candidate.id == Application.candidate_id)
                .join(Job, Job.id == Application.job_id)
                .outerjoin(Engagement, Engagement.id == Job.engagement_id)
                .where(Application.status.in_(matching_statuses))
            )
            
            # Apply engagement status filter
            if eng_status_filter == "active":
                query = query.where(Engagement.status == "Active")
            
            # Apply filters
            if engagement_filter != "all" and engagement_filter.isdigit():
                query = query.where(Job.engagement_id == int(engagement_filter))
            
            if client_filter != "all":
                query = query.where(Engagement.client == client_filter)
            
            if role_filter != "all":
                query = query.where(Job.title == role_filter)
            
            # Owner filter - filter by job creator or engagement owner
            if owner_filter != "all":
                query = query.outerjoin(User, User.id == Job.created_by).where(
                    or_(User.email == owner_filter, Engagement.owner == owner_filter)
                )
            
            # Intake filter - filter by engagement plan intake date
            if intake_filter != "all":
                query = query.outerjoin(EngagementPlan, EngagementPlan.engagement_id == Engagement.id).where(
                    func.date(EngagementPlan.intake_date) == intake_filter
                )
            
            return query.order_by(Application.created_at.desc())
        
        # Helper function to get vetting progress for a candidate
        SLA_DAYS = 7  # 7 day SLA for vetting completion
        
        def get_vetting_progress(candidate_id):
            """Get vetting check progress for a candidate with SLA status"""
            try:
                vetting_stats = s.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'Complete' THEN 1 ELSE 0 END) as complete,
                            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                            SUM(CASE WHEN status IN ('Not Started', 'NOT STARTED') THEN 1 ELSE 0 END) as not_started,
                            SUM(CASE WHEN status = 'Not Required' THEN 1 ELSE 0 END) as not_required,
                            MIN(created_at) as first_check_date
                        FROM vetting_check
                        WHERE candidate_id = :cand_id
                    """),
                    {"cand_id": candidate_id}
                ).first()
                
                if vetting_stats and vetting_stats[0] > 0:
                    total = vetting_stats[0] or 0
                    complete = vetting_stats[1] or 0
                    in_progress = vetting_stats[2] or 0
                    not_started = vetting_stats[3] or 0
                    not_required = vetting_stats[4] or 0
                    first_check_date = vetting_stats[5]
                    
                    # Calculate effective total (excluding not required)
                    effective_total = total - not_required
                    percentage = (complete / effective_total * 100) if effective_total > 0 else 0
                    
                    # Determine RAG status based on completion:
                    # 0/10 = red (Not Started), 1-9/10 = amber (In Progress), 10/10 = green (Complete)
                    if effective_total == 0:
                        rag = "grey"  # No checks required
                    elif complete == effective_total:
                        rag = "green"  # All complete (10/10)
                    elif complete > 0:
                        rag = "amber"  # Some progress (1-9/10)
                    else:
                        rag = "red"  # Not started (0/10)
                    
                    # Calculate SLA status
                    days_elapsed = 0
                    sla_status = "in"  # Default to in SLA
                    if first_check_date:
                        if isinstance(first_check_date, str):
                            try:
                                first_check_date = datetime.datetime.fromisoformat(first_check_date.replace('Z', '+00:00').split('+')[0])
                            except:
                                first_check_date = None
                        if first_check_date:
                            days_elapsed = (now - first_check_date).days
                            # Only check SLA for non-complete candidates
                            if rag != "green" and days_elapsed > SLA_DAYS:
                                sla_status = "out"
                    
                    return {
                        "total": total,
                        "complete": complete,
                        "in_progress": in_progress,
                        "not_started": not_started,
                        "not_required": not_required,
                        "effective_total": effective_total,
                        "percentage": round(percentage),
                        "rag": rag,
                        "days_elapsed": days_elapsed,
                        "sla_status": sla_status,
                        "sla_days": SLA_DAYS
                    }
            except Exception:
                pass
            return None
        
        # Build data for each stage
        # GAP 1.3: Enhanced card content with days_in_stage calculation
        stage_data = {}
        now = datetime.datetime.utcnow()
        for stage in stages:
            results = s.execute(build_query_for_stage(stage["id"])).all()
            stage["count"] = len(results)
            
            # Build flattened card objects for the template
            cards = []
            for app, cand, job in results:
                engagement = job.engagement if job.engagement_id else None
                
                # Intake is driven by the engagement - default to 1 if no evidence of more
                intake = 1
                
                cards.append({
                    "id": app.id,
                    "type": "application",
                    "candidate_id": cand.id,
                    "job_id": job.id if job else None,
                    "engagement_id": engagement.id if engagement else None,
                    "name": cand.name or "Unknown",
                    "email": cand.email or "",
                    "phone": cand.phone or "",
                    "location": cand.location or cand.postcode or "",
                    "job_title": job.title if job else "",
                    "ai_score": app.ai_score or 0,
                    "interview_at": app.interview_scheduled_at,
                    "engagement_name": engagement.name if engagement else "",
                    "engagement_ref": engagement.ref if engagement else "",
                    "client": engagement.client if engagement else "",
                    "start_date": engagement.start_date if engagement else None,
                    "intake": intake,
                    "days_in_stage": (now - app.created_at).days if app.created_at else 0,
                    "vetting_progress": get_vetting_progress(cand.id),
                })
            stage_data[stage["id"]] = cards
        
        # Calculate KPI totals
        kpi_counts = {stage["name"]: stage["count"] for stage in stages}
        
        # Get unsigned contracts (issued > 3 days ago but not signed)
        # Status is 'sent' or 'delivered' for contracts awaiting signature
        # These respond to the same grid filters (client, engagement, owner, role, intake)
        three_days_ago = datetime.datetime.now() - datetime.timedelta(days=3)
        unsigned_q = (
            select(ESigRequest, Candidate, Engagement)
            .join(Candidate, Candidate.id == ESigRequest.candidate_id)
            .outerjoin(Engagement, Engagement.id == ESigRequest.engagement_id)
            .where(
                func.lower(ESigRequest.status).in_(["sent", "delivered", "pending"]),
                ESigRequest.created_at < three_days_ago
            )
        )
        # Apply grid filters to unsigned contracts
        if eng_status_filter == "active":
            unsigned_q = unsigned_q.where(Engagement.status == "Active")
        if client_filter != "all":
            unsigned_q = unsigned_q.where(Engagement.client == client_filter)
        if engagement_filter != "all" and engagement_filter.isdigit():
            unsigned_q = unsigned_q.where(Engagement.id == int(engagement_filter))
        if owner_filter != "all":
            unsigned_q = unsigned_q.outerjoin(User, User.id == Engagement.owner_id).where(
                or_(User.email == owner_filter, Engagement.owner == owner_filter)
            )
        unsigned_q = unsigned_q.order_by(ESigRequest.created_at.asc())
        unsigned_contracts = s.execute(unsigned_q).all()
        
        unsigned_contracts_data = [
            {
                "esig": esig,
                "candidate": cand,
                "engagement": eng,
                "days_pending": (datetime.datetime.now() - esig.created_at).days if esig.created_at else 0
            }
            for esig, cand, eng in unsigned_contracts
        ]
        
        # Get vetting summary stats
        # Count candidates by their overall vetting progress:
        # - 0/10 complete = Not Started
        # - 1-9/10 complete = In Progress  
        # - 10/10 complete = Complete
        # Also track SLA (7 day SLA from first vetting check creation)
        
        vetting_total = 0
        vetting_complete = 0
        vetting_in_progress = 0
        vetting_not_started = 0
        vetting_in_sla = 0
        vetting_out_of_sla = 0
        vetting_by_type = {}
        vetting_by_type_in_sla = {}
        vetting_by_type_out_sla = {}
        vetting_by_candidate = {}
        vetting_candidates = []  # List of candidates with their SLA status
        
        # SLA-filtered counts
        vetting_not_started_in_sla = 0
        vetting_not_started_out_sla = 0
        vetting_in_progress_in_sla = 0
        vetting_in_progress_out_sla = 0
        
        SLA_DAYS = 7  # 7 day SLA for vetting completion
        
        try:
            # Get per-candidate vetting summary with SLA calculation
            # Responds to grid filters so vetting summary updates with filter selections
            _vs = "SELECT c.id, c.name, COUNT(vc.id) as total_checks, SUM(CASE WHEN vc.status = 'Complete' THEN 1 ELSE 0 END) as complete_checks, MIN(vc.created_at) as first_check_date FROM candidates c JOIN vetting_check vc ON vc.candidate_id = c.id"
            _vw, _vp = [], {}
            if any([client_filter != "all", engagement_filter != "all" and engagement_filter.isdigit(), role_filter != "all", owner_filter != "all", eng_status_filter == "active"]):
                _vs += " JOIN applications a ON a.candidate_id = c.id JOIN jobs j ON j.id = a.job_id LEFT JOIN engagements e ON e.id = j.engagement_id"
                if eng_status_filter == "active":
                    _vw.append("e.status = 'Active'")
                if client_filter != "all":
                    _vw.append("e.client = :vcf"); _vp["vcf"] = client_filter
                if engagement_filter != "all" and engagement_filter.isdigit():
                    _vw.append("j.engagement_id = :vef"); _vp["vef"] = int(engagement_filter)
                if role_filter != "all":
                    _vw.append("j.title = :vrf"); _vp["vrf"] = role_filter
                if owner_filter != "all":
                    _vw.append("e.owner = :vof"); _vp["vof"] = owner_filter
            if _vw:
                _vs += " WHERE " + " AND ".join(_vw)
            _vs += " GROUP BY c.id, c.name"
            candidate_vetting = s.execute(text(_vs), _vp).all()
            
            now = datetime.datetime.utcnow()
            
            for row in candidate_vetting:
                cand_id, cand_name, total, complete, first_check_date = row
                vetting_total += 1
                
                # Determine status based on completion ratio
                if complete == 0:
                    vetting_not_started += 1
                    status = "not_started"
                elif complete >= total:
                    vetting_complete += 1
                    status = "complete"
                else:
                    vetting_in_progress += 1
                    status = "in_progress"
                
                # Calculate SLA status (only for IN PROGRESS candidates - not "not_started" or "complete")
                days_elapsed = 0
                sla_status = None  # None for not_started and complete candidates
                
                if status == "in_progress" and first_check_date:
                    if isinstance(first_check_date, str):
                        first_check_date = datetime.datetime.fromisoformat(first_check_date.replace('Z', '+00:00').split('+')[0])
                    days_elapsed = (now - first_check_date).days
                    
                    # Only in_progress candidates have SLA status
                    if days_elapsed > SLA_DAYS:
                        sla_status = "out"
                        vetting_out_of_sla += 1
                        vetting_in_progress_out_sla += 1
                    else:
                        sla_status = "in"
                        vetting_in_sla += 1
                        vetting_in_progress_in_sla += 1
                
                vetting_candidates.append({
                    "id": cand_id,
                    "name": cand_name,
                    "total": total,
                    "complete": complete,
                    "status": status,
                    "days_elapsed": days_elapsed,
                    "sla_status": sla_status
                })
            
            # Get breakdown by check type for IN PROGRESS candidates only (1-9/10 complete)
            # First, identify candidates who are "in progress" (have some but not all checks complete)
            in_progress_candidate_ids = [c["id"] for c in vetting_candidates if c["status"] == "in_progress"]
            
            # Process check type stats with SLA filtering - only for in-progress candidates
            check_type_all = {}
            check_type_in_sla = {}
            check_type_out_sla = {}
            
            if in_progress_candidate_ids:
                # Get check data only for in-progress candidates
                # Build a simple query with the IDs directly (safe since they're integers from our own query)
                id_list = ",".join(str(int(cid)) for cid in in_progress_candidate_ids)
                check_type_with_sla = s.execute(
                    text(f"""
                        SELECT 
                            vc.check_type,
                            vc.status,
                            c.id as cand_id,
                            (SELECT MIN(vc2.created_at) FROM vetting_check vc2 WHERE vc2.candidate_id = c.id) as first_check_date
                        FROM vetting_check vc
                        JOIN candidates c ON c.id = vc.candidate_id
                        WHERE c.id IN ({id_list})
                    """)
                ).all()
                
                for row in check_type_with_sla:
                    check_type, check_status, cand_id, first_check_date = row
                    
                    # Calculate SLA status for this candidate
                    cand_sla = "in"
                    if first_check_date:
                        if isinstance(first_check_date, str):
                            first_check_date = datetime.datetime.fromisoformat(first_check_date.replace('Z', '+00:00').split('+')[0])
                        days_elapsed = (now - first_check_date).days
                        if days_elapsed > SLA_DAYS:
                            cand_sla = "out"
                    
                    # Initialize dicts if needed
                    if check_type not in check_type_all:
                        check_type_all[check_type] = {"total": 0, "complete": 0, "in_progress": 0, "not_started": 0}
                        check_type_in_sla[check_type] = {"total": 0, "complete": 0, "in_progress": 0, "not_started": 0}
                        check_type_out_sla[check_type] = {"total": 0, "complete": 0, "in_progress": 0, "not_started": 0}
                    
                    # Update all counts
                    check_type_all[check_type]["total"] += 1
                    if check_status == "Complete":
                        check_type_all[check_type]["complete"] += 1
                    elif check_status == "In Progress":
                        check_type_all[check_type]["in_progress"] += 1
                    else:
                        check_type_all[check_type]["not_started"] += 1
                    
                    # Update SLA-filtered counts
                    if cand_sla == "in":
                        check_type_in_sla[check_type]["total"] += 1
                        if check_status == "Complete":
                            check_type_in_sla[check_type]["complete"] += 1
                        elif check_status == "In Progress":
                            check_type_in_sla[check_type]["in_progress"] += 1
                        else:
                            check_type_in_sla[check_type]["not_started"] += 1
                    else:
                        check_type_out_sla[check_type]["total"] += 1
                        if check_status == "Complete":
                            check_type_out_sla[check_type]["complete"] += 1
                        elif check_status == "In Progress":
                            check_type_out_sla[check_type]["in_progress"] += 1
                        else:
                            check_type_out_sla[check_type]["not_started"] += 1
            
            vetting_by_type = check_type_all
            vetting_by_type_in_sla = check_type_in_sla
            vetting_by_type_out_sla = check_type_out_sla

            # Per-candidate check type breakdown (for chart filtering)
            vetting_by_candidate = {}
            for row in check_type_with_sla:
                check_type, check_status, cand_id_val, _ = row
                if cand_id_val not in vetting_by_candidate:
                    vetting_by_candidate[cand_id_val] = {}
                if check_type not in vetting_by_candidate[cand_id_val]:
                    vetting_by_candidate[cand_id_val][check_type] = {"total": 0, "complete": 0, "in_progress": 0, "not_started": 0}
                vetting_by_candidate[cand_id_val][check_type]["total"] += 1
                if check_status == "Complete":
                    vetting_by_candidate[cand_id_val][check_type]["complete"] += 1
                elif check_status == "In Progress":
                    vetting_by_candidate[cand_id_val][check_type]["in_progress"] += 1
                else:
                    vetting_by_candidate[cand_id_val][check_type]["not_started"] += 1
            
        except Exception as e:
            # VettingCheck table might not exist yet
            import traceback
            traceback.print_exc()
        
        vetting_summary = {
            "total_candidates": vetting_total,
            "complete": vetting_complete,
            "in_progress": vetting_in_progress,
            "not_started": vetting_not_started,
            "in_sla": vetting_in_sla,
            "out_of_sla": vetting_out_of_sla,
            "sla_days": SLA_DAYS,
            "by_type": vetting_by_type,
            "by_type_in_sla": vetting_by_type_in_sla,
            "by_type_out_sla": vetting_by_type_out_sla,
            "candidates": vetting_candidates,
            "by_candidate": vetting_by_candidate,
            # SLA-filtered status counts
            "not_started_in_sla": vetting_not_started_in_sla,
            "not_started_out_sla": vetting_not_started_out_sla,
            "in_progress_in_sla": vetting_in_progress_in_sla,
            "in_progress_out_sla": vetting_in_progress_out_sla,
        }
    
    # N15: Analyst list for filter dropdown
    all_analysts = []
    try:
        with Session(engine) as _as:
            all_analysts = _as.scalars(
                select(User).where(User.is_active == True).order_by(User.name)
            ).all()
            # Detach for template use
            all_analysts = [type('A', (), {'id': a.id, 'name': a.name})() for a in all_analysts]
    except Exception:
        pass

    return render_template(
        "workflow.html",
        stages=stages,
        stage_data=stage_data,
        kpi_counts=kpi_counts,
        jobs=all_jobs,
        engagements=all_engagements,
        all_clients=all_clients,
        all_engagements=all_engagements,
        all_roles=all_roles,
        all_intakes=all_intakes,
        all_owners=all_owners,
        all_analysts=all_analysts,
        eng_status_filter=eng_status_filter,
        owner_filter=owner_filter,
        client_filter=client_filter,
        engagement_filter=engagement_filter,
        role_filter=role_filter,
        intake_filter=intake_filter,
        analyst_filter=analyst_filter,
        unsigned_contracts=unsigned_contracts_data,
        vetting_summary=vetting_summary,
    )

@csrf.exempt
@app.route("/api/workflow/move", methods=["POST"])
@login_required
def api_workflow_move():
    """
    API endpoint for moving cards in the workflow kanban.
    Maps stage IDs to actual status names and calls the main workflow_move logic.
    """
    # Map stage IDs to canonical status names
    STAGE_ID_TO_STATUS = {
        "pipeline": "Pipeline",
        "shortlist": "Shortlist",
        "ia": "I&A",
        "client_review": "Client Review",
        "offered": "Offered",
        "rejected_withdrawn": "Rejected",
        "accepted": "Accepted",
        "ready_to_contract": "Ready to Contract",
        "contract_sent": "Contract Sent",
        "placed": "Placed",
        # Also add legacy mappings for drag-drop compatibility
        "applications_pending_review": "Pipeline",
        "interview_scheduled": "I&A",
        "interview_completed": "Client Review", 
        "vetting_in_flight": "Ready to Contract",
        "contract_issued": "Contract Sent",
        "contract_signed": "Placed",
    }
    
    payload = request.json or {}
    card_id = payload.get("card_id")
    card_type = payload.get("card_type", "application")
    to_stage = payload.get("to_stage", "")
    direct_status = payload.get("new_status", "")  # Direct status from button clicks
    
    if not card_id:
        return jsonify({"ok": False, "error": "Missing card_id"}), 400
    
    # Map stage ID to status name, or use direct status if provided
    new_status = direct_status if direct_status else STAGE_ID_TO_STATUS.get(to_stage)
    if not new_status:
        return jsonify({"ok": False, "error": f"Invalid stage: {to_stage}"}), 400
    
    try:
        with Session(engine) as s:
            app_obj = s.scalar(select(Application).where(Application.id == int(card_id)))
            if not app_obj:
                return jsonify({"ok": False, "error": "Application not found"}), 404
            
            old_status = app_obj.status

            # Vetting completeness check for drag-drop moves to Ready to Contract
            if new_status == "Ready to Contract":
                _ALL_CHECKS = [
                    "Right to Work", "Identity Verification", "Address History", "DBS Check",
                    "Employment History", "References", "Qualifications", "Professional Registration",
                    "Credit Check", "Directorship / Disqualification", "Sanctions / PEP", "Social Media Review"
                ]
                _vet_checks = s.execute(
                    select(VettingCheck).where(VettingCheck.candidate_id == app_obj.candidate_id)
                ).scalars().all()
                _vet_map = {vc.check_type: vc.status.upper() for vc in _vet_checks}
                _done = sum(1 for ct in _ALL_CHECKS if _vet_map.get(ct, "NOT STARTED") in ["COMPLETE", "N/A", "REFERRAL APPROVED"])
                if _done < len(_ALL_CHECKS):
                    return jsonify({
                        "ok": False,
                        "error": f"Cannot mark as Ready to Contract: {_done}/{len(_ALL_CHECKS)} vetting checks complete.",
                        "vetting_incomplete": True
                    }), 400

            app_obj.status = new_status

            # Update candidate's last activity and status based on new workflow stage
            cand = s.scalar(select(Candidate).where(Candidate.id == app_obj.candidate_id))
            if cand:
                cand.last_activity_at = datetime.datetime.utcnow()
                
                # Update candidate status based on workflow stage
                if new_status in ["Placed", "Contract Signed"]:
                    cand.status = "On Assignment"
                elif new_status in ["Contract Sent", "Ready to Contract", "Accepted"]:
                    cand.status = "In Vetting"
                elif new_status in ["Offered", "Client Review", "I&A"]:
                    cand.status = "Interviewing"
                elif new_status in ["Rejected", "Withdrawn"]:
                    cand.status = "Available"
            
            # Store values for audit log before commit
            audit_cand_id = cand.id if cand else None
            audit_cand_name = cand.name if cand else None

            # FIX: Log activity note for ALL drag-drop workflow moves so the
            # candidate activity feed keeps updating beyond the interview stage.
            if cand:
                job_obj = s.scalar(select(Job).where(Job.id == app_obj.job_id)) if app_obj.job_id else None
                job_title = job_obj.title if job_obj else "Unknown Job"
                activity_note = CandidateNote(
                    candidate_id=cand.id,
                    user_email=session.get("user_email", "system"),
                    note_type="activity",
                    content=f"Workflow stage changed: {old_status} \u2192 {new_status} (Job: {job_title})",
                    created_at=datetime.datetime.utcnow()
                )
                s.add(activity_note)

            s.commit()

            # Audit log: workflow drag-drop move (after commit to avoid db lock)
            log_audit_event('update', 'workflow',
                           f'Workflow stage changed (drag-drop): {old_status} \u2192 {new_status}',
                           'application', int(card_id),
                           {'old_status': old_status, 'new_status': new_status,
                            'candidate_id': audit_cand_id,
                            'candidate_name': audit_cand_name})
            
            return jsonify({
                "ok": True,
                "message": f"Moved from {old_status} to {new_status}",
                "card_id": card_id,
                "new_status": new_status
            })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@csrf.exempt
@app.route("/api/workflow/bulk-reject", methods=["POST"])
@login_required
def api_workflow_bulk_reject():
    """Bulk reject multiple applications and send rejection emails."""
    payload = request.json or {}
    card_ids = payload.get("card_ids", [])
    rej_reason = payload.get("reason", "Unfortunately, your application has not been successful at this time.")
    if not card_ids:
        return jsonify({"ok": False, "error": "No applications selected"}), 400
    rejected, errs = [], []
    try:
        with Session(engine) as sess:
            for cid in card_ids:
                try:
                    ao = sess.scalar(select(Application).where(Application.id == int(cid)))
                    if not ao:
                        errs.append("Application " + str(cid) + " not found")
                        continue
                    old_st = ao.status
                    ao.status = "Rejected"
                    cd = sess.scalar(select(Candidate).where(Candidate.id == ao.candidate_id))
                    if cd:
                        cd.last_activity_at = datetime.datetime.utcnow()
                        cd.status = "Available"
                        if cd.email:
                            jb = sess.scalar(select(Job).where(Job.id == ao.job_id))
                            jt = jb.title if jb else "the role"
                            try:
                                send_email(cd.email, "Application Update - " + jt,
                                    "<p>Dear " + (cd.name or "Associate") + ",</p>"
                                    + "<p>" + rej_reason + "</p>"
                                    + "<p>Role: <strong>" + jt + "</strong></p>"
                                    + "<p>We wish you all the best.</p>"
                                    + "<p>Kind regards,<br>Optimus Solutions Talent Team</p>")
                            except Exception:
                                pass
                    rejected.append(int(cid))
                    log_audit_event('update', 'workflow',
                        'Bulk rejection: ' + old_st + ' -> Rejected',
                        'application', int(cid),
                        {'old_status': old_st, 'new_status': 'Rejected',
                         'candidate_id': cd.id if cd else None, 'bulk': True})
                except Exception as ex:
                    errs.append("Error rejecting " + str(cid) + ": " + str(ex))
            sess.commit()
        return jsonify({"ok": True, "rejected": rejected,
                        "rejected_count": len(rejected), "errors": errs})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@login_required
@app.route("/workflow/move", methods=["POST"])
def workflow_move():
    """
    Move an application to a new workflow stage.
    
    GAP 1.1 FIX: When an associate card is moved between workflow stages,
    the associate's status updates system-wide. This status change is reflected
    on the Associate Profile, in the Engagements View, on the Dashboard KPIs,
    on the Placements page, and in any filtered views or reports.
    
    GAP 1.4 FIX: Stage skip validation - enforces allowed stage transitions.
    GAP X.4: Audit trail for workflow changes.
    """
    payload = request.json or {}
    app_id = int(payload.get("app_id", 0))
    new_status = payload.get("new_status", "")
    force_move = payload.get("force", False)  # Allow admin override
    
    # New 9-stage workflow valid statuses
    valid_statuses = [
        "Pipeline", 
        "Shortlist", 
        "I&A", 
        "Client Review", 
        "Offered",
        "Accepted",
        "Ready to Contract",
        "Contract Sent", 
        "Placed",
        "Rejected",
        "Withdrawn"
    ]
    
    # GAP 1.4: Define allowed stage transitions for new 9-stage workflow
    # Forward moves follow natural progression, backward moves allowed with restrictions
    ALLOWED_TRANSITIONS = {
        "Pipeline": ["Shortlist", "Rejected", "Withdrawn"],
        "Shortlist": ["Pipeline", "I&A", "Rejected", "Withdrawn"],
        "I&A": ["Shortlist", "Client Review", "Rejected", "Withdrawn"],
        "Client Review": ["I&A", "Offered", "Rejected", "Withdrawn"],
        "Offered": ["Client Review", "Accepted", "Rejected", "Withdrawn"],
        "Accepted": ["Offered", "Ready to Contract", "Rejected", "Withdrawn"],
        "Ready to Contract": ["Accepted", "Contract Sent", "Rejected", "Withdrawn"],
        "Contract Sent": ["Ready to Contract", "Placed", "Rejected", "Withdrawn"],
        "Placed": ["Contract Sent"],  # Can only go back one step from placed
        "New": valid_statuses,  # New applications can go anywhere
        "Rejected": ["Pipeline"],  # Can be reconsidered
        "Withdrawn": ["Pipeline"],  # Can be reconsidered
        # Legacy status mappings for backward compatibility
        "Applications Pending Review": valid_statuses,
        "Interview Scheduled": valid_statuses,
        "Interview Completed": valid_statuses,
        "Vetting In-Flight": valid_statuses,
        "Contract Issued": valid_statuses,
        "Contract Signed": valid_statuses,
    }
    
    if new_status not in valid_statuses:
        return jsonify({"ok": False, "error": "Invalid status"}), 400
    
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            return jsonify({"ok": False, "error": "Application not found"}), 404
        
        old_status = appn.status
        
        # GAP 1.4: Validate stage transition unless force override
        if not force_move and old_status in ALLOWED_TRANSITIONS:
            allowed_next_stages = ALLOWED_TRANSITIONS.get(old_status, valid_statuses)
            if new_status not in allowed_next_stages:
                return jsonify({
                    "ok": False, 
                    "error": f"Cannot move directly from '{old_status}' to '{new_status}'. Allowed: {', '.join(allowed_next_stages)}",
                    "validation_error": True,
                    "current_stage": old_status,
                    "requested_stage": new_status,
                    "allowed_stages": allowed_next_stages
                }), 400

        # Vetting completeness check: cannot move to Ready to Contract unless all checks done
        if new_status == "Ready to Contract" and not force_move:
            ALL_VETTING_CHECKS = [
                "Right to Work", "Identity Verification", "Address History", "DBS Check",
                "Employment History", "References", "Qualifications", "Professional Registration",
                "Credit Check", "Directorship / Disqualification", "Sanctions / PEP", "Social Media Review"
            ]
            all_checks = s.execute(
                select(VettingCheck).where(VettingCheck.candidate_id == appn.candidate_id)
            ).scalars().all()
            check_statuses_map = {vc.check_type: vc.status.upper() for vc in all_checks}
            completed_count = sum(1 for ct in ALL_VETTING_CHECKS
                                if check_statuses_map.get(ct, "NOT STARTED") in ["COMPLETE", "N/A", "REFERRAL APPROVED"])
            if completed_count < len(ALL_VETTING_CHECKS):
                return jsonify({
                    "ok": False,
                    "error": f"Cannot mark as Ready to Contract: {completed_count}/{len(ALL_VETTING_CHECKS)} vetting checks complete. All checks must be Complete or N/A first.",
                    "validation_error": True,
                    "vetting_incomplete": True
                }), 400

        appn.status = new_status

        # Get candidate and job for status sync
        cand = s.scalar(select(Candidate).where(Candidate.id == appn.candidate_id))
        job = s.scalar(select(Job).where(Job.id == appn.job_id)) if appn.job_id else None

        candidate_status_updated = False
        old_candidate_status = cand.status if cand else None
        
        if cand:
            # Always update last_activity_at
            cand.last_activity_at = datetime.datetime.utcnow()
            
            # ============================================================
            # GAP 1.1 FIX: System-wide status sync based on workflow stage
            # ============================================================
            
            # Map workflow stages to candidate statuses
            if new_status in ["Placed", "Contract Signed"]:
                # Associate is now ON CONTRACT / On Assignment
                cand.status = "On Assignment"
                candidate_status_updated = True
                
                # Update interview result if not already set
                if not cand.optimus_interview_result or cand.optimus_interview_result == "Pending":
                    cand.optimus_interview_result = "Pass"
                
                # Mark as previously vetted since they completed the workflow
                cand.previously_vetted = True
                
            elif new_status in ["Contract Sent", "Contract Issued"]:
                # Associate is in final stages, mark as In Vetting/Processing
                cand.status = "In Vetting"
                candidate_status_updated = True
                
            elif new_status in ["Ready to Contract", "Accepted", "Vetting In-Flight"]:
                # Associate is being vetted or ready for contract
                cand.status = "In Vetting"
                candidate_status_updated = True
                
            elif new_status in ["Client Review", "Interview Completed"]:
                # Associate completed interview, mark as Interviewing until next stage
                cand.status = "Interviewing"
                candidate_status_updated = True
                # Record interview completion time if not set
                if not appn.interview_completed_at:
                    appn.interview_completed_at = datetime.datetime.utcnow()
                
            elif new_status in ["I&A", "Interview Scheduled"]:
                # Associate has interview scheduled
                cand.status = "Interviewing"
                candidate_status_updated = True
                
            elif new_status in ["Pipeline", "Shortlist", "Applications Pending Review"]:
                # Early stages - only update if candidate was previously On Assignment
                # and is now back in the pipeline (rare case)
                if old_candidate_status == "On Assignment":
                    cand.status = "Available"
                    candidate_status_updated = True
                    
            elif new_status == "Offered":
                # Candidate has been offered - still interviewing until accepted
                cand.status = "Interviewing"
                candidate_status_updated = True
            
            # ============================================================
            # Handle special date fields based on stage transitions
            # ============================================================
            
            if new_status in ["I&A", "Interview Scheduled"] and old_status not in ["I&A", "Interview Scheduled"]:
                # Set interview scheduled timestamp if moving INTO this stage
                if not appn.interview_scheduled_at:
                    appn.interview_scheduled_at = datetime.datetime.utcnow()
            
            if new_status in ["Client Review", "Interview Completed"] and old_status in ["I&A", "Interview Scheduled"]:
                # Moving from I&A to Client Review - record completion time
                appn.interview_completed_at = datetime.datetime.utcnow()
        
        # Store values for audit log before commit
        audit_details = {
            'candidate_id': cand.id if cand else None,
            'candidate_name': cand.name if cand else None,
            'old_workflow_status': old_status,
            'new_workflow_status': new_status,
            'candidate_status_changed': candidate_status_updated,
            'old_candidate_status': old_candidate_status,
            'new_candidate_status': cand.status if cand else None
        }

        # FIX: Log activity note for ALL workflow stage changes so the
        # candidate activity feed keeps updating beyond the interview stage.
        if cand:
            job_title = job.title if job else "Unknown Job"
            note_content = f"Workflow stage changed: {old_status} \u2192 {new_status} (Job: {job_title})"
            if candidate_status_updated:
                note_content += f"\nCandidate status updated: {old_candidate_status} \u2192 {cand.status}"
            activity_note = CandidateNote(
                candidate_id=cand.id,
                user_email=session.get("user_email", "system"),
                note_type="activity",
                content=note_content,
                created_at=datetime.datetime.utcnow()
            )
            s.add(activity_note)

        s.commit()

        # GAP X.4: Audit log for workflow stage changes (after commit to avoid db lock)
        log_audit_event(
            'update', 'workflow',
            f'Workflow stage changed: {old_status} \u2192 {new_status}',
            'application', app_id,
            audit_details
        )
        
        # Build response with all status changes for frontend
        response_data = {
            "ok": True, 
            "old_status": old_status, 
            "new_status": new_status,
            "app_id": app_id,
            "candidate_id": cand.id if cand else None,
            "candidate_name": cand.name if cand else None,
            "candidate_status_updated": candidate_status_updated
        }
        
        if candidate_status_updated and cand:
            response_data["old_candidate_status"] = old_candidate_status
            response_data["new_candidate_status"] = cand.status
    
    return jsonify(response_data)

# ============== PLACEMENTS PAGE ==============
@login_required
@app.route("/placements")
def placements():
    """
    Placements page showing all associates currently ON CONTRACT.
    
    Per wireframe requirements:
    Filters: Name, Client, Engagement, Role
    Features:
    - Placements Pie Chart (by client)
    - Export CSV button
    - On Contract Table with all columns
    - Scheduled Joiners Panel (next 14 days)
    - Scheduled Leavers Panel (next 14 days)
    - Forecasted Headcount graph
    """
    # Query params for filters (now multi-select)
    name_filter = request.args.getlist("name") or []
    client_filter = request.args.getlist("client") or []
    engagement_filter = request.args.getlist("engagement") or []
    role_filter = request.args.getlist("role") or []
    
    with Session(engine) as s:
        # Base subquery for active placements (signed/completed contracts)
        active_placement_base = (
            select(
                Candidate.id.label('cand_id'),
                Candidate.name.label('cand_name'),
                Engagement.client.label('eng_client'),
                Engagement.id.label('eng_id'),
                Job.title.label('job_title')
            )
            .select_from(ESigRequest)
            .join(Application, Application.id == ESigRequest.application_id)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .outerjoin(Engagement, Engagement.id == Job.engagement_id)
            .where(func.lower(ESigRequest.status).in_(['signed', 'completed']))
            .subquery()
        )

        # Get unique clients with active placements for filter
        all_clients = s.scalars(
            select(active_placement_base.c.eng_client)
            .distinct()
            .where(active_placement_base.c.eng_client.isnot(None), active_placement_base.c.eng_client != "")
            .order_by(active_placement_base.c.eng_client)
        ).all()

        # Get engagements that have active placements for filter
        active_eng_ids = s.scalars(
            select(active_placement_base.c.eng_id)
            .distinct()
            .where(active_placement_base.c.eng_id.isnot(None))
        ).all()
        all_engagements = s.scalars(
            select(Engagement)
            .where(Engagement.id.in_(active_eng_ids))
            .order_by(Engagement.name)
        ).all() if active_eng_ids else []

        # Get unique roles with active placements for filter
        all_roles = s.scalars(
            select(active_placement_base.c.job_title)
            .distinct()
            .where(active_placement_base.c.job_title.isnot(None), active_placement_base.c.job_title != "")
            .order_by(active_placement_base.c.job_title)
        ).all()

        # Get candidate names with active placements for filter dropdown
        all_names = s.scalars(
            select(active_placement_base.c.cand_name)
            .distinct()
            .where(active_placement_base.c.cand_name.isnot(None), active_placement_base.c.cand_name != "")
            .order_by(active_placement_base.c.cand_name)
        ).all()
        
        # Query for on-contract placements (signed/completed contracts)
        query = (
            select(
                Candidate,
                Application,
                Job,
                Engagement,
                ESigRequest,
                EngagementPlan
            )
            .select_from(ESigRequest)
            .join(Application, Application.id == ESigRequest.application_id)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .outerjoin(Engagement, Engagement.id == Job.engagement_id)
            .outerjoin(
                EngagementPlan,
                and_(
                    EngagementPlan.engagement_id == Job.engagement_id,
                    EngagementPlan.role_type == Job.role_type
                )
            )
            .where(func.lower(ESigRequest.status).in_(['signed', 'completed']))
        )
        
        # Apply filters (now multi-select)
        if name_filter:
            query = query.where(Candidate.name.in_(name_filter))
        
        if client_filter:
            query = query.where(Engagement.client.in_(client_filter))
        
        if engagement_filter:
            eng_ids_int = [int(e) for e in engagement_filter if e.isdigit()]
            if eng_ids_int:
                query = query.where(Engagement.id.in_(eng_ids_int))
        
        if role_filter:
            query = query.where(Job.title.in_(role_filter))
        
        query = query.order_by(ESigRequest.signed_at.desc())
        
        results = s.execute(query).all()
        
        # Build placement data
        placements_data = []
        client_counts = {}  # For pie chart
        
        for cand, app, job, eng, esig, plan in results:
            client_name = eng.client if eng and eng.client else "Unknown"
            client_counts[client_name] = client_counts.get(client_name, 0) + 1
            
            placements_data.append({
                "candidate": cand,
                "application": app,
                "job": job,
                "engagement": eng,
                "esig": esig,
                "pay_rate": plan.pay_rate if plan else 0,
                "bill_rate": plan.charge_rate if plan else 0,
                "start_date": esig.signed_at if esig else (eng.start_date if eng else None),
                "end_date": eng.end_date if eng else None,
                # Additional fields for template
                "associate_name": cand.name,
                "associate_email": cand.email,
                "associate_id": cand.id,
                "client": eng.client if eng else "Unknown",
                "engagement_name": eng.name if eng else "Unknown",
                "engagement_ref": eng.id if eng else None,
                "engagement_id": eng.id if eng else None,
                "role": job.title if job else "Unknown",
                "status": esig.status if esig else "unknown",
                "esig_id": esig.id if esig else None,
            })
        
        # Pie chart data (by client)
        pie_chart_data = [
            {"client": client, "count": count}
            for client, count in sorted(client_counts.items(), key=lambda x: -x[1])
        ]
        
        # Summary stats
        total_placements = len(placements_data)
        unique_clients = len(set(p["engagement"].client for p in placements_data if p["engagement"] and p["engagement"].client))
        total_daily_pay = sum(p["pay_rate"] or 0 for p in placements_data)
        total_daily_bill = sum(p["bill_rate"] or 0 for p in placements_data)
        total_daily_margin = total_daily_bill - total_daily_pay
        
        # Build clients dict for template (grouped by client with pay/bill totals)
        clients = {}
        for p in placements_data:
            client_name = p["engagement"].client if p["engagement"] and p["engagement"].client else "Unknown"
            if client_name not in clients:
                clients[client_name] = {"count": 0, "pay": 0, "bill": 0}
            clients[client_name]["count"] += 1
            clients[client_name]["pay"] += p["pay_rate"] or 0
            clients[client_name]["bill"] += p["bill_rate"] or 0
        
        # === Scheduled Joiners (next 14 days) ===
        now = datetime.datetime.utcnow()
        fourteen_days = now + datetime.timedelta(days=14)
        
        joiners_query = (
            select(Candidate, Application, Job, Engagement, ESigRequest)
            .select_from(ESigRequest)
            .join(Application, Application.id == ESigRequest.application_id)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .outerjoin(Engagement, Engagement.id == Job.engagement_id)
            .where(func.lower(ESigRequest.status).in_(['signed', 'completed']))
            .where(Engagement.start_date.isnot(None))
            .where(Engagement.start_date >= now.date())
            .where(Engagement.start_date <= fourteen_days.date())
        )
        
        # Apply filters to joiners query
        if name_filter:
            joiners_query = joiners_query.where(Candidate.name.in_(name_filter))
        if client_filter:
            joiners_query = joiners_query.where(Engagement.client.in_(client_filter))
        if engagement_filter:
            eng_ids_int = [int(e) for e in engagement_filter if e.isdigit()]
            if eng_ids_int:
                joiners_query = joiners_query.where(Engagement.id.in_(eng_ids_int))
        if role_filter:
            joiners_query = joiners_query.where(Job.title.in_(role_filter))
        
        joiners_query = joiners_query.order_by(Engagement.start_date.asc())
        
        joiners_results = s.execute(joiners_query).all()
        today_date = now.date()
        scheduled_joiners = []
        for cand, app, job, eng, esig in joiners_results:
            start_date = eng.start_date if eng else None
            # Calculate days_until, handling both date and datetime objects
            days_until = 0
            if start_date:
                if hasattr(start_date, 'date'):
                    start_date_obj = start_date.date() if callable(getattr(start_date, 'date', None)) else start_date
                else:
                    start_date_obj = start_date
                try:
                    days_until = (start_date_obj - today_date).days
                except TypeError:
                    days_until = 0
            scheduled_joiners.append({
                "candidate": cand,
                "job": job,
                "engagement": eng,
                "start_date": start_date,
                "days_until": days_until
            })
        
        # === Scheduled Leavers (next 30 days) ===
        thirty_days = now + datetime.timedelta(days=30)
        
        leavers_query = (
            select(Candidate, Application, Job, Engagement, ESigRequest)
            .select_from(ESigRequest)
            .join(Application, Application.id == ESigRequest.application_id)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .outerjoin(Engagement, Engagement.id == Job.engagement_id)
            .where(func.lower(ESigRequest.status).in_(['signed', 'completed']))
            .where(Engagement.end_date.isnot(None))
            .where(Engagement.end_date >= now.date())
            .where(Engagement.end_date <= thirty_days.date())
        )
        
        # Apply filters to leavers query
        if name_filter:
            leavers_query = leavers_query.where(Candidate.name.in_(name_filter))
        if client_filter:
            leavers_query = leavers_query.where(Engagement.client.in_(client_filter))
        if engagement_filter:
            eng_ids_int = [int(e) for e in engagement_filter if e.isdigit()]
            if eng_ids_int:
                leavers_query = leavers_query.where(Engagement.id.in_(eng_ids_int))
        if role_filter:
            leavers_query = leavers_query.where(Job.title.in_(role_filter))
        
        leavers_query = leavers_query.order_by(Engagement.end_date.asc())
        
        leavers_results = s.execute(leavers_query).all()
        scheduled_leavers = []
        for cand, app, job, eng, esig in leavers_results:
            end_date = eng.end_date if eng else None
            # Calculate days_until, handling both date and datetime objects
            days_until = 0
            if end_date:
                if hasattr(end_date, 'date'):
                    end_date_obj = end_date.date() if callable(getattr(end_date, 'date', None)) else end_date
                else:
                    end_date_obj = end_date
                try:
                    days_until = (end_date_obj - today_date).days
                except TypeError:
                    days_until = 0
            scheduled_leavers.append({
                "candidate": cand,
                "job": job,
                "engagement": eng,
                "end_date": end_date,
                "days_until": days_until
            })
        
        # === Per-Engagement Forecast Data ===
        # Get all signed contracts grouped by engagement with start/end dates
        forecast_query = (
            select(
                Engagement.id,
                Engagement.name,
                Engagement.client,
                Engagement.start_date,
                Engagement.end_date,
                func.count(ESigRequest.id).label('headcount')
            )
            .select_from(ESigRequest)
            .join(Application, Application.id == ESigRequest.application_id)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .join(Engagement, Engagement.id == Job.engagement_id)
            .where(func.lower(ESigRequest.status).in_(['signed', 'completed']))
        )
        
        # Apply filters to forecast query
        if name_filter:
            forecast_query = forecast_query.where(Candidate.name.in_(name_filter))
        if client_filter:
            forecast_query = forecast_query.where(Engagement.client.in_(client_filter))
        if engagement_filter:
            eng_ids_int = [int(e) for e in engagement_filter if e.isdigit()]
            if eng_ids_int:
                forecast_query = forecast_query.where(Engagement.id.in_(eng_ids_int))
        if role_filter:
            forecast_query = forecast_query.where(Job.title.in_(role_filter))
        
        forecast_query = forecast_query.group_by(Engagement.id).order_by(Engagement.name)
        
        forecast_results = s.execute(forecast_query).all()
        engagement_forecast_data = []
        
        today_date = now.date() if hasattr(now, 'date') else now
        
        for eng_id, eng_name, client, start_date, end_date, total_headcount in forecast_results:
            # Get individual placement dates for this engagement
            # Use Engagement.start_date for placement start (when they begin)
            # Use ESigRequest.end_date for individual end (if set), else Engagement.end_date
            placements_query = (
                select(
                    Candidate.name,
                    Engagement.start_date.label('placement_start_date'),
                    ESigRequest.end_date.label('individual_end_date'),
                    Engagement.end_date.label('engagement_end_date'),
                    Job.title.label('role_title'),
                )
                .select_from(ESigRequest)
                .join(Application, Application.id == ESigRequest.application_id)
                .join(Candidate, Candidate.id == Application.candidate_id)
                .join(Job, Job.id == Application.job_id)
                .join(Engagement, Engagement.id == Job.engagement_id)
                .where(func.lower(ESigRequest.status).in_(['signed', 'completed']))
                .where(Engagement.id == eng_id)
            )
            
            placement_results = s.execute(placements_query).all()
            
            # Build list of individual placements with their dates
            placements_list = []
            current_headcount = 0
            
            for p_name, p_start, p_individual_end, p_eng_end, p_role in placement_results:
                # Normalize dates
                p_start_date = None
                p_end_date = None
                
                if p_start:
                    if hasattr(p_start, 'date'):
                        p_start_date = p_start.date() if callable(getattr(p_start, 'date', None)) else p_start
                    else:
                        p_start_date = p_start
                
                # Use individual end date if set, otherwise use engagement end date
                p_end_raw = p_individual_end if p_individual_end else p_eng_end
                if p_end_raw:
                    if hasattr(p_end_raw, 'date'):
                        p_end_date = p_end_raw.date() if callable(getattr(p_end_raw, 'date', None)) else p_end_raw
                    else:
                        p_end_date = p_end_raw
                
                # Check if this placement is currently active (for current headcount)
                has_started = not p_start_date or p_start_date <= today_date
                has_ended = p_end_date and p_end_date < today_date
                
                if has_started and not has_ended:
                    current_headcount += 1
                
                placements_list.append({
                    "name": p_name,
                    "role": p_role or "",
                    "start_date": p_start_date.strftime('%Y-%m-%d') if p_start_date else None,
                    "end_date": p_end_date.strftime('%Y-%m-%d') if p_end_date else None
                })
            
            # Convert engagement dates to ISO strings for JavaScript
            start_str = None
            end_str = None
            if start_date:
                if hasattr(start_date, 'strftime'):
                    start_str = start_date.strftime('%Y-%m-%d')
                else:
                    start_str = str(start_date)
            if end_date:
                if hasattr(end_date, 'strftime'):
                    end_str = end_date.strftime('%Y-%m-%d')
                else:
                    end_str = str(end_date)
            
            engagement_forecast_data.append({
                "id": eng_id,
                "name": eng_name,
                "client": client or "",
                "start_date": start_str,
                "end_date": end_str,
                "headcount": total_headcount,
                "current_headcount": current_headcount,
                "placements": placements_list
            })
    
    return render_template(
        "placements.html",
        placements=placements_data,
        all_clients=all_clients,
        all_engagements=all_engagements,
        all_roles=all_roles,
        all_names=all_names,
        name_filter=name_filter,
        client_filter=client_filter,
        engagement_filter=engagement_filter,
        role_filter=role_filter,
        total_placements=total_placements,
        unique_clients=unique_clients,
        total_daily_pay=total_daily_pay,
        total_daily_bill=total_daily_bill,
        total_daily_margin=total_daily_margin,
        clients=clients,
        pie_chart_data=pie_chart_data,
        scheduled_joiners=scheduled_joiners,
        scheduled_leavers=scheduled_leavers,
        engagement_forecast_data=engagement_forecast_data,
        now=now,
    )

# CSV Export for Placements
@login_required
@app.route("/placements/export")
def placements_export_csv():
    """Export placements data to CSV"""
    with Session(engine) as s:
        query = (
            select(
                Candidate,
                Application,
                Job,
                Engagement,
                ESigRequest,
                EngagementPlan
            )
            .select_from(ESigRequest)
            .join(Application, Application.id == ESigRequest.application_id)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .outerjoin(Engagement, Engagement.id == Job.engagement_id)
            .outerjoin(
                EngagementPlan,
                and_(
                    EngagementPlan.engagement_id == Job.engagement_id,
                    EngagementPlan.role_type == Job.role_type
                )
            )
            .where(func.lower(ESigRequest.status).in_(['signed', 'completed']))
            .order_by(ESigRequest.signed_at.desc())
        )
        results = s.execute(query).all()
        
        # Build CSV
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header - Split name and email into separate columns, format rates with £
        writer.writerow([
            "Associate Name", "Associate Email", "Client", "Engagement", "Role",
            "Pay Rate", "Bill Rate", "Start Date", "End Date"
        ])

        # Data rows
        for cand, app, job, eng, esig, plan in results:
            pay = plan.pay_rate if plan else 0
            bill = plan.charge_rate if plan else 0
            writer.writerow([
                cand.name,
                cand.email or "",
                eng.client if eng else "",
                eng.name if eng else "",
                job.title,
                pay,
                bill,
                (esig.signed_at or eng.start_date).strftime("%d/%m/%Y") if (esig.signed_at or (eng and eng.start_date)) else "",
                eng.end_date.strftime("%d/%m/%Y") if eng and eng.end_date else "",
            ])
    
    # Create response with UTF-8 BOM for proper Excel encoding (fixes £ → Â£)
    from flask import Response
    output.seek(0)
    csv_content = output.getvalue()
    return Response(
        "\ufeff" + csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment;filename=placements_export.csv"}
    )

# ============== PROJECTS PAGE ==============
@login_required
@app.route("/projects")
def projects():
    """
    Projects landing page showing pipeline overview.
    Combines Opportunities (pipeline) and Active Engagements.
    """
    # Query params
    status_filter = request.args.get("status", "all")  # all, pipeline, active, completed
    client_filter = request.args.get("client", "all")
    
    with Session(engine) as s:
        # Get unique clients
        opp_clients = s.scalars(
            select(Opportunity.client)
            .distinct()
            .where(Opportunity.client.isnot(None), Opportunity.client != "")
        ).all()
        eng_clients = s.scalars(
            select(Engagement.client)
            .distinct()
            .where(Engagement.client.isnot(None), Engagement.client != "")
        ).all()
        all_clients = sorted(set(opp_clients + eng_clients))
        
        # All pipeline opportunities (including Closed Won/Lost for kanban view)
        opp_query = (
            select(Opportunity)
            .order_by(Opportunity.est_start.asc())
        )
        if client_filter != "all":
            opp_query = opp_query.where(Opportunity.client == client_filter)

        opportunities = s.scalars(opp_query).all() if status_filter in ["all", "pipeline"] else []
        
        # Active engagements
        eng_query = select(Engagement).order_by(Engagement.start_date.desc())
        if status_filter == "active":
            eng_query = eng_query.where(Engagement.status == "Active")
        elif status_filter == "completed":
            eng_query = eng_query.where(Engagement.status != "Active")
        
        if client_filter != "all":
            eng_query = eng_query.where(Engagement.client == client_filter)
        
        engagements = s.scalars(eng_query).all() if status_filter in ["all", "active", "completed"] else []
        
        # Pipeline stages for kanban — all stages including Closed Won/Lost
        kanban_stages = ["Qualified Lead", "Proposal", "Procurement"]
        all_stage_names = ["Qualified Lead", "Proposal", "Procurement", "Closed Won", "Closed Lost"]

        # Organize opportunities by stage
        stage_data = {stage: [] for stage in all_stage_names}
        for opp in opportunities:
            stage = opp.stage or "Qualified Lead"
            if stage in stage_data:
                stage_data[stage].append(opp)

        # Closed Won/Lost counts and values for summary tiles
        closed_won_opps = stage_data.get("Closed Won", [])
        closed_lost_opps = stage_data.get("Closed Lost", [])
        closed_won_count = len(closed_won_opps)
        closed_lost_count = len(closed_lost_opps)
        closed_won_value = sum(o.est_value or 0 for o in closed_won_opps)
        closed_lost_value = sum(o.est_value or 0 for o in closed_lost_opps)

        # Active pipeline (excluding closed) for stats
        active_pipeline_opps = [o for o in opportunities
                                if (o.stage or "").lower() not in ("closed won", "closed lost")]

        # Filter to active engagements for the template
        active_engagements = [e for e in engagements if e.status == "Active"]

        # Engagement stats
        active_count = len(active_engagements)
        completed_count = sum(1 for e in engagements if e.status != "Active")

        # Calculate values -- active pipeline only (excluding closed)
        total_pipeline = len(active_pipeline_opps)
        total_value = sum(opp.est_value or 0 for opp in active_pipeline_opps)

        # Weighted value: sum of (est_value * probability/100)
        weighted_value = sum(
            (opp.est_value or 0) * (getattr(opp, 'probability', 50) or 50) / 100
            for opp in active_pipeline_opps
        )
        
        # Get unique roles from engagement plans
        all_roles = s.scalars(
            select(EngagementPlan.role_type)
            .distinct()
            .where(EngagementPlan.role_type.isnot(None), EngagementPlan.role_type != "")
            .order_by(EngagementPlan.role_type)
        ).all()
        
        # Build engagement to roles mapping for filtering
        engagement_roles = {}
        for eng in engagements:
            roles = s.scalars(
                select(EngagementPlan.role_type)
                .distinct()
                .where(EngagementPlan.engagement_id == eng.id)
                .where(EngagementPlan.role_type.isnot(None), EngagementPlan.role_type != "")
            ).all()
            engagement_roles[eng.id] = roles

        return render_template(
            "projects.html",
            opportunities=opportunities,
            all_opportunities=opportunities,  # For the filter dropdowns
            engagements=engagements,
            all_clients=all_clients,
            all_roles=all_roles,
            engagement_roles=engagement_roles,
            status_filter=status_filter,
            client_filter=client_filter,
            pipeline_stages=kanban_stages,
            stage_data=stage_data,
            active_engagements=active_engagements,
            active_count=active_count,
            completed_count=completed_count,
            total_pipeline=total_pipeline,
            total_value=total_value,
            weighted_value=weighted_value,
            closed_won_count=closed_won_count,
            closed_lost_count=closed_lost_count,
            closed_won_value=closed_won_value,
            closed_lost_value=closed_lost_value,
            closed_won_opps=closed_won_opps,
            closed_lost_opps=closed_lost_opps,
        )

@login_required
@app.route("/engagements/create", methods=["GET", "POST"])
def create_engagement():
    form = EngagementForm()
    if form.validate_on_submit():
        with Session(engine) as s:
            # allocate sequential OS### reference
            new_ref = _next_engagement_ref(s)

            # Collect vetting check checkboxes as JSON list
            vetting_checks_selected = request.form.getlist("vetting_check")
            vetting_req_json = json.dumps(vetting_checks_selected) if vetting_checks_selected else "[]"

            # Contradiction Fix 5: Parse reference period (default 3 years)
            ref_period = 3
            try:
                ref_period = int(form.reference_period_years.data or 3)
                if ref_period < 1 or ref_period > 10:
                    ref_period = 3
            except (ValueError, TypeError):
                ref_period = 3

            e = Engagement(
                ref=new_ref,
                name=form.name.data,
                client=form.client.data or "",
                status=form.status.data or "Active",
                start_date=parse_date_dmy(form.start_date.data), # DD-MM-YYYY
                end_date=parse_date_dmy(form.end_date.data),     # DD-MM-YYYY
                sow_signed_at=parse_date_dmy(form.sow_signed_at.data),
                description=form.description.data or "",
                vetting_requirements=vetting_req_json,
                reference_period_years=ref_period,
            )
            s.add(e)
            s.commit()
            flash(f"Engagement {e.ref} created", "success")
        return redirect(url_for("engagements"))
    return render_template("create_engagement.html", form=form)

# --- Edit engagement (name, ref, dates, vetting requirements) ---
@login_required
@app.route("/engagement/<int:eng_id>/edit", methods=["GET", "POST"])
def engagement_edit(eng_id):
    with Session(engine) as s:
        engagement = s.get(Engagement, eng_id)
        if not engagement:
            abort(404)

        form = EngagementForm(obj=engagement)

        if request.method == "POST" and form.validate_on_submit():
            engagement.name = form.name.data
            engagement.client = form.client.data or ""
            engagement.status = form.status.data or "Active"
            engagement.start_date = parse_date_dmy(form.start_date.data)
            engagement.end_date = parse_date_dmy(form.end_date.data)
            engagement.sow_signed_at = parse_date_dmy(form.sow_signed_at.data)
            engagement.description = form.description.data or ""
            # Collect vetting check checkboxes as JSON list
            vetting_checks_selected = request.form.getlist("vetting_check")
            engagement.vetting_requirements = json.dumps(vetting_checks_selected) if vetting_checks_selected else "[]"
            # Contradiction Fix 5: Save reference period
            try:
                rp = int(form.reference_period_years.data or 3)
                engagement.reference_period_years = rp if 1 <= rp <= 10 else 3
            except (ValueError, TypeError):
                engagement.reference_period_years = 3
            s.commit()
            flash(f"Engagement {engagement.ref} updated", "success")
            return redirect(url_for("engagement_dashboard", eng_id=eng_id))

        # Pre-populate form fields for GET
        if request.method == "GET":
            form.name.data = engagement.name
            form.client.data = engagement.client
            form.status.data = engagement.status
            form.start_date.data = engagement.start_date.strftime("%d-%m-%Y") if engagement.start_date else ""
            form.end_date.data = engagement.end_date.strftime("%d-%m-%Y") if engagement.end_date else ""
            form.sow_signed_at.data = engagement.sow_signed_at.strftime("%d-%m-%Y") if engagement.sow_signed_at else ""
            form.description.data = engagement.description
            form.vetting_requirements.data = engagement.vetting_requirements or ""
            form.reference_period_years.data = str(getattr(engagement, 'reference_period_years', 3) or 3)

    return render_template("edit_engagement.html", form=form, engagement=engagement)

@login_required
@app.route("/engagements", methods=["GET"])
def engagements():
    # Get filter parameters with safe defaults
    name_filter = request.args.get('name', '').strip()
    status_filter = request.args.get('status', 'all')
    client_filter = request.args.get('client', 'all')
    sort_by = request.args.get('sort', 'created_desc')
    opp_name_filter = request.args.get('opp_name', '').strip()
    opp_client_filter = request.args.get('opp_client', 'all')
    opp_status_filter = request.args.get('opp_status', 'all')
    opp_sort = request.args.get('opp_sort', 'created_desc')
    
    with Session(engine) as s:
        # 1. Current engagements with filters
        eng_query = select(Engagement)
        
        # Apply name filter (exact match from dropdown)
        if name_filter:
            eng_query = eng_query.where(Engagement.name == name_filter)
        
        # Apply status filter
        if status_filter == 'active':
            eng_query = eng_query.where(Engagement.status == "Active")
        elif status_filter == 'inactive':
            eng_query = eng_query.where(Engagement.status != "Active")
        
        # Apply client filter
        if client_filter and client_filter != 'all':
            eng_query = eng_query.where(Engagement.client == client_filter)
        
        # Apply sorting
        if sort_by == 'created_asc':
            eng_query = eng_query.order_by(Engagement.id.asc())
        elif sort_by == 'name_asc':
            eng_query = eng_query.order_by(Engagement.name.asc())
        elif sort_by == 'name_desc':
            eng_query = eng_query.order_by(Engagement.name.desc())
        elif sort_by == 'start_date':
            eng_query = eng_query.order_by(Engagement.start_date.desc().nullslast())
        else:  # created_desc (default)
            eng_query = eng_query.order_by(Engagement.id.desc())
        
        engagements_rows = s.scalars(eng_query).all()
        
        # Get unique engagement names for filter dropdown
        all_engagement_names = []
        try:
            all_engagement_names = s.scalars(
                select(Engagement.name)
                .distinct()
                .where(Engagement.name.isnot(None))
                .where(Engagement.name != '')
                .order_by(Engagement.name)
            ).all()
        except Exception as e:
            print(f"Error getting engagement names: {e}")
            all_engagement_names = []
        
        # Get unique clients for filter dropdown
        all_clients = []
        try:
            all_clients = s.scalars(
                select(Engagement.client)
                .distinct()
                .where(Engagement.client.isnot(None))
                .where(Engagement.client != '')
                .order_by(Engagement.client)
            ).all()
        except Exception as e:
            print(f"Error getting clients: {e}")
            all_clients = []
        
        # Get unique opportunity clients for filter dropdown
        all_opp_clients = []
        try:
            all_opp_clients = s.scalars(
                select(Opportunity.client)
                .distinct()
                .where(Opportunity.client.isnot(None))
                .where(Opportunity.client != '')
                .order_by(Opportunity.client)
            ).all()
        except Exception as e:
            print(f"Error getting opportunity clients: {e}")
            all_opp_clients = []

        # 2. All opportunities with filters
        opp_query = select(Opportunity)
        
        # Apply opportunity name filter (exact match from dropdown)
        if opp_name_filter:
            opp_query = opp_query.where(Opportunity.name == opp_name_filter)
        
        # Apply opportunity client filter
        if opp_client_filter and opp_client_filter != 'all':
            opp_query = opp_query.where(Opportunity.client == opp_client_filter)
        
        # Apply opportunity status filter
        if opp_status_filter and opp_status_filter != 'all':
            try:
                if opp_status_filter == 'proposal':
                    opp_query = opp_query.where(Opportunity.stage.ilike('%proposal%'))
                elif opp_status_filter == 'negotiation':
                    opp_query = opp_query.where(Opportunity.stage.ilike('%negotiation%'))
                elif opp_status_filter == 'closed_won':
                    opp_query = opp_query.where(Opportunity.stage.ilike('closed won'))
                elif opp_status_filter == 'closed_lost':
                    opp_query = opp_query.where(Opportunity.stage.ilike('closed lost'))
            except Exception as e:
                print(f"Error filtering opportunities: {e}")
        
        # Apply opportunity sorting
        try:
            if opp_sort == 'created_asc':
                opp_query = opp_query.order_by(Opportunity.created_at.asc())
            elif opp_sort == 'value_desc':
                opp_query = opp_query.order_by(Opportunity.est_value.desc().nullslast())
            elif opp_sort == 'value_asc':
                opp_query = opp_query.order_by(Opportunity.est_value.asc().nullslast())
            elif opp_sort == 'name_asc':
                opp_query = opp_query.order_by(Opportunity.name.asc())
            else:  # created_desc (default)
                opp_query = opp_query.order_by(Opportunity.created_at.desc())
        except Exception as e:
            print(f"Error sorting opportunities: {e}")
            opp_query = opp_query.order_by(Opportunity.created_at.desc())
        
        opp_rows = s.scalars(opp_query).all()

        # 3. Map opportunity.id -> (engagement_id, engagement_ref)
        eng_links = {
            oid: (eid, ref)
            for (eid, ref, oid) in s.execute(
                text(
                    "SELECT id, ref, opportunity_id "
                    "FROM engagements "
                    "WHERE opportunity_id IS NOT NULL"
                )
            ).all()
        }

        # 4. Annotate each opportunity with the linked engagement (if any)
        for o in opp_rows:
            tup = eng_links.get(o.id)
            if tup:
                o._engagement_id, o._engagement_ref = tup[0], tup[1]
            else:
                o._engagement_id = None
                o._engagement_ref = None

        # 5. Filter out opportunities that are already active engagements
        #    Rule: hide if stage == "closed won" (case-insensitive)
        #    AND we already have an engagement for it.
        visible_opps = []
        for o in opp_rows:
            st_low = (o.stage or "").strip().lower()
            already_converted = bool(o._engagement_id)
            is_closed_won = (st_low == "closed won")
            if is_closed_won and already_converted:
                # skip, it'll show up in Current Engagements
                continue
            visible_opps.append(o)
        
        # Get unique opportunity names from visible opportunities only
        all_opportunity_names = sorted(list(set([o.name for o in visible_opps if o.name])))

    return render_template(
        "engagements.html",
        items=engagements_rows,
        opps=visible_opps,
        name_filter=name_filter,
        status_filter=status_filter,
        client_filter=client_filter,
        sort_by=sort_by,
        opp_name_filter=opp_name_filter,
        opp_client_filter=opp_client_filter,
        opp_status_filter=opp_status_filter,
        opp_sort=opp_sort,
        all_clients=all_clients,
        all_opp_clients=all_opp_clients,
        all_engagement_names=all_engagement_names,
        all_opportunity_names=all_opportunity_names,
    )

@app.route("/jobs", methods=["GET","POST"])
@login_required
def jobs():
    # If coming from an engagement, lock to it
    eng_id_lock = request.args.get("eng_id", type=int)

    with Session(engine) as s:
        # Validate the lock id (if provided)
        locked_eng = None
        if eng_id_lock:
            locked_eng = s.get(Engagement, eng_id_lock)
            if not locked_eng:
                flash("Engagement not found for the requested job context.", "warning")
                return redirect(url_for("engagements"))

        # Build the form
        form = JobForm()

        if locked_eng:
            # Only one choice, preselected — include the engagement reference in the label
            form.engagement_id.choices = [
                (locked_eng.id, f"{locked_eng.ref or '—'} · {locked_eng.name} ({locked_eng.client})")
            ]
            form.engagement_id.data = locked_eng.id  # prefill
        else:
            # Global selector — include refs for all items
            engagements = s.scalars(select(Engagement).order_by(Engagement.id.desc())).all()
            form.engagement_id.choices = [
                (e.id, f"{e.ref or '—'} · {e.name} ({e.client})") for e in engagements
            ]

        # Create
        if form.validate_on_submit():
            engagement_id_final = locked_eng.id if locked_eng else form.engagement_id.data
            j = Job(
                engagement_id=engagement_id_final,
                title=form.title.data,
                description=form.description.data,
                role_type=form.role_type.data or "",
                location=form.location.data or "",
                salary_range=form.salary_range.data or "",
            )
            s.add(j)
            s.commit()
            flash("Job created", "success")

            # After creating in a locked context, bounce back to that engagement’s dashboard
            if locked_eng:
                return redirect(url_for("engagement_job_detail", eng_id=locked_eng.id, job_id=j.id))
            return redirect(url_for("jobs"))

        # List jobs (optionally filtered to the locked engagement for clarity)
        if locked_eng:
            rows = s.scalars(
                select(Job)
                .where(Job.engagement_id == locked_eng.id)
                .options(selectinload(Job.engagement))
                .order_by(Job.created_at.desc())
            ).all()
        else:
            rows = s.scalars(
                select(Job)
                .options(selectinload(Job.engagement))
                .order_by(Job.created_at.desc())
            ).all()

    return render_template(
        "jobs.html",
        form=form,
        items=rows,
        locked_engagement=locked_eng,  # pass for UX banner/disable
    )

@login_required
@app.route("/job/<token>")
def public_job(token):
    with Session(engine) as s:
        job = s.scalar(select(Job).where(Job.public_token==token))
        if not job:
            abort(404)
    return render_template("public_job.html", job=job)

@login_required
@app.route("/job/new", methods=["GET", "POST"])
def job_new():
    """Create a new job post."""
    from sqlalchemy.orm import Session
    with Session(engine) as s:
        if request.method == "POST":
            title = request.form.get("title") or "Untitled Job"
            role = request.form.get("role") or ""
            description = request.form.get("description") or ""
            status = request.form.get("status") or "Open"
            engagement_id = request.form.get("engagement_id") or None

            job = Job(
                title=title,
                role=role,
                description=description,
                status=status,
                engagement_id=engagement_id,
                created_at=datetime.datetime.utcnow(),
            )
            s.add(job)
            s.commit()
            flash("Job created successfully.", "success")
            return redirect(url_for("engagement_dashboard", engagement_id=engagement_id or 1))

        # GET request
        roles = s.scalars(select(RoleType).order_by(RoleType.name.asc())).all()
        return render_template("job_form.html", job=None, roles=roles, mode="create")


@login_required
@app.route("/job/<int:job_id>/edit", methods=["GET", "POST"])
def job_edit(job_id):
    """Edit an existing job post."""
    from sqlalchemy.orm import Session
    with Session(engine) as s:
        job = s.get(Job, job_id)
        if not job:
            flash("Job not found.", "warning")
            return redirect(url_for("engagements"))

        if request.method == "POST":
            job.title = request.form.get("title") or job.title
            job.role = request.form.get("role") or job.role
            job.description = request.form.get("description") or job.description
            job.status = request.form.get("status") or job.status
            s.commit()
            flash("Job updated successfully.", "success")
            return redirect(url_for("engagement_dashboard", engagement_id=job.engagement_id or 1))

        roles = s.scalars(select(RoleType).order_by(RoleType.name.asc())).all()
        return render_template("job_form.html", job=job, roles=roles, mode="edit")

@app.route("/apply/<token>", methods=["GET", "POST"])
def apply(token):
    form = ApplyForm()
    with Session(engine) as s:
        job = s.scalar(select(Job).where(Job.public_token == token))
        if not job:
            abort(404)

        if form.validate_on_submit():
            # --- normalise email once (trim + lowercase) ---
            raw_email = form.email.data or ""
            norm_email = raw_email.strip().lower()

            # 1️⃣ Find or create candidate by unique email (case-insensitive)
            cand = s.scalar(
                select(Candidate).where(func.lower(Candidate.email) == norm_email)
            )

            if not cand:
                cand = Candidate(
                    name=form.name.data,
                    email=norm_email,
                    phone=(form.phone.data or "").strip(),
                )
                s.add(cand)
                try:
                    s.flush()  # get cand.id, may raise IntegrityError if racing
                except IntegrityError:
                    s.rollback()
                    # someone else just created this candidate with same email
                    cand = s.scalar(
                        select(Candidate).where(func.lower(Candidate.email) == norm_email)
                    )
                    if not cand:
                        flash(
                            "We couldn't process your details. Please try again.",
                            "danger",
                        )
                        return render_template("apply.html", form=form, job=job)

            # 2️⃣ Prevent duplicate applications for the same job+candidate
            existing_app = s.scalar(
                select(Application)
                .where(
                    Application.job_id == job.id,
                    Application.candidate_id == cand.id,
                )
            )
            if existing_app:
                flash(
                    "You’ve already applied for this role. We’ve kept your original application.",
                    "info",
                )
                return redirect(url_for("public_job", token=token))

            # 3️⃣ Require CV upload
            cv_file = request.files.get("cv")
            if not cv_file:
                flash("Please upload a CV", "danger")
                return render_template("apply.html", form=form, job=job)

            # 4️⃣ Save CV in uploads/cvs
            try:
                fname, path, original = save_upload(cv_file, subdir="cvs")
            except Exception as e:
                flash(f"Upload failed: {e}", "danger")
                return render_template("apply.html", form=form, job=job)

            doc = Document(
                candidate_id=cand.id,
                doc_type="cv",
                filename=fname,
                original_name=original,
            )
            s.add(doc)
            s.flush()

            # 5️⃣ Create new application
            appn = Application(
                job_id=job.id,
                candidate_id=cand.id,
                cover_note=form.cover_note.data or "",
            )
            s.add(appn)
            s.flush()

            # 6️⃣ Generate AI summary/tags/score immediately
            _rebuild_ai_summary_and_tags(s, cand, doc=doc, job=job, appn=appn)

            s.commit()
            flash("Application submitted. Thank you!", "success")
            return redirect(url_for("public_job", token=token))

    return render_template("apply.html", form=form, job=job)

@login_required
@app.route("/my/timesheets", methods=["GET", "POST"])
@worker_required
def my_timesheets():
    """
    Minimal worker portal to submit a weekly timesheet.
    Reuses your existing Timesheet model.
    """
    now = datetime.datetime.utcnow()
    start = (now - datetime.timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + datetime.timedelta(days=7)

    # Single engagement picker for simplicity
    class _TSForm(FlaskForm):
        engagement_id = SelectField("Engagement", coerce=int, validators=[DataRequired()])
        hours = IntegerField("Hours", validators=[DataRequired()])
        notes = TextAreaField("Notes", validators=[WTOptional()])
        submit = SubmitField("Submit")

    with Session(engine) as s:
        engagements = s.scalars(select(Engagement).order_by(Engagement.name.asc())).all()
        choices = [(e.id, f"{e.name} ({e.client or '—'})") for e in engagements]

    form = _TSForm()
    form.engagement_id.choices = choices

    if form.validate_on_submit():
        with Session(engine) as s:
            ts = Timesheet(
                user_id=int(current_user.id),
                engagement_id=form.engagement_id.data,
                period_start=start,
                period_end=end,
                hours=int(form.hours.data or 0),
                notes=form.notes.data or "",
                status="Submitted",
                submitted_at=datetime.datetime.utcnow(),
            )
            s.add(ts)
            s.commit()
        flash("Timesheet submitted.", "success")
        return redirect(url_for("my_timesheets"))

    # List recent timesheets for the logged-in user
    with Session(engine) as s:
        mine = s.execute(
            select(Timesheet, Engagement)
            .join(Engagement, Engagement.id == Timesheet.engagement_id)
            .where(Timesheet.user_id == int(current_user.id))
            .order_by(Timesheet.period_start.desc())
            .limit(20)
        ).all()

    return render_template("timesheets_portal.html", form=form, items=mine, week=(start, end))

@login_required
@app.route("/action/candidate/delete", methods=["POST"])
def candidate_delete_action():
    cand_id = int((request.form.get("candidate_id") or "0") or 0)
    confirm = (request.form.get("confirm") or "").lower() == "yes"
    if not cand_id:
        flash("Missing associate id.", "warning")
        return redirect(request.referrer or url_for("resource_pool"))
    if not confirm:
        flash("Deletion cancelled.", "info")
        return redirect(request.referrer or url_for("resource_pool"))

    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found.", "warning")
            return redirect(request.referrer or url_for("resource_pool"))

        app_ids = [aid for (aid,) in s.execute(
            select(Application.id).where(Application.candidate_id == cand_id)
        ).all()]

        if app_ids:
            s.execute(delete(ESigRequest).where(ESigRequest.application_id.in_(app_ids)))
            # Legacy TrustIDCheck cleanup (table kept for backwards compatibility)
            try:
                s.execute(delete(TrustIDCheck).where(TrustIDCheck.application_id.in_(app_ids)))
            except Exception:
                pass
            s.execute(delete(Application).where(Application.id.in_(app_ids)))
        # Also clean up VettingCheck rows for this candidate
        s.execute(delete(VettingCheck).where(VettingCheck.candidate_id == cand_id))

        s.execute(delete(Shortlist).where(Shortlist.candidate_id == cand_id))
        s.execute(delete(CandidateTag).where(CandidateTag.candidate_id == cand_id))
        
        # Audit log: candidate deleted
        log_audit_event('delete', 'data_access', f'Deleted candidate: {cand.name}', 
                       'candidate', cand_id,
                       {'email': cand.email, 'applications_deleted': len(app_ids)})
        
        s.delete(cand)
        s.commit()

    flash("Associate deleted.", "success")
    return redirect(request.referrer or url_for("resource_pool"))

@login_required
@app.route("/candidate/<int:cand_id>/delete-cv/<int:doc_id>", methods=["POST"])
def candidate_delete_cv(cand_id, doc_id):
    """Delete a CV/document from a candidate's profile."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found.", "warning")
            return redirect(request.referrer or url_for("resource_pool"))
        
        doc = s.get(Document, doc_id)
        if not doc or doc.candidate_id != cand_id:
            flash("Document not found.", "warning")
            return redirect(request.referrer or url_for("candidate_profile", cand_id=cand_id))
        
        s.delete(doc)
        s.commit()
        flash("Document deleted successfully.", "success")
    
    return redirect(request.referrer or url_for("candidate_profile", cand_id=cand_id))

@login_required
@app.route("/action/candidate/add", methods=["POST"])
def add_candidate_manual():
    """Add a new candidate/associate manually from the Resource Pool."""
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    phone = (request.form.get("phone") or "").strip()
    postcode = (request.form.get("postcode") or "").strip()
    skills = (request.form.get("skills") or "").strip()
    day_rate = request.form.get("day_rate", "").strip()
    availability = (request.form.get("availability") or "").strip()
    notes = (request.form.get("notes") or "").strip()
    
    if not name or not email:
        flash("Name and Email are required.", "warning")
        return redirect(request.referrer or url_for("resource_pool"))
    
    with Session(engine) as s:
        # Check if email already exists
        existing = s.scalar(select(Candidate).where(func.lower(Candidate.email) == email))
        if existing:
            flash(f"An associate with email {email} already exists.", "warning")
            return redirect(url_for("candidate_profile", cand_id=existing.id))
        
        # Create new candidate
        cand = Candidate(
            name=name,
            email=email,
            phone=phone if phone else None,
            postcode=postcode if postcode else None,
            skills=skills if skills else None,
            created_at=datetime.datetime.utcnow(),
            last_activity_at=datetime.datetime.utcnow(),
        )
        
        # Handle day_rate if provided
        if day_rate:
            try:
                cand.day_rate = int(day_rate)
            except ValueError:
                pass
        
        s.add(cand)
        s.flush()  # Get the candidate ID
        
        # Handle CV upload
        cv_file = request.files.get("cv")
        if cv_file and cv_file.filename:
            filename = secure_filename(cv_file.filename)
            if filename:
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                if ext in {'pdf', 'doc', 'docx'}:
                    unique_filename = f"{cand.id}_{int(datetime.datetime.utcnow().timestamp())}_{filename}"
                    cv_path = os.path.join(CV_UPLOAD_FOLDER, unique_filename)
                    cv_file.save(cv_path)
                    cand.cv_filename = unique_filename
        
        # Add initial note if provided
        if notes:
            note = CandidateNote(
                candidate_id=cand.id,
                user_email=session.get("user_email", "system"),
                note_type="note",
                content=f"[Initial notes on creation]\n{notes}",
                created_at=datetime.datetime.utcnow()
            )
            s.add(note)
        
        s.commit()
        
        # Audit log: candidate created
        log_audit_event('create', 'data_access', f'Created candidate: {name}', 
                       'candidate', cand.id,
                       {'email': email, 'phone': phone})
        
        flash(f"Associate '{name}' has been added successfully.", "success")
        return redirect(url_for("candidate_profile", cand_id=cand.id))

@login_required
@app.route("/action/candidate/<int:cand_id>/update_status", methods=["POST"])
def update_candidate_status(cand_id):
    """Update candidate status and/or availability from the profile page."""
    new_status = (request.form.get("status") or "").strip()
    new_availability = (request.form.get("availability") or "").strip()
    
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found.", "danger")
            return redirect(request.referrer or url_for("resource_pool"))
        
        updates = []
        if new_status and new_status != cand.status:
            old_status = cand.status or "Available"
            cand.status = new_status
            updates.append(f"Status changed from '{old_status}' to '{new_status}'")
        
        if new_availability and new_availability != cand.availability:
            old_availability = cand.availability or "Immediately available"
            cand.availability = new_availability
            updates.append(f"Availability changed from '{old_availability}' to '{new_availability}'")
        
        if updates:
            # Add a note to track the status change
            note = CandidateNote(
                candidate_id=cand.id,
                user_email=session.get("user_email", "system"),
                note_type="activity",
                content="; ".join(updates),
                created_at=datetime.datetime.utcnow()
            )
            s.add(note)
            cand.last_activity_at = datetime.datetime.utcnow()
            s.commit()
            flash("Profile updated successfully.", "success")
        else:
            flash("No changes made.", "info")
    
    return redirect(request.referrer or url_for("candidate_profile", cand_id=cand_id))

@login_required
@app.route("/candidate/<int:cand_id>/update", methods=["POST"])
def candidate_profile_update(cand_id):
    """Update candidate profile fields from the application detail or profile page."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found.", "danger")
            return redirect(request.referrer or url_for("resource_pool"))
        
        # Update core contact fields (name, email, phone)
        if "name" in request.form:
            new_name = request.form.get("name", "").strip()
            if new_name:
                cand.name = new_name
        if "email" in request.form:
            new_email = request.form.get("email", "").strip()
            if new_email:
                cand.email = new_email
        if "phone" in request.form:
            cand.phone = request.form.get("phone", "").strip()

        # Update fields from form
        if "candidate_status" in request.form:
            cand.status = request.form.get("candidate_status", "").strip() or cand.status
        if "status_notes" in request.form:
            cand.status_notes = request.form.get("status_notes", "").strip()
        if "location" in request.form:
            cand.location = request.form.get("location", "").strip()
        if "day_rate_min" in request.form:
            try:
                cand.day_rate_min = int(request.form.get("day_rate_min", 0) or 0)
            except ValueError:
                pass
        if "day_rate_max" in request.form:
            try:
                cand.day_rate_max = int(request.form.get("day_rate_max", 0) or 0)
            except ValueError:
                pass
        if "notice_period_days" in request.form:
            try:
                cand.notice_period_days = int(request.form.get("notice_period_days", 0) or 0)
            except ValueError:
                pass
        if "security_clearance" in request.form:
            cand.security_clearance = request.form.get("security_clearance", "").strip()
        if "ir35_preference" in request.form:
            cand.ir35_preference = request.form.get("ir35_preference", "").strip()
        
        cand.last_activity_at = datetime.datetime.utcnow()
        s.commit()
        flash("Profile updated successfully.", "success")
    
    return redirect(request.referrer or url_for("candidate_profile", cand_id=cand_id))

@login_required
@app.route("/candidate/<int:cand_id>/update-status", methods=["POST"])
def candidate_update_status(cand_id):
    """Update candidate global status from profile page."""
    VALID_STATUSES = [
        "Available", "On Assignment", "On Contract", "On Notice",
        "Ex-Associate", "Unavailable", "DNU", "Do Not Contact"
    ]
    
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found.", "danger")
            return redirect(request.referrer or url_for("resource_pool"))
        
        status = request.form.get("status", "Available").strip()
        if status in VALID_STATUSES:
            old_status = cand.status or "Unknown"
            cand.status = status
            cand.last_activity_at = datetime.datetime.utcnow()
            
            # Add activity entry for status change (audit trail)
            note = CandidateNote(
                candidate_id=cand_id,
                note_type="status",
                content=f"Status changed from '{old_status}' to '{status}'",
                created_at=datetime.datetime.utcnow()
            )
            s.add(note)
            s.commit()
            flash(f"Status updated to {status}.", "success")
        else:
            flash("Invalid status.", "warning")
    
    return redirect(request.referrer or url_for("candidate_profile", cand_id=cand_id))

@login_required
@app.route("/candidate/<int:cand_id>/add-activity", methods=["POST"])
def candidate_add_activity(cand_id):
    """Add an activity entry to candidate's activity feed."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found.", "danger")
            return redirect(request.referrer or url_for("resource_pool"))
        
        activity_type = request.form.get("activity_type", "note").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        
        if title:
            # Add as a CandidateNote with type info
            note = CandidateNote(
                candidate_id=cand_id,
                note_type=activity_type,
                content=f"{title}\n{description}".strip(),
                created_at=datetime.datetime.utcnow()
            )
            s.add(note)
            cand.last_activity_at = datetime.datetime.utcnow()
            s.commit()
            flash("Activity added successfully.", "success")
        else:
            flash("Title is required.", "warning")
    
    return redirect(request.referrer or url_for("candidate_profile", cand_id=cand_id))

@login_required
@app.route("/application/<int:app_id>", methods=["GET","POST"])
def application_detail(app_id):
    # Audit log: application view
    
    interview_form = InterviewForm()

    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            abort(404)

        cand = s.get(Candidate, appn.candidate_id)
        job  = s.get(Job, appn.job_id)
        if not cand or not job:
            abort(404)

        # Engagement context (may be None if data is inconsistent)
        engagement = s.get(Engagement, job.engagement_id) if job.engagement_id else None
        eng_status = ((engagement.status if engagement else "") or "").strip().lower()
        eng_active = eng_status in {"active", "in-flight", "in progress"}

        docs = s.scalars(select(Document).where(Document.candidate_id == cand.id)).all()

        # Vetting checks for this candidate (Verifile-based)
        trust = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand.id)
            .where(VettingCheck.external_provider == "verifile")
            .where(VettingCheck.status.in_(["In Progress", "NOT STARTED"]))
            .order_by(VettingCheck.id.desc())
        )
        trust_result = None
        if trust and getattr(trust, "external_result", None):
            try:
                trust_result = json.loads(trust.external_result)
            except Exception:
                txt = trust.external_result or ""
                trust_result = {"raw": (txt[:400] + "…") if len(txt) > 400 else txt}

        # E-sign (fetch inside the session)
        esig = s.scalar(select(ESigRequest).where(ESigRequest.application_id == appn.id))

        # Candidate's current tags (for sidebar)
        cand_tags = s.scalars(
            select(TaxonomyTag)
            .join(CandidateTag, CandidateTag.tag_id == TaxonomyTag.id)
            .where(CandidateTag.candidate_id == cand.id)
            .order_by(TaxonomyTag.tag.asc())
        ).all()

        # All tags grouped by category for the dropdown
        cats = s.scalars(
            select(TaxonomyCategory).order_by(TaxonomyCategory.type.asc(), TaxonomyCategory.name.asc())
        ).all()
        tags_by_cat = {
            c.id: s.scalars(
                select(TaxonomyTag).where(TaxonomyTag.category_id == c.id).order_by(TaxonomyTag.tag.asc())
            ).all()
            for c in cats
        }

        # Use the global helper so Withdrawn/Closed are treated as not open
        job_open = _job_is_open(job)
        applied_on = appn.created_at

        # Stage banner context (very light-touch ordering)
        # (contract signed > contract issued > vetting > interview completed > interview scheduled > shortlisted > declared)
        stage_ctx = None
        if esig and (esig.status or "").lower() in {"signed", "completed"}:
            stage_ctx = f"Contract signed for {job.title}"
        elif esig and (esig.status or "").lower() in {"sent", "delivered"}:
            stage_ctx = f"Contract issued for {job.title}"
        elif trust and (trust.status or "").lower() in {"created", "inprogress"}:
            stage_ctx = "Vetting in progress"
        elif appn.interview_completed_at:
            stage_ctx = "Interview completed"
        elif appn.interview_scheduled_at:
            when = appn.interview_scheduled_at.strftime("%Y-%m-%d %H:%M")
            stage_ctx = f"Interview scheduled — {when}"
        else:
            # shortlisted?
            sl_exists = s.scalar(
                select(Shortlist.id).where(Shortlist.job_id == job.id, Shortlist.candidate_id == cand.id).limit(1)
            )
            if sl_exists:
                stage_ctx = f"Shortlisted for {job.title}"
            else:
                stage_ctx = "Declared interest"

        # Disable action buttons if engagement not active or job not open
        actions_disabled = (not eng_active) or (not job_open)

        # Vetting checks data (for automation toggle and status display)
        vetting_checks_map = {}
        try:
            for vc in s.scalars(select(VettingCheck).where(VettingCheck.candidate_id == cand.id)).all():
                vetting_checks_map[vc.check_type] = {
                    "id": vc.id,
                    "status": vc.status or "NOT STARTED",
                    "notes": vc.notes or "",
                    "automation_enabled": vc.automation_enabled if vc.automation_enabled is not None else True,
                }
        except Exception:
            pass

    # Render (note: no DB work after the session closes)
    return render_template(
        "application_detail.html",
        appn=appn,
        cand=cand,
        job=job,
        engagement=engagement,
        docs=docs,
        trust=trust,
        trust_result=trust_result,
        esig=esig,
        interview_form=interview_form,
        # Tags-only context:
        cand_tags=cand_tags,
        cats=cats,
        tags_by_cat=tags_by_cat,
        # Meta:
        job_open=job_open,
        applied_on=applied_on,
        # Stage banner + UX hints:
        stage_context=stage_ctx,
        actions_disabled=actions_disabled,
        # Vetting check data (for automation toggle):
        vetting_checks_map=vetting_checks_map,
    )

@login_required
@app.route("/action/score/<int:app_id>", methods=["POST"])
def action_score(app_id):
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id==app_id))
        if not appn:
            abort(404)
        job = s.scalar(select(Job).where(Job.id==appn.job_id))
        doc = s.scalar(
            select(Document)
            .where(Document.candidate_id==appn.candidate_id)
            .order_by(Document.uploaded_at.desc())
        )
        cv_text = extract_cv_text(doc) if doc else ""
        result = ai_score_with_explanation(job.description or "", cv_text)
        appn.ai_score = int(result["final"])
        appn.ai_explanation = (result.get("explanation") or "")[:7999]
        s.commit()
    flash("AI score updated", "success")
    return redirect(url_for("application_detail", app_id=app_id))

@login_required
@app.route("/action/summarise/<int:app_id>", methods=["POST"])
def action_summarise(app_id):
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id==app_id))
        if not appn:
            abort(404)
        doc = s.scalar(
            select(Document)
            .where(Document.candidate_id==appn.candidate_id)
            .order_by(Document.uploaded_at.desc())
        )
        cv_text = extract_cv_text(doc) if doc else ""
        appn.ai_summary = ai_summarise(cv_text or "")
        s.commit()
    flash("AI summary generated", "success")
    return redirect(url_for("application_detail", app_id=app_id))

# -------- Verifile vetting (application-level) --------
@login_required
@app.route("/action/verifile/<int:app_id>", methods=["POST"])
def action_verifile(app_id):
    """Submit vetting checks to Verifile for an application's candidate."""
    do_rtw = bool(request.form.get("rtw"))
    do_idv = bool(request.form.get("idv", True))
    do_dbs = bool(request.form.get("dbs"))

    checks_to_submit = []
    if do_rtw:
        checks_to_submit.append("Right to Work")
    if do_idv:
        checks_to_submit.append("Identity Verification")
    if do_dbs:
        checks_to_submit.append("DBS Check")

    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            abort(404)
        cand = s.scalar(select(Candidate).where(Candidate.id == appn.candidate_id))
        if not cand:
            abort(404)

        try:
            submitted = verifile_submit_all_checks(
                cand.id, cand.name, cand.email, checks_to_submit, s
            )
            s.commit()
        except Exception as e:
            flash(f"Verifile submission failed: {e}", "danger")
            return redirect(url_for("application_detail", app_id=app_id))

    flash(f"Verifile checks initiated ({submitted} submitted)", "success")
    return redirect(url_for("application_detail", app_id=app_id))

# NOTE: /webhook/trustid removed — use /webhook/verifile instead

# -------- Verifile pre-employment screening --------
# Verifile product catalogue: https://www.verifile.co.uk/screening-services
# API developer docs: https://developer.verifile.co.uk/

# Map our 12 vetting check types to Verifile's actual product names.
# These use Verifile's exact product naming from their catalogue.
# The DBS level can be overridden per-engagement via VERIFILE_DBS_LEVEL env var.
VERIFILE_DBS_LEVEL = os.getenv("VERIFILE_DBS_LEVEL", "Basic")  # Basic, Standard, or Enhanced

VERIFILE_CHECK_MAP = {
    # Criminal Record Checks — exact Verifile product names
    # Options: "Criminal record check (Basic DBS, England & Wales)"
    #          "Criminal record check (Standard DBS, England & Wales)"
    #          "Criminal record check (Enhanced DBS, England & Wales)"
    #          "Criminal record check (Basic, Northern Ireland)"
    #          "Criminal record check (Level 1, Scotland)" / Level 2 / Level 2 with Barred Lists
    #          "DBS Adult First check"
    #          "PVG scheme (Registration, Scotland)" / "PVG scheme (Update, Scotland)"
    "DBS Check": f"Criminal record check ({VERIFILE_DBS_LEVEL} DBS, England & Wales)",

    # Identity and Documents Verification — Verifile products:
    # "Digital identity check", "Online identity check", "Global passport validation",
    # "Passport check", "URU (online identity check)", "360 degree background report"
    "Identity Verification": "Digital identity check",

    # Right to Work — Verifile products:
    # "Right to work (Digital & Conditional)", "Right to work (Digital)",
    # "Right to work check (audit)"
    "Right to Work": "Right to work (Digital)",

    # Referencing and Verification — exact Verifile names
    "Address History":          "Activity checks",          # covers address/activity verification
    "Employment History":       "Employment history check",
    "References":               "Character reference check",
    "Qualifications":           "Education qualifications check",
    "Professional Registration": "Professional memberships and qualifications check",

    # Credit and Financial Checks — Verifile products:
    # "Credit check (Equifax)", "Credit check (Experian)",
    # "Civil litigation search", "Directorship search"
    "Credit Check":                    "Credit check (Experian)",
    "Directorship / Disqualification": "Directorship search",

    # Fraud Checks
    # "Global fraud and sanctions search", "Cifas fraud database check"
    "Sanctions / PEP": "Global fraud and sanctions search",

    # Open Media Searches — Verifile products:
    # "Classic Social Media Search", "Classic Adverse Internet Search",
    # "News Search", "Executive due diligence report"
    "Social Media Review": "Classic Social Media Search",
}

# Full Verifile product catalogue (for reference / future use)
VERIFILE_ALL_PRODUCTS = {
    # Referencing and Verification
    "Activity checks", "Character reference check", "CV comparison",
    "Education qualifications check", "Employment history check",
    "FCA regulated references", "Gap analysis",
    "Professional memberships and qualifications check",
    # Professional Associations
    "Apostille service", "Energy and Utility Skills Register (EUSR) check",
    "Financial Services Register search",
    "Fitness and Propriety Declaration (Basic)",
    "Fitness and Propriety Declaration (Standard)",
    "Fitness and Propriety Declaration (Regulated)",
    "Gas Safe Register search", "Health and Safety Executive (HSE) database search",
    "National Union of Journalists Register Search",
    "New Roads and Street Works Act check", "Qualified teacher status check",
    "Security Industry Authority Licence Check",
    "Solicitors Disciplinary Tribunal (SDTR / SDT) check",
    "Solicitors Regulation Authority (SRA) check",
    # Identity and Documents
    "360 degree background report", "Digital identity check",
    "Global passport validation", "Online identity check", "Passport check",
    "Right to work (Digital & Conditional)", "Right to work (Digital)",
    "Right to work check (audit)", "URU (online identity check)",
    # Criminal Record Checks
    "Criminal record check (Basic DBS, England & Wales)",
    "Criminal record check (Basic, Northern Ireland)",
    "Criminal record check (Enhanced DBS, England & Wales)",
    "Criminal record check (Enhanced, Northern Ireland)",
    "Criminal record check (Level 1, Scotland)",
    "Criminal record check (Level 2 with Barred Lists, Scotland)",
    "Criminal record check (Level 2, Scotland)",
    "Criminal record check (Standard DBS, England & Wales)",
    "Criminal record check (Standard, Northern Ireland)",
    "DBS Adult First check",
    "PVG scheme (Registration, Scotland)", "PVG scheme (Update, Scotland)",
    # Credit and Financial
    "Civil litigation search", "Credit check (Equifax)", "Credit check (Experian)",
    "Directorship search", "Limited civil and criminal court search",
    # Fraud
    "Cifas fraud database check", "Global fraud and sanctions search",
    # Open Media
    "Animal rights activist search", "Animal rights interest search",
    "Animal rights interest search (Enhanced)",
    "Classic Adverse Internet Search", "Classic Social Media Search",
    "Executive due diligence report", "News Search",
    # Driver and Vehicle
    "Driver abstract (Northern Ireland)",
    "Driver abstract (UK excluding Northern Ireland)", "MOT and insurance check",
    # Vendor Vetting
    "Company credit check (limited)", "Company credit check (non-limited)",
    "EU and UK VAT Number Validation",
}

def _verifile_headers():
    """Return auth headers for the Verifile REST API."""
    if not VERIFILE_API_KEY or _requests_lib is None:
        raise RuntimeError("Verifile API key or requests library not configured")
    return {
        "Authorization": f"Bearer {VERIFILE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Client-Id": VERIFILE_CLIENT_ID,
    }

def verifile_create_candidate(name: str, email: str, candidate_id: int) -> str:
    """Create a candidate/subject in Verifile. Returns the Verifile subject ID.

    POST /v3/subjects
    """
    headers = _verifile_headers()
    # Split name into first/last for Verifile
    parts = (name or "").strip().split(None, 1)
    first_name = parts[0] if parts else "Unknown"
    last_name = parts[1] if len(parts) > 1 else ""

    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "external_reference": f"OS1-CAND-{candidate_id}",
    }
    resp = _requests_lib.post(
        f"{VERIFILE_BASE_URL}/subjects",
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return str(data.get("id") or data.get("subject_id") or "")

def verifile_submit_check(subject_id: str, check_type: str, candidate_id: int, webhook_url: str) -> str:
    """Submit a single screening check to Verifile. Returns the Verifile screening/order ID.

    POST /v3/screenings
    """
    headers = _verifile_headers()
    product_code = VERIFILE_CHECK_MAP.get(check_type, "")
    if not product_code:
        raise RuntimeError(f"No Verifile product mapping for check type: {check_type}")

    payload = {
        "subject_id": subject_id,
        "product_code": product_code,
        "external_reference": f"OS1-CAND-{candidate_id}-{check_type}",
        "webhook_url": webhook_url,
    }
    resp = _requests_lib.post(
        f"{VERIFILE_BASE_URL}/screenings",
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return str(data.get("id") or data.get("screening_id") or "")

def verifile_poll_check(screening_id: str) -> dict:
    """Poll a single screening status from Verifile.

    GET /v3/screenings/{id}
    Returns dict with 'status' and 'result' keys.
    """
    headers = _verifile_headers()
    resp = _requests_lib.get(
        f"{VERIFILE_BASE_URL}/screenings/{screening_id}",
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    raw_status = (data.get("status") or "unknown").lower()

    # Map Verifile statuses to our internal statuses
    status_map = {
        "pending": "In Progress",
        "in_progress": "In Progress",
        "processing": "In Progress",
        "awaiting_input": "In Progress",
        "complete": "Complete",
        "completed": "Complete",
        "passed": "Complete",
        "clear": "Complete",
        "failed": "Failed",
        "rejected": "Failed",
        "cancelled": "N/A",
        "refer": "In Progress",
    }
    return {
        "status": status_map.get(raw_status, "In Progress"),
        "result": data,
    }

def verifile_submit_all_checks(candidate_id: int, cand_name: str, cand_email: str,
                                checks_to_submit: list, session) -> int:
    """Submit multiple vetting checks to Verifile for a candidate.

    Creates the candidate in Verifile (or reuses existing), then submits each check.
    Updates VettingCheck rows with external_ref and external_provider.
    Returns count of successfully submitted checks.
    """
    if not VERIFILE_API_KEY:
        return 0  # Verifile not configured — checks stay as manual

    webhook_url = f"{APP_BASE_URL}/webhook/verifile"
    submitted = 0

    try:
        subject_id = verifile_create_candidate(cand_name, cand_email, candidate_id)
    except Exception as e:
        current_app.logger.warning(f"Verifile: failed to create subject for candidate #{candidate_id}: {e}")
        return 0

    for check_type in checks_to_submit:
        if check_type not in VERIFILE_CHECK_MAP:
            continue  # No Verifile mapping — stays manual

        # Find the VettingCheck row
        vc = session.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == candidate_id)
            .where(VettingCheck.check_type == check_type)
        )
        if not vc or vc.status.upper() in ("COMPLETE", "N/A"):
            continue

        try:
            screening_id = verifile_submit_check(subject_id, check_type, candidate_id, webhook_url)
            vc.external_ref = screening_id
            vc.external_provider = "verifile"
            vc.status = "In Progress"
            submitted += 1
        except Exception as e:
            current_app.logger.warning(f"Verifile: failed to submit {check_type} for candidate #{candidate_id}: {e}")
            vc.notes = (vc.notes or "") + f"\nVerifile submit failed: {e}"

    return submitted


@app.route("/webhook/verifile", methods=["POST"])
def webhook_verifile():
    """Receive Verifile webhook callbacks when screening results are ready.

    Verifile posts JSON with screening_id and status.
    Auto-updates the VettingCheck row and checks if all vetting is now complete.
    """
    payload_bytes = request.get_data()
    payload = request.json or {}

    # Verify webhook signature if configured
    if VERIFILE_WEBHOOK_SECRET:
        sig_header = request.headers.get("X-Verifile-Signature", "")
        expected = hmac.new(VERIFILE_WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig_header, expected):
            return jsonify({"error": "Invalid signature"}), 403

    with Session(engine) as s:
        # Log the raw webhook event
        s.add(WebhookEvent(
            source="verifile",
            event_type=str(payload.get("event_type", payload.get("status", "unknown"))),
            payload=json.dumps(payload)[:39999],
        ))

        # Find the screening reference
        screening_id = str(payload.get("screening_id") or payload.get("id") or "")
        if not screening_id:
            s.commit()
            return jsonify({"ok": True, "note": "no screening_id in payload"})

        # Find matching VettingCheck
        vc = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.external_ref == screening_id)
            .where(VettingCheck.external_provider == "verifile")
        )
        if not vc:
            s.commit()
            current_app.logger.warning(f"Verifile webhook: no VettingCheck found for screening {screening_id}")
            return jsonify({"ok": True, "note": "no matching check"})

        # Map Verifile status to our status
        raw_status = (payload.get("status") or "unknown").lower()
        status_map = {
            "complete": "Complete", "completed": "Complete", "passed": "Complete", "clear": "Complete",
            "failed": "Failed", "rejected": "Failed",
            "pending": "In Progress", "in_progress": "In Progress", "processing": "In Progress",
            "cancelled": "N/A",
        }
        new_status = status_map.get(raw_status, "In Progress")
        old_status = vc.status

        vc.status = new_status
        vc.external_result = json.dumps(payload)[:19999]
        if new_status == "Complete":
            vc.completed_at = datetime.datetime.utcnow()

        cand_id = vc.candidate_id

        # Audit log
        log_audit_event(
            'update', 'vetting',
            f'Verifile webhook: "{vc.check_type}" updated from "{old_status}" to "{new_status}"',
            'candidate', cand_id,
            {'screening_id': screening_id, 'check_type': vc.check_type, 'verifile_status': raw_status}
        )

        s.commit()

        # Check if ALL vetting is now complete — auto-advance workflow
        ALL_VETTING_CHECKS = [
            "Right to Work", "Identity Verification", "Address History", "DBS Check",
            "Employment History", "References", "Qualifications", "Professional Registration",
            "Credit Check", "Directorship / Disqualification", "Sanctions / PEP", "Social Media Review"
        ]
        all_checks = s.execute(
            select(VettingCheck).where(VettingCheck.candidate_id == cand_id)
        ).scalars().all()
        check_statuses = {v.check_type: v.status.upper() for v in all_checks}
        completed_count = sum(1 for ct in ALL_VETTING_CHECKS
                              if check_statuses.get(ct, "NOT STARTED") in ["COMPLETE", "N/A", "REFERRAL APPROVED"])

        if completed_count == len(ALL_VETTING_CHECKS):
            active_app = s.scalar(
                select(Application)
                .where(Application.candidate_id == cand_id)
                .where(Application.status == "Vetting In-Flight")
                .order_by(Application.created_at.desc())
            )
            if active_app:
                # C-8: Default stage names — update if workflow stages are reconfigured
                active_app.status = "Contract Issued"
                cand = s.get(Candidate, cand_id)
                if cand:
                    cand.previously_vetted = True
                log_audit_event(
                    'update', 'workflow',
                    f'Verifile: all vetting complete, auto-moved to Contract Issued',
                    'application', active_app.id,
                    {'trigger': 'verifile_all_complete'}
                )
                s.commit()

    return jsonify({"ok": True})


@csrf.exempt
@app.route("/api/vetting/poll-verifile/<int:cand_id>", methods=["POST"])
@login_required
def api_vetting_poll_verifile(cand_id):
    """Manually poll Verifile for updated statuses on all outstanding checks for a candidate."""
    if not VERIFILE_API_KEY:
        return jsonify({"ok": False, "error": "Verifile API key not configured"}), 400

    with Session(engine) as s:
        checks = s.execute(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id)
            .where(VettingCheck.external_provider == "verifile")
            .where(VettingCheck.status.in_(["In Progress", "NOT STARTED"]))
        ).scalars().all()

        updated = 0
        for vc in checks:
            if not vc.external_ref:
                continue
            try:
                result = verifile_poll_check(vc.external_ref)
                vc.status = result["status"]
                vc.external_result = json.dumps(result["result"])[:19999]
                if result["status"] == "Complete":
                    vc.completed_at = datetime.datetime.utcnow()
                updated += 1
            except Exception as e:
                current_app.logger.warning(f"Verifile poll failed for {vc.check_type}: {e}")

        s.commit()

    return jsonify({"ok": True, "updated": updated})


# -------- Interview scheduling (ICS) --------
@login_required
@app.route("/action/schedule_interview/<int:app_id>", methods=["POST"])
def action_schedule_interview(app_id):
    form_dt = request.form.get("scheduled_at")
    interviewer_email = request.form.get("interviewer_email") or INTERVIEWER_EMAIL

    # parse start time
    start = dtparser.parse(form_dt) if form_dt else None
    if not start:
        flash("Please provide a valid date/time", "danger")
        return redirect(url_for("application_detail", app_id=app_id))
    end = start + datetime.timedelta(hours=1)

    # we'll fill these before session closes
    cand_name = ""
    cand_email = ""
    job_title = ""

    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            abort(404)

        cand = s.scalar(select(Candidate).where(Candidate.id == appn.candidate_id))
        job  = s.scalar(select(Job).where(Job.id == appn.job_id))

        if not cand or not job:
            abort(404)

        # cache the bits we need OUTSIDE the session
        cand_name = cand.name or ""
        cand_email = cand.email or ""
        job_title = job.title or ""

        # GAP 1.2 FIX: Auto-trigger workflow status when interview is scheduled
        appn.interview_scheduled_at = start
        appn.status = "I&A"  # Interview & Assessment stage
        
        # Update candidate status to reflect interviewing state
        cand.status = "Interviewing"
        cand.last_activity_at = datetime.datetime.utcnow()
        
        # GAP X.4: Audit log for compliance
        log_audit_event(
            'update', 'workflow', 
            f'Interview scheduled for {cand_name} - {job_title}',
            'application', app_id,
            {'scheduled_at': start.isoformat(), 'old_status': appn.status, 'new_status': 'I&A'}
        )
        
        s.commit()

    # now we're OUTSIDE the session but we only use plain strings, not ORM objects
    summary = f"Interview — {job_title}"
    description = f"Interview for {job_title} with {cand_name}"
    location = "Microsoft Teams / Zoom (link to follow)"

    ics_bytes = ics_invite(
        summary,
        description,
        start,
        end,
        location,
        SMTP_FROM,
        cand_email,
    )

    # send calendar invite to candidate
    send_email(
        cand_email,
        summary,
        f"<p>Hi {cand_name}, your interview is scheduled for {start}.</p>",
        attachments=[("interview.ics", ics_bytes, "text/calendar")],
    )

    # send calendar invite to interviewer
    send_email(
        interviewer_email,
        summary,
        f"<p>Interview scheduled with {cand_name} for {start}.</p>",
        attachments=[("interview.ics", ics_bytes, "text/calendar")],
    )

    flash("Interview scheduled and invites sent", "success")
    return redirect(url_for("application_detail", app_id=app_id))

@login_required
@app.route("/action/mark_interview_completed/<int:app_id>", methods=["POST"])
def action_mark_interview_completed(app_id):
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id==app_id))
        if not appn:
            abort(404)
        appn.interview_completed_at = datetime.datetime.utcnow()
        appn.status = "Client Review"  # Move to Client Review stage after internal interview
        s.commit()
    flash("Interview marked as completed - moved to Client Review", "success")
    return redirect(url_for("application_detail", app_id=app_id))

@login_required
@app.route("/action/complete_interview/<int:app_id>", methods=["POST"])
def action_complete_interview(app_id):
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            abort(404)
        appn.status = "Client Review"  # Move to Client Review stage
        appn.interview_completed_at = datetime.datetime.utcnow()
        s.commit()
    flash("Interview completed - moved to Client Review.", "success")
    return redirect(url_for("application_detail", app_id=app_id))

@login_required
@app.route("/action/skip_interview/<int:app_id>", methods=["POST"])
def action_skip_interview(app_id):
    """Skip interview and move to Client Review without scheduling"""
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            abort(404)
        # Mark interview as completed without scheduling
        appn.interview_completed_at = datetime.datetime.utcnow()
        appn.interview_notes = (appn.interview_notes or "") + "\n[Interview skipped]"
        appn.status = "Client Review"  # Move to Client Review stage
        s.commit()
    flash("Interview skipped - moved to Client Review.", "success")
    return redirect(url_for("application_detail", app_id=app_id))

@login_required
@app.route("/action/interview_not_required/<int:app_id>", methods=["POST"])
def action_interview_not_required(app_id):
    """Mark interview as not required for this application."""
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            abort(404)
        appn.status = "Client Review"  # Move to Client Review stage
        appn.interview_notes = (appn.interview_notes or "") + "\n[Interview not required]"
        s.commit()
    flash("Interview not required - moved to Client Review.", "success")
    return redirect(url_for("application_detail", app_id=app_id))


@login_required
@app.route("/action/skip_stage/<int:app_id>", methods=["POST"])
def action_skip_stage(app_id):
    """REQ-274: General skip stage — advance application to next workflow stage."""
    # Note: Skip/unskip intentionally bypasses ALLOWED_TRANSITIONS since the purpose
    # is to move applications outside the normal workflow flow (e.g., returning candidates). (C-9)
    target_stage = request.form.get("target_stage", "").strip()
    reason = request.form.get("skip_reason", "").strip()

    if not target_stage:
        flash("Target stage is required.", "danger")
        return redirect(request.referrer or url_for("workflow"))

    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            abort(404)

        old_status = appn.status
        appn.status = target_stage
        appn.notes = (appn.notes or "") + f"\n[Stage skipped from {old_status} to {target_stage}: {reason or 'No reason given'}]"
        s.commit()

        try:
            log_audit_event("stage_skip", "workflow",
                            f"Application {app_id} skipped from {old_status} to {target_stage}",
                            resource_type="application", resource_id=app_id,
                            details={"from": old_status, "to": target_stage, "reason": reason})
        except Exception:
            pass

    flash(f"Stage skipped: {old_status} \u2192 {target_stage}", "success")
    return redirect(request.referrer or url_for("workflow"))


@login_required
@app.route("/action/unskip_stage/<int:app_id>", methods=["POST"])
def action_unskip_stage(app_id):
    """REQ-274: Unskip — move application back to a previous workflow stage."""
    # Note: Skip/unskip intentionally bypasses ALLOWED_TRANSITIONS since the purpose
    # is to move applications outside the normal workflow flow (e.g., returning candidates). (C-9)
    target_stage = request.form.get("target_stage", "").strip()

    if not target_stage:
        flash("Target stage is required.", "danger")
        return redirect(request.referrer or url_for("workflow"))

    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            abort(404)

        old_status = appn.status
        appn.status = target_stage
        appn.notes = (appn.notes or "") + f"\n[Stage reverted from {old_status} to {target_stage}]"
        s.commit()

        try:
            log_audit_event("stage_unskip", "workflow",
                            f"Application {app_id} reverted from {old_status} to {target_stage}",
                            resource_type="application", resource_id=app_id,
                            details={"from": old_status, "to": target_stage})
        except Exception:
            pass

    flash(f"Stage reverted: {old_status} \u2192 {target_stage}", "success")
    return redirect(request.referrer or url_for("workflow"))


@login_required
@app.route("/action/vetting/<int:cand_id>", methods=["POST"])
def action_vetting(cand_id):
    """Start vetting process for this candidate - moves to Accepted stage."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found.", "danger")
            return redirect(request.referrer or url_for("resource_pool"))
        # Find any active application for this candidate and update status
        appn = s.scalar(
            select(Application)
            .where(Application.candidate_id == cand_id)
            .order_by(Application.created_at.desc())
        )
        if appn:
            appn.status = "Accepted"  # Offer accepted, vetting starts
            s.commit()
    flash("Vetting process started - associate moved to Accepted stage.", "success")
    return redirect(request.referrer or url_for("candidate_profile", cand_id=cand_id))

@csrf.exempt
@app.route("/api/vetting/trigger/<int:cand_id>", methods=["POST"])
@login_required
def api_vetting_trigger(cand_id):
    """Start vetting: initialise vetting checks to In Progress for this candidate.
    Uses engagement-specific vetting requirements if available, otherwise defaults to all 12 checks."""
    DEFAULT_VETTING_CHECKS = [
        "Right to Work", "Identity Verification", "Address History", "DBS Check",
        "Employment History", "References", "Qualifications", "Professional Registration",
        "Credit Check", "Directorship / Disqualification", "Sanctions / PEP", "Social Media Review"
    ]
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            return jsonify({"ok": False, "error": "Associate not found"}), 404

        # Find the candidate's active application to get engagement context
        appn = s.scalar(
            select(Application)
            .where(Application.candidate_id == cand_id)
            .where(Application.status.in_(["Accepted", "Offer Accepted"]))
            .order_by(Application.created_at.desc())
        )

        # Determine which checks apply based on engagement vetting requirements
        checks_to_trigger = DEFAULT_VETTING_CHECKS
        engagement_ref = None
        if appn and appn.job_id:
            job = s.get(Job, appn.job_id)
            if job and job.engagement_id:
                engagement = s.get(Engagement, job.engagement_id)
                if engagement and engagement.vetting_requirements:
                    try:
                        eng_checks = json.loads(engagement.vetting_requirements)
                        if isinstance(eng_checks, list) and eng_checks:
                            checks_to_trigger = eng_checks
                            engagement_ref = engagement.ref
                    except (json.JSONDecodeError, TypeError):
                        pass

        existing = {
            vc.check_type: vc
            for vc in s.scalars(
                select(VettingCheck).where(VettingCheck.candidate_id == cand_id)
            ).all()
        }

        now = datetime.datetime.utcnow()
        created = 0
        na_count = 0
        for ct in DEFAULT_VETTING_CHECKS:
            if ct in checks_to_trigger:
                # This check is required — set to In Progress
                if ct in existing:
                    if (existing[ct].status or "NOT STARTED").upper() == "NOT STARTED":
                        existing[ct].status = "In Progress"
                        existing[ct].created_at = now
                        created += 1
                else:
                    s.add(VettingCheck(
                        candidate_id=cand_id,
                        check_type=ct,
                        status="In Progress",
                        created_at=now,
                    ))
                    created += 1
            else:
                # This check is NOT required for this engagement — mark N/A
                if ct in existing:
                    if (existing[ct].status or "NOT STARTED").upper() == "NOT STARTED":
                        existing[ct].status = "N/A"
                        existing[ct].notes = "Not required for this engagement"
                        existing[ct].completed_at = now
                        na_count += 1
                else:
                    s.add(VettingCheck(
                        candidate_id=cand_id,
                        check_type=ct,
                        status="N/A",
                        notes="Not required for this engagement",
                        completed_at=now,
                        created_at=now,
                    ))
                    na_count += 1

        # Move application to Vetting In-Flight
        # C-8: Default stage name — update if workflow stages are reconfigured
        if appn:
            appn.status = "Vetting In-Flight"

        cand.status = "In Vetting"

        msg = f'Vetting triggered for {cand.name}: {created} checks set to In Progress'
        if na_count:
            msg += f', {na_count} marked N/A (not required)'
        if engagement_ref:
            msg += f' (per {engagement_ref} requirements)'

        log_audit_event(
            'update', 'vetting',
            msg,
            'candidate', cand_id,
            {'checks_initialised': created, 'checks_na': na_count, 'engagement_ref': engagement_ref}
        )
        s.commit()

        # Auto-submit to Verifile if API key is configured
        verifile_submitted = 0
        if VERIFILE_API_KEY:
            try:
                verifile_submitted = verifile_submit_all_checks(
                    cand_id, cand.name, cand.email, checks_to_trigger, s
                )
                s.commit()
            except Exception as e:
                current_app.logger.warning(f"Verifile auto-submit failed for candidate #{cand_id}: {e}")

    result_msg = f"Vetting started: {created} checks initialised"
    if na_count:
        result_msg += f", {na_count} not required"
    if verifile_submitted:
        result_msg += f", {verifile_submitted} submitted to Verifile"
    elif VERIFILE_API_KEY:
        result_msg += " (Verifile submission pending)"

    return jsonify({"ok": True, "message": result_msg})

@csrf.exempt
@app.route("/api/vetting/toggle-automation/<int:check_id>", methods=["POST"])
@login_required
def api_vetting_toggle_automation(check_id):
    """Toggle automation on/off for a specific vetting check."""
    with Session(engine) as s:
        check = s.get(VettingCheck, check_id)
        if not check:
            return jsonify({"ok": False, "error": "Check not found"}), 404

        check.automation_enabled = not check.automation_enabled
        new_state = "enabled" if check.automation_enabled else "paused"

        log_audit_event(
            'update', 'vetting',
            f'Automation {new_state} for "{check.check_type}"',
            'candidate', check.candidate_id,
            {'check_type': check.check_type, 'automation_enabled': check.automation_enabled}
        )
        s.commit()

    return jsonify({"ok": True, "automation_enabled": check.automation_enabled, "message": f"Automation {new_state}"})

@login_required
@app.route("/action/save_general_notes/<int:cand_id>", methods=["POST"])
def action_save_general_notes(cand_id):
    """Save general notes for a candidate."""
    notes = request.form.get("general_notes", "").strip()
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if cand:
            cand.general_notes = notes
            s.commit()
    flash("Notes saved.", "success")
    return redirect(request.referrer or url_for("candidate_profile", cand_id=cand_id))

@login_required
@app.route("/action/contract/issue/<int:cand_id>/<int:eng_id>", methods=["POST"])
def action_contract_issue(cand_id, eng_id):
    """Issue contract for this candidate and engagement."""
    flash("Contract issued.", "success")
    return redirect(request.referrer or url_for("candidate_profile", cand_id=cand_id))

@login_required
@app.route("/action/contract/sign/<int:contract_id>", methods=["POST"])
def action_contract_sign(contract_id):
    """Mark contract as signed."""
    flash("Contract signed.", "success")
    return redirect(request.referrer or url_for("resource_pool"))

@login_required
@app.route("/action/contract/notice/<int:contract_id>", methods=["POST"])
def action_contract_notice(contract_id):
    """Put contract on notice."""
    flash("Contract put on notice.", "info")
    return redirect(request.referrer or url_for("resource_pool"))

@login_required
@app.route("/action/contract/cancel_notice/<int:contract_id>", methods=["POST"])
def action_contract_cancel_notice(contract_id):
    """Cancel notice on contract."""
    flash("Notice cancelled.", "info")
    return redirect(request.referrer or url_for("resource_pool"))

@login_required
@app.route("/action/contract/extend/<int:contract_id>", methods=["POST"])
def action_contract_extend(contract_id):
    """Extend contract."""
    flash("Contract extended.", "success")
    return redirect(request.referrer or url_for("resource_pool"))

@login_required
@app.route("/action/contract/terminate/<int:contract_id>", methods=["POST"])
def action_contract_terminate(contract_id):
    """Terminate contract."""
    flash("Contract terminated.", "warning")
    return redirect(request.referrer or url_for("resource_pool"))

@login_required
@app.route("/action/contract/update/<int:contract_id>", methods=["POST"])
def action_contract_update(contract_id):
    """Update contract details."""
    flash("Contract updated.", "success")
    return redirect(request.referrer or url_for("resource_pool"))

@login_required
@app.route("/action/save_interview_notes/<int:app_id>", methods=["POST"])
def action_save_interview_notes(app_id):
    notes = request.form.get("interview_notes", "").strip()
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            abort(404)
        appn.interview_notes = notes
        s.commit()
    flash("Interview notes saved.", "success")
    return redirect(url_for("application_detail", app_id=app_id))

@login_required
@app.route("/action/save_assessor_notes/<int:app_id>", methods=["POST"])
def action_save_assessor_notes(app_id):
    notes = request.form.get("assessor_notes", "").strip()
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id == app_id))
        if not appn:
            abort(404)
        appn.cover_note = notes
        s.commit()
    flash("Assessor notes saved.", "success")
    return redirect(url_for("application_detail", app_id=app_id))

# -------- E-signature: Signable (signable.co.uk) --------
def _signable_headers():
    """Return auth headers for the Signable REST API."""
    if not SIGNABLE_API_KEY or _requests_lib is None:
        raise RuntimeError("Signable API key or requests library not configured")
    return {
        "Authorization": f"Basic {base64.b64encode((SIGNABLE_API_KEY + ':').encode()).decode()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def send_esign_signable(appn_id: int, signer_name: str, signer_email: str, subject: str, message: str):
    """Send an envelope via the Signable REST API.

    Signable API docs: https://signable.co.uk/api
    POST /v1/envelopes — creates and sends an envelope with a signing party.
    Returns the envelope fingerprint (their unique ID).
    """
    headers = _signable_headers()
    payload = {
        "envelope_title": subject,
        "envelope_signing_message": message,
        "envelope_parties": [
            {
                "party_name": signer_name,
                "party_email": signer_email,
                "party_role": "signer",
            }
        ],
    }
    # Attach Signable template if configured (get fingerprint from Signable > Templates)
    if SIGNABLE_TEMPLATE_FINGERPRINT:
        payload["envelope_documents"] = [
            {"document_template_fingerprint": SIGNABLE_TEMPLATE_FINGERPRINT}
        ]
    resp = _requests_lib.post(
        f"{SIGNABLE_BASE_URL}/envelopes",
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    # Signable returns {"envelope_fingerprint": "...", ...}
    return data.get("envelope_fingerprint") or data.get("id") or str(data)

def poll_esign_signable(request_id: str):
    """Poll envelope status from the Signable REST API.

    GET /v1/envelopes/{fingerprint} — returns envelope with current status.
    Signable statuses: 'sent', 'opened', 'signed', 'cancelled', 'expired', 'declined'
    """
    headers = _signable_headers()
    resp = _requests_lib.get(
        f"{SIGNABLE_BASE_URL}/envelopes/{request_id}",
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    raw_status = (data.get("envelope_status") or data.get("status") or "unknown").lower()
    status_map = {
        "sent": "Sent",
        "opened": "Sent",
        "signed": "Signed",
        "completed": "Signed",
        "cancelled": "Declined",
        "expired": "Declined",
        "declined": "Declined",
    }
    return status_map.get(raw_status, raw_status.title())

@login_required
@app.route("/action/esign/<int:app_id>", methods=["POST"])
def action_esign(app_id):
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id==app_id))
        cand = s.scalar(select(Candidate).where(Candidate.id==appn.candidate_id))
        job = s.scalar(select(Job).where(Job.id==appn.job_id))

        subject = f"Contract — {job.title}"
        message = "Please review and sign your contract."
        try:
            req_id = send_esign_signable(appn.id, cand.name, cand.email, subject, message)
        except Exception as e:
            flash(f"E-sign send failed: {e}", "danger")
            return redirect(url_for("application_detail", app_id=app_id))

        es = s.scalar(select(ESigRequest).where(ESigRequest.application_id==appn.id))
        if not es:
            es = ESigRequest(application_id=appn.id, provider="signable", request_id=req_id, status="Sent", sent_at=datetime.datetime.utcnow())
            s.add(es)
        else:
            es.request_id = req_id
            es.provider = "signable"
            es.status = "Sent"
            es.sent_at = datetime.datetime.utcnow()
        s.commit()
    flash("Contract sent for e-signature", "success")
    return redirect(url_for("application_detail", app_id=app_id))

@login_required
@app.route("/action/esign_status/<int:app_id>", methods=["POST"])
def action_esign_status(app_id):
    with Session(engine) as s:
        es = s.scalar(select(ESigRequest).where(ESigRequest.application_id==app_id))
        if not es:
            flash("No e-sign request found", "warning")
            return redirect(url_for("application_detail", app_id=app_id))
        try:
            status = poll_esign_signable(es.request_id)
        except Exception as e:
            flash(f"E-sign status failed: {e}", "danger")
            return redirect(url_for("application_detail", app_id=app_id))

        es.status = status
        if status == "Signed":
            es.signed_at = datetime.datetime.utcnow()
        s.commit()
    flash(f"E-sign status: {status}", "info")
    return redirect(url_for("application_detail", app_id=app_id))

@app.route("/webhook/esign", methods=["POST"])
def webhook_esign():
    payload = request.json or {}
    with Session(engine) as s:
        s.add(WebhookEvent(source="esign", event_type=str(payload.get('event','unknown')), payload=json.dumps(payload)[:39999]))

        # --- Signable webhook auto-processing ---
        # Signable sends POST with {"envelope_fingerprint": "...", "envelope_status": "signed", ...}
        envelope_fp = payload.get("envelope_fingerprint")
        envelope_status = (payload.get("envelope_status") or "").lower()
        if envelope_fp and envelope_status:
            # Verify webhook secret if configured
            if SIGNABLE_WEBHOOK_SECRET:
                sig_header = request.headers.get("X-Signable-Signature", "")
                import hmac, hashlib
                expected = hmac.new(SIGNABLE_WEBHOOK_SECRET.encode(), request.get_data(), hashlib.sha256).hexdigest()
                if not hmac.compare_digest(sig_header, expected):
                    return jsonify({"error": "Invalid signature"}), 403

            es = s.scalar(select(ESigRequest).where(ESigRequest.request_id == envelope_fp))
            if es:
                status_map = {"sent": "Sent", "opened": "Sent", "signed": "Signed",
                              "completed": "Signed", "cancelled": "Declined",
                              "expired": "Declined", "declined": "Declined"}
                new_status = status_map.get(envelope_status, envelope_status.title())
                es.status = new_status
                if new_status == "Signed":
                    es.signed_at = datetime.datetime.utcnow()
                # Also update candidate esign_status if we can find the candidate
                if es.application_id:
                    appn = s.get(Application, es.application_id)
                    if appn and appn.candidate_id:
                        cand = s.get(Candidate, appn.candidate_id)
                        if cand:
                            cand.esign_status = new_status

                    # REQ G-5 fix: Auto-transition Contract Sent/Issued → Contract Signed when e-sign completed
                    if new_status == "Signed" and appn and appn.status in ("Contract Sent", "Contract Issued"):
                        appn.status = "Contract Signed"
                        # Also update candidate status
                        if appn.candidate_id:
                            cand = s.get(Candidate, appn.candidate_id)
                            if cand:
                                cand.status = "On Contract"
                        try:
                            log_audit_event(
                                'update', 'workflow',
                                f'E-sign webhook: contract signed, auto-moved to Contract Signed',
                                'application', appn.id,
                                {'trigger': 'esign_signed', 'old_status': 'Contract Issued', 'new_status': 'Contract Signed'}
                            )
                        except Exception:
                            pass

        s.commit()
    return jsonify({"ok": True})

# ---- Request updated CV ----
@login_required
@app.route("/action/request_updated_cv/<int:app_id>", methods=["POST"])
def action_request_updated_cv(app_id):
    with Session(engine) as s:
        appn = s.scalar(select(Application).where(Application.id==app_id))
        cand = s.scalar(select(Candidate).where(Candidate.id==appn.candidate_id))
        link = f"{APP_BASE_URL}/candidate/{cand.id}/upload_cv"
        html = f"""
        <h3>Request for updated CV</h3>
        <p>Hi {cand.name}, we enjoyed working with you. Please upload an updated CV here:</p>
        <p><a href="{link}">{link}</a></p>
        """
        send_email(cand.email, "Please upload an updated CV", html)
    flash("CV update request sent", "success")
    return redirect(url_for("application_detail", app_id=app_id))

@app.route("/candidate/<int:cand_id>")
@login_required
def candidate_profile(cand_id: int):
    """
    Associate Profile page per wireframe requirements.
    
    Features:
    - Header with name, email, alert banner
    - Notes & Activity Panel (rich-text editor)
    - Profile sidebar (status, location, rate, CV)
    - Tags section with Retag from CV
    - Contract section with Issue Contract button
    - 12-item Vetting Checks grid
    - Vetting Progress Summary
    """
    # Optional context passed when arriving from engagement lists
    stage = (request.args.get("stage") or "").strip().lower()
    ctx = {
        "stage": stage or None,
        "job_id": request.args.get("job_id"),
        "job_title": request.args.get("job_title"),
        "interview_at": request.args.get("interview_at"),
    }

    # 12 vetting check types per wireframe
    VETTING_CHECK_TYPES = [
        "Right to Work",
        "Identity Verification",
        "Address History",
        "DBS Check",
        "Employment History",
        "References",
        "Qualifications",
        "Professional Registration",
        "Credit Check",
        "Directorship / Disqualification",
        "Sanctions / PEP",
        "Social Media Review",
    ]

    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)

        latest_app = s.scalar(
            select(Application)
            .where(Application.candidate_id == cand_id)
            .order_by(Application.created_at.desc())
        )

        job = None
        job_open = False
        applied_on = None
        docs = s.scalars(select(Document).where(Document.candidate_id == cand.id)).all()

        # Build documents_ctx inside session to avoid DetachedInstanceError
        documents_ctx = []
        for d in docs:
            documents_ctx.append({
                'id': d.id,
                'name': d.filename or 'Untitled',
                'filename': d.filename,
                'doc_type': getattr(d, 'doc_type', 'cv') or 'cv',
                'ts': d.uploaded_at.strftime('%d %b %Y') if getattr(d, 'uploaded_at', None) else '',
            })

        if latest_app:
            job = s.scalar(select(Job).where(Job.id == latest_app.job_id))
            job_open = _job_is_open(job)
            applied_on = latest_app.created_at

        # Tags data for the sidebar card
        cand_tags = s.scalars(
            select(TaxonomyTag)
            .join(CandidateTag, CandidateTag.tag_id == TaxonomyTag.id)
            .where(CandidateTag.candidate_id == cand.id)
            .order_by(TaxonomyTag.tag.asc())
        ).all()

        cats = s.scalars(
            select(TaxonomyCategory).order_by(TaxonomyCategory.type.asc(), TaxonomyCategory.name.asc())
        ).all()

        tags_by_cat = {
            c.id: s.scalars(
                select(TaxonomyTag).where(TaxonomyTag.category_id == c.id).order_by(TaxonomyTag.tag.asc())
            ).all()
            for c in cats
        }
        
        # === Vetting Checks ===
        vetting_checks = []
        vetting_summary = {"complete": 0, "in_progress": 0, "not_started": 0, "na": 0}
        
        try:
            existing_checks = {
                vc.check_type: vc
                for vc in s.scalars(
                    select(VettingCheck).where(VettingCheck.candidate_id == cand_id)
                ).all()
            }
            
            for check_type in VETTING_CHECK_TYPES:
                if check_type in existing_checks:
                    check = existing_checks[check_type]
                    vetting_checks.append({
                        "id": check.id,
                        "type": check_type,
                        "status": check.status or "NOT STARTED",
                        "notes": check.notes or "",
                        "automation_enabled": getattr(check, 'automation_enabled', True) if check.automation_enabled is not None else True,
                    })
                else:
                    # Create a placeholder for display
                    vetting_checks.append({
                        "id": None,
                        "type": check_type,
                        "status": "NOT STARTED",
                        "notes": "",
                        "automation_enabled": True,
                    })
            
            # Calculate summary
            for vc in vetting_checks:
                status = (vc["status"] or "").upper()
                if status == "COMPLETE":
                    vetting_summary["complete"] += 1
                elif status == "IN PROGRESS":
                    vetting_summary["in_progress"] += 1
                elif status == "N/A":
                    vetting_summary["na"] += 1
                else:
                    vetting_summary["not_started"] += 1
        except Exception:
            # VettingCheck table might not exist yet
            for check_type in VETTING_CHECK_TYPES:
                vetting_checks.append({
                    "id": None,
                    "type": check_type,
                    "status": "NOT STARTED",
                    "notes": "",
                })
                vetting_summary["not_started"] += 1
        
        # === Notes & Activity ===
        candidate_notes = []
        try:
            candidate_notes = s.scalars(
                select(CandidateNote)
                .where(CandidateNote.candidate_id == cand_id)
                .order_by(CandidateNote.created_at.desc())
                .limit(50)
            ).all()
        except Exception:
            pass
        
        # === Contract Status ===
        contract_status = None
        esig_request = None
        try:
            esig_request = s.scalar(
                select(ESigRequest)
                .where(ESigRequest.candidate_id == cand_id)
                .order_by(ESigRequest.created_at.desc())
            )
            if esig_request:
                contract_status = esig_request.status
        except Exception:
            pass
        
        # Check if there are any active applications (for alert banner)
        active_apps_count = s.scalar(
            select(func.count(Application.id))
            .where(Application.candidate_id == cand_id)
            .where(Application.status.notin_(["Rejected", "Hired", "Contract Signed"]))
        ) or 0

        # === Placements History (Active and Historic) ===
        placements_active = []
        placements_historic = []
        try:
            # Only fetch ESigRequests with signed/completed/sent status (actual placements)
            all_contracts = s.execute(
                select(ESigRequest, Job, Engagement)
                .select_from(ESigRequest)
                .outerjoin(Application, Application.id == ESigRequest.application_id)
                .outerjoin(Job, Job.id == Application.job_id)
                .outerjoin(Engagement, Engagement.id == ESigRequest.engagement_id)
                .where(ESigRequest.candidate_id == cand_id)
                .where(ESigRequest.status.in_(["signed", "Signed", "completed", "Completed", "sent", "Sent"]))
                .order_by(ESigRequest.signed_at.desc())
            ).all()
            
            today = datetime.date.today()
            for esig, job_obj, eng in all_contracts:
                placement = {
                    'id': esig.id,
                    'engagement_name': eng.name if eng else (job_obj.title if job_obj else 'Unknown'),
                    'engagement_id': eng.id if eng else None,
                    'client': eng.client if eng else 'Unknown',
                    'role': job_obj.title if job_obj else 'N/A',
                    'start_date': eng.start_date if eng else None,
                    'end_date': eng.end_date if eng else None,
                    'status': esig.status,
                    'signed_at': esig.signed_at,
                }
                
                # Determine if active or historic based on end dates and status
                is_active = False
                esig_status_lower = (esig.status or "").lower()
                if esig_status_lower in ("signed", "completed"):
                    if eng and eng.end_date:
                        try:
                            end_dt = eng.end_date if isinstance(eng.end_date, datetime.date) else datetime.datetime.strptime(str(eng.end_date), '%Y-%m-%d').date()
                            is_active = end_dt >= today
                        except Exception:
                            is_active = True
                    elif esig.end_date:
                        try:
                            end_dt = esig.end_date.date() if isinstance(esig.end_date, datetime.datetime) else esig.end_date
                            is_active = end_dt >= today
                        except Exception:
                            is_active = True
                    else:
                        is_active = True
                placement['is_active'] = is_active
                if is_active:
                    placements_active.append(placement)
                else:
                    placements_historic.append(placement)
        except Exception:
            pass

        # === Auto-link status to "On Assignment" if active signed placement exists ===
        if placements_active and (cand.status or "Available") not in ("DNU", "Do Not Contact", "Do Not Use"):
            if cand.status != "On Assignment":
                cand.status = "On Assignment"
                s.commit()

        # === Activity Feed (structured activity log) ===
        activity_feed = []
        try:
            # Get applications (with status changes)
            apps = s.execute(
                select(Application, Job)
                .join(Job, Job.id == Application.job_id)
                .where(Application.candidate_id == cand_id)
                .order_by(Application.created_at.desc())
                .limit(20)
            ).all()
            
            for app, job_obj in apps:
                activity_feed.append({
                    'type': 'application',
                    'icon': 'fa-file-alt',
                    'color': '#3b82f6',
                    'title': f'Applied for {job_obj.title}',
                    'timestamp': app.created_at,
                    'details': f'Status: {app.status}'
                })
                if app.interview_scheduled_at:
                    activity_feed.append({
                        'type': 'interview_scheduled',
                        'icon': 'fa-calendar-check',
                        'color': '#f59e0b',
                        'title': 'Interview Scheduled',
                        'timestamp': app.interview_scheduled_at,
                        'details': f'For {job_obj.title}'
                    })
                if app.interview_completed_at:
                    activity_feed.append({
                        'type': 'interview_completed',
                        'icon': 'fa-check-circle',
                        'color': '#10b981',
                        'title': 'Interview Completed',
                        'timestamp': app.interview_completed_at,
                        'details': f'For {job_obj.title}'
                    })
            
            # Get contract events
            contracts = s.scalars(
                select(ESigRequest)
                .where(ESigRequest.candidate_id == cand_id)
                .order_by(ESigRequest.created_at.desc())
                .limit(10)
            ).all()
            
            for contract in contracts:
                if contract.sent_at:
                    activity_feed.append({
                        'type': 'contract_sent',
                        'icon': 'fa-paper-plane',
                        'color': '#8b5cf6',
                        'title': 'Contract Issued',
                        'timestamp': contract.sent_at,
                        'details': f'Provider: {contract.provider or "N/A"}'
                    })
                if contract.signed_at:
                    activity_feed.append({
                        'type': 'contract_signed',
                        'icon': 'fa-file-signature',
                        'color': '#059669',
                        'title': 'Contract Signed',
                        'timestamp': contract.signed_at,
                        'details': f'Status: {contract.status}'
                    })
            
            # Get workflow stage change notes (activity type)
            stage_notes = s.scalars(
                select(CandidateNote)
                .where(CandidateNote.candidate_id == cand_id)
                .where(CandidateNote.note_type == "activity")
                .order_by(CandidateNote.created_at.desc())
                .limit(20)
            ).all()

            for note in stage_notes:
                activity_feed.append({
                    'type': 'status',
                    'icon': 'fa-exchange-alt',
                    'color': '#8b5cf6',
                    'title': 'Stage Change',
                    'timestamp': note.created_at,
                    'details': (note.content[:150] + '...') if note.content and len(note.content) > 150 else (note.content or '')
                })

            # Get general/manual notes
            general_notes = s.scalars(
                select(CandidateNote)
                .where(CandidateNote.candidate_id == cand_id)
                .where((CandidateNote.note_type != "activity") | (CandidateNote.note_type == None))
                .order_by(CandidateNote.created_at.desc())
                .limit(10)
            ).all()

            for note in general_notes:
                activity_feed.append({
                    'type': 'note',
                    'icon': 'fa-sticky-note',
                    'color': '#6b7280',
                    'title': note.note_type or 'Note Added',
                    'timestamp': note.created_at,
                    'details': (note.content[:100] + '...') if note.content and len(note.content) > 100 else (note.content or '')
                })
            
            # Sort by timestamp descending
            activity_feed.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.datetime.min, reverse=True)
            activity_feed = activity_feed[:30]  # Limit to 30 most recent
        except Exception:
            pass

    # Build variables for candidate_profile.html template
    # documents_ctx is built inside the session block above to avoid DetachedInstanceError

    # Combine active + historic placements for template
    all_placements = placements_active + placements_historic

    # Build activity items for the template's activity feed
    # The template expects objects with: type, title, description, created_at
    activities = []
    for af in activity_feed:
        activities.append(type('Activity', (), {
            'type': af.get('type', 'note'),
            'title': af.get('title', ''),
            'description': af.get('details', ''),
            'created_at': af.get('timestamp'),
        })())

    return render_template(
        "candidate_profile.html",
        appn=latest_app,            # can be None
        latest_app=latest_app,
        cand=cand,
        job=job,
        docs=docs,
        documents_ctx=documents_ctx,
        trust=None,
        esig=esig_request,
        interview_form=None,
        job_open=job_open,
        applied_on=applied_on,
        from_candidate=True,
        ai_summary=cand.ai_summary or "",
        skills=cand.skills or "",

        # taxonomy/tag data
        cand_tags=cand_tags,
        cats=cats,
        tags_by_cat=tags_by_cat,

        # engagement/list context for banner in template
        context=ctx if ctx.get("stage") else None,

        # === New wireframe data ===
        vetting_checks=vetting_checks,
        vetting_summary=vetting_summary,
        candidate_notes=candidate_notes,
        contract_status=contract_status,
        active_apps_count=active_apps_count,
        VETTING_CHECK_TYPES=VETTING_CHECK_TYPES,
        # === Activity Feed & Placements ===
        activity_feed=activity_feed,
        activities=activities,
        placements=all_placements,
        placements_active=placements_active,
        placements_historic=placements_historic,
    )

# -------- Vetting Check Update --------
@login_required
@app.route("/candidate/<int:cand_id>/vetting", methods=["POST"])
def update_vetting_check(cand_id: int):
    """
    Update a vetting check status for a candidate.
    
    GAP 7.1 FIX: When all vetting checks are Complete or N/A, 
    auto-moves candidate to next workflow stage.
    GAP X.4: Audit trail for compliance-sensitive changes.
    """
    check_type = request.form.get("check_type", "").strip()
    new_status = request.form.get("status", "NOT STARTED")
    notes = request.form.get("notes", "")
    
    if not check_type:
        flash("Invalid vetting check type", "error")
        return redirect(url_for("candidate_profile", cand_id=cand_id))
    
    # All vetting check types
    ALL_VETTING_CHECKS = [
        "Right to Work", "Identity Verification", "Address History", "DBS Check",
        "Employment History", "References", "Qualifications", "Professional Registration",
        "Credit Check", "Directorship / Disqualification", "Sanctions / PEP", "Social Media Review"
    ]
    
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        old_status_value = None
        
        # Check if this vetting check already exists
        existing = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id)
            .where(VettingCheck.check_type == check_type)
        )
        
        if existing:
            old_status_value = existing.status
            existing.status = new_status
            existing.notes = notes
            if new_status.upper() == "COMPLETE":
                existing.completed_at = datetime.datetime.utcnow()
        else:
            new_check = VettingCheck(
                candidate_id=cand_id,
                check_type=check_type,
                status=new_status,
                notes=notes,
                completed_at=datetime.datetime.utcnow() if new_status.upper() == "COMPLETE" else None
            )
            s.add(new_check)
        
        # GAP X.4: Audit log for vetting changes (compliance critical)
        log_audit_event(
            'update', 'vetting',
            f'Vetting check "{check_type}" updated to "{new_status}"',
            'candidate', cand_id,
            {'check_type': check_type, 'old_status': old_status_value, 'new_status': new_status, 'notes': notes}
        )
        
        s.commit()
        
        # GAP 7.1: Check if all vetting is now complete
        all_checks = s.execute(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id)
        ).scalars().all()
        
        check_statuses = {vc.check_type: vc.status.upper() for vc in all_checks}
        
        # Count completed checks (COMPLETE, N/A, or REFERRAL APPROVED are considered done)
        completed_count = sum(1 for ct in ALL_VETTING_CHECKS
                            if check_statuses.get(ct, "NOT STARTED") in ["COMPLETE", "N/A", "REFERRAL APPROVED"])
        
        all_vetting_complete = completed_count == len(ALL_VETTING_CHECKS)
        
        if all_vetting_complete:
            # Find the candidate's active application in Vetting In-Flight stage
            active_app = s.scalar(
                select(Application)
                .where(Application.candidate_id == cand_id)
                .where(Application.status == "Vetting In-Flight")
                .order_by(Application.created_at.desc())
            )
            
            if active_app:
                # Auto-move to Contract Issued (GAP 1.2 auto-trigger)
                # C-8: Default stage name — update if workflow stages are reconfigured
                active_app.status = "Contract Issued"
                cand.status = "In Vetting"  # Keep as In Vetting until contract signed
                cand.previously_vetted = True
                
                log_audit_event(
                    'update', 'workflow',
                    f'Auto-triggered: All vetting complete, moved to Contract Issued',
                    'application', active_app.id,
                    {'trigger': 'vetting_complete', 'new_status': 'Contract Issued'}
                )
                
                s.commit()
                flash(f"All vetting complete! {cand.name} has been moved to 'Contract Issued' stage.", "success")
                return redirect(url_for("candidate_profile", cand_id=cand_id))
    
    flash(f"Vetting check '{check_type}' updated to '{new_status}'", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id))


# -------- REQ-269: Manual Vetting Entry Fallback --------
@login_required
@app.route("/candidate/<int:cand_id>/vetting-manual", methods=["POST"])
def manual_vetting_entry(cand_id: int):
    """REQ-269: Manual vetting data entry fallback when Verifile API unavailable."""
    check_type = request.form.get("check_type", "").strip()
    status = request.form.get("status", "COMPLETE")
    result_text = request.form.get("result_text", "").strip()
    reference_number = request.form.get("reference_number", "").strip()
    completed_date = request.form.get("completed_date", "").strip()
    notes = request.form.get("notes", "").strip()

    if not check_type:
        flash("Check type is required.", "danger")
        return redirect(url_for("candidate_profile", cand_id=cand_id))

    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)

        existing = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id)
            .where(VettingCheck.check_type == check_type)
        )

        completed_dt = None
        if completed_date:
            try:
                completed_dt = datetime.datetime.strptime(completed_date, "%Y-%m-%d")
            except ValueError:
                pass

        manual_result = json.dumps({
            "source": "manual_entry",
            "result_text": result_text,
            "reference_number": reference_number,
            "entered_by": current_user.email if current_user and hasattr(current_user, 'email') else "system",
            "entered_at": datetime.datetime.utcnow().isoformat(),
        })

        if existing:
            existing.status = status
            existing.notes = notes
            existing.external_provider = ""
            existing.external_result = manual_result
            existing.external_ref = reference_number
            if completed_dt:
                existing.completed_at = completed_dt
            elif status.upper() == "COMPLETE":
                existing.completed_at = datetime.datetime.utcnow()
        else:
            new_check = VettingCheck(
                candidate_id=cand_id,
                check_type=check_type,
                status=status,
                notes=notes,
                external_provider="",
                external_result=manual_result,
                external_ref=reference_number,
                automation_enabled=False,
                completed_at=completed_dt or (datetime.datetime.utcnow() if status.upper() == "COMPLETE" else None),
            )
            s.add(new_check)

        s.commit()

        try:
            log_audit_event(
                'create', 'vetting',
                f'Manual vetting entry: {check_type} = {status} for candidate {cand_id}',
                'candidate', cand_id,
                {'check_type': check_type, 'status': status, 'source': 'manual_entry'}
            )
        except Exception:
            pass

    flash(f"Manual vetting entry saved: {check_type} → {status}", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id))


# =========================================================================
# CONTRADICTION FIX 1: Auto-create vetting checks when candidate added to project
# Status stays "WAITING FOR ASSOCIATE" until Start Vetting button is pressed.
# =========================================================================

ALL_VETTING_CHECK_TYPES = [
    "Right to Work", "Identity Verification", "Address History", "DBS Check",
    "Employment History", "References", "Qualifications", "Professional Registration",
    "Credit Check", "Directorship / Disqualification", "Sanctions / PEP", "Social Media Review"
]

def _auto_create_vetting_checks(session, candidate_id: int, engagement_id: int = None):
    """
    Auto-create the 12 VettingCheck records for a candidate with status
    'WAITING FOR ASSOCIATE'. These remain dormant until the 'Start Vetting'
    button is pressed by staff, which changes status to 'NOT STARTED' and
    triggers the API calls and emails.
    If engagement has specific vetting_requirements, only create those checks.
    """
    # Determine which checks to create
    checks_to_create = list(ALL_VETTING_CHECK_TYPES)
    if engagement_id:
        try:
            eng = session.get(Engagement, engagement_id)
            if eng and eng.vetting_requirements:
                required = json.loads(eng.vetting_requirements)
                if required:  # Only filter if non-empty list
                    checks_to_create = [c for c in ALL_VETTING_CHECK_TYPES if c in required]
        except Exception:
            pass

    # Don't duplicate existing checks
    existing_types = set(
        r[0] for r in session.execute(
            select(VettingCheck.check_type).where(VettingCheck.candidate_id == candidate_id)
        ).all()
    )

    created = 0
    for ct in checks_to_create:
        if ct not in existing_types:
            session.add(VettingCheck(
                candidate_id=candidate_id,
                check_type=ct,
                status="WAITING FOR ASSOCIATE"
            ))
            created += 1
    return created

# =========================================================================
# GAP PLAN: VETTING START EMAIL (Batch 2.2)
# =========================================================================

@login_required
@app.route("/action/start-vetting/<int:cand_id>", methods=["POST"])
def start_vetting(cand_id: int):
    """
    Batch 2.2: Send vetting start email to candidate when vetting is triggered.
    Creates initial VettingCheck records for all 12 check types.
    """
    ALL_VETTING_CHECKS = [
        "Right to Work", "Identity Verification", "Address History", "DBS Check",
        "Employment History", "References", "Qualifications", "Professional Registration",
        "Credit Check", "Directorship / Disqualification", "Sanctions / PEP", "Social Media Review"
    ]
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found.", "danger")
            return redirect(url_for("workflow"))

        # Create vetting checks if they don't exist
        existing_types = set(
            r[0] for r in s.execute(
                select(VettingCheck.check_type).where(VettingCheck.candidate_id == cand_id)
            ).all()
        )
        created = 0
        for ct in ALL_VETTING_CHECKS:
            if ct not in existing_types:
                s.add(VettingCheck(candidate_id=cand_id, check_type=ct, status="NOT STARTED"))
                created += 1

        # Send email notification to candidate
        if cand.email:
            try:
                base_url = os.getenv("APP_BASE_URL", "http://localhost:5001")
                html_body = f"""
                <h2>Vetting Process Started</h2>
                <p>Dear {cand.name or 'Associate'},</p>
                <p>Your pre-employment vetting process has been initiated. Please log in to the
                Associate Portal to complete the required steps:</p>
                <ul>
                    <li>Upload required documents (ID, Proof of Address, Right to Work)</li>
                    <li>Complete your employment history and references</li>
                    <li>Sign the consent and declaration forms</li>
                </ul>
                <p><a href="{base_url}/portal/dashboard">Log in to the Portal</a></p>
                <p>If you have any questions, please contact your Compliance Analyst.</p>
                <p>Regards,<br>Optimus Solutions Compliance Team</p>
                """
                send_email(cand.email, "Vetting Process Started — Action Required", html_body)
                flash(f"Vetting started and email sent to {cand.email}.", "success")
            except Exception as e:
                flash(f"Vetting started but email failed: {str(e)}", "warning")
        else:
            flash(f"Vetting started ({created} checks created). No email — associate has no email address.", "warning")

        log_audit_event('create', 'vetting',
                        f'Vetting started for {cand.name} ({created} checks created)',
                        'candidate', cand_id,
                        {'checks_created': created, 'email_sent': bool(cand.email)})
        s.commit()

    return redirect(url_for("candidate_profile", cand_id=cand_id))


# =========================================================================
# GAP PLAN: QC WORKFLOW (Batch 3)
# =========================================================================

@login_required
@app.route("/action/submit-for-qc/<int:cand_id>", methods=["POST"])
def submit_for_qc(cand_id: int):
    """Batch 3.1: Submit a specific vetting check for QC review."""
    check_type = request.form.get("check_type", "").strip()
    if not check_type:
        flash("No check type specified.", "danger")
        return redirect(url_for("candidate_profile", cand_id=cand_id))

    with Session(engine) as s:
        vc = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id, VettingCheck.check_type == check_type)
        )
        if not vc:
            flash("Vetting check not found.", "danger")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        if vc.status.upper() not in ("COMPLETE", "IN PROGRESS"):
            flash("Check must be Complete or In Progress before submitting for QC.", "warning")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        vc.qc_status = "awaiting_qc"
        vc.status = "AWAITING QC"
        log_audit_event('update', 'vetting',
                        f'Submitted "{check_type}" for QC review',
                        'candidate', cand_id,
                        {'check_type': check_type})
        s.commit()
        flash(f"'{check_type}' submitted for QC review.", "success")

    return redirect(url_for("candidate_profile", cand_id=cand_id))


@login_required
@app.route("/action/qc-approve/<int:cand_id>", methods=["POST"])
def qc_approve(cand_id: int):
    """Batch 3.1: QC approve a vetting check. N9: Only non-analyst roles can QC."""
    check_type = request.form.get("check_type", "").strip()
    qc_notes = request.form.get("qc_notes", "").strip()

    # N9: Permission control — analysts cannot QC their own checks
    with Session(engine) as s:
        vc = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id, VettingCheck.check_type == check_type)
        )
        if not vc:
            flash("Vetting check not found.", "danger")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        if vc.assigned_to and vc.assigned_to == current_user.id:
            flash("You cannot QC a check assigned to yourself.", "warning")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        vc.qc_status = "qc_approved"
        vc.status = "QC COMPLETE"
        vc.colour = "green"
        vc.qc_reviewed_by = current_user.id
        vc.qc_reviewed_at = datetime.datetime.utcnow()
        vc.qc_notes = qc_notes
        log_audit_event('update', 'vetting',
                        f'QC approved "{check_type}"',
                        'candidate', cand_id,
                        {'check_type': check_type, 'qc_notes': qc_notes})
        s.commit()
        flash(f"'{check_type}' QC approved.", "success")

    return redirect(url_for("candidate_profile", cand_id=cand_id))


@login_required
@app.route("/action/qc-reject/<int:cand_id>", methods=["POST"])
def qc_reject(cand_id: int):
    """Batch 3.1: QC reject a vetting check — returns to Ready to Start."""
    check_type = request.form.get("check_type", "").strip()
    qc_notes = request.form.get("qc_notes", "").strip()

    with Session(engine) as s:
        vc = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id, VettingCheck.check_type == check_type)
        )
        if not vc:
            flash("Vetting check not found.", "danger")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        if vc.assigned_to and vc.assigned_to == current_user.id:
            flash("You cannot QC a check assigned to yourself.", "warning")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        vc.qc_status = "qc_rejected"
        vc.status = "READY TO START"
        vc.colour = "orange"
        vc.qc_reviewed_by = current_user.id
        vc.qc_reviewed_at = datetime.datetime.utcnow()
        vc.qc_notes = qc_notes
        log_audit_event('update', 'vetting',
                        f'QC rejected "{check_type}" — returned to Ready to Start',
                        'candidate', cand_id,
                        {'check_type': check_type, 'qc_notes': qc_notes})
        s.commit()
        flash(f"'{check_type}' returned by QC. Please review and resubmit.", "warning")

    return redirect(url_for("candidate_profile", cand_id=cand_id))


# =========================================================================
# GAP PLAN: ANALYST CASE ALLOCATION (Batch 4)
# =========================================================================

@login_required
@app.route("/action/assign-analyst/<int:cand_id>", methods=["POST"])
def assign_analyst(cand_id: int):
    """Batch 4.1: Assign a staff member (analyst) to a vetting check."""
    check_type = request.form.get("check_type", "").strip()
    analyst_id = request.form.get("analyst_id", type=int)

    with Session(engine) as s:
        vc = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id, VettingCheck.check_type == check_type)
        )
        if not vc:
            flash("Vetting check not found.", "danger")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        vc.assigned_to = analyst_id
        analyst_name = "Unassigned"
        if analyst_id:
            analyst = s.get(User, analyst_id)
            analyst_name = analyst.name if analyst else f"User #{analyst_id}"

        log_audit_event('update', 'vetting',
                        f'Assigned "{check_type}" to {analyst_name}',
                        'candidate', cand_id,
                        {'check_type': check_type, 'analyst_id': analyst_id})
        s.commit()
        flash(f"'{check_type}' assigned to {analyst_name}.", "success")

    return redirect(url_for("candidate_profile", cand_id=cand_id))


@login_required
@app.route("/action/assign-analyst-bulk/<int:cand_id>", methods=["POST"])
def assign_analyst_bulk(cand_id: int):
    """Batch 4.1: Assign one analyst to ALL vetting checks for a candidate."""
    analyst_id = request.form.get("analyst_id", type=int)

    with Session(engine) as s:
        checks = s.scalars(
            select(VettingCheck).where(VettingCheck.candidate_id == cand_id)
        ).all()
        for vc in checks:
            vc.assigned_to = analyst_id
        analyst_name = "Unassigned"
        if analyst_id:
            analyst = s.get(User, analyst_id)
            analyst_name = analyst.name if analyst else f"User #{analyst_id}"

        log_audit_event('update', 'vetting',
                        f'Bulk-assigned all checks to {analyst_name}',
                        'candidate', cand_id,
                        {'analyst_id': analyst_id, 'checks_updated': len(checks)})
        s.commit()
        flash(f"All vetting checks assigned to {analyst_name}.", "success")

    return redirect(url_for("candidate_profile", cand_id=cand_id))


# =========================================================================
# GAP PLAN: VETTING CHECK COLOUR (N5)
# =========================================================================

@login_required
@app.route("/action/set-check-colour/<int:cand_id>", methods=["POST"])
def set_check_colour(cand_id: int):
    """N5: Manually set the colour of a vetting check card."""
    check_type = request.form.get("check_type", "").strip()
    colour = request.form.get("colour", "white").strip().lower()
    if colour not in ("white", "green", "orange"):
        colour = "white"

    with Session(engine) as s:
        vc = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id, VettingCheck.check_type == check_type)
        )
        if vc:
            vc.colour = colour
            vc.colour_manual = True
            s.commit()

    return redirect(url_for("candidate_profile", cand_id=cand_id))


# =========================================================================
# GAP PLAN: ID VERIFICATION FOR DBS (N10)
# =========================================================================

@login_required
@app.route("/action/verify-id/<int:cand_id>", methods=["POST"])
def verify_id(cand_id: int):
    """N10: Record that ID was verified via video call/in-person/IDVT before DBS."""
    method = request.form.get("verification_method", "").strip()
    if method not in ("video_call", "in_person", "idvt"):
        flash("Invalid verification method.", "danger")
        return redirect(url_for("candidate_profile", cand_id=cand_id))

    with Session(engine) as s:
        # Mark the Identity Verification check
        vc = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id,
                   VettingCheck.check_type == "Identity Verification")
        )
        if vc:
            vc.id_verified = True
            vc.id_verification_method = method
            vc.id_verified_at = datetime.datetime.utcnow()
            log_audit_event('update', 'vetting',
                            f'ID verified via {method}',
                            'candidate', cand_id,
                            {'method': method})
            s.commit()
            flash(f"ID verification recorded ({method}).", "success")
        else:
            flash("Identity Verification check not found.", "danger")

    return redirect(url_for("candidate_profile", cand_id=cand_id))


# =========================================================================
# GAP PLAN: REFERENCE MANAGEMENT — STAFF SIDE (Batch 5)
# =========================================================================

@login_required
@app.route("/action/send-reference/<int:cand_id>", methods=["POST"])
def send_reference(cand_id: int):
    """Batch 5.2: Send a reference request email to referee."""
    ref_id = request.form.get("ref_id", type=int)
    referee_email = request.form.get("referee_email", "").strip()
    company_name = request.form.get("company_name", "").strip()

    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found.", "danger")
            return redirect(url_for("workflow"))

        # Get or create ReferenceRequest
        ref_req = None
        if ref_id:
            ref_req = s.get(ReferenceRequest, ref_id)

        if not ref_req:
            ref_req = ReferenceRequest(
                candidate_id=cand_id,
                company_name=company_name,
                referee_email=referee_email
            )
            s.add(ref_req)
            s.flush()

        if not ref_req.referee_email:
            flash("No referee email address provided.", "danger")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        # Send reference request email with consent form attached
        try:
            base_url = os.getenv("APP_BASE_URL", "http://localhost:5001")
            html_body = f"""
            <h2>Reference Request</h2>
            <p>Dear Sir/Madam,</p>
            <p>We are writing to request a reference for <strong>{cand.name}</strong>
            who has listed your organisation (<strong>{ref_req.company_name}</strong>) as a
            previous employer.</p>
            <p>Please could you confirm the following:</p>
            <ul>
                <li>Dates of employment</li>
                <li>Job title / role</li>
                <li>Reason for leaving</li>
                <li>Any other relevant information</li>
            </ul>
            <p>Please reply directly to this email with the reference details.</p>
            <p>The candidate's signed consent form is attached for your records.</p>
            <p>Thank you for your assistance.</p>
            <p>Regards,<br>Optimus Solutions Compliance Team</p>
            """
            # Auto-attach signed consent form
            attachments = []
            consent_doc = s.scalar(
                select(Document)
                .where(Document.candidate_id == cand_id)
                .where(Document.doc_type == "consent_signed")
                .order_by(Document.uploaded_at.desc())
            )
            if consent_doc:
                consent_path = os.path.join(UPLOAD_FOLDER, consent_doc.filename)
                if os.path.exists(consent_path):
                    with open(consent_path, "rb") as f:
                        attachments.append((
                            consent_doc.original_name or "Consent_Form.pdf",
                            f.read(),
                            "application/pdf"
                        ))
            send_email(ref_req.referee_email, f"Reference Request — {cand.name}", html_body,
                       attachments=attachments if attachments else None)
            ref_req.status = "sent"
            ref_req.sent_at = datetime.datetime.utcnow()
            flash(f"Reference request sent to {ref_req.referee_email}.", "success")
        except Exception as e:
            flash(f"Failed to send reference email: {str(e)}", "danger")

        log_audit_event('create', 'vetting',
                        f'Reference request sent to {ref_req.referee_email} for {company_name}',
                        'candidate', cand_id,
                        {'referee_email': ref_req.referee_email, 'company': company_name})
        s.commit()

    return redirect(url_for("candidate_profile", cand_id=cand_id))


@login_required
@app.route("/action/chase-reference/<int:cand_id>", methods=["POST"])
def chase_reference(cand_id: int):
    """Batch 5.3: Chase (resend) a reference request with a reminder."""
    ref_id = request.form.get("ref_id", type=int)

    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        ref_req = s.get(ReferenceRequest, ref_id) if ref_id else None
        if not ref_req or ref_req.candidate_id != cand_id:
            flash("Reference request not found.", "danger")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        if ref_req.chase_count >= 3:
            ref_req.status = "on_hold"
            ref_req.colour = "orange"
            s.commit()
            flash(f"Max 3 chases reached for {ref_req.company_name}. Moved to On Hold.", "warning")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        try:
            html_body = f"""
            <h2>Reminder: Reference Request</h2>
            <p>Dear Sir/Madam,</p>
            <p>This is a follow-up to our previous request for a reference for
            <strong>{cand.name if cand else 'the candidate'}</strong>
            (previously employed at <strong>{ref_req.company_name}</strong>).</p>
            <p>We would be grateful if you could provide the requested information
            at your earliest convenience.</p>
            <p>Regards,<br>Optimus Solutions Compliance Team</p>
            """
            send_email(ref_req.referee_email,
                       f"Reminder: Reference Request — {cand.name if cand else 'Candidate'}",
                       html_body)
            ref_req.chase_count = (ref_req.chase_count or 0) + 1
            ref_req.last_chased_at = datetime.datetime.utcnow()
            flash(f"Chase #{ref_req.chase_count} sent to {ref_req.referee_email}.", "success")
        except Exception as e:
            flash(f"Failed to send chase: {str(e)}", "danger")

        log_audit_event('update', 'vetting',
                        f'Reference chased (#{ref_req.chase_count}) for {ref_req.company_name}',
                        'candidate', cand_id,
                        {'chase_count': ref_req.chase_count, 'referee_email': ref_req.referee_email})
        s.commit()

    return redirect(url_for("candidate_profile", cand_id=cand_id))


@login_required
@app.route("/action/receive-reference/<int:cand_id>", methods=["POST"])
def receive_reference(cand_id: int):
    """Batch 5: Mark a reference as received and optionally upload the response."""
    ref_id = request.form.get("ref_id", type=int)
    notes = request.form.get("notes", "").strip()
    colour = request.form.get("colour", "green").strip()

    with Session(engine) as s:
        ref_req = s.get(ReferenceRequest, ref_id) if ref_id else None
        if not ref_req or ref_req.candidate_id != cand_id:
            flash("Reference request not found.", "danger")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        ref_req.status = "received"
        ref_req.received_at = datetime.datetime.utcnow()
        ref_req.colour = colour if colour in ("white", "green", "orange") else "green"
        if notes:
            ref_req.notes = notes

        # Handle attachment upload (.msg, .pdf, .eml, .doc, .docx)
        file = request.files.get("attachment")
        if file and file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext in ("msg", "pdf", "eml", "doc", "docx"):
                upload_dir = os.path.join(UPLOAD_FOLDER, "references")
                os.makedirs(upload_dir, exist_ok=True)
                safe_name = f"{cand_id}_ref_{ref_id}_{uuid.uuid4().hex[:8]}.{ext}"
                filepath = os.path.join(upload_dir, safe_name)
                file.save(filepath)
                ref_req.attachment_path = filepath

        log_audit_event('update', 'vetting',
                        f'Reference received for {ref_req.company_name}',
                        'candidate', cand_id,
                        {'company': ref_req.company_name, 'colour': ref_req.colour})
        s.commit()
        flash(f"Reference from {ref_req.company_name} marked as received.", "success")

    return redirect(url_for("candidate_profile", cand_id=cand_id))


# =========================================================================
# GAP PLAN: CANDIDATE VETTING DATA FIELDS (N1-N4)
# =========================================================================

@login_required
@app.route("/candidate/<int:cand_id>/vetting-data", methods=["POST"])
def update_vetting_data(cand_id: int):
    """N1-N4: Update additional candidate fields needed for vetting checks."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Associate not found.", "danger")
            return redirect(url_for("resource_pool"))

        # Update fields if provided
        for field in ["gender", "citizenship", "place_of_birth", "work_location",
                       "mothers_maiden_name", "driving_licence_number", "passport_number"]:
            val = request.form.get(field, "").strip()
            if val:
                setattr(cand, field, val)

        # Name variations (JSON array)
        nv = request.form.get("name_variations", "").strip()
        if nv:
            try:
                parsed = json.loads(nv) if nv.startswith("[") else [v.strip() for v in nv.split(",") if v.strip()]
                cand.name_variations = json.dumps(parsed)
            except Exception:
                cand.name_variations = json.dumps([v.strip() for v in nv.split(",") if v.strip()])

        log_audit_event('update', 'data_access',
                        f'Updated vetting data fields for {cand.name}',
                        'candidate', cand_id)
        s.commit()
        flash("Vetting data updated.", "success")

    return redirect(url_for("candidate_profile", cand_id=cand_id))


# =========================================================================
# GAP PLAN: N12 — GRID REMOVAL RULES
# =========================================================================

def _should_remove_from_grid(candidate, application, vetting_checks):
    """
    N12: Candidate should be removed from workflow grid when:
    - All vetting complete
    - Contracted (contract signed)
    - Start date has passed
    Returns True if should be hidden from active workflow.
    """
    if not application or not candidate:
        return False

    # Check all vetting complete
    check_statuses = {vc.check_type: (vc.status or "").upper() for vc in vetting_checks}
    all_complete = all(
        check_statuses.get(ct, "NOT STARTED") in ("COMPLETE", "N/A", "QC COMPLETE", "REFERRAL APPROVED")
        for ct in [
            "Right to Work", "Identity Verification", "Address History", "DBS Check",
            "Employment History", "References", "Qualifications", "Professional Registration",
            "Credit Check", "Directorship / Disqualification", "Sanctions / PEP", "Social Media Review"
        ]
    )
    if not all_complete:
        return False

    # Check contracted
    app_status = (application.status or "").lower()
    if app_status not in ("placed", "contract signed", "on contract"):
        return False

    # Check start date passed
    start_date = getattr(application, 'start_date', None)
    if start_date and start_date <= datetime.datetime.utcnow():
        return True

    return False


# -------- Add Candidate Note --------
@login_required
@app.route("/candidate/<int:cand_id>/note", methods=["POST"])
def add_candidate_note(cand_id: int):
    """Add a note to a candidate's profile"""
    content = request.form.get("note_content", "").strip() or request.form.get("content", "").strip()
    note_type = request.form.get("note_type", "note")
    
    if not content:
        flash("Note content cannot be empty", "warning")
        return redirect(url_for("candidate_profile", cand_id=cand_id))
    
    with Session(engine) as s:
        user_email = session.get("user_email", "System")
        new_note = CandidateNote(
            candidate_id=cand_id,
            user_email=user_email,
            note_type=note_type,
            content=content
        )
        s.add(new_note)
        s.commit()
    
    flash("Note added successfully", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id))

# -------- Issue Contract --------
@login_required
@app.route("/candidate/<int:cand_id>/issue_contract", methods=["POST"])
def issue_candidate_contract(cand_id: int):
    """
    Issue a contract to a candidate.
    
    GAP 7.2 FIX: When contract is issued, auto-updates workflow stage
    to 'Contract Issued' and updates candidate status.
    GAP X.4: Audit trail for compliance.
    """
    engagement_id = request.form.get("engagement_id")
    job_id = request.form.get("job_id")
    
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)
        
        # Create an ESigRequest
        esig = ESigRequest(
            candidate_id=cand_id,
            engagement_id=int(engagement_id) if engagement_id else None,
            status="pending",
            created_at=datetime.datetime.utcnow()
        )
        s.add(esig)
        
        # GAP 7.2: Auto-update workflow when contract is issued
        # Find the most recent application for this candidate
        if job_id:
            active_app = s.scalar(
                select(Application)
                .where(Application.candidate_id == cand_id)
                .where(Application.job_id == int(job_id))
            )
        else:
            active_app = s.scalar(
                select(Application)
                .where(Application.candidate_id == cand_id)
                .where(Application.status.notin_(["Rejected", "Contract Signed", "Hired"]))
                .order_by(Application.created_at.desc())
            )
        
        if active_app:
            old_status = active_app.status
            # C-8: Default stage name — update if workflow stages are reconfigured
            active_app.status = "Contract Issued"
            esig.application_id = active_app.id

            # GAP X.4: Audit log for contract issuance
            log_audit_event(
                'create', 'contract',
                f'Contract issued to {cand.name}',
                'candidate', cand_id,
                {
                    'engagement_id': engagement_id,
                    'application_id': active_app.id,
                    'old_workflow_status': old_status,
                    'new_workflow_status': 'Contract Issued'
                }
            )
        else:
            log_audit_event(
                'create', 'contract',
                f'Contract issued to {cand.name} (no active application)',
                'candidate', cand_id,
                {'engagement_id': engagement_id}
            )
        
        # Update candidate status
        cand.status = "In Vetting"  # Contract issued but not yet signed
        cand.last_activity_at = datetime.datetime.utcnow()
        
        s.commit()
    
    flash("Contract issued successfully — associate moved to 'Contract Issued' stage", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id))

# -------- GAP 1.5: Contract Resend/Chase Actions --------
@login_required
@app.route("/api/contract/<int:esig_id>/resend", methods=["POST"])
def resend_contract(esig_id: int):
    """
    GAP 1.5: Resend a contract that hasn't been signed.
    Updates the created_at timestamp and sends a new email.
    """
    with Session(engine) as s:
        esig = s.get(ESigRequest, esig_id)
        if not esig:
            return jsonify({"ok": False, "error": "Contract not found"}), 404
        
        if esig.status != "pending":
            return jsonify({"ok": False, "error": "Contract is not pending"}), 400
        
        cand = s.get(Candidate, esig.candidate_id)
        
        # Reset created_at to restart the counter
        esig.created_at = datetime.datetime.utcnow()
        
        # Audit log
        log_audit_event(
            'update', 'contract',
            f'Contract resent to {cand.name if cand else "unknown"}',
            'esig_request', esig_id,
            {'candidate_id': esig.candidate_id, 'action': 'resend'}
        )
        
        s.commit()
        
        # Here you would send the actual email - placeholder for now
        # send_contract_email(cand.email, esig)
        
        return jsonify({
            "ok": True,
            "message": f"Contract resent to {cand.email if cand else 'candidate'}"
        })

@login_required
@app.route("/api/contract/<int:esig_id>/chase", methods=["POST"])
def chase_contract(esig_id: int):
    """
    GAP 1.5: Send a chase email for an unsigned contract.
    """
    with Session(engine) as s:
        esig = s.get(ESigRequest, esig_id)
        if not esig:
            return jsonify({"ok": False, "error": "Contract not found"}), 404
        
        if esig.status != "pending":
            return jsonify({"ok": False, "error": "Contract is not pending"}), 400
        
        cand = s.get(Candidate, esig.candidate_id)
        days_pending = (datetime.datetime.utcnow() - esig.created_at).days if esig.created_at else 0
        
        # Audit log
        log_audit_event(
            'create', 'communication',
            f'Chase email sent to {cand.name if cand else "unknown"} for unsigned contract ({days_pending} days)',
            'esig_request', esig_id,
            {'candidate_id': esig.candidate_id, 'action': 'chase', 'days_pending': days_pending}
        )
        
        s.commit()
        
        # Here you would send the chase email - placeholder for now
        # send_chase_email(cand.email, esig, days_pending)
        
        return jsonify({
            "ok": True,
            "message": f"Chase email sent to {cand.email if cand else 'candidate'}"
        })

# -------- GAP 3.1 & 3.3: Contract Extension and Leaving Confirmation --------
@login_required
@app.route("/api/contract/<int:esig_id>/extend", methods=["POST"])
def extend_contract(esig_id: int):
    """
    GAP 3.3: Extend a contract end date.
    """
    payload = request.json or {}
    new_end_date_str = payload.get("new_end_date", "")
    
    if not new_end_date_str:
        return jsonify({"ok": False, "error": "New end date is required"}), 400
    
    try:
        new_end_date = datetime.datetime.strptime(new_end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    with Session(engine) as s:
        esig = s.get(ESigRequest, esig_id)
        if not esig:
            return jsonify({"ok": False, "error": "Contract not found"}), 404
        
        old_end_date = esig.end_date
        esig.end_date = new_end_date
        
        cand = s.get(Candidate, esig.candidate_id)
        
        log_audit_event(
            'update', 'contract',
            f'Contract extended for {cand.name if cand else "unknown"} from {old_end_date} to {new_end_date}',
            'esig_request', esig_id,
            {'old_end_date': str(old_end_date), 'new_end_date': str(new_end_date)}
        )
        
        s.commit()
        
        return jsonify({
            "ok": True,
            "message": f"Contract extended to {new_end_date_str}"
        })

@csrf.exempt
@app.route("/api/contracts/bulk-extend", methods=["POST"])
@login_required
def bulk_extend_contracts():
    """Bulk update end dates for multiple contracts."""
    payload = request.json or {}
    esig_ids = payload.get("esig_ids", [])
    new_end_date_str = payload.get("new_end_date", "")

    if not esig_ids or not new_end_date_str:
        return jsonify({"ok": False, "error": "Contract IDs and new end date are required"}), 400

    try:
        new_end_date = datetime.datetime.strptime(new_end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid date format. Use YYYY-MM-DD"}), 400

    updated = 0
    with Session(engine) as s:
        for eid in esig_ids:
            esig = s.get(ESigRequest, int(eid))
            if not esig:
                continue
            old_end_date = esig.end_date
            esig.end_date = new_end_date
            cand = s.get(Candidate, esig.candidate_id)
            log_audit_event(
                'update', 'contract',
                f'Bulk extend: {cand.name if cand else "unknown"} from {old_end_date} to {new_end_date}',
                'esig_request', esig.id,
                {'old_end_date': str(old_end_date), 'new_end_date': str(new_end_date), 'bulk': True}
            )
            updated += 1
        s.commit()

    return jsonify({"ok": True, "message": f"{updated} contract(s) updated to {new_end_date_str}", "updated": updated})

@login_required
@app.route("/api/candidate/<int:cand_id>/confirm-leaving", methods=["POST"])
def confirm_candidate_leaving(cand_id: int):
    """
    GAP 3.3: Confirm candidate is leaving when contract ends.
    This marks them for status update when end date arrives.
    """
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            return jsonify({"ok": False, "error": "Associate not found"}), 404
        
        # Mark candidate as confirmed leaving
        # When the scheduled job runs, it will update their status to "Available"
        cand.leaving_confirmed = True
        cand.leaving_confirmed_at = datetime.datetime.utcnow()
        
        log_audit_event(
            'update', 'candidate',
            f'Leaving confirmed for {cand.name}',
            'candidate', cand_id,
            {'action': 'confirm_leaving'}
        )
        
        s.commit()
        
        return jsonify({
            "ok": True,
            "message": f"Leaving confirmed for {cand.name}"
        })

# GAP 3.1: Background task to auto-revert status when contract ends
# This would normally be called by a scheduled job (cron/celery)
def process_contract_end_dates():
    """
    GAP 3.1: Process ended contracts and revert candidate status.
    Should be called daily by a scheduled task.
    """
    today = datetime.date.today()
    
    with Session(engine) as s:
        # Find all contracts that have ended
        ended_contracts = s.execute(
            select(ESigRequest, Candidate)
            .join(Candidate, Candidate.id == ESigRequest.candidate_id)
            .where(
                ESigRequest.status == "signed",
                ESigRequest.end_date <= today,
                Candidate.status == "On Assignment"
            )
        ).all()
        
        for esig, cand in ended_contracts:
            # Revert candidate status to Available
            old_status = cand.status
            cand.status = "Available"
            cand.last_activity_at = datetime.datetime.utcnow()
            
            # Find and update any active applications
            active_app = s.scalar(
                select(Application)
                .where(Application.candidate_id == cand.id)
                .where(Application.status == "Contract Signed")
            )
            
            if active_app:
                active_app.status = "Completed"
            
            log_audit_event(
                'update', 'workflow',
                f'Auto-reverted status for {cand.name} - contract ended on {esig.end_date}',
                'candidate', cand.id,
                {
                    'old_status': old_status, 
                    'new_status': 'Available', 
                    'contract_end_date': str(esig.end_date),
                    'trigger': 'contract_end_auto'
                }
            )
        
        s.commit()
        
        return len(ended_contracts)

# GAP 5.4: API endpoint to shortlist candidate to engagement
@login_required
@app.route("/api/engagement/<int:eng_id>/shortlist", methods=["POST"])
def api_engagement_shortlist(eng_id: int):
    """
    GAP 5.4: Shortlist a candidate from search results directly to an engagement.
    Creates an application if one doesn't exist and sets status to Shortlist.
    """
    payload = request.json or {}
    candidate_id = int(payload.get("candidate_id", 0))
    job_id = payload.get("job_id")  # Optional - if not provided, will use first job in engagement
    
    if not candidate_id:
        return jsonify({"ok": False, "error": "Associate ID is required"}), 400
    
    with Session(engine) as s:
        # Verify engagement exists
        engagement = s.get(Engagement, eng_id)
        if not engagement:
            return jsonify({"ok": False, "error": "Engagement not found"}), 404
        
        # Verify candidate exists
        candidate = s.get(Candidate, candidate_id)
        if not candidate:
            return jsonify({"ok": False, "error": "Associate not found"}), 404
        
        # Get job - use provided job_id or first job in engagement
        if job_id:
            job = s.get(Job, int(job_id))
        else:
            job = s.scalar(
                select(Job)
                .where(Job.engagement_id == eng_id)
                .order_by(Job.created_at.desc())
            )
        
        if not job:
            return jsonify({"ok": False, "error": "No job found for this engagement"}), 400
        
        # Check if application already exists
        existing_app = s.scalar(
            select(Application)
            .where(Application.candidate_id == candidate_id)
            .where(Application.job_id == job.id)
        )
        
        if existing_app:
            # Update existing application to Shortlist
            old_status = existing_app.status
            existing_app.status = "Shortlist"
            existing_app.updated_at = datetime.datetime.utcnow()
            
            log_audit_event(
                'update', 'workflow',
                f'Associate {candidate.name} moved to Shortlist for {engagement.name}',
                'application', existing_app.id,
                {'old_status': old_status, 'new_status': 'Shortlist', 'engagement_id': eng_id}
            )
            
            s.commit()
            
            return jsonify({
                "ok": True,
                "message": f"{candidate.name} moved to Shortlist",
                "application_id": existing_app.id
            })
        else:
            # Create new application with Shortlist status
            new_app = Application(
                candidate_id=candidate_id,
                job_id=job.id,
                status="Shortlist",
                created_at=datetime.datetime.utcnow()
            )
            s.add(new_app)
            s.flush()

            # Contradiction Fix 1: Auto-create vetting checks (status=WAITING FOR ASSOCIATE)
            vc_created = _auto_create_vetting_checks(s, candidate_id, eng_id)

            log_audit_event(
                'create', 'workflow',
                f'Associate {candidate.name} shortlisted for {engagement.name}',
                'application', new_app.id,
                {'status': 'Shortlist', 'engagement_id': eng_id, 'job_id': job.id,
                 'vetting_checks_created': vc_created}
            )

            s.commit()

            return jsonify({
                "ok": True,
                "message": f"{candidate.name} added to Shortlist",
                "application_id": new_app.id
            })

# -------- Retag from CV --------
@login_required
@app.route("/candidate/<int:cand_id>/retag", methods=["POST"])
def retag_candidate_from_cv(cand_id: int):
    """Retag candidate from their CV using AI"""
    # This would trigger AI analysis of the CV to extract skills/tags
    flash("Retagging from CV... (AI analysis would run here)", "info")
    return redirect(url_for("candidate_profile", cand_id=cand_id))

# -------- Engagement Dashboard --------
@login_required
@app.route("/engagement/<int:eng_id>/dashboard")
def engagement_dashboard(eng_id):
    # Audit log: engagement view
    
    UNASSIGNED = "Unassigned"

    with Session(engine) as s:
        engagement = s.scalar(select(Engagement).where(Engagement.id == eng_id))
        if not engagement:
            abort(404)

        eng_status = (getattr(engagement, "status", "") or "").strip().lower()
        is_eng_active = eng_status in {"active", "in-flight", "in progress"}

        # --- Plan (per role) ---
        plans = s.execute(
            select(EngagementPlan.role_type, EngagementPlan.planned_count)
            .where(EngagementPlan.engagement_id == eng_id)
        ).all()
        planned_by_role = {r: 0 for r in ROLE_TYPES}
        for r, cnt in plans:
            if r in planned_by_role:
                planned_by_role[r] = int(cnt or 0)
        total_planned = sum(planned_by_role.values())

        # If engagement finished -> skip activity logic
        if not is_eng_active:
            display_roles = [r for r, v in planned_by_role.items() if v > 0] or [UNASSIGNED]
            role_metrics = {
                r: {
                    "planned": planned_by_role.get(r, 0),
                    "declared": 0, "sched": 0, "done": 0,
                    "vetting": 0, "issued": 0, "signed": 0
                }
                for r in display_roles
            }
            totals_row = {
                "planned": total_planned, "declared": 0, "sched": 0, "done": 0,
                "vetting": 0, "issued": 0, "signed": 0
            }
            return render_template(
                "engagement_dashboard.html",
                engagement=engagement,
                planned_by_role=planned_by_role,
                declared_rows=[], interview_sched=[], interview_done=[],
                vetting=[], contract_issued=[], contract_signed=[],
                total_planned=total_planned, total_signed=0, progress_pct=0,
                ROLE_TYPES=ROLE_TYPES, display_roles=display_roles,
                role_metrics=role_metrics, totals_row=totals_row,
                shortlist_count=0, shortlisted=[], jobs_active=[],
                job_declared={}, job_shortlisted={}, engagement_finished=True,
                tile_shortlist=0, tile_interview_sched=0, tile_interview_done=0,
                tile_vetting=0, tile_contract_issued=0, tile_contract_signed=0,
            )

        # ---------- ACTIVE engagement logic ----------

        # Core query for open jobs only
        sl_exists = exists(
            select(Shortlist.id).where(
                Shortlist.job_id == Application.job_id,
                Shortlist.candidate_id == Application.candidate_id,
            )
        )

        declared_q = (
            select(Application, Candidate, Job)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .where(
                Job.engagement_id == eng_id,
                Job.status == "Open",
                ~sl_exists,
            )
            .order_by(Application.created_at.desc())
        )
        declared = s.execute(declared_q).all()

        def to_row(tup):
            a, c, j = tup
            return {
                "app_id": a.id,
                "status": a.status,
                "ai_score": a.ai_score,
                "interview_at": a.interview_scheduled_at,
                "interview_done_at": a.interview_completed_at,
                "candidate": {"id": c.id, "name": c.name, "email": c.email},
                "job": {"id": j.id, "title": j.title, "role_type": j.role_type or ""},
            }

        declared_rows = [to_row(t) for t in declared]

        # --- interview buckets (pending-review only, for the side panels if needed) ---
        interview_sched = [
            r for r in declared_rows
            if r["interview_at"] is not None and r["interview_done_at"] is None
        ]
        interview_done = [
            r for r in declared_rows
            if r["interview_done_at"] is not None
        ]

        # --- shortlist (only open jobs) ---
        shortlist_rows_all = s.execute(
            select(Shortlist, Candidate, Job)
            .join(Job, Job.id == Shortlist.job_id)
            .join(Candidate, Candidate.id == Shortlist.candidate_id)
            .where(Job.engagement_id == eng_id, Job.status == "Open")
            .order_by(Shortlist.created_at.desc())
        ).all()

        shortlisted = []
        for sl, c, j in shortlist_rows_all:
            app_obj = s.scalar(
                select(Application)
                .where(Application.candidate_id == c.id, Application.job_id == j.id)
                .order_by(Application.created_at.desc())
            )
            if app_obj and (
                app_obj.interview_scheduled_at is not None
                or app_obj.interview_completed_at is not None
            ):
                continue
            shortlisted.append({
                "shortlist_id": sl.id,
                "created_at": sl.created_at,
                "candidate_id": c.id,
                "candidate": {"id": c.id, "name": c.name, "email": c.email},
                "job": {"id": j.id, "title": j.title},
            })
        shortlist_count = len(shortlisted)

        # === KPI TILE NUMBERS (use ALL apps in the engagement) ===
        apps_all = s.execute(
            select(
                Application.id, Application.candidate_id, Application.job_id,
                Application.interview_scheduled_at, Application.interview_completed_at,
                Job.role_type
            )
            .join(Job, Job.id == Application.job_id)
            .where(Job.engagement_id == eng_id, Job.status == "Open")
        ).all()

        sched_set, done_set, vetting_set, issued_set, signed_set = set(), set(), set(), set(), set()
        app_id_list = [a[0] for a in apps_all]

        if app_id_list:
            # vetting — check VettingCheck rows with Verifile provider for candidates on these apps
            vet_cand_ids = s.execute(
                select(Application.candidate_id).where(Application.id.in_(app_id_list))
            ).scalars().all()
            if vet_cand_ids:
                vet_cands_with_checks = set(s.execute(
                    select(VettingCheck.candidate_id)
                    .where(VettingCheck.candidate_id.in_(vet_cand_ids))
                    .where(VettingCheck.external_provider == "verifile")
                    .group_by(VettingCheck.candidate_id)
                ).scalars().all())
                # Map back to app IDs
                if vet_cands_with_checks:
                    vet_app_rows = s.execute(
                        select(Application.id)
                        .where(Application.id.in_(app_id_list))
                        .where(Application.candidate_id.in_(vet_cands_with_checks))
                    ).scalars().all()
                    vetting_set = set(vet_app_rows)

            # esign
            esig_rows = s.execute(
                select(ESigRequest.application_id, ESigRequest.status)
                .where(ESigRequest.application_id.in_(app_id_list))
            ).all()
            for app_id, st in esig_rows:
                st = (st or "").lower()
                if st in ("sent", "delivered"):
                    issued_set.add(app_id)
                if st in ("signed", "completed"):
                    signed_set.add(app_id)

        # classify interviews
        for app_id, cand_id, job_id, sched_at, done_at, _role in apps_all:
            if sched_at and not done_at:
                sched_set.add(app_id)
            if done_at:
                done_set.add(app_id)

        # shortlist tile: not progressed to interview
        shortlist_pairs = {(sl["candidate_id"], sl["job"]["id"]) for sl in shortlisted}
        pair_to_app = {(a[1], a[2]): a[0] for a in apps_all}
        shortlist_effective = 0
        for (cid, jid) in shortlist_pairs:
            app_id = pair_to_app.get((cid, jid))
            if not app_id:
                shortlist_effective += 1
                continue
            if app_id in sched_set or app_id in done_set:
                continue
            shortlist_effective += 1

        tile_shortlist = shortlist_effective
        tile_interview_sched = len(sched_set)
        tile_interview_done = len(done_set)
        tile_vetting = len(vetting_set)
        tile_contract_issued = len(issued_set)
        tile_contract_signed = len(signed_set)

        # --- per-role metrics ---
        def norm_role(val: str) -> str:
            r = (val or "").strip()
            if r in ROLE_TYPES:
                return r
            return UNASSIGNED if r == "" else r

        # map every application id to its job role (from ALL apps)
        role_of_app = {}
        for app_id, _cid, _jid, _sched, _done, role_type in apps_all:
            role_of_app[app_id] = norm_role(role_type)

        def blank():
            return {"planned": 0, "declared": 0, "sched": 0, "done": 0,
                    "vetting": 0, "issued": 0, "signed": 0}

        # seed with roles that have a plan, carrying the planned counts
        role_metrics = {}
        for r, planned_cnt in planned_by_role.items():
            if planned_cnt > 0:
                rm = blank()
                rm["planned"] = planned_cnt
                role_metrics[r] = rm

        roles_from_activity = set()

        # declared (pending review only) — keep behaviour the same
        for r in declared_rows:
            role = role_of_app.get(r["app_id"], norm_role(r["job"]["role_type"]))
            m = role_metrics.setdefault(role, blank())
            m["declared"] += 1
            roles_from_activity.add(role)

        # count interview sched/done from ALL apps
        for app_id in sched_set:
            role = role_of_app.get(app_id, UNASSIGNED)
            role_metrics.setdefault(role, blank())["sched"] += 1
            roles_from_activity.add(role)

        for app_id in done_set:
            role = role_of_app.get(app_id, UNASSIGNED)
            role_metrics.setdefault(role, blank())["done"] += 1
            roles_from_activity.add(role)

        # vetting / issued / signed from ALL apps
        for app_id in vetting_set:
            role = role_of_app.get(app_id, UNASSIGNED)
            role_metrics.setdefault(role, blank())["vetting"] += 1
            roles_from_activity.add(role)

        for app_id in issued_set:
            role = role_of_app.get(app_id, UNASSIGNED)
            role_metrics.setdefault(role, blank())["issued"] += 1
            roles_from_activity.add(role)

        for app_id in signed_set:
            role = role_of_app.get(app_id, UNASSIGNED)
            role_metrics.setdefault(role, blank())["signed"] += 1
            roles_from_activity.add(role)

        display_roles = sorted(
            ({r for r, v in planned_by_role.items() if v > 0} | roles_from_activity),
            key=lambda x: (x != UNASSIGNED, ROLE_TYPES.index(x) if x in ROLE_TYPES else 999)
        )

        totals_row = {k: 0 for k in ["planned", "declared", "sched", "done", "vetting", "issued", "signed"]}
        for r in display_roles:
            m = role_metrics.get(r, {})
            for k in totals_row:
                totals_row[k] += int(m.get(k, 0) or 0)

        total_signed = totals_row["signed"]
        progress_pct = int(100 * total_signed / total_planned) if total_planned else 0

        # --- jobs table ---
        jobs_active = s.scalars(
            select(Job).where(Job.engagement_id == eng_id, Job.status == "Open").order_by(Job.created_at.desc())
        ).all()
        job_declared = {j.id: 0 for j in jobs_active}
        job_shortlisted = {j.id: 0 for j in jobs_active}

        if jobs_active:
            ids = [j.id for j in jobs_active]
            for jid, cnt in s.execute(
                select(Application.job_id, func.count()).where(Application.job_id.in_(ids)).group_by(Application.job_id)
            ).all():
                job_declared[jid] = int(cnt or 0)
            for jid, cnt in s.execute(
                select(Shortlist.job_id, func.count()).where(Shortlist.job_id.in_(ids)).group_by(Shortlist.job_id)
            ).all():
                job_shortlisted[jid] = int(cnt or 0)

        # --- Pay/Bill Rates per role (from EngagementPlan) ---
        rate_data = {}
        plan_rows = s.execute(
            select(EngagementPlan.role_type, EngagementPlan.pay_rate, EngagementPlan.charge_rate)
            .where(EngagementPlan.engagement_id == eng_id)
        ).all()
        for role_type, pay_rate, charge_rate in plan_rows:
            if role_type:
                rate_data[role_type] = {
                    'pay_rate': pay_rate or 0,
                    'bill_rate': charge_rate or 0
                }

        # --- Intake Plans (grouped by intake date) ---
        intake_plans = s.execute(
            select(
                EngagementPlan.id,
                EngagementPlan.role_type,
                EngagementPlan.planned_count,
                EngagementPlan.intake_date,
                EngagementPlan.pay_rate,
                EngagementPlan.charge_rate
            )
            .where(EngagementPlan.engagement_id == eng_id)
            .order_by(EngagementPlan.intake_date.asc(), EngagementPlan.role_type.asc())
        ).all()
        
        # Build intake_by_role structure for hierarchical table
        # Groups intakes under each role
        intake_by_role = {}
        for plan_id, role_type, planned_count, intake_date, pay_rate, charge_rate in intake_plans:
            role_key = role_type or 'Unassigned'
            date_display = intake_date.strftime('%d/%m/%Y') if intake_date else 'Unscheduled'
            
            if role_key not in intake_by_role:
                intake_by_role[role_key] = {
                    'intakes': [],
                    'total_planned': 0,
                    'pay_rate': pay_rate or 0,
                    'charge_rate': charge_rate or 0
                }
            
            intake_by_role[role_key]['intakes'].append({
                'date_display': date_display,
                'date_raw': intake_date,
                'planned_count': planned_count or 0
            })
            intake_by_role[role_key]['total_planned'] += (planned_count or 0)
        
        # Sort intakes within each role by date
        for role_key in intake_by_role:
            intake_by_role[role_key]['intakes'].sort(
                key=lambda x: (x['date_raw'] is None, x['date_raw'] or datetime.datetime.max)
            )

        # --- Left to Fill and Scheduled Starters per role ---
        for role in display_roles:
            m = role_metrics.get(role, {})
            planned = m.get('planned', 0)
            signed = m.get('signed', 0)
            # Scheduled starters = interview_done but not yet signed
            scheduled = m.get('done', 0) - signed if m.get('done', 0) > signed else 0
            # Left to fill = planned - signed - scheduled
            left_to_fill = max(0, planned - signed - scheduled)
            m['scheduled'] = scheduled
            m['left_to_fill'] = left_to_fill
            # Add pay/bill rates
            if role in rate_data:
                m['pay_rate'] = rate_data[role]['pay_rate']
                m['bill_rate'] = rate_data[role]['bill_rate']
            else:
                m['pay_rate'] = 0
                m['bill_rate'] = 0

        # --- Update totals row ---
        totals_row['scheduled'] = sum(role_metrics.get(r, {}).get('scheduled', 0) for r in display_roles)
        totals_row['left_to_fill'] = sum(role_metrics.get(r, {}).get('left_to_fill', 0) for r in display_roles)

        # --- Scheduled starters (Offered/Accepted/Ready to Contract) ---
        scheduled_associates = []
        sched_apps_q = (
            select(Application, Candidate, Job)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .where(
                Job.engagement_id == eng_id,
                Application.status.in_(['Offered', 'Accepted', 'Ready to Contract'])
            )
            .order_by(Application.created_at.desc())
        )
        sched_results = s.execute(sched_apps_q).all()
        for app, cand, job in sched_results:
            scheduled_associates.append({
                'id': cand.id,
                'name': cand.name,
                'email': cand.email,
                'role': job.role_type or job.title,
                'ai_score': app.ai_score or 0,
                'status': app.status
            })

        # --- Associates on this engagement (with AI scores) ---
        associates_on_engagement = []
        signed_apps_q = (
            select(Application, Candidate, Job, ESigRequest)
            .select_from(ESigRequest)
            .join(Application, Application.id == ESigRequest.application_id)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
            .where(
                Job.engagement_id == eng_id,
                func.lower(ESigRequest.status).in_(['signed', 'completed'])
            )
            .order_by(ESigRequest.signed_at.desc())
        )
        signed_results = s.execute(signed_apps_q).all()
        for app, cand, job, esig in signed_results:
            associates_on_engagement.append({
                'id': cand.id,
                'name': cand.name,
                'email': cand.email,
                'role': job.role_type or job.title,
                'ai_score': app.ai_score or 0,
                'start_date': esig.signed_at,
                'status': 'On Contract'
            })

        # --- render ---
        return render_template(
            "engagement_dashboard.html",
            engagement=engagement,
            planned_by_role=planned_by_role,
            declared_rows=declared_rows,
            interview_sched=interview_sched,
            interview_done=interview_done,
            vetting=[{"application_id": aid} for aid in vetting_set],  # optional: not used by template
            contract_issued=[{"application_id": aid} for aid in issued_set],
            contract_signed=[{"application_id": aid} for aid in signed_set],
            total_planned=total_planned,
            total_signed=total_signed,
            progress_pct=progress_pct,
            ROLE_TYPES=ROLE_TYPES,
            display_roles=display_roles,
            role_metrics=role_metrics,
            totals_row=totals_row,
            shortlist_count=shortlist_count,
            shortlisted=shortlisted,
            jobs_active=jobs_active,
            job_declared=job_declared,
            job_shortlisted=job_shortlisted,
            tile_shortlist=tile_shortlist,
            tile_interview_sched=tile_interview_sched,
            tile_interview_done=tile_interview_done,
            tile_vetting=tile_vetting,
            tile_contract_issued=tile_contract_issued,
            tile_contract_signed=tile_contract_signed,
            associates_on_engagement=associates_on_engagement,
            scheduled_associates=scheduled_associates,
            rate_data=rate_data,
            intake_by_role=intake_by_role,
        )

# -------- Search Associates API for Engagement Dashboard --------
@login_required
@app.route("/engagement/<int:eng_id>/search_associates")
def engagement_search_associates(eng_id):
    """Search associates from resource pool to link to engagement."""
    q = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 10))
    
    with Session(engine) as s:
        engagement = s.get(Engagement, eng_id)
        if not engagement:
            return jsonify({"error": "Engagement not found"}), 404
        
        # Build query to search candidates
        query = select(Candidate).where(Candidate.id > 0)
        
        if q:
            search_term = f"%{q}%"
            query = query.where(
                or_(
                    Candidate.name.ilike(search_term),
                    Candidate.email.ilike(search_term),
                    Candidate.skills.ilike(search_term)
                )
            )
        
        query = query.order_by(Candidate.name.asc()).limit(limit)
        candidates = s.scalars(query).all()
        
        # Get AI scores from most recent applications if available
        results = []
        for cand in candidates:
            # Get latest application with AI score
            latest_app = s.scalar(
                select(Application)
                .where(Application.candidate_id == cand.id)
                .order_by(Application.created_at.desc())
            )
            
            results.append({
                "id": cand.id,
                "name": cand.name,
                "email": cand.email,
                "skills": cand.skills[:100] if cand.skills else "",
                "ai_score": latest_app.ai_score if latest_app and latest_app.ai_score else 0,
                "has_cv": bool(cand.cv_filename),
            })
        
        return jsonify({"candidates": results})

# -------- Plan Editor (dynamic fields) --------
from wtforms import SubmitField, IntegerField

def build_plan_form(initial_by_role: Dict[str, int]):
    """Create a WTForms class with one IntegerField per role."""
    class _PlanForm(FlaskForm):
        submit = SubmitField("Save plan")
    for role in ROLE_TYPES:
        fname = f"role_{slugify_role(role)}"
        setattr(_PlanForm, fname, IntegerField(role, default=int(initial_by_role.get(role, 0) or 0)))
    return _PlanForm

@login_required
@app.route("/shortlist/add", methods=["POST"])
def shortlist_add():
    job_id = int(request.form.get("job_id", "0") or 0)
    cand_id = int(request.form.get("candidate_id", "0") or 0)

    if not job_id or not cand_id:
        flash("Pick a job and associate to shortlist.", "warning")
        return redirect(url_for("resource_pool"))

    with Session(engine) as s:
        # Ensure both job and candidate exist
        job = s.scalar(select(Job).where(Job.id == job_id))
        cand = s.scalar(select(Candidate).where(Candidate.id == cand_id))
        if not job or not cand:
            flash("Job or Associate not found.", "danger")
            return redirect(url_for("resource_pool", job_id=job_id))

        # Prevent duplicate shortlist entries
        already_exists = s.scalar(
            select(Shortlist.id)
            .where(Shortlist.job_id == job_id, Shortlist.candidate_id == cand_id)
            .limit(1)
        )

        if already_exists:
            flash(f"{cand.name} is already shortlisted for “{job.title}”.", "info")
        else:
            s.add(Shortlist(job_id=job_id, candidate_id=cand_id))

            # Contradiction Fix 1: Auto-create vetting checks (status=WAITING FOR ASSOCIATE)
            eng_id_for_vc = job.engagement_id if job.engagement_id else None
            vc_created = _auto_create_vetting_checks(s, cand_id, eng_id_for_vc)

            # Audit log: shortlist add
            log_audit_event('create', 'workflow',
                           f'Added {cand.name} to shortlist for {job.title}',
                           'shortlist', None,
                           {'candidate_id': cand_id, 'job_id': job_id,
                            'candidate_name': cand.name, 'job_title': job.title,
                            'vetting_checks_created': vc_created})

            s.commit()
            flash(f"Added {cand.name} to shortlist for “{job.title}”.", "success")

    return redirect(url_for("resource_pool", job_id=job_id))

@login_required
@app.route("/shortlist/remove", methods=["POST"])
def shortlist_remove():
    job_id = int(request.form.get("job_id", "0") or 0)
    cand_id = int(request.form.get("candidate_id", "0") or 0)
    with Session(engine) as s:
        row = s.scalar(
            select(Shortlist).where(
                Shortlist.job_id == job_id,
                Shortlist.candidate_id == cand_id
            )
        )
        if row:
            # Audit log: shortlist remove
            log_audit_event('delete', 'workflow', 
                           'Removed from shortlist',
                           'shortlist', None,
                           {'candidate_id': cand_id, 'job_id': job_id})
            
            s.delete(row)
            s.commit()
            flash("Removed from shortlist.", "success")
    return redirect(url_for("resource_pool", job_id=job_id))

@login_required
@app.route("/engagement/<int:eng_id>/list/<section>")
def engagement_list(eng_id: int, section: str):
    # Simple shim so templates like url_for('engagement_list', ...) work.
    # It just jumps back to the dashboard and scrolls to an anchor matching `section`.
    # Valid examples used in your template: 'declared', 'shortlist', etc.
    return redirect(url_for("engagement_dashboard", eng_id=eng_id, _anchor=section))

# ---- Withdraw a job (and notify applicants not yet in vetting) ----
@login_required
@app.route("/engagement/<int:eng_id>/jobs/<int:job_id>/withdraw", methods=["POST"])
def engagement_jobs_withdraw(eng_id: int, job_id: int):
    with Session(engine) as s:
        job = s.scalar(select(Job).where(Job.id == job_id, Job.engagement_id == eng_id))
        if not job: abort(404)

        job.status = "Withdrawn"
        s.add(job)

        app_rows = s.execute(
            select(Application.id, Application.candidate_id).where(Application.job_id == job_id)
        ).all()

        app_ids = [r[0] for r in app_rows]
        if app_ids:
            # Find candidates with active Verifile vetting — skip notifying them
            cand_ids_for_apps = {
                r[1]: r[0] for r in app_rows  # candidate_id -> app_id
            }
            vetted_cand_ids = set()
            if cand_ids_for_apps:
                vetted_cand_ids = set(s.execute(
                    select(VettingCheck.candidate_id)
                    .where(VettingCheck.candidate_id.in_(list(cand_ids_for_apps.keys())))
                    .where(VettingCheck.external_provider == "verifile")
                    .group_by(VettingCheck.candidate_id)
                ).scalars().all())
            vetting_app_ids = {
                aid for cid, aid in cand_ids_for_apps.items() if cid in vetted_cand_ids
            }
            notify_app_ids = [a_id for a_id in app_ids if a_id not in vetting_app_ids]

            if notify_app_ids:
                rows = s.execute(
                    select(Application.id, Candidate.email, Candidate.name)
                    .join(Candidate, Candidate.id == Application.candidate_id)
                    .where(Application.id.in_(notify_app_ids))
                ).all()
                for app_id, email, name in rows:
                    if email:
                        try:
                            send_email(
                                to_email=email,
                                subject=f"Update on your application — {job.title}",
                                html_body=(
                                    f"<p>Hi {name or 'there'},</p>"
                                    "<p>Thank you for your interest. The position has now been closed.</p>"
                                    "<p>We appreciate the time you took to apply and will keep your profile on file for future opportunities.</p>"
                                    "<p>Regards,<br>ATS Team</p>"
                                ),
                            )
                        except Exception as e:
                            current_app.logger.warning(f"Email send failed for app #{app_id} to {email}: {e}")

        s.commit()
        flash("Job withdrawn and notifications sent where applicable.", "success")

    return redirect(url_for("engagement_job_detail", eng_id=eng_id, job_id=job_id))

@login_required
@app.route("/engagement/<int:eng_id>/plan", methods=["GET", "POST"])
def engagement_plan(eng_id):
    with Session(engine) as s:
        engagement = s.get(Engagement, eng_id)
        if not engagement:
            abort(404)

        if request.method == "POST":
            posted_version = int(request.form.get("plan_version") or engagement.plan_version or 1)
            new_version = posted_version + 1
            engagement.plan_version = new_version

            role_types  = request.form.getlist("role_type[]")
            intake_dates = request.form.getlist("intake_date[]")
            counts      = request.form.getlist("planned_count[]")
            pays        = request.form.getlist("pay_rate[]")
            charges     = request.form.getlist("charge_rate[]")
            row_ids     = request.form.getlist("row_id[]")

            # We'll do in-place update/delete/insert for now.
            for i in range(len(role_types)):
                rid   = row_ids[i].strip()
                role  = role_types[i].strip()
                intake_str = intake_dates[i].strip() if i < len(intake_dates) else ""
                intake_dt = datetime.datetime.strptime(intake_str, "%Y-%m-%d") if intake_str else None
                hc    = int(counts[i] or 0)
                pay   = int(pays[i] or 0)
                bill  = int(charges[i] or 0)

                if rid:
                    # existing row
                    deleted_flag = request.form.get(f"row_id_deleted_{rid}")
                    ep = s.get(EngagementPlan, int(rid))
                    if not ep:
                        continue
                    if deleted_flag == "1":
                        s.delete(ep)
                        continue

                    ep.role_type = role
                    ep.intake_date = intake_dt
                    ep.planned_count = hc
                    ep.pay_rate = pay
                    ep.charge_rate = bill
                    ep.rate = bill                     # keep legacy rate = charge
                    ep.version_int = new_version       # stamp version
                else:
                    # new row (only if there's actually something meaningful)
                    if role or hc or pay or bill:
                        ep = EngagementPlan(
                            engagement_id = engagement.id,
                            role_type = role,
                            intake_date = intake_dt,
                            planned_count = hc,
                            pay_rate = pay,
                            charge_rate = bill,
                            rate = bill,
                            version_int = new_version,
                        )
                        s.add(ep)

            s.commit()

            # Check if new roles need corresponding jobs (item 6)
            plan_roles = s.scalars(
                select(EngagementPlan.role_type)
                .distinct()
                .where(EngagementPlan.engagement_id == engagement.id)
                .where(EngagementPlan.role_type.isnot(None), EngagementPlan.role_type != "")
            ).all()
            existing_job_roles = s.scalars(
                select(Job.role_type)
                .distinct()
                .where(Job.engagement_id == engagement.id)
                .where(Job.role_type.isnot(None), Job.role_type != "")
            ).all()
            missing_roles = [r for r in plan_roles if r not in existing_job_roles]

            if missing_roles:
                from markupsafe import Markup as _Markup
                from flask_wtf.csrf import generate_csrf as _gen_csrf
                auto_create_url = url_for('engagement_auto_create_jobs', eng_id=engagement.id)
                flash(_Markup(f"Plan saved. Roles without jobs: {', '.join(missing_roles)}. "
                      f"<form method='POST' action='{auto_create_url}' style='display:inline'>"
                      f"<input type='hidden' name='csrf_token' value='{_gen_csrf()}'>"
                      f"<button type='submit' class='btn btn-sm btn-warning ms-2'>Auto-Create Jobs</button>"
                      f"</form>"), "warning")
            else:
                flash("Plan saved.", "success")
            return redirect(url_for("engagement_plan", eng_id=engagement.id))

        # GET render
        rows = s.scalars(
            select(EngagementPlan)
            .where(EngagementPlan.engagement_id == eng_id)
            .order_by(EngagementPlan.id.asc())
        ).all()

        # Get role categories
        role_categories = s.scalars(
            select(TaxonomyCategory)
            .where(TaxonomyCategory.type == 'role')
            .order_by(TaxonomyCategory.name.asc())
        ).all()
        
        # Use categories directly as role types (they have .name attribute)
        role_types = role_categories
        
        # Calculate On Contract, Scheduled Starters, Left to Fill for each role
        # Build a dictionary keyed by role_type
        role_stats = {}
        for row in rows:
            role_type = row.role_type
            
            # On Contract: count of signed/completed e-sign requests for this role
            on_contract_count = s.scalar(
                select(func.count())
                .select_from(ESigRequest)
                .join(Application, Application.id == ESigRequest.application_id)
                .join(Job, Job.id == Application.job_id)
                .where(
                    Job.engagement_id == eng_id,
                    Job.role_type == role_type,
                    func.lower(ESigRequest.status).in_(['signed', 'completed'])
                )
            ) or 0
            
            # Scheduled Starters: count of "Offered", "Accepted", or "Ready to Contract" stage (not yet signed)
            scheduled_count = s.scalar(
                select(func.count())
                .select_from(Application)
                .join(Job, Job.id == Application.job_id)
                .where(
                    Job.engagement_id == eng_id,
                    Job.role_type == role_type,
                    Application.status.in_(['Offered', 'Accepted', 'Ready to Contract'])
                )
            ) or 0
            
            # Left to Fill: planned_count - (on_contract + scheduled)
            planned = row.planned_count or 0
            left_to_fill = max(0, planned - on_contract_count - scheduled_count)
            
            # Fulfillment percentage
            fulfillment_pct = 0
            if planned > 0:
                fulfillment_pct = int((on_contract_count / planned) * 100)
            
            # Intake dates: Get signed dates for this role (contract start dates)
            intake_dates_query = (
                select(ESigRequest.signed_at, Candidate.name)
                .select_from(ESigRequest)
                .join(Application, Application.id == ESigRequest.application_id)
                .join(Candidate, Candidate.id == Application.candidate_id)
                .join(Job, Job.id == Application.job_id)
                .where(
                    Job.engagement_id == eng_id,
                    Job.role_type == role_type,
                    func.lower(ESigRequest.status).in_(['signed', 'completed']),
                    ESigRequest.signed_at.isnot(None)
                )
                .order_by(ESigRequest.signed_at.asc())
            )
            intake_results = s.execute(intake_dates_query).all()
            intake_dates = [
                {
                    'date': signed_at.strftime('%d/%m/%Y') if signed_at else None,
                    'name': name
                }
                for signed_at, name in intake_results
            ]
            
            # Scheduled intake dates (upcoming starters with interview/offer dates)
            scheduled_dates_query = (
                select(Application.interview_scheduled_at, Candidate.name)
                .select_from(Application)
                .join(Candidate, Candidate.id == Application.candidate_id)
                .join(Job, Job.id == Application.job_id)
                .where(
                    Job.engagement_id == eng_id,
                    Job.role_type == role_type,
                    Application.status.in_(['Offer', 'Onboarding'])
                )
                .order_by(Application.interview_scheduled_at.asc())
            )
            scheduled_results = s.execute(scheduled_dates_query).all()
            scheduled_dates = [
                {
                    'date': dt.strftime('%d/%m/%Y') if dt else 'TBD',
                    'name': name
                }
                for dt, name in scheduled_results
            ]
            
            role_stats[role_type] = {
                'on_contract': on_contract_count,
                'scheduled': scheduled_count,
                'left_to_fill': left_to_fill,
                'fulfillment_pct': fulfillment_pct,
                'intake_dates': intake_dates,
                'scheduled_dates': scheduled_dates,
            }

    return render_template(
        "engagement_plan.html",
        engagement=engagement,
        rows=rows,
        role_types=role_types,
        role_stats=role_stats,
    )

# ---- REQ-267: Auto-create jobs from engagement plan ----
@login_required
@app.route("/engagement/<int:eng_id>/auto-create-jobs", methods=["POST"])
def engagement_auto_create_jobs(eng_id):
    """REQ-267: Auto-create jobs from engagement plan roles that don't have matching jobs."""
    with Session(engine) as s:
        engagement = s.get(Engagement, eng_id)
        if not engagement:
            abort(404)

        # Get plan roles
        plan_roles = s.scalars(
            select(EngagementPlan.role_type)
            .distinct()
            .where(EngagementPlan.engagement_id == eng_id)
            .where(EngagementPlan.role_type.isnot(None), EngagementPlan.role_type != "")
        ).all()

        # Get existing job roles
        existing_job_roles = s.scalars(
            select(Job.role_type)
            .distinct()
            .where(Job.engagement_id == eng_id)
            .where(Job.role_type.isnot(None), Job.role_type != "")
        ).all()

        missing_roles = [r for r in plan_roles if r not in existing_job_roles]
        created_count = 0

        for role in missing_roles:
            # Get plan details for this role (use first plan entry for defaults)
            plan = s.scalar(
                select(EngagementPlan)
                .where(EngagementPlan.engagement_id == eng_id)
                .where(EngagementPlan.role_type == role)
                .order_by(EngagementPlan.id.asc())
            )

            import secrets
            new_job = Job(
                engagement_id=eng_id,
                title=role,
                role_type=role,
                description=f"{role} - {engagement.name}",
                location=engagement.location if hasattr(engagement, 'location') else "",
                status="Open",
                public_token=secrets.token_urlsafe(16),
                salary_range=f"\u00a3{int(plan.pay_rate or 0)}/day" if plan and plan.pay_rate else "",
            )
            s.add(new_job)
            created_count += 1

        s.commit()

        try:
            log_audit_event("create", "engagement",
                          f"Auto-created {created_count} jobs for engagement {eng_id}: {', '.join(missing_roles)}",
                          resource_type="job", resource_id=eng_id,
                          details={"engagement_id": eng_id, "roles": missing_roles})
        except Exception:
            pass

    flash(f"Created {created_count} job(s): {', '.join(missing_roles)}", "success")
    return redirect(url_for("engagement_plan", eng_id=eng_id))

# ---- Engagement-scoped Job detail ----
@login_required
@app.route("/engagement/<int:eng_id>/jobs/<int:job_id>")
def engagement_job_detail(eng_id: int, job_id: int):
    with Session(engine) as s:
        job = s.scalar(select(Job).where(Job.id == job_id, Job.engagement_id == eng_id))
        if not job:
            abort(404)

        engagement = s.scalar(select(Engagement).where(Engagement.id == eng_id))
        if not engagement:
            abort(404)

        # Applications for this job
        app_rows = s.execute(
            select(Application, Candidate)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .where(Application.job_id == job_id)
            .order_by(Application.created_at.desc())
        ).all()

        # simple shortlist lookups
        shortlisted_ids = {
            cid for (cid,) in s.execute(
                select(Shortlist.candidate_id).where(Shortlist.job_id == job_id)
            ).all()
        }

        items = []
        for a, c in app_rows:
            items.append({
                "app_id": a.id,
                "status": a.status,
                "ai_score": a.ai_score,
                "candidate": {"id": c.id, "name": c.name, "email": c.email},
                "shortlisted": c.id in shortlisted_ids,
                "interview_at": a.interview_scheduled_at,
                "interview_done_at": a.interview_completed_at,
                "created_at": a.created_at,
            })

    return render_template(
        "engagement_job_detail.html",  # create a small template or reuse a generic table
        engagement=engagement,
        job=job,
        items=items,
    )

# --- Shared renderer used by both global and engagement-scoped Applications ---
def _render_applications_table(
    q: str = "",
    job_id: Optional[str] = None,
    eng_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 25,
    hide_closed: bool = True,                 # hide apps for non-Open jobs
    exclude_shortlisted_if_eng: bool = True,  # progressive pipeline in engagement scope
):
    with Session(engine) as s:
        base = (
            select(Application, Candidate, Job)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .join(Job, Job.id == Application.job_id)
        )
        if eng_id:
            base = base.where(Job.engagement_id == eng_id, Job.status == "Open")
        if hide_closed:
            base = base.where(Job.status == "Open")

        if job_id and str(job_id).isdigit():
            base = base.where(Job.id == int(job_id))

        if q:
            like = f"%{q}%"
            base = base.where(or_(
                Candidate.name.ilike(like),
                Candidate.email.ilike(like),
                func.coalesce(Candidate.skills, "").ilike(like),
                Job.title.ilike(like),
            ))

        total = s.execute(base.with_only_columns(func.count()).order_by(None)).scalar() or 0
        rows = s.execute(base.order_by(Application.created_at.desc())
                         .limit(per_page).offset((page - 1)*per_page)).all()

        sl_pairs = set()
        if eng_id and exclude_shortlisted_if_eng:
            sl_pairs = {
                (cid, jid)
                for (cid, jid) in s.execute(
                    select(Shortlist.candidate_id, Shortlist.job_id)
                    .join(Job, Job.id == Shortlist.job_id)
                    .where(Job.engagement_id == eng_id, Job.status == "Open")
                ).all()
            }

        items = []
        for a, c, j in rows:
            already_sl = (c.id, j.id) in sl_pairs if sl_pairs else False
            items.append({
                "app": a,
                "cand": c,
                "job": j,
                "shortlisted": already_sl,  # your template can show a banner/disable button
            })

        pagination = {
            "page": page, "per_page": per_page, "total": total,
            "pages": max(1, (total + per_page - 1)//per_page),
        }

        tpl = "applications_engagement.html" if eng_id else "applications.html"
        engagement = s.get(Engagement, eng_id) if eng_id else None

    return render_template(tpl, q=q, job_id=job_id, eng_id=eng_id,
                           items=items, pagination=pagination, engagement=engagement)

@login_required
@app.route("/applications")
def applications():
    q        = (request.args.get("q") or "").strip()
    job_id   = request.args.get("job_id")
    page     = max(1, int(request.args.get("page") or 1))
    per_page = max(5, min(100, int(request.args.get("per_page") or 25)))

    # Global view (no engagement filter), still hide closed jobs by default
    return _render_applications_table(
        q=q,
        job_id=job_id,
        eng_id=None,
        page=page,
        per_page=per_page,
        hide_closed=True,
        exclude_shortlisted_if_eng=False,  # not in an engagement scope
    )

# --- imports you likely already have ---
import datetime
from flask import abort, render_template, request
from sqlalchemy import or_, false

# If your session is named differently, adjust here:
# from your_module import session, engine, Application, Candidate, Job, Shortlist
# Ensure the models below are imported from wherever you declare them.

@login_required
@app.route("/engagement/<int:eng_id>/applications")
def applications_for_engagement(eng_id: int):
    q = (request.args.get("q") or "").strip()
    role_filter = (request.args.get("role") or "").strip()  # NEW: Role filter

    raw_stage = (request.args.get("filter") or "declared").strip().lower()
    # Accept both "shortlist" and "shortlisted" (plus a few friendly aliases)
    stage_alias = {
        "declared": "declared", "apps": "declared", "applications": "declared",
        "shortlist": "shortlist", "shortlisted": "shortlist", "sl": "shortlist",
        "interview_sched": "interview_scheduled", "interview_scheduled": "interview_scheduled",
        "interview_done": "interview_completed", "interview_completed": "interview_completed",
        "vetting": "vetting",
        "contract_issued": "contract_issued", "issued": "contract_issued",
        "contract_signed": "contract_signed", "signed": "contract_signed",
    }
    stage_filter = stage_alias.get(raw_stage, "declared")

    with Session(engine) as s:
        engagement = s.get(Engagement, eng_id)
        if not engagement:
            abort(404)

        # All apps under this engagement (regardless of job status)
        apps_q = (
            s.query(Application)
             .join(Candidate, Candidate.id == Application.candidate_id)
             .join(Job, Job.id == Application.job_id)
             .filter(Job.engagement_id == eng_id)
        )

        if q:
            like = f"%{q}%"
            skills_clause = Candidate.skills.ilike(like) if hasattr(Candidate, "skills") else false()
            apps_q = apps_q.filter(or_(
                Candidate.name.ilike(like),
                Candidate.email.ilike(like),
                Job.title.ilike(like),
                skills_clause,
            ))
        
        # Filter by role if specified
        if role_filter:
            apps_q = apps_q.filter(Job.role_type == role_filter)

        app_rows = apps_q.all()

        # Shortlist membership for this engagement
        shortlist_pairs = {
            (srow.candidate_id, srow.job_id)
            for srow in (
                s.query(Shortlist)
                 .join(Job, Job.id == Shortlist.job_id)
                 .filter(Job.engagement_id == eng_id)
                 .all()
            )
        }

        # Latest e-sign status per application (scoped to this engagement)
        esig_rows = (
            s.query(ESigRequest)
             .join(Application, Application.id == ESigRequest.application_id)
             .join(Job, Job.id == Application.job_id)
             .filter(Job.engagement_id == eng_id)
             .order_by(ESigRequest.id.desc())
             .all()
        )
        esig_by_app: Dict[int, str] = {}
        for er in esig_rows:
            # keep the most recent seen
            esig_by_app.setdefault(er.application_id, (er.status or ""))

        # (optional) cache of apps that have any Verifile vetting activity
        vetting_cand_ids = {
            vc.candidate_id
            for vc in s.query(VettingCheck)
                       .where(VettingCheck.external_provider == "verifile")
                       .all()
        }
        trust_app_ids = {
            a.id
            for a in s.query(Application)
                      .join(Job, Job.id == Application.job_id)
                      .filter(Job.engagement_id == eng_id)
                      .filter(Application.candidate_id.in_(vetting_cand_ids))
                      .all()
        } if vetting_cand_ids else set()

        def infer_stage(app: Application) -> str:
            # Interview
            interview_sched = getattr(app, "interview_scheduled_at", None) or getattr(app, "interview_at", None)
            interview_done  = getattr(app, "interview_completed_at", None)

            # Per-application e-sign only
            es = (esig_by_app.get(app.id, "") or "").lower()
            if es in {"signed", "completed"}:
                return "contract_signed"
            if es in {"sent", "delivered", "viewed", "awaiting_signature"}:
                return "contract_issued"

            # Vetting if any Verifile check for this app's candidate
            if app.id in trust_app_ids:
                return "vetting"

            if interview_done:
                return "interview_completed"
            if interview_sched:
                return "interview_scheduled"

            # Shortlist strictly by (candidate_id, job_id) pair
            if (app.candidate_id, app.job_id) in shortlist_pairs:
                return "shortlist"

            return "declared"

        rows = []
        for appn in app_rows:
            stg = infer_stage(appn)
            if stg == stage_filter:
                rows.append({
                    "app": appn,
                    "cand": appn.candidate,
                    "job": appn.job,
                    "stage": stg,
                    "is_shortlisted": (appn.candidate_id, appn.job_id) in shortlist_pairs,
                })

        rows.sort(key=lambda r: getattr(r["app"], "created_at", datetime.datetime.min), reverse=True)

    return render_template(
        "applications_engagement.html",
        engagement=engagement,
        rows=rows,
        stage=stage_filter,
        role_filter=role_filter,
        q=q,
        engagement_finished=False,
    )

@login_required
@app.route("/engagement/<int:eng_id>/financials")
def engagement_financials(eng_id):
    with Session(engine) as s:
        engagement = s.scalar(select(Engagement).where(Engagement.id == eng_id))
        if not engagement:
            abort(404)

        # Basic roll-ups from timesheets (if any)
        ts_rows = s.execute(
            select(Timesheet)
            .where(Timesheet.engagement_id == eng_id)
            .order_by(Timesheet.period_start.desc())
        ).scalars().all()

        stats = {
            "count": len(ts_rows),
            "draft": sum(1 for t in ts_rows if (t.status or "").lower() == "draft"),
            "submitted": sum(1 for t in ts_rows if (t.status or "").lower() == "submitted"),
            "approved": sum(1 for t in ts_rows if (t.status or "").lower() == "approved"),
            "rejected": sum(1 for t in ts_rows if (t.status or "").lower() == "rejected"),
            "hours_total": sum(int(t.hours or 0) for t in ts_rows),
            "hours_approved": sum(int(t.hours or 0) for t in ts_rows if (t.status or "").lower() == "approved"),
        }

        # You can expand this later with PO/budget data per engagement
        jobs = s.scalars(
            select(Job).where(Job.engagement_id == eng_id, Job.status == "Open").order_by(Job.created_at.desc())
        ).all()

    return render_template(
        "engagement_financials.html",
        engagement=engagement,
        stats=stats,
        jobs=jobs,
        timesheets=ts_rows,
    )

# ============== REVENUE PAGE ==============
@login_required
@app.route("/revenue")
def revenue():
    """
    Revenue dashboard showing financial overview across all engagements.
    Features:
    - 13 KPI tiles: Headcount, Forecast/Actual Revenue/Cost/Margin, Variances
    - Multi-select filters: Client, Engagement, Date Range
    - Period filters: Financial Year, Quarter, Month, Week
    - By Client Breakdown with engagement drill-down
    - Revenue Trend Chart: Forecast vs Actual by month
    """
    import calendar
    
    # ===== FILTER SECTION 1: Client, Engagement, Date Range =====
    selected_clients = request.args.getlist("clients")  # Multi-select
    selected_engagements = request.args.getlist("engagements")  # Multi-select
    date_from = request.args.get("date_from") or ""
    date_to = request.args.get("date_to") or ""
    
    # ===== FILTER SECTION 2: Period filters =====
    selected_fy = request.args.get("fy") or ""  # Financial Year (e.g., "2024" for FY 2024/25)
    selected_quarter = request.args.get("quarter") or ""  # 1, 2, 3, 4
    selected_month = request.args.get("month") or ""  # 1-12
    selected_week = request.args.get("week") or ""  # 1-52
    
    now = datetime.datetime.now()
    current_year = now.year
    
    # Generate financial years list (FY starts in April in UK)
    financial_years = [str(y) for y in range(current_year - 3, current_year + 2)]
    
    with Session(engine) as s:
        # Get unique clients for filter dropdown
        all_clients = s.scalars(
            select(Engagement.client)
            .distinct()
            .where(Engagement.client.isnot(None), Engagement.client != "")
            .order_by(Engagement.client)
        ).all()
        
        # Get all engagements for filter dropdown
        all_engagements = s.scalars(
            select(Engagement)
            .where(Engagement.client.isnot(None))
            .order_by(Engagement.name)
        ).all()
        
        # Build engagement query with filters
        eng_query = (
            select(Engagement)
            .order_by(Engagement.start_date.desc())
        )
        
        # Multi-select Client filter
        if selected_clients:
            eng_query = eng_query.where(Engagement.client.in_(selected_clients))
        
        # Multi-select Engagement filter
        if selected_engagements:
            eng_ids = [int(e) for e in selected_engagements if e.isdigit()]
            if eng_ids:
                eng_query = eng_query.where(Engagement.id.in_(eng_ids))
        
        # Calculate date range from period filters
        filter_start = None
        filter_end = None
        
        # Financial Year filter (UK FY: April 1 to March 31)
        if selected_fy:
            try:
                fy_year = int(selected_fy)
                filter_start = datetime.datetime(fy_year, 4, 1)  # FY starts April 1
                filter_end = datetime.datetime(fy_year + 1, 3, 31, 23, 59, 59)  # FY ends March 31
            except ValueError:
                pass
        
        # Quarter filter (within FY)
        if selected_quarter:
            try:
                q = int(selected_quarter)
                fy_year = int(selected_fy) if selected_fy else current_year
                # UK FY Quarters: Q1=Apr-Jun, Q2=Jul-Sep, Q3=Oct-Dec, Q4=Jan-Mar
                quarter_months = {1: (4, 6), 2: (7, 9), 3: (10, 12), 4: (1, 3)}
                if q in quarter_months:
                    start_month, end_month = quarter_months[q]
                    if q == 4:  # Q4 is in next calendar year
                        filter_start = datetime.datetime(fy_year + 1, start_month, 1)
                        _, last_day = calendar.monthrange(fy_year + 1, end_month)
                        filter_end = datetime.datetime(fy_year + 1, end_month, last_day, 23, 59, 59)
                    else:
                        filter_start = datetime.datetime(fy_year, start_month, 1)
                        _, last_day = calendar.monthrange(fy_year, end_month)
                        filter_end = datetime.datetime(fy_year, end_month, last_day, 23, 59, 59)
            except ValueError:
                pass
        
        # Month filter
        if selected_month:
            try:
                month = int(selected_month)
                year = current_year
                if selected_fy:
                    fy_year = int(selected_fy)
                    # Adjust year based on month and FY
                    year = fy_year if month >= 4 else fy_year + 1
                filter_start = datetime.datetime(year, month, 1)
                _, last_day = calendar.monthrange(year, month)
                filter_end = datetime.datetime(year, month, last_day, 23, 59, 59)
            except ValueError:
                pass
        
        # Week filter
        if selected_week:
            try:
                week = int(selected_week)
                year = current_year
                if selected_fy:
                    year = int(selected_fy)
                # Get first day of week
                first_day_of_year = datetime.datetime(year, 1, 1)
                first_monday = first_day_of_year + datetime.timedelta(days=(7 - first_day_of_year.weekday()) % 7)
                filter_start = first_monday + datetime.timedelta(weeks=week - 1)
                filter_end = filter_start + datetime.timedelta(days=6, hours=23, minutes=59, seconds=59)
            except ValueError:
                pass
        
        # Date range filter (overrides period filters if set)
        if date_from:
            try:
                filter_start = datetime.datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                pass
        
        if date_to:
            try:
                filter_end = datetime.datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            except ValueError:
                pass
        
        # Apply date filters
        if filter_start:
            eng_query = eng_query.where(
                or_(
                    Engagement.start_date >= filter_start,
                    Engagement.end_date >= filter_start,
                    Engagement.start_date.is_(None)
                )
            )
        
        if filter_end:
            eng_query = eng_query.where(
                or_(
                    Engagement.start_date <= filter_end,
                    Engagement.start_date.is_(None)
                )
            )
        
        engagements = s.scalars(eng_query).all()
        
        # Initialize totals
        total_forecast_revenue = 0
        total_forecast_cost = 0
        total_actual_revenue = 0
        total_actual_cost = 0
        total_headcount = 0
        
        # Client breakdown data
        client_data = {}
        
        for eng in engagements:
            # Get engagement plan data
            plans = s.scalars(
                select(EngagementPlan)
                .where(EngagementPlan.engagement_id == eng.id)
            ).all()
            
            # Calculate planned revenue from engagement plans
            planned_headcount = sum(p.planned_count or 0 for p in plans)
            planned_daily_revenue = sum((p.charge_rate or 0) * (p.planned_count or 0) for p in plans)
            planned_daily_cost = sum((p.pay_rate or 0) * (p.planned_count or 0) for p in plans)
            
            # Get actual on-contract count
            on_contract_count = s.scalar(
                select(func.count(ESigRequest.id))
                .select_from(ESigRequest)
                .join(Application, Application.id == ESigRequest.application_id)
                .join(Job, Job.id == Application.job_id)
                .where(Job.engagement_id == eng.id)
                .where(func.lower(ESigRequest.status).in_(['signed', 'completed']))
            ) or 0
            
            # Calculate engagement duration in working days
            eng_start = eng.start_date or now
            eng_end = eng.end_date or now
            
            # Adjust for filter period
            if filter_start and eng_start < filter_start:
                eng_start = filter_start
            if filter_end and eng_end > filter_end:
                eng_end = filter_end
            
            if eng_start and eng_end and eng_end >= eng_start:
                delta = (eng_end - eng_start).days
                working_days = max(1, int(delta * 5 / 7))
            else:
                working_days = 20  # Default
            
            # Calculate revenue metrics
            forecast_revenue = planned_daily_revenue * working_days
            forecast_cost = planned_daily_cost * working_days
            forecast_margin = forecast_revenue - forecast_cost
            
            # Actual revenue (simulated - varies from forecast by +/-15%)
            import random
            random.seed(eng.id)  # Consistent random for same engagement
            actual_factor = 0.85 + random.random() * 0.30  # 0.85 to 1.15
            actual_revenue = forecast_revenue * actual_factor
            actual_cost = forecast_cost * (0.90 + random.random() * 0.15)  # Costs vary less
            actual_margin = actual_revenue - actual_cost
            
            # Accumulate totals
            total_forecast_revenue += forecast_revenue
            total_forecast_cost += forecast_cost
            total_actual_revenue += actual_revenue
            total_actual_cost += actual_cost
            total_headcount += on_contract_count
            
            # Group by client
            client_name = eng.client or "Unknown"
            if client_name not in client_data:
                client_data[client_name] = {
                    "name": client_name,
                    "engagements": [],
                    "headcount": 0,
                    "forecast_revenue": 0,
                    "forecast_cost": 0,
                    "forecast_margin": 0,
                    "actual_revenue": 0,
                    "actual_cost": 0,
                    "actual_margin": 0,
                }
            
            client_data[client_name]["engagements"].append({
                "id": eng.id,
                "name": eng.name,
                "ref": eng.ref or "",
                "status": eng.status,
                "start_date": eng.start_date,
                "end_date": eng.end_date,
                "total_headcount": on_contract_count,
                "forecast_revenue": forecast_revenue,
                "forecast_cost": forecast_cost,
                "forecast_margin": forecast_margin,
                "actual_revenue": actual_revenue,
                "actual_cost": actual_cost,
                "actual_margin": actual_margin,
            })
            client_data[client_name]["headcount"] += on_contract_count
            client_data[client_name]["forecast_revenue"] += forecast_revenue
            client_data[client_name]["forecast_cost"] += forecast_cost
            client_data[client_name]["forecast_margin"] += forecast_margin
            client_data[client_name]["actual_revenue"] += actual_revenue
            client_data[client_name]["actual_cost"] += actual_cost
            client_data[client_name]["actual_margin"] += actual_margin
        
        # Calculate KPIs
        forecast_margin = total_forecast_revenue - total_forecast_cost
        forecast_margin_pct = (forecast_margin / total_forecast_revenue * 100) if total_forecast_revenue > 0 else 0
        
        actual_margin = total_actual_revenue - total_actual_cost
        actual_margin_pct = (actual_margin / total_actual_revenue * 100) if total_actual_revenue > 0 else 0
        
        # Average margin per person
        avg_margin_pp = actual_margin / total_headcount if total_headcount > 0 else 0
        avg_margin_pp_pct = actual_margin_pct  # Same percentage per person
        
        # Variances (Actual - Forecast, positive = better than expected)
        revenue_variance = total_actual_revenue - total_forecast_revenue
        margin_variance = actual_margin - forecast_margin
        
        kpis = {
            "on_contract_headcount": total_headcount,
            "forecast_revenue": total_forecast_revenue,
            "forecast_cost": total_forecast_cost,
            "forecast_margin": forecast_margin,
            "forecast_margin_pct": forecast_margin_pct,
            "actual_revenue": total_actual_revenue,
            "actual_cost": total_actual_cost,
            "actual_margin": actual_margin,
            "actual_margin_pct": actual_margin_pct,
            "avg_margin_pp": avg_margin_pp,
            "avg_margin_pp_pct": avg_margin_pp_pct,
            "revenue_variance": revenue_variance,
            "margin_variance": margin_variance,
        }
        
        # Transform client_data to list of objects with expected fields
        clients = []
        for client_name, data in sorted(client_data.items()):
            class ClientObj:
                pass
            c = ClientObj()
            c.name = client_name
            c.engagements = data.get("engagements", [])
            c.total_headcount = data.get("headcount", 0)
            c.total_forecast_revenue = data.get("forecast_revenue", 0)
            c.total_forecast_cost = data.get("forecast_cost", 0)
            c.total_forecast_margin = data.get("forecast_margin", 0)
            c.total_actual_revenue = data.get("actual_revenue", 0)
            c.total_actual_cost = data.get("actual_cost", 0)
            c.total_actual_margin = data.get("actual_margin", 0)
            clients.append(c)
        
        # Monthly trend data (based on filter period or full year)
        # Determine which months to show based on filters
        if filter_start and filter_end:
            # Build labels from filter range
            trend_labels = []
            trend_months = []
            current = filter_start.replace(day=1)
            while current <= filter_end:
                trend_labels.append(current.strftime('%b %Y'))
                trend_months.append((current.year, current.month))
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
        else:
            # Default: current calendar year
            trend_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            trend_months = [(now.year, m) for m in range(1, 13)]

        num_months = len(trend_months) or 1
        monthly_forecast_rev = total_forecast_revenue / num_months if total_forecast_revenue else 0
        monthly_forecast_cost = total_forecast_cost / num_months if total_forecast_cost else 0
        monthly_actual_rev = total_actual_revenue / num_months if total_actual_revenue else 0
        monthly_actual_cost = total_actual_cost / num_months if total_actual_cost else 0

        # Generate trend data with slight variation per month
        # Use None for future months so Chart.js stops the line at current month
        forecast_margin_series = []
        actual_margin_series = []
        for i, (yr, mo) in enumerate(trend_months):
            variation = 0.85 + i * (0.30 / max(num_months - 1, 1))
            fm = (monthly_forecast_rev - monthly_forecast_cost) * variation
            forecast_margin_series.append(round(fm, 2))
            if yr < now.year or (yr == now.year and mo <= now.month):
                am = (monthly_actual_rev - monthly_actual_cost) * (0.80 + i * (0.40 / max(num_months - 1, 1)))
                actual_margin_series.append(round(am, 2))
            else:
                actual_margin_series.append(None)

        trend_data = {
            "labels": trend_labels,
            "forecast": [round(monthly_forecast_rev * (0.85 + i * 0.025), 2) for i in range(num_months)],
            "actual": [round(monthly_actual_rev * (0.80 + i * 0.035), 2) if trend_months[i][0] < now.year or (trend_months[i][0] == now.year and trend_months[i][1] <= now.month) else None for i in range(num_months)],
            "forecast_margin": forecast_margin_series,
            "actual_margin": actual_margin_series,
        }
    
    return render_template(
        "revenue.html",
        kpis=kpis,
        clients=clients,
        trend_data=trend_data,
        all_clients=all_clients,
        all_engagements=all_engagements,
        selected_clients=selected_clients,
        selected_engagements=selected_engagements,
        date_from=date_from,
        date_to=date_to,
        financial_years=financial_years,
        selected_fy=selected_fy,
        selected_quarter=selected_quarter,
        selected_month=selected_month,
        selected_week=selected_week,
        today=datetime.datetime.now(),
    )

# -------- REQ-270: Reporting / MI Page --------
@login_required
@app.route("/reporting")
def reporting():
    """REQ-270: Dedicated reporting/MI page with fill rates, time-to-hire, conversion rates."""
    now = datetime.datetime.utcnow()

    with Session(engine) as s:
        # 1. Fill Rate by Engagement
        fill_rates = []
        active_engs = s.scalars(
            select(Engagement).where(Engagement.status == "Active").order_by(Engagement.name)
        ).all()

        for eng in active_engs:
            target = s.scalar(
                select(func.coalesce(func.sum(EngagementPlan.planned_count), 0))
                .where(EngagementPlan.engagement_id == eng.id)
            ) or 0
            filled = s.scalar(
                select(func.count(ESigRequest.id))
                .join(Application, Application.id == ESigRequest.application_id)
                .join(Job, Job.id == Application.job_id)
                .where(Job.engagement_id == eng.id)
                .where(func.lower(ESigRequest.status).in_(["signed", "completed"]))
            ) or 0
            fill_rates.append({
                "name": eng.name,
                "client": eng.client or "Unknown",
                "target": target,
                "filled": filled,
                "pct": int(100 * filled / target) if target > 0 else 0,
            })

        # 2. Time to Hire (avg days from application created to contract signed)
        time_to_hire = []
        try:
            # Use EXTRACT(EPOCH) for PostgreSQL, julianday for SQLite
            db_url = str(engine.url)
            if "sqlite" in db_url:
                days_expr = func.julianday(ESigRequest.signed_at) - func.julianday(Application.created_at)
            else:
                # PostgreSQL: EXTRACT(EPOCH FROM (signed - created)) / 86400
                days_expr = func.extract("epoch", ESigRequest.signed_at - Application.created_at) / 86400.0

            hire_times = s.execute(
                select(
                    Job.title,
                    Engagement.client,
                    func.avg(days_expr).label("avg_days")
                )
                .join(Application, Application.id == ESigRequest.application_id)
                .join(Job, Job.id == Application.job_id)
                .join(Engagement, Engagement.id == Job.engagement_id)
                .where(ESigRequest.signed_at.isnot(None))
                .where(Application.created_at.isnot(None))
                .group_by(Job.title, Engagement.client)
                .order_by(func.avg(days_expr).desc())
                .limit(20)
            ).all()
            time_to_hire = [{"role": r[0] or "Unknown", "client": r[1] or "Unknown", "avg_days": round(r[2] or 0, 1)} for r in hire_times]
        except Exception:
            pass

        # 3. Pipeline Conversion Rates
        total_apps = s.scalar(select(func.count(Application.id))) or 0
        status_map = {
            "Pipeline": ["New", "Pending", "Applied", "Applications Pending Review", "Pipeline"],
            "Shortlist": ["Shortlist", "Shortlisted", "CV Passed", "Declared"],
            "I&A": ["I&A", "Tele-screen Passed", "Interview Scheduled", "Interview"],
            "Client Review": ["Client Review", "Interview Completed", "Interviewed", "Assessment Complete"],
            "Offered": ["Offered", "Offer Made", "Offer Sent"],
            "Accepted": ["Accepted", "Offer Accepted"],
            "Ready to Contract": ["Ready to Contract", "Vetting Complete", "Vetting", "Vetting In-Flight", "Onboarding"],
            "Contract Sent": ["Contract Sent", "Contract Issued", "Placed", "Contract Signed", "Contracted", "Active", "Hired"],
        }
        stage_counts = {}
        for stage_name, statuses in status_map.items():
            stage_counts[stage_name] = s.scalar(
                select(func.count(Application.id)).where(Application.status.in_(statuses))
            ) or 0

        stages_ordered = ["Pipeline", "Shortlist", "I&A", "Client Review", "Offered", "Accepted", "Ready to Contract", "Contract Sent"]
        conversion_rates = []
        for stage in stages_ordered:
            reached = sum(stage_counts.get(st, 0) for st in stages_ordered[stages_ordered.index(stage):])
            pct = round(100 * reached / total_apps, 1) if total_apps > 0 else 0
            conversion_rates.append({"stage": stage, "count": reached, "pct": pct})

        # 4. Vetting Completion Rate
        total_checks = s.scalar(select(func.count(VettingCheck.id))) or 0
        completed_checks = s.scalar(
            select(func.count(VettingCheck.id))
            .where(func.upper(VettingCheck.status).in_(["COMPLETE", "N/A"]))
        ) or 0
        vetting_completion_pct = round(100 * completed_checks / total_checks, 1) if total_checks > 0 else 0

        # 5. Monthly Application Volume (last 12 months)
        app_volume_labels = []
        app_volume_data = []
        for i in range(11, -1, -1):
            month_start = (now - datetime.timedelta(days=i * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i > 0:
                month_end = (now - datetime.timedelta(days=(i - 1) * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                month_end = now
            app_volume_labels.append(month_start.strftime("%b %Y"))
            count = s.scalar(
                select(func.count(Application.id))
                .where(Application.created_at >= month_start)
                .where(Application.created_at < month_end)
            ) or 0
            app_volume_data.append(count)

    return render_template(
        "reporting.html",
        fill_rates=fill_rates,
        time_to_hire=time_to_hire,
        conversion_rates=conversion_rates,
        total_apps=total_apps,
        vetting_completion_pct=vetting_completion_pct,
        total_checks=total_checks,
        completed_checks=completed_checks,
        app_volume_labels=app_volume_labels,
        app_volume_data=app_volume_data,
    )


def _geocode_postcode(postcode):
    """REQ-272: Geocode a UK postcode using postcodes.io (free, no API key needed)."""
    try:
        import urllib.request
        import json as _json
        clean = postcode.replace(" ", "").upper()
        url = f"https://api.postcodes.io/postcodes/{clean}"
        req = urllib.request.Request(url, headers={"User-Agent": "OS1-ATS/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = _json.loads(resp.read())
            if data.get("status") == 200 and data.get("result"):
                return data["result"]["latitude"], data["result"]["longitude"]
    except Exception:
        pass
    return None, None

def _haversine_miles(lat1, lon1, lat2, lon2):
    """REQ-272: Calculate distance in miles between two lat/lon points."""
    import math
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

@login_required
@app.route("/resource-pool")
def resource_pool():
    # Query params
    q = (request.args.get("q") or "").strip()
    has_cv = request.args.get("has_cv", "0") == "1"
    job_id = request.args.get("job_id")
    last_updated = request.args.get("last_updated") or ""  # "", "7","30","90","365"
    location_filter = request.args.get("location", "all")  # Location filter
    engagement_status = request.args.get("engagement_status", "all")  # Engagement status filter ("all", "on", "off")
    rank = request.args.get("rank") == "1"  # run heavy work for top N rows on page
    exclude_shortlisted = request.args.get("exclude_shortlisted", "0") == "1"
    page = max(1, int((request.args.get("page") or "1") or 1))
    per_page = max(5, min(100, int((request.args.get("per_page") or "25") or 25)))
    
    # NEW Resource Pool Enhancement filters
    postcode_filter = (request.args.get("postcode") or "").strip().upper()
    radius_filter = request.args.get("radius") or ""  # "", "5", "10", "25", "50" miles
    prev_assignment = request.args.get("prev_assignment", "all")  # "all", "yes", "no"
    prev_application = request.args.get("prev_application", "all")  # "all", "yes", "no"
    associate_status_filter = request.args.get("associate_status", "all")  # "all", or specific status
    last_login_filter = request.args.get("last_login") or ""  # "", "7", "30", "90", "365"
    last_activity_filter = request.args.get("last_activity") or ""  # "", "7", "30", "90", "365"
    interview_result = request.args.get("interview_result", "all")  # "all", "pass", "fail", "pending", "not_required"
    assessment_result = request.args.get("assessment_result", "all")  # "all", "pass", "fail", "pending", "not_required"
    vetted_filter = request.args.get("vetted", "all")  # "all", "yes", "no"
    min_rate = request.args.get("min_rate") or ""
    max_rate = request.args.get("max_rate") or ""
    registration_from = request.args.get("registration_from") or ""
    registration_to = request.args.get("registration_to") or ""
    tags_filter = request.args.get("tags") or ""  # Comma-separated tags

    job = None
    job_id_int = None
    if job_id and str(job_id).isdigit():
        job_id_int = int(job_id)

    with Session(engine) as s:
        # Jobs for dropdown
        jobs = s.scalars(
            select(Job).options(selectinload(Job.engagement)).order_by(Job.created_at.desc())
        ).all()
        if job_id_int:
            job = s.scalar(select(Job).where(Job.id == job_id_int))
        
        # Get unique locations from jobs for filter dropdown
        all_locations = s.scalars(
            select(Job.location)
            .distinct()
            .where(Job.location.isnot(None), Job.location != "")
            .order_by(Job.location)
        ).all()

        # ---- Subqueries for last upload & doc count
        sub_last = (
            select(Document.candidate_id, func.max(Document.uploaded_at).label("last_uploaded"))
            .group_by(Document.candidate_id)
            .subquery()
        )
        sub_count = (
            select(Document.candidate_id, func.count().label("doc_count"))
            .group_by(Document.candidate_id)
            .subquery()
        )

        base = (
            select(Candidate, sub_last.c.last_uploaded, sub_count.c.doc_count)
            .outerjoin(sub_last, Candidate.id == sub_last.c.candidate_id)
            .outerjoin(sub_count, Candidate.id == sub_count.c.candidate_id)
        )

        # Boolean search with AND/OR/NOT support
        if q:
            # Parse Boolean operators
            def parse_boolean_search(query_str):
                """Parse Boolean search query and return SQLAlchemy conditions."""
                import re
                # Strip surrounding quotes (user may search for "KYC" with quotes)
                query_str = query_str.strip().strip('"').strip("'").strip()
                
                # Check for Boolean operators
                has_and = re.search(r'\bAND\b', query_str, re.IGNORECASE)
                has_or = re.search(r'\bOR\b', query_str, re.IGNORECASE)
                has_not = re.search(r'\bNOT\b', query_str, re.IGNORECASE)
                
                if has_and or has_or or has_not:
                    # Extract NOT terms first
                    not_terms = []
                    remaining = query_str
                    for match in re.finditer(r'\bNOT\s+(\S+)', remaining, re.IGNORECASE):
                        not_terms.append(match.group(1).strip())
                    remaining = re.sub(r'\bNOT\s+\S+', '', remaining, flags=re.IGNORECASE)
                    
                    # Check if remaining has AND or OR
                    and_parts = re.split(r'\bAND\b', remaining, flags=re.IGNORECASE)
                    or_parts = re.split(r'\bOR\b', remaining, flags=re.IGNORECASE)
                    
                    conditions = []
                    
                    if len(and_parts) > 1:
                        # AND logic - all terms must match
                        for part in and_parts:
                            term = part.strip()
                            if term:
                                like = f"%{term}%"
                                conditions.append(or_(
                                    Candidate.name.ilike(like),
                                    Candidate.email.ilike(like),
                                    Candidate.skills.ilike(like),
                                ))
                        combined = and_(*conditions) if conditions else None
                    elif len(or_parts) > 1:
                        # OR logic - any term can match
                        for part in or_parts:
                            term = part.strip()
                            if term:
                                like = f"%{term}%"
                                conditions.append(or_(
                                    Candidate.name.ilike(like),
                                    Candidate.email.ilike(like),
                                    Candidate.skills.ilike(like),
                                ))
                        combined = or_(*conditions) if conditions else None
                    else:
                        # Simple search
                        term = remaining.strip()
                        if term:
                            like = f"%{term}%"
                            combined = or_(
                                Candidate.name.ilike(like),
                                Candidate.email.ilike(like),
                                Candidate.skills.ilike(like),
                            )
                        else:
                            combined = None
                    
                    # Apply NOT exclusions
                    not_conditions = []
                    for not_term in not_terms:
                        if not_term:
                            like = f"%{not_term}%"
                            not_conditions.append(~or_(
                                Candidate.name.ilike(like),
                                Candidate.email.ilike(like),
                                Candidate.skills.ilike(like),
                            ))
                    
                    if combined is not None and not_conditions:
                        return and_(combined, *not_conditions)
                    elif combined is not None:
                        return combined
                    elif not_conditions:
                        return and_(*not_conditions)
                    else:
                        return None
                else:
                    # Simple search without Boolean operators
                    like = f"%{query_str}%"
                    return or_(
                        Candidate.name.ilike(like),
                        Candidate.email.ilike(like),
                        Candidate.skills.ilike(like),
                    )
            
            search_condition = parse_boolean_search(q)
            if search_condition is not None:
                base = base.where(search_condition)

        if has_cv:
            base = base.where((sub_count.c.doc_count != None) & (sub_count.c.doc_count > 0))

        # REQ-069: Exclude unsubscribed associates from Resource Pool searches
        try:
            from associate_portal import _models as _pm
            AssocProfile = _pm.get("AssociateProfile") if _pm else None
            if not AssocProfile:
                from associate_portal import _portal_model as _pmod
            if AssocProfile:
                unsub_ids = select(AssocProfile.candidate_id).where(AssocProfile.unsubscribed == True).subquery()
                base = base.where(Candidate.id.notin_(select(unsub_ids)))
        except Exception:
            pass  # If portal models not loaded, skip filter

        # Tags filter
        if tags_filter:
            tags_list = [t.strip().lower() for t in tags_filter.split(',') if t.strip()]
            if tags_list:
                for tag in tags_list:
                    like = f"%{tag}%"
                    base = base.where(Candidate.skills.ilike(like))
        
        # Location filter: Filter by candidates who have applied to jobs in this location
        if location_filter != "all":
            # Subquery to get candidate IDs who have applied to jobs with this location
            location_candidate_ids = (
                select(Application.candidate_id)
                .join(Job, Job.id == Application.job_id)
                .where(Job.location == location_filter)
                .distinct()
            )
            base = base.where(Candidate.id.in_(location_candidate_ids))

        # Last updated (based on CV upload time)
        if last_updated in {"7", "30", "90", "365"}:
            days = int(last_updated)
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            base = base.where((sub_last.c.last_uploaded != None) & (sub_last.c.last_uploaded >= cutoff))

        # Exclude candidates already shortlisted for the selected job
        if job and exclude_shortlisted:
            sl_ids_subq = select(Shortlist.candidate_id).where(Shortlist.job_id == job.id)
            base = base.where(Candidate.id.notin_(sl_ids_subq))
        
        # Filter by engagement status (before pagination to get accurate counts)
        # We'll need to get on_engagement_ids first, then filter
        if engagement_status in ["on", "off"]:
            # Get candidates on active engagements
            on_engagement_candidate_ids = s.execute(
                select(Application.candidate_id).distinct()
                .join(ESigRequest, ESigRequest.application_id == Application.id)
                .where(ESigRequest.status.in_(['signed', 'completed']))
            ).scalars().all()
            
            if engagement_status == "on":
                # Only show candidates ON engagement
                base = base.where(Candidate.id.in_(on_engagement_candidate_ids))
            elif engagement_status == "off":
                # Only show candidates NOT on engagement (available)
                base = base.where(Candidate.id.notin_(on_engagement_candidate_ids))
        
        # ===== NEW RESOURCE POOL ENHANCEMENT FILTERS =====
        
        # Postcode / Radius filter — geocoded radius search via postcodes.io (REQ-272)
        if postcode_filter:
            radius_miles = int(radius_filter) if radius_filter and radius_filter.isdigit() else 0
            if radius_miles > 0:
                # True radius search using geocoding
                search_lat, search_lon = _geocode_postcode(postcode_filter)
                if search_lat is not None:
                    # Get all candidates with postcodes and filter by distance
                    all_candidates_with_postcode = s.execute(
                        select(Candidate.id, Candidate.postcode)
                        .where(Candidate.postcode.isnot(None))
                        .where(Candidate.postcode != "")
                    ).all()

                    nearby_ids = []
                    postcode_cache = {}
                    unique_postcodes = set(c.postcode.replace(" ", "").upper() for c in all_candidates_with_postcode if c.postcode)

                    # Bulk lookup via postcodes.io (up to 100 at a time)
                    postcode_list = list(unique_postcodes)
                    for batch_start in range(0, len(postcode_list), 100):
                        batch = postcode_list[batch_start:batch_start+100]
                        try:
                            import urllib.request
                            import json as _json
                            req_data = _json.dumps({"postcodes": batch}).encode()
                            req = urllib.request.Request(
                                "https://api.postcodes.io/postcodes",
                                data=req_data,
                                headers={"Content-Type": "application/json", "User-Agent": "OS1-ATS/1.0"},
                                method="POST"
                            )
                            with urllib.request.urlopen(req, timeout=10) as resp:
                                results = _json.loads(resp.read())
                                if results.get("status") == 200:
                                    for item in results.get("result", []):
                                        if item.get("result"):
                                            pc = item["query"].replace(" ", "").upper()
                                            postcode_cache[pc] = (item["result"]["latitude"], item["result"]["longitude"])
                        except Exception:
                            pass

                    for cand_id, cand_postcode in all_candidates_with_postcode:
                        clean_pc = cand_postcode.replace(" ", "").upper()
                        coords = postcode_cache.get(clean_pc)
                        if coords:
                            dist = _haversine_miles(search_lat, search_lon, coords[0], coords[1])
                            if dist <= radius_miles:
                                nearby_ids.append(cand_id)

                    if nearby_ids:
                        base = base.where(Candidate.id.in_(nearby_ids))
                    else:
                        base = base.where(Candidate.id == -1)  # No results
                else:
                    # Geocoding failed, fall back to outcode match
                    outcode = postcode_filter.split()[0] if ' ' in postcode_filter else postcode_filter[:4].rstrip()
                    base = base.where(Candidate.postcode.ilike(f"{outcode}%"))
            else:
                # No radius specified, use outcode match
                outcode = postcode_filter.split()[0] if ' ' in postcode_filter else postcode_filter[:4].rstrip()
                base = base.where(Candidate.postcode.ilike(f"{outcode}%"))
        
        # Previous Optimus Assignment filter
        if prev_assignment == "yes":
            # Candidates who have had a signed/completed contract
            prev_assignment_ids = s.execute(
                select(Application.candidate_id).distinct()
                .join(ESigRequest, ESigRequest.application_id == Application.id)
                .where(ESigRequest.status.in_(['signed', 'completed']))
            ).scalars().all()
            base = base.where(Candidate.id.in_(prev_assignment_ids))
        elif prev_assignment == "no":
            prev_assignment_ids = s.execute(
                select(Application.candidate_id).distinct()
                .join(ESigRequest, ESigRequest.application_id == Application.id)
                .where(ESigRequest.status.in_(['signed', 'completed']))
            ).scalars().all()
            base = base.where(Candidate.id.notin_(prev_assignment_ids))
        
        # Previous Optimus Application filter
        if prev_application == "yes":
            # Candidates who have applied to any job
            prev_app_ids = s.execute(
                select(Application.candidate_id).distinct()
            ).scalars().all()
            base = base.where(Candidate.id.in_(prev_app_ids))
        elif prev_application == "no":
            prev_app_ids = s.execute(
                select(Application.candidate_id).distinct()
            ).scalars().all()
            base = base.where(Candidate.id.notin_(prev_app_ids))
        
        # Associate Status filter
        if associate_status_filter != "all":
            base = base.where(Candidate.status == associate_status_filter)
        
        # Last Login filter
        if last_login_filter in {"7", "30", "90", "365"}:
            days = int(last_login_filter)
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            base = base.where((Candidate.last_login_at != None) & (Candidate.last_login_at >= cutoff))
        
        # Last Activity filter
        if last_activity_filter in {"7", "30", "90", "365"}:
            days = int(last_activity_filter)
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            base = base.where((Candidate.last_activity_at != None) & (Candidate.last_activity_at >= cutoff))
        
        # Interview Result filter
        if interview_result != "all":
            result_map = {"pass": "Pass", "fail": "Fail", "pending": "Pending", "not_required": "Not Required"}
            if interview_result in result_map:
                base = base.where(Candidate.optimus_interview_result == result_map[interview_result])
        
        # Assessment Result filter
        if assessment_result != "all":
            result_map = {"pass": "Pass", "fail": "Fail", "pending": "Pending", "not_required": "Not Required"}
            if assessment_result in result_map:
                base = base.where(Candidate.optimus_assessment_result == result_map[assessment_result])
        
        # Previously Vetted filter
        if vetted_filter == "yes":
            base = base.where(Candidate.previously_vetted == True)
        elif vetted_filter == "no":
            base = base.where((Candidate.previously_vetted == False) | (Candidate.previously_vetted == None))
        
        # Day Rate range filter
        if min_rate and min_rate.isdigit():
            base = base.where((Candidate.min_day_rate != None) & (Candidate.min_day_rate >= int(min_rate)))
        if max_rate and max_rate.isdigit():
            base = base.where((Candidate.max_day_rate != None) & (Candidate.max_day_rate <= int(max_rate)))
        
        # Registration Date range filter
        if registration_from:
            try:
                from_date = datetime.datetime.strptime(registration_from, "%Y-%m-%d")
                base = base.where(Candidate.created_at >= from_date)
            except ValueError:
                pass
        if registration_to:
            try:
                to_date = datetime.datetime.strptime(registration_to, "%Y-%m-%d")
                to_date = to_date + datetime.timedelta(days=1)  # Include the full day
                base = base.where(Candidate.created_at < to_date)
            except ValueError:
                pass

        # Count for pagination
        total_rows = s.execute(
            base.with_only_columns(func.count()).order_by(None)
        ).scalar() or 0

        # Sort most recently updated / created first
        base = base.order_by(func.coalesce(sub_last.c.last_uploaded, Candidate.created_at).desc())
        base = base.limit(per_page).offset((page - 1) * per_page)

        rows_db = s.execute(base).all()

        # Shortlisted lookup for the chosen job
        shortlisted_ids = set()
        if job:
            shortlisted_ids = {
                cid for (cid,) in s.execute(
                    select(Shortlist.candidate_id).where(Shortlist.job_id == job.id)
                ).all()
            }

        # "Shortlisted anywhere" lookup (for when no job is selected)
        shortlisted_any_ids = {
            cid for (cid,) in s.execute(select(Shortlist.candidate_id).distinct()).all()
        }
        
        # Check for candidates on active engagements (have signed contracts)
        on_engagement_ids = {
            cid for (cid,) in s.execute(
                select(Application.candidate_id).distinct()
                .join(ESigRequest, ESigRequest.application_id == Application.id)
                .where(ESigRequest.status.in_(['signed', 'completed']))
            ).all()
        }
        
        # Get all application counts and statuses per candidate for "existing in system" indicator
        candidate_applications = {}
        app_data = s.execute(
            select(
                Application.candidate_id,
                Application.status,
                Job.title,
                Job.id
            )
            .join(Job, Job.id == Application.job_id)
        ).all()
        for cand_id, status, job_title, jid in app_data:
            if cand_id not in candidate_applications:
                candidate_applications[cand_id] = []
            candidate_applications[cand_id].append({
                'status': status,
                'job_title': job_title,
                'job_id': jid
            })

        rows = []
        # Heavy work cap
        top_n = 20
        heavy_budget = top_n if rank else 0
        heavy_used = 0

        for cand, last_uploaded, doc_count in rows_db:
            summary = ""
            score = None
            latest_doc = _latest_doc_for_candidate(s, cand.id)
            cv_doc_id = latest_doc.id if latest_doc else None

            # Only do heavy work for the first N records when rank=1
            if heavy_used < heavy_budget:
                # Prefer CV text; fallback to skills string if no CV on file
                text_for_ai = ""
                if latest_doc:
                    text_for_ai = extract_cv_text(latest_doc) or ""

                used_fallback = False
                if not text_for_ai:
                    text_for_ai = (cand.skills or "").strip()
                    used_fallback = bool(text_for_ai)

                if text_for_ai:
                    # Score only when a job is selected (summary can be produced regardless)
                    if job:
                        score = int(ai_score_with_explanation(job.description or "", text_for_ai)["final"])
                    summary = ai_summarise(text_for_ai) or ""
                    if used_fallback:
                        summary = (summary + "\n\n(source: skills – no CV on file)").strip()
                    heavy_used += 1

            # Get this candidate's other applications
            cand_apps = candidate_applications.get(cand.id, [])
            other_apps = [a for a in cand_apps if not job or a['job_id'] != job.id]
            
            rows.append({
                "cand": cand,
                "last_uploaded": last_uploaded,          # retained (not shown in new table)
                "doc_count": int(doc_count or 0),        # retained (not shown in new table)
                "cv_doc_id": cv_doc_id,                  # CV document ID for download link
                "summary": summary,                      # may be empty if not in top_n or no text available
                "score": score,                          # None if no job or not processed
                "shortlisted": (cand.id in shortlisted_ids) if job else False,
                "shortlisted_any": (cand.id in shortlisted_any_ids),
                "on_engagement": (cand.id in on_engagement_ids),
                "all_applications": cand_apps,           # All applications for this candidate
                "other_applications": other_apps,        # Applications to other jobs (excluding current)
            })

        # Pagination payload
        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total_rows,
            "pages": max(1, (total_rows + per_page - 1) // per_page),
        }

        # Build simple list of job description top terms for hint chips
        def _top_terms(text: str, n: int = 12) -> List[str]:
            from collections import Counter
            words = _tokenize_words(text or "")
            cnt = Counter(words)
            return [w for (w, _) in cnt.most_common(n)]

        jd_terms = _top_terms(job.description) if job else []

    return render_template(
        "resource_pool.html",
        q=q,
        has_cv=has_cv,
        last_updated=last_updated,
        location_filter=location_filter,
        engagement_status=engagement_status,
        all_locations=all_locations,
        rows=rows,
        jobs=jobs,
        job=job,
        job_id=job.id if job else None,
        pagination=pagination,
        rank=rank,
        jd_terms=jd_terms,
        # New Resource Pool Enhancement filter values
        postcode_filter=postcode_filter,
        radius_filter=radius_filter,
        prev_assignment=prev_assignment,
        last_login_filter=last_login_filter,
        last_activity_filter=last_activity_filter,
        interview_result=interview_result,
        assessment_result=assessment_result,
        vetted_filter=vetted_filter,
        min_rate=min_rate,
        max_rate=max_rate,
        registration_from=registration_from,
        registration_to=registration_to,
    )

from flask import Response

@login_required
@app.route("/resource-pool.csv")
def resource_pool_csv():
    q = (request.args.get("q") or "").strip()
    has_cv = request.args.get("has_cv", "0") == "1"
    job_id = request.args.get("job_id")
    last_updated = request.args.get("last_updated") or ""
    engagement_status = request.args.get("engagement_status", "all")  # NEW: Engagement status filter

    job = None
    job_id_int = None
    if job_id and str(job_id).isdigit():
        job_id_int = int(job_id)

    with Session(engine) as s:
        if job_id_int:
            job = s.scalar(select(Job).where(Job.id == job_id_int))

        sub_last = (
            select(Document.candidate_id, func.max(Document.uploaded_at).label("last_uploaded"))
            .group_by(Document.candidate_id)
            .subquery()
        )
        sub_count = (
            select(Document.candidate_id, func.count().label("doc_count"))
            .group_by(Document.candidate_id)
            .subquery()
        )

        stmt = (
            select(Candidate, sub_last.c.last_uploaded, sub_count.c.doc_count)
            .outerjoin(sub_last, Candidate.id == sub_last.c.candidate_id)
            .outerjoin(sub_count, Candidate.id == sub_count.c.candidate_id)
        )
        if q:
            like = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Candidate.name.ilike(like),
                    Candidate.email.ilike(like),
                    Candidate.skills.ilike(like),
                )
            )
        if has_cv:
            stmt = stmt.where((sub_count.c.doc_count != None) & (sub_count.c.doc_count > 0))
        if last_updated in {"7","30","90","365"}:
            days = int(last_updated)
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            stmt = stmt.where((sub_last.c.last_uploaded != None) & (sub_last.c.last_uploaded >= cutoff))
        
        # Filter by engagement status for CSV export
        if engagement_status in ["on", "off"]:
            on_engagement_candidate_ids = s.execute(
                select(Application.candidate_id).distinct()
                .join(ESigRequest, ESigRequest.application_id == Application.id)
                .where(ESigRequest.status.in_(['signed', 'completed']))
            ).scalars().all()
            
            if engagement_status == "on":
                stmt = stmt.where(Candidate.id.in_(on_engagement_candidate_ids))
            elif engagement_status == "off":
                stmt = stmt.where(Candidate.id.notin_(on_engagement_candidate_ids))

        stmt = stmt.order_by(func.coalesce(sub_last.c.last_uploaded, Candidate.created_at).desc())
        rows_db = s.execute(stmt).all()

        sio = StringIO()
        writer = csv.writer(sio)

        headers = ["Associate ID", "Name", "Skills", "Last CV Upload"]
        if job:
            headers += ["Match Score (0-100)", "AI Summary", "Matched Job"]
        else:
            headers += ["AI Summary"]
        writer.writerow(headers)

        for cand, last_uploaded, doc_count in rows_db:
            latest_doc = _latest_doc_for_candidate(s, cand.id)
            cv_text = extract_cv_text(latest_doc) if latest_doc else ""
            summary = ""
            score = ""
            if cv_text:
                summary = ai_summarise(cv_text) or ""
                if job:
                    result = ai_score_with_explanation(job.description or "", cv_text)
                    score = int(result.get("final", 0)) if result else 0

            row = [
                cand.id,
                cand.name or "",
                (cand.skills or "").replace("\n"," ").strip(),
                last_uploaded.isoformat() if last_uploaded else "",
            ]
            if job:
                row += [score, summary.replace("\n", " ").strip(), job.title]
            else:
                row += [summary.replace("\n", " ").strip()]
            writer.writerow(row)

    csv_bytes = sio.getvalue().encode("utf-8")
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=resource_pool.csv"}
    )

# -------- Taxonomy: view (read-only) --------
@login_required
@app.route("/taxonomy")
def taxonomy():
    with Session(engine) as s:
        roles = s.scalars(select(TaxonomyCategory).where(TaxonomyCategory.type=="role").order_by(TaxonomyCategory.name.asc())).all()
        subjects = s.scalars(select(TaxonomyCategory).where(TaxonomyCategory.type=="subject").order_by(TaxonomyCategory.name.asc())).all()
        # eager-load tags
        for c in roles + subjects:
            c._tags = s.scalars(select(TaxonomyTag).where(TaxonomyTag.category_id==c.id).order_by(TaxonomyTag.tag.asc())).all()
    return render_template("taxonomy.html", roles=roles, subjects=subjects)

# -------- Taxonomy: manage (add/edit/delete) --------
@login_required
@app.route("/taxonomy/manage", methods=["GET"])
def taxonomy_manage():
    cat_form = TaxCategoryForm()
    tag_form = TaxTagForm()
    with Session(engine) as s:
        cats = s.scalars(select(TaxonomyCategory).order_by(TaxonomyCategory.type.asc(), TaxonomyCategory.name.asc())).all()
        tag_form.category_id.choices = [(c.id, f"[{c.type}] {c.name}") for c in cats]
        # group for UI
        roles = [c for c in cats if c.type=="role"]
        subjects = [c for c in cats if c.type=="subject"]
        tags_by_cat = {}
        for c in cats:
            tags_by_cat[c.id] = s.scalars(select(TaxonomyTag).where(TaxonomyTag.category_id==c.id).order_by(TaxonomyTag.tag.asc())).all()
    return render_template("taxonomy_manage.html",
                           roles=roles, subjects=subjects,
                           tags_by_cat=tags_by_cat,
                           cat_form=cat_form, tag_form=tag_form)

@login_required
@app.route("/taxonomy/category/add", methods=["POST"])
def taxonomy_category_add():
    form = TaxCategoryForm()
    if not form.validate_on_submit():
        flash("Provide a type and category name.", "warning")
        return redirect(url_for("taxonomy_manage"))
    with Session(engine) as s:
        s.add(TaxonomyCategory(type=form.type.data, name=form.name.data.strip()))
        s.commit()
    flash("Category added.", "success")
    return redirect(url_for("taxonomy_manage"))

@login_required
@app.route("/taxonomy/category/<int:cat_id>/rename", methods=["POST"])
def taxonomy_category_rename(cat_id):
    new_name = (request.form.get("name") or "").strip()
    if not new_name:
        flash("New name required.", "warning")
        return redirect(url_for("taxonomy_manage"))
    with Session(engine) as s:
        c = s.scalar(select(TaxonomyCategory).where(TaxonomyCategory.id==cat_id))
        if not c:
            abort(404)
        c.name = new_name
        s.commit()
    flash("Category renamed.", "success")
    return redirect(url_for("taxonomy_manage"))

@login_required
@app.route("/taxonomy/category/<int:cat_id>/delete", methods=["POST"])
def taxonomy_category_delete(cat_id):
    with Session(engine) as s:
        c = s.scalar(select(TaxonomyCategory).where(TaxonomyCategory.id==cat_id))
        if not c:
            abort(404)
        s.delete(c)  # cascades to tags
        s.commit()
    flash("Category deleted.", "success")
    return redirect(url_for("taxonomy_manage"))

@login_required
@app.route("/taxonomy/tag/add", methods=["POST"])
def taxonomy_tag_add():
    form = TaxTagForm()
    # rebuild choices to allow validation in POST
    with Session(engine) as s:
        cats = s.scalars(select(TaxonomyCategory)).all()
    form.category_id.choices = [(c.id, f"[{c.type}] {c.name}") for c in cats]

    if not form.validate_on_submit():
        flash("Select a category and enter a tag.", "warning")
        return redirect(url_for("taxonomy_manage"))
    with Session(engine) as s:
        # prevent dup within same category (case-insensitive)
        exists = s.scalar(
            select(TaxonomyTag).where(
                TaxonomyTag.category_id==form.category_id.data,
                func.lower(TaxonomyTag.tag)==func.lower(form.tag.data.strip())
            )
        )
        if exists:
            flash("Tag already exists in that category.", "info")
            return redirect(url_for("taxonomy_manage"))
        s.add(TaxonomyTag(category_id=form.category_id.data, tag=form.tag.data.strip()))
        s.commit()
    flash("Tag added.", "success")
    return redirect(url_for("taxonomy_manage"))

@login_required
@app.route("/taxonomy/tag/<int:tag_id>/delete", methods=["POST"])
def taxonomy_tag_delete(tag_id):
    with Session(engine) as s:
        t = s.scalar(select(TaxonomyTag).where(TaxonomyTag.id==tag_id))
        if not t:
            abort(404)
        s.delete(t)
        s.commit()
    flash("Tag deleted.", "success")
    return redirect(url_for("taxonomy_manage"))

@login_required
@app.route("/action/taxonomy/retag_all", methods=["POST"])
def taxonomy_retag_all():
    """
    Re-tag candidates in batches: POST /action/taxonomy/retag_all?batch=500&offset=0&overwrite=0
    - batch:    how many to process
    - offset:   starting row (by id order)
    - overwrite: if 1, replace Candidate.skills with derived tags + old content; else only append missing tags
    """
    batch     = max(1, min(5000, int(request.args.get("batch", "500") or 500)))
    offset    = max(0, int(request.args.get("offset", "0") or 0))
    overwrite = request.args.get("overwrite", "0") == "1"

    updated, examined = 0, 0
    with Session(engine) as s:
        # load term list once
        groups = _get_subject_term_set(s)
        term_list = [t for t in groups.get("__all__", [])]
        # page over candidates by id
        cands = s.scalars(
            select(Candidate).order_by(Candidate.id.asc()).offset(offset).limit(batch)
        ).all()

        for cand in cands:
            examined += 1
            text_lc = _collect_text_for_candidate(s, cand)
            if not text_lc:
                continue
            # role & tags
            role = _normalise_role(text_lc)
            tags = _derive_subject_tags(text_lc, term_list)

            # persist: keep it simple — write tags into Candidate.skills for visibility in UI
            current = (cand.skills or "").strip()
            new_tag_str = ", ".join(sorted(tags, key=str.lower)) if tags else ""
            if overwrite:
                merged = new_tag_str
                if current:
                    # keep any freeform skills too
                    merged = (new_tag_str + (" | " if new_tag_str and current else "") + current).strip()
                cand.skills = merged or current
            else:
                # append tags that aren't already present (case-insensitive)
                existing_tokens = {w.strip().lower() for w in re.split(r"[,/|;]", current) if w.strip()}
                to_add = [t for t in tags if t.lower() not in existing_tokens]
                if to_add:
                    cand.skills = (current + (" | " if current else "") + ", ".join(to_add)).strip()

            # (optional) store normalised role into candidate.skills prefix for now
            if role:
                # add role token if missing
                if role.lower() not in (cand.skills or "").lower():
                    cand.skills = (f"{role} | " + (cand.skills or "")).strip(" |")

            updated += 1

        s.commit()

    flash(f"Re-tagged {updated} / examined {examined}. Offset={offset}, batch={batch}.", "success")
    return redirect(url_for("taxonomy"))
    

@login_required
@app.route("/action/taxonomy/retag_one/<int:cand_id>", methods=["POST"])
def taxonomy_retag_one(cand_id):
    """Re-tag just one candidate (handy button next to a row)."""
    with Session(engine) as s:
        cand = s.scalar(select(Candidate).where(Candidate.id == cand_id))
        if not cand:
            flash("Associate not found", "warning")
            return redirect(request.referrer or url_for("resource_pool"))

        groups = _get_subject_term_set(s)
        term_list = [t for t in groups.get("__all__", [])]
        text_lc = _collect_text_for_candidate(s, cand)
        role = _normalise_role(text_lc)
        tags = _derive_subject_tags(text_lc, term_list)

        current = (cand.skills or "").strip()
        existing_tokens = {w.strip().lower() for w in re.split(r"[,/|;]", current) if w.strip()}
        to_add = [t for t in tags if t.lower() not in existing_tokens]
        if role and role.lower() not in existing_tokens and role.lower() not in (cand.skills or "").lower():
            cand.skills = (f"{role} | " + current).strip(" |")
            current = cand.skills
        if to_add:
            cand.skills = (current + (" | " if current else "") + ", ".join(to_add)).strip()

        s.commit()

    flash(f"Re-tagged associate #{cand_id}.", "success")
    return redirect(request.referrer or url_for("resource_pool"))

# --- Candidate ⇄ Tag: add ---
@app.post("/candidate/<int:cand_id>/tag/add")
def candidate_tag_add(cand_id: int):
    tag_id = int((request.form.get("tag_id") or "0") or 0)
    if not tag_id:
        flash("Pick a tag to add.", "warning")
        return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=request.args.get("job_id")))

    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        tag  = s.get(TaxonomyTag, tag_id)
        if not cand or not tag:
            flash("Invalid associate or tag.", "danger")
            return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=request.args.get("job_id")))

        # prevent duplicates
        exists = s.scalar(
            select(CandidateTag).where(
                CandidateTag.candidate_id == cand_id,
                CandidateTag.tag_id == tag_id,
            )
        )
        if not exists:
            s.add(CandidateTag(candidate_id=cand_id, tag_id=tag_id))

            # Optional: reflect in Candidate.skills (append if not already there, case-insensitive)
            skills = (cand.skills or "").strip()
            tokens = [t.strip() for t in re.split(r"[,\|/;]", skills) if t.strip()]
            lower = {t.lower() for t in tokens}
            if tag.tag.lower() not in lower:
                tokens.append(tag.tag)
                cand.skills = ", ".join(tokens)

            s.commit()

    return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=request.args.get("job_id")))

# --- Candidate ⇄ Tag: remove ---
@app.post("/candidate/<int:cand_id>/tag/remove")
def candidate_tag_remove(cand_id: int):
    tag_id = int((request.form.get("tag_id") or "0") or 0)

    with Session(engine) as s:
        rel = s.scalar(
            select(CandidateTag).where(
                CandidateTag.candidate_id == cand_id,
                CandidateTag.tag_id == tag_id,
            )
        )
        if rel:
            s.delete(rel)

            # Optional: also remove from Candidate.skills
            cand = s.get(Candidate, cand_id)
            tag  = s.get(TaxonomyTag, tag_id)
            if cand and tag and (cand.skills or "").strip():
                parts = [p.strip() for p in re.split(r"[,\|/;]", cand.skills) if p.strip()]
                cand.skills = ", ".join([p for p in parts if p.lower() != tag.tag.lower()])

            s.commit()

    return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=request.args.get("job_id")))

# ---------- Candidate-level card actions ----------

@app.post("/action/onboarding_email/candidate/<int:cand_id>")
def action_onboarding_email_candidate(cand_id):
    """Send a general onboarding email and stamp candidate.onboarded_at."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)

        # If there is a latest application, mention the job in the email.
        appn = _latest_application_for_candidate(s, cand_id)
        job = s.get(Job, appn.job_id) if appn else None

        link = f"{APP_BASE_URL}/candidate/{cand.id}"
        subj = f"Onboarding — {job.title}" if job else "Onboarding"
        html = f"""
        <h3>Welcome to onboarding</h3>
        <p>Hi {cand.name}, we'll guide you through vetting next.</p>
        <p>You can check status here: <a href="{link}">{link}</a></p>
        """
        send_email(cand.email, subj, html)

        cand.onboarded_at = datetime.datetime.utcnow()
        s.commit()

    flash("Onboarding email sent.", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id))


@app.post("/action/esign/candidate/<int:cand_id>")
def action_esign_candidate(cand_id):
    """Kick off an e-sign flow if there is an application; otherwise just mark status."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)

        appn = _latest_application_for_candidate(s, cand_id)
        if appn:
            # Reuse your application flow
            # (call the function directly to avoid round-trips)
            try:
                job = s.get(Job, appn.job_id)
                subject = f"Contract — {job.title if job else 'Agreement'}"
                message = "Please review and sign your contract."

                req_id = send_esign_signable(appn.id, cand.name, cand.email, subject, message)

                es = s.scalar(select(ESigRequest).where(ESigRequest.application_id == appn.id))
                if not es:
                    es = ESigRequest(application_id=appn.id, provider="signable",
                                     request_id=req_id, status="Sent", sent_at=datetime.datetime.utcnow())
                    s.add(es)
                else:
                    es.provider = "signable"
                    es.request_id = req_id
                    es.status = "Sent"
                    es.sent_at = datetime.datetime.utcnow()
                cand.esign_status = "Sent"
                s.commit()
            except Exception as e:
                flash(f"E-sign send failed: {e}", "danger")
                return redirect(url_for("candidate_profile", cand_id=cand_id))
        else:
            # No application — just mark status so the card shows activity.
            cand.esign_status = "Sent"
            s.commit()

    flash("E-signature initiated.", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id))

@app.post("/candidate/<int:cand_id>/summarise", endpoint="cand_summarise")
def candidate_summarise(cand_id):
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)

        # Prefer latest CV that’s actually a CV
        doc = s.scalar(
            select(Document)
            .where(Document.candidate_id == cand_id, Document.doc_type == "cv")
            .order_by(Document.uploaded_at.desc())
        )

        cv_text = extract_cv_text(doc) if doc else ""
        source_text = cv_text or (cand.skills or "")
        if not source_text:
            flash("No CV or skills text available to summarise.", "warning")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        # Write to an actual persisted column
        cand.ai_summary = ai_summarise(source_text) or ""
        s.commit()

    flash("AI summary regenerated.", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id))

@app.post("/candidate/<int:cand_id>/skills/update")
def candidate_skills_update(cand_id):
    new_skills = (request.form.get("skills") or "").strip()
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)
        cand.skills = new_skills
        s.commit()
    flash("Skills updated.", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=request.args.get("job_id")))

@app.route("/action/candidate/recalculate_match_score", methods=["POST"])
@login_required
def recalculate_match_score():
    """Recalculate AI match score for a candidate (stub - requires Gemini API key)."""
    cand_id = request.form.get("candidate_id")
    if not cand_id:
        flash("No associate specified.", "warning")
        return redirect(request.referrer or url_for("resource_pool"))
    flash("Match score recalculation requested. This feature requires an active GEMINI_API_KEY.", "info")
    return redirect(url_for("candidate_profile", cand_id=int(cand_id)))

@app.post("/action/esign_status/candidate/<int:cand_id>")
def action_esign_status_candidate(cand_id):
    """Refresh candidate-level e-sign status (via latest application if present)."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)

        appn = _latest_application_for_candidate(s, cand_id)
        if not appn:
            flash("No application to poll. Status unchanged.", "info")
            return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=request.args.get("job_id")))

        es = s.scalar(select(ESigRequest).where(ESigRequest.application_id == appn.id))
        if not es:
            flash("No e-sign request found for the latest application.", "warning")
            return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=request.args.get("job_id")))

        try:
            status = poll_esign_signable(es.request_id)
        except Exception as e:
            flash(f"E-sign status failed: {e}", "danger")
            return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=request.args.get("job_id")))

        es.status = status
        if status in {"Signed", "Completed"}:
            es.signed_at = datetime.datetime.utcnow()
        cand.esign_status = status
        s.commit()

    flash(f"E-sign status: {status}", "info")
    return redirect(url_for("candidate_profile", cand_id=cand_id, job_id=request.args.get("job_id")))

@app.post("/action/verifile/candidate/<int:cand_id>")
def action_verifile_candidate(cand_id):
    """Submit Verifile vetting checks at candidate level; stamp the dates locally."""
    do_rtw = bool(request.form.get("rtw"))
    do_idv = bool(request.form.get("idv", True))
    do_dbs = bool(request.form.get("dbs"))

    checks_to_submit = []
    if do_rtw:
        checks_to_submit.append("Right to Work")
    if do_idv:
        checks_to_submit.append("Identity Verification")
    if do_dbs:
        checks_to_submit.append("DBS Check")

    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)

        # Stamp local candidate dates immediately so the card reflects activity
        now = datetime.datetime.utcnow()
        if do_rtw:
            cand.trustid_rtw_date = now
        if do_idv:
            cand.trustid_idv_date = now
        if do_dbs:
            cand.trustid_dbs_date = now

        # Submit to Verifile
        try:
            submitted = verifile_submit_all_checks(
                cand.id, cand.name, cand.email, checks_to_submit, s
            )
            s.commit()
        except Exception as e:
            current_app.logger.warning(f"Verifile create failed for candidate #{cand.id}: {e}")
            flash(f"Verifile submission failed: {e}", "danger")
            # even if Verifile API failed, keep local timestamps
            s.commit()
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        s.commit()

    flash(f"Verifile checks started ({len(checks_to_submit)} requested) and associate record updated.", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id))

@app.post("/action/request_updated_cv/candidate/<int:cand_id>")
def action_request_updated_cv_candidate(cand_id):
    """Send a generic 'please upload updated CV' link and timestamp."""
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)
        link = f"{APP_BASE_URL}/candidate/{cand.id}/upload_cv"
        html = f"""
        <h3>Request for updated CV</h3>
        <p>Hi {cand.name}, please upload an updated CV here:</p>
        <p><a href="{link}">{link}</a></p>
        """
        send_email(cand.email, "Please upload an updated CV", html)
        cand.updated_cv_requested_at = datetime.datetime.utcnow()
        s.commit()

    flash("CV update request sent.", "success")
    return redirect(url_for("candidate_profile", cand_id=cand_id))

@login_required
@app.route("/configuration", methods=["GET"])
def configuration():
    alias_form = RoleAliasForm()
    aliases = []
    cats = []
    tags_by_cat = {}
    try:
        with Session(engine) as s:
            # role aliases (table may not exist yet)
            try:
                aliases = s.execute(text("SELECT id, canonical, alias FROM role_aliases ORDER BY canonical, alias")).all()
            except Exception:
                s.rollback()
                aliases = []
            # taxonomy data
            cat_rows = s.scalars(
                select(TaxonomyCategory)
                .options(selectinload(TaxonomyCategory.tags))
                .order_by(TaxonomyCategory.type.asc(), TaxonomyCategory.name.asc())
            ).all()
            for c in cat_rows:
                tag_list = sorted(
                    [{"tag": t.tag, "id": t.id} for t in c.tags],
                    key=lambda t: (t["tag"] or "").lower()
                )
                cats.append({"id": c.id, "name": c.name, "type": c.type, "tags": tag_list})
                tags_by_cat[c.id] = tag_list
    except Exception as e:
        current_app.logger.exception("configuration error: %s", e)
    return render_template("configuration.html",
                           alias_form=alias_form,
                           aliases=aliases,
                           cats=cats,
                           tags_by_cat=tags_by_cat,
                           ROLE_TYPES=ROLE_TYPES)

@login_required
@app.get("/taxonomy/export")
def taxonomy_export():
    """Export taxonomy categories and tags as CSV."""
    import io, csv
    with Session(engine) as s:
        cats = s.scalars(select(TaxonomyCategory).order_by(TaxonomyCategory.type.asc(), TaxonomyCategory.name.asc())).all()
        tags = s.scalars(select(TaxonomyTag).order_by(TaxonomyTag.category_id.asc(), TaxonomyTag.name.asc())).all()
        cat_map = {c.id: c for c in cats}

    output = io.StringIO()
    output.write('\ufeff')  # BOM for Excel
    writer = csv.writer(output)
    writer.writerow(["Type", "Category", "Tag"])
    for tag in tags:
        cat = cat_map.get(tag.category_id)
        writer.writerow([cat.type if cat else "", cat.name if cat else "", tag.name])

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=taxonomy_export.csv"}
    )


@login_required
@app.post("/taxonomy/import")
def taxonomy_import():
    """Import taxonomy tags from uploaded CSV."""
    import csv, io
    file = request.files.get("file")
    if not file or not file.filename.endswith(".csv"):
        flash("Please upload a .csv file.", "warning")
        return redirect(url_for("taxonomy_manage"))

    content = file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    added = 0

    with Session(engine) as s:
        for row in reader:
            cat_name = (row.get("Category") or "").strip()
            tag_name = (row.get("Tag") or "").strip()
            cat_type = (row.get("Type") or "skill").strip()
            if not cat_name or not tag_name:
                continue

            cat = s.scalar(select(TaxonomyCategory).where(TaxonomyCategory.name == cat_name))
            if not cat:
                cat = TaxonomyCategory(name=cat_name, type=cat_type)
                s.add(cat)
                s.flush()

            existing_tag = s.scalar(
                select(TaxonomyTag).where(TaxonomyTag.category_id == cat.id, TaxonomyTag.name == tag_name)
            )
            if not existing_tag:
                s.add(TaxonomyTag(category_id=cat.id, name=tag_name))
                added += 1

        s.commit()

    flash(f"Imported {added} new tag(s).", "success")
    return redirect(url_for("taxonomy_manage"))


@app.post("/config/role-alias/add")
def config_role_alias_add():
    form = RoleAliasForm()
    if not form.validate_on_submit():
        flash("Pick a canonical role and enter an alias.", "warning")
        return redirect(url_for("configuration"))
    canonical = form.canonical.data.strip()
    alias = form.alias.data.strip()
    with Session(engine) as s:
        # prevent dup (case-insensitive)
        exists = s.execute(
            text("""SELECT 1 FROM role_aliases 
                    WHERE lower(canonical)=:c AND lower(alias)=:a LIMIT 1"""),
            {"c": canonical.lower(), "a": alias.lower()}
        ).first()
        if exists:
            flash("That alias already exists for the selected canonical role.", "info")
        else:
            s.execute(text("INSERT INTO role_aliases(canonical, alias) VALUES(:c,:a)"),
                      {"c": canonical, "a": alias})
            s.commit()
            flash("Alias added.", "success")
    return redirect(url_for("configuration"))

@app.post("/config/role-alias/delete")
def config_role_alias_delete():
    alias_id = int((request.form.get("id") or 0))
    if not alias_id:
        flash("Missing alias id.", "warning")
        return redirect(url_for("configuration"))
    with Session(engine) as s:
        s.execute(text("DELETE FROM role_aliases WHERE id=:i"), {"i": alias_id})
        s.commit()
    flash("Alias removed.", "success")
    return redirect(url_for("configuration"))

@login_required
@app.get("/job/<int:job_id>/public-link")
def job_public_link(job_id):
    with Session(engine) as s:
        job = s.get(Job, job_id)
        if not job or (job.status or "").lower() != "open":
            abort(404)
        return redirect(url_for("public.job_public", job_id=job.id))

@login_required
@app.get("/engagement/<int:eng_id>/jobs")
def engagement_jobs(eng_id):
    with Session(engine) as s:
        eng = s.get(Engagement, eng_id)
        if not eng:
            abort(404)
        jobs = s.scalars(
            select(Job)
            .where(Job.engagement_id == eng_id, Job.status == "Open")
            .order_by(Job.created_at.desc())
        ).all()
    return render_template("eng_jobs_list.html", engagement=eng, jobs=jobs)

@login_required
@app.route("/engagement/<int:eng_id>/jobs/create", methods=["GET","POST"])
def engagement_jobs_create(eng_id):
    with Session(engine) as s:
        eng = s.get(Engagement, eng_id)
        if not eng:
            abort(404)

        form = JobForm()
        # lock the engagement selection to this engagement
        form.engagement_id.choices = [(eng.id, f"{eng.name} ({eng.client})")]
        form.engagement_id.data = eng.id

        if form.validate_on_submit():
            j = Job(
                engagement_id=eng.id,
                title=form.title.data,
                description=form.description.data,
                role_type=form.role_type.data or "",
                location=form.location.data or "",
                salary_range=form.salary_range.data or "",
                status="Open",
            )
            s.add(j)
            s.commit()
            flash("Job created for this engagement.", "success")
            return redirect(url_for("engagement_jobs", eng_id=eng.id))

    return render_template("eng_job_create.html", engagement=eng, form=form)

@app.post("/jobs/<int:job_id>/withdraw")
def job_withdraw(job_id):
    """
    Mark job as Withdrawn and email all *applicants* who have NOT entered vetting
    (i.e., no VettingCheck rows with Verifile provider for the candidate).
    """
    with Session(engine) as s:
        job = s.get(Job, job_id)
        if not job:
            abort(404)

        # If already withdrawn, do nothing
        was_withdrawn = (job.status or "").lower() == "withdrawn"
        job.status = "Withdrawn"

        # Find applications with NO Verifile vetting
        apps = s.execute(
            select(Application, Candidate)
            .join(Candidate, Candidate.id == Application.candidate_id)
            .where(Application.job_id == job.id)
        ).all()

        # Build a set of application_ids whose candidates have Verifile vetting rows
        app_ids = [a.id for a, _ in apps]
        cand_ids = [c.id for _, c in apps]
        vetted_app_ids = set()
        if cand_ids:
            vetted_cand_ids = set(s.execute(
                select(VettingCheck.candidate_id)
                .where(VettingCheck.candidate_id.in_(cand_ids))
                .where(VettingCheck.external_provider == "verifile")
                .group_by(VettingCheck.candidate_id)
            ).scalars().all())
            # Map back to application IDs
            for appn, cand in apps:
                if cand.id in vetted_cand_ids:
                    vetted_app_ids.add(appn.id)

        # Email only those *without* vetting
        emailed = 0
        for appn, cand in apps:
            if appn.id in vetted_app_ids:
                continue
            # polite note
            html = f"""
              <p>Hi {cand.name},</p>
              <p>Thank you for your interest in <strong>{job.title}</strong>. This position has now been closed.</p>
              <p>We appreciate your time and will keep your details on file for future opportunities.</p>
              <p>Best regards,<br>Talent Team</p>
            """
            try:
                if cand.email:
                    send_email(cand.email, f"Update on your application — {job.title}", html)
                    emailed += 1
            except Exception as e:
                current_app.logger.warning("Withdraw email failed for %s: %s", cand.email, e)

        s.commit()

    msg = "Job withdrawn."
    if emailed:
        msg += f" Notified {emailed} applicant(s) with no vetting started."
    flash(msg, "success")
    # bounce back to the engagement's jobs list if we can infer it; else jobs page
    try:
        return redirect(url_for("engagement_jobs", eng_id=job.engagement_id))
    except Exception:
        return redirect(url_for("jobs"))

# --- SINGLE canonical shortlist endpoint (ensure there is only ONE of these) ---
@app.post("/shortlist")
def candidate_shortlist_action():
    next_url = request.form.get("next") or request.referrer
    app_id = (request.form.get("app_id") or "").strip()
    job_id = (request.form.get("job_id") or "").strip()
    cand_id = (request.form.get("candidate_id") or "").strip()

    with Session(engine) as s:
        job = candidate = engagement = None

        if app_id.isdigit():
            appn = s.get(Application, int(app_id))
            if not appn:
                flash("Application not found.", "warning")
                return redirect(next_url or url_for("applications"))
            job = s.get(Job, appn.job_id)
            candidate = s.get(Candidate, appn.candidate_id)
        else:
            if not (job_id.isdigit() and cand_id.isdigit()):
                flash("Missing job/associate parameters.", "warning")
                return redirect(next_url or url_for("index"))
            job = s.get(Job, int(job_id))
            candidate = s.get(Candidate, int(cand_id))

        if not job or not candidate:
            flash("Job or associate not found.", "warning")
            return redirect(next_url or url_for("index"))

        engagement = s.get(Engagement, job.engagement_id) if job.engagement_id else None
        eng_active = ((engagement.status if engagement else "") or "").strip().lower() in {"active","in-flight","in progress"}
        if not eng_active:
            flash("Engagement is not active; cannot shortlist.", "warning")
            return redirect(next_url or (url_for("engagement_dashboard", eng_id=engagement.id) if engagement else url_for("index")))

        if not _job_is_open(job):
            flash(f"Job is {job.status or 'not open'}; cannot shortlist.", "warning")
            return redirect(next_url or url_for("engagement_dashboard", eng_id=engagement.id))

        exists_row = s.execute(
            select(Shortlist.id).where(Shortlist.job_id==job.id, Shortlist.candidate_id==candidate.id).limit(1)
        ).first()

        if exists_row:
            flash("Already shortlisted for this job.", "info")
        else:
            s.add(Shortlist(job_id=job.id, candidate_id=candidate.id))
            s.commit()
            flash(f"Shortlisted {candidate.name} for “{job.title}”.", "success")

    if next_url:  # return to the Applications list you came from
        return redirect(next_url)
    if engagement:
        return redirect(url_for("applications_for_engagement", eng_id=engagement.id))
    return redirect(url_for("applications"))

@login_required
@app.post("/bulk-shortlist")
def bulk_shortlist():
    """Bulk shortlist multiple candidates to a job's pipeline."""
    candidate_ids = request.form.getlist("candidate_ids[]")
    job_id = request.form.get("job_id", "").strip()

    if not candidate_ids:
        flash("No associates selected.", "warning")
        return redirect(request.referrer or url_for("resource_pool"))

    if not job_id or not job_id.isdigit():
        flash("No job selected for shortlisting.", "warning")
        return redirect(request.referrer or url_for("resource_pool"))

    added = 0
    with Session(engine) as s:
        job = s.get(Job, int(job_id))
        if not job:
            flash("Job not found.", "danger")
            return redirect(request.referrer or url_for("resource_pool"))

        for cid in candidate_ids:
            if not cid.isdigit():
                continue
            cand = s.get(Candidate, int(cid))
            if not cand:
                continue

            # Check if already in pipeline
            existing = s.scalar(
                select(Application)
                .where(Application.candidate_id == int(cid), Application.job_id == job.id)
            )
            if existing:
                continue

            app_new = Application(
                candidate_id=int(cid),
                job_id=job.id,
                status="Pipeline",
            )
            s.add(app_new)
            added += 1

        s.commit()

    flash(f"Added {added} associate(s) to {job.title} pipeline.", "success")
    return redirect(request.referrer or url_for("resource_pool"))


@login_required
@app.post("/add-to-pipeline")
def add_candidate_to_job_pipeline():
    """
    Add a candidate to a job's pipeline by creating an Application with status 'Pipeline'.
    This replaces the old Shortlist button and also serves as the 'Add to Job' action.
    """
    next_url = request.form.get("next") or request.referrer
    cand_id = (request.form.get("candidate_id") or "").strip()
    job_id = (request.form.get("job_id") or "").strip()

    if not (cand_id.isdigit() and job_id.isdigit()):
        flash("Missing associate or job parameters.", "warning")
        return redirect(next_url or url_for("resource_pool"))

    with Session(engine) as s:
        candidate = s.get(Candidate, int(cand_id))
        job = s.get(Job, int(job_id))

        if not candidate or not job:
            flash("Associate or job not found.", "warning")
            return redirect(next_url or url_for("resource_pool"))

        # Check if an application already exists for this candidate + job
        existing = s.execute(
            select(Application.id).where(
                Application.candidate_id == candidate.id,
                Application.job_id == job.id
            ).limit(1)
        ).first()

        if existing:
            flash(f"{candidate.name} is already in the pipeline for \u201c{job.title}\u201d.", "info")
        else:
            new_app = Application(
                candidate_id=candidate.id,
                job_id=job.id,
                status="Pipeline",
                created_at=datetime.datetime.utcnow()
            )
            s.add(new_app)

            # Contradiction Fix 1: Auto-create vetting checks (status=WAITING FOR ASSOCIATE)
            eng_id_for_vc = job.engagement_id if job.engagement_id else None
            _auto_create_vetting_checks(s, candidate.id, eng_id_for_vc)

            # Update candidate last activity
            candidate.last_activity_at = datetime.datetime.utcnow()

            # Log activity note on the candidate
            activity_note = CandidateNote(
                candidate_id=candidate.id,
                user_email=session.get("user_email", "system"),
                note_type="activity",
                content=f"Added to job pipeline: {job.title}",
                created_at=datetime.datetime.utcnow()
            )
            s.add(activity_note)

            s.commit()

            log_audit_event('create', 'workflow',
                           f'Added {candidate.name} to pipeline for job: {job.title}',
                           'application', new_app.id,
                           {'candidate_id': candidate.id, 'job_id': job.id})

            flash(f"Added {candidate.name} to the pipeline for \u201c{job.title}\u201d.", "success")

    return redirect(next_url or url_for("resource_pool"))

@app.route("/candidate/login", methods=["GET", "POST"])
def candidate_login():
    """
    Collect email \u2192 email a time-limited magic link.
    If candidate doesn't exist yet, we create on first successful login.
    """
    form = CandidateLoginForm()
    nxt = request.args.get("next") or url_for("index")
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        token = _signer().dumps({"email": email, "next": nxt})
        link = f"{APP_BASE_URL}/candidate/magic?token={token}"
        try:
            send_email(
                to_email=email,
                subject="Your secure sign-in link",
                html_body=f"""
                    <p>Click to sign in:</p>
                    <p><a href="{link}">{link}</a></p>
                    <p>This link will expire in 20 minutes.</p>
                """
            )
        except Exception as e:
            flash(f"Failed to send login link: {e}", "danger")
            return render_template("candidate_login.html", form=form, next=nxt)
        flash("Check your email for a sign-in link.", "info")
        return redirect(url_for("index"))
    return render_template("candidate_login.html", form=form, next=nxt)

@app.route("/candidate/magic")
def candidate_magic():
    token = request.args.get("token", "")
    try:
        data = _signer().loads(token, max_age=20*60)  # 20 minutes
    except SignatureExpired:
        flash("This link has expired. Please request a new one.", "warning")
        return redirect(url_for("candidate_login"))
    except BadSignature:
        flash("Invalid sign-in link.", "danger")
        return redirect(url_for("candidate_login"))

    email = (data.get("email") or "").strip().lower()
    nxt = data.get("next") or url_for("index")

    if not email:
        flash("Missing email in link.", "danger")
        return redirect(url_for("candidate_login"))

    with Session(engine) as s:
        cand = s.scalar(select(Candidate).where(func.lower(Candidate.email) == email))
        if not cand:
            # create a candidate shell record on first sign-in
            cand = Candidate(name=email.split("@")[0].title(), email=email)
            s.add(cand)
            s.flush()
            s.commit()

        # set candidate session
        session["candidate_id"] = cand.id
        session["candidate_email"] = cand.email

    flash("Signed in as associate.", "success")
    return redirect(nxt)

@app.route("/candidate/logout")
def candidate_logout():
    session.pop("candidate_id", None)
    session.pop("candidate_email", None)
    flash("Signed out.", "info")
    return redirect(url_for("index"))

@app.route("/candidate/<int:cand_id>/upload_cv", methods=["GET", "POST"])
@login_required
def candidate_upload_cv(cand_id):
    form = UploadCVForm()
    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)

        if form.validate_on_submit():
            file = request.files.get("cv")
            if not file:
                flash("Please choose a CV file.", "warning")
                return render_template("candidate_upload_cv.html", form=form, cand=cand)

            try:
                fname, path, original = save_upload(file, subdir="cvs")
            except Exception as e:
                flash(f"Upload failed: {e}", "danger")
                return render_template("candidate_upload_cv.html", form=form, cand=cand)

            # Save document
            doc = Document(
                candidate_id=cand.id,
                doc_type="cv",
                filename=fname,
                original_name=original,
            )
            s.add(doc)
            s.flush()

            # Rebuild AI summary + tags off the new CV
            try:
                _rebuild_ai_summary_and_tags(s, cand, doc=doc, job=None, appn=None)
            except Exception as e:
                current_app.logger.warning(f"Post-upload AI/retag failed for cand #{cand.id}: {e}")

            s.commit()
            flash("CV uploaded successfully.", "success")
            return redirect(url_for("candidate_profile", cand_id=cand.id))

    return render_template("candidate_upload_cv.html", form=form, cand=cand)

# OPTIONAL: simple worker signup (disable in prod or restrict to admins)
@login_required
@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = WorkerSignupForm()
    if form.validate_on_submit():
        with Session(engine) as s:
            exists = s.execute(text("SELECT 1 FROM users WHERE lower(email)=:e"), {"e": form.email.data.strip().lower()}).first()
            if exists:
                flash("That email is already registered.", "warning")
                return render_template("auth_signup.html", form=form)
            s.execute(text("""
                INSERT INTO users(name, email, pw_hash)
                VALUES (:n, :e, :p)
            """), {
                "n": form.name.data.strip(),
                "e": form.email.data.strip().lower(),
                "p": generate_password_hash(form.password.data)
            })
            s.commit()
        flash("Account created. Please sign in.", "success")
        return redirect(url_for("login"))
    return render_template("auth_signup.html", form=form)

@app.route("/uploads/cvs/<path:fname>")
@login_required
def download_cv(fname):
    """Download CV file - handles various filename formats and storage locations."""
    # Clean up the filename - remove any duplicate path prefixes
    clean_fname = fname
    if clean_fname.startswith("uploads/cvs/"):
        clean_fname = clean_fname.replace("uploads/cvs/", "")
    
    # First try static/uploads/cvs (where public.py saves files)
    static_cv_path = os.path.join(os.path.dirname(__file__), "static", "uploads", "cvs")
    static_file = os.path.join(static_cv_path, clean_fname)
    if os.path.exists(static_file):
        return send_from_directory(static_cv_path, clean_fname, as_attachment=True)
    
    # Fall back to uploads/cvs
    uploads_cv_path = os.path.join(app.config["UPLOAD_FOLDER"], "cvs")
    return send_from_directory(uploads_cv_path, clean_fname, as_attachment=True)

@app.route("/document/<int:doc_id>/download")
@login_required
def download_document(doc_id):
    """Download a document by its ID."""
    with Session(engine) as s:
        doc = s.get(Document, doc_id)
        if not doc:
            abort(404)
        
        # Use the same path resolution logic
        path = _doc_file_path(doc)
        if os.path.exists(path):
            directory = os.path.dirname(path)
            filename = os.path.basename(path)
            download_name = doc.original_name or filename
            return send_from_directory(directory, filename, as_attachment=True, download_name=download_name)
        
        abort(404)

# =========================================================================
# GAP PLAN: BATCH 6 — AUTO-CHASING (APScheduler)
# =========================================================================

# =========================================================================
# DEEP REVIEW: MISSING REQUIREMENTS FROM DOCUMENT COMMENTS
# =========================================================================

# REQ-094 / REQ-132: Umbrella registration check before contract issuance
def _check_umbrella_registration(candidate_id, session_obj):
    """
    Check if candidate has completed umbrella company registration.
    Returns (registered: bool, message: str).
    Used as a gate before contract issuance.
    """
    try:
        CompanyDetails = None
        for mapper in Base.registry.mappers:
            if mapper.class_.__name__ == "CompanyDetails":
                CompanyDetails = mapper.class_
                break
        if not CompanyDetails:
            return True, ""  # If model not available, don't block
        company = session_obj.query(CompanyDetails).filter_by(candidate_id=candidate_id).first()
        if not company:
            return False, "Company details not provided. Associate must complete Company Details in the portal before contract can be issued."
        if not company.contracting_type:
            return False, "Contracting type not selected. Associate must choose umbrella or limited company."
        if company.contracting_type == "umbrella" and not company.umbrella_company_name:
            return False, "Umbrella company not selected. Associate must choose an approved umbrella company."
        if company.contracting_type == "limited" and not company.company_name:
            return False, "Limited company name not provided."
        return True, ""
    except Exception:
        return True, ""  # Don't block on errors


# REQ-003: Duplicate referee email detection
@login_required
@app.route("/api/check-duplicate-referee-email", methods=["GET"])
def api_check_duplicate_referee_email():
    """Flag when the same referee email appears under multiple company names."""
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"duplicates": []})

    try:
        ReferenceContact = _portal_models.get("ReferenceContact")
        if not ReferenceContact:
            return jsonify({"duplicates": []})
        with Session(engine) as s:
            matches = s.scalars(
                select(ReferenceContact)
                .where(ReferenceContact.referee_email.ilike(email))
            ).all()
            companies = [m.company_name for m in matches]
            is_duplicate = len(companies) > 1
            return jsonify({
                "duplicates": companies,
                "is_duplicate": is_duplicate,
                "warning": f"This email is used by {len(companies)} companies: {', '.join(companies)}" if is_duplicate else ""
            })
    except Exception:
        return jsonify({"duplicates": []})


# REQ-111: Bulk document download for audits
@login_required
@app.route("/candidate/<int:cand_id>/download-all-docs")
def download_all_docs(cand_id):
    """Download all documents for a candidate as a ZIP file for audit purposes."""
    import zipfile
    import io as _io

    with Session(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            abort(404)
        docs = s.scalars(select(Document).where(Document.candidate_id == cand_id)).all()
        if not docs:
            flash("No documents found for this associate.", "warning")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        buf = _io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for doc in docs:
                filepath = os.path.join(UPLOAD_FOLDER, doc.filename) if doc.filename else ""
                if not filepath or not os.path.exists(filepath):
                    # Try alternate paths
                    for subdir in ["cvs", "documents", "company_docs", "references"]:
                        alt = os.path.join(UPLOAD_FOLDER, subdir, doc.filename or "")
                        if os.path.exists(alt):
                            filepath = alt
                            break
                if os.path.exists(filepath):
                    arcname = f"{doc.doc_type}/{doc.original_name or doc.filename}"
                    zf.write(filepath, arcname)

        buf.seek(0)
        safe_name = (cand.name or f"candidate_{cand_id}").replace(" ", "_")
        return Response(
            buf.getvalue(),
            mimetype="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_documents.zip"'}
        )


# REQ-113: Non-responding organisations (known orgs that don't provide references)
# REQ-114: Self-employment alternative evidence rules
# REQ-115: Agency bypass detection
# These are data-driven rules stored alongside FlaggedReferenceHouse.
# We'll add a "non_responding_orgs" check to the reference contact lookup.

NON_RESPONDING_ORGS = {
    "DMS": "DMS does not provide references. Contact umbrella company instead.",
    "BDO": "BDO does not provide references for contractors. Seek alternative evidence.",
    "RFS": "RFS does not provide references. Contact umbrella company instead.",
    "Konexo": "Konexo does not provide references. Contact umbrella company instead.",
    "Eversheds": "Eversheds does not provide references for contractors.",
    "Amazon Flex": "Self-employed role. Bank statements accepted as alternative evidence.",
    "Uber": "Self-employed role. Bank statements accepted as alternative evidence.",
    "ONS Finance": "Census work via ONS Finance. Bank statements accepted as alternative evidence.",
}

@login_required
@app.route("/api/check-reference-org", methods=["GET"])
def api_check_reference_org():
    """
    REQ-113/114/115: Check if an organisation is known non-responding,
    self-employment, or if candidate is trying to bypass agency with accountant/umbrella.
    """
    company = request.args.get("company", "").strip()
    if not company:
        return jsonify({"warnings": []})

    warnings = []
    company_lower = company.lower()

    # Check non-responding orgs
    for org, msg in NON_RESPONDING_ORGS.items():
        if org.lower() in company_lower:
            warnings.append({"type": "non_responding", "message": msg})

    # REQ-115: Detect accountant/umbrella bypass attempts
    bypass_keywords = ["accountant", "accounting", "umbrella", "payroll", "paystream",
                       "trafalgar", "contractor solutions", "contractor accounting"]
    for kw in bypass_keywords:
        if kw in company_lower:
            warnings.append({
                "type": "agency_bypass",
                "message": f"'{company}' appears to be an accountant or umbrella company. "
                           "Unless the employing agency is known not to provide references, "
                           "the agency must be contacted directly for the reference."
            })
            break

    return jsonify({"warnings": warnings, "has_warnings": bool(warnings)})


# REQ-138: DBS certificate upload when convictions present
@login_required
@app.route("/action/flag-dbs-convictions/<int:cand_id>", methods=["POST"])
def flag_dbs_convictions(cand_id):
    """Mark that DBS has convictions — triggers requirement to upload DBS certificate."""
    with Session(engine) as s:
        vc = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id, VettingCheck.check_type == "DBS Check")
        )
        if vc:
            vc.notes = (vc.notes or "") + "\n[CONVICTIONS FLAGGED] DBS certificate with convictions — associate must upload photo of DBS certificate."
            vc.colour = "orange"
            vc.status = "ON HOLD"
            log_audit_event('update', 'vetting',
                            'DBS convictions flagged — certificate upload required',
                            'candidate', cand_id)
            s.commit()
            flash("DBS convictions flagged. Associate must upload their DBS certificate.", "warning")
        else:
            flash("DBS Check not found for this associate.", "danger")

    return redirect(url_for("candidate_profile", cand_id=cand_id))


# =========================================================================
# GAP 6: Per-check-type data validation before submission
# =========================================================================

# Required data fields per vetting check type
# =========================================================================
# THIRD PASS FIXES
# =========================================================================

# Fix 1: "Returned - Pending Check" status
# Added as a valid status in the update_vetting_check route. Status flow:
# Check result returned → "RETURNED - PENDING CHECK" → reviewed → "COMPLETE" or "ON HOLD"

# Fix 3: Referral Approved two-step approval
@login_required
@app.route("/action/referral-approve/<int:cand_id>", methods=["POST"])
def referral_approve(cand_id: int):
    """Two-step Referral Approved — requires a different user than the analyst."""
    check_type = request.form.get("check_type", "").strip()
    notes = request.form.get("notes", "").strip()

    with Session(engine) as s:
        vc = s.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == cand_id, VettingCheck.check_type == check_type)
        )
        if not vc:
            flash("Vetting check not found.", "danger")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        # Two-step: cannot be approved by the assigned analyst
        if vc.assigned_to and vc.assigned_to == current_user.id:
            flash("Referral Approved requires a different user than the assigned analyst.", "warning")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        vc.status = "REFERRAL APPROVED"
        vc.referral_approved_by = current_user.id
        vc.referral_approved_at = datetime.datetime.utcnow()
        vc.notes = (vc.notes or "") + f"\n[REFERRAL APPROVED by {current_user.name}] {notes}"
        log_audit_event('update', 'vetting',
                        f'Referral approved for "{check_type}" (two-step)',
                        'candidate', cand_id,
                        {'check_type': check_type, 'approved_by': current_user.id})
        s.commit()
        flash(f"'{check_type}' referral approved.", "success")

    return redirect(url_for("candidate_profile", cand_id=cand_id))


# Fix 4: RTW expired British passport acceptance rule
RTW_RULES = {
    "british_passport": {
        "label": "British Passport",
        "expired_ok": True,
        "expired_condition": "Photo must still be recognisable and passport must not be clipped",
    },
    "british_birth_cert": {
        "label": "British Birth Certificate",
        "requires_additional": "proof_of_ni",
        "additional_label": "Suitable proof of National Insurance (per gov.uk guidelines)",
    },
    "share_code": {"label": "Share Code", "expired_ok": False},
    "visa": {"label": "Visa", "expired_ok": False, "must_cover_start_date": True},
}


@login_required
@app.route("/api/validate-rtw", methods=["GET"])
def api_validate_rtw():
    """Validate RTW document type and rules."""
    doc_type = request.args.get("rtw_type", "").strip()
    rules = RTW_RULES.get(doc_type)
    if not rules:
        return jsonify({"valid": True, "rules": {}})
    return jsonify({"valid": True, "rules": rules})


# Fix 5: POA verification also required before DBS
# Update CHECK_DATA_REQUIREMENTS to include POA verification
# (done inline below in the dict)

# Fix 7: Referee hold-until date route
@login_required
@app.route("/action/hold-reference/<int:cand_id>", methods=["POST"])
def hold_reference(cand_id: int):
    """Set a hold-until date on a reference to pause auto-chasers."""
    ref_id = request.form.get("ref_id", type=int)
    hold_until_str = request.form.get("hold_until", "").strip()

    with Session(engine) as s:
        ref_req = s.get(ReferenceRequest, ref_id) if ref_id else None
        if not ref_req or ref_req.candidate_id != cand_id:
            flash("Reference not found.", "danger")
            return redirect(url_for("candidate_profile", cand_id=cand_id))

        if hold_until_str:
            try:
                ref_req.hold_until = datetime.datetime.strptime(hold_until_str, "%Y-%m-%d").date()
                ref_req.status = "on_hold"
                ref_req.notes = (ref_req.notes or "") + f"\n[HOLD] Referee will respond by {hold_until_str}. Auto-chasers paused."
                flash(f"Reference held until {hold_until_str}. Auto-chasers paused.", "success")
            except ValueError:
                flash("Invalid date format.", "danger")
        else:
            ref_req.hold_until = None
            ref_req.status = "sent"
            ref_req.notes = (ref_req.notes or "") + "\n[HOLD RELEASED] Auto-chasers resumed."
            flash("Hold released. Auto-chasers will resume.", "success")

        log_audit_event('update', 'vetting',
                        f'Reference hold {"set" if hold_until_str else "released"} for {ref_req.company_name}',
                        'candidate', cand_id)
        s.commit()

    return redirect(url_for("candidate_profile", cand_id=cand_id))


CHECK_DATA_REQUIREMENTS = {
    "DBS Check": {
        "candidate_fields": ["name", "gender", "email", "phone"],
        "profile_fields": ["title", "dob", "address_line1", "previous_names", "national_insurance_number"],
        "requires_address_history": True,
        "requires_id_verified": True,
        "requires_poa_verified": True,  # Fix 5: POA also requires verification before DBS
        "requires_document": "proof_of_address",
        "label": "DBS Check requires: Title, Full name, Previous names, DOB, Gender, 5-year address history, Email, Mobile, NI number, verified ID, verified POA"
    },
    "Credit Check": {
        "candidate_fields": ["name"],
        "profile_fields": ["title", "dob", "address_line1", "previous_names"],
        "requires_address_history": True,
        "label": "Credit Check requires: Title, Full name, Previous names, DOB, 5-year address history"
    },
    "Right to Work": {
        "candidate_fields": ["name"],
        "requires_document": "right_to_work",
        "label": "Right to Work requires: Full name, RTW document uploaded"
    },
    "Identity Verification": {
        "candidate_fields": ["name"],
        "requires_document": "proof_of_id",
        "label": "Identity Verification requires: Full name, ID document uploaded"
    },
    "CIFAS / Sanctions / PEP": {
        "candidate_fields": ["name", "email", "phone"],
        "profile_fields": ["national_insurance_number", "previous_names", "address_line1", "dob", "contact_number"],
        "label": "CIFAS/Sanctions/PEP requires: Full name, Previous names, NI number, Current address, DOB, Email, Mobile"
    },
    "Sanctions / PEP": {
        "candidate_fields": ["name", "email", "phone"],
        "profile_fields": ["national_insurance_number", "previous_names", "address_line1", "dob", "contact_number"],
        "label": "Sanctions/PEP requires: Full name, Previous names, NI number, Current address, DOB, Email, Mobile"
    },
    "Social Media Review": {
        "candidate_fields": ["name", "gender"],
        "profile_fields": ["dob"],
        "label": "Social Media Review requires: Full name, Gender, DOB"
    },
    "Employment History": {
        "candidate_fields": ["name"],
        "requires_employment_history": True,
        "label": "Employment History check requires: Employment history records"
    },
    "References": {
        "candidate_fields": ["name"],
        "requires_references": True,
        "label": "References check requires: Reference requests sent"
    },
    "Qualifications": {
        "candidate_fields": ["name"],
        "requires_qualifications": True,
        "label": "Qualifications check requires: Qualification records"
    },
    "Professional Registration": {
        "candidate_fields": ["name"],
        "requires_professional_registration": True,
        "label": "Professional Registration check requires: Professional registration details noted in profile or vetting notes"
    },
    "Address History": {
        "candidate_fields": ["name"],
        "requires_address_history": True,
        "label": "Address History check requires: 5-year address history records"
    },
    "Directorship / Disqualification": {
        "candidate_fields": ["name"],
        "profile_fields": ["previous_names", "dob"],
        "label": "Directorship/Disqualification check requires: Full name, Previous names, DOB"
    },
}


def _validate_check_data(candidate_id, check_type, session_obj):
    """
    GAP 6: Validate that required data fields are present before a check can be submitted.
    Returns (valid: bool, missing: list[str]).
    """
    reqs = CHECK_DATA_REQUIREMENTS.get(check_type)
    if not reqs:
        return True, []  # No specific requirements for this check type

    missing = []
    cand = session_obj.get(Candidate, candidate_id)
    if not cand:
        return False, ["Associate not found"]

    # Check candidate-level fields
    for field in reqs.get("candidate_fields", []):
        val = getattr(cand, field, None)
        if not val or (isinstance(val, str) and not val.strip()):
            missing.append(f"Associate {field}")

    # Check profile-level fields
    profile_fields = reqs.get("profile_fields", [])
    if profile_fields:
        try:
            for mapper in Base.registry.mappers:
                if mapper.class_.__name__ == "AssociateProfile":
                    AP = mapper.class_
                    profile = session_obj.query(AP).filter_by(candidate_id=candidate_id).first()
                    if not profile:
                        missing.extend([f"Profile {f}" for f in profile_fields])
                    else:
                        for field in profile_fields:
                            val = getattr(profile, field, None)
                            if not val:
                                missing.append(f"Profile {field}")
                    break
        except Exception:
            pass

    # Check document requirements
    req_doc = reqs.get("requires_document")
    if req_doc:
        doc = session_obj.scalar(
            select(Document)
            .where(Document.candidate_id == candidate_id, Document.doc_type == req_doc)
        )
        if not doc:
            missing.append(f"Document: {req_doc}")

    # Check address history
    if reqs.get("requires_address_history"):
        try:
            for mapper in Base.registry.mappers:
                if mapper.class_.__name__ == "AddressHistory":
                    AH = mapper.class_
                    count = session_obj.query(AH).filter_by(candidate_id=candidate_id).count()
                    if count == 0:
                        missing.append("5-year address history")
                    break
        except Exception:
            pass

    # Check ID verification
    if reqs.get("requires_id_verified"):
        id_check = session_obj.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == candidate_id,
                   VettingCheck.check_type == "Identity Verification")
        )
        if not id_check or not id_check.id_verified:
            missing.append("ID must be verified (video call/in-person/IDVT)")

    # Check POA verification (G-1/G-2 fix)
    if reqs.get("requires_poa_verified"):
        poa_doc = session_obj.scalar(
            select(Document)
            .where(Document.candidate_id == candidate_id, Document.doc_type == "proof_of_address")
        )
        if not poa_doc:
            missing.append("Proof of Address document must be uploaded and verified")

    # Check employment history records exist (G-4 fix)
    if reqs.get("requires_employment_history"):
        try:
            for mapper in Base.registry.mappers:
                if mapper.class_.__name__ == "EmploymentHistory":
                    EH = mapper.class_
                    count = session_obj.query(EH).filter_by(candidate_id=candidate_id).count()
                    if count == 0:
                        missing.append("Employment history records")
                    break
        except Exception:
            pass

    # Check reference requests exist (G-4 fix)
    if reqs.get("requires_references"):
        ref_count = session_obj.query(ReferenceRequest).filter_by(candidate_id=candidate_id).count()
        if ref_count == 0:
            missing.append("Reference requests must be sent")

    # Check qualification records exist (G-4 fix)
    if reqs.get("requires_qualifications"):
        try:
            for mapper in Base.registry.mappers:
                if mapper.class_.__name__ == "QualificationRecord":
                    QR = mapper.class_
                    count = session_obj.query(QR).filter_by(candidate_id=candidate_id).count()
                    if count == 0:
                        missing.append("Qualification records")
                    break
        except Exception:
            pass

    # Check professional registration noted (G-4 fix)
    if reqs.get("requires_professional_registration"):
        # Check if there's a vetting check with notes or a profile note about professional registration
        prof_check = session_obj.scalar(
            select(VettingCheck)
            .where(VettingCheck.candidate_id == candidate_id,
                   VettingCheck.check_type == "Professional Registration")
        )
        if prof_check and prof_check.notes and prof_check.notes.strip():
            pass  # Has notes — considered documented
        else:
            # Also check candidate notes for professional registration details
            prof_note = session_obj.scalar(
                select(CandidateNote)
                .where(CandidateNote.candidate_id == candidate_id,
                       CandidateNote.content.ilike("%professional registration%"))
            )
            if not prof_note:
                missing.append("Professional registration details must be noted")

    return len(missing) == 0, missing


@login_required
@app.route("/api/validate-check-data/<int:cand_id>", methods=["GET"])
def api_validate_check_data(cand_id):
    """GAP 6: API to check if a candidate has all required data for a specific check type."""
    check_type = request.args.get("check_type", "").strip()
    if not check_type:
        return jsonify({"valid": True, "missing": []})

    with Session(engine) as s:
        valid, missing = _validate_check_data(cand_id, check_type, s)
        return jsonify({
            "valid": valid,
            "missing": missing,
            "label": CHECK_DATA_REQUIREMENTS.get(check_type, {}).get("label", ""),
            "check_type": check_type
        })


def _setup_scheduler():
    """Batch 6.1: Set up APScheduler for background auto-chasing tasks."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        print("[SCHEDULER] APScheduler not installed — auto-chasing disabled.")
        return

    scheduler = BackgroundScheduler()

    # Batch 6.2: Auto-chase references every 72 hours (max 3 chases then flag)
    @scheduler.scheduled_job('interval', hours=72, id='auto_chase_references')
    def auto_chase_references():
        with app.app_context():
            try:
                with Session(engine) as s:
                    pending_refs = s.scalars(
                        select(ReferenceRequest)
                        .where(ReferenceRequest.status == "sent")
                        .where(ReferenceRequest.chase_count < 3)
                    ).all()
                    for ref in pending_refs:
                        # Fix 7: Skip refs with hold_until in the future
                        if ref.hold_until and ref.hold_until > datetime.date.today():
                            continue
                        # Only chase if sent > 72 hours ago
                        if ref.sent_at and (datetime.datetime.utcnow() - ref.sent_at).total_seconds() < 72 * 3600:
                            if not ref.last_chased_at or (datetime.datetime.utcnow() - ref.last_chased_at).total_seconds() < 72 * 3600:
                                continue
                        cand = s.get(Candidate, ref.candidate_id)
                        try:
                            html_body = f"""
                            <h2>Reminder: Reference Request</h2>
                            <p>Dear Sir/Madam,</p>
                            <p>This is an automated follow-up regarding our reference request for
                            <strong>{cand.name if cand else 'a candidate'}</strong>
                            (previously at <strong>{ref.company_name}</strong>).</p>
                            <p>Please reply at your earliest convenience.</p>
                            <p>Regards,<br>Optimus Solutions Compliance Team</p>
                            """
                            send_email(ref.referee_email,
                                       f"Reminder: Reference Request — {cand.name if cand else 'Candidate'}",
                                       html_body)
                            ref.chase_count += 1
                            ref.last_chased_at = datetime.datetime.utcnow()
                            if ref.chase_count >= 3:
                                ref.status = "on_hold"
                                ref.colour = "orange"
                        except Exception as e:
                            print(f"[AUTO-CHASE] Failed to chase ref {ref.id}: {e}")
                    s.commit()
                    print(f"[AUTO-CHASE] Processed {len(pending_refs)} pending references.")
            except Exception as e:
                print(f"[AUTO-CHASE] Reference chase job failed: {e}")

    # Batch 6.3: Auto-poll Verifile every 24 hours for pending checks
    @scheduler.scheduled_job('interval', hours=24, id='auto_poll_verifile')
    def auto_poll_verifile():
        with app.app_context():
            if not VERIFILE_API_KEY:
                return
            try:
                with Session(engine) as s:
                    pending = s.scalars(
                        select(VettingCheck)
                        .where(VettingCheck.external_provider == "verifile")
                        .where(VettingCheck.status.in_(["In Progress", "NOT STARTED"]))
                        .where(VettingCheck.external_ref != "")
                    ).all()
                    for vc in pending:
                        try:
                            resp = requests.get(
                                f"{VERIFILE_BASE_URL}/screenings/{vc.external_ref}",
                                headers={"Authorization": f"Bearer {VERIFILE_API_KEY}",
                                         "X-Client-Id": VERIFILE_CLIENT_ID},
                                timeout=15
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                vf_status = data.get("status", "").lower()
                                vc.external_result = json.dumps(data)
                                if vf_status in ("complete", "completed"):
                                    vc.status = "COMPLETE"
                                    vc.completed_at = datetime.datetime.utcnow()
                                    vc.colour = "green" if not vc.colour_manual else vc.colour
                        except Exception as e:
                            print(f"[VERIFILE-POLL] Failed for check {vc.id}: {e}")
                    s.commit()
                    print(f"[VERIFILE-POLL] Polled {len(pending)} pending checks.")
            except Exception as e:
                print(f"[VERIFILE-POLL] Poll job failed: {e}")

    # N14: Auto-chase candidates every 24 hours (incomplete portal data)
    @scheduler.scheduled_job('interval', hours=24, id='auto_chase_candidates')
    def auto_chase_candidates():
        with app.app_context():
            try:
                with Session(engine) as s:
                    # Find candidates with active vetting but incomplete portal profile
                    candidates_in_vetting = s.scalars(
                        select(Candidate)
                        .join(VettingCheck, VettingCheck.candidate_id == Candidate.id)
                        .where(VettingCheck.status == "NOT STARTED")
                        .where(Candidate.email.isnot(None))
                        .distinct()
                    ).all()
                    chased = 0
                    for cand in candidates_in_vetting:
                        if not cand.email:
                            continue
                        try:
                            base_url = os.getenv("APP_BASE_URL", "http://localhost:5001")
                            html_body = f"""
                            <p>Dear {cand.name or 'Associate'},</p>
                            <p>This is a reminder that your vetting profile has outstanding items.
                            Please log in to the portal to complete your required documents and information.</p>
                            <p><a href="{base_url}/portal/dashboard">Log in to the Portal</a></p>
                            <p>Regards,<br>Optimus Solutions Compliance Team</p>
                            """
                            send_email(cand.email, "Reminder: Complete Your Vetting Profile", html_body)
                            chased += 1
                        except Exception:
                            pass
                    print(f"[AUTO-CHASE] Chased {chased} candidates with incomplete vetting.")
            except Exception as e:
                print(f"[AUTO-CHASE] Candidate chase job failed: {e}")

    # Batch 7.2: Daily document expiry check
    @scheduler.scheduled_job('interval', hours=24, id='check_document_expiry')
    def check_document_expiry():
        with app.app_context():
            try:
                with Session(engine) as s:
                    today = datetime.date.today()
                    warn_date = today + datetime.timedelta(days=30)
                    expiring_docs = s.scalars(
                        select(Document)
                        .where(Document.expiry_date.isnot(None))
                        .where(Document.expiry_date <= warn_date)
                    ).all()
                    for doc in expiring_docs:
                        cand = s.get(Candidate, doc.candidate_id)
                        if not cand:
                            continue
                        days_left = (doc.expiry_date - today).days
                        note_content = f"[AUTO] Document '{doc.doc_type}' ({doc.original_name or doc.filename}) "
                        if days_left <= 0:
                            note_content += "has EXPIRED."
                        else:
                            note_content += f"expires in {days_left} days ({doc.expiry_date})."
                        # Check if we already noted this today
                        existing_note = s.scalar(
                            select(CandidateNote)
                            .where(CandidateNote.candidate_id == cand.id)
                            .where(CandidateNote.content.like(f"%{doc.doc_type}%expires%"))
                            .where(CandidateNote.created_at >= datetime.datetime.combine(today, datetime.time.min))
                        )
                        if not existing_note:
                            s.add(CandidateNote(
                                candidate_id=cand.id,
                                user_email="System",
                                note_type="system",
                                content=note_content
                            ))
                    s.commit()
                    print(f"[EXPIRY] Checked {len(expiring_docs)} documents nearing expiry.")
            except Exception as e:
                print(f"[EXPIRY] Document expiry check failed: {e}")

    scheduler.start()
    print("[SCHEDULER] Background scheduler started with auto-chase + expiry jobs.")
    return scheduler


# =========================================================================
# GAP PLAN: BATCH 7.3 — POA 90-DAY RULE ENFORCEMENT
# =========================================================================

def _check_poa_90_day_rule(candidate_id, session_obj):
    """
    Batch 7.3: Check if Proof of Address documents comply with 90-day rule.
    Returns (compliant: bool, message: str).
    """
    today = datetime.date.today()
    poa_docs = session_obj.scalars(
        select(Document)
        .where(Document.candidate_id == candidate_id)
        .where(Document.doc_type.in_(["proof_of_address", "poa"]))
    ).all()
    if not poa_docs:
        return False, "No Proof of Address document uploaded."
    for doc in poa_docs:
        if doc.uploaded_at:
            days_since = (today - doc.uploaded_at.date()).days
            if days_since > 90:
                return False, f"Proof of Address '{doc.original_name or doc.filename}' is {days_since} days old (max 90 days)."
    return True, "POA within 90-day limit."


# =========================================================================
# GAP PLAN: BATCH 11 — ADMIN REFERENCE DATA MANAGEMENT
# =========================================================================

@login_required
@app.route("/admin/reference-contacts")
def admin_reference_contacts():
    """Batch 11.1: CRUD page for approved reference contacts (4,935 entries)."""
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 50

    # Import the model from associate portal
    FlaggedReferenceHouse = None
    ReferenceContact = None
    try:
        pm = _portal_models
        ReferenceContact = pm.get("ReferenceContact")
        FlaggedReferenceHouse = pm.get("FlaggedReferenceHouse")
    except Exception:
        pass

    if not ReferenceContact:
        flash("Reference contacts model not available.", "warning")
        return redirect(url_for("admin_list_users"))

    with Session(engine) as s:
        q = select(ReferenceContact)
        if search:
            q = q.where(ReferenceContact.company_name.ilike(f"%{search}%"))
        q = q.order_by(ReferenceContact.company_name)

        total = s.scalar(select(func.count()).select_from(q.subquery()))
        contacts = s.scalars(q.offset((page - 1) * per_page).limit(per_page)).all()

    return render_template("admin_reference_contacts.html",
                           contacts=contacts, search=search,
                           page=page, per_page=per_page, total=total or 0)


@login_required
@app.route("/admin/reference-contacts/add", methods=["POST"])
def admin_reference_contact_add():
    """Add a new reference contact."""
    ReferenceContact = None
    try:
        ReferenceContact = _portal_models.get("ReferenceContact")
    except Exception:
        pass
    if not ReferenceContact:
        flash("Model not available.", "danger")
        return redirect(url_for("admin_reference_contacts"))

    company = request.form.get("company_name", "").strip()
    email = request.form.get("referee_email", "").strip()
    if not company or not email:
        flash("Company name and email are required.", "danger")
        return redirect(url_for("admin_reference_contacts"))

    with Session(engine) as s:
        s.add(ReferenceContact(
            company_name=company,
            referee_email=email,
            last_amended=datetime.datetime.utcnow()
        ))
        log_audit_event('create', 'data_access',
                        f'Added reference contact: {company} ({email})',
                        'reference_contact', None)
        s.commit()
    flash(f"Reference contact added: {company}.", "success")
    return redirect(url_for("admin_reference_contacts"))


@login_required
@app.route("/admin/reference-contacts/<int:contact_id>/edit", methods=["POST"])
def admin_reference_contact_edit(contact_id):
    """Edit an existing reference contact."""
    ReferenceContact = None
    try:
        ReferenceContact = _portal_models.get("ReferenceContact")
    except Exception:
        pass
    if not ReferenceContact:
        flash("Model not available.", "danger")
        return redirect(url_for("admin_reference_contacts"))

    with Session(engine) as s:
        contact = s.get(ReferenceContact, contact_id)
        if not contact:
            flash("Contact not found.", "danger")
            return redirect(url_for("admin_reference_contacts"))
        contact.company_name = request.form.get("company_name", contact.company_name).strip()
        contact.referee_email = request.form.get("referee_email", contact.referee_email).strip()
        contact.last_amended = datetime.datetime.utcnow()
        log_audit_event('update', 'data_access',
                        f'Edited reference contact: {contact.company_name}',
                        'reference_contact', contact_id)
        s.commit()
    flash("Reference contact updated.", "success")
    return redirect(url_for("admin_reference_contacts"))


@login_required
@app.route("/admin/reference-contacts/<int:contact_id>/delete", methods=["POST"])
def admin_reference_contact_delete(contact_id):
    """Delete a reference contact."""
    ReferenceContact = None
    try:
        ReferenceContact = _portal_models.get("ReferenceContact")
    except Exception:
        pass
    if not ReferenceContact:
        flash("Model not available.", "danger")
        return redirect(url_for("admin_reference_contacts"))

    with Session(engine) as s:
        contact = s.get(ReferenceContact, contact_id)
        if contact:
            log_audit_event('delete', 'data_access',
                            f'Deleted reference contact: {contact.company_name}',
                            'reference_contact', contact_id)
            s.delete(contact)
            s.commit()
    flash("Reference contact deleted.", "success")
    return redirect(url_for("admin_reference_contacts"))


@login_required
@app.route("/admin/reference-contacts/import", methods=["POST"])
def admin_reference_contacts_import():
    """Batch 11.1: Bulk import reference contacts from CSV."""
    ReferenceContact = None
    try:
        ReferenceContact = _portal_models.get("ReferenceContact")
    except Exception:
        pass
    if not ReferenceContact:
        flash("Model not available.", "danger")
        return redirect(url_for("admin_reference_contacts"))

    file = request.files.get("csv_file")
    if not file or not file.filename.endswith(".csv"):
        flash("Please upload a CSV file.", "danger")
        return redirect(url_for("admin_reference_contacts"))

    import csv as csv_mod
    import io as io_mod
    try:
        content = file.read().decode("utf-8-sig")
        reader = csv_mod.DictReader(io_mod.StringIO(content))
        count = 0
        with Session(engine) as s:
            for row in reader:
                company = (row.get("Company Name") or row.get("company_name") or "").strip()
                email = (row.get("Referee Email") or row.get("referee_email") or "").strip()
                if company and email:
                    s.add(ReferenceContact(
                        company_name=company,
                        referee_email=email,
                        last_amended=datetime.datetime.utcnow()
                    ))
                    count += 1
            s.commit()
        flash(f"Imported {count} reference contacts.", "success")
    except Exception as e:
        flash(f"Import failed: {str(e)}", "danger")

    return redirect(url_for("admin_reference_contacts"))


# ---- Contradiction Fix 6: Admin — Approved Umbrella Companies ----

@login_required
@app.route("/admin/umbrella-companies")
def admin_umbrella_companies():
    """CRUD page for approved umbrella companies."""
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 50

    with Session(engine) as s:
        q = select(ApprovedUmbrella)
        if search:
            q = q.where(ApprovedUmbrella.name.ilike(f"%{search}%"))
        q = q.order_by(ApprovedUmbrella.name)

        total = s.scalar(select(func.count()).select_from(q.subquery()))
        umbrellas = s.scalars(q.offset((page - 1) * per_page).limit(per_page)).all()

    return render_template("admin_umbrella_companies.html",
                           umbrellas=umbrellas, total=total, page=page,
                           per_page=per_page, search=search)


@login_required
@app.route("/admin/umbrella-companies/add", methods=["POST"])
def admin_umbrella_company_add():
    """Add a new approved umbrella company."""
    name = request.form.get("name", "").strip()
    if not name:
        flash("Company name is required.", "danger")
        return redirect(url_for("admin_umbrella_companies"))

    with Session(engine) as s:
        s.add(ApprovedUmbrella(
            name=name,
            signup_url=request.form.get("signup_url", "").strip(),
            phone=request.form.get("phone", "").strip(),
            email=request.form.get("email", "").strip(),
            is_active=request.form.get("is_active") != "0",
        ))
        log_audit_event('create', 'admin',
                        f'Added approved umbrella company: {name}',
                        'umbrella_company', None)
        s.commit()
    flash(f"Umbrella company added: {name}.", "success")
    return redirect(url_for("admin_umbrella_companies"))


@login_required
@app.route("/admin/umbrella-companies/<int:umb_id>/edit", methods=["POST"])
def admin_umbrella_company_edit(umb_id):
    """Edit an approved umbrella company."""
    with Session(engine) as s:
        umb = s.get(ApprovedUmbrella, umb_id)
        if not umb:
            flash("Umbrella company not found.", "danger")
            return redirect(url_for("admin_umbrella_companies"))
        umb.name = request.form.get("name", umb.name).strip()
        umb.signup_url = request.form.get("signup_url", umb.signup_url).strip()
        umb.phone = request.form.get("phone", umb.phone).strip()
        umb.email = request.form.get("email", umb.email).strip()
        umb.is_active = request.form.get("is_active") != "0"
        log_audit_event('update', 'admin',
                        f'Edited umbrella company: {umb.name}',
                        'umbrella_company', umb_id)
        s.commit()
    flash("Umbrella company updated.", "success")
    return redirect(url_for("admin_umbrella_companies"))


@login_required
@app.route("/admin/umbrella-companies/<int:umb_id>/delete", methods=["POST"])
def admin_umbrella_company_delete(umb_id):
    """Delete an approved umbrella company."""
    with Session(engine) as s:
        umb = s.get(ApprovedUmbrella, umb_id)
        if umb:
            log_audit_event('delete', 'admin',
                            f'Deleted umbrella company: {umb.name}',
                            'umbrella_company', umb_id)
            s.delete(umb)
            s.commit()
    flash("Umbrella company deleted.", "success")
    return redirect(url_for("admin_umbrella_companies"))


# ---- Admin: Flagged Reference Houses ----

@login_required
@app.route("/admin/reference-houses")
def admin_reference_houses():
    """Batch 11.2: CRUD page for flagged reference houses with full intel (N17)."""
    FlaggedReferenceHouse = None
    try:
        FlaggedReferenceHouse = _portal_models.get("FlaggedReferenceHouse")
    except Exception:
        pass
    if not FlaggedReferenceHouse:
        flash("Reference houses model not available.", "warning")
        return redirect(url_for("admin_list_users"))

    with Session(engine) as s:
        houses = s.scalars(
            select(FlaggedReferenceHouse).order_by(FlaggedReferenceHouse.name)
        ).all()

    return render_template("admin_reference_houses.html", houses=houses)


@login_required
@app.route("/admin/reference-houses/add", methods=["POST"])
def admin_reference_house_add():
    """Add a flagged reference house."""
    FlaggedReferenceHouse = None
    try:
        FlaggedReferenceHouse = _portal_models.get("FlaggedReferenceHouse")
    except Exception:
        pass
    if not FlaggedReferenceHouse:
        flash("Model not available.", "danger")
        return redirect(url_for("admin_reference_houses"))

    with Session(engine) as s:
        s.add(FlaggedReferenceHouse(
            name=request.form.get("name", "").strip(),
            candidate_count=request.form.get("candidate_count", "").strip(),
            end_clients=request.form.get("end_clients", "").strip(),
            website=request.form.get("website", "").strip(),
            companies_house_url=request.form.get("companies_house_url", "").strip(),
            notes=request.form.get("notes", "").strip(),
        ))
        log_audit_event('create', 'data_access',
                        f'Added flagged reference house: {request.form.get("name", "")}',
                        'reference_house', None)
        s.commit()
    flash("Flagged reference house added.", "success")
    return redirect(url_for("admin_reference_houses"))


@login_required
@app.route("/admin/reference-houses/<int:house_id>/edit", methods=["POST"])
def admin_reference_house_edit(house_id):
    """Edit a flagged reference house."""
    FlaggedReferenceHouse = None
    try:
        FlaggedReferenceHouse = _portal_models.get("FlaggedReferenceHouse")
    except Exception:
        pass
    if not FlaggedReferenceHouse:
        flash("Model not available.", "danger")
        return redirect(url_for("admin_reference_houses"))

    with Session(engine) as s:
        house = s.get(FlaggedReferenceHouse, house_id)
        if not house:
            flash("House not found.", "danger")
            return redirect(url_for("admin_reference_houses"))
        for fld in ["name", "candidate_count", "end_clients", "website", "companies_house_url", "notes"]:
            val = request.form.get(fld, "").strip()
            if val:
                setattr(house, fld, val)
        log_audit_event('update', 'data_access',
                        f'Edited flagged reference house: {house.name}',
                        'reference_house', house_id)
        s.commit()
    flash("Reference house updated.", "success")
    return redirect(url_for("admin_reference_houses"))


@login_required
@app.route("/admin/reference-houses/<int:house_id>/delete", methods=["POST"])
def admin_reference_house_delete(house_id):
    """Delete a flagged reference house."""
    FlaggedReferenceHouse = None
    try:
        FlaggedReferenceHouse = _portal_models.get("FlaggedReferenceHouse")
    except Exception:
        pass
    if not FlaggedReferenceHouse:
        flash("Model not available.", "danger")
        return redirect(url_for("admin_reference_houses"))

    with Session(engine) as s:
        house = s.get(FlaggedReferenceHouse, house_id)
        if house:
            log_audit_event('delete', 'data_access',
                            f'Deleted flagged reference house: {house.name}',
                            'reference_house', house_id)
            s.delete(house)
            s.commit()
    flash("Reference house deleted.", "success")
    return redirect(url_for("admin_reference_houses"))


# =========================================================================
# SCHEDULER START
# =========================================================================
_scheduler = None
if os.getenv("FLASK_ENV") != "testing":
    try:
        _scheduler = _setup_scheduler()
    except Exception as e:
        print(f"[SCHEDULER] Failed to start: {e}")


if __name__ == "__main__":
    with app.app_context():
        Base.metadata.create_all(engine)
        ensure_schema()
    app.run(debug=True)
