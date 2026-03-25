# associate_portal.py — Associate (Candidate) Portal Blueprint
# Registered at /portal/ prefix
from __future__ import annotations

import os
import io
import json
import base64
import importlib
import secrets
from datetime import datetime, timedelta, date
from functools import wraps
from typing import Optional, List
from uuid import uuid4

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app,
    abort,
    jsonify,
    send_file,
)
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session as SASession
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Date,
    ForeignKey,
    select,
    Float,
)

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

associate_bp = Blueprint(
    "associate",
    __name__,
    template_folder="templates_associate",
    static_folder="static_associate",
    static_url_path="/associate_static",
)


def _apply_rate_limits(app):
    """Apply rate limits to portal auth routes. Called after blueprint registration."""
    try:
        from app import limiter
        if limiter and hasattr(limiter, 'limit'):
            limiter.limit("10 per minute")(login)
            limiter.limit("10 per minute")(register)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Lazy imports to avoid circular import with app.py
# ---------------------------------------------------------------------------

def _app_module():
    """Return the app module lazily."""
    return importlib.import_module("app")


def _engine():
    return getattr(_app_module(), "engine")


def _base():
    return getattr(_app_module(), "Base")


def _model(name: str):
    """Load a model class from app by name. Returns None if missing."""
    try:
        return getattr(_app_module(), name, None)
    except Exception:
        return None


def _load(name: str):
    """Load any attribute from app at runtime."""
    try:
        return getattr(_app_module(), name, None)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# New models (Associate Portal specific)
# ---------------------------------------------------------------------------
# These are defined lazily so that Base is resolved at import-time of app.py
# We use a module-level flag to avoid re-defining.

_MODELS_DEFINED = False
_models = {}  # Model registry for external access


