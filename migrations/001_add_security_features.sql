-- Security Features Migration
-- Add MFA support and audit logging tables

-- Add MFA columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_secret TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled_at TIMESTAMP;

-- Create index for MFA lookups
CREATE INDEX IF NOT EXISTS idx_users_mfa ON users(mfa_secret) WHERE mfa_secret IS NOT NULL;

-- Create audit log table for security events
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    event_type TEXT NOT NULL,
    user_id INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for audit log queries
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_logs(event_type);

-- For SQLite compatibility (if using SQLite locally):
-- Note: SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS before 3.35
-- If you get errors, use these instead:

-- For SQLite, use these commands:
-- ALTER TABLE users ADD COLUMN mfa_secret TEXT;
-- ALTER TABLE users ADD COLUMN mfa_enabled_at TIMESTAMP;
-- CREATE INDEX idx_users_mfa ON users(mfa_secret) WHERE mfa_secret IS NOT NULL;
