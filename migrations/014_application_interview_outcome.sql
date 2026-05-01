-- 014_application_interview_outcome.sql
-- Req 9 — per-interview outcome on the applications table. A candidate
-- can have multiple interviews across different applications and each
-- one needs its own Pass / Fail / No Show value. The mirror on
-- candidates.optimus_interview_result still tracks the latest
-- interview's outcome for the resource-pool badge / overall status.

ALTER TABLE applications ADD COLUMN IF NOT EXISTS optimus_interview_result VARCHAR(50);
