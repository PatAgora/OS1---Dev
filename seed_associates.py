#!/usr/bin/env python3
"""
seed_associates.py — Seed 10 associate profiles only (no jobs, engagements, applications, etc.)
Safe to run multiple times — skips existing records.
"""

import os, sys, json, secrets, datetime, random, pathlib
from datetime import timedelta, date

os.environ.setdefault("FLASK_SECRET_KEY", "seed-key-not-used")
from app import (
    engine, Base,
    Candidate, Document, TaxonomyCategory, TaxonomyTag, CandidateTag,
    RoleType, StageConfig,
)
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text
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
    _PortalBase = _base()
    if _PortalBase:
        _PortalBase.metadata.create_all(engine, checkfirst=True)
    PORTAL_MODELS = True
    print("[OK] Associate portal models loaded")
except Exception as e:
    PORTAL_MODELS = False
    print(f"[WARN] Portal models not available: {e}")

NOW = datetime.datetime.utcnow()
TODAY = date.today()

def days_ago(n):
    return NOW - timedelta(days=n)

def date_days_ago(n):
    return TODAY - timedelta(days=n)

def count(session, model):
    return session.scalar(select(func.count(model.id)))

UK_NAMES = [
    ("James", "Richardson", "M"), ("Sarah", "Mitchell", "F"), ("David", "Thompson", "M"),
    ("Emma", "Clarke", "F"), ("Michael", "Patel", "M"), ("Laura", "Williams", "F"),
    ("Robert", "Singh", "M"), ("Hannah", "Brown", "F"), ("Daniel", "O'Brien", "M"),
    ("Charlotte", "Taylor", "F"),
]

POSTCODES = [
    "EC2R 8AH", "EC3V 3NG", "EC4M 7AN", "E14 5AB", "SE1 2QH",
    "M1 3BB", "M2 5BQ", "M3 4LU", "B1 1TT", "B2 5DB",
]

LOCATIONS = ["London", "Manchester", "Birmingham", "Leeds", "Edinburgh", "Cardiff", "Bristol", "Reading"]

SKILLS_POOL = [
    "KYC", "AML", "CDD", "EDD", "Compliance", "Risk Management",
    "Audit", "Financial Crime", "Sanctions Screening", "PEP Checks",
    "Transaction Monitoring", "Regulatory Reporting", "Basel III",
    "SOX Compliance", "GDPR", "Data Protection", "FCA Regulations",
    "Credit Risk", "Operational Risk", "Market Risk",
    "SAR Filing", "Client Onboarding", "Remediation",
    "Project Management", "Team Leadership",
]

