-- ========================================
-- CREST COMPLIANCE: Database Migration
-- ========================================
-- This migration adds security columns needed for:
-- - Account lockout protection
-- - Role-based access control
-- - Audit logging
-- - Session tracking
--
-- RUN THIS IN: Railway Dashboard → PostgreSQL → Data tab
-- ========================================

-- Step 1: Add security columns to users table
ALTER TABLE users 
  ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'employee',
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS last_login TIMESTAMP,
  ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

-- Step 2: Create audit_logs table for security event tracking
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id INTEGER,
    user_email VARCHAR(255),
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    status VARCHAR(20) DEFAULT 'success',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Step 3: Create indexes for performance and security queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_email ON audit_logs(user_email);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_category ON audit_logs(event_category);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Step 4: Set first user as admin (if exists)
UPDATE users 
SET role = 'admin' 
WHERE id = (SELECT MIN(id) FROM users)
AND role IS NULL;

-- ========================================
-- Verification Queries (Run these after)
-- ========================================

-- Check users table structure:
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position;

-- Check audit_logs table exists:
-- SELECT COUNT(*) FROM audit_logs;

-- Check first user is admin:
-- SELECT id, name, email, role FROM users ORDER BY id LIMIT 1;

-- ========================================
-- MIGRATION COMPLETE
-- Next step: Redeploy application to enable security features
-- ========================================
