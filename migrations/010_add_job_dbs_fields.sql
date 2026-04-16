-- Migration 010: DBS vetting criteria on jobs
--
-- Captures staff-entered DBS detail at job creation so the data can later be
-- pushed straight into Verifile's /orders/candidateentry CheckSpecificData
-- block without re-prompting. Fields are staff-only; the public job advert
-- (public_job.html) does not render any of them.
--
-- All columns nullable / defaulted so existing rows don't need backfill.
-- TIMESTAMP-style types avoided — no dates needed here.

ALTER TABLE jobs ADD COLUMN dbs_level VARCHAR(20) DEFAULT 'Basic';
ALTER TABLE jobs ADD COLUMN dbs_sector VARCHAR(100) DEFAULT '';
ALTER TABLE jobs ADD COLUMN dbs_purpose VARCHAR(100) DEFAULT '';
ALTER TABLE jobs ADD COLUMN dbs_position_applied_for VARCHAR(60) DEFAULT '';
ALTER TABLE jobs ADD COLUMN dbs_employer_name VARCHAR(60) DEFAULT '';
ALTER TABLE jobs ADD COLUMN dbs_job_role VARCHAR(200) DEFAULT '';
ALTER TABLE jobs ADD COLUMN dbs_working_with_children BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN dbs_working_with_vulnerable_adults BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN dbs_children_in_environment BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN dbs_vulnerable_adults_in_environment BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN dbs_is_volunteer BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN dbs_working_from_home BOOLEAN DEFAULT FALSE;