def _ensure_models():
    """Define portal-specific SQLAlchemy models once, using app.Base."""
    global _MODELS_DEFINED
    if _MODELS_DEFINED:
        return
    _MODELS_DEFINED = True

    Base = _base()

    # Guard against re-registration if tables already mapped
    if "associate_profiles" in Base.metadata.tables:
        # Populate _models from existing registry so external access works
        for mapper in Base.registry.mappers:
            cls = mapper.class_
            if cls.__name__ in ("TimesheetConfig", "TimesheetEntry", "TimesheetExpense"):
                _models[cls.__name__] = cls
        return

    class AssociateProfile(Base):
        __tablename__ = "associate_profiles"
        id = Column(Integer, primary_key=True, autoincrement=True)
        candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, unique=True, index=True)
        title = Column(String(20), default="")
        first_name = Column(String(200), default="")
        surname = Column(String(200), default="")
        aliases = Column(Text, default="")
        previous_names = Column(Text, default="")
        previous_first_names = Column(String(500), default="")
        previous_surnames = Column(String(500), default="")
        unsubscribed = Column(Boolean, default=False)
        profile_picture = Column(String(500), default="")
        dob = Column(Date, nullable=True)
        address_line1 = Column(String(500), default="")
        address_line2 = Column(String(500), default="")
        city = Column(String(200), default="")
        postcode = Column(String(20), default="")
        country = Column(String(100), default="United Kingdom")
        contact_number = Column(String(50), default="")
        emergency_contact_name = Column(String(200), default="")
        emergency_contact_phone = Column(String(50), default="")
        emergency_contact_relationship = Column(String(100), default="")
        current_salary = Column(String(100), default="")
        expected_salary = Column(String(100), default="")
        available_from = Column(Date, nullable=True)
        national_insurance_number = Column(String(20), default="")
        # P8: Gender field for vetting checks
        gender = Column(String(20), default="")
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class CompanyDetails(Base):
        __tablename__ = "company_details"
        id = Column(Integer, primary_key=True, autoincrement=True)
        candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, unique=True, index=True)
        contracting_type = Column(String(20), default="")  # umbrella / limited
        company_name = Column(String(300), default="")
        registration_number = Column(String(50), default="")
        vat_registered = Column(Boolean, default=False)
        vat_number = Column(String(50), default="")
        bank_account_number = Column(String(20), default="")
        bank_sort_code = Column(String(10), default="")
        umbrella_company_name = Column(String(300), default="")
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class ConsentRecord(Base):
        __tablename__ = "consent_records"
        id = Column(Integer, primary_key=True, autoincrement=True)
        candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
        consent_given = Column(Boolean, default=False)
        secondary_employment = Column(Boolean, default=False)
        secondary_employment_details = Column(Text, default="")
        legal_name = Column(String(300), default="")
        signed_date = Column(DateTime, nullable=True)
        ip_address = Column(String(50), default="")
        created_at = Column(DateTime, default=datetime.utcnow)

    class DeclarationRecord(Base):
        __tablename__ = "declaration_records"
        id = Column(Integer, primary_key=True, autoincrement=True)
        candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
        work_restrictions = Column(Boolean, default=False)
        work_restrictions_detail = Column(Text, default="")
        criminal_convictions = Column(Boolean, default=False)
        criminal_convictions_detail = Column(Text, default="")
        ccj_debt = Column(Boolean, default=False)
        ccj_debt_detail = Column(Text, default="")
        bankruptcy = Column(Boolean, default=False)
        bankruptcy_detail = Column(Text, default="")
        dismissed = Column(Boolean, default=False)
        dismissed_detail = Column(Text, default="")
        referencing_issues = Column(Boolean, default=False)
        referencing_issues_detail = Column(Text, default="")
        disclosure_text = Column(Text, default="")
        legal_name = Column(String(300), default="")
        signed_date = Column(DateTime, nullable=True)
        ip_address = Column(String(50), default="")
        created_at = Column(DateTime, default=datetime.utcnow)

    class EmploymentHistory(Base):
        __tablename__ = "employment_history"
        id = Column(Integer, primary_key=True, autoincrement=True)
        candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
        company_name = Column(String(300), default="")
        agency_name = Column(String(300), default="")
        referee_email = Column(String(300), default="")
        company_address = Column(Text, default="")
        start_date = Column(Date, nullable=True)
        end_date = Column(Date, nullable=True)
        job_title = Column(String(300), default="")
        reason_for_leaving = Column(Text, default="")
        is_gap = Column(Boolean, default=False)
        gap_reason = Column(Text, default="")
        gap_evidence_doc_id = Column(Integer, nullable=True)
        permission_to_request = Column(Boolean, default=True)
        permission_delay_reason = Column(Text, default="")
        permission_future_date = Column(Date, nullable=True)
        reference_status = Column(String(30), default="not_sent")  # not_sent/sent/received/flagged
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class QualificationRecord(Base):
        __tablename__ = "qualification_records"
        id = Column(Integer, primary_key=True, autoincrement=True)
        candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
        qualification_name = Column(String(300), default="")
        qualification_type = Column(String(100), default="")
        grade = Column(String(100), default="")
        institution = Column(String(300), default="")
        start_date = Column(Date, nullable=True)
        end_date = Column(Date, nullable=True)
        permission_to_request = Column(Boolean, default=True)
        permission_delay_reason = Column(Text, default="")
        created_at = Column(DateTime, default=datetime.utcnow)

    class ReferenceContact(Base):
        __tablename__ = "reference_contacts"
        id = Column(Integer, primary_key=True, autoincrement=True)
        company_name = Column(String(300), nullable=False, index=True)
        referee_email = Column(String(300), default="")
        last_amended = Column(DateTime, default=datetime.utcnow)

    class FlaggedReferenceHouse(Base):
        __tablename__ = "flagged_reference_houses"
        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String(300), nullable=False, index=True)
        candidate_count = Column(Integer, default=0)
        end_clients = Column(Text, default="")
        website = Column(String(500), default="")
        companies_house_url = Column(String(500), default="")
        notes = Column(Text, default="")
        created_at = Column(DateTime, default=datetime.utcnow)

    class TimesheetConfig(Base):
        """Admin-configurable timesheet settings per engagement."""
        __tablename__ = "timesheet_configs"
        __table_args__ = {"extend_existing": True}
        id = Column(Integer, primary_key=True)
        engagement_id = Column(Integer, index=True)
        time_types = Column(Text, default='["Standard Time","Overtime","Holiday","Sickness","Unplanned Absence"]')  # JSON
        overtime_enabled = Column(Boolean, default=False)
        overtime_multiplier = Column(Float, default=1.5)
        overtime_rate_type = Column(String(20), default="hourly")  # hourly or daily
        expense_enabled = Column(Boolean, default=False)
        expense_types = Column(Text, default='["Travel","Accommodation","Meals","Equipment","Other"]')  # JSON
        expense_limits = Column(Text, default="{}")  # JSON: {"Travel": 100}
        day_rate = Column(Float, default=0)
        overtime_rate = Column(Float, default=0)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class TimesheetEntry(Base):
        """Individual day entry for a timesheet (one row per time-type per day)."""
        __tablename__ = "timesheet_entries"
        __table_args__ = {"extend_existing": True}
        id = Column(Integer, primary_key=True)
        timesheet_id = Column(Integer, index=True)
        entry_date = Column(Date)
        time_type = Column(String(100))  # "Standard Time", "Overtime", etc.
        value = Column(Float, default=0)  # 1.0=full day, 0.5=half day, or hours for OT
        value_unit = Column(String(20), default="days")  # "days" or "hours"
        created_at = Column(DateTime, default=datetime.utcnow)

    class TimesheetExpense(Base):
        """Expense line item attached to a timesheet."""
        __tablename__ = "timesheet_expenses"
        __table_args__ = {"extend_existing": True}
        id = Column(Integer, primary_key=True)
        timesheet_id = Column(Integer, index=True)
        expense_type = Column(String(100))
        description = Column(String(500))
        amount = Column(Float, default=0)
        receipt_doc_id = Column(Integer, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)

    # P7: 5-year address history for DBS/Credit checks
    class AddressHistory(Base):
        """Associate address history — 5 years required for DBS/Credit checks."""
        __tablename__ = "address_history"
        __table_args__ = {"extend_existing": True}
        id = Column(Integer, primary_key=True)
        candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False, index=True)
        address_line1 = Column(String(500), default="")
        address_line2 = Column(String(500), default="")
        city = Column(String(200), default="")
        postcode = Column(String(20), default="")
        country = Column(String(100), default="United Kingdom")
        from_date = Column(Date, nullable=True)
        to_date = Column(Date, nullable=True)
        is_current = Column(Boolean, default=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    # Register models in the _models dict for external access
    _models["TimesheetConfig"] = TimesheetConfig
    _models["TimesheetEntry"] = TimesheetEntry
    _models["TimesheetExpense"] = TimesheetExpense
    _models["AddressHistory"] = AddressHistory


def _portal_model(name: str):
    """Get a portal-specific model class by table registration in Base.metadata."""
    _ensure_models()
    Base = _base()
    # Models are registered via Base; find the class in Base._decl_class_registry or via metadata
    # Since we defined them inside _ensure_models, we need to resolve via the registry
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if cls.__name__ == name:
            return cls
    return None


# ---------------------------------------------------------------------------
# Session / Auth helpers
# ---------------------------------------------------------------------------

def _get_associate_id() -> Optional[int]:
    return session.get("associate_user_id")


def _get_current_associate():
    """Return the Candidate object for the logged-in associate, or None."""
    cid = _get_associate_id()
    if not cid:
        return None
    Candidate = _model("Candidate")
    if not Candidate:
        return None
    with SASession(_engine()) as s:
        return s.get(Candidate, cid)


def _require_login(f):
    """Decorator: redirect to associate login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _get_associate_id():
            flash("Please sign in to access the portal.", "warning")
            return redirect(url_for("associate.login", next=request.url))
        return f(*args, **kwargs)
    return decorated


def _sanitise(value: str) -> str:
    """Sanitise user input with bleach."""
    try:
        import bleach
        return bleach.clean(value or "", strip=True)
    except ImportError:
        # Fallback: basic HTML entity escaping
        return (value or "").replace("<", "&lt;").replace(">", "&gt;")


def _portal_signer():
    """Timed serializer for magic link tokens."""
    from itsdangerous import URLSafeTimedSerializer
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"], salt="associate-portal-link"
    )


def _send_magic_link(email: str, name: str, is_signup: bool = True, next_url: str = ""):
    """Generate and send a magic-link email to the associate."""
    send_email = _load("send_email")
    PORTAL_BASE_URL = _load("PORTAL_BASE_URL") or _load("APP_BASE_URL") or "http://localhost:5000"

    token_data = {"email": email, "name": name, "is_signup": is_signup}
    if next_url:
        token_data["next"] = next_url
    token = _portal_signer().dumps(token_data)
    verify_url = f"{PORTAL_BASE_URL}/portal/verify-email?token={token}"

    subject = (
        "Complete Your Registration - Optimus Solutions"
        if is_signup
        else "Password Reset - Optimus Solutions"
    )

    html_body = f"""
    <div style="font-family:'Inter',Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <div style="background:#0a1628;padding:30px;border-radius:12px 12px 0 0;text-align:center;">
            <h1 style="color:#00d4ff;margin:0;font-size:24px;">Optimus Solutions</h1>
            <p style="color:#94a3b8;margin:10px 0 0;font-size:14px;">Associate Portal</p>
        </div>
        <div style="background:#fff;padding:40px 30px;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;">
            <h2 style="color:#0a1628;margin:0 0 20px;font-size:20px;">Hello, {_sanitise(name)}!</h2>
            <p style="color:#334155;margin:0 0 20px;line-height:1.6;">
                {'Thank you for registering. Click below to verify your email and set up your account.' if is_signup else 'Click below to reset your password.'}
            </p>
            <div style="text-align:center;margin:30px 0;">
                <a href="{verify_url}" style="background:#0066cc;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:600;display:inline-block;">
                    {'Complete Registration' if is_signup else 'Reset Password'}
                </a>
            </div>
            <p style="color:#64748b;font-size:14px;margin:20px 0 0;">
                This link expires in 30 minutes. If you did not request this, ignore this email.
            </p>
        </div>
        <div style="text-align:center;padding:20px;color:#94a3b8;font-size:12px;">
            <p>&copy; 2026 Optimus Solutions. All rights reserved.</p>
        </div>
    </div>
    """

    if callable(send_email):
        send_email(to_email=email, subject=subject, html_body=html_body)
        current_app.logger.info("Associate magic link sent to %s", email)
    else:
        current_app.logger.warning("send_email not available; magic link NOT sent to %s", email)


def _audit_portal(event_type: str, action: str, candidate_id: int = None,
                   details: dict = None, status: str = "success"):
    """Log audit event for portal activity. Non-blocking — never raises."""
    try:
        log_fn = _load("log_audit_event")
        if log_fn:
            log_fn(event_type, "portal_auth", action,
                   resource_type="candidate", resource_id=candidate_id,
                   details=details, status=status)
    except Exception:
        pass  # Audit logging must never break the portal


def _safe_next_url(url: str) -> str:
    """Validate redirect URL to prevent open redirect attacks."""
    if not url or not isinstance(url, str):
        return url_for("associate.dashboard")
    url = url.strip()
    # Must be a relative path starting with / but not //
    if url.startswith("/") and not url.startswith("//"):
        return url
    return url_for("associate.dashboard")


def _validate_password(password: str) -> tuple:
    """Return (is_valid, error_message)."""
    if len(password) < 12:
        return False, "Password must be at least 12 characters."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
        return False, "Password must contain at least one special character."
    return True, ""


def _upload_dir() -> str:
    """Return the absolute upload directory for associate docs, creating it if needed."""
    root = current_app.root_path
    d = os.path.join(root, "static", "uploads", "associate_docs")
    os.makedirs(d, exist_ok=True)
    return d


def _save_file(file_storage) -> Optional[dict]:
    """Save an uploaded file. Returns dict(filename, original_name) or None."""
    if not file_storage or not (file_storage.filename or "").strip():
        return None
    orig = secure_filename(file_storage.filename)
    ext = os.path.splitext(orig)[1].lower() or ".pdf"
    new_name = f"{uuid4().hex}{ext}"
    dest = os.path.join(_upload_dir(), new_name)
    file_storage.save(dest)
    return {"filename": f"uploads/associate_docs/{new_name}", "original_name": orig}


def _add_note(s, candidate_id: int, content: str, note_type: str = "system"):
    """Create a CandidateNote audit entry."""
    CandidateNote = _model("CandidateNote")
    if not CandidateNote:
        return
    try:
        note = CandidateNote(
            candidate_id=candidate_id,
            user_email="associate-portal",
            note_type=note_type,
            content=_sanitise(content),
            created_at=datetime.utcnow(),
        )
        s.add(note)
    except Exception:
        current_app.logger.exception("Failed to add CandidateNote")


def _parse_date(value: str) -> Optional[date]:
    """Parse a date string (YYYY-MM-DD) safely."""
    if not value:
        return None
    try:
        from dateutil import parser as dtparser
        return dtparser.parse(value).date()
    except Exception:
        return None


def _parse_bool(value) -> bool:
    """Parse a form boolean value."""
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# Profile completeness calculation
# ---------------------------------------------------------------------------

def _calc_completeness(s, candidate_id: int) -> dict:
    """
    Calculate profile completeness percentages for the three dashboard sections.
    Returns dict with personal_pct, company_pct, checks_pct, overall_pct.
    """
    Candidate = _model("Candidate")
    AssociateProfile = _portal_model("AssociateProfile")
    CompanyDetails = _portal_model("CompanyDetails")
    VettingCheck = _model("VettingCheck")
    ConsentRecord = _portal_model("ConsentRecord")
    DeclarationRecord = _portal_model("DeclarationRecord")
    Document = _model("Document")
    EmploymentHistory = _portal_model("EmploymentHistory")

    # --- Personal Information ---
    personal_score = 0
    personal_total = 8

    cand = s.get(Candidate, candidate_id) if Candidate else None
    if cand:
        if cand.name:
            personal_score += 1
        if cand.email:
            personal_score += 1
        if cand.phone:
            personal_score += 1

    profile = None
    if AssociateProfile:
        profile = s.query(AssociateProfile).filter_by(candidate_id=candidate_id).first()
    if profile:
        if profile.first_name:
            personal_score += 1
        if profile.surname:
            personal_score += 1
        if profile.dob:
            personal_score += 1
        if profile.address_line1:
            personal_score += 1
        if profile.emergency_contact_name:
            personal_score += 1

    personal_pct = int(round(personal_score / personal_total * 100)) if personal_total else 0

    # --- Company Details ---
    company_score = 0
    company_total = 3
    comp = None
    if CompanyDetails:
        comp = s.query(CompanyDetails).filter_by(candidate_id=candidate_id).first()
    if comp:
        if comp.contracting_type:
            company_score += 1
        if comp.contracting_type == "umbrella" and comp.umbrella_company_name:
            company_score += 1
        elif comp.contracting_type == "limited" and comp.company_name:
            company_score += 1
        if comp.contracting_type == "limited" and comp.registration_number:
            company_score += 1
        elif comp.contracting_type == "umbrella":
            company_score += 1  # no reg number needed

    company_pct = int(round(company_score / company_total * 100)) if company_total else 0

    # --- Background Checks & References ---
    checks_score = 0
    checks_total = 5

    # Consent form
    if ConsentRecord:
        consent = s.query(ConsentRecord).filter_by(candidate_id=candidate_id).first()
        if consent and consent.consent_given:
            checks_score += 1

    # Declaration form
    if DeclarationRecord:
        decl = s.query(DeclarationRecord).filter_by(candidate_id=candidate_id).first()
        if decl and decl.legal_name:
            checks_score += 1

    # Documents uploaded
    if Document:
        doc_count = s.query(Document).filter_by(candidate_id=candidate_id).count()
        if doc_count >= 2:
            checks_score += 1

    # Employment history entries
    if EmploymentHistory:
        emp_count = s.query(EmploymentHistory).filter_by(candidate_id=candidate_id).filter(
            EmploymentHistory.is_gap == False  # noqa: E712
        ).count()
        if emp_count >= 1:
            checks_score += 1

    # Vetting checks
    if VettingCheck:
        completed = s.query(VettingCheck).filter_by(candidate_id=candidate_id).filter(
            VettingCheck.status.in_(["Complete", "Completed", "Pass"])
        ).count()
        if completed >= 1:
            checks_score += 1

    checks_pct = int(round(checks_score / checks_total * 100)) if checks_total else 0

    overall_pct = int(round((personal_pct + company_pct + checks_pct) / 3))

    return {
        "personal_pct": min(personal_pct, 100),
        "company_pct": min(company_pct, 100),
        "checks_pct": min(checks_pct, 100),
        "overall_pct": min(overall_pct, 100),
    }


# ---------------------------------------------------------------------------
# Gap detection for employment history
# ---------------------------------------------------------------------------

def _detect_gaps(entries: list, threshold_days: int = 90) -> list:
    """
    Given a list of EmploymentHistory objects sorted by start_date,
    return a list of dicts describing gaps > threshold_days.
    """
    gaps = []
    # Sort by start_date ascending, filter out entries without dates
    dated = [e for e in entries if e.start_date and e.end_date]
    dated.sort(key=lambda e: e.start_date)

    for i in range(len(dated) - 1):
        gap_start = dated[i].end_date
        gap_end = dated[i + 1].start_date
        if gap_start and gap_end:
            delta = (gap_end - gap_start).days
            if delta > threshold_days:
                gaps.append({
                    "from_date": gap_start,
                    "to_date": gap_end,
                    "days": delta,
                    "after_company": dated[i].company_name,
                    "before_company": dated[i + 1].company_name,
                })
    return gaps


# ---------------------------------------------------------------------------
# Ensure tables exist
# ---------------------------------------------------------------------------

@associate_bp.before_app_request
def _create_portal_tables():
    """Create portal-specific tables on first request if they don't exist."""
    if getattr(current_app, "_associate_tables_created", False):
        return
    try:
        _ensure_models()
        Base = _base()
        engine = _engine()
        # Only create tables that don't yet exist (checkfirst=True is default)
        Base.metadata.create_all(engine, checkfirst=True)
        current_app._associate_tables_created = True
    except Exception as exc:
        current_app.logger.warning("Could not create associate portal tables: %s", exc)
        current_app._associate_tables_created = True  # Don't retry every request


@associate_bp.context_processor
def _inject_associate():
    """Inject the associate (Candidate) object into all portal templates."""
    cand_id = session.get("associate_user_id")
    if not cand_id:
        return {"associate": None}
    try:
        Candidate = _model("Candidate")
        engine = _engine()
        if Candidate and engine:
            with SASession(engine) as s:
                cand = s.get(Candidate, cand_id)
                if cand:
                    # Return a simple namespace so it's session-safe
                    from types import SimpleNamespace
                    return {"associate": SimpleNamespace(
                        id=cand.id,
                        name=cand.name or "",
                        email=cand.email or "",
                        phone=cand.phone or "",
                    )}
        return {"associate": None}
    except Exception:
        return {"associate": None}


# =========================================================================
# AUTH ROUTES
# =========================================================================

@associate_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login with email/password; redirect to 2FA if enabled.
    Rate limited to 10/minute via blueprint before_request (see _rate_limit_login)."""
    Candidate = _model("Candidate")
    engine = _engine()
    next_url = _safe_next_url(request.args.get("next") or request.form.get("next") or "")

    if request.method == "GET":
        return render_template("associate/auth_login.html", next=next_url)

    email = _sanitise(request.form.get("email", "")).strip().lower()
    password = request.form.get("password", "")

    if not email:
        flash("Please enter your email address.", "danger")
        return redirect(url_for("associate.login", next=next_url))

    with SASession(engine) as s:
        cand = s.query(Candidate).filter(Candidate.email.ilike(email)).first()

        if not cand:
            flash("No account found with that email. Please register first.", "info")
            return redirect(url_for("associate.register", next=next_url))

        if hasattr(cand, "is_locked") and cand.is_locked():
            flash("Account temporarily locked. Please try again later.", "danger")
            return redirect(url_for("associate.login", next=next_url))

        if not cand.password_hash:
            flash("Please complete your account setup first. Check your email for a registration link.", "info")
            return redirect(url_for("associate.login", next=next_url))

        if not cand.check_password(password):
            cand.failed_login_attempts = (cand.failed_login_attempts or 0) + 1
            locked = cand.failed_login_attempts >= 5
            if locked:
                cand.locked_until = datetime.utcnow() + timedelta(minutes=15)
                flash("Too many failed attempts. Account locked for 15 minutes.", "danger")
            else:
                flash("Invalid email or password.", "danger")
            s.commit()
            _audit_portal("login", f"Failed portal login (attempt {cand.failed_login_attempts})",
                          candidate_id=cand.id,
                          details={"locked": locked, "email": email},
                          status="failure")
            return redirect(url_for("associate.login", next=next_url))

        # Password correct
        cand.failed_login_attempts = 0
        cand.locked_until = None

        if cand.totp_enabled and cand.totp_secret:
            session["associate_2fa_pending_id"] = cand.id
            session["associate_2fa_next"] = next_url
            s.commit()
            return redirect(url_for("associate.verify_2fa"))

        # Log in directly
        cand.last_login_at = datetime.utcnow()
        session["associate_user_id"] = cand.id
        s.commit()
        _audit_portal("login", "Portal login (no 2FA)", candidate_id=cand.id)

    flash("Signed in successfully.", "success")
    return redirect(next_url)


@associate_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new associate account; send magic link."""
    Candidate = _model("Candidate")
    engine = _engine()
    next_url = _safe_next_url(request.args.get("next") or request.form.get("next") or "")

    if request.method == "GET":
        return render_template("associate/auth_register.html", next=next_url)

    email = _sanitise(request.form.get("email", "")).strip().lower()
    first_name = _sanitise(request.form.get("first_name", "")).strip()
    surname = _sanitise(request.form.get("surname", "")).strip()
    name = _sanitise(request.form.get("name", "")).strip() or f"{first_name} {surname}".strip()
    phone = _sanitise(request.form.get("phone", "")).strip()

    if not email or not name:
        flash("Please provide your name and email address.", "danger")
        return redirect(url_for("associate.register", next=next_url))

    with SASession(engine) as s:
        existing = s.query(Candidate).filter(Candidate.email.ilike(email)).first()
        if existing:
            if existing.password_hash:
                flash("An account with this email already exists. Please sign in.", "info")
                return redirect(url_for("associate.login", next=next_url))
            # Resend magic link
            try:
                _send_magic_link(email, existing.name or name, is_signup=True, next_url=next_url)
            except Exception as e:
                current_app.logger.exception("Magic link send failed: %s", e)
                flash("Unable to send verification email. Please contact support.", "danger")
                return redirect(url_for("associate.register", next=next_url))
            flash("We have sent you a new verification link.", "info")
            return render_template("associate/auth_check_email.html", email=email)

    # Send email first, then create record
    try:
        _send_magic_link(email, name, is_signup=True, next_url=next_url)
    except Exception as e:
        current_app.logger.exception("Magic link send failed: %s", e)
        flash("Unable to send verification email. Please contact support.", "danger")
        return redirect(url_for("associate.register", next=next_url))

    with SASession(engine) as s:
        existing = s.query(Candidate).filter(Candidate.email.ilike(email)).first()
        if existing:
            flash("Check your email to complete registration.", "success")
            return render_template("associate/auth_check_email.html", email=email)

        cand = Candidate(
            name=name,
            email=email,
            phone=phone,
            email_verified=False,
            source="associate-portal",
        )
        s.add(cand)
        s.commit()

    flash("Check your email to complete registration.", "success")
    return render_template("associate/auth_check_email.html", email=email)


@associate_bp.route("/verify-email", methods=["GET"])
def verify_email():
    """Verify magic-link token and redirect to password setup."""
    from itsdangerous import SignatureExpired, BadSignature

    Candidate = _model("Candidate")
    engine = _engine()
    token = request.args.get("token", "")

    if not token:
        flash("Invalid verification link.", "danger")
        return redirect(url_for("associate.login"))

    try:
        data = _portal_signer().loads(token, max_age=30 * 60)
    except SignatureExpired:
        flash("This link has expired. Please request a new one.", "warning")
        return redirect(url_for("associate.register"))
    except BadSignature:
        flash("Invalid verification link.", "danger")
        return redirect(url_for("associate.login"))

    email = (data.get("email") or "").strip().lower()
    if not email:
        flash("Invalid verification link.", "danger")
        return redirect(url_for("associate.login"))

    with SASession(engine) as s:
        cand = s.query(Candidate).filter(Candidate.email.ilike(email)).first()
        if not cand:
            flash("Account not found. Please register again.", "warning")
            return redirect(url_for("associate.register"))

        cand.email_verified = True
        if hasattr(cand, "email_verified_at"):
            cand.email_verified_at = datetime.utcnow()
        s.commit()

        session["associate_setup_password_id"] = cand.id
        session["associate_setup_password_ts"] = datetime.utcnow().timestamp()
        # Carry next_url from magic link through the setup flow
        token_next = _safe_next_url(data.get("next") or "")
        if token_next:
            session["associate_setup_next"] = token_next

    return redirect(url_for("associate.set_password"))


@associate_bp.route("/set-password", methods=["GET", "POST"])
def set_password():
    """Set password after email verification."""
    Candidate = _model("Candidate")
    engine = _engine()

    cand_id = session.get("associate_setup_password_id")
    setup_ts = session.get("associate_setup_password_ts")
    # S9: Expire setup session keys after 15 minutes
    if not cand_id or (setup_ts and (datetime.utcnow().timestamp() - setup_ts) > 900):
        session.pop("associate_setup_password_id", None)
        session.pop("associate_setup_password_ts", None)
        flash("Please use the link from your email.", "warning")
        return redirect(url_for("associate.login"))

    if request.method == "GET":
        with SASession(engine) as s:
            cand = s.get(Candidate, cand_id)
            if not cand:
                session.pop("associate_setup_password_id", None)
                flash("Account not found.", "danger")
                return redirect(url_for("associate.register"))
            return render_template("associate/auth_set_password.html", name=cand.name, email=cand.email)

    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    with SASession(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            session.pop("associate_setup_password_id", None)
            flash("Account not found.", "danger")
            return redirect(url_for("associate.register"))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("associate/auth_set_password.html", name=cand.name, email=cand.email)

        valid, msg = _validate_password(password)
        if not valid:
            flash(msg, "danger")
            return render_template("associate/auth_set_password.html", name=cand.name, email=cand.email)

        cand.set_password(password)
        s.commit()

        session["associate_setup_2fa_id"] = cand.id
        session["associate_setup_2fa_ts"] = datetime.utcnow().timestamp()
        session.pop("associate_setup_password_id", None)
        session.pop("associate_setup_password_ts", None)

        flash("Password set successfully. Now set up two-factor authentication.", "success")
        return redirect(url_for("associate.setup_2fa"))


@associate_bp.route("/setup-2fa", methods=["GET", "POST"])
def setup_2fa():
    """Set up TOTP 2FA with QR code."""
    import pyotp

    Candidate = _model("Candidate")
    engine = _engine()

    cand_id = session.get("associate_setup_2fa_id")
    setup_ts = session.get("associate_setup_2fa_ts")
    # S9: Expire setup session keys after 15 minutes
    if not cand_id or (setup_ts and (datetime.utcnow().timestamp() - setup_ts) > 900):
        session.pop("associate_setup_2fa_id", None)
        session.pop("associate_setup_2fa_ts", None)
        flash("Session expired. Please sign in again.", "warning")
        return redirect(url_for("associate.login"))

    if request.method == "GET":
        with SASession(engine) as s:
            cand = s.get(Candidate, cand_id)
            if not cand:
                session.pop("associate_setup_2fa_id", None)
                flash("Account not found.", "danger")
                return redirect(url_for("associate.register"))

            if not cand.totp_secret:
                cand.totp_secret = cand.generate_totp_secret()
                s.commit()

            secret = cand.totp_secret
            email = cand.email

        totp = pyotp.TOTP(secret)
        prov_uri = totp.provisioning_uri(name=email, issuer_name="Optimus Solutions Portal")

        # Generate QR code
        qr_data_uri = ""
        try:
            import qrcode as qrlib
            qr = qrlib.QRCode(version=1, box_size=10, border=4)
            qr.add_data(prov_uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            qr_data_uri = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
        except Exception:
            import urllib.parse
            encoded = urllib.parse.quote(prov_uri)
            qr_data_uri = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded}"

        return render_template("associate/auth_setup_2fa.html", qr_url=qr_data_uri, secret=secret, email=email)

    # POST: verify token (field name matches auth_setup_2fa.html: name="totp_code")
    token_code = (request.form.get("totp_code") or request.form.get("token", "")).strip().replace(" ", "")
    if not token_code or len(token_code) != 6 or not token_code.isdigit():
        flash("Please enter a valid 6-digit code.", "danger")
        return redirect(url_for("associate.setup_2fa"))

    with SASession(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            session.pop("associate_setup_2fa_id", None)
            flash("Account not found.", "danger")
            return redirect(url_for("associate.register"))

        if not cand.verify_totp(token_code):
            flash("Invalid code. Please try again.", "danger")
            return redirect(url_for("associate.setup_2fa"))

        cand.totp_enabled = True
        backup_codes = cand.generate_backup_codes(count=10)
        cand.last_login_at = datetime.utcnow()
        s.commit()

        session["associate_user_id"] = cand.id
        session.pop("associate_setup_2fa_id", None)
        session.pop("associate_setup_2fa_next", None)

    setup_next = session.pop("associate_setup_next", "") or ""
    return render_template("associate/auth_backup_codes.html",
                           backup_codes=backup_codes,
                           next_url=setup_next)


@associate_bp.route("/verify-2fa", methods=["GET", "POST"])
def verify_2fa():
    """Verify TOTP during login."""
    Candidate = _model("Candidate")
    engine = _engine()

    cand_id = session.get("associate_2fa_pending_id")
    next_url = _safe_next_url(session.get("associate_2fa_next") or "")

    if not cand_id:
        flash("Please sign in first.", "warning")
        return redirect(url_for("associate.login"))

    if request.method == "GET":
        return render_template("associate/auth_verify_2fa.html")

    # Template sends totp_code or backup_code (auth_verify_2fa.html)
    totp_input = (request.form.get("totp_code") or request.form.get("token", "")).strip().replace(" ", "")
    backup_input = (request.form.get("backup_code", "")).strip().replace(" ", "")
    use_backup = bool(backup_input)
    token_code = backup_input if use_backup else totp_input

    with SASession(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            session.pop("associate_2fa_pending_id", None)
            flash("Account not found.", "danger")
            return redirect(url_for("associate.login"))

        verified = False
        if use_backup:
            if cand.verify_backup_code(token_code):
                verified = True
        else:
            if len(token_code) == 6 and token_code.isdigit() and cand.verify_totp(token_code):
                verified = True

        if not verified:
            flash("Invalid code. Please try again.", "danger")
            return redirect(url_for("associate.verify_2fa"))

        cand.last_login_at = datetime.utcnow()
        session["associate_user_id"] = cand.id
        session.pop("associate_2fa_pending_id", None)
        session.pop("associate_2fa_next", None)
        s.commit()
        _audit_portal("login", "Portal login via 2FA", candidate_id=cand.id)

    flash("Signed in successfully.", "success")
    return redirect(next_url)


@associate_bp.route("/logout")
def logout():
    """Clear session and redirect to login."""
    cand_id = session.get("associate_user_id")
    _audit_portal("logout", "Portal logout", candidate_id=cand_id)
    for key in list(session.keys()):
        if key.startswith("associate_"):
            session.pop(key, None)
    # S7: Regenerate session ID to prevent session fixation
    session.modified = True
    flash("You have been signed out.", "success")
    return redirect(url_for("associate.login"))


# =========================================================================
# PROTECTED ROUTES
# =========================================================================

@associate_bp.route("/dashboard")
@_require_login
def dashboard():
    """Main dashboard with profile completeness progress bars."""
    Candidate = _model("Candidate")
    engine = _engine()
    cand_id = _get_associate_id()

    with SASession(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            session.pop("associate_user_id", None)
            flash("Session expired. Please sign in again.", "warning")
            return redirect(url_for("associate.login"))

        completeness = _calc_completeness(s, cand_id)

        # Build next actions based on completeness gaps
        next_actions = []
        if completeness.get("personal_pct", 0) < 100:
            next_actions.append({
                "icon": "user",
                "title": "Complete Personal Details",
                "description": "Fill in your personal information to complete your profile.",
                "url": "/portal/personal-details"
            })
        if completeness.get("company_pct", 0) < 100:
            next_actions.append({
                "icon": "building",
                "title": "Add Company Details",
                "description": "Provide your contracting entity details.",
                "url": "/portal/company-details"
            })
        if completeness.get("checks_pct", 0) < 100:
            next_actions.append({
                "icon": "clipboard-check",
                "title": "Complete Vetting Checks",
                "description": "Submit required documents and references.",
                "url": "/portal/intro-to-vetting"
            })

        # Recent activity from candidate notes
        CandidateNote = _model("CandidateNote")
        recent_activity = []
        if CandidateNote:
            notes = s.query(CandidateNote).filter_by(candidate_id=cand_id).order_by(
                CandidateNote.created_at.desc()
            ).limit(5).all()
            for note in notes:
                recent_activity.append({
                    "content": note.content,
                    "timestamp": note.created_at.strftime("%d %b %Y %H:%M") if note.created_at else "",
                    "created_at": note.created_at,
                })

        return render_template(
            "associate/dashboard.html",
            associate=cand,
            overall_pct=completeness.get("overall_pct", 0),
            personal_pct=completeness.get("personal_pct", 0),
            company_pct=completeness.get("company_pct", 0),
            vetting_pct=completeness.get("checks_pct", 0),
            completeness=completeness,
            next_actions=next_actions,
            recent_activity=recent_activity,
        )


@associate_bp.route("/personal-details", methods=["GET", "POST"])
@_require_login
def personal_details():
    """Extended personal details form."""
    Candidate = _model("Candidate")
    AssociateProfile = _portal_model("AssociateProfile")
    engine = _engine()
    cand_id = _get_associate_id()

    if request.method == "GET":
        with SASession(engine) as s:
            cand = s.get(Candidate, cand_id)
            profile = s.query(AssociateProfile).filter_by(candidate_id=cand_id).first() if AssociateProfile else None
            CompanyDetails = _portal_model("CompanyDetails")
            company = s.query(CompanyDetails).filter_by(candidate_id=cand_id).first() if CompanyDetails else None
            employment_company = ""
            if company:
                if company.contracting_type == "umbrella" and company.umbrella_company_name:
                    employment_company = company.umbrella_company_name
                elif company.contracting_type == "limited" and company.company_name:
                    employment_company = company.company_name
            Document = _model("Document")
            cv_document = None
            if Document:
                cv_document = s.query(Document).filter_by(candidate_id=cand_id, doc_type="cv").first()
            return render_template("associate/personal_details.html", associate=cand, profile=profile, employment_company=employment_company, cv_document=cv_document)

    # POST
    with SASession(engine) as s:
        cand = s.get(Candidate, cand_id)
        if not cand:
            flash("Session expired.", "danger")
            return redirect(url_for("associate.login"))

        profile = s.query(AssociateProfile).filter_by(candidate_id=cand_id).first() if AssociateProfile else None
        if not profile and AssociateProfile:
            profile = AssociateProfile(candidate_id=cand_id)
            s.add(profile)

        # Update candidate base fields
        cand.name = _sanitise(request.form.get("name", cand.name or ""))
        cand.email = _sanitise(request.form.get("email", cand.email or "")).strip().lower()
        cand.phone = _sanitise(request.form.get("phone", cand.phone or ""))

        # Update profile fields
        if profile:
            profile.title = _sanitise(request.form.get("title", ""))
            profile.first_name = _sanitise(request.form.get("first_name", ""))
            profile.surname = _sanitise(request.form.get("surname", ""))
            profile.aliases = _sanitise(request.form.get("aliases", ""))
            profile.previous_names = _sanitise(request.form.get("previous_names", ""))
            profile.previous_first_names = _sanitise(request.form.get("previous_first_names", ""))
            profile.previous_surnames = _sanitise(request.form.get("previous_surnames", ""))
            profile.dob = _parse_date(request.form.get("dob", ""))
            profile.address_line1 = _sanitise(request.form.get("address_line1", ""))
            profile.address_line2 = _sanitise(request.form.get("address_line2", ""))
            profile.city = _sanitise(request.form.get("city", ""))
            profile.postcode = _sanitise(request.form.get("postcode", ""))
            profile.country = _sanitise(request.form.get("country", "United Kingdom"))
            profile.contact_number = _sanitise(request.form.get("contact_number", ""))
            profile.emergency_contact_name = _sanitise(request.form.get("emergency_contact_name", ""))
            profile.emergency_contact_phone = _sanitise(request.form.get("emergency_contact_phone", ""))
            # P8: Gender field
            profile.gender = _sanitise(request.form.get("gender", ""))
            profile.emergency_contact_relationship = _sanitise(request.form.get("emergency_contact_relationship", ""))
            profile.current_salary = _sanitise(request.form.get("current_salary", ""))
            profile.expected_salary = _sanitise(request.form.get("expected_salary", ""))
            profile.available_from = _parse_date(request.form.get("available_from", ""))
            profile.national_insurance_number = _sanitise(request.form.get("national_insurance_number", ""))
            profile.unsubscribed = request.form.get("unsubscribed") == "1"

        _add_note(s, cand_id, "Personal details updated via Associate Portal.")
        s.commit()

    flash("Personal details saved.", "success")
    return redirect(url_for("associate.personal_details"))


@associate_bp.route("/profile-picture", methods=["POST"])
@_require_login
def upload_profile_picture():
    """Upload a profile picture."""
    AssociateProfile = _portal_model("AssociateProfile")
    engine = _engine()
    cand_id = _get_associate_id()

    file = request.files.get("profile_picture")
    if not file or not file.filename:
        flash("No file selected.", "danger")
        return redirect(url_for("associate.personal_details"))

    # Validate file type
    allowed = {"jpg", "jpeg", "png", "gif", "webp"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        flash("Please upload an image file (JPG, PNG, GIF, or WebP).", "danger")
        return redirect(url_for("associate.personal_details"))

    # Save file
    import uuid
    upload_dir = os.path.join("uploads", "profile_pictures")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{cand_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    with SASession(engine) as s:
        profile = s.query(AssociateProfile).filter_by(candidate_id=cand_id).first()
        if not profile:
            profile = AssociateProfile(candidate_id=cand_id)
            s.add(profile)
        profile.profile_picture = filepath
        s.commit()

    flash("Profile picture updated.", "success")
    return redirect(url_for("associate.personal_details"))


@associate_bp.route("/profile-pic/<filename>")
@_require_login
def serve_profile_pic(filename):
    """Serve profile picture files."""
    from flask import send_from_directory
    upload_dir = os.path.join(os.getcwd(), "uploads", "profile_pictures")
    return send_from_directory(upload_dir, filename)


@associate_bp.route("/upload-cv", methods=["POST"])
@_require_login
def upload_cv():
    """Upload or replace CV document."""
    Document = _model("Document")
    engine = _engine()
    cand_id = _get_associate_id()

    file = request.files.get("cv_file")
    if not file or not file.filename:
        flash("No file selected.", "danger")
        return redirect(url_for("associate.personal_details"))

    allowed = {"pdf", "doc", "docx"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        flash("Please upload a PDF, DOC, or DOCX file.", "danger")
        return redirect(url_for("associate.personal_details"))

    import uuid
    upload_dir = os.path.join("uploads", "cvs")
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{cand_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(upload_dir, safe_name)
    file.save(filepath)

    with SASession(engine) as s:
        if Document:
            # Remove old CV if exists
            old_cv = s.query(Document).filter_by(candidate_id=cand_id, doc_type="cv").first()
            if old_cv:
                s.delete(old_cv)
            doc = Document(
                candidate_id=cand_id,
                doc_type="cv",
                filename=safe_name,
                original_name=file.filename,
            )
            s.add(doc)
            s.commit()

    flash("CV uploaded successfully.", "success")
    return redirect(url_for("associate.personal_details"))


@associate_bp.route("/company-details", methods=["GET", "POST"])
@_require_login
def company_details():
    """Contracting entity details: Umbrella or Limited Company."""
    CompanyDetails = _portal_model("CompanyDetails")
    engine = _engine()
    cand_id = _get_associate_id()

    # Contradiction Fix 6: Query approved umbrella companies from DB instead of hardcoded list
    ApprovedUmbrella = _model("ApprovedUmbrella")
    umbrella_options = [
        "Trafalgar Workforce Solutions Ltd",
        "PayStream My Max 2 Ltd",
    ]  # fallback if model not available
    if ApprovedUmbrella:
        try:
            with SASession(engine) as _s:
                db_umbrellas = _s.query(ApprovedUmbrella).filter_by(is_active=True).order_by(ApprovedUmbrella.name).all()
                if db_umbrellas:
                    umbrella_options = [u.name for u in db_umbrellas]
        except Exception:
            pass  # fallback to hardcoded list

    if request.method == "GET":
        with SASession(engine) as s:
            comp = s.query(CompanyDetails).filter_by(candidate_id=cand_id).first() if CompanyDetails else None

            # Check if any active engagement is outside IR35
            Application = _model("Application")
            Engagement = _model("Engagement")
            allow_limited = False
            if Application and Engagement:
                apps = s.query(Application).filter_by(candidate_id=cand_id).all()
                for app in apps:
                    if hasattr(app, "job") and app.job and hasattr(app.job, "engagement_id") and app.job.engagement_id:
                        eng = s.query(Engagement).get(app.job.engagement_id)
                        if eng and getattr(eng, "ir35_status", "inside") == "outside":
                            allow_limited = True
                            break

            # Query existing company documents
            Document = _model("Document")
            company_docs = {}
            if Document:
                for dtype in ["cert_incorporation", "pipl_insurance", "vat_certificate"]:
                    doc = s.query(Document).filter_by(candidate_id=cand_id, doc_type=dtype).first()
                    if doc:
                        company_docs[dtype] = doc

            return render_template("associate/company_details.html", company=comp, umbrella_options=umbrella_options, allow_limited=allow_limited, company_docs=company_docs)

    with SASession(engine) as s:
        comp = s.query(CompanyDetails).filter_by(candidate_id=cand_id).first() if CompanyDetails else None
        if not comp and CompanyDetails:
            comp = CompanyDetails(candidate_id=cand_id)
            s.add(comp)

        if comp:
            comp.contracting_type = _sanitise(request.form.get("entity_type", ""))
            comp.company_name = _sanitise(request.form.get("company_name", ""))
            comp.registration_number = _sanitise(request.form.get("company_reg_number", ""))
            comp.vat_registered = request.form.get("vat_registered") == "yes"
            comp.vat_number = _sanitise(request.form.get("vat_number", ""))
            comp.bank_account_number = _sanitise(request.form.get("bank_account_number", ""))
            comp.bank_sort_code = _sanitise(request.form.get("bank_sort_code", ""))
            comp.umbrella_company_name = _sanitise(request.form.get("umbrella_company", ""))

        # Handle Ltd Co document uploads
        Document = _model("Document")
        if Document and comp and comp.contracting_type == "limited":
            import uuid
            for doc_type_key in ["cert_incorporation", "pipl_insurance", "vat_certificate"]:
                file = request.files.get(doc_type_key)
                if file and file.filename:
                    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "pdf"
                    if ext not in {"pdf", "doc", "docx", "jpg", "jpeg", "png"}:
                        flash(f"Invalid file type for {doc_type_key}. Allowed: PDF, DOC, DOCX, JPG, PNG.", "danger")
                        continue
                    upload_dir = os.path.join("uploads", "company_docs")
                    os.makedirs(upload_dir, exist_ok=True)
                    safe_name = f"{cand_id}_{doc_type_key}_{uuid.uuid4().hex[:8]}.{ext}"
                    filepath = os.path.join(upload_dir, safe_name)
                    file.save(filepath)
                    # Replace existing doc of this type
                    old_doc = s.query(Document).filter_by(candidate_id=cand_id, doc_type=doc_type_key).first()
                    if old_doc:
                        s.delete(old_doc)
                    new_doc = Document(candidate_id=cand_id, doc_type=doc_type_key, filename=safe_name, original_name=file.filename)
                    s.add(new_doc)

        _add_note(s, cand_id, "Company details updated via Associate Portal.")
        s.commit()

    flash("Company details saved.", "success")
    return redirect(url_for("associate.company_details"))


@associate_bp.route("/consent-form", methods=["GET", "POST"])
@_require_login
def consent_form():
    """Digital consent form with e-signature."""
    ConsentRecord = _portal_model("ConsentRecord")
    engine = _engine()
    cand_id = _get_associate_id()

    if request.method == "GET":
        with SASession(engine) as s:
            consent = s.query(ConsentRecord).filter_by(candidate_id=cand_id).order_by(
                ConsentRecord.created_at.desc()
            ).first() if ConsentRecord else None
            return render_template("associate/consent_form.html", consent=consent, already_signed=consent is not None)

    with SASession(engine) as s:
        # Contradiction Fix 4: Manual consent PDF upload fallback
        manual_file = request.files.get("manual_consent")
        if manual_file and manual_file.filename:
            import uuid as _uuid
            ext = manual_file.filename.rsplit(".", 1)[-1].lower() if "." in manual_file.filename else "pdf"
            if ext not in {"pdf", "doc", "docx", "jpg", "jpeg", "png"}:
                flash("Invalid file type for consent form. Allowed: PDF, DOC, DOCX, JPG, PNG.", "danger")
                return redirect(url_for("associate.consent_form"))

            upload_dir = os.path.join("uploads", "consent_forms")
            os.makedirs(upload_dir, exist_ok=True)
            safe_name = f"{cand_id}_consent_{_uuid.uuid4().hex[:8]}.{ext}"
            filepath = os.path.join(upload_dir, safe_name)
            manual_file.save(filepath)

            # Save as Document record
            Document = _model("Document")
            if Document:
                # Remove old consent doc if exists
                old_doc = s.query(Document).filter_by(candidate_id=cand_id, doc_type="consent_signed").first()
                if old_doc:
                    s.delete(old_doc)
                new_doc = Document(
                    candidate_id=cand_id,
                    doc_type="consent_signed",
                    filename=safe_name,
                    original_name=manual_file.filename
                )
                s.add(new_doc)

            # Create ConsentRecord for the manual upload
            consent = ConsentRecord(
                candidate_id=cand_id,
                consent_given=True,
                secondary_employment=request.form.get("has_secondary_employment") == "yes",
                secondary_employment_details=_sanitise(request.form.get("secondary_employment_details", "")),
                legal_name=_sanitise(request.form.get("legal_name", "Manual Upload")).strip() or "Manual Upload",
                signed_date=datetime.utcnow(),
                ip_address=request.remote_addr or "",
            )
            s.add(consent)
            _add_note(s, cand_id, f"Consent form uploaded manually (file: {manual_file.filename}).")
            s.commit()

            flash("Signed consent form uploaded successfully.", "success")
            return redirect(url_for("associate.dashboard"))

        # Original digital consent flow
        legal_name = _sanitise(request.form.get("legal_name", "")).strip()
        if not legal_name:
            flash("You must provide your legal name to sign.", "danger")
            return redirect(url_for("associate.consent_form"))

        consent = ConsentRecord(
            candidate_id=cand_id,
            consent_given=True,  # signing the form implies consent
            secondary_employment=request.form.get("has_secondary_employment") == "yes",
            secondary_employment_details=_sanitise(request.form.get("secondary_employment_details", "")),
            legal_name=legal_name,
            signed_date=datetime.utcnow(),
            ip_address=request.remote_addr or "",
        )
        s.add(consent)
        _add_note(s, cand_id, f"Consent form signed by '{legal_name}' from IP {request.remote_addr}.")
        s.commit()

    flash("Consent form submitted successfully.", "success")
    return redirect(url_for("associate.dashboard"))


@associate_bp.route("/declaration")
@_require_login
def declaration_redirect():
    """Redirect /portal/declaration to /portal/declaration-form."""
    return redirect(url_for("associate.declaration_form"))


@associate_bp.route("/declaration-form", methods=["GET", "POST"])
@_require_login
def declaration_form():
    """Declaration form with 6 yes/no questions and e-signature."""
    DeclarationRecord = _portal_model("DeclarationRecord")
    engine = _engine()
    cand_id = _get_associate_id()

    if request.method == "GET":
        with SASession(engine) as s:
            decl = s.query(DeclarationRecord).filter_by(candidate_id=cand_id).order_by(
                DeclarationRecord.created_at.desc()
            ).first() if DeclarationRecord else None
            return render_template("associate/declaration_form.html", declaration=decl, already_signed=decl is not None)

    with SASession(engine) as s:
        legal_name = _sanitise(request.form.get("legal_name", "")).strip()
        if not legal_name:
            flash("You must provide your legal name to sign.", "danger")
            return redirect(url_for("associate.declaration_form"))

        work_restrictions = _parse_bool(request.form.get("work_restrictions", False))
        criminal_convictions = _parse_bool(request.form.get("criminal_convictions", False))
        ccj_debt = _parse_bool(request.form.get("ccj_debt", False))
        bankruptcy = _parse_bool(request.form.get("bankruptcy", False))
        dismissed = _parse_bool(request.form.get("dismissed", False))
        referencing_issues = _parse_bool(request.form.get("referencing_issues", False))

        decl = DeclarationRecord(
            candidate_id=cand_id,
            work_restrictions=work_restrictions,
            work_restrictions_detail=_sanitise(request.form.get("work_restrictions_details", "")),
            criminal_convictions=criminal_convictions,
            criminal_convictions_detail=_sanitise(request.form.get("criminal_convictions_details", "")),
            ccj_debt=ccj_debt,
            ccj_debt_detail=_sanitise(request.form.get("ccj_debt_details", "")),
            bankruptcy=bankruptcy,
            bankruptcy_detail=_sanitise(request.form.get("bankruptcy_details", "")),
            dismissed=dismissed,
            dismissed_detail=_sanitise(request.form.get("dismissed_details", "")),
            referencing_issues=referencing_issues,
            referencing_issues_detail=_sanitise(request.form.get("referencing_issues_details", "")),
            disclosure_text=_sanitise(request.form.get("open_disclosure", "")),
            legal_name=legal_name,
            signed_date=datetime.utcnow(),
            ip_address=request.remote_addr or "",
        )
        s.add(decl)

        # If any answer is "Yes", create a flag note for internal review
        flags = []
        if work_restrictions:
            flags.append("Work Restrictions")
        if criminal_convictions:
            flags.append("Criminal Convictions")
        if ccj_debt:
            flags.append("CCJ/Debt")
        if bankruptcy:
            flags.append("Bankruptcy")
        if dismissed:
            flags.append("Previous Dismissal")
        if referencing_issues:
            flags.append("Referencing Issues")

        if flags:
            flag_text = (
                f"DECLARATION FLAG: Candidate declared YES to: {', '.join(flags)}. "
                f"Signed by '{legal_name}' from IP {request.remote_addr}. "
                "Manual review required."
            )
            _add_note(s, cand_id, flag_text, note_type="system")

            # Contradiction Fix 3: If vetting checks exist, set them ALL to ON HOLD (orange)
            # If no vetting checks exist yet, fall back to the existing Flagged behaviour
            VettingCheck = _model("VettingCheck")
            existing_checks = []
            if VettingCheck:
                existing_checks = s.query(VettingCheck).filter_by(candidate_id=cand_id).all()

            if existing_checks:
                for vc in existing_checks:
                    vc.status = "ON HOLD"
                    if hasattr(vc, "colour"):
                        vc.colour = "orange"
                _add_note(s, cand_id,
                          f"All {len(existing_checks)} vetting checks set to ON HOLD due to declaration flags.",
                          note_type="system")
            else:
                # No vetting checks exist yet — keep existing flag behaviour
                Candidate = _model("Candidate")
                cand = s.get(Candidate, cand_id)
                if cand and hasattr(cand, "status"):
                    if cand.status not in ("On Hold", "Flagged"):
                        cand.status = "Flagged"
        else:
            _add_note(s, cand_id, f"Declaration form signed by '{legal_name}'. No flags raised.")

        s.commit()

    flash("Declaration form submitted successfully.", "success")
    return redirect(url_for("associate.dashboard"))


@associate_bp.route("/intro-to-vetting")
@_require_login
def intro_to_vetting():
    """Introduction to the vetting process."""
    return render_template("associate/intro_to_vetting.html")


@associate_bp.route("/vetting-progress")
@_require_login
def vetting_progress():
    """Read-only view of all vetting check statuses."""
    VettingCheck = _model("VettingCheck")
    engine = _engine()
    cand_id = _get_associate_id()

    # P10: Check employment completeness — warn (don't hard block vetting view)
    employment_ok = True
    employment_msg = ""
    with SASession(engine) as s_check:
        employment_ok, employment_msg = _check_employment_complete(s_check, cand_id)

    ConsentRecord = _portal_model("ConsentRecord")
    DeclarationRecord = _portal_model("DeclarationRecord")

    with SASession(engine) as s:
        checks = []
        if VettingCheck:
            checks = s.query(VettingCheck).filter_by(candidate_id=cand_id).order_by(
                VettingCheck.check_type.asc()
            ).all()

        consent_signed = False
        if ConsentRecord:
            consent = s.query(ConsentRecord).filter_by(candidate_id=cand_id).first()
            consent_signed = bool(consent and consent.consent_given)

        declaration_signed = False
        if DeclarationRecord:
            decl = s.query(DeclarationRecord).filter_by(candidate_id=cand_id).first()
            declaration_signed = bool(decl and decl.signed_date)

        return render_template(
            "associate/vetting_progress.html",
            vetting_checks=checks,
            consent_signed=consent_signed,
            declaration_signed=declaration_signed,
        )


@associate_bp.route("/references", methods=["GET", "POST"])
@_require_login
def references():
    """Employment history timeline with gap detection, qualifications."""
    EmploymentHistory = _portal_model("EmploymentHistory")
    QualificationRecord = _portal_model("QualificationRecord")
    engine = _engine()
    cand_id = _get_associate_id()

    with SASession(engine) as s:
        entries = []
        qualifications = []
        gaps = []

        if EmploymentHistory:
            entries = s.query(EmploymentHistory).filter_by(candidate_id=cand_id).order_by(
                EmploymentHistory.start_date.desc().nullslast()
            ).all()
            gaps = _detect_gaps(entries)

        if QualificationRecord:
            qualifications = s.query(QualificationRecord).filter_by(candidate_id=cand_id).order_by(
                QualificationRecord.start_date.desc().nullslast()
            ).all()

        return render_template(
            "associate/references.html",
            employment_entries=entries,
            qualifications=qualifications,
            gaps_detected=gaps,
        )


@associate_bp.route("/references/add-employment", methods=["POST"])
@_require_login
def references_add_employment():
    """Form handler: add an employment history entry."""
    EmploymentHistory = _portal_model("EmploymentHistory")
    engine = _engine()
    cand_id = _get_associate_id()

    if not EmploymentHistory:
        flash("Employment history not available.", "danger")
        return redirect(url_for("associate.references"))

    company_name = _sanitise(request.form.get("company_name", "")).strip()
    if not company_name:
        flash("Company name is required.", "danger")
        return redirect(url_for("associate.references"))

    perm = request.form.get("permission_to_request", "yes") == "yes"

    with SASession(engine) as s:
        entry = EmploymentHistory(
            candidate_id=cand_id,
            company_name=company_name,
            agency_name=_sanitise(request.form.get("agency_name", "")),
            referee_email=_sanitise(request.form.get("referee_email", "")),
            company_address=_sanitise(request.form.get("company_address", "")),
            start_date=_parse_date(request.form.get("start_date", "")),
            end_date=_parse_date(request.form.get("end_date", "")),
            job_title=_sanitise(request.form.get("job_title", "")),
            reason_for_leaving=_sanitise(request.form.get("reason_for_leaving", "")),
            is_gap=False,
            permission_to_request=perm,
            permission_delay_reason=_sanitise(request.form.get("no_permission_reason", "")),
            permission_future_date=_parse_date(request.form.get("future_permission_date", "")),
            reference_status="not_sent",
        )
        s.add(entry)
        _add_note(s, cand_id, f"Employment history added: {company_name}.")
        s.commit()

    flash("Employment entry added successfully.", "success")
    return redirect(url_for("associate.references"))


@associate_bp.route("/references/add-gap", methods=["POST"])
@_require_login
def references_add_gap():
    """Form handler: add a gap entry."""
    EmploymentHistory = _portal_model("EmploymentHistory")
    engine = _engine()
    cand_id = _get_associate_id()

    if not EmploymentHistory:
        flash("Employment history not available.", "danger")
        return redirect(url_for("associate.references"))

    reason = _sanitise(request.form.get("reason", "")).strip()
    other_reason = _sanitise(request.form.get("other_reason", "")).strip()
    gap_reason = other_reason if reason == "Other" and other_reason else reason

    evidence_doc_id = None
    evidence_file = request.files.get("evidence")
    if evidence_file and evidence_file.filename:
        saved = _save_file(evidence_file)
        if saved:
            Document = _model("Document")
            if Document:
                with SASession(engine) as s_doc:
                    doc = Document(
                        candidate_id=cand_id,
                        doc_type="gap_evidence",
                        filename=saved["filename"],
                        original_name=saved["original_name"],
                        uploaded_at=datetime.utcnow(),
                    )
                    s_doc.add(doc)
                    s_doc.commit()
                    evidence_doc_id = doc.id

    with SASession(engine) as s:
        entry = EmploymentHistory(
            candidate_id=cand_id,
            company_name="",
            start_date=_parse_date(request.form.get("start_date", "")),
            end_date=_parse_date(request.form.get("end_date", "")),
            is_gap=True,
            gap_reason=gap_reason,
            gap_evidence_doc_id=evidence_doc_id,
            reference_status="not_sent",
        )
        s.add(entry)
        _add_note(s, cand_id, f"Gap entry added: {gap_reason}.")
        s.commit()

    flash("Gap entry added successfully.", "success")
    return redirect(url_for("associate.references"))


@associate_bp.route("/references/add-qualification", methods=["POST"])
@_require_login
def references_add_qualification():
    """Form handler: add a qualification record."""
    QualificationRecord = _portal_model("QualificationRecord")
    engine = _engine()
    cand_id = _get_associate_id()

    if not QualificationRecord:
        flash("Qualifications not available.", "danger")
        return redirect(url_for("associate.references"))

    qual_name = _sanitise(request.form.get("name", "")).strip()
    if not qual_name:
        flash("Qualification name is required.", "danger")
        return redirect(url_for("associate.references"))

    perm = request.form.get("qual_permission", "yes") == "yes"

    with SASession(engine) as s:
        qual = QualificationRecord(
            candidate_id=cand_id,
            qualification_name=qual_name,
            qualification_type=_sanitise(request.form.get("qual_type", "")),
            grade=_sanitise(request.form.get("grade", "")),
            institution=_sanitise(request.form.get("institution", "")),
            start_date=_parse_date(request.form.get("start_date", "")),
            end_date=_parse_date(request.form.get("end_date", "")),
            permission_to_request=perm,
            permission_delay_reason=_sanitise(request.form.get("qual_delay_reason", "")),
        )
        s.add(qual)
        _add_note(s, cand_id, f"Qualification added: {qual_name}.")
        s.commit()

    flash("Qualification added successfully.", "success")
    return redirect(url_for("associate.references"))


@associate_bp.route("/references/delete-entry/<int:entry_id>", methods=["DELETE"])
@_require_login
def references_delete_entry(entry_id):
    """AJAX: delete an employment/gap entry."""
    EmploymentHistory = _portal_model("EmploymentHistory")
    engine = _engine()
    cand_id = _get_associate_id()

    if not EmploymentHistory:
        return jsonify({"success": False, "error": "Not available"}), 500

    with SASession(engine) as s:
        entry = s.query(EmploymentHistory).filter_by(id=entry_id, candidate_id=cand_id).first()
        if not entry:
            return jsonify({"success": False, "error": "Entry not found"}), 404
        desc = entry.company_name or "Gap"
        s.delete(entry)
        _add_note(s, cand_id, f"Employment entry deleted: {desc}.")
        s.commit()

    return jsonify({"success": True})


@associate_bp.route("/references/delete-qualification/<int:qual_id>", methods=["DELETE"])
@_require_login
def references_delete_qualification(qual_id):
    """AJAX: delete a qualification record."""
    QualificationRecord = _portal_model("QualificationRecord")
    engine = _engine()
    cand_id = _get_associate_id()

    if not QualificationRecord:
        return jsonify({"success": False, "error": "Not available"}), 500

    with SASession(engine) as s:
        qual = s.query(QualificationRecord).filter_by(id=qual_id, candidate_id=cand_id).first()
        if not qual:
            return jsonify({"success": False, "error": "Qualification not found"}), 404
        name = qual.qualification_name
        s.delete(qual)
        _add_note(s, cand_id, f"Qualification deleted: {name}.")
        s.commit()

    return jsonify({"success": True})


@associate_bp.route("/documents", methods=["GET", "POST"])
@_require_login
def documents():
    """Upload and view documents (ID, proof of address, RTW, CV, qualifications)."""
    Document = _model("Document")
    engine = _engine()
    cand_id = _get_associate_id()

    if request.method == "GET":
        with SASession(engine) as s:
            docs_list = []
            if Document:
                docs_list = s.query(Document).filter_by(candidate_id=cand_id).order_by(
                    Document.uploaded_at.desc()
                ).all()
            # Organize documents by category (doc_type) for the template
            docs_by_category = {}
            for doc in docs_list:
                cat = getattr(doc, "doc_type", "other") or "other"
                docs_by_category.setdefault(cat, []).append(doc)
            return render_template("associate/documents.html", documents=docs_by_category)

    # POST: handle file upload
    doc_type = _sanitise(request.form.get("doc_type", "other"))
    file = request.files.get("file")

    # P11: POA type-specific expiry validation
    expiry_date_str = request.form.get("expiry_date", "").strip()
    poa_sub_type = _sanitise(request.form.get("poa_sub_type", "")).strip()
    if doc_type in ("proof_of_address", "poa") and poa_sub_type:
        # Validate POA expiry based on document sub-type
        max_days = {"bank_statement": 90, "credit_card_statement": 90,
                    "utility_bill": 90, "council_tax": 365, "mortgage_statement": 365}
        limit = max_days.get(poa_sub_type, 90)
        if not expiry_date_str:
            flash(f"Please enter the document date for your proof of address. "
                  f"{'Bank/utility/credit statements must be within 90 days.' if limit == 90 else 'Council tax/mortgage statements must be within 12 months.'}",
                  "danger")
            return redirect(url_for("associate.documents"))

    if not file or not file.filename:
        flash("Please select a file to upload.", "danger")
        return redirect(url_for("associate.documents"))

    # Validate extension
    allowed = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}
    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in allowed:
        flash(f"File type .{ext} not allowed. Accepted: {', '.join(sorted(allowed))}.", "danger")
        return redirect(url_for("associate.documents"))

    saved = _save_file(file)
    if not saved:
        flash("Failed to save file.", "danger")
        return redirect(url_for("associate.documents"))

    with SASession(engine) as s:
        if Document:
            doc = Document(
                candidate_id=cand_id,
                doc_type=doc_type,
                filename=saved["filename"],
                original_name=saved["original_name"],
                uploaded_at=datetime.utcnow(),
            )
            s.add(doc)
            _add_note(s, cand_id, f"Document uploaded: {saved['original_name']} (type: {doc_type}).")
            s.commit()

    flash("Document uploaded successfully.", "success")
    return redirect(url_for("associate.documents"))


@associate_bp.route("/my-applications")
@_require_login
def my_applications():
    """View all submitted applications with simplified status (Applied / Unsuccessful)."""
    Application = _model("Application")
    Job = _model("Job")
    Engagement = _model("Engagement")
    engine = _engine()
    cand_id = _get_associate_id()

    UNSUCCESSFUL_STATUSES = {
        "rejected", "withdrawn", "rejected/withdrawn", "offer declined",
        "declined", "unsuccessful", "closed", "cancelled", "canceled",
    }

    applications = []
    with SASession(engine) as s:
        if Application:
            from sqlalchemy.orm import joinedload
            query = s.query(Application).filter_by(candidate_id=cand_id)
            if hasattr(Application, "job"):
                query = query.options(joinedload(Application.job))
            rows = query.order_by(Application.created_at.desc()).all()

            for app in rows:
                job = app.job if hasattr(app, "job") and app.job else None
                raw_status = (app.status or "").strip().lower()

                # Determine client name from engagement
                client_name = ""
                if job and hasattr(job, "engagement_id") and job.engagement_id and Engagement:
                    eng = s.get(Engagement, job.engagement_id)
                    if eng:
                        client_name = getattr(eng, "client", "") or getattr(eng, "name", "") or ""

                applications.append({
                    "job_title": job.title if job else "Untitled Role",
                    "client": client_name,
                    "applied_date": app.created_at.strftime("%d %b %Y") if app.created_at else "N/A",
                    "status": "Unsuccessful" if raw_status in UNSUCCESSFUL_STATUSES else "Applied",
                })

    return render_template("associate/my_applications.html",
                           applications=applications,
                           active_page="my_applications")


@associate_bp.route("/assignments")
@_require_login
def assignments():
    """View current and past assignments (engagements/placements)."""
    Application = _model("Application")
    Job = _model("Job")
    Engagement = _model("Engagement")
    ESigRequest = _model("ESigRequest")
    engine = _engine()
    cand_id = _get_associate_id()

    with SASession(engine) as s:
        apps = []
        if Application:
            query = s.query(Application).filter_by(candidate_id=cand_id)
            if hasattr(Application, "job"):
                from sqlalchemy.orm import joinedload
                query = query.options(joinedload(Application.job))
            apps = query.order_by(Application.created_at.desc()).all()

        esign_requests = []
        if ESigRequest:
            try:
                # Try candidate_id first, fall back to fetching by application_ids
                if hasattr(ESigRequest, "candidate_id"):
                    esign_requests = s.query(ESigRequest).filter_by(candidate_id=cand_id).order_by(
                        ESigRequest.created_at.desc()
                    ).all()
                elif apps and hasattr(ESigRequest, "application_id"):
                    app_ids = [a.id for a in apps]
                    esign_requests = s.query(ESigRequest).filter(
                        ESigRequest.application_id.in_(app_ids)
                    ).order_by(ESigRequest.created_at.desc()).all()
            except Exception:
                esign_requests = []

        # Build assignment dicts from applications for the template
        all_assignments = []
        for app in apps:
            job = app.job if hasattr(app, "job") and app.job else None
            # Look up engagement name if job has engagement_id
            engagement_name = ""
            client_name = ""
            if job and hasattr(job, "engagement_id") and job.engagement_id and Engagement:
                eng = s.get(Engagement, job.engagement_id)
                if eng:
                    engagement_name = getattr(eng, "name", "") or ""
                    client_name = getattr(eng, "client", "") or getattr(eng, "name", "") or ""
            if not client_name:
                client_name = job.engagement_name if job and hasattr(job, "engagement_name") else ""

            stage = (app.stage or "").lower() if hasattr(app, "stage") else ""
            is_ended = stage in ("completed", "ended", "terminated", "withdrawn")
            display_status = "Contract ended" if is_ended else "On Contract"

            assignment = {
                "id": app.id,
                "job_title": job.title if job else (app.role if hasattr(app, "role") else "Untitled Role"),
                "client": client_name,
                "engagement_name": engagement_name,
                "start_date": app.start_date.strftime("%d %b %Y") if hasattr(app, "start_date") and app.start_date else "TBC",
                "end_date": app.end_date.strftime("%d %b %Y") if hasattr(app, "end_date") and app.end_date else "TBC",
                "day_rate": getattr(app, "day_rate", None),
                "status": display_status,
                "contract_status": "N/A",
                "duration": "",
            }
            # Check e-sign status for contract
            for esig in esign_requests:
                if hasattr(esig, "application_id") and esig.application_id == app.id:
                    assignment["contract_status"] = esig.status.title() if esig.status else "Pending"
                    break

            all_assignments.append(assignment)

        return render_template(
            "associate/assignments.html",
            assignments=all_assignments,
        )


@associate_bp.route("/timesheets", methods=["GET"])
@_require_login
def timesheets():
    """View and manage timesheets with weekly grid."""
    import json as _json
    from collections import defaultdict
    Timesheet = _model("Timesheet")
    Application = _model("Application")
    Engagement = _model("Engagement")
    TimesheetConfig = _portal_model("TimesheetConfig")
    TimesheetEntry = _portal_model("TimesheetEntry")
    TimesheetExpense = _portal_model("TimesheetExpense")
    engine = _engine()
    cand_id = _get_associate_id()

    with SASession(engine) as s:
        # Get candidate's active assignments for dropdown
        assignments = []
        if Application:
            apps = s.query(Application).filter_by(candidate_id=cand_id).all()
            for app in apps:
                job = app.job if hasattr(app, "job") and app.job else None
                eng = None
                if job and hasattr(job, "engagement_id") and job.engagement_id and Engagement:
                    eng = s.query(Engagement).get(job.engagement_id)
                assignments.append({
                    "id": app.id,
                    "engagement_id": job.engagement_id if job and hasattr(job, "engagement_id") else None,
                    "job_title": job.title if job else "Assignment",
                    "client": eng.client if eng else "",
                    "engagement_name": eng.name if eng else "",
                })

        # Get all timesheets for this candidate
        all_sheets = []
        if Timesheet:
            all_sheets = s.query(Timesheet).filter_by(user_id=cand_id).order_by(
                Timesheet.period_start.desc()
            ).all()

        # Current draft timesheet
        current_ts = None
        previous_sheets = []
        for ts in all_sheets:
            if not current_ts and getattr(ts, "status", "") in ("Draft", "Unsubmitted", None, ""):
                current_ts = ts
            else:
                previous_sheets.append(ts)

        # Load config, entries, and expenses for current timesheet
        config = None
        time_types = ["Standard Time", "Overtime", "Holiday", "Sickness", "Unplanned Absence"]
        entries = {}  # {(date_str, time_type): value}
        expenses = []

        if current_ts:
            # Get config for this timesheet's engagement
            eng_id = getattr(current_ts, "engagement_id", None)
            if eng_id and TimesheetConfig:
                config = s.query(TimesheetConfig).filter_by(engagement_id=eng_id).first()
            if config:
                try:
                    time_types = _json.loads(config.time_types)
                except Exception:
                    pass

            # Load entries
            if TimesheetEntry:
                entry_rows = s.query(TimesheetEntry).filter_by(timesheet_id=current_ts.id).all()
                for e in entry_rows:
                    date_str = e.entry_date.strftime("%Y-%m-%d") if e.entry_date else ""
                    entries[(date_str, e.time_type)] = {"value": e.value, "unit": e.value_unit}

            # Load expenses
            if TimesheetExpense:
                expenses = s.query(TimesheetExpense).filter_by(timesheet_id=current_ts.id).all()

        # Build week days for grid
        week_days = []
        if current_ts and getattr(current_ts, "week_start", None):
            ws = current_ts.week_start
            for i in range(7):
                d = ws + timedelta(days=i)
                week_days.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "label": d.strftime("%a %d %b"),
                    "short": d.strftime("%a"),
                })

        # Group previous timesheets by month
        monthly_bundles = defaultdict(lambda: {"sheets": [], "total_days": 0, "total_hours": 0, "total_expenses": 0, "total_amount": 0})
        for ts in previous_sheets:
            ws = getattr(ts, "week_start", None) or getattr(ts, "period_start", None)
            if ws:
                month_key = ws.strftime("%Y-%m")
                month_label = ws.strftime("%B %Y")
            else:
                month_key = "unknown"
                month_label = "Unknown"
            bundle = monthly_bundles[month_key]
            bundle["label"] = month_label
            bundle["sheets"].append(ts)
            bundle["total_days"] += getattr(ts, "billable_days", 0) or 0
            bundle["total_hours"] += getattr(ts, "billable_hours", 0) or 0
            bundle["total_expenses"] += getattr(ts, "expense_total", 0) or 0
            bundle["total_amount"] += getattr(ts, "grand_total", 0) or getattr(ts, "total_amount", 0) or 0

        # Sort monthly bundles by key (most recent first)
        sorted_bundles = sorted(monthly_bundles.items(), key=lambda x: x[0], reverse=True)

        expense_enabled = config.expense_enabled if config else False
        expense_types_list = []
        if config:
            try:
                expense_types_list = _json.loads(config.expense_types)
            except Exception:
                expense_types_list = []

        return render_template(
            "associate/timesheets.html",
            assignments=assignments,
            current_ts=current_ts,
            config=config,
            time_types=time_types,
            entries=entries,
            expenses=expenses,
            week_days=week_days,
            monthly_bundles=sorted_bundles,
            expense_enabled=expense_enabled,
            expense_types=expense_types_list,
        )


@associate_bp.route("/vacancies")
@_require_login
def vacancies():
    """Browse open vacancies with optional search/filter."""
    Job = _model("Job")
    engine = _engine()

    search_query = request.args.get("q", "").strip()
    location_filter = request.args.get("location", "").strip()

    with SASession(engine) as s:
        jobs = []
        locations = []
        if Job:
            query = s.query(Job).filter(
                (Job.status == "Open") | (Job.status == None)  # noqa: E711
            )
            if search_query:
                like_q = f"%{search_query}%"
                query = query.filter(
                    Job.title.ilike(like_q) | Job.description.ilike(like_q)
                )
            if location_filter and hasattr(Job, "location"):
                query = query.filter(Job.location.ilike(f"%{location_filter}%"))

            jobs = query.order_by(Job.created_at.desc()).all()

            # Build distinct location list for the filter dropdown
            if hasattr(Job, "location"):
                loc_rows = s.query(Job.location).filter(
                    ((Job.status == "Open") | (Job.status == None)),  # noqa: E711
                    Job.location != None, Job.location != ""  # noqa: E711
                ).distinct().all()
                locations = sorted(set(r[0] for r in loc_rows if r[0]))

        return render_template(
            "associate/vacancies.html",
            jobs=jobs,
            search_query=search_query,
            location_filter=location_filter,
            locations=locations,
        )


# =========================================================================
# API ROUTES (AJAX)
# =========================================================================

@associate_bp.route("/api/upload-document", methods=["POST"])
@_require_login
def api_upload_document():
    """AJAX endpoint for uploading a document."""
    Document = _model("Document")
    engine = _engine()
    cand_id = _get_associate_id()

    file = request.files.get("file")
    doc_type = _sanitise(request.form.get("doc_type", "other"))

    if not file or not file.filename:
        return jsonify({"error": "No file provided"}), 400

    allowed = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}
    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in allowed:
        return jsonify({"error": f"File type .{ext} not allowed"}), 400

    saved = _save_file(file)
    if not saved:
        return jsonify({"error": "Failed to save file"}), 500

    doc_id = None
    with SASession(engine) as s:
        if Document:
            doc = Document(
                candidate_id=cand_id,
                doc_type=doc_type,
                filename=saved["filename"],
                original_name=saved["original_name"],
                uploaded_at=datetime.utcnow(),
            )
            s.add(doc)
            _add_note(s, cand_id, f"Document uploaded via API: {saved['original_name']} (type: {doc_type}).")
            s.commit()
            doc_id = doc.id

    return jsonify({
        "success": True,
        "document": {
            "id": doc_id,
            "filename": saved["filename"],
            "original_name": saved["original_name"],
        },
    })


@associate_bp.route("/api/reference-contacts")
@_require_login
def api_reference_contacts():
    """Search known reference contacts by company name prefix."""
    ReferenceContact = _portal_model("ReferenceContact")
    engine = _engine()
    q = _sanitise(request.args.get("q", "")).strip()

    if not q or len(q) < 2:
        return jsonify({"results": []})

    results = []
    if ReferenceContact:
        with SASession(engine) as s:
            contacts = s.query(ReferenceContact).filter(
                ReferenceContact.company_name.ilike(f"{q}%")
            ).limit(20).all()
            results = [
                {
                    "company_name": c.company_name,
                    "referee_email": c.referee_email,
                    "last_amended": c.last_amended.isoformat() if c.last_amended else None,
                }
                for c in contacts
            ]

    return jsonify({"results": results})


@associate_bp.route("/api/check-reference-house")
@_require_login
def api_check_reference_house():
    """Check if a reference house name is flagged as suspicious."""
    FlaggedReferenceHouse = _portal_model("FlaggedReferenceHouse")
    engine = _engine()
    name = _sanitise(request.args.get("name", "")).strip()

    if not name:
        return jsonify({"flagged": False})

    flagged = False
    details = None
    if FlaggedReferenceHouse:
        with SASession(engine) as s:
            match = s.query(FlaggedReferenceHouse).filter(
                FlaggedReferenceHouse.name.ilike(name)
            ).first()
            if match:
                flagged = True
                details = {
                    "name": match.name,
                    "candidate_count": match.candidate_count,
                    "end_clients": match.end_clients,
                    "website": match.website,
                    "notes": match.notes,
                }

    return jsonify({"flagged": flagged, "details": details})


@associate_bp.route("/api/company-lookup")
@_require_login
def api_company_lookup():
    """Combined company name lookup: reference contacts + flagged reference houses."""
    ReferenceContact = _portal_model("ReferenceContact")
    FlaggedReferenceHouse = _portal_model("FlaggedReferenceHouse")
    engine = _engine()
    q = _sanitise(request.args.get("q", "")).strip()

    if not q or len(q) < 2:
        return jsonify({"results": []})

    results = []
    with SASession(engine) as s:
        # Find matching reference contacts
        contacts = []
        if ReferenceContact:
            contacts = s.query(ReferenceContact).filter(
                ReferenceContact.company_name.ilike(f"{q}%")
            ).limit(10).all()

        # Build set of flagged house names for cross-check
        flagged_names = set()
        if FlaggedReferenceHouse:
            flagged = s.query(FlaggedReferenceHouse.name).all()
            flagged_names = {f.name.lower() for f in flagged}

        seen = set()
        for c in contacts:
            key = c.company_name.lower()
            if key not in seen:
                seen.add(key)
                results.append({
                    "name": c.company_name,
                    "referee_email": c.referee_email,
                    "is_reference_house": key in flagged_names,
                })

    return jsonify({"results": results})


@associate_bp.route("/api/add-reference", methods=["POST"])
@_require_login
def api_add_reference():
    """Add an employment history entry."""
    EmploymentHistory = _portal_model("EmploymentHistory")
    engine = _engine()
    cand_id = _get_associate_id()

    if not EmploymentHistory:
        return jsonify({"error": "Employment history not available"}), 500

    data = request.get_json(silent=True) or {}

    company_name = _sanitise(data.get("company_name", ""))
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400

    with SASession(engine) as s:
        entry = EmploymentHistory(
            candidate_id=cand_id,
            company_name=company_name,
            agency_name=_sanitise(data.get("agency_name", "")),
            referee_email=_sanitise(data.get("referee_email", "")),
            company_address=_sanitise(data.get("company_address", "")),
            start_date=_parse_date(data.get("start_date", "")),
            end_date=_parse_date(data.get("end_date", "")),
            job_title=_sanitise(data.get("job_title", "")),
            reason_for_leaving=_sanitise(data.get("reason_for_leaving", "")),
            is_gap=_parse_bool(data.get("is_gap", False)),
            gap_reason=_sanitise(data.get("gap_reason", "")),
            permission_to_request=_parse_bool(data.get("permission_to_request", True)),
            permission_delay_reason=_sanitise(data.get("permission_delay_reason", "")),
            permission_future_date=_parse_date(data.get("permission_future_date", "")),
            reference_status="not_sent",
        )
        s.add(entry)
        _add_note(s, cand_id, f"Employment history added: {company_name}.")
        s.commit()
        entry_id = entry.id

    return jsonify({"success": True, "id": entry_id})


@associate_bp.route("/api/add-qualification", methods=["POST"])
@_require_login
def api_add_qualification():
    """Add a qualification entry."""
    QualificationRecord = _portal_model("QualificationRecord")
    engine = _engine()
    cand_id = _get_associate_id()

    if not QualificationRecord:
        return jsonify({"error": "Qualifications not available"}), 500

    data = request.get_json(silent=True) or {}

    qual_name = _sanitise(data.get("qualification_name", ""))
    if not qual_name:
        return jsonify({"error": "Qualification name is required"}), 400

    with SASession(engine) as s:
        qual = QualificationRecord(
            candidate_id=cand_id,
            qualification_name=qual_name,
            qualification_type=_sanitise(data.get("qualification_type", "")),
            grade=_sanitise(data.get("grade", "")),
            institution=_sanitise(data.get("institution", "")),
            start_date=_parse_date(data.get("start_date", "")),
            end_date=_parse_date(data.get("end_date", "")),
            permission_to_request=_parse_bool(data.get("permission_to_request", True)),
            permission_delay_reason=_sanitise(data.get("permission_delay_reason", "")),
        )
        s.add(qual)
        _add_note(s, cand_id, f"Qualification added: {qual_name}.")
        s.commit()
        qual_id = qual.id

    return jsonify({"success": True, "id": qual_id})


@associate_bp.route("/api/download-document/<int:doc_id>")
@_require_login
def api_download_document(doc_id):
    """Download a document file belonging to the current associate."""
    Document = _model("Document")
    engine = _engine()
    cand_id = _get_associate_id()

    if not Document:
        abort(404)

    with SASession(engine) as s:
        doc = s.query(Document).filter_by(id=doc_id, candidate_id=cand_id).first()
        if not doc:
            abort(404)
        filepath = os.path.join(current_app.root_path, "static", doc.filename)
        if not os.path.isfile(filepath):
            abort(404)
        download_name = getattr(doc, "original_name", None) or os.path.basename(doc.filename)
        return send_file(filepath, as_attachment=True, download_name=download_name)


@associate_bp.route("/api/delete-document/<int:doc_id>", methods=["DELETE"])
@_require_login
def api_delete_document(doc_id):
    """Delete a document belonging to the current associate."""
    Document = _model("Document")
    engine = _engine()
    cand_id = _get_associate_id()

    if not Document:
        return jsonify({"success": False, "error": "Not available"}), 500

    with SASession(engine) as s:
        doc = s.query(Document).filter_by(id=doc_id, candidate_id=cand_id).first()
        if not doc:
            return jsonify({"success": False, "error": "Document not found"}), 404
        fname = getattr(doc, "original_name", doc.filename)
        # Remove file from disk
        filepath = os.path.join(current_app.root_path, "static", doc.filename)
        if os.path.isfile(filepath):
            os.remove(filepath)
        s.delete(doc)
        _add_note(s, cand_id, f"Document deleted: {fname}.")
        s.commit()

    return jsonify({"success": True})


# =========================================================================
# TIMESHEET CRUD ROUTES
# =========================================================================

@associate_bp.route("/timesheets/new", methods=["POST"])
@_require_login
def timesheets_new():
    """Create a new weekly timesheet."""
    Timesheet = _model("Timesheet")
    TimesheetConfig = _portal_model("TimesheetConfig")
    engine = _engine()
    cand_id = _get_associate_id()

    assignment_id = request.form.get("assignment_id")
    week_start_str = request.form.get("week_start", "")

    if not assignment_id or not week_start_str:
        flash("Please select an assignment and week.", "danger")
        return redirect(url_for("associate.timesheets"))

    week_start = _parse_date(week_start_str)
    if not week_start:
        flash("Invalid week start date.", "danger")
        return redirect(url_for("associate.timesheets"))

    # Ensure it's a Monday
    if hasattr(week_start, 'weekday') and week_start.weekday() != 0:
        flash("Week must start on a Monday.", "danger")
        return redirect(url_for("associate.timesheets"))

    week_end = week_start + timedelta(days=6)

    # Get engagement_id from Application
    Application = _model("Application")
    engagement_id = None
    with SASession(engine) as s:
        if Application:
            app = s.get(Application, int(assignment_id))
            if app and hasattr(app, "job") and app.job and hasattr(app.job, "engagement_id"):
                engagement_id = app.job.engagement_id

        # Load rates from config
        day_rate = 0
        overtime_rate = 0
        if engagement_id and TimesheetConfig:
            config = s.query(TimesheetConfig).filter_by(engagement_id=engagement_id).first()
            if config:
                day_rate = config.day_rate or 0
                overtime_rate = config.overtime_rate or 0

        ts = Timesheet(
            user_id=cand_id,
            engagement_id=engagement_id or 0,
            period_start=week_start,
            period_end=week_end,
            status="Draft",
        )
        if hasattr(ts, "week_start"):
            ts.week_start = week_start
            ts.week_end = week_end
            ts.day_rate = day_rate
            ts.overtime_rate = overtime_rate

        s.add(ts)
        s.commit()

    flash("New timesheet created.", "success")
    return redirect(url_for("associate.timesheets"))


@associate_bp.route("/timesheets/save", methods=["POST"])
@_require_login
def timesheets_save():
    """Save timesheet grid entries and expenses as Draft."""
    import json as _json
    Timesheet = _model("Timesheet")
    TimesheetEntry = _portal_model("TimesheetEntry")
    TimesheetExpense = _portal_model("TimesheetExpense")
    engine = _engine()
    cand_id = _get_associate_id()
    ts_id = request.form.get("timesheet_id")

    if not ts_id:
        flash("No timesheet specified.", "danger")
        return redirect(url_for("associate.timesheets"))

    with SASession(engine) as s:
        ts = s.get(Timesheet, int(ts_id))
        if not ts or ts.user_id != cand_id:
            flash("Timesheet not found.", "danger")
            return redirect(url_for("associate.timesheets"))

        # Delete existing entries and re-create from form
        if TimesheetEntry:
            s.query(TimesheetEntry).filter_by(timesheet_id=ts.id).delete()

            # Parse grid entries: entry_<date>_<time_type> = value
            total_days = 0
            total_hours = 0
            for key, val in request.form.items():
                if key.startswith("entry_") and val and val != "0" and val != "-":
                    parts = key.split("_", 2)  # entry_2026-03-23_Standard__Time
                    if len(parts) >= 3:
                        entry_date_str = parts[1]
                        time_type = parts[2].replace("__", " ")
                        try:
                            value = float(val)
                        except ValueError:
                            # Handle HH:MM format for overtime
                            if ":" in val:
                                hh, mm = val.split(":")
                                value = float(hh) + float(mm) / 60
                            else:
                                continue

                        unit = "hours" if "overtime" in time_type.lower() else "days"
                        entry = TimesheetEntry(
                            timesheet_id=ts.id,
                            entry_date=_parse_date(entry_date_str),
                            time_type=time_type,
                            value=value,
                            value_unit=unit,
                        )
                        s.add(entry)

                        if time_type.lower() == "standard time":
                            total_days += value
                        elif "overtime" in time_type.lower():
                            total_hours += value

            ts.billable_days = total_days
            ts.billable_hours = total_hours

        # Calculate totals
        day_rate = getattr(ts, "day_rate", 0) or 0
        ot_rate = getattr(ts, "overtime_rate", 0) or 0
        ts.total_amount = (ts.billable_days * day_rate) + (ts.billable_hours * ot_rate)
        ts.expense_total = getattr(ts, "expense_total", 0) or 0
        ts.grand_total = ts.total_amount + ts.expense_total

        ts.status = "Draft"
        s.commit()

    flash("Timesheet saved as draft.", "success")
    return redirect(url_for("associate.timesheets"))


@associate_bp.route("/timesheets/submit", methods=["POST"])
@_require_login
def timesheets_submit():
    """Submit a timesheet (saves entries first, then changes status to Submitted)."""
    import json as _json
    Timesheet = _model("Timesheet")
    TimesheetEntry = _portal_model("TimesheetEntry")
    engine = _engine()
    cand_id = _get_associate_id()
    ts_id = request.form.get("timesheet_id")

    if not ts_id:
        flash("No timesheet specified.", "danger")
        return redirect(url_for("associate.timesheets"))

    with SASession(engine) as s:
        ts = s.get(Timesheet, int(ts_id))
        if not ts or ts.user_id != cand_id:
            flash("Timesheet not found.", "danger")
            return redirect(url_for("associate.timesheets"))

        # Save entries from form before submitting
        if TimesheetEntry:
            s.query(TimesheetEntry).filter_by(timesheet_id=ts.id).delete()

            total_days = 0
            total_hours = 0
            for key, val in request.form.items():
                if key.startswith("entry_") and val and val != "0" and val != "-":
                    parts = key.split("_", 2)
                    if len(parts) >= 3:
                        entry_date_str = parts[1]
                        time_type = parts[2].replace("__", " ")
                        try:
                            value = float(val)
                        except ValueError:
                            if ":" in val:
                                hh, mm = val.split(":")
                                value = float(hh) + float(mm) / 60
                            else:
                                continue

                        unit = "hours" if "overtime" in time_type.lower() else "days"
                        entry = TimesheetEntry(
                            timesheet_id=ts.id,
                            entry_date=_parse_date(entry_date_str),
                            time_type=time_type,
                            value=value,
                            value_unit=unit,
                        )
                        s.add(entry)

                        if time_type.lower() == "standard time":
                            total_days += value
                        elif "overtime" in time_type.lower():
                            total_hours += value

            ts.billable_days = total_days
            ts.billable_hours = total_hours

        # Calculate totals
        day_rate = getattr(ts, "day_rate", 0) or 0
        ot_rate = getattr(ts, "overtime_rate", 0) or 0
        ts.total_amount = (ts.billable_days * day_rate) + (ts.billable_hours * ot_rate)
        ts.expense_total = getattr(ts, "expense_total", 0) or 0
        ts.grand_total = ts.total_amount + ts.expense_total

        ts.status = "Submitted"
        ts.submitted_at = datetime.utcnow()
        s.commit()

    flash("Timesheet submitted successfully.", "success")
    return redirect(url_for("associate.timesheets"))


@associate_bp.route("/timesheets/cancel", methods=["POST"])
@_require_login
def timesheets_cancel():
    """Cancel/delete a draft timesheet."""
    Timesheet = _model("Timesheet")
    TimesheetEntry = _portal_model("TimesheetEntry")
    TimesheetExpense = _portal_model("TimesheetExpense")
    engine = _engine()
    cand_id = _get_associate_id()
    ts_id = request.form.get("timesheet_id")

    if not ts_id:
        flash("No timesheet specified.", "danger")
        return redirect(url_for("associate.timesheets"))

    with SASession(engine) as s:
        ts = s.get(Timesheet, int(ts_id))
        if not ts or ts.user_id != cand_id:
            flash("Timesheet not found.", "danger")
            return redirect(url_for("associate.timesheets"))

        if ts.status not in ("Draft", "Unsubmitted", None, ""):
            flash("Only draft timesheets can be cancelled.", "warning")
            return redirect(url_for("associate.timesheets"))

        # Delete entries and expenses
        if TimesheetEntry:
            s.query(TimesheetEntry).filter_by(timesheet_id=ts.id).delete()
        if TimesheetExpense:
            s.query(TimesheetExpense).filter_by(timesheet_id=ts.id).delete()
        s.delete(ts)
        s.commit()

    flash("Timesheet cancelled.", "info")
    return redirect(url_for("associate.timesheets"))


# =========================================================================
# P1: VACANCY DETAIL ROUTE
# =========================================================================

@associate_bp.route("/vacancies/<int:job_id>")
@_require_login
def vacancy_detail(job_id):
    """P1: View details of a single vacancy."""
    Job = _model("Job")
    Application = _model("Application")
    Engagement = _model("Engagement")
    engine = _engine()
    cand_id = _get_associate_id()

    with SASession(engine) as s:
        job = s.get(Job, job_id) if Job else None
        if not job:
            flash("Vacancy not found.", "danger")
            return redirect(url_for("associate.vacancies"))

        engagement = s.get(Engagement, job.engagement_id) if Engagement and job.engagement_id else None

        already_applied = False
        if Application:
            existing = s.query(Application).filter_by(
                candidate_id=cand_id, job_id=job_id
            ).first()
            already_applied = existing is not None

        # Check if associate has a CV on file
        Document = _model("Document")
        has_cv = False
        if Document:
            cv_doc = s.query(Document).filter_by(
                candidate_id=cand_id, doc_type="cv"
            ).first()
            has_cv = cv_doc is not None

        return render_template(
            "associate/vacancy_detail.html",
            job=job,
            engagement=engagement,
            already_applied=already_applied,
            has_cv=has_cv,
        )


# =========================================================================
# P2: VACANCY APPLY ROUTE
# =========================================================================

@associate_bp.route("/vacancies/<int:job_id>/apply", methods=["POST"])
@_require_login
def vacancy_apply(job_id):
    """P2: Apply for a vacancy from the portal."""
    import secrets as _secrets
    Job = _model("Job")
    Application = _model("Application")
    Candidate = _model("Candidate")
    Document = _model("Document")
    engine = _engine()
    cand_id = _get_associate_id()

    with SASession(engine) as s:
        job = s.get(Job, job_id) if Job else None
        if not job:
            flash("Vacancy not found.", "danger")
            return redirect(url_for("associate.vacancies"))

        if Application:
            existing = s.query(Application).filter_by(
                candidate_id=cand_id, job_id=job_id
            ).first()
            if existing:
                flash("You have already applied for this role.", "info")
                return redirect(url_for("associate.vacancy_detail", job_id=job_id))

        # Check if CV is on file
        cand = s.get(Candidate, cand_id) if Candidate else None
        has_cv = False
        if Document:
            cv_doc = s.query(Document).filter_by(candidate_id=cand_id, doc_type="cv").first()
            has_cv = cv_doc is not None

        # Handle CV upload if no CV on file
        cv_file = request.files.get("cv_file")
        if not has_cv and not cv_file:
            flash("Please upload your CV to apply.", "danger")
            return redirect(url_for("associate.vacancy_detail", job_id=job_id))

        if cv_file and cv_file.filename:
            # Validate file type
            allowed_ext = {'.pdf', '.doc', '.docx'}
            from werkzeug.utils import secure_filename as _secure
            original_name = cv_file.filename
            ext = os.path.splitext(original_name)[1].lower()
            if ext not in allowed_ext:
                flash("CV must be a PDF, DOC, or DOCX file.", "danger")
                return redirect(url_for("associate.vacancy_detail", job_id=job_id))

            # Save the CV to the main uploads/cvs directory
            safe_name = _secure(original_name)
            unique_name = f"{_secrets.token_hex(8)}_{safe_name}"
            upload_dir = os.path.join(current_app.root_path, "uploads", "cvs")
            os.makedirs(upload_dir, exist_ok=True)
            cv_file.save(os.path.join(upload_dir, unique_name))

            # Create Document record
            if Document:
                doc = Document(
                    candidate_id=cand_id,
                    filename=unique_name,
                    original_name=original_name,
                    doc_type="cv",
                )
                s.add(doc)

        if Application:
            app = Application(
                candidate_id=cand_id,
                job_id=job_id,
                status="Pipeline",
            )
            s.add(app)
            s.flush()
            app_id = app.id
            print(f"[PORTAL] Application flushed: candidate_id={cand_id}, job_id={job_id}, app_id={app_id}, status=Pipeline, job_engagement_id={job.engagement_id}")
            try:
                _add_note(s, cand_id, f"Applied for {job.title} via Associate Portal.")
            except Exception as e:
                print(f"[PORTAL] Note failed (non-fatal): {e}")
            s.commit()
            print(f"[PORTAL] Application committed successfully: app_id={app_id}")

        flash(f"Application submitted for {job.title}.", "success")
        return redirect(url_for("associate.vacancy_detail", job_id=job_id))


# =========================================================================
# P2b: VACANCY WITHDRAW ROUTE
# =========================================================================

@associate_bp.route("/vacancies/<int:job_id>/withdraw", methods=["POST"])
@_require_login
def vacancy_withdraw(job_id):
    """Withdraw an application from the portal."""
    Application = _model("Application")
    engine = _engine()
    cand_id = _get_associate_id()

    with SASession(engine) as s:
        if Application:
            app = s.query(Application).filter_by(
                candidate_id=cand_id, job_id=job_id
            ).first()
            if app:
                s.delete(app)
                _add_note(s, cand_id, f"Withdrew application for job #{job_id} via Associate Portal.")
                s.commit()
                flash("Application withdrawn. You may re-apply.", "success")
            else:
                flash("No application found to withdraw.", "warning")

    return redirect(url_for("associate.vacancy_detail", job_id=job_id))


# =========================================================================
# P3: FORGOT PASSWORD ROUTE
# =========================================================================

@associate_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """P3: Send a password reset magic link."""
    Candidate = _model("Candidate")
    engine = _engine()

    if request.method == "GET":
        return render_template("associate/auth_forgot_password.html")

    email = _sanitise(request.form.get("email", "")).strip().lower()
    if not email:
        flash("Please enter your email address.", "danger")
        return redirect(url_for("associate.forgot_password"))

    with SASession(engine) as s:
        cand = s.query(Candidate).filter(Candidate.email.ilike(email)).first()
        if cand:
            try:
                _send_magic_link(email, cand.name or "Associate", is_signup=False)
            except Exception:
                pass  # Don't reveal whether account exists

    # Always show success to prevent email enumeration
    flash("If an account exists with that email, a password reset link has been sent.", "success")
    return render_template("associate/auth_check_email.html", email=email)


# =========================================================================
# P4: RESEND VERIFICATION ROUTE
# =========================================================================

@associate_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    """P4: Resend the email verification magic link."""
    Candidate = _model("Candidate")
    engine = _engine()

    email = _sanitise(request.form.get("email", "")).strip().lower()
    if not email:
        flash("Email address is required.", "danger")
        return redirect(url_for("associate.login"))

    with SASession(engine) as s:
        cand = s.query(Candidate).filter(Candidate.email.ilike(email)).first()
        if cand and not cand.password_hash:
            try:
                _send_magic_link(email, cand.name or "Associate", is_signup=True)
            except Exception:
                pass

    flash("If an account exists, a new verification link has been sent.", "success")
    return render_template("associate/auth_check_email.html", email=email)


# =========================================================================
# P5: EMPLOYMENT/GAP ENTRY EDIT
# =========================================================================

@associate_bp.route("/references/edit-entry/<int:entry_id>", methods=["POST"])
@_require_login
def references_edit_entry(entry_id):
    """P5: Edit an existing employment or gap entry."""
    EmploymentHistory = _portal_model("EmploymentHistory")
    engine = _engine()
    cand_id = _get_associate_id()

    if not EmploymentHistory:
        flash("Employment history not available.", "danger")
        return redirect(url_for("associate.references"))

    with SASession(engine) as s:
        entry = s.query(EmploymentHistory).filter_by(id=entry_id, candidate_id=cand_id).first()
        if not entry:
            flash("Entry not found.", "danger")
            return redirect(url_for("associate.references"))

        if entry.is_gap:
            entry.start_date = _parse_date(request.form.get("start_date", ""))
            entry.end_date = _parse_date(request.form.get("end_date", ""))
            entry.gap_reason = _sanitise(request.form.get("gap_reason", ""))
        else:
            entry.company_name = _sanitise(request.form.get("company_name", ""))
            entry.agency_name = _sanitise(request.form.get("agency_name", ""))
            entry.referee_email = _sanitise(request.form.get("referee_email", ""))
            entry.company_address = _sanitise(request.form.get("company_address", ""))
            entry.start_date = _parse_date(request.form.get("start_date", ""))
            entry.end_date = _parse_date(request.form.get("end_date", ""))
            entry.job_title = _sanitise(request.form.get("job_title", ""))
            entry.reason_for_leaving = _sanitise(request.form.get("reason_for_leaving", ""))
            perm = request.form.get("permission_to_request", "yes") == "yes"
            entry.permission_to_request = perm
            entry.permission_delay_reason = _sanitise(request.form.get("no_permission_reason", ""))
            entry.permission_future_date = _parse_date(request.form.get("future_permission_date", ""))

        _add_note(s, cand_id, f"Employment entry updated: {entry.company_name or 'Gap'}.")
        s.commit()

    flash("Entry updated successfully.", "success")
    return redirect(url_for("associate.references"))


@associate_bp.route("/api/edit-entry/<int:entry_id>", methods=["PUT", "POST"])
@_require_login
def api_edit_entry(entry_id):
    """P5: AJAX edit for employment/gap entry."""
    EmploymentHistory = _portal_model("EmploymentHistory")
    engine = _engine()
    cand_id = _get_associate_id()

    if not EmploymentHistory:
        return jsonify({"error": "Not available"}), 500

    data = request.get_json(silent=True) or {}

    with SASession(engine) as s:
        entry = s.query(EmploymentHistory).filter_by(id=entry_id, candidate_id=cand_id).first()
        if not entry:
            return jsonify({"error": "Not found"}), 404

        for field in ["company_name", "agency_name", "referee_email", "company_address",
                       "job_title", "reason_for_leaving", "gap_reason",
                       "permission_delay_reason"]:
            if field in data:
                setattr(entry, field, _sanitise(data[field]))
        for date_field in ["start_date", "end_date", "permission_future_date"]:
            if date_field in data:
                setattr(entry, date_field, _parse_date(data[date_field]))
        if "permission_to_request" in data:
            entry.permission_to_request = _parse_bool(data["permission_to_request"])

        _add_note(s, cand_id, f"Employment entry edited: {entry.company_name or 'Gap'}.")
        s.commit()

    return jsonify({"success": True})


# =========================================================================
# P6: EXPENSE INPUT ON TIMESHEETS
# =========================================================================

@associate_bp.route("/timesheets/add-expense", methods=["POST"])
@_require_login
def timesheets_add_expense():
    """P6: Add an expense line item to a timesheet."""
    TimesheetExpense = _portal_model("TimesheetExpense")
    Timesheet = _model("Timesheet")
    engine = _engine()
    cand_id = _get_associate_id()

    ts_id = request.form.get("timesheet_id", type=int)
    if not ts_id or not TimesheetExpense:
        flash("Cannot add expense.", "danger")
        return redirect(url_for("associate.timesheets"))

    with SASession(engine) as s:
        ts = s.get(Timesheet, ts_id)
        if not ts or ts.user_id != cand_id:
            flash("Timesheet not found.", "danger")
            return redirect(url_for("associate.timesheets"))

        if ts.status not in ("Draft", "Unsubmitted", None, ""):
            flash("Expenses can only be added to draft timesheets.", "warning")
            return redirect(url_for("associate.timesheets"))

        expense_type = _sanitise(request.form.get("expense_type", "Other"))
        description = _sanitise(request.form.get("expense_description", ""))
        try:
            amount = float(request.form.get("expense_amount", 0))
        except (ValueError, TypeError):
            amount = 0

        if amount <= 0:
            flash("Expense amount must be greater than zero.", "danger")
            return redirect(url_for("associate.timesheets"))

        # Handle receipt upload
        receipt_doc_id = None
        receipt_file = request.files.get("expense_receipt")
        if receipt_file and receipt_file.filename:
            ext = os.path.splitext(receipt_file.filename)[1].lower().lstrip(".")
            if ext in {"pdf", "jpg", "jpeg", "png"}:
                saved = _save_file(receipt_file)
                if saved:
                    Document = _model("Document")
                    if Document:
                        doc = Document(
                            candidate_id=cand_id,
                            doc_type="expense_receipt",
                            filename=saved["filename"],
                            original_name=saved["original_name"],
                        )
                        s.add(doc)
                        s.flush()
                        receipt_doc_id = doc.id

        expense = TimesheetExpense(
            timesheet_id=ts_id,
            expense_type=expense_type,
            description=description,
            amount=amount,
            receipt_doc_id=receipt_doc_id,
        )
        s.add(expense)

        # Update timesheet totals
        ts.expense_total = (ts.expense_total or 0) + amount
        ts.grand_total = (ts.total_amount or 0) + ts.expense_total

        _add_note(s, cand_id, f"Expense added: {expense_type} - GBP{amount:.2f}.")
        s.commit()

    flash(f"Expense added: {expense_type} - GBP{amount:.2f}.", "success")
    return redirect(url_for("associate.timesheets"))


@associate_bp.route("/timesheets/delete-expense/<int:expense_id>", methods=["POST"])
@_require_login
def timesheets_delete_expense(expense_id):
    """P6: Delete an expense from a timesheet."""
    TimesheetExpense = _portal_model("TimesheetExpense")
    Timesheet = _model("Timesheet")
    engine = _engine()
    cand_id = _get_associate_id()

    with SASession(engine) as s:
        expense = s.get(TimesheetExpense, expense_id) if TimesheetExpense else None
        if not expense:
            flash("Expense not found.", "danger")
            return redirect(url_for("associate.timesheets"))

        ts = s.get(Timesheet, expense.timesheet_id)
        if not ts or ts.user_id != cand_id:
            flash("Timesheet not found.", "danger")
            return redirect(url_for("associate.timesheets"))

        if ts.status not in ("Draft", "Unsubmitted", None, ""):
            flash("Cannot delete expenses from submitted timesheets.", "warning")
            return redirect(url_for("associate.timesheets"))

        ts.expense_total = max(0, (ts.expense_total or 0) - expense.amount)
        ts.grand_total = (ts.total_amount or 0) + ts.expense_total
        s.delete(expense)
        s.commit()

    flash("Expense removed.", "success")
    return redirect(url_for("associate.timesheets"))


# =========================================================================
# P7: 5-YEAR ADDRESS HISTORY
# =========================================================================

@associate_bp.route("/address-history", methods=["GET", "POST"])
@_require_login
def address_history():
    """P7: 5-year address history for DBS/Credit checks."""
    AddressHistory = _portal_model("AddressHistory")
    engine = _engine()
    cand_id = _get_associate_id()

    if not AddressHistory:
        flash("Address history not available.", "warning")
        return redirect(url_for("associate.dashboard"))

    if request.method == "GET":
        with SASession(engine) as s:
            addresses = s.query(AddressHistory).filter_by(
                candidate_id=cand_id
            ).order_by(AddressHistory.to_date.desc().nullslast()).all()

            # Calculate coverage
            total_months = 0
            for addr in addresses:
                if addr.from_date and addr.to_date:
                    delta = (addr.to_date.year - addr.from_date.year) * 12 + (addr.to_date.month - addr.from_date.month)
                    total_months += max(0, delta)
                elif addr.from_date and addr.is_current:
                    delta = (date.today().year - addr.from_date.year) * 12 + (date.today().month - addr.from_date.month)
                    total_months += max(0, delta)

            required_months = 60  # 5 years
            coverage_pct = min(100, int(total_months / required_months * 100)) if required_months > 0 else 0

            return render_template(
                "associate/address_history.html",
                addresses=addresses,
                coverage_pct=coverage_pct,
                total_months=total_months,
                required_months=required_months,
            )

    # POST: Add a new address
    with SASession(engine) as s:
        is_current = request.form.get("is_current") == "yes"
        addr = AddressHistory(
            candidate_id=cand_id,
            address_line1=_sanitise(request.form.get("address_line1", "")),
            address_line2=_sanitise(request.form.get("address_line2", "")),
            city=_sanitise(request.form.get("city", "")),
            postcode=_sanitise(request.form.get("postcode", "")),
            country=_sanitise(request.form.get("country", "United Kingdom")),
            from_date=_parse_date(request.form.get("from_date", "")),
            to_date=date.today() if is_current else _parse_date(request.form.get("to_date", "")),
            is_current=is_current,
        )
        s.add(addr)

        # If marking as current, unset other current addresses
        if is_current:
            others = s.query(AddressHistory).filter(
                AddressHistory.candidate_id == cand_id,
                AddressHistory.id != addr.id,
                AddressHistory.is_current == True  # noqa: E712
            ).all()
            for o in others:
                o.is_current = False

        _add_note(s, cand_id, f"Address added: {addr.address_line1}, {addr.city} {addr.postcode}.")
        s.commit()

    flash("Address added successfully.", "success")
    return redirect(url_for("associate.address_history"))


@associate_bp.route("/address-history/<int:addr_id>/delete", methods=["POST"])
@_require_login
def address_history_delete(addr_id):
    """P7: Delete an address history entry."""
    AddressHistory = _portal_model("AddressHistory")
    engine = _engine()
    cand_id = _get_associate_id()

    with SASession(engine) as s:
        addr = s.query(AddressHistory).filter_by(id=addr_id, candidate_id=cand_id).first() if AddressHistory else None
        if addr:
            s.delete(addr)
            s.commit()

    flash("Address removed.", "success")
    return redirect(url_for("associate.address_history"))


# =========================================================================
# P10: EMPLOYMENT COMPLETENESS ENFORCEMENT
# =========================================================================

def _check_employment_complete(session_obj, cand_id):
    """
    P10: Check if employment history covers the required period with no unexplained gaps.
    Returns (complete: bool, message: str).
    """
    EmploymentHistory = _portal_model("EmploymentHistory")
    if not EmploymentHistory:
        return True, ""

    entries = session_obj.query(EmploymentHistory).filter_by(candidate_id=cand_id).all()
    if not entries:
        return False, "No employment history entries. Please add your employment history before proceeding."

    # Check for unexplained gaps > 90 days
    employment_entries = [e for e in entries if not e.is_gap]
    gap_entries = [e for e in entries if e.is_gap]

    if not employment_entries:
        return False, "Please add at least one employment entry."

    # Sort by start_date
    sorted_entries = sorted(
        [e for e in entries if e.start_date],
        key=lambda e: e.start_date
    )

    for i in range(len(sorted_entries) - 1):
        current_end = sorted_entries[i].end_date
        next_start = sorted_entries[i + 1].start_date
        if current_end and next_start:
            gap_days = (next_start - current_end).days
            if gap_days > 90:
                # Check if gap is explained
                gap_covered = any(
                    g.is_gap and g.start_date and g.end_date
                    and g.start_date <= current_end + timedelta(days=7)
                    and g.end_date >= next_start - timedelta(days=7)
                    for g in gap_entries
                )
                if not gap_covered:
                    return False, f"Unexplained gap of {gap_days} days between entries. Please add a gap explanation."

    return True, ""