CV_TEMPLATES = [
    """CURRICULUM VITAE

{name}
{email} | {phone} | {location}

PROFESSIONAL SUMMARY
Experienced KYC/AML analyst with {years}+ years in financial services compliance. Strong track record in customer due diligence, enhanced due diligence, and suspicious activity reporting across tier-1 banking institutions. CISI Level 3 qualified with deep understanding of FCA regulations.

KEY SKILLS
- Know Your Customer (KYC) / Customer Due Diligence (CDD)
- Anti-Money Laundering (AML) / Counter-Terrorist Financing (CTF)
- Enhanced Due Diligence (EDD) for high-risk customers
- Suspicious Activity Reports (SARs) filing
- Transaction monitoring and alert investigation
- PEP and sanctions screening (World-Check, Dow Jones)

PROFESSIONAL EXPERIENCE

Senior KYC Analyst — Deutsche Bank, London
{start1} - Present
- Led a team of 8 analysts conducting CDD/EDD reviews on corporate clients
- Processed 200+ KYC reviews per month with 99.2% quality pass rate
- Developed risk-based approach reducing backlog by 35%

KYC Analyst — Barclays, London
{start2} - {end2}
- Conducted KYC onboarding and periodic reviews for retail clients
- Screened clients against sanctions lists, PEP databases, and adverse media
- Escalated 45+ cases to MLRO for SAR consideration

Compliance Assistant — HSBC, Birmingham
{start3} - {end3}
- Supported AML compliance team with transaction monitoring alerts
- Assisted in remediation project reviewing 5,000+ client files

EDUCATION
BSc (Hons) Finance — University of Manchester (2:1)
CISI Level 3 Certificate in Compliance
ICA Certificate in Anti-Money Laundering
""",
    """CURRICULUM VITAE

{name}
{email} | {phone} | {location}

PROFESSIONAL SUMMARY
Detail-oriented transaction monitoring analyst with {years}+ years specialising in AML alert investigation and SAR filing. Proven ability to analyse complex financial transactions and identify suspicious patterns. Experienced with Actimize, Mantas, and Norkom platforms.

KEY SKILLS
- Transaction monitoring and alert investigation
- SAR/STR drafting and filing
- Typology identification (trade-based ML, layering, structuring)
- Actimize / NICE Actimize platform
- Sanctions screening (World-Check, Fircosoft)
- Regulatory reporting (FCA, NCA)

PROFESSIONAL EXPERIENCE

Senior TM Analyst — HSBC, Birmingham
{start1} - Present
- Investigate Level 2 and Level 3 transaction monitoring alerts
- Drafted and filed 80+ SARs to the NCA with zero regulatory feedback
- Reduced false positive rate by 18% through rule tuning recommendations

Transaction Monitoring Analyst — JP Morgan, London
{start2} - {end2}
- Investigated automated alerts generated by Mantas platform
- Analysed transaction patterns across multiple jurisdictions

Financial Crime Analyst — NatWest, Edinburgh
{start3} - {end3}
- Monitored high-value transactions for potential money laundering
- Supported regulatory examinations and internal audits

EDUCATION
BA (Hons) Economics — University of Edinburgh (First)
ACAMS Certification
""",
    """CURRICULUM VITAE

{name}
{email} | {phone} | {location}

PROFESSIONAL SUMMARY
Senior compliance professional with {years}+ years leading financial crime prevention teams in investment banking. Extensive experience in regulatory compliance, policy development, and stakeholder management. Proven track record managing teams of 15+ analysts.

KEY SKILLS
- Team leadership and people management (15+ direct reports)
- Regulatory compliance (FCA, PRA, MiFID II, MAR)
- Policy and procedure development
- Risk assessment frameworks
- Project management (remediation programmes)

PROFESSIONAL EXPERIENCE

Head of KYC Remediation — Goldman Sachs, London
{start1} - Present
- Lead remediation programme across 25,000+ client files
- Manage team of 18 analysts and 3 team leaders
- Designed quality assurance framework achieving 97% first-pass rate

Senior Compliance Manager — Morgan Stanley, London
{start2} - {end2}
- Managed AML compliance team of 12 across London and Glasgow
- Led regulatory examination preparation resulting in clean findings

Compliance Officer — Citi, London
{start3} - {end3}
- Conducted compliance monitoring and surveillance reviews
- Drafted compliance policies and procedures

EDUCATION
MSc Financial Crime and Compliance — University of London (Distinction)
CISI Diploma in Investment Compliance
""",
    """CURRICULUM VITAE

{name}
{email} | {phone} | {location}

PROFESSIONAL SUMMARY
Analytical risk professional with {years}+ years in operational and financial crime risk management. Strong quantitative skills combined with practical compliance experience. Expert in Basel III frameworks and operational risk capital calculations.

KEY SKILLS
- Operational risk management
- Credit risk analysis
- Risk modelling and quantification
- Basel III / CRD IV frameworks
- SOX compliance testing
- Data analytics (SQL, Python, Excel VBA)

PROFESSIONAL EXPERIENCE

Risk Analyst — Lloyds Banking Group, London
{start1} - Present
- Conduct operational risk assessments across retail banking division
- Model operational risk capital requirements under Basel III
- Produced quarterly risk reports for Board Risk Committee

Junior Risk Analyst — Standard Chartered, London
{start2} - {end2}
- Supported credit risk analysis for emerging markets portfolio
- Conducted stress testing and scenario analysis

Graduate Analyst — BNP Paribas, London
{start3} - {end3}
- Rotated across market risk, credit risk, and operational risk teams
- Developed automated reporting tools using Python

EDUCATION
BSc (Hons) Mathematics — University of Leeds (First)
FRM (Financial Risk Manager) — GARP
""",
    """CURRICULUM VITAE

{name}
{email} | {phone} | {location}

PROFESSIONAL SUMMARY
Specialist sanctions screening analyst with {years}+ years in financial crime prevention. Expert in OFAC, EU, and UN sanctions regimes with hands-on experience using World-Check, Fircosoft, and Dow Jones screening platforms.

KEY SKILLS
- Sanctions screening and investigation
- OFAC, EU, UN, HMT sanctions regimes
- World-Check / Refinitiv platform
- Trade finance sanctions risk
- PEP screening and adverse media

PROFESSIONAL EXPERIENCE

Senior Sanctions Analyst — Standard Chartered, London
{start1} - Present
- Lead sanctions screening for correspondent banking and trade finance
- Investigate complex Level 3 sanctions alerts across 40+ jurisdictions
- Developed screening rule library reducing false positives by 25%

Sanctions Analyst — Barclays, London
{start2} - {end2}
- Screened payment messages and trade finance documents for sanctions hits
- Achieved 100% accuracy rate in QC reviews

Financial Crime Analyst — HSBC, London
{start3} - {end3}
- Conducted name screening for client onboarding
- Monitored changes to sanctions lists and updated screening systems

EDUCATION
BA (Hons) International Relations — University of Bristol (2:1)
ICA Advanced Certificate in Sanctions
ACAMS Certification
""",
]


