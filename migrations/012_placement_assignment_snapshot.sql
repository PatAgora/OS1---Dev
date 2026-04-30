-- 012_placement_assignment_snapshot.sql
-- When an assignment is ended, the live umbrella_assignment_* flags on the
-- candidates row are reset so the Contract card on the profile renders blank.
-- These columns hold the snapshot of those flags at the moment of ending so
-- the new "Previous Contract" tile can show the historical state.

ALTER TABLE esign_requests ADD COLUMN IF NOT EXISTS assignment_sent_at   TIMESTAMP;
ALTER TABLE esign_requests ADD COLUMN IF NOT EXISTS assignment_signed    BOOLEAN DEFAULT FALSE;
ALTER TABLE esign_requests ADD COLUMN IF NOT EXISTS assignment_signed_at TIMESTAMP;
