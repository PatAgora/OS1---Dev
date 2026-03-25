-- Migration: Add password and 2FA fields to candidates table
-- Date: 2026-02-23

-- Password and 2FA columns for portal authentication
ALTER TABLE candidates ADD COLUMN password_hash VARCHAR(255);
ALTER TABLE candidates ADD COLUMN totp_secret VARCHAR(32);
ALTER TABLE candidates ADD COLUMN totp_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE candidates ADD COLUMN backup_codes TEXT;
ALTER TABLE candidates ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE candidates ADD COLUMN locked_until DATETIME;
ALTER TABLE candidates ADD COLUMN password_set_at DATETIME;

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_candidates_totp_enabled ON candidates(totp_enabled);
CREATE INDEX IF NOT EXISTS idx_candidates_email_verified ON candidates(email_verified);
