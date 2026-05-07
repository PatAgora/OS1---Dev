-- 016_offer_end_date.sql
-- Req 13 — explicit end date on the Offer of Engagement, captured
-- alongside offer_start_date so the offer can be locked to the parent
-- Engagement's date window. offer_expected_duration is kept as a
-- freeform display string for the docx merge.

ALTER TABLE applications ADD COLUMN IF NOT EXISTS offer_end_date DATE;
