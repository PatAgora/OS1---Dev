-- 017_intro_to_vetting_sent_at.sql
-- Req 21 — auto-fire the Intro to Vetting email the moment the
-- candidate accepts an offer via the portal. The timestamp acts as an
-- idempotency lock so duplicate sends are impossible without an
-- explicit "Resend" action that clears the column.

ALTER TABLE candidates ADD COLUMN IF NOT EXISTS intro_to_vetting_sent_at TIMESTAMP;
