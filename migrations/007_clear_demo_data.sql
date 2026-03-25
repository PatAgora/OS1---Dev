-- 007_clear_demo_data.sql
-- Clears all transactional demo data while preserving:
--   - All user accounts (passwords/logins intact)
--   - All associate_profiles (10 records)
--   - Candidates 1-10 (linked to associate profiles)
--   - Reference/config tables (role_types, stage_config, taxonomy, umbrella companies, flagged houses)
--
-- Run once. Safe to re-run (all DELETEs are idempotent).

BEGIN;

-- 1. Clear tables with no inbound FKs first (leaf tables)
DELETE FROM webhook_events;
DELETE FROM audit_logs;
DELETE FROM trustid_checks;

-- 2. Clear esign_requests (FK to applications, candidates, engagements)
DELETE FROM esign_requests;

-- 3. Clear shortlists (FK to jobs, candidates)
DELETE FROM shortlists;

-- 4. Clear applications (FK to jobs, candidates)
DELETE FROM applications;

-- 5. Clear invoices (FK to engagements, users)
DELETE FROM invoices;

-- 6. Clear jobs (FK to engagements)
DELETE FROM jobs;

-- 7. Clear engagement_plans (FK to engagements)
DELETE FROM engagement_plans;

-- 8. Clear engagements (FK to opportunities)
DELETE FROM engagements;

-- 9. Clear opportunities
DELETE FROM opportunities;

-- 10. Clear candidate-linked data for ALL candidates (including 1-10)
--     These are demo records, not part of the associate profile itself
DELETE FROM candidate_notes;
DELETE FROM candidate_tags;
DELETE FROM documents;
DELETE FROM vetting_check;
DELETE FROM reference_requests;
DELETE FROM reference_contacts;
DELETE FROM employment_history;
DELETE FROM address_history;
DELETE FROM qualification_records;
DELETE FROM declaration_records;
DELETE FROM consent_records;
DELETE FROM company_details;

-- 11. Delete candidates NOT linked to associate profiles (IDs 11-25)
DELETE FROM candidates WHERE id NOT IN (SELECT candidate_id FROM associate_profiles);

-- 12. Clear timesheets (all empty but include for completeness)
DELETE FROM timesheet_expenses;
DELETE FROM timesheet_entries;
DELETE FROM timesheets;
DELETE FROM timesheet_configs;

-- 13. Remove all demo users except admin@demo.example.com
DELETE FROM password_history WHERE user_id IN (SELECT id FROM users WHERE email != 'admin@demo.example.com');
DELETE FROM users WHERE email != 'admin@demo.example.com';

COMMIT;
