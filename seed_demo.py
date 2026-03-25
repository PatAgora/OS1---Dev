#!/usr/bin/env python3
"""
seed_demo.py — Comprehensive demo data seed for OS1 ATS
========================================================
Run INSIDE Docker:  docker compose exec os1-app python seed_demo.py
Or standalone:      python seed_demo.py

Does NOT delete existing data. Checks counts before inserting.
Idempotent — safe to run multiple times.
"""

import os, sys, json, secrets, datetime, random
from datetime import timedelta, date

# ---------------------------------------------------------------------------
# Bootstrap — import everything from app.py
# ---------------------------------------------------------------------------
os.environ.setdefault("FLASK_SECRET_KEY", "seed-key-not-used")
from app import (
    engine, Base,
    User, PasswordHistory, AuditLog,
    Candidate, CandidateTag, CandidateNote, Document,
    Application, Job, Engagement, EngagementPlan,
    ESigRequest, VettingCheck, TrustIDCheck,
    Shortlist, Invoice, Opportunity,
    TaxonomyCategory, TaxonomyTag, RoleType,
    WebhookEvent, ReferenceRequest, ApprovedUmbrella, StageConfig,
)
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from werkzeug.security import generate_password_hash

# Try to import associate portal models
try:
    from associate_portal import _ensure_models, _portal_model, _base
    _ensure_models()
    AssociateProfile = _portal_model("AssociateProfile")
    CompanyDetails = _portal_model("CompanyDetails")
    ConsentRecord = _portal_model("ConsentRecord")
    DeclarationRecord = _portal_model("DeclarationRecord")
    EmploymentHistory = _portal_model("EmploymentHistory")
    QualificationRecord = _portal_model("QualificationRecord")
    ReferenceContact = _portal_model("ReferenceContact")
    FlaggedReferenceHouse = _portal_model("FlaggedReferenceHouse")
    AddressHistory = _portal_model("AddressHistory")
    # Ensure portal tables exist in the database
    _PortalBase = _base()
    if _PortalBase:
        _PortalBase.metadata.create_all(engine, checkfirst=True)
    PORTAL_MODELS = True
    print("[OK] Associate portal models loaded + tables created")
except Exception as e:
    PORTAL_MODELS = False
    print(f"[WARN] Portal models not available: {e}")

NOW = datetime.datetime.utcnow()
TODAY = date.today()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def days_ago(n):
    return NOW - timedelta(days=n)

def date_days_ago(n):
    return TODAY - timedelta(days=n)

def date_days_ahead(n):
    return TODAY + timedelta(days=n)

def dt_days_ahead(n):
    return NOW + timedelta(days=n)