def seed_associates():
    print("\n" + "=" * 60)
    print("  OS1 ATS — Associate-Only Seed (10 profiles)")
    print("=" * 60)

    with Session(engine) as s:

        # 1. CANDIDATES (10 only)
        print("\n--- Candidates ---")
        existing = count(s, Candidate)
        if existing >= 10:
            print(f"  Already have {existing} candidates — skipping")
            candidates = s.scalars(select(Candidate).order_by(Candidate.id).limit(10)).all()
        else:
            candidates = []
            for i, (first, last, gender) in enumerate(UK_NAMES):
                email = f"{first.lower()}.{last.lower()}@candidate.demo"
                existing_c = s.scalar(select(Candidate).where(Candidate.email == email))
                if existing_c:
                    candidates.append(existing_c)
                    print(f"  [SKIP] {first} {last}")
                    continue

                c = Candidate(
                    name=f"{first} {last}",
                    email=email,
                    phone=f"07{random.randint(100,999)} {random.randint(100,999)} {random.randint(100,999)}",
                    skills=", ".join(random.sample(SKILLS_POOL, random.randint(3, 7))),
                    postcode=POSTCODES[i],
                    location=random.choice(LOCATIONS),
                    status=random.choice(["Available", "On Contract", "On Notice"]),
                    availability="Immediately available",
                    day_rate=random.choice([180, 200, 220, 250, 280, 300]),
                    min_day_rate=random.choice([150, 170, 180, 200]),
                    max_day_rate=random.choice([280, 300, 350, 400]),
                    previously_vetted=random.random() > 0.6,
                    gender=gender,
                    citizenship="British",
                    source="portal",
                    created_at=days_ago(random.randint(14, 180)),
                    password_hash=generate_password_hash("DemoCandidate2024!", method="pbkdf2:sha256"),
                    email_verified=True,
                    email_verified_at=days_ago(random.randint(5, 30)),
                )
                s.add(c)
                s.flush()
                candidates.append(c)
                print(f"  [ADD] {c.name} (id={c.id})")
            s.commit()

        # 2. ASSOCIATE PROFILES
        print("\n--- Associate Profiles ---")
        if PORTAL_MODELS and AssociateProfile:
            profile_added = 0
            for i, c in enumerate(candidates[:10]):
                existing_p = s.scalar(select(AssociateProfile).where(AssociateProfile.candidate_id == c.id))
                if existing_p:
                    print(f"  [SKIP] Profile for {c.name}")
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
            print(f"  [ADD] {profile_added} associate profiles")

            # 3. COMPANY DETAILS
            print("\n--- Company Details ---")
            cd_added = 0
            for i, c in enumerate(candidates[:8]):
                existing_cd = s.scalar(select(CompanyDetails).where(CompanyDetails.candidate_id == c.id))
                if existing_cd:
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
            print(f"  [ADD] {cd_added} company details")

            # 4. CONSENT RECORDS
            print("\n--- Consent Records ---")
            consent_added = 0
            for c in candidates[:8]:
                existing_cr = s.scalar(select(ConsentRecord).where(ConsentRecord.candidate_id == c.id))
                if not existing_cr:
                    s.add(ConsentRecord(
                        candidate_id=c.id,
                        consent_given=True,
                        legal_name=c.name,
                        signed_date=days_ago(random.randint(5, 30)),
                        ip_address=f"192.168.1.{random.randint(10, 200)}",
                    ))
                    consent_added += 1
            s.commit()
            print(f"  [ADD] {consent_added} consent records")

            # 5. DECLARATION RECORDS
            print("\n--- Declaration Records ---")
            decl_added = 0
            for i, c in enumerate(candidates[:8]):
                existing_dr = s.scalar(select(DeclarationRecord).where(DeclarationRecord.candidate_id == c.id))
                if not existing_dr:
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
            print(f"  [ADD] {decl_added} declaration records")

            # 6. EMPLOYMENT HISTORY
            print("\n--- Employment History ---")
            emp_companies = [
                ("Deutsche Bank", "KYC Analyst"), ("JP Morgan", "AML Analyst"),
                ("Goldman Sachs", "Compliance Officer"), ("Barclays", "Case Handler"),
                ("HSBC", "Transaction Monitoring Analyst"), ("Citi", "Risk Analyst"),
                ("BNP Paribas", "Regulatory Reporting Analyst"), ("UBS", "Financial Crime Analyst"),
                ("Morgan Stanley", "Sanctions Analyst"), ("Nomura", "Remediation Specialist"),
            ]
            emp_added = 0
            for i, c in enumerate(candidates[:10]):
                existing_emp = s.scalar(select(func.count(EmploymentHistory.id)).where(EmploymentHistory.candidate_id == c.id))
                if existing_emp and existing_emp >= 2:
                    continue
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
                        end_date=end if j > 0 else None,
                        reason_for_leaving=random.choice(["Contract ended", "Seeking new opportunity", "Redundancy", ""]) if j > 0 else "",
                        permission_to_request=True,
                        referee_email=f"hr@{comp.lower().replace(' ', '')}.demo",
                    ))
                    emp_added += 1
                    end = start - timedelta(days=random.randint(14, 60))
            s.commit()
            print(f"  [ADD] {emp_added} employment history records")

            # 7. QUALIFICATIONS
            print("\n--- Qualifications ---")
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
            qual_added = 0
            for i, c in enumerate(candidates[:8]):
                existing_q = s.scalar(select(func.count(QualificationRecord.id)).where(QualificationRecord.candidate_id == c.id))
                if existing_q and existing_q >= 1:
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
            print(f"  [ADD] {qual_added} qualification records")

            # 8. ADDRESS HISTORY
            print("\n--- Address History ---")
            addr_added = 0
            for i, c in enumerate(candidates[:8]):
                existing_a = s.scalar(select(func.count(AddressHistory.id)).where(AddressHistory.candidate_id == c.id))
                if existing_a and existing_a >= 1:
                    continue
                s.add(AddressHistory(
                    candidate_id=c.id,
                    address_line1=f"{random.randint(1, 200)} {random.choice(['High St', 'Kings Rd', 'Church Ln', 'Park Ave'])}",
                    city=random.choice(LOCATIONS),
                    postcode=POSTCODES[i % len(POSTCODES)],
                    from_date=date_days_ago(random.randint(365, 730)),
                    is_current=True,
                ))
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
            print(f"  [ADD] {addr_added} address history records")
        else:
            print("  [SKIP] Portal models not available")

        # 9. CV FILES + DOCUMENT RECORDS
        print("\n--- CV Files ---")
        cv_dir = pathlib.Path(os.path.dirname(__file__)) / "uploads" / "cvs"
        cv_dir.mkdir(parents=True, exist_ok=True)

        cv_created = 0
        for i, c in enumerate(candidates[:10]):
            safe_name = c.name.lower().replace(" ", "_").replace("'", "")
            fname = f"cv_{safe_name}.pdf"
            fpath = cv_dir / fname

            if not fpath.exists():
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

            # Ensure document record exists
            existing_doc = s.scalar(
                select(Document).where(Document.candidate_id == c.id, Document.doc_type == "cv")
            )
            if not existing_doc:
                s.add(Document(
                    candidate_id=c.id,
                    doc_type="cv",
                    filename=fname,
                    original_name=fname,
                    uploaded_at=days_ago(random.randint(5, 30)),
                ))
        s.commit()
        print(f"  [ADD] {cv_created} CV files written to {cv_dir}")

        # 10. REFERENCE CONFIG (role types, stage config, taxonomy)
        print("\n--- Reference Data ---")
        role_names = ["Case Handler", "Team Leader", "QC Analyst", "Project Manager", "Compliance Officer", "Risk Analyst"]
        for rn in role_names:
            existing_r = s.scalar(select(RoleType).where(RoleType.name == rn))
            if not existing_r:
                s.add(RoleType(name=rn, default_rate=random.choice([200, 250, 300, 350])))
        s.commit()

        try:
            from app import _seed_default_stages
            _seed_default_stages(s)
        except Exception:
            pass

        taxonomy_data = {
            ("subject", "Skills"): ["KYC", "AML", "CDD", "EDD", "Compliance", "Risk Management", "Audit", "Financial Crime", "Sanctions Screening", "PEP Checks", "Transaction Monitoring", "Regulatory Reporting"],
            ("subject", "Sector"): ["Banking", "Insurance", "Asset Management", "Fintech", "Payments", "Wealth Management"],
            ("subject", "Clearance"): ["SC Cleared", "CTC Cleared", "DV Cleared", "BPSS", "None"],
            ("subject", "Location"): ["London", "Manchester", "Birmingham", "Edinburgh", "Leeds", "Bristol", "Remote"],
        }
        for (cat_type, cat_name), tags in taxonomy_data.items():
            cat = s.scalar(select(TaxonomyCategory).where(TaxonomyCategory.name == cat_name))
            if not cat:
                cat = TaxonomyCategory(type=cat_type, name=cat_name)
                s.add(cat)
                s.flush()
            for tag_name in tags:
                t = s.scalar(select(TaxonomyTag).where(TaxonomyTag.category_id == cat.id, TaxonomyTag.tag == tag_name))
                if not t:
                    s.add(TaxonomyTag(category_id=cat.id, tag=tag_name))
        s.commit()
        print("  [OK] Role types, stages, taxonomy seeded")

        # SUMMARY
        print("\n" + "=" * 60)
        print("  ASSOCIATE SEED COMPLETE")
        print("=" * 60)
        print(f"  Candidates:          {count(s, Candidate)}")
        print(f"  Documents:           {count(s, Document)}")
        if PORTAL_MODELS:
            print(f"  Associate Profiles:  {s.scalar(select(func.count(AssociateProfile.id)))}")
        print(f"  Role Types:          {count(s, RoleType)}")
        print(f"  Taxonomy Tags:       {count(s, TaxonomyTag)}")
        print("=" * 60)
        print("  Portal logins (first 5):")
        for c in candidates[:5]:
            print(f"    {c.email} / DemoCandidate2024!")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        seed_associates()
    except Exception as e:
        print(f"\n[FATAL] Seed failed: {e}")
        import traceback
        traceback.print_exc()
