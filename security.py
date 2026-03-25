"""
Security middleware and utilities for CREST-compliant deployment.
"""
import os
import hashlib
import hmac
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
from functools import wraps
from flask import request, session, abort, current_app, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import logging

# Configure audit logger
audit_logger = logging.getLogger('security_audit')
audit_logger.setLevel(logging.INFO)

# Use stdout for Railway/production (no filesystem access)
if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('FLASK_ENV') == 'production':
    handler = logging.StreamHandler()  # Log to stdout
else:
    # Only use file logging in local dev
    os.makedirs('logs', exist_ok=True)
    handler = logging.FileHandler('logs/security_audit.log')

handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
audit_logger.addHandler(handler)


def init_security(app):
    """
    Initialize all security middleware and configurations.
    Call this after creating the Flask app instance.
    """
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # 1. HTTPS Enforcement and Security Headers (Talisman)
    csp = {
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            "'unsafe-inline'",  # Required for inline scripts (minimize usage)
            "'unsafe-eval'",    # Required for some JS frameworks
            'cdn.jsdelivr.net',
            'cdnjs.cloudflare.com',
            'static.sumsub.com',  # SumSub KYC SDK
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            'cdn.jsdelivr.net',
            'cdnjs.cloudflare.com',
        ],
        'img-src': ["'self'", 'data:', 'https:'],
        'font-src': ["'self'", 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com'],
        'connect-src': [
            "'self'",
            'api.sumsub.com',
            'api.trustid.co.uk',
        ],
        'frame-src': ["'self'", 'https:'],  # For e-sign iframes
    }
    
    # Only enforce HTTPS in production (not in local dev)
    force_https = os.getenv('FLASK_ENV') == 'production'
    
    # Initialize Talisman - Railway handles HTTPS at edge, so we don't force redirect
    # But we still set secure headers for production
    Talisman(app,
        force_https=False,  # Railway handles HTTPS at edge
        strict_transport_security=True if force_https else False,
        strict_transport_security_max_age=31536000,  # 1 year
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src'],
        feature_policy={
            'geolocation': "'none'",
            'microphone': "'none'",
            'camera': "'none'",
            'payment': "'none'",
        },
        referrer_policy='strict-origin-when-cross-origin',
        frame_options='SAMEORIGIN',
        # Note: content_type_options is enabled by default in Talisman 1.1.0
    )
    
    # 2. Rate Limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["1000 per day", "100 per hour"],
        storage_uri="memory://",  # Use Redis in production: redis://localhost:6379
        strategy="fixed-window",
    )
    
    # 3. Session Security Configuration
    # SESSION_COOKIE_DOMAIN=None means cookies are scoped to exact hostname
    # This prevents cookie leakage between portal.* and app.* subdomains
    cookie_domain = os.getenv('SESSION_COOKIE_DOMAIN') or None

    app.config.update(
        # Session cookies — subdomain-isolated
        SESSION_COOKIE_DOMAIN=cookie_domain,       # None = exact host only (most secure)
        SESSION_COOKIE_SECURE=force_https,          # HTTPS only
        SESSION_COOKIE_HTTPONLY=True,               # No JavaScript access
        SESSION_COOKIE_SAMESITE='Strict',           # No cross-subdomain cookie sending
        PERMANENT_SESSION_LIFETIME=timedelta(hours=2),  # 2 hour timeout
        
        # File upload security
        MAX_CONTENT_LENGTH=25 * 1024 * 1024,        # 25MB max upload
        
        # CSRF protection (Flask-WTF)
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_TIME_LIMIT=None,                   # Token doesn't expire
        
        # Security headers
        SEND_FILE_MAX_AGE_DEFAULT=300,              # 5 minutes cache
    )
    
    return limiter


def audit_log(event_type, user_id=None, details=None):
    """
    Log security-relevant events for audit trail.
    
    Args:
        event_type: Type of event (login, logout, access_denied, etc.)
        user_id: User ID involved
        details: Additional context
    """
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event': event_type,
        'user_id': user_id,
        'ip': request.remote_addr if request else None,
        'user_agent': request.user_agent.string if request else None,
        'details': details,
    }
    audit_logger.info(f"AUDIT: {log_entry}")


