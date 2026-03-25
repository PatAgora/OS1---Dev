-- Migration 005: Add automation_enabled column to vetting_check table
-- Allows per-check automation toggle (start/stop) as requested in feedback item #15

ALTER TABLE vetting_check ADD COLUMN automation_enabled BOOLEAN DEFAULT 1;
