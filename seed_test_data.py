"""Seed 50 realistic test candidates with engagements, jobs, applications, etc."""
import datetime, random, uuid
from app import engine
from sqlalchemy import text
from sqlalchemy.orm import Session

now = datetime.datetime.utcnow()
def days_ago(n):
    return now - datetime.timedelta(days=n)

with Session(engine) as s:
    # Clean existing demo data
    for table in ["applications", "shortlists", "candidate_tags", "candidates", "jobs",
                  "engagement_plans", "engagements", "opportunities", "taxonomy_tags", "taxonomy_categories"]:
        try:
            s.execute(text(f"DELETE FROM {table}"))
        except:
            pass
    s.commit()
    print("Cleaned existing data.")

    # ── TAXONOMY ──
    categories = [
        ("skill", "Python"), ("skill", "Java"), ("skill", "React.js"), ("skill", "Node.js"),
        ("skill", "AWS"), ("skill", "Azure"), ("skill", "Docker"), ("skill", "Kubernetes"),
        ("skill", "SQL"), ("skill", "PostgreSQL"), ("skill", "MongoDB"),
        ("skill", "FCA Regulations"), ("skill", "Anti-Money Laundering"),
        ("skill", "Risk Management"), ("skill", "Basel III/IV"),
        ("skill", "Project Management"), ("skill", "Agile/Scrum"),
        ("skill", "EPR Systems"), ("skill", "HL7/FHIR"), ("skill", "Cyber Security"),
        ("skill", "Power BI"), ("skill", "Tableau"), ("skill", "SAP"),
        ("skill", "ServiceNow"), ("skill", "Salesforce"),
    ]
    for cat_type, cat_name in categories:
        s.execute(text("INSERT INTO taxonomy_categories (type, name) VALUES (:t, :n)"),
                  {"t": cat_type, "n": cat_name})
    s.commit()
    rows = s.execute(text("SELECT id, name FROM taxonomy_categories")).fetchall()
    for row in rows:
        s.execute(text("INSERT INTO taxonomy_tags (category_id, tag) VALUES (:cid, :tag)"),
                  {"cid": row[0], "tag": row[1]})
    s.commit()
    print(f"Created {len(categories)} taxonomy categories & tags")

    # ── ENGAGEMENTS ──
    engagements = [
        ("Barclays Digital Transformation", "Barclays PLC", "active", "ENG-001", days_ago(90),
         "Large-scale digital banking transformation programme requiring developers, PMs and analysts"),
        ("HSBC Regulatory Compliance", "HSBC Holdings", "active", "ENG-002", days_ago(60),
         "FCA compliance remediation project - risk, compliance and audit specialists needed"),
        ("NHS Digital - EPR Rollout", "NHS England", "active", "ENG-003", days_ago(45),
         "Electronic Patient Records implementation across 12 trusts"),
        ("Lloyds Banking Group - Cloud Migration", "Lloyds Banking Group", "active", "ENG-004", days_ago(30),
         "Migration of legacy systems to AWS cloud infrastructure"),
        ("Deloitte Consulting - SAP Programme", "Deloitte UK", "active", "ENG-005", days_ago(75),
         "SAP S/4HANA implementation for major retail client"),
        ("FCA Enforcement Division", "Financial Conduct Authority", "active", "ENG-006", days_ago(20),
         "Specialist investigators and data analysts for enforcement cases"),
        ("AstraZeneca IT Ops", "AstraZeneca", "pending", "ENG-007", days_ago(10),
         "IT operations and ServiceNow administration support"),
        ("Aviva Claims Platform", "Aviva PLC", "active", "ENG-008", days_ago(55),
         "Modernisation of claims processing platform - full stack developers needed"),
        ("PwC Cyber Security", "PwC UK", "active", "ENG-009", days_ago(40),
         "Penetration testing and security operations centre staffing"),
        ("Standard Chartered - Data Analytics", "Standard Chartered", "pending", "ENG-010", days_ago(5),
         "Data engineering and BI reporting team build-out"),
    ]
    for name, client, status, ref, start, desc in engagements:
        s.execute(text("""INSERT INTO engagements (name, client, status, ref, start_date, description)
                         VALUES (:name, :client, :status, :ref, :start, :desc)"""),
                  {"name": name, "client": client, "status": status, "ref": ref,
                   "start": start, "desc": desc})
    s.commit()
    eng_ids = [r[0] for r in s.execute(text("SELECT id FROM engagements ORDER BY id")).fetchall()]
    print(f"Created {len(engagements)} engagements")

    # ── ENGAGEMENT PLANS ──
    plans = [
        (eng_ids[0], "Project Manager", 2, 550, 750), (eng_ids[0], "Case Handler", 8, 350, 500),
        (eng_ids[1], "Project Director", 1, 800, 1100), (eng_ids[1], "Case Handler", 6, 400, 600),
        (eng_ids[2], "Project Manager", 2, 500, 700), (eng_ids[2], "Team Leader", 3, 450, 650),
        (eng_ids[3], "Ops Manager", 1, 600, 850), (eng_ids[3], "Case Handler", 10, 400, 550),
        (eng_ids[4], "Project Director", 1, 900, 1200), (eng_ids[4], "Case Handler", 5, 500, 700),
        (eng_ids[7], "Project Manager", 1, 550, 750), (eng_ids[7], "Case Handler", 4, 380, 520),
        (eng_ids[8], "Team Leader", 2, 650, 900), (eng_ids[8], "Case Handler", 6, 500, 700),
    ]
    for eid, role, count, pay, charge in plans:
        s.execute(text("""INSERT INTO engagement_plans (engagement_id, role_type, planned_count, pay_rate, charge_rate, rate, version_int)
                         VALUES (:eid, :role, :count, :pay, :charge, :charge, 1)"""),
                  {"eid": eid, "role": role, "count": count, "pay": pay, "charge": charge})
    s.commit()
    print(f"Created {len(plans)} engagement plans")

    # ── JOBS ──
    jobs_data = [
        (eng_ids[0], "Senior Python Developer", "Build microservices for digital banking platform. Python, FastAPI, PostgreSQL, Docker experience required. Must have financial services background.", "Case Handler", "London (Hybrid)", "550-650/day", "open"),
        (eng_ids[0], "Delivery Manager", "Lead delivery of digital transformation workstreams. Agile/SAFe experience essential. Banking sector preferred.", "Project Manager", "London (On-site)", "700-800/day", "open"),
        (eng_ids[1], "FCA Compliance Analyst", "Review and remediate compliance frameworks against FCA SYSC requirements. SM&CR experience essential.", "Case Handler", "London (On-site)", "500-600/day", "open"),
        (eng_ids[1], "Risk Framework Specialist", "Design and implement risk assessment frameworks aligned with Basel III/IV. Strong quantitative background.", "Case Handler", "London (Hybrid)", "600-750/day", "open"),
        (eng_ids[2], "Clinical Systems Analyst", "Support EPR implementation across NHS trusts. HL7/FHIR integration experience required.", "Case Handler", "Birmingham (Hybrid)", "400-500/day", "open"),
        (eng_ids[2], "EPR Project Manager", "Manage rollout of electronic patient records across multiple hospital sites. Prince2/MSP certified.", "Project Manager", "Birmingham (On-site)", "550-700/day", "open"),
        (eng_ids[3], "AWS Cloud Architect", "Design and implement cloud migration strategy for legacy banking systems. AWS Solutions Architect Professional required.", "Case Handler", "Edinburgh (Hybrid)", "700-900/day", "open"),
        (eng_ids[3], "DevOps Engineer", "Build CI/CD pipelines and infrastructure as code for cloud-native banking applications. Terraform, Kubernetes, Jenkins.", "Case Handler", "Edinburgh (Remote)", "500-650/day", "open"),
        (eng_ids[4], "SAP S/4HANA Functional Consultant", "Configure and implement SAP S/4HANA Finance module. CPA certification preferred.", "Case Handler", "Manchester (Hybrid)", "600-800/day", "open"),
        (eng_ids[5], "Financial Investigator", "Conduct enforcement investigations into market abuse and financial crime. FCA experience essential.", "Case Handler", "London (On-site)", "550-700/day", "open"),
        (eng_ids[5], "Data Analyst - Enforcement", "Analyse large datasets to identify patterns of market abuse. Python, SQL, Tableau required.", "Case Handler", "London (Hybrid)", "450-550/day", "open"),
        (eng_ids[7], "Full Stack Developer", "Modernise claims platform using React, Node.js, and AWS. Insurance domain experience valuable.", "Case Handler", "Norwich (Hybrid)", "450-550/day", "open"),
        (eng_ids[7], "QA Test Lead", "Lead testing strategy for claims platform modernisation. Automation experience with Cypress/Playwright.", "Case Handler", "Norwich (Remote)", "400-500/day", "open"),
        (eng_ids[8], "Penetration Tester", "Conduct infrastructure and application penetration tests for financial services clients. CREST/OSCP certified.", "Case Handler", "London (Hybrid)", "600-800/day", "open"),
        (eng_ids[8], "SOC Analyst", "Monitor and respond to security incidents in 24/7 SOC environment. SIEM experience required.", "Case Handler", "London (On-site)", "400-500/day", "open"),
        (eng_ids[9], "Data Engineer", "Build data pipelines and warehousing solutions using Spark, Airflow, and Snowflake.", "Case Handler", "London (Remote)", "550-700/day", "draft"),
    ]
    for eid, title, desc, role, loc, sal, status in jobs_data:
        token = str(uuid.uuid4())[:8]
        s.execute(text("""INSERT INTO jobs (engagement_id, title, description, role_type, location, salary_range, status, public_token, created_at)
                         VALUES (:eid, :title, :desc, :role, :loc, :sal, :status, :token, :created)"""),
                  {"eid": eid, "title": title, "desc": desc, "role": role, "loc": loc,
                   "sal": sal, "status": status, "token": token, "created": days_ago(random.randint(5, 60))})
    s.commit()
    job_ids = [r[0] for r in s.execute(text("SELECT id FROM jobs ORDER BY id")).fetchall()]
    print(f"Created {len(jobs_data)} jobs")

    # ── 50 CANDIDATES ──
    candidates = [
        ("Sarah Johnson", "sarah.johnson@demo.example.com", "+44 7700 900001", "Python, Flask, Django, PostgreSQL, Docker, AWS", "London", "Available", 550, 650, "Experienced Python developer with 8 years in financial services. Built trading platforms at Goldman Sachs.", "LinkedIn"),
        ("Michael Chen", "michael.chen@demo.example.com", "+44 7700 900002", "AWS, Terraform, Kubernetes, Docker, Jenkins, Python", "Edinburgh", "Available", 650, 800, "Cloud architect with AWS Professional certification. Led migrations for 3 major banks.", "Referral"),
        ("Emma Williams", "emma.williams@demo.example.com", "+44 7700 900003", "FCA Regulations, SM&CR, Compliance, Risk Management", "London", "2 weeks notice", 500, 600, "Senior compliance professional with 12 years FCA-regulated firm experience.", "Direct"),
        ("James Patel", "james.patel@demo.example.com", "+44 7700 900004", "HL7, FHIR, EPR Systems, SQL, Project Management", "Birmingham", "Available", 400, 500, "Clinical systems specialist with NHS Digital background. Implemented EPR across 5 trusts.", "LinkedIn"),
        ("Sophie Martinez", "sophie.martinez@demo.example.com", "+44 7700 900005", "React, Node.js, TypeScript, AWS, MongoDB", "Norwich", "Available", 450, 550, "Full stack developer specialising in insurance technology platforms.", "Agency"),
        ("Oliver Thompson", "oliver.thompson@demo.example.com", "+44 7700 900006", "Agile, SAFe, PRINCE2, Delivery Management, Banking", "London", "1 month notice", 700, 850, "Programme delivery manager with 15 years in banking transformation.", "Referral"),
        ("Charlotte Brown", "charlotte.brown@demo.example.com", "+44 7700 900007", "Penetration Testing, OSCP, CREST, Burp Suite, Python", "London", "Available", 650, 800, "CREST-certified penetration tester with focus on financial services.", "Direct"),
        ("William Davies", "william.davies@demo.example.com", "+44 7700 900008", "SAP S/4HANA, SAP FI/CO, ABAP, Integration", "Manchester", "Available", 600, 750, "SAP functional consultant with 10 years experience. S/4HANA certified.", "LinkedIn"),
        ("Amelia Wilson", "amelia.wilson@demo.example.com", "+44 7700 900009", "Python, SQL, Tableau, Power BI, Data Analysis", "London", "Available", 450, 550, "Data analyst with experience in FCA enforcement and market surveillance.", "Direct"),
        ("George Taylor", "george.taylor@demo.example.com", "+44 7700 900010", "Java, Spring Boot, Microservices, Kafka, Oracle", "London", "2 weeks notice", 550, 700, "Backend developer with strong Java skills. Built real-time trading systems.", "LinkedIn"),
        ("Isabella Anderson", "isabella.anderson@demo.example.com", "+44 7700 900011", "Risk Management, Basel III, Credit Risk, VaR", "London", "Available", 600, 750, "Quantitative risk specialist with Basel III/IV implementation experience.", "Referral"),
        ("Harry Thomas", "harry.thomas@demo.example.com", "+44 7700 900012", "DevOps, CI/CD, Terraform, AWS, GitHub Actions", "Edinburgh", "Available", 500, 650, "DevOps engineer specialising in cloud infrastructure and automation.", "LinkedIn"),
        ("Mia Jackson", "mia.jackson@demo.example.com", "+44 7700 900013", "ServiceNow, ITIL, IT Operations, Automation", "Leeds", "1 week notice", 380, 450, "ServiceNow administrator with ITIL v4 foundation. 6 years IT ops experience.", "Agency"),
        ("Jack White", "jack.white@demo.example.com", "+44 7700 900014", "Salesforce, Apex, Lightning, Integration, CRM", "London", "Available", 500, 650, "Salesforce architect with platform developer II certification.", "Direct"),
        ("Poppy Harris", "poppy.harris@demo.example.com", "+44 7700 900015", "Project Management, Agile, Scrum, Healthcare, NHS", "Birmingham", "Available", 500, 650, "Healthcare project manager. Led EPR implementations for 3 NHS trusts.", "Referral"),
        ("Oscar Martin", "oscar.martin@demo.example.com", "+44 7700 900016", "React, Vue.js, TypeScript, CSS, UX", "London", "Available", 400, 550, "Frontend developer with a passion for accessible design. Built Gov.UK services.", "LinkedIn"),
        ("Lily Robinson", "lily.robinson@demo.example.com", "+44 7700 900017", "Anti-Money Laundering, KYC, Financial Crime, Compliance", "London", "2 weeks notice", 500, 650, "AML specialist with experience at major clearing banks. CAMS certified.", "Direct"),
        ("Charlie Clark", "charlie.clark@demo.example.com", "+44 7700 900018", "Python, Spark, Airflow, Snowflake, Data Engineering", "London", "Available", 550, 700, "Data engineer building scalable pipelines for banking analytics.", "LinkedIn"),
        ("Evie Lewis", "evie.lewis@demo.example.com", "+44 7700 900019", "Cyber Security, SIEM, Splunk, Incident Response", "London", "Available", 450, 550, "SOC analyst with 4 years experience in financial services security operations.", "Agency"),
        ("Freddie Walker", "freddie.walker@demo.example.com", "+44 7700 900020", "AWS, Azure, GCP, Cloud Architecture, Security", "Manchester", "1 month notice", 700, 900, "Multi-cloud architect. Designed infrastructure for FTSE 100 companies.", "Referral"),
        ("Daisy Hall", "daisy.hall@demo.example.com", "+44 7700 900021", "QA, Test Automation, Cypress, Playwright, Selenium", "Norwich", "Available", 400, 500, "QA lead with deep experience in test automation for insurance platforms.", "LinkedIn"),
        ("Alfie Young", "alfie.young@demo.example.com", "+44 7700 900022", "Java, Kotlin, Android, Mobile Development", "London", "Available", 500, 650, "Mobile developer with banking app experience. Built Monzo features.", "Direct"),
        ("Grace King", "grace.king@demo.example.com", "+44 7700 900023", "Business Analysis, Requirements, Agile, Banking", "London", "2 weeks notice", 450, 600, "Senior BA with 10 years in investment banking. Strong stakeholder management.", "LinkedIn"),
        ("Henry Wright", "henry.wright@demo.example.com", "+44 7700 900024", "Network Security, Firewalls, VPN, Zero Trust", "London", "Available", 500, 650, "Network security engineer with experience securing trading floor infrastructure.", "Referral"),
        ("Ella Scott", "ella.scott@demo.example.com", "+44 7700 900025", "Power BI, DAX, SQL, Data Modelling, Reporting", "Manchester", "Available", 400, 500, "BI developer creating executive dashboards for financial services clients.", "Agency"),
        ("Leo Green", "leo.green@demo.example.com", "+44 7700 900026", "Python, Machine Learning, NLP, TensorFlow", "London", "1 month notice", 600, 800, "ML engineer applying NLP to regulatory document analysis.", "LinkedIn"),
        ("Scarlett Adams", "scarlett.adams@demo.example.com", "+44 7700 900027", "Compliance, MiFID II, EMIR, Regulatory Reporting", "London", "Available", 550, 700, "Regulatory reporting specialist. Led MiFID II implementation at Deutsche Bank.", "Direct"),
        ("Archie Baker", "archie.baker@demo.example.com", "+44 7700 900028", "PostgreSQL, MySQL, Oracle, DBA, Performance Tuning", "Edinburgh", "Available", 500, 650, "Database administrator with expertise in high-availability financial systems.", "Referral"),
        ("Florence Nelson", "florence.nelson@demo.example.com", "+44 7700 900029", "UX Research, User Testing, Design Thinking, Figma", "London", "2 weeks notice", 400, 550, "UX researcher specialising in financial services digital products.", "LinkedIn"),
        ("Arthur Carter", "arthur.carter@demo.example.com", "+44 7700 900030", "PRINCE2, MSP, Programme Management, Change Management", "Birmingham", "Available", 650, 850, "Senior programme manager. Delivered 50M+ NHS transformation programmes.", "Direct"),
        ("Rosie Mitchell", "rosie.mitchell@demo.example.com", "+44 7700 900031", "React, Next.js, GraphQL, Node.js, AWS", "London", "Available", 500, 650, "Full stack developer with fintech startup experience. Built payment systems.", "LinkedIn"),
        ("Theodore Perez", "theodore.perez@demo.example.com", "+44 7700 900032", "Azure, .NET, C#, Microservices, Event Sourcing", "Manchester", "1 week notice", 550, 700, ".NET architect with Azure Solutions Architect Expert certification.", "Agency"),
        ("Willow Roberts", "willow.roberts@demo.example.com", "+44 7700 900033", "Clinical Safety, DSCN, NHS Digital Standards, HL7", "Leeds", "Available", 450, 600, "Clinical safety officer with DSCN certification. Healthcare IT governance specialist.", "Direct"),
        ("Sebastian Turner", "sebastian.turner@demo.example.com", "+44 7700 900034", "Financial Investigation, Fraud, Intelligence Analysis", "London", "Available", 500, 650, "Former SFO investigator. Expert in complex financial fraud cases.", "Referral"),
        ("Ivy Phillips", "ivy.phillips@demo.example.com", "+44 7700 900035", "Scrum Master, Agile Coach, SAFe, Kanban", "London", "Available", 500, 650, "Certified Scrum Master and SAFe Program Consultant. Banking transformation experience.", "LinkedIn"),
        ("Max Campbell", "max.campbell@demo.example.com", "+44 7700 900036", "Kubernetes, Helm, ArgoCD, Platform Engineering", "Edinburgh", "2 weeks notice", 600, 750, "Platform engineer building internal developer platforms for banks.", "Direct"),
        ("Sienna Parker", "sienna.parker@demo.example.com", "+44 7700 900037", "Tableau, SQL, Python, Statistical Analysis, R", "London", "Available", 400, 550, "Statistical analyst with experience in market surveillance at the FCA.", "Agency"),
        ("Hugo Evans", "hugo.evans@demo.example.com", "+44 7700 900038", "Java, Spring, Kafka, Redis, Trading Systems", "London", "1 month notice", 650, 800, "Senior Java developer building low-latency trading platforms.", "LinkedIn"),
        ("Matilda Edwards", "matilda.edwards@demo.example.com", "+44 7700 900039", "GDPR, Data Protection, Privacy, Information Governance", "London", "Available", 450, 600, "Data protection officer with GDPR implementation experience across financial services.", "Referral"),
        ("Noah Collins", "noah.collins@demo.example.com", "+44 7700 900040", "AWS, Lambda, DynamoDB, Serverless, API Gateway", "London", "Available", 550, 700, "Serverless architect. Built event-driven systems processing 1M+ transactions/day.", "Direct"),
        ("Aria Stewart", "aria.stewart@demo.example.com", "+44 7700 900041", "ServiceNow, ITSM, Change Management, CMDB", "Manchester", "1 week notice", 400, 500, "ServiceNow developer with ITSM and CMDB specialisation. Pharma sector experience.", "LinkedIn"),
        ("Ethan Morris", "ethan.morris@demo.example.com", "+44 7700 900042", "Penetration Testing, Red Team, Cobalt Strike, Kali", "London", "Available", 600, 800, "Red team operator with OSEP certification. Conducted adversary simulations for banks.", "Agency"),
        ("Luna Rogers", "luna.rogers@demo.example.com", "+44 7700 900043", "Business Analysis, Insurance, Claims, Transformation", "Norwich", "Available", 400, 550, "Insurance BA with deep claims domain knowledge. Aviva and LV= experience.", "Referral"),
        ("Theo Reed", "theo.reed@demo.example.com", "+44 7700 900044", "SQL, ETL, SSIS, Data Warehousing, Azure Data Factory", "Leeds", "2 weeks notice", 450, 600, "Data warehouse developer with experience in banking regulatory reporting.", "LinkedIn"),
        ("Phoebe Cook", "phoebe.cook@demo.example.com", "+44 7700 900045", "Project Management, Waterfall, Agile, Financial Services", "London", "Available", 550, 700, "Hybrid project manager comfortable with waterfall and agile. 8 years in banking.", "Direct"),
        ("Jasper Morgan", "jasper.morgan@demo.example.com", "+44 7700 900046", "React Native, iOS, Swift, Mobile Banking", "London", "1 month notice", 550, 700, "Mobile developer building banking apps. React Native and native iOS experience.", "Agency"),
        ("Aurora Bell", "aurora.bell@demo.example.com", "+44 7700 900047", "Compliance Monitoring, Conduct Risk, FCA, Supervision", "London", "Available", 500, 650, "Compliance monitoring specialist. Built conduct risk frameworks at Barclays.", "LinkedIn"),
        ("Luca Murphy", "luca.murphy@demo.example.com", "+44 7700 900048", "Docker, Kubernetes, Istio, Service Mesh, SRE", "Edinburgh", "Available", 550, 700, "SRE engineer with focus on container orchestration and service mesh architectures.", "Referral"),
        ("Chloe Bailey", "chloe.bailey@demo.example.com", "+44 7700 900049", "EPR Systems, Cerner, Epic, Healthcare Integration", "Birmingham", "2 weeks notice", 450, 600, "EPR implementation specialist with Cerner and Epic certification.", "Direct"),
        ("Felix Howard", "felix.howard@demo.example.com", "+44 7700 900050", "Python, Go, Rust, Systems Programming, Performance", "London", "Available", 650, 850, "Systems programmer building high-performance financial infrastructure. Ex-Jane Street.", "LinkedIn"),
    ]

    statuses = ["available", "active", "screening", "placed", "on_bench"]
    for i, (name, email, phone, skills, location, avail, min_rate, max_rate, summary, source) in enumerate(candidates):
        status = statuses[i % len(statuses)]
        s.execute(text("""INSERT INTO candidates
            (name, email, phone, skills, location, availability, min_day_rate, max_day_rate, day_rate,
             ai_summary, source, status, created_at)
            VALUES (:name, :email, :phone, :skills, :loc, :avail, :min_r, :max_r, :day_r,
                    :summary, :source, :status, :created)"""),
            {"name": name, "email": email, "phone": phone, "skills": skills, "loc": location,
             "avail": avail, "min_r": min_rate, "max_r": max_rate, "day_r": (min_rate + max_rate) // 2,
             "summary": summary, "source": source, "status": status,
             "created": days_ago(random.randint(1, 90))})
    s.commit()
    cand_ids = [r[0] for r in s.execute(text("SELECT id FROM candidates ORDER BY id")).fetchall()]
    print(f"Created {len(candidates)} candidates")

    # ── APPLICATIONS ──
    applications = [
        (cand_ids[0], job_ids[0], "shortlisted", 85, "Strong Python/Flask skills. Goldman Sachs background ideal for banking."),
        (cand_ids[9], job_ids[0], "interview_scheduled", 78, "Java dev but strong Python skills. Trading systems experience relevant."),
        (cand_ids[30], job_ids[0], "applied", 72, "Full stack with fintech experience. React focus but Python capable."),
        (cand_ids[17], job_ids[0], "screening", 80, "Data engineer but strong Python. Spark experience a bonus."),
        (cand_ids[5], job_ids[1], "interview_completed", 92, "Perfect fit. 15 years banking transformation. SAFe certified."),
        (cand_ids[34], job_ids[1], "shortlisted", 75, "Scrum Master expanding to delivery. Good potential."),
        (cand_ids[44], job_ids[1], "applied", 70, "PM with financial services background. Hybrid methodology experience."),
        (cand_ids[2], job_ids[2], "offer", 95, "Outstanding compliance professional. 12 years FCA experience. SM&CR expert."),
        (cand_ids[16], job_ids[2], "interview_scheduled", 88, "AML specialist. Strong KYC and financial crime expertise."),
        (cand_ids[26], job_ids[2], "shortlisted", 82, "MiFID II specialist. Good regulatory reporting background."),
        (cand_ids[46], job_ids[2], "screening", 79, "Compliance monitoring background. Conduct risk experience at Barclays."),
        (cand_ids[10], job_ids[3], "contract_sent", 93, "Ideal candidate. Quantitative risk with Basel III/IV implementation."),
        (cand_ids[38], job_ids[3], "interview_completed", 76, "GDPR/data protection focus but some risk management experience."),
        (cand_ids[3], job_ids[4], "placed", 90, "NHS Digital background. Implemented EPR across 5 trusts. Perfect match."),
        (cand_ids[48], job_ids[4], "interview_scheduled", 85, "Cerner/Epic certified. Strong healthcare integration skills."),
        (cand_ids[32], job_ids[4], "shortlisted", 78, "Clinical safety officer. Good complementary skills for the role."),
        (cand_ids[14], job_ids[5], "offer", 91, "Healthcare PM who led EPR at 3 NHS trusts. Ideal candidate."),
        (cand_ids[29], job_ids[5], "interview_completed", 88, "Senior programme manager. 50M+ NHS experience. Strong candidate."),
        (cand_ids[1], job_ids[6], "interview_scheduled", 94, "AWS Professional certified. Led 3 major bank migrations. Top candidate."),
        (cand_ids[19], job_ids[6], "shortlisted", 89, "Multi-cloud architect. FTSE 100 experience. AWS very strong."),
        (cand_ids[39], job_ids[6], "screening", 75, "Serverless specialist. Deep AWS but narrower scope than needed."),
        (cand_ids[11], job_ids[7], "shortlisted", 86, "Strong DevOps skills. Terraform and K8s expertise. Good fit."),
        (cand_ids[35], job_ids[7], "interview_scheduled", 83, "Platform engineer with K8s/ArgoCD. Slightly different angle but strong."),
        (cand_ids[47], job_ids[7], "applied", 80, "SRE with container expertise. Docker/K8s/Istio background."),
        (cand_ids[7], job_ids[8], "onboarding", 92, "SAP S/4HANA certified. 10 years experience. Onboarding in progress."),
        (cand_ids[33], job_ids[9], "interview_completed", 94, "Former SFO investigator. Complex fraud expertise. Excellent match."),
        (cand_ids[8], job_ids[9], "shortlisted", 72, "Data analyst. FCA enforcement experience but not investigation."),
        (cand_ids[8], job_ids[10], "offer", 91, "Perfect for data analyst role. FCA market surveillance Python/Tableau."),
        (cand_ids[36], job_ids[10], "interview_scheduled", 85, "Statistical analyst with FCA market surveillance. Strong candidate."),
        (cand_ids[24], job_ids[10], "shortlisted", 80, "BI developer. Power BI expert. Some overlap with requirements."),
        (cand_ids[4], job_ids[11], "placed", 88, "Insurance tech specialist. React/Node/AWS. Perfect for claims platform."),
        (cand_ids[15], job_ids[11], "interview_completed", 75, "Frontend dev. React strong but limited backend. Could work."),
        (cand_ids[45], job_ids[11], "screening", 70, "Mobile dev with React Native. Transitioning to web. Potential."),
        (cand_ids[20], job_ids[12], "contract_sent", 90, "QA lead with Cypress/Playwright. Insurance platform experience. Ideal."),
        (cand_ids[6], job_ids[13], "interview_scheduled", 95, "CREST certified. Financial services focus. Outstanding candidate."),
        (cand_ids[41], job_ids[13], "shortlisted", 90, "Red team operator. OSEP certified. Very strong technical skills."),
        (cand_ids[23], job_ids[13], "applied", 65, "Network security. Different discipline but some overlap."),
        (cand_ids[18], job_ids[14], "offer", 88, "SOC analyst with 4 years FS security ops. SIEM expertise. Great fit."),
        (cand_ids[41], job_ids[14], "screening", 72, "Red team background. Could transition to blue team but overqualified."),
        (cand_ids[17], job_ids[15], "applied", 92, "Data engineer. Spark/Airflow/Snowflake. Perfect match."),
        (cand_ids[43], job_ids[15], "applied", 78, "Data warehouse dev. ETL/SSIS background. Could transition to modern stack."),
    ]

    for cid, jid, status, score, notes in applications:
        created = days_ago(random.randint(1, 30))
        interview_at = None
        interview_done = None
        if status in ("interview_scheduled", "interview_completed", "offer", "contract_sent", "onboarding", "placed"):
            interview_at = days_ago(random.randint(1, 15))
        if status in ("interview_completed", "offer", "contract_sent", "onboarding", "placed"):
            interview_done = days_ago(random.randint(0, 10))
        s.execute(text("""INSERT INTO applications
            (job_id, candidate_id, status, ai_score, ai_summary, ai_explanation,
             interview_scheduled_at, interview_completed_at, created_at)
            VALUES (:jid, :cid, :status, :score, :summary, :explanation,
                    :interview_at, :interview_done, :created)"""),
            {"jid": jid, "cid": cid, "status": status, "score": score,
             "summary": notes, "explanation": notes,
             "interview_at": interview_at, "interview_done": interview_done,
             "created": created})
    s.commit()
    print(f"Created {len(applications)} applications")

    # ── OPPORTUNITIES ──
    opps = [
        ("Morgan Stanley Data Platform", "Morgan Stanley", "Lead", "Oliver Thompson", None, 500000, 60, "Data lake modernisation. Initial conversations with CTO office."),
        ("BNP Paribas Regulatory", "BNP Paribas", "Lead", "Emma Williams", None, 350000, 40, "DORA compliance programme. Awaiting RFP response."),
        ("Vodafone IT Transformation", "Vodafone UK", "Closed Won", "Oliver Thompson", days_ago(5), 800000, 100, "Won. Converted to engagement. Major IT outsourcing deal."),
        ("Tesco Bank Migration", "Tesco Bank", "Closed Lost", None, None, 250000, 0, "Lost to Accenture. Price was the deciding factor."),
    ]
    for name, client, stage, owner, est_start, value, prob, notes in opps:
        s.execute(text("""INSERT INTO opportunities (name, client, stage, owner, est_start, est_value, probability, notes, created_at)
                         VALUES (:name, :client, :stage, :owner, :start, :val, :prob, :notes, :created)"""),
                  {"name": name, "client": client, "stage": stage, "owner": owner,
                   "start": est_start, "val": value, "prob": prob, "notes": notes,
                   "created": days_ago(random.randint(10, 60))})
    s.commit()
    print(f"Created {len(opps)} opportunities")

    # ── SHORTLISTS ──
    shortlist_pairs = [
        (job_ids[0], cand_ids[0]), (job_ids[0], cand_ids[9]),
        (job_ids[2], cand_ids[2]), (job_ids[2], cand_ids[16]), (job_ids[2], cand_ids[26]),
        (job_ids[6], cand_ids[1]), (job_ids[6], cand_ids[19]),
        (job_ids[9], cand_ids[33]), (job_ids[13], cand_ids[6]), (job_ids[13], cand_ids[41]),
    ]
    for jid, cid in shortlist_pairs:
        s.execute(text("INSERT INTO shortlists (job_id, candidate_id, created_at) VALUES (:jid, :cid, :created)"),
                  {"jid": jid, "cid": cid, "created": days_ago(random.randint(1, 20))})
    s.commit()
    print(f"Created {len(shortlist_pairs)} shortlist entries")

    # ── FINAL COUNTS ──
    print("\n=== DATABASE SUMMARY ===")
    for table in ["candidates", "jobs", "engagements", "applications", "engagement_plans",
                   "opportunities", "shortlists", "taxonomy_categories", "taxonomy_tags"]:
        count = s.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"  {table}: {count}")

print("\nDone! Test data seeded successfully.")