# MFA/2FA Implementation using TOTP

def generate_mfa_secret():
    """Generate a new TOTP secret for MFA setup."""
    return pyotp.random_base32()


def generate_mfa_qr_code(secret, email, app_name="ATS Onboarding"):
    """
    Generate QR code for MFA setup.
    Returns base64-encoded PNG image.
    """
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=app_name
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def verify_mfa_token(secret, token):
    """
    Verify TOTP token against secret.
    Returns True if valid, False otherwise.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)  # Allow 30s window


def require_mfa(f):
    """
    Decorator to require MFA for admin routes.
    Use after @login_required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('mfa_verified'):
            audit_log('mfa_required', user_id=session.get('user_id'))
            return abort(403, "MFA verification required")
        return f(*args, **kwargs)
    return decorated_function


# Magic Link Authentication for Candidates

def generate_magic_link_token(candidate_id, email):
    """
    Generate secure token for magic link authentication.
    Token includes: candidate_id, email, timestamp, HMAC signature.
    """
    from itsdangerous import URLSafeTimedSerializer
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    payload = {
        'candidate_id': candidate_id,
        'email': email,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    token = serializer.dumps(payload, salt='candidate-magic-link')
    return token


def verify_magic_link_token(token, max_age=3600):
    """
    Verify magic link token.
    Returns (candidate_id, email) if valid, None otherwise.
    max_age: token expiration in seconds (default 1 hour)
    """
    from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
    
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    
    try:
        payload = serializer.loads(token, salt='candidate-magic-link', max_age=max_age)
        return payload['candidate_id'], payload['email']
    except (BadSignature, SignatureExpired):
        return None, None


# File Upload Security

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
}


def validate_file_upload(file_storage):
    """
    Validate uploaded file for security.
    Returns (is_valid, error_message).
    """
    if not file_storage or not file_storage.filename:
        return False, "No file provided"
    
    filename = file_storage.filename.lower()
    
    # Check extension
    if '.' not in filename:
        return False, "File must have an extension"
    
    ext = filename.rsplit('.', 1)[1]
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type .{ext} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size (using tell() to get size)
    file_storage.seek(0, 2)  # Seek to end
    size = file_storage.tell()
    file_storage.seek(0)  # Reset to beginning
    
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 25 * 1024 * 1024)
    if size > max_size:
        return False, f"File too large. Max size: {max_size / 1024 / 1024:.1f}MB"
    
    if size == 0:
        return False, "File is empty"
    
    # TODO: Add MIME type validation using python-magic
    # TODO: Add virus scanning using ClamAV (clamd)
    
    return True, None


def sanitize_filename(filename):
    """
    Sanitize filename to prevent path traversal attacks.
    """
    from werkzeug.utils import secure_filename
    return secure_filename(filename)


# Password Security Helpers

def validate_password_strength(password):
    """
    Validate password meets minimum security requirements.
    Returns (is_valid, error_message).
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letters"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain lowercase letters"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain numbers"
    
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False, "Password must contain special characters"
    
    return True, None


# CSRF Token Helpers (for AJAX requests)

def generate_csrf_token():
    """Generate CSRF token for current session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = os.urandom(32).hex()
    return session['_csrf_token']


def validate_csrf_token(token):
    """Validate CSRF token from request."""
    return token == session.get('_csrf_token')


# IP-based Security

def check_ip_whitelist():
    """
    Check if request IP is in whitelist (for admin access).
    Set ADMIN_IP_WHITELIST env var with comma-separated IPs.
    """
    whitelist = os.getenv('ADMIN_IP_WHITELIST', '').split(',')
    if not whitelist or whitelist == ['']:
        return True  # No whitelist configured
    
    client_ip = request.remote_addr
    return client_ip in whitelist


# Security Headers for API responses

def add_security_headers(response):
    """Add security headers to response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response
