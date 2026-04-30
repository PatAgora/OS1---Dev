-- 011_placement_end_fields.sql
-- Adds the columns required to support the "End Assignment" action on the
-- candidate profile Contract card. A placement (ESigRequest) is treated as
-- ended when ended_at IS NOT NULL.

ALTER TABLE esign_requests ADD COLUMN IF NOT EXISTS ended_at   TIMESTAMP;
ALTER TABLE esign_requests ADD COLUMN IF NOT EXISTS end_reason VARCHAR(50);
ALTER TABLE esign_requests ADD COLUMN IF NOT EXISTS end_notes  TEXT;