def count(session, model):
    return session.scalar(select(func.count(model.id)))

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ---------------------------------------------------------------------------
# Data constants
# ---------------------------------------------------------------------------
CHECK_TYPES = [
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

UK_NAMES = [
    ("James", "Richardson", "M"), ("Sarah", "Mitchell", "F"), ("David", "Thompson", "M"),
    ("Emma", "Clarke", "F"), ("Michael", "Patel", "M"), ("Laura", "Williams", "F"),
    ("Robert", "Singh", "M"), ("Hannah", "Brown", "F"), ("Daniel", "O'Brien", "M"),
    ("Charlotte", "Taylor", "F"), ("Andrew", "Khan", "M"), ("Rebecca", "Jones", "F"),
    ("Thomas", "Evans", "M"), ("Sophie", "Green", "F"), ("Christopher", "Murphy", "M"),
    ("Jessica", "Wilson", "F"), ("Matthew", "Ahmed", "M"), ("Olivia", "Martin", "F"),
    ("William", "Davies", "M"), ("Emily", "Scott", "F"), ("Joseph", "Hall", "M"),
    ("Amelia", "Baker", "F"), ("Benjamin", "Cooper", "M"), ("Lucy", "Wood", "F"),
    ("Alexander", "Phillips", "M"),
]

POSTCODES = [
    "EC2R 8AH", "EC3V 3NG", "EC4M 7AN", "E14 5AB", "SE1 2QH",
    "M1 3BB", "M2 5BQ", "M3 4LU",
    "B1 1TT", "B2 5DB", "B3 2NS",
    "LS1 4AP", "EH2 4AD", "CF10 1EP",
    "SW1A 1AA", "W1S 4BS", "N1 9GU",
    "WC2N 5DU", "SE1 7PB", "EC1A 1BB",
    "E1 6AN", "NW1 2DB", "SW7 2AZ",
    "W1J 9HP", "EC2M 7EB",
]

SKILLS_POOL = [
    "KYC", "AML", "CDD", "EDD", "Compliance", "Risk Management",
    "Audit", "Financial Crime", "Sanctions Screening", "PEP Checks",
    "Transaction Monitoring", "Regulatory Reporting", "Basel III",
    "SOX Compliance", "GDPR", "Data Protection", "FCA Regulations",
    "Credit Risk", "Operational Risk", "Market Risk",
    "SAR Filing", "Client Onboarding", "Remediation",
    "Project Management", "Team Leadership",
]

LOCATIONS = ["London", "Manchester", "Birmingham", "Leeds", "Edinburgh", "Cardiff", "Bristol", "Reading"]


# ============================================================================
#  MAIN SEED
# ============================================================================
def seed():
    print("\n" + "="*60)
    print("  OS1 ATS — Comprehensive Demo Data Seed")
    print("="*60)

    with Session(engine) as s:

        # ------------------------------------------------------------------
        #  1. USERS
        # ------------------------------------------------------------------
        section("1. Users")
        existing_users = count(s, User)
        print(f"   Existing users: {existing_users}")

        user_specs = [
            {"name": "Admin User",          "email": "admin@demo.example.com",    "role": "admin",    "password": "DemoAdmin2024!"},
            {"name": "Sarah Recruiter",     "email": "sarah.r@optimus.demo",      "role": "employee", "password": "DemoPass2024!"},
            {"name": "James Recruiter",     "email": "james.r@optimus.demo",      "role": "employee", "password": "DemoPass2024!"},
            {"name": "Helen Manager",       "email": "helen.m@optimus.demo",      "role": "admin",    "password": "DemoPass2024!"},
            {"name": "Tom Analyst",         "email": "tom.a@optimus.demo",        "role": "employee", "password": "DemoPass2024!"},
        ]

        users = {}
        for spec in user_specs:
            existing = s.scalar(select(User).where(User.email == spec["email"]))
            if existing:
                users[spec["email"]] = existing
                print(f"   [SKIP] {spec['email']} already exists (id={existing.id})")
            else:
                u = User(
                    name=spec["name"],
                    email=spec["email"],
                    password_hash=generate_password_hash(spec["password"], method="pbkdf2:sha256"),
                    role=spec["role"],
                    is_active=True,
                    created_at=days_ago(90),
                    last_login=days_ago(random.randint(0, 5)),
                )
                s.add(u)
                s.flush()
                users[spec["email"]] = u
                print(f"   [ADD] {spec['email']} (id={u.id}, role={spec['role']})")
        s.commit()

        admin_user = users["admin@demo.example.com"]
        recruiter1 = users["sarah.r@optimus.demo"]
        recruiter2 = users["james.r@optimus.demo"]
        manager = users["helen.m@optimus.demo"]
        analyst = users["tom.a@optimus.demo"]

        # ------------------------------------------------------------------
        #  2. ROLE TYPES
        # ------------------------------------------------------------------
        section("2. Role Types")
        role_names = ["Case Handler", "Team Leader", "QC Analyst", "Project Manager", "Compliance Officer", "Risk Analyst"]
        for rn in role_names:
            existing = s.scalar(select(RoleType).where(RoleType.name == rn))
            if existing:
                print(f"   [SKIP] {rn}")
            else:
                s.add(RoleType(name=rn, default_rate=random.choice([200, 250, 300, 350])))
                print(f"   [ADD] {rn}")
        s.commit()

        # ------------------------------------------------------------------
        #  3. TAXONOMY
        # ------------------------------------------------------------------
        section("3. Taxonomy Categories & Tags")
        taxonomy_data = {
            ("subject", "Skills"): ["KYC", "AML", "CDD", "EDD", "Compliance", "Risk Management", "Audit", "Financial Crime", "Sanctions Screening", "PEP Checks", "Transaction Monitoring", "Regulatory Reporting"],
            ("subject", "Sector"): ["Banking", "Insurance", "Asset Management", "Fintech", "Payments", "Wealth Management"],
            ("subject", "Clearance"): ["SC Cleared", "CTC Cleared", "DV Cleared", "BPSS", "None"],
            ("subject", "Location"): ["London", "Manchester", "Birmingham", "Edinburgh", "Leeds", "Bristol", "Remote"],
        }

        tag_objects = {}
        for (cat_type, cat_name), tags in taxonomy_data.items():
            cat = s.scalar(select(TaxonomyCategory).where(TaxonomyCategory.name == cat_name, TaxonomyCategory.type == cat_type))
            if not cat:
                cat = TaxonomyCategory(type=cat_type, name=cat_name)
                s.add(cat)
                s.flush()
                print(f"   [ADD] Category: {cat_name} (type={cat_type})")
            else:
                print(f"   [SKIP] Category: {cat_name}")

            for tag_name in tags:
                t = s.scalar(select(TaxonomyTag).where(TaxonomyTag.category_id == cat.id, TaxonomyTag.tag == tag_name))
                if not t:
                    t = TaxonomyTag(category_id=cat.id, tag=tag_name)
                    s.add(t)
                    s.flush()
                tag_objects[tag_name] = t
        s.commit()

        # ------------------------------------------------------------------
        #  4. OPPORTUNITIES
        # ------------------------------------------------------------------
        section("4. Opportunities")
        if count(s, Opportunity) >= 5:
            print("   [SKIP] Already have 5+ opportunities")
            opps = s.scalars(select(Opportunity).limit(5)).all()
        else:
            opp_specs = [
                {"name": "Barclays Remediation Programme",    "client": "Barclays", "stage": "Closed Won",  "owner": recruiter1.email, "est_value": 850000,  "probability": 100, "client_contact_name": "Mark Stevens", "client_contact_email": "m.stevens@barclays.demo"},
                {"name": "HSBC Transaction Monitoring",       "client": "HSBC",     "stage": "Closed Won",  "owner": recruiter2.email, "est_value": 620000,  "probability": 100, "client_contact_name": "Lisa Chen",    "client_contact_email": "l.chen@hsbc.demo"},
                {"name": "Lloyds SAR Review",                 "client": "Lloyds",   "stage": "Closed Won",  "owner": recruiter1.email, "est_value": 380000,  "probability": 100, "client_contact_name": "John Harper",  "client_contact_email": "j.harper@lloyds.demo"},
                {"name": "NatWest KYC Uplift",                "client": "NatWest",  "stage": "Lead",        "owner": manager.email,    "est_value": 450000,  "probability": 40,  "client_contact_name": "Amy Foster",   "client_contact_email": "a.foster@natwest.demo"},
                {"name": "Standard Chartered EDD Programme",  "client": "Standard Chartered", "stage": "Closed Lost", "owner": recruiter2.email, "est_value": 700000, "probability": 0, "client_contact_name": "Raj Gupta", "client_contact_email": "r.gupta@sc.demo"},
            ]
            opps = []
            for spec in opp_specs:
                existing = s.scalar(select(Opportunity).where(Opportunity.name == spec["name"]))
                if existing:
                    opps.append(existing)
                    print(f"   [SKIP] {spec['name']}")
                else:
                    o = Opportunity(
                        name=spec["name"], client=spec["client"], stage=spec["stage"],
                        owner=spec["owner"], est_start=dt_days_ahead(random.randint(14, 90)),
                        est_value=spec["est_value"], probability=spec["probability"],
                        notes=f"Demo opportunity for {spec['client']}",
                        created_at=days_ago(random.randint(30, 120)),
                        client_contact_name=spec.get("client_contact_name", ""),
                        client_contact_email=spec.get("client_contact_email", ""),
                    )
                    s.add(o)
                    s.flush()
                    opps.append(o)
                    print(f"   [ADD] {spec['name']} (id={o.id})")
            s.commit()

        # ------------------------------------------------------------------
        #  5. ENGAGEMENTS
        # ------------------------------------------------------------------
        section("5. Engagements")
        eng_specs = [
            {"ref": "OS001", "name": "Barclays KYC Remediation",       "client": "Barclays", "status": "Active",    "start_days_ago": 120, "end_days_ahead": 90,  "ir35": "inside",  "opp_idx": 0, "location": "London"},
            {"ref": "OS002", "name": "Barclays AML Monitoring",        "client": "Barclays", "status": "Active",    "start_days_ago": 60,  "end_days_ahead": 30,  "ir35": "inside",  "opp_idx": 0, "location": "London"},
            {"ref": "OS003", "name": "HSBC Transaction Monitoring",    "client": "HSBC",     "status": "Active",    "start_days_ago": 90,  "end_days_ahead": 180, "ir35": "inside",  "opp_idx": 1, "location": "Birmingham"},
            {"ref": "OS004", "name": "HSBC Sanctions Screening",       "client": "HSBC",     "status": "Active",    "start_days_ago": 45,  "end_days_ahead": 120, "ir35": "outside", "opp_idx": 1, "location": "London"},
            {"ref": "OS005", "name": "Lloyds SAR Review (Completed)",  "client": "Lloyds",   "status": "Completed", "start_days_ago": 365, "end_days_ago": 30,    "ir35": "inside",  "opp_idx": 2, "location": "Edinburgh"},
        ]

        engagements = {}
        for spec in eng_specs:
            existing = s.scalar(select(Engagement).where(Engagement.ref == spec["ref"]))
            if existing:
                engagements[spec["ref"]] = existing
                print(f"   [SKIP] {spec['ref']} — {spec['name']}")
            else:
                end_date = days_ago(-spec["end_days_ahead"]) if "end_days_ahead" in spec else days_ago(spec.get("end_days_ago", 0))
                opp = opps[spec["opp_idx"]] if spec["opp_idx"] < len(opps) else None
                eng = Engagement(
                    ref=spec["ref"],
                    name=spec["name"],
                    client=spec["client"],
                    status=spec["status"],
                    start_date=days_ago(spec["start_days_ago"]),
                    end_date=end_date,
                    ir35_status=spec["ir35"],
                    description=f"Demo engagement: {spec['name']}",
                    opportunity_id=opp.id if opp and not s.scalar(select(Engagement).where(Engagement.opportunity_id == opp.id)) else None,
                    required_documents=json.dumps(["proof_of_id", "proof_of_address", "right_to_work"]),
                    reference_period_years=3,
                    gap_threshold_days=90,
                )
                s.add(eng)
                s.flush()
                engagements[spec["ref"]] = eng
                print(f"   [ADD] {spec['ref']} — {spec['name']} (id={eng.id})")
        s.commit()

        # ------------------------------------------------------------------
        #  6. ENGAGEMENT PLANS
        # ------------------------------------------------------------------
        section("6. Engagement Plans")
        if count(s, EngagementPlan) >= 15:
            print("   [SKIP] Already have 15+ engagement plans")
        else:
            plan_specs = [
                # OS001 Barclays KYC
                {"ref": "OS001", "role": "Case Handler",      "count": 10, "pay": 150, "charge": 220, "intake_offset": -30},
                {"ref": "OS001", "role": "Team Leader",       "count": 2,  "pay": 250, "charge": 350, "intake_offset": -30},
                {"ref": "OS001", "role": "QC Analyst",        "count": 3,  "pay": 200, "charge": 280, "intake_offset": -14},
                {"ref": "OS001", "role": "Project Manager",   "count": 1,  "pay": 300, "charge": 400, "intake_offset": -60},
                # OS002 Barclays AML
                {"ref": "OS002", "role": "Case Handler",      "count": 6,  "pay": 160, "charge": 230, "intake_offset": 7},
                {"ref": "OS002", "role": "Team Leader",       "count": 1,  "pay": 260, "charge": 360, "intake_offset": 7},
                {"ref": "OS002", "role": "Risk Analyst",      "count": 2,  "pay": 220, "charge": 300, "intake_offset": 14},
                # OS003 HSBC TM
                {"ref": "OS003", "role": "Case Handler",      "count": 8,  "pay": 155, "charge": 225, "intake_offset": -45},
                {"ref": "OS003", "role": "Team Leader",       "count": 2,  "pay": 255, "charge": 355, "intake_offset": -45},
                {"ref": "OS003", "role": "Compliance Officer", "count": 2, "pay": 270, "charge": 370, "intake_offset": 21},
                # OS004 HSBC Sanctions
                {"ref": "OS004", "role": "Case Handler",      "count": 5,  "pay": 165, "charge": 240, "intake_offset": -7},
                {"ref": "OS004", "role": "QC Analyst",        "count": 2,  "pay": 210, "charge": 290, "intake_offset": 0},
                # OS005 Lloyds SAR (completed)
                {"ref": "OS005", "role": "Case Handler",      "count": 4,  "pay": 150, "charge": 210, "intake_offset": -300},
                {"ref": "OS005", "role": "Team Leader",       "count": 1,  "pay": 240, "charge": 340, "intake_offset": -300},
                {"ref": "OS005", "role": "Project Manager",   "count": 1,  "pay": 280, "charge": 380, "intake_offset": -300},
            ]
            for spec in plan_specs:
                eng = engagements.get(spec["ref"])
                if not eng:
                    continue
                ep = EngagementPlan(
                    engagement_id=eng.id,
                    role_type=spec["role"],
                    planned_count=spec["count"],
                    pay_rate=spec["pay"],
                    charge_rate=spec["charge"],
                    rate=spec["charge"],
                    intake_date=dt_days_ahead(spec["intake_offset"]) if spec["intake_offset"] else None,
                )
                s.add(ep)
            s.commit()
            print(f"   [ADD] {len(plan_specs)} engagement plan rows")

        # ------------------------------------------------------------------
        #  7. JOBS (10)
        # ------------------------------------------------------------------
        section("7. Jobs")
        if count(s, Job) >= 10:
            print("   [SKIP] Already have 10+ jobs")
            jobs = s.scalars(select(Job).order_by(Job.id).limit(10)).all()
        else:
            job_specs = [
                # OS001 Barclays KYC
                {"eng_ref": "OS001", "title": "KYC Case Handler",          "role_type": "Case Handler",    "status": "Open",   "location": "London"},
                {"eng_ref": "OS001", "title": "KYC Team Leader",           "role_type": "Team Leader",     "status": "Open",   "location": "London"},
                # OS002 Barclays AML
                {"eng_ref": "OS002", "title": "AML Analyst",               "role_type": "Case Handler",    "status": "Open",   "location": "London"},
                {"eng_ref": "OS002", "title": "AML Risk Analyst",          "role_type": "Risk Analyst",    "status": "Open",   "location": "London"},
                # OS003 HSBC TM
                {"eng_ref": "OS003", "title": "Transaction Monitoring Analyst", "role_type": "Case Handler", "status": "Open", "location": "Birmingham"},
                {"eng_ref": "OS003", "title": "TM Team Leader",            "role_type": "Team Leader",     "status": "Open",   "location": "Birmingham"},
                # OS004 HSBC Sanctions
                {"eng_ref": "OS004", "title": "Sanctions Screening Analyst","role_type": "Case Handler",    "status": "Open",   "location": "London"},
                {"eng_ref": "OS004", "title": "QC Analyst — Sanctions",    "role_type": "QC Analyst",      "status": "Open",   "location": "London"},
                # OS005 Lloyds (filled — completed engagement)
                {"eng_ref": "OS005", "title": "SAR Reviewer",              "role_type": "Case Handler",    "status": "Filled", "location": "Edinburgh"},
                {"eng_ref": "OS005", "title": "SAR Team Leader",           "role_type": "Team Leader",     "status": "Filled", "location": "Edinburgh"},
            ]
            jobs = []
            for spec in job_specs:
                eng = engagements.get(spec["eng_ref"])
                if not eng:
                    continue
                j = Job(
                    engagement_id=eng.id,
                    title=spec["title"],
                    description=f"We are looking for an experienced {spec['title']} to join the {eng.name} programme. "
                                f"The role is based in {spec['location']} and requires strong {spec['role_type']} experience "
                                f"in financial services compliance.",
                    role_type=spec["role_type"],
                    location=spec["location"],
                    salary_range=f"£{random.randint(150,250)}-{random.randint(280,400)}/day",
                    status=spec["status"],
                    public_token=secrets.token_urlsafe(16),
                    created_at=days_ago(random.randint(7, 60)),
                )
                s.add(j)
                s.flush()
                jobs.append(j)
                print(f"   [ADD] {spec['title']} (id={j.id}, eng={spec['eng_ref']})")
            s.commit()

        # ------------------------------------------------------------------
        #  8. CANDIDATES (25)
        # ------------------------------------------------------------------
        section("8. Candidates")
        if count(s, Candidate) >= 25:
            print("   [SKIP] Already have 25+ candidates")
            candidates = s.scalars(select(Candidate).order_by(Candidate.id).limit(25)).all()
        else:
            candidates = []
            statuses = ["Available"] * 10 + ["On Contract"] * 8 + ["On Notice"] * 4 + ["Ex-Associate"] * 3
            random.shuffle(statuses)

            interview_results = [None] * 10 + ["Pass"] * 8 + ["Fail"] * 2 + ["Pending"] * 5
            assessment_results = [None] * 10 + ["Pass"] * 7 + ["Fail"] * 3 + ["Pending"] * 5
            random.shuffle(interview_results)
            random.shuffle(assessment_results)

            for i, (first, last, gender) in enumerate(UK_NAMES):
                email = f"{first.lower()}.{last.lower()}@candidate.demo"
                existing = s.scalar(select(Candidate).where(Candidate.email == email))
                if existing:
                    candidates.append(existing)
                    print(f"   [SKIP] {first} {last}")
                    continue

                num_skills = random.randint(3, 7)
                skills = ", ".join(random.sample(SKILLS_POOL, num_skills))
                cand_status = statuses[i] if i < len(statuses) else "Available"

                c = Candidate(
                    name=f"{first} {last}",
                    email=email,
                    phone=f"07{random.randint(100,999)} {random.randint(100,999)} {random.randint(100,999)}",
                    skills=skills,
                    postcode=POSTCODES[i],
                    location=random.choice(LOCATIONS),
                    status=cand_status,
                    availability="Immediately available" if cand_status == "Available" else ("2 weeks notice" if cand_status == "On Notice" else "On assignment"),
                    day_rate=random.choice([180, 200, 220, 250, 280, 300]),
                    min_day_rate=random.choice([150, 170, 180, 200]) if random.random() > 0.4 else None,
                    max_day_rate=random.choice([280, 300, 350, 400]) if random.random() > 0.4 else None,
                    previously_vetted=random.random() > 0.6,
                    last_login_at=days_ago(random.randint(0, 30)) if random.random() > 0.3 else None,
                    last_activity_at=days_ago(random.randint(0, 14)) if random.random() > 0.3 else None,
                    optimus_interview_result=interview_results[i] if i < len(interview_results) else None,
                    optimus_assessment_result=assessment_results[i] if i < len(assessment_results) else None,
                    gender=gender,
                    citizenship="British" if random.random() > 0.2 else random.choice(["Irish", "EU", "Other"]),
                    source="portal" if random.random() > 0.3 else "manual",
                    created_at=days_ago(random.randint(14, 180)),
                )
                s.add(c)
                s.flush()
                candidates.append(c)
                print(f"   [ADD] {c.name} (id={c.id}, status={cand_status})")
            s.commit()

        # ------------------------------------------------------------------
        #  8b. CANDIDATE TAGS
        # ------------------------------------------------------------------
        section("8b. Candidate Tags")
        existing_tags = count(s, CandidateTag)
        if existing_tags >= 30:
            print(f"   [SKIP] Already have {existing_tags} candidate tags")
        else:
            skill_tags = {k: v for k, v in tag_objects.items() if k in SKILLS_POOL}
            added = 0
            for c in candidates[:20]:
                tag_sample = random.sample(list(skill_tags.values()), min(3, len(skill_tags)))
                for t in tag_sample:
                    exists = s.scalar(select(CandidateTag).where(CandidateTag.candidate_id == c.id, CandidateTag.tag_id == t.id))
                    if not exists:
                        s.add(CandidateTag(candidate_id=c.id, tag_id=t.id))
                        added += 1
            s.commit()
            print(f"   [ADD] {added} candidate-tag links")

        # ------------------------------------------------------------------
        #  9. APPLICATIONS (40)
        # ------------------------------------------------------------------
        section("9. Applications")
        if count(s, Application) >= 40:
            print("   [SKIP] Already have 40+ applications")
            applications = s.scalars(select(Application).order_by(Application.id).limit(40)).all()
        else:
            # Workflow stages with counts
            stages = (
                [("Pipeline", 8), ("Shortlist", 6), ("I&A", 5), ("Client Review", 4),
                 ("Offered", 3), ("Accepted", 3), ("Vetting In-Flight", 3),
                 ("Ready to Contract", 2), ("Contract Sent", 2), ("Contract Signed", 2),
                 ("Rejected", 2)]
            )

            applications = []
            cand_idx = 0
            for stage, cnt in stages:
                for _ in range(cnt):
                    job = random.choice(jobs)
                    cand = candidates[cand_idx % len(candidates)]
                    cand_idx += 1

                    created = days_ago(random.randint(1, 60))
                    ai_score = random.randint(60, 95) if random.random() > 0.3 else 0
                    interview_dt = dt_days_ahead(random.randint(1, 14)) if stage in ("I&A", "Client Review") else None
                    interview_done = days_ago(random.randint(1, 10)) if stage in ("Offered", "Accepted", "Vetting In-Flight", "Ready to Contract", "Contract Sent", "Contract Signed") else None

                    app = Application(
                        job_id=job.id,
                        candidate_id=cand.id,
                        status=stage,
                        cover_note=f"Experienced {job.role_type} with strong financial services background. Keen to join {job.title} role.",
                        ai_score=ai_score,
                        ai_summary=f"Strong candidate with relevant {job.role_type} experience. Score {ai_score}/100." if ai_score else "",
                        ai_explanation=f"Candidate demonstrates {random.choice(['excellent', 'strong', 'good', 'solid'])} experience in {random.choice(SKILLS_POOL)} and {random.choice(SKILLS_POOL)}." if ai_score else "",
                        interview_scheduled_at=interview_dt,
                        interview_completed_at=interview_done,
                        interview_notes=f"Good interview. Candidate showed strong knowledge of {random.choice(SKILLS_POOL)}." if interview_done else "",
                        created_at=created,
                    )
                    s.add(app)
                    s.flush()
                    applications.append(app)
            s.commit()
            print(f"   [ADD] {len(applications)} applications across all workflow stages")

        # ------------------------------------------------------------------
        #  10. SHORTLISTS
        # ------------------------------------------------------------------
        section("10. Shortlists")
        if count(s, Shortlist) >= 8:
            print("   [SKIP] Already have 8+ shortlists")
        else:
            added = 0
            for i in range(min(8, len(candidates), len(jobs))):
                c = candidates[i]
                j = jobs[i % len(jobs)]
                exists = s.scalar(select(Shortlist).where(Shortlist.candidate_id == c.id, Shortlist.job_id == j.id))
                if not exists:
                    s.add(Shortlist(candidate_id=c.id, job_id=j.id, created_at=days_ago(random.randint(1, 30))))
                    added += 1
            s.commit()
            print(f"   [ADD] {added} shortlist entries")

        # ------------------------------------------------------------------
        #  11. E-SIGN REQUESTS (8)
        # ------------------------------------------------------------------
        section("11. E-Sign Requests")
        if count(s, ESigRequest) >= 8:
            print("   [SKIP] Already have 8+ e-sign requests")
        else:
            # Find applications in contract stages
            contract_apps = [a for a in applications if a.status in ("Contract Sent", "Contract Signed", "Ready to Contract", "Vetting In-Flight")]
            other_apps = [a for a in applications if a.status in ("Accepted", "Offered")]

            esig_specs = []
            # 4 signed
            for i in range(4):
                app = contract_apps[i] if i < len(contract_apps) else random.choice(applications)
                esig_specs.append({"app": app, "status": "Signed", "sent_ago": random.randint(10, 30), "signed_ago": random.randint(1, 9), "end_ahead": random.randint(30, 180)})
            # 2 sent (unsigned > 3 days for alert)
            for i in range(2):
                app = other_apps[i] if i < len(other_apps) else random.choice(applications)
                esig_specs.append({"app": app, "status": "Sent", "sent_ago": random.randint(4, 10), "signed_ago": None, "end_ahead": random.randint(60, 150)})
            # 2 completed
            for i in range(2):
                app = contract_apps[i + 4] if i + 4 < len(contract_apps) else random.choice(applications)
                esig_specs.append({"app": app, "status": "Completed", "sent_ago": random.randint(20, 50), "signed_ago": random.randint(15, 45), "end_ahead": random.randint(90, 180)})

            for spec in esig_specs:
                app = spec["app"]
                cand = s.get(Candidate, app.candidate_id)
                job = s.get(Job, app.job_id)
                eng_id = job.engagement_id if job else None

                esig = ESigRequest(
                    application_id=app.id,
                    candidate_id=app.candidate_id,
                    engagement_id=eng_id,
                    provider="signable",
                    request_id=f"SIG-{secrets.token_hex(6).upper()}",
                    status=spec["status"],
                    sent_at=days_ago(spec["sent_ago"]),
                    signed_at=days_ago(spec["signed_ago"]) if spec["signed_ago"] else None,
                    created_at=days_ago(spec["sent_ago"] + 1),
                    end_date=dt_days_ahead(spec["end_ahead"]),
                )
                s.add(esig)
            s.commit()
            print(f"   [ADD] {len(esig_specs)} e-sign requests")

        # ------------------------------------------------------------------
        #  12. VETTING CHECKS (~96)
        # ------------------------------------------------------------------
        section("12. Vetting Checks")
        if count(s, VettingCheck) >= 50:
            print("   [SKIP] Already have 50+ vetting checks")
        else:
            vc_added = 0
            # 3 candidates: ALL 12 checks COMPLETE
            for c in candidates[:3]:
                for ct in CHECK_TYPES:
                    exists = s.scalar(select(VettingCheck).where(VettingCheck.candidate_id == c.id, VettingCheck.check_type == ct))
                    if not exists:
                        s.add(VettingCheck(
                            candidate_id=c.id, check_type=ct, status="Complete",
                            notes=f"Verified — {ct} check passed", colour="green",
                            completed_at=days_ago(random.randint(5, 30)),
                            automation_enabled=True, external_provider="verifile",
                            external_ref=f"VF-{secrets.token_hex(4).upper()}",
                            assigned_to=analyst.id,
                            created_at=days_ago(random.randint(30, 60)),
                        ))
                        vc_added += 1

            # 2 candidates: IN PROGRESS (mixed)
            for c in candidates[3:5]:
                for i, ct in enumerate(CHECK_TYPES):
                    exists = s.scalar(select(VettingCheck).where(VettingCheck.candidate_id == c.id, VettingCheck.check_type == ct))
                    if not exists:
                        if i < 5:
                            status, colour = "Complete", "green"
                            completed = days_ago(random.randint(2, 15))
                        elif i < 9:
                            status, colour = "In Progress", "orange"
                            completed = None
                        else:
                            status, colour = "NOT STARTED", "white"
                            completed = None
                        s.add(VettingCheck(
                            candidate_id=c.id, check_type=ct, status=status,
                            notes=f"{ct} — {status.lower()}", colour=colour,
                            completed_at=completed,
                            automation_enabled=True, external_provider="verifile" if status != "NOT STARTED" else "",
                            external_ref=f"VF-{secrets.token_hex(4).upper()}" if status != "NOT STARTED" else "",
                            assigned_to=analyst.id,
                            created_at=days_ago(random.randint(15, 45)),
                        ))
                        vc_added += 1

            # 1 candidate: ON HOLD (declaration issue)
            if len(candidates) > 5:
                c = candidates[5]
                for i, ct in enumerate(CHECK_TYPES):
                    exists = s.scalar(select(VettingCheck).where(VettingCheck.candidate_id == c.id, VettingCheck.check_type == ct))
                    if not exists:
                        if i < 3:
                            status, colour = "Complete", "green"
                        elif ct == "DBS Check":
                            status, colour = "On Hold", "orange"
                        else:
                            status, colour = "NOT STARTED", "white"
                        s.add(VettingCheck(
                            candidate_id=c.id, check_type=ct, status=status,
                            notes=f"On hold — awaiting declaration clarification" if status == "On Hold" else f"{ct} check",
                            colour=colour,
                            completed_at=days_ago(random.randint(5, 20)) if status == "Complete" else None,
                            assigned_to=analyst.id,
                            created_at=days_ago(random.randint(10, 30)),
                        ))
                        vc_added += 1

            # 1 candidate: REFERRAL APPROVED
            if len(candidates) > 6:
                c = candidates[6]
                for i, ct in enumerate(CHECK_TYPES):
                    exists = s.scalar(select(VettingCheck).where(VettingCheck.candidate_id == c.id, VettingCheck.check_type == ct))
                    if not exists:
                        if i < 8:
                            status, colour = "Complete", "green"
                        elif ct == "Credit Check":
                            status, colour = "Referral Approved", "orange"
                        else:
                            status, colour = "In Progress", "orange"
                        s.add(VettingCheck(
                            candidate_id=c.id, check_type=ct, status=status,
                            notes=f"Referral approved by manager" if status == "Referral Approved" else f"{ct} check",
                            colour=colour,
                            completed_at=days_ago(random.randint(3, 20)) if status == "Complete" else None,
                            referral_approved_by=manager.id if status == "Referral Approved" else None,
                            referral_approved_at=days_ago(2) if status == "Referral Approved" else None,
                            assigned_to=analyst.id,
                            created_at=days_ago(random.randint(10, 40)),
                        ))
                        vc_added += 1

            # 1 candidate: WAITING FOR ASSOCIATE
            if len(candidates) > 7:
                c = candidates[7]
                for i, ct in enumerate(CHECK_TYPES):
                    exists = s.scalar(select(VettingCheck).where(VettingCheck.candidate_id == c.id, VettingCheck.check_type == ct))
                    if not exists:
                        if i < 4:
                            status, colour = "Complete", "green"
                        elif i < 7:
                            status, colour = "Waiting for Associate", "orange"
                        else:
                            status, colour = "NOT STARTED", "white"
                        s.add(VettingCheck(
                            candidate_id=c.id, check_type=ct, status=status,
                            notes=f"Awaiting associate to provide documents" if "Waiting" in status else f"{ct} check",
                            colour=colour,
                            completed_at=days_ago(random.randint(5, 25)) if status == "Complete" else None,
                            assigned_to=analyst.id,
                            created_at=days_ago(random.randint(10, 35)),
                        ))
                        vc_added += 1

            s.commit()
            print(f"   [ADD] {vc_added} vetting checks")

        # ------------------------------------------------------------------
        #  13. DOCUMENTS (15)
        # ------------------------------------------------------------------
        section("13. Documents")
        if count(s, Document) >= 15:
            print("   [SKIP] Already have 15+ documents")
        else:
            doc_specs = [
                ("cv",              "cv_{name}.pdf"),
                ("proof_of_id",     "passport_{name}.pdf"),
                ("proof_of_address", "utility_bill_{name}.pdf"),
                ("right_to_work",   "rtw_{name}.pdf"),
                ("consent_signed",  "consent_{name}.pdf"),
                ("declaration_signed", "declaration_{name}.pdf"),
            ]
            doc_added = 0
            for i, c in enumerate(candidates[:15]):
                doc_type, fname_template = doc_specs[i % len(doc_specs)]
                safe_name = c.name.lower().replace(" ", "_")
                fname = fname_template.format(name=safe_name)

                exists = s.scalar(select(Document).where(Document.candidate_id == c.id, Document.doc_type == doc_type))
                if exists:
                    continue

                exp_date = None
                if doc_type in ("proof_of_id", "right_to_work"):
                    # Some expiring soon for alerts, some far out
                    exp_date = date_days_ahead(random.choice([10, 15, 30, 90, 365]))

                s.add(Document(
                    candidate_id=c.id,
                    doc_type=doc_type,
                    filename=fname,
                    original_name=fname,
                    uploaded_at=days_ago(random.randint(5, 60)),
                    expiry_date=exp_date,
                ))
                doc_added += 1
            s.commit()
            print(f"   [ADD] {doc_added} documents")

        # ------------------------------------------------------------------
        #  14. INVOICES (5)
        # ------------------------------------------------------------------
        section("14. Invoices")
        if count(s, Invoice) >= 5:
            print("   [SKIP] Already have 5+ invoices")
        else:
            inv_specs = [
                {"number": "INV-2024-001", "client": "Barclays", "eng_ref": "OS001", "subtotal": 44000, "status": "Paid",    "days_ago": 60, "due_ago": 30, "paid": True},
                {"number": "INV-2024-002", "client": "Barclays", "eng_ref": "OS001", "subtotal": 38500, "status": "Pending",  "days_ago": 14, "due_ahead": 16, "paid": False},
                {"number": "INV-2024-003", "client": "HSBC",     "eng_ref": "OS003", "subtotal": 52000, "status": "Overdue",  "days_ago": 45, "due_ago": 15, "paid": False},
                {"number": "INV-2024-004", "client": "HSBC",     "eng_ref": "OS004", "subtotal": 18500, "status": "Draft",    "days_ago": 3,  "due_ahead": 27, "paid": False},
                {"number": "INV-2024-005", "client": "Lloyds",   "eng_ref": "OS005", "subtotal": 28000, "status": "Paid",     "days_ago": 120,"due_ago": 90, "paid": True},
            ]

            for spec in inv_specs:
                existing = s.scalar(select(Invoice).where(Invoice.invoice_number == spec["number"]))
                if existing:
                    print(f"   [SKIP] {spec['number']}")
                    continue

                eng = engagements.get(spec["eng_ref"])
                vat = spec["subtotal"] * 0.2
                total = spec["subtotal"] + vat
                due_date = days_ago(spec.get("due_ago", 0)) if "due_ago" in spec else dt_days_ahead(spec.get("due_ahead", 30))

                line_items = json.dumps([
                    {"description": f"Case Handlers x {random.randint(3,8)} @ £{random.randint(200,250)}/day x {random.randint(15,22)} days", "amount": spec["subtotal"] * 0.7},
                    {"description": f"Team Leader x 1 @ £{random.randint(300,380)}/day x {random.randint(15,22)} days", "amount": spec["subtotal"] * 0.3},
                ])

                inv = Invoice(
                    invoice_number=spec["number"],
                    engagement_id=eng.id if eng else None,
                    client_name=spec["client"],
                    engagement_name=eng.name if eng else "",
                    invoice_date=days_ago(spec["days_ago"]),
                    due_date=due_date,
                    paid_date=days_ago(spec["due_ago"] - 5) if spec["paid"] else None,
                    subtotal=spec["subtotal"],
                    vat_rate=20.0,
                    vat_amount=vat,
                    total_amount=total,
                    status=spec["status"],
                    line_items=line_items,
                    notes=f"Invoice for {spec['client']} — {eng.name if eng else 'N/A'}",
                    payment_terms="Net 30",
                    created_by=admin_user.id,
                    created_at=days_ago(spec["days_ago"]),
                )
                s.add(inv)
                print(f"   [ADD] {spec['number']} ({spec['status']}, £{total:,.0f})")
            s.commit()

        # ------------------------------------------------------------------
        #  15. CANDIDATE NOTES (10)
        # ------------------------------------------------------------------
        section("15. Candidate Notes")
        if count(s, CandidateNote) >= 10:
            print("   [SKIP] Already have 10+ candidate notes")
        else:
            note_templates = [
                ("note", "Spoke with {name} — available to start immediately. Strong KYC background with 3+ years in banking remediation."),
                ("note", "CV reviewed. {name} has excellent experience in AML transaction monitoring. Recommend for shortlist."),
                ("email", "Sent onboarding email pack to {name}. Awaiting confirmation of start date."),
                ("activity", "Interview completed with {name}. Positive feedback from hiring manager."),
                ("note", "Reference check initiated for {name}. Previous employer confirmed 2 years at Deutsche Bank."),
                ("system", "Vetting checks auto-triggered for {name} after acceptance."),
                ("note", "{name} confirmed availability for HSBC engagement starting next Monday."),
                ("email", "Contract sent to {name} via Signable. Awaiting signature."),
                ("note", "Right to Work documentation received from {name}. British passport — verified."),
                ("activity", "Profile updated by {name} via Associate Portal. New qualifications added."),
            ]

            for i, (ntype, template) in enumerate(note_templates):
                c = candidates[i % len(candidates)]
                user_email = [recruiter1.email, recruiter2.email, manager.email, analyst.email][i % 4]
                s.add(CandidateNote(
                    candidate_id=c.id,
                    user_email=user_email,
                    note_type=ntype,
                    content=template.format(name=c.name),
                    created_at=days_ago(random.randint(1, 30)),
                ))
            s.commit()
            print(f"   [ADD] 10 candidate notes")

        # ------------------------------------------------------------------
        #  16. REFERENCE REQUESTS (10)
        # ------------------------------------------------------------------
        section("16. Reference Requests")
        if count(s, ReferenceRequest) >= 10:
            print("   [SKIP] Already have 10+ reference requests")
        else:
            ref_companies = [
                "Deutsche Bank", "JP Morgan", "Goldman Sachs", "Morgan Stanley", "Citi",
                "BNP Paribas", "Credit Suisse", "UBS", "Nomura", "Macquarie",
            ]
            ref_statuses = ["not_sent", "sent", "sent", "received", "received", "received", "sent", "flagged", "on_hold", "sent"]

            for i in range(10):
                c = candidates[i % len(candidates)]
                company = ref_companies[i]
                status = ref_statuses[i]
                s.add(ReferenceRequest(
                    candidate_id=c.id,
                    company_name=company,
                    referee_email=f"hr@{company.lower().replace(' ', '')}.demo",
                    referee_name=f"{random.choice(['Sarah', 'Mark', 'Lisa', 'John', 'Emma'])} {random.choice(['Smith', 'Jones', 'Brown', 'Taylor', 'Wilson'])}",
                    status=status,
                    permission_status="yes",
                    sent_at=days_ago(random.randint(5, 20)) if status not in ("not_sent",) else None,
                    received_at=days_ago(random.randint(1, 10)) if status == "received" else None,
                    chase_count=random.randint(0, 3) if status == "sent" else 0,
                    last_chased_at=days_ago(random.randint(1, 5)) if status == "sent" else None,
                    hold_until=date_days_ahead(random.randint(3, 14)) if status == "on_hold" else None,
                    colour="green" if status == "received" else ("orange" if status in ("flagged", "on_hold") else "white"),
                    notes=f"Reference request for {c.name} from {company}",
                    created_at=days_ago(random.randint(10, 40)),
                ))
            s.commit()
            print(f"   [ADD] 10 reference requests")

        # ------------------------------------------------------------------
        #  17. REFERENCE CONTACTS (approved) — 20
        # ------------------------------------------------------------------
        section("17. Reference Contacts (Approved)")
        if PORTAL_MODELS and ReferenceContact:
            if s.scalar(select(func.count(ReferenceContact.id))) >= 20:
                print("   [SKIP] Already have 20+ reference contacts")
            else:
                companies = [
                    "Deutsche Bank", "JP Morgan", "Goldman Sachs", "Morgan Stanley", "Citi",
                    "BNP Paribas", "Credit Suisse", "UBS", "Nomura", "Macquarie",
                    "Barclays", "HSBC", "Lloyds Banking Group", "NatWest Group", "Standard Chartered",
                    "Nationwide", "Santander UK", "Virgin Money", "TSB", "Metro Bank",
                ]
                for company in companies:
                    exists = s.scalar(select(ReferenceContact).where(ReferenceContact.company_name == company))
                    if not exists:
                        s.add(ReferenceContact(
                            company_name=company,
                            referee_email=f"references@{company.lower().replace(' ', '').replace('.', '')}.demo",
                        ))
                s.commit()
                print(f"   [ADD] {len(companies)} approved reference contacts")
        else:
            print("   [SKIP] Portal models not available")

        # ------------------------------------------------------------------
        #  18. FLAGGED REFERENCE HOUSES — 5
        # ------------------------------------------------------------------
        section("18. Flagged Reference Houses")
        if PORTAL_MODELS and FlaggedReferenceHouse:
            if s.scalar(select(func.count(FlaggedReferenceHouse.id))) >= 5:
                print("   [SKIP] Already have 5+ flagged reference houses")
            else:
                flagged = [
                    {"name": "QuickRef Solutions Ltd",    "count": 7,  "clients": "Multiple banks",       "notes": "Suspected fabricated references. Under investigation."},
                    {"name": "FastTrack Staffing",        "count": 4,  "clients": "HSBC, Barclays",       "notes": "References could not be verified. Company dissolved."},
                    {"name": "Premier Compliance Agency",  "count": 3,  "clients": "Lloyds, NatWest",      "notes": "Referee phone numbers disconnected. Companies House shows dormant."},
                    {"name": "City Talent Partners",       "count": 5,  "clients": "Multiple institutions", "notes": "Pattern of identical reference wording across candidates."},
                    {"name": "Elite Financial Resourcing", "count": 2,  "clients": "Standard Chartered",   "notes": "Under review — referee email domains recently registered."},
                ]
                for f in flagged:
                    exists = s.scalar(select(FlaggedReferenceHouse).where(FlaggedReferenceHouse.name == f["name"]))
                    if not exists:
                        s.add(FlaggedReferenceHouse(
                            name=f["name"],
                            candidate_count=f["count"],
                            end_clients=f["clients"],
                            notes=f["notes"],
                        ))
                s.commit()
                print(f"   [ADD] 5 flagged reference houses")
        else:
            print("   [SKIP] Portal models not available")

        # ------------------------------------------------------------------
        #  19. AUDIT LOG (20)
        # ------------------------------------------------------------------
        section("19. Audit Log")
        if count(s, AuditLog) >= 20:
            print("   [SKIP] Already have 20+ audit log entries")
        else:
            audit_specs = [
                ("login",       "auth",        "User logged in",                        "success"),
                ("login",       "auth",        "User logged in",                        "success"),
                ("login",       "auth",        "Failed login attempt",                  "failure"),
                ("create",      "user_mgmt",   "Created new user account",              "success"),
                ("create",      "user_mgmt",   "Created new user account",              "success"),
                ("update",      "data_access", "Application moved to Shortlist",        "success"),
                ("update",      "data_access", "Application moved to I&A",              "success"),
                ("update",      "data_access", "Application moved to Client Review",    "success"),
                ("update",      "data_access", "Application moved to Accepted",         "success"),
                ("update",      "data_access", "Application moved to Vetting In-Flight","success"),
                ("update",      "data_access", "Vetting check completed",               "success"),
                ("update",      "data_access", "Vetting check completed",               "success"),
                ("create",      "data_access", "Contract sent via Signable",            "success"),
                ("create",      "data_access", "Contract signed — auto-moved to Contract Signed", "success"),
                ("update",      "security",    "2FA enabled for user",                  "success"),
                ("export",      "data_access", "Resource pool exported to CSV",         "success"),
                ("view",        "data_access", "Viewed candidate profile",              "success"),
                ("update",      "data_access", "Invoice status updated to Paid",        "success"),
                ("create",      "data_access", "New engagement created",                "success"),
                ("login",       "auth",        "User logged in from new IP",            "warning"),
            ]

            user_ids = [admin_user.id, recruiter1.id, recruiter2.id, manager.id, analyst.id]
            user_emails = [admin_user.email, recruiter1.email, recruiter2.email, manager.email, analyst.email]

            for i, (etype, ecat, action, status) in enumerate(audit_specs):
                idx = i % len(user_ids)
                s.add(AuditLog(
                    timestamp=days_ago(random.randint(0, 30)),
                    user_id=user_ids[idx],
                    user_email=user_emails[idx],
                    event_type=etype,
                    event_category=ecat,
                    action=action,
                    status=status,
                    ip_address=f"192.168.1.{random.randint(10, 200)}",
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                    details=json.dumps({"demo": True}),
                ))
            s.commit()
            print(f"   [ADD] 20 audit log entries")

        # ------------------------------------------------------------------
        #  20. APPROVED UMBRELLA COMPANIES
        # ------------------------------------------------------------------
        section("20. Approved Umbrella Companies")
        if count(s, ApprovedUmbrella) >= 3:
            print("   [SKIP] Already have 3+ umbrella companies")
        else:
            umbrellas = [
                {"name": "Parasol Group", "email": "onboarding@parasol.demo", "phone": "0161 123 4567", "url": "https://parasol.demo/signup"},
                {"name": "Brookson One",  "email": "join@brookson.demo",      "phone": "0161 987 6543", "url": "https://brookson.demo/register"},
                {"name": "Giant Group",   "email": "hello@giant.demo",        "phone": "0330 024 0000", "url": "https://giant.demo/join"},
            ]
            for u in umbrellas:
                exists = s.scalar(select(ApprovedUmbrella).where(ApprovedUmbrella.name == u["name"]))
                if not exists:
                    s.add(ApprovedUmbrella(name=u["name"], email=u["email"], phone=u["phone"], signup_url=u["url"], is_active=True))
            s.commit()
            print(f"   [ADD] {len(umbrellas)} approved umbrella companies")

        # ------------------------------------------------------------------
        #  21. ASSOCIATE PORTAL DATA
        # ------------------------------------------------------------------
        section("21. Associate Portal Data")
        if PORTAL_MODELS and AssociateProfile:
            # Create profiles for first 10 candidates
            profile_added = 0
            for i, c in enumerate(candidates[:10]):
                existing = s.scalar(select(AssociateProfile).where(AssociateProfile.candidate_id == c.id))
                if existing:
                    continue

                first, last = c.name.split(" ", 1)
                profile = AssociateProfile(
                    candidate_id=c.id,
                    title=random.choice(["Mr", "Mrs", "Ms", "Dr"]),
                    first_name=first,
                    surname=last,
                    dob=date(random.randint(1975, 1998), random.randint(1, 12), random.randint(1, 28)),
                    address_line1=f"{random.randint(1, 200)} {random.choice(['High Street', 'Kings Road', 'Church Lane', 'Park Avenue', 'Victoria Road'])}",
                    city=random.choice(LOCATIONS),
                    postcode=c.postcode or "EC2R 8AH",
                    contact_number=c.phone,
                    emergency_contact_name=f"{random.choice(['John', 'Mary', 'David', 'Sarah'])} {last}",
                    emergency_contact_phone=f"07{random.randint(100,999)} {random.randint(100,999)} {random.randint(100,999)}",
                    emergency_contact_relationship=random.choice(["Spouse", "Parent", "Sibling", "Partner"]),
                    national_insurance_number=f"AB{random.randint(10,99)}{random.randint(10,99)}{random.randint(10,99)}C",
                    gender=random.choice(["Male", "Female"]),
                )
                s.add(profile)
                profile_added += 1
            s.commit()
            print(f"   [ADD] {profile_added} associate profiles")

            # Company details for first 8
            cd_added = 0
            for i, c in enumerate(candidates[:8]):
                existing = s.scalar(select(CompanyDetails).where(CompanyDetails.candidate_id == c.id))
                if existing:
                    continue
                ctype = "umbrella" if random.random() > 0.4 else "limited"
                s.add(CompanyDetails(
                    candidate_id=c.id,
                    contracting_type=ctype,
                    company_name=random.choice(["Parasol Group", "Brookson One", "Giant Group"]) if ctype == "umbrella" else f"{c.name.split()[1]} Consulting Ltd",
                    umbrella_company_name=random.choice(["Parasol Group", "Brookson One"]) if ctype == "umbrella" else "",
                ))
                cd_added += 1
            s.commit()
            print(f"   [ADD] {cd_added} company details records")

            # Consent records for first 8
            consent_added = 0
            for c in candidates[:8]:
                existing = s.scalar(select(ConsentRecord).where(ConsentRecord.candidate_id == c.id))
                if not existing:
                    s.add(ConsentRecord(
                        candidate_id=c.id,
                        consent_given=True,
                        legal_name=c.name,
                        signed_date=days_ago(random.randint(5, 30)),
                        ip_address=f"192.168.1.{random.randint(10, 200)}",
                    ))
                    consent_added += 1
            s.commit()
            print(f"   [ADD] {consent_added} consent records")

            # Declaration records for first 8
            decl_added = 0
            for i, c in enumerate(candidates[:8]):
                existing = s.scalar(select(DeclarationRecord).where(DeclarationRecord.candidate_id == c.id))
                if not existing:
                    # One candidate with declarations to test the hold workflow
                    has_issues = (i == 5)
                    s.add(DeclarationRecord(
                        candidate_id=c.id,
                        work_restrictions=has_issues,
                        work_restrictions_detail="Tier 2 visa — expires Dec 2026" if has_issues else "",
                        criminal_convictions=False,
                        ccj_debt=has_issues,
                        ccj_debt_detail="CCJ from 2019 — satisfied and discharged" if has_issues else "",
                        bankruptcy=False,
                        dismissed=False,
                        referencing_issues=False,
                        legal_name=c.name,
                        signed_date=days_ago(random.randint(5, 30)),
                        ip_address=f"192.168.1.{random.randint(10, 200)}",
                    ))
                    decl_added += 1
            s.commit()
            print(f"   [ADD] {decl_added} declaration records")

            # Employment history for first 10 candidates
            emp_added = 0
            emp_companies = [
                ("Deutsche Bank", "KYC Analyst"), ("JP Morgan", "AML Analyst"),
                ("Goldman Sachs", "Compliance Officer"), ("Barclays", "Case Handler"),
                ("HSBC", "Transaction Monitoring Analyst"), ("Citi", "Risk Analyst"),
                ("BNP Paribas", "Regulatory Reporting Analyst"), ("UBS", "Financial Crime Analyst"),
                ("Morgan Stanley", "Sanctions Analyst"), ("Nomura", "Remediation Specialist"),
            ]
            for i, c in enumerate(candidates[:10]):
                existing_count = s.scalar(select(func.count(EmploymentHistory.id)).where(EmploymentHistory.candidate_id == c.id))
                if existing_count and existing_count >= 2:
                    continue
                # 2-3 employment records each
                num_jobs = random.randint(2, 3)
                end = date_days_ago(random.randint(30, 60))
                for j in range(num_jobs):
                    comp, title = emp_companies[(i * 3 + j) % len(emp_companies)]
                    start = end - timedelta(days=random.randint(180, 730))
                    s.add(EmploymentHistory(
                        candidate_id=c.id,
                        company_name=comp,
                        job_title=title,
                        start_date=start,
                        end_date=end if j > 0 else None,  # Current job has no end date
                        reason_for_leaving=random.choice(["Contract ended", "Seeking new opportunity", "Redundancy", ""]) if j > 0 else "",
                        permission_to_request=True,
                        referee_email=f"hr@{comp.lower().replace(' ', '')}.demo",
                    ))
                    emp_added += 1
                    end = start - timedelta(days=random.randint(14, 60))
            s.commit()
            print(f"   [ADD] {emp_added} employment history records")

            # Qualification records for first 8
            qual_added = 0
            quals = [
                ("ICA Certificate in AML", "Professional", "Pass", "International Compliance Association"),
                ("CISI Level 3 Compliance", "Professional", "Distinction", "Chartered Institute for Securities & Investment"),
                ("BSc Finance", "Degree", "2:1", "University of Manchester"),
                ("MSc Financial Crime", "Postgraduate", "Merit", "University of London"),
                ("ACAMS Certification", "Professional", "Pass", "Association of Certified AML Specialists"),
                ("BA Economics", "Degree", "First", "University of Edinburgh"),
                ("FCA Approved Persons", "Professional", "Pass", "Financial Conduct Authority"),
                ("CFA Level 1", "Professional", "Pass", "CFA Institute"),
            ]
            for i, c in enumerate(candidates[:8]):
                existing = s.scalar(select(func.count(QualificationRecord.id)).where(QualificationRecord.candidate_id == c.id))
                if existing and existing >= 1:
                    continue
                qname, qtype, grade, inst = quals[i % len(quals)]
                s.add(QualificationRecord(
                    candidate_id=c.id,
                    qualification_name=qname,
                    qualification_type=qtype,
                    grade=grade,
                    institution=inst,
                    start_date=date(random.randint(2015, 2020), 9, 1),
                    end_date=date(random.randint(2020, 2023), 6, 30),
                    permission_to_request=True,
                ))
                qual_added += 1
            s.commit()
            print(f"   [ADD] {qual_added} qualification records")

            # Address history for first 8
            addr_added = 0
            for i, c in enumerate(candidates[:8]):
                existing = s.scalar(select(func.count(AddressHistory.id)).where(AddressHistory.candidate_id == c.id))
                if existing and existing >= 1:
                    continue
                # Current address
                s.add(AddressHistory(
                    candidate_id=c.id,
                    address_line1=f"{random.randint(1, 200)} {random.choice(['High St', 'Kings Rd', 'Church Ln', 'Park Ave'])}",
                    city=random.choice(LOCATIONS),
                    postcode=POSTCODES[i % len(POSTCODES)],
                    from_date=date_days_ago(random.randint(365, 730)),
                    is_current=True,
                ))
                # Previous address
                s.add(AddressHistory(
                    candidate_id=c.id,
                    address_line1=f"{random.randint(1, 300)} {random.choice(['Oak Street', 'Mill Lane', 'Station Road'])}",
                    city=random.choice(LOCATIONS),
                    postcode=POSTCODES[(i + 5) % len(POSTCODES)],
                    from_date=date_days_ago(random.randint(1095, 1825)),
                    to_date=date_days_ago(random.randint(365, 730)),
                    is_current=False,
                ))
                addr_added += 2
            s.commit()
            print(f"   [ADD] {addr_added} address history records")
        else:
            print("   [SKIP] Portal models not available — skipping associate data")

        # ------------------------------------------------------------------
        #  22. PORTAL-READY CANDIDATES (passwords for portal login)
        # ------------------------------------------------------------------
        section("22. Portal-Ready Candidate Passwords")
        portal_candidates = candidates[:5]
        portal_pw = generate_password_hash("DemoCandidate2024!", method="pbkdf2:sha256")
        pw_set = 0
        for c in portal_candidates:
            if not c.password_hash:
                c.password_hash = portal_pw
                c.email_verified = True
                if hasattr(c, "email_verified_at") and not c.email_verified_at:
                    c.email_verified_at = days_ago(random.randint(5, 30))
                pw_set += 1
        s.commit()
        if pw_set:
            print(f"   [ADD] Set passwords for {pw_set} candidates (password: DemoCandidate2024!)")
            for c in portal_candidates:
                print(f"         Portal login: {c.email} / DemoCandidate2024!")
        else:
            print("   [SKIP] Candidates already have passwords")

        # ------------------------------------------------------------------
        #  23. CV FILES ON DISK (for AI scoring)
        # ------------------------------------------------------------------
        section("23. CV Files on Disk")
        import pathlib
        cv_dir = pathlib.Path(os.path.dirname(__file__)) / "uploads" / "cvs"
        cv_dir.mkdir(parents=True, exist_ok=True)

        CV_TEMPLATES = [
            # 0: KYC/AML specialist
            """CURRICULUM VITAE

{name}
{email} | {phone} | {location}

PROFESSIONAL SUMMARY
Experienced KYC/AML analyst with {years}+ years in financial services compliance. Strong track record in customer due diligence, enhanced due diligence, and suspicious activity reporting across tier-1 banking institutions. CISI Level 3 qualified with deep understanding of FCA regulations and the Money Laundering Regulations 2017.

KEY SKILLS
- Know Your Customer (KYC) / Customer Due Diligence (CDD)
- Anti-Money Laundering (AML) / Counter-Terrorist Financing (CTF)
- Enhanced Due Diligence (EDD) for high-risk customers
- Suspicious Activity Reports (SARs) filing
- Transaction monitoring and alert investigation
- PEP and sanctions screening (World-Check, Dow Jones)
- FCA regulatory compliance
- Risk assessment and categorisation

PROFESSIONAL EXPERIENCE

Senior KYC Analyst — Deutsche Bank, London
{start1} - Present
- Led a team of 8 analysts conducting CDD/EDD reviews on corporate and institutional clients
- Processed 200+ KYC reviews per month with 99.2% quality pass rate
- Developed risk-based approach to periodic reviews reducing backlog by 35%
- Identified 12 high-risk clients requiring enhanced monitoring

KYC Analyst — Barclays, London
{start2} - {end2}
- Conducted KYC onboarding and periodic reviews for retail and wealth management clients
- Screened clients against sanctions lists, PEP databases, and adverse media
- Escalated 45+ cases to MLRO for SAR consideration
- Achieved highest quality scores in quarterly audits

Compliance Assistant — HSBC, Birmingham
{start3} - {end3}
- Supported AML compliance team with transaction monitoring alerts
- Assisted in remediation project reviewing 5,000+ client files
- Conducted name screening and adverse media checks

EDUCATION
BSc (Hons) Finance — University of Manchester (2:1)
CISI Level 3 Certificate in Compliance
ICA Certificate in Anti-Money Laundering
""",
            # 1: Transaction monitoring analyst
            """CURRICULUM VITAE

{name}
{email} | {phone} | {location}

PROFESSIONAL SUMMARY
Detail-oriented transaction monitoring analyst with {years}+ years specialising in AML alert investigation and SAR filing. Proven ability to analyse complex financial transactions, identify suspicious patterns, and produce regulatory-quality documentation. Experienced with Actimize, Mantas, and Norkom monitoring platforms.

KEY SKILLS
- Transaction monitoring and alert investigation
- SAR/STR drafting and filing
- Typology identification (trade-based ML, layering, structuring)
- Actimize / NICE Actimize platform
- Sanctions screening (World-Check, Fircosoft)
- Data analysis and pattern recognition
- Regulatory reporting (FCA, NCA)
- Quality control and peer review

PROFESSIONAL EXPERIENCE

Senior TM Analyst — HSBC, Birmingham
{start1} - Present
- Investigate Level 2 and Level 3 transaction monitoring alerts across retail and commercial banking
- Drafted and filed 80+ SARs to the NCA with zero regulatory feedback
- Mentored 5 junior analysts on alert investigation methodology
- Reduced false positive rate by 18% through rule tuning recommendations

Transaction Monitoring Analyst — JP Morgan, London
{start2} - {end2}
- Investigated automated alerts generated by Mantas platform
- Analysed transaction patterns across multiple jurisdictions
- Produced detailed case narratives and escalation reports
- Participated in annual AML risk assessment

Financial Crime Analyst — NatWest, Edinburgh
{start3} - {end3}
- Monitored high-value transactions for potential money laundering
- Conducted customer activity reviews and account closures
- Supported regulatory examinations and internal audits

EDUCATION
BA (Hons) Economics — University of Edinburgh (First)
ACAMS Certification (Association of Certified AML Specialists)
""",
            # 2: Compliance officer / team leader
            """CURRICULUM VITAE

{name}
{email} | {phone} | {location}

PROFESSIONAL SUMMARY
Senior compliance professional with {years}+ years leading financial crime prevention teams in investment banking. Extensive experience in regulatory compliance, policy development, and stakeholder management. Proven track record of building and managing teams of 15+ analysts across KYC remediation and AML programmes.

KEY SKILLS
- Team leadership and people management (15+ direct reports)
- Regulatory compliance (FCA, PRA, MiFID II, MAR)
- Policy and procedure development
- Stakeholder management (C-suite, regulators)
- Risk assessment frameworks
- Project management (remediation programmes)
- Budget management and resource planning
- Training and development programme design

PROFESSIONAL EXPERIENCE

Head of KYC Remediation — Goldman Sachs, London
{start1} - Present
- Lead remediation programme across 25,000+ client files
- Manage team of 18 analysts and 3 team leaders
- Reduced programme timeline by 4 months through process optimisation
- Designed quality assurance framework achieving 97% first-pass rate
- Regular reporting to FCA on programme progress

Senior Compliance Manager — Morgan Stanley, London
{start2} - {end2}
- Managed AML compliance team of 12 across London and Glasgow
- Developed risk-based approach to client categorisation
- Led regulatory examination preparation resulting in clean findings
- Implemented new CDD policies aligned with 5th Money Laundering Directive

Compliance Officer — Citi, London
{start3} - {end3}
- Conducted compliance monitoring and surveillance reviews
- Drafted compliance policies and procedures
- Provided compliance advisory to front office teams
- Managed regulatory reporting obligations

EDUCATION
MSc Financial Crime and Compliance — University of London (Distinction)
CISI Diploma in Investment Compliance
FCA Approved Persons (CF10, CF11)
""",
            # 3: Risk analyst
            """CURRICULUM VITAE

{name}
{email} | {phone} | {location}

PROFESSIONAL SUMMARY
Analytical risk professional with {years}+ years in operational and financial crime risk management. Strong quantitative skills combined with practical compliance experience. Skilled in risk modelling, control testing, and regulatory reporting. Expert in Basel III frameworks and operational risk capital calculations.

KEY SKILLS
- Operational risk management
- Credit risk analysis
- Risk modelling and quantification
- Control testing and assurance
- Basel III / CRD IV frameworks
- SOX compliance testing
- Internal audit support
- Data analytics (SQL, Python, Excel VBA)

PROFESSIONAL EXPERIENCE

Risk Analyst — Lloyds Banking Group, London
{start1} - Present
- Conduct operational risk assessments across retail banking division
- Develop and maintain risk control self-assessments (RCSAs)
- Model operational risk capital requirements under Basel III
- Produced quarterly risk reports for Board Risk Committee

Junior Risk Analyst — Standard Chartered, London
{start2} - {end2}
- Supported credit risk analysis for emerging markets portfolio
- Conducted stress testing and scenario analysis
- Maintained risk databases and reporting dashboards
- Assisted in annual ICAAP submissions

Graduate Analyst — BNP Paribas, London
{start3} - {end3}
- Rotated across market risk, credit risk, and operational risk teams
- Developed automated reporting tools using Python
- Supported regulatory capital calculations

EDUCATION
BSc (Hons) Mathematics — University of Leeds (First)
FRM (Financial Risk Manager) — GARP
CFA Level 2 Candidate
""",
            # 4: Sanctions screening specialist
            """CURRICULUM VITAE

{name}
{email} | {phone} | {location}

PROFESSIONAL SUMMARY
Specialist sanctions screening analyst with {years}+ years in financial crime prevention. Expert in OFAC, EU, and UN sanctions regimes with hands-on experience using World-Check, Fircosoft, and Dow Jones screening platforms. Strong understanding of trade finance sanctions risk and dual-use goods controls.

KEY SKILLS
- Sanctions screening and investigation
- OFAC, EU, UN, HMT sanctions regimes
- World-Check / Refinitiv platform
- Fircosoft / NICE Actimize
- Trade finance sanctions risk
- Dual-use goods and export controls
- PEP screening and adverse media
- Alert dispositioning and escalation

PROFESSIONAL EXPERIENCE

Senior Sanctions Analyst — Standard Chartered, London
{start1} - Present
- Lead sanctions screening for correspondent banking and trade finance
- Investigate complex Level 3 sanctions alerts across 40+ jurisdictions
- Developed screening rule library reducing false positives by 25%
- Trained 20+ analysts on OFAC secondary sanctions and Russian sanctions regime

Sanctions Analyst — Barclays, London
{start2} - {end2}
- Screened payment messages and trade finance documents for sanctions hits
- Investigated potential sanctions evasion through complex corporate structures
- Participated in sanctions policy review and updates
- Achieved 100% accuracy rate in QC reviews

Financial Crime Analyst — HSBC, London
{start3} - {end3}
- Conducted name screening for client onboarding
- Supported sanctions compliance programme
- Monitored changes to sanctions lists and updated screening systems

EDUCATION
BA (Hons) International Relations — University of Bristol (2:1)
ICA Advanced Certificate in Sanctions
ACAMS Certification
""",
        ]

        cv_created = 0
        for i, c in enumerate(candidates[:15]):
            safe_name = c.name.lower().replace(" ", "_")
            fname = f"cv_{safe_name}.pdf"
            fpath = cv_dir / fname

            if fpath.exists():
                continue

            template = CV_TEMPLATES[i % len(CV_TEMPLATES)]
            years = random.randint(3, 12)
            cv_text = template.format(
                name=c.name,
                email=c.email,
                phone=c.phone or "07700 900123",
                location=c.location or "London",
                years=years,
                start1=f"Jan {2024 - random.randint(1, 3)}",
                start2=f"Mar {2024 - random.randint(4, 6)}",
                end2=f"Dec {2024 - random.randint(1, 3)}",
                start3=f"Sep {2024 - random.randint(7, 10)}",
                end3=f"Feb {2024 - random.randint(4, 6)}",
            )
            fpath.write_text(cv_text, encoding="utf-8")
            cv_created += 1

        print(f"   [ADD] {cv_created} CV text files written to {cv_dir}")

        # Update Document records to point to actual CV files
        doc_updated = 0
        for i, c in enumerate(candidates[:15]):
            safe_name = c.name.lower().replace(" ", "_")
            fname = f"cv_{safe_name}.pdf"
            fpath = cv_dir / fname

            if not fpath.exists():
                continue

            # Check if candidate already has a CV document
            existing_doc = s.scalar(
                select(Document).where(Document.candidate_id == c.id, Document.doc_type == "cv")
            )
            if existing_doc:
                # Update filename to point to our actual file
                if existing_doc.filename != fname:
                    existing_doc.filename = fname
                    existing_doc.original_name = fname
                    doc_updated += 1
            else:
                s.add(Document(
                    candidate_id=c.id,
                    doc_type="cv",
                    filename=fname,
                    original_name=fname,
                    uploaded_at=days_ago(random.randint(5, 30)),
                ))
                doc_updated += 1
        s.commit()
        print(f"   [UPDATE] {doc_updated} CV document records linked to files")

        # ------------------------------------------------------------------
        #  24. RICHER JOB DESCRIPTIONS (for AI scoring)
        # ------------------------------------------------------------------
        section("24. Richer Job Descriptions")
        JOB_DESCRIPTIONS = {
            "KYC Case Handler": """KYC Case Handler — Barclays KYC Remediation Programme

We are seeking experienced KYC Case Handlers to join the Barclays KYC Remediation Programme based in London. This is a contract role paying £150-£220 per day (inside IR35).

Key Responsibilities:
- Conduct Customer Due Diligence (CDD) and Enhanced Due Diligence (EDD) reviews
- Review and remediate client files to meet current regulatory standards
- Screen clients against sanctions lists, PEP databases, and adverse media
- Escalate high-risk cases to the MLRO as required
- Maintain accurate records in the KYC management system

Essential Requirements:
- 2+ years KYC/CDD experience in a UK bank or financial institution
- Understanding of Money Laundering Regulations 2017 and FCA requirements
- Experience with remediation programmes
- Strong attention to detail and analytical skills
- Right to work in the UK

Desirable:
- ICA or CISI compliance qualification
- Experience with Barclays systems and processes
- ACAMS certification""",

            "KYC Team Leader": """KYC Team Leader — Barclays KYC Remediation Programme

We are seeking an experienced KYC Team Leader to manage a team of Case Handlers on the Barclays KYC Remediation Programme in London. Contract role paying £250-£350 per day (inside IR35).

Key Responsibilities:
- Lead and manage a team of 8-10 KYC Case Handlers
- Conduct quality assurance reviews on completed cases
- Manage team performance, SLAs, and productivity targets
- Escalate complex cases and provide technical guidance
- Produce weekly MI reports for programme leadership
- Conduct 1-2-1s and team briefings

Essential Requirements:
- 5+ years KYC/AML experience with at least 2 years in a team lead role
- Strong understanding of UK regulatory framework (FCA, PRA)
- People management experience (8+ direct reports)
- Experience with KYC remediation programmes
- Excellent communication and stakeholder management skills

Desirable:
- CISI Diploma or ICA Advanced Certificate
- Experience at Barclays or similar tier-1 bank
- Project management qualification""",

            "AML Analyst": """AML Analyst — Barclays AML Monitoring Programme

We are recruiting AML Analysts for the Barclays Anti-Money Laundering Monitoring team in London. Contract role paying £160-£230 per day (inside IR35).

Key Responsibilities:
- Investigate transaction monitoring alerts generated by automated systems
- Analyse customer transaction patterns for suspicious activity
- Draft Suspicious Activity Reports (SARs) for filing with the NCA
- Conduct customer activity reviews and risk assessments
- Maintain case management records and investigation logs

Essential Requirements:
- 2+ years AML/financial crime investigation experience
- Experience investigating transaction monitoring alerts
- Knowledge of SAR filing requirements
- Understanding of money laundering typologies
- Strong analytical and report writing skills

Desirable:
- ACAMS or ICA AML certification
- Experience with Actimize, Mantas, or similar TM platform
- Previous experience at a UK bank""",

            "Transaction Monitoring Analyst": """Transaction Monitoring Analyst — HSBC TM Programme

HSBC is looking for Transaction Monitoring Analysts to join the Birmingham-based TM operations team. Contract role paying £155-£225 per day (inside IR35).

Key Responsibilities:
- Investigate Level 1 and Level 2 transaction monitoring alerts
- Analyse payment patterns across retail and commercial accounts
- Identify potential money laundering, terrorist financing, and sanctions evasion
- Draft case narratives and escalation reports
- Support rule tuning by providing false positive analysis

Essential Requirements:
- 1+ years transaction monitoring or financial crime investigation experience
- Familiarity with TM platforms (Actimize, Mantas, Norkom, or similar)
- Understanding of money laundering typologies
- Strong attention to detail
- Ability to work in Birmingham office

Desirable:
- ACAMS or equivalent qualification
- Experience at HSBC or similar global bank
- SQL or data analysis skills""",

            "Sanctions Screening Analyst": """Sanctions Screening Analyst — HSBC Sanctions Programme

HSBC is seeking Sanctions Screening Analysts for the London-based sanctions compliance team. Contract role paying £165-£240 per day (outside IR35).

Key Responsibilities:
- Screen payments, trade finance documents, and customer data for sanctions matches
- Investigate potential true matches and escalate confirmed hits
- Monitor changes to OFAC, EU, UN, and HMT sanctions lists
- Support trade finance team with sanctions risk assessments
- Participate in sanctions policy reviews and system tuning

Essential Requirements:
- 2+ years sanctions screening or financial crime experience
- Knowledge of OFAC, EU, and UK sanctions regimes
- Experience with screening platforms (World-Check, Fircosoft, or similar)
- Understanding of trade finance sanctions risk
- Strong analytical skills

Desirable:
- ICA Sanctions Certificate or ACAMS
- Experience with correspondent banking sanctions
- Understanding of Russian/Belarus sanctions regime""",

            "QC Analyst": """QC Analyst — HSBC Sanctions Programme

We are looking for QC Analysts to join the HSBC Sanctions quality control team in London. Contract role paying £210-£290 per day (outside IR35).

Key Responsibilities:
- Conduct quality assurance reviews on sanctions screening dispositions
- Identify errors, inconsistencies, and training needs
- Produce QC reports and trend analysis
- Provide feedback and coaching to screening analysts
- Support continuous improvement of screening processes

Essential Requirements:
- 3+ years sanctions or AML experience with QC responsibilities
- Deep knowledge of sanctions regulations and screening methodologies
- Experience reviewing complex sanctions cases
- Excellent attention to detail
- Strong communication skills for feedback delivery

Desirable:
- Previous QC or audit experience
- ICA or ACAMS certification
- Team leadership experience""",
        }

        desc_updated = 0
        for j in jobs:
            # Find matching description by checking if job title contains key
            for key, desc in JOB_DESCRIPTIONS.items():
                if key.lower() in j.title.lower() or j.title.lower() in key.lower():
                    if len(j.description or "") < 500:  # Update descriptions shorter than rich versions
                        j.description = desc
                        desc_updated += 1
                    break
        s.commit()
        print(f"   [UPDATE] {desc_updated} job descriptions enriched")

        # ------------------------------------------------------------------
        #  25. STAGE CONFIG (seed defaults if empty)
        # ------------------------------------------------------------------
        section("25. Stage Config")
        try:
            from app import _seed_default_stages
            _seed_default_stages(s)
            print("   [OK] Default stages seeded (or already exist)")
        except Exception as e:
            print(f"   [WARN] Could not seed stages: {e}")

        # ------------------------------------------------------------------
        #  SUMMARY
        # ------------------------------------------------------------------
        section("SEED COMPLETE — Summary")
        summary = {
            "Users": count(s, User),
            "Role Types": count(s, RoleType),
            "Taxonomy Categories": count(s, TaxonomyCategory),
            "Taxonomy Tags": count(s, TaxonomyTag),
            "Candidate Tags": count(s, CandidateTag),
            "Opportunities": count(s, Opportunity),
            "Engagements": count(s, Engagement),
            "Engagement Plans": count(s, EngagementPlan),
            "Jobs": count(s, Job),
            "Candidates": count(s, Candidate),
            "Applications": count(s, Application),
            "Shortlists": count(s, Shortlist),
            "E-Sign Requests": count(s, ESigRequest),
            "Vetting Checks": count(s, VettingCheck),
            "Documents": count(s, Document),
            "Invoices": count(s, Invoice),
            "Candidate Notes": count(s, CandidateNote),
            "Reference Requests": count(s, ReferenceRequest),
            "Approved Umbrellas": count(s, ApprovedUmbrella),
            "Audit Log Entries": count(s, AuditLog),
            "Stage Configs": count(s, StageConfig),
        }

        for label, cnt in summary.items():
            print(f"   {label:25s} {cnt:>6}")

        print(f"\n{'='*60}")
        print("  All done!")
        print(f"{'='*60}")
        print("  STAFF APP:  http://localhost:5001/login")
        print("    Admin:  admin@demo.example.com / DemoAdmin2024!")
        print("    Staff:  sarah.r@optimus.demo / DemoPass2024!")
        print("")
        print("  ASSOCIATE PORTAL:  http://localhost:5001/portal/login")
        for c in candidates[:5]:
            print(f"    {c.name:25s} {c.email} / DemoCandidate2024!")
        print("")
        print("  JOB BOARD:  http://localhost:5001/jobs")
        print(f"{'='*60}\n")


# ============================================================================
if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        print(f"\n[FATAL] Seed failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
