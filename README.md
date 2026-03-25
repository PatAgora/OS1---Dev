# ATS Onboarding Platform - Client Demo

![Status](https://img.shields.io/badge/status-demo-blue)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.3-green.svg)
![License](https://img.shields.io/badge/license-proprietary-red.svg)

## 🎯 About This Demo

This is a **clean, production-ready demo environment** of the ATS (Applicant Tracking System) Onboarding Platform v7.4. It contains **no real data** and is specifically prepared for client demonstrations.

### What This Is:
- ✅ Fully functional ATS with all features enabled
- ✅ Safe for client demonstrations (no real PII)
- ✅ Production-ready security configuration
- ✅ Fictional demo data (5 candidates, 4 jobs, 3 clients)
- ✅ GDPR compliant for demonstrations

### What This Is NOT:
- ❌ Not for production use with real candidates
- ❌ Not containing any test data or real CVs
- ❌ Not the development version (that's in `ats-onboarding` repo)

---

## 🚀 Quick Start

### For Clients Viewing This Demo:

**Live Demo URL**: `https://your-demo-url.up.railway.app`

**Demo Login**:
- Email: `admin@demo.example.com`
- Password: `DemoAdmin2024!`

### For Deployment Team:

See [`DEMO_DEPLOYMENT_GUIDE.md`](./DEMO_DEPLOYMENT_GUIDE.md) for complete deployment instructions.

**Quick deploy to Railway**:
```bash
# 1. Push to GitHub
git push origin main

# 2. Connect Railway to this repository
# 3. Add PostgreSQL database
# 4. Set environment variables (see guide)
# 5. Run migrations
```

---

## ✨ Key Features

### Recruitment Management
- **Multi-tenant Engagements** - Manage multiple clients simultaneously
- **Job Posting & Distribution** - Public job portal with unique links
- **Application Tracking** - Full lifecycle from application to offer
- **Candidate Database** - Searchable resource pool with CV storage

### Workflow & Collaboration
- **Kanban Board** - Visual pipeline management
- **Application Stages** - Applied → Screening → Interview → Shortlisted → Offered
- **Notes & Comments** - Collaborative feedback on candidates
- **Activity Timeline** - Full audit trail of actions

### Compliance & Security
- **GDPR Compliant** - Right to be forgotten, data export
- **Secure File Upload** - CV validation and sanitization
- **Role-based Access** - Worker vs Candidate permissions
- **Audit Logging** - Security event tracking
- **MFA Support** - TOTP-based two-factor authentication

### Integration Features
- **E-Signatures** - DocuSign & HelloSign integration
- **KYC/Identity Verification** - Sumsub integration
- **AI-Powered Matching** - OpenAI GPT for candidate summaries
- **Email Notifications** - SMTP integration for updates
- **Magic Links** - Passwordless candidate authentication

### Reporting & Analytics
- **Engagement Financials** - Revenue tracking and projections
- **Pipeline Metrics** - Applications by stage
- **Candidate Statistics** - Active vs placed contractors
- **Job Performance** - Application rates and conversion

---

## 📊 Demo Data Overview

The demo includes fictional data for realistic demonstrations:

| Category | Count | Examples |
|----------|-------|----------|
| **Clients** | 3 | Demo Tech Solutions, Demo Financial Services, Demo Healthcare |
| **Jobs** | 4 | Full Stack Developer, DevOps Engineer, Compliance Manager |
| **Candidates** | 5 | Sarah Johnson, Michael Chen, Emma Williams, etc. |
| **Applications** | 5 | Various stages from "applied" to "shortlisted" |
| **Skills** | 6 | React.js, Node.js, AWS, Docker, FCA Regulations, EPR Systems |

**All data is 100% fictional** - names, emails (`@demo.example.com`), and phone numbers are not real.

---

## 🔒 Security Features

### Production-Ready Security:
- ✅ HTTPS enforcement (via Railway edge)
- ✅ HTTP Strict Transport Security (HSTS)
- ✅ Content Security Policy (CSP)
- ✅ CSRF protection
- ✅ Rate limiting (1000/day, 100/hour)
- ✅ Secure session cookies
- ✅ File upload validation
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ XSS protection (Jinja2 auto-escaping)

### Disabled for Demo:
- ❌ Debug routes (`/__ping`, `/__routes`) - Commented out
- ❌ Test endpoints - Removed from production build

---

## 🛠️ Technology Stack

### Backend
- **Python 3.11+** - Modern Python with type hints
- **Flask 3.0.3** - Lightweight web framework
- **SQLAlchemy 2.0** - SQL toolkit and ORM
- **PostgreSQL 16** - Production database
- **Gunicorn** - WSGI HTTP server

### Frontend
- **Jinja2 Templates** - Server-side rendering
- **TailwindCSS** - Utility-first CSS (via CDN)
- **Vanilla JavaScript** - No heavy frameworks
- **Responsive Design** - Mobile-friendly interface

### Security
- **Flask-Talisman** - Security headers (CSP, HSTS, etc.)
- **Flask-Limiter** - Rate limiting
- **Flask-Login** - Session management
- **Flask-WTF** - CSRF protection
- **pyotp** - TOTP/MFA implementation

### Integrations
- **OpenAI GPT-4** - AI-powered features (optional)
- **Sumsub** - KYC/Identity verification (optional)
- **DocuSign / HelloSign** - E-signatures (optional)
- **SMTP** - Email notifications (optional)

---

## 📖 Demo Workflow Guide

### Recommended Demo Script:

1. **Start at Dashboard** (`/`)
   - Show KPIs: Active candidates, applications, engagements
   - Highlight recent activity timeline

2. **Browse Jobs** (`/jobs`)
   - Show job listings
   - Create a new job posting
   - Demonstrate public job link (`/public/jobs/JOB_TOKEN`)

3. **View Candidates** (`/resource-pool`)
   - Browse candidate database
   - Show search/filter capabilities
   - View candidate profile with CV and applications

4. **Manage Applications** (`/applications`)
   - Show application pipeline
   - Move candidate between stages
   - Add interview notes

5. **Kanban Board** (`/kanban`)
   - Visualize full pipeline
   - Drag-and-drop stage changes
   - Quick status overview

6. **Engagements** (`/engagements`)
   - Show multi-client management
   - Demonstrate financials tracking
   - Engagement-specific jobs and applications

7. **Public Portal** (`/public/jobs`)
   - Candidate-facing job board
   - Application form workflow
   - Self-service features

### Features to Emphasize:
- 🎯 **Multi-tenancy** - Separate pipelines per client
- 🤖 **AI Integration** - Smart candidate summaries
- 📝 **Compliance** - GDPR-ready with audit trails
- 🔐 **Security** - Enterprise-grade protection
- 🚀 **Speed** - Fast, responsive interface

---

## 🔧 Configuration

### Required Environment Variables:
```bash
DATABASE_URL=postgresql://...          # PostgreSQL connection string
FLASK_SECRET_KEY=...                   # Cryptographic key (32+ chars)
FLASK_ENV=production                   # Must be 'production' for demo
```

### Optional Integrations:
```bash
OPENAI_API_KEY=sk-...                  # For AI features
SUMSUB_APP_TOKEN=...                   # For KYC verification
SUMSUB_SECRET_KEY=...                  # Sumsub secret
HELLOSIGN_API_KEY=...                  # For e-signatures
SMTP_HOST=smtp.gmail.com               # For email notifications
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

---

## 📞 Support & Contact

### For Client Demos:
- **Live Demo**: Contact your account representative for access
- **Questions**: See in-app help or contact support team

### For Deployment Issues:
- See [`DEMO_DEPLOYMENT_GUIDE.md`](./DEMO_DEPLOYMENT_GUIDE.md)
- Check Railway logs for troubleshooting
- Review PostgreSQL connection and migrations

---

## 🔄 Updating the Demo

```bash
# Pull latest changes
git pull origin main

# Push updates (Railway auto-deploys)
git push origin main
```

Railway will automatically redeploy within 3-4 minutes.

---

## ⚠️ Important Disclaimers

1. **Demo Environment Only** - This is NOT for production recruitment
2. **Fictional Data** - All candidates, jobs, and clients are fictional
3. **Public Demo Credentials** - Change password if using long-term
4. **No Real PII** - Safe to demonstrate to any audience
5. **Separate Deployment** - Isolated from production systems

---

## 📄 License

**Proprietary Software** - For demonstration purposes only.

© 2024 All Rights Reserved. This demo environment is provided for client evaluation only and may not be used for actual recruitment activities without a proper license agreement.

---

## 🎉 Ready to Deploy?

See [`DEMO_DEPLOYMENT_GUIDE.md`](./DEMO_DEPLOYMENT_GUIDE.md) for step-by-step instructions!

**Questions?** Contact the deployment team or your account representative.
