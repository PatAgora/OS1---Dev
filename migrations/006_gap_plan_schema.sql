-- Migration 006: Gap Plan Schema Additions
-- Covers: Batches 1-11 model/column additions + new staff-side requirements (N1-N17)
-- Safe to re-run: uses ADD COLUMN IF NOT EXISTS pattern for SQLite/PostgreSQL compatibility

-- =========================================================================
-- VETTING CHECK TABLE — New columns (Batch 1.1, 3, 4, N5, N6, N10)
-- =========================================================================

-- Batch 1.1: Analyst case allocation
ALTER TABLE vetting_check ADD COLUMN assigned_to INTEGER REFERENCES users(id);

-- N5: Per-check colour system (white/green/orange)
ALTER TABLE vetting_check ADD COLUMN colour VARCHAR(20) DEFAULT 'white';
ALTER TABLE vetting_check ADD COLUMN colour_manual BOOLEAN DEFAULT 0;

-- N6: Prompt-only checks (no upload required)
ALTER TABLE vetting_check ADD COLUMN prompt_only BOOLEAN DEFAULT 0;

-- N10: ID verification method required before DBS
ALTER TABLE vetting_check ADD COLUMN id_verified BOOLEAN DEFAULT 0;
ALTER TABLE vetting_check ADD COLUMN id_verification_method VARCHAR(50);
ALTER TABLE vetting_check ADD COLUMN id_verified_at DATETIME;

-- Batch 3: QC workflow
ALTER TABLE vetting_check ADD COLUMN qc_status VARCHAR(30) DEFAULT '';
ALTER TABLE vetting_check ADD COLUMN qc_reviewed_by INTEGER REFERENCES users(id);
ALTER TABLE vetting_check ADD COLUMN qc_reviewed_at DATETIME;
ALTER TABLE vetting_check ADD COLUMN qc_notes TEXT DEFAULT '';

-- =========================================================================
-- DOCUMENTS TABLE — New columns (Batch 1.2, N13/J1)
-- =========================================================================

-- Batch 1.2: Document expiry tracking
ALTER TABLE documents ADD COLUMN expiry_date DATE;

-- N13/J1: Track which project/engagement used this document
ALTER TABLE documents ADD COLUMN engagement_id INTEGER REFERENCES engagements(id);

-- =========================================================================
-- CANDIDATES TABLE — New columns (Batch 1.4, N1-N4)
-- =========================================================================

-- Batch 1.4: Additional vetting fields
ALTER TABLE candidates ADD COLUMN citizenship VARCHAR(100);
ALTER TABLE candidates ADD COLUMN place_of_birth VARCHAR(200);

-- N1: Gender (DBS, World Check, Social Media)
ALTER TABLE candidates ADD COLUMN gender VARCHAR(20);

-- N2: Optional DBS fields
ALTER TABLE candidates ADD COLUMN mothers_maiden_name VARCHAR(200);
ALTER TABLE candidates ADD COLUMN driving_licence_number VARCHAR(50);
ALTER TABLE candidates ADD COLUMN passport_number VARCHAR(50);

-- N3: Location of place of work (World Check)
ALTER TABLE candidates ADD COLUMN work_location VARCHAR(200);

-- N4: Name variations (JSON array for multi-name checks)
ALTER TABLE candidates ADD COLUMN name_variations TEXT;

-- =========================================================================
-- ENGAGEMENTS TABLE — New columns (Batch 8.3, P9)
-- =========================================================================

-- Batch 8.3: Client-specific document requirements
ALTER TABLE engagements ADD COLUMN required_documents TEXT;

-- P9: Reference period configurable per client
ALTER TABLE engagements ADD COLUMN reference_period_years INTEGER DEFAULT 3;

-- =========================================================================
-- NEW TABLE: REFERENCE REQUESTS (Batch 5 — staff-side reference tracking)
-- =========================================================================

CREATE TABLE IF NOT EXISTS reference_requests (
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
);

CREATE INDEX IF NOT EXISTS idx_reference_requests_candidate ON reference_requests(candidate_id);
CREATE INDEX IF NOT EXISTS idx_reference_requests_status ON reference_requests(status);

-- =========================================================================
-- INDEXES for new columns
-- =========================================================================

CREATE INDEX IF NOT EXISTS idx_vetting_check_assigned ON vetting_check(assigned_to);
CREATE INDEX IF NOT EXISTS idx_vetting_check_qc_status ON vetting_check(qc_status);
CREATE INDEX IF NOT EXISTS idx_documents_expiry ON documents(expiry_date);
CREATE INDEX IF NOT EXISTS idx_documents_engagement ON documents(engagement_id);
