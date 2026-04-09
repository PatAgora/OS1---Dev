-- Migration 009: Offer detail capture on applications (Req-046)
--
-- Adds 12 nullable columns to the applications table so the staff can record
-- offer details when they make an offer, and so the candidate can accept or
-- decline the offer from the associate portal. No Signable involvement at
-- this stage — accept/decline directly updates the application status.
--
-- All columns are nullable so existing applications don't need backfill.

-- NOTE: TIMESTAMP not DATETIME — Postgres rejects DATETIME with
-- `type "datetime" does not exist`. SQLite accepts both transparently.
ALTER TABLE applications ADD COLUMN offer_start_date DATE;
ALTER TABLE applications ADD COLUMN offer_role_title VARCHAR(300);
ALTER TABLE applications ADD COLUMN offer_day_rate NUMERIC(10, 2);
ALTER TABLE applications ADD COLUMN offer_rate_type VARCHAR(20);
ALTER TABLE applications ADD COLUMN offer_location VARCHAR(300);
ALTER TABLE applications ADD COLUMN offer_notes TEXT;
ALTER TABLE applications ADD COLUMN offer_made_at TIMESTAMP;
ALTER TABLE applications ADD COLUMN offer_made_by_id INTEGER REFERENCES users(id);
ALTER TABLE applications ADD COLUMN offer_response VARCHAR(20);
ALTER TABLE applications ADD COLUMN offer_responded_at TIMESTAMP;
ALTER TABLE applications ADD COLUMN offer_responded_ip VARCHAR(50);
ALTER TABLE applications ADD COLUMN offer_decline_reason TEXT;
