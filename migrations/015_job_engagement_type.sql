-- 015_job_engagement_type.sql
-- Req 13 — Contract / Permanent flag on jobs. Drives the Engagement Type
-- field on the Offer of Engagement capture sheet so the offer can be
-- locked to the JD. Default 'Contract' reflects current Optimus business.

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS engagement_type VARCHAR(20) DEFAULT 'Contract';
